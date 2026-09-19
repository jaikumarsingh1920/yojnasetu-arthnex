import re
import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.scheme import Scheme
from app.models.candidate import CandidateScheme
from app.models.verification import SchemeVerification
from app.models.changelog import SchemeChangelog
from app.models.ingestion import SchemeSource
from app.services.ingestion.rule_generator import SchemeRuleGenerator
from app.services.ingestion.document_generator import SchemeDocumentGenerator
from app.services.ingestion.sync_service import IngestionSyncService

logger = logging.getLogger("yojnasetu.ingestion.promotion")


class CandidatePromotionService:
    """
    Promotes an approved CandidateScheme into the canonical Scheme dataset.
    Generates sequence-safe canonical scheme_id, creates statutory SchemeRule and
    SchemeDocument records, writes immutable audit changelog, and triggers RAG sync.
    """

    @classmethod
    def generate_next_scheme_id(cls, db: Session) -> str:
        """Determines the next sequential canonical scheme_id (e.g. SIH26092-860)."""
        existing_ids = db.query(Scheme.scheme_id).filter(Scheme.scheme_id.like("SIH26092-%")).all()
        max_num = 0
        for (sid,) in existing_ids:
            m = re.search(r"SIH26092-(\d+)", sid)
            if m:
                try:
                    num = int(m.group(1))
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
        return f"SIH26092-{max_num + 1:03d}"

    @classmethod
    def can_promote(cls, candidate: CandidateScheme) -> tuple[bool, str]:
        """
        Phase 10 Safety Promotion Gate:
        Enforces that a candidate may be promoted ONLY when:
        candidate_status == STAGED (or DISCOVERED during ingestion)
        AND verification_status == OFFICIALLY_VERIFIED
        AND duplicate_status == UNIQUE
        AND validation_status == VALID
        AND data_confidence in (HIGH, MEDIUM)
        AND authoritative official source exists
        """
        if candidate.candidate_status not in ("STAGED", "DISCOVERED"):
            return False, f"candidate_status is '{candidate.candidate_status}', must be STAGED"
        if candidate.verification_status != "OFFICIALLY_VERIFIED":
            return False, f"verification_status is '{candidate.verification_status}', must be OFFICIALLY_VERIFIED"
        if candidate.duplicate_status != "UNIQUE":
            return False, f"duplicate_status is '{candidate.duplicate_status}', must be UNIQUE"
        if candidate.validation_status != "VALID":
            return False, f"validation_status is '{candidate.validation_status}', must be VALID"
        if candidate.data_confidence not in ("HIGH", "MEDIUM"):
            return False, f"data_confidence is '{candidate.data_confidence}', must be HIGH/MEDIUM"
        if not candidate.official_source_url or not candidate.official_source_url.startswith("http"):
            return False, "Authoritative official source URL missing or invalid"
        return True, "QUALIFIED"

    @classmethod
    def promote_candidate(
        cls,
        db: Session,
        candidate_id: str,
        reviewer_id: str = "admin@yojnasetu.gov.in",
        notes: Optional[str] = None,
        sync_rag: bool = True
    ) -> Scheme:
        candidate = db.query(CandidateScheme).filter(CandidateScheme.candidate_id == candidate_id).first()
        if not candidate:
            raise ValueError(f"CandidateScheme '{candidate_id}' not found.")

        # Idempotency: if candidate is already approved, return the matching canonical scheme
        if candidate.candidate_status == "APPROVED":
            existing = None
            if candidate.official_source_url:
                existing = db.query(Scheme).filter(Scheme.official_source_url == candidate.official_source_url).first()
            if not existing and candidate.normalized_name:
                existing = db.query(Scheme).filter(Scheme.scheme_name == candidate.normalized_name).first()
            if existing:
                logger.info(f"Candidate '{candidate_id}' was already approved; returning existing canonical scheme '{existing.scheme_id}'.")
                return existing
            raise ValueError(f"Candidate '{candidate_id}' has already been approved.")

        can_p, reason = cls.can_promote(candidate)
        if not can_p:
            raise ValueError(f"Cannot promote candidate '{candidate_id}': {reason}")

        now = datetime.utcnow()
        today_str = now.strftime("%Y-%m-%d")

        # Idempotency: check if canonical scheme already exists for this URL or normalized name
        existing_canonical = None
        if candidate.official_source_url:
            existing_canonical = db.query(Scheme).filter(Scheme.official_source_url == candidate.official_source_url).first()
        if not existing_canonical and candidate.normalized_name:
            existing_canonical = db.query(Scheme).filter(Scheme.scheme_name == candidate.normalized_name).first()

        if existing_canonical:
            candidate.candidate_status = "APPROVED"
            candidate.reviewed_at = now
            candidate.reviewed_by = reviewer_id
            candidate.admin_notes = (notes or "") + f" [Linked to existing canonical scheme {existing_canonical.scheme_id}]"
            try:
                db.commit()
                db.refresh(candidate)
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to link candidate '{candidate_id}' to existing scheme: {e}")
                raise
            logger.info(f"Candidate '{candidate_id}' matches existing canonical scheme '{existing_canonical.scheme_id}'; idempotently linked without duplicate creation.")
            return existing_canonical

        # Parse candidate payload
        try:
            extracted: Dict[str, Any] = json.loads(candidate.extracted_data) if candidate.extracted_data else {}
        except Exception:
            extracted = {}

        try:
            evidence: Dict[str, Any] = json.loads(candidate.evidence) if candidate.evidence else {}
        except Exception:
            evidence = {}

        # 1. Generate canonical ID
        new_scheme_id = cls.generate_next_scheme_id(db)

        # 2. Build canonical Scheme instance
        scheme_name = candidate.normalized_name or candidate.discovered_name
        scheme_code = candidate.scheme_code if candidate.scheme_code != "UNKNOWN" else new_scheme_id

        # Financial values & sentinels
        max_loan = extracted.get("max_loan_amount")
        min_loan = extracted.get("min_loan_amount")
        max_proj = extracted.get("max_project_cost")
        subsidy_pct = extracted.get("subsidy_percentage")
        int_max = extracted.get("interest_rate_max")
        int_min = extracted.get("interest_rate_min")
        income_lim = extracted.get("income_limit")

        # Loan availability sentinel
        if max_loan is not None and max_loan > 0:
            loan_avail = "YES"
        elif "loan" in (candidate.stated_benefits or "").lower() or "credit" in (candidate.stated_benefits or "").lower():
            loan_avail = "YES"
        else:
            loan_avail = "NO"

        # Subsidy availability sentinel
        subsidy_avail = "YES" if (subsidy_pct is not None and subsidy_pct > 0) else "NO"

        new_scheme = Scheme(
            scheme_id=new_scheme_id,
            scheme_code=scheme_code,
            scheme_name=scheme_name,
            scheme_type=candidate.level,
            source_organization=candidate.implementing_agency or candidate.ministry,
            ministry=candidate.ministry,
            implementing_agency=candidate.implementing_agency,
            scheme_status="ACTIVE",
            short_description=candidate.stated_benefits or f"Government assistance under {scheme_name}.",
            detailed_description=candidate.stated_benefits,
            purpose=candidate.stated_benefits or f"Welfare and enterprise support through {scheme_name}.",
            target_beneficiary=candidate.target_beneficiaries or "Eligible Citizens / Entrepreneurs",
            applicant_types=extracted.get("applicant_types", "INDIVIDUAL, MICRO_ENTERPRISE"),
            marginalized_group=extracted.get("marginalized_group", "GENERAL"),
            target_groups=candidate.target_beneficiaries,
            social_category=extracted.get("social_category", "ALL"),
            gender_condition=extracted.get("gender_condition", "ALL"),
            gender_requirement=extracted.get("gender_requirement", "ALL"),
            age_min=extracted.get("age_min"),
            age_min_raw=extracted.get("age_min_raw", str(extracted.get("age_min")) if extracted.get("age_min") else "UNKNOWN"),
            age_max=extracted.get("age_max"),
            age_max_raw=extracted.get("age_max_raw", str(extracted.get("age_max")) if extracted.get("age_max") else "UNKNOWN"),
            income_limit=income_lim,
            income_limit_raw=extracted.get("income_limit_raw", str(income_lim) if income_lim else "NOT_APPLICABLE"),
            state_restriction=extracted.get("state_restriction", "NO" if candidate.state_coverage == "All India" else "YES"),
            state_coverage=candidate.state_coverage or "All India",
            district_restriction="NO",
            district_coverage=candidate.district_coverage or "All Districts",
            sector=candidate.sector or extracted.get("sector", "GENERAL_BUSINESS"),
            activity_type=extracted.get("activity_type", "MANUFACTURING, SERVICE, BUSINESS"),
            business_types=extracted.get("business_types", "MICRO, SMALL"),
            business_stage=extracted.get("business_stage", "NEW_OR_EXISTING"),
            new_unit_required=extracted.get("new_unit_required", "NO"),
            new_business_allowed="YES",
            existing_unit_allowed="YES",
            existing_business_allowed="YES",
            support_type=extracted.get("support_type", "CREDIT_AND_SUBSIDY" if loan_avail == "YES" else "NON_FINANCIAL"),
            benefit_description=candidate.stated_benefits,
            loan_available=loan_avail,
            min_loan_amount=min_loan,
            min_loan_amount_raw=str(min_loan) if min_loan else "NOT_APPLICABLE",
            minimum_loan_amount=min_loan,
            minimum_loan_amount_raw=str(min_loan) if min_loan else "NOT_APPLICABLE",
            max_loan_amount=max_loan,
            max_loan_amount_raw=extracted.get("max_loan_amount_raw", str(max_loan) if max_loan else "NOT_APPLICABLE"),
            maximum_loan_amount=max_loan,
            maximum_loan_amount_raw=extracted.get("max_loan_amount_raw", str(max_loan) if max_loan else "NOT_APPLICABLE"),
            max_project_cost=max_proj,
            max_project_cost_raw=str(max_proj) if max_proj else "NOT_APPLICABLE",
            subsidy_available=subsidy_avail,
            subsidy_percentage=subsidy_pct,
            subsidy_percentage_raw=extracted.get("subsidy_percentage_raw", str(subsidy_pct) if subsidy_pct else "NOT_APPLICABLE"),
            interest_rate_max=int_max,
            interest_rate_max_raw=extracted.get("interest_rate_max_raw", str(int_max) if int_max else "UNKNOWN"),
            interest_rate_min=int_min,
            interest_rate_min_raw=str(int_min) if int_min else "UNKNOWN",
            application_mode=extracted.get("application_mode", "ONLINE_PORTAL"),
            application_url=candidate.discovery_url or candidate.official_source_url,
            official_portal=candidate.official_source_url,
            required_documents=extracted.get("required_documents", "Aadhaar Card, Bank Account Details, Project Report"),
            official_source_url=candidate.official_source_url,
            source_document=candidate.source_document or "Official Government Scheme Guidelines",
            scheme_version="1.0",
            previous_version=None,
            last_verified_date=today_str,
            created_at=now,
            updated_at=now
        )
        db.add(new_scheme)
        db.flush()

        # 3. Generate SchemeRule records
        rules = SchemeRuleGenerator.generate_rules_for_scheme(
            scheme_id=new_scheme.scheme_id,
            data=extracted,
            source_doc=new_scheme.source_document
        )
        for r in rules:
            db.add(r)

        # 4. Generate SchemeDocument records
        docs = SchemeDocumentGenerator.generate_documents_for_scheme(
            scheme_id=new_scheme.scheme_id,
            data=extracted,
            source_doc=new_scheme.source_document
        )
        for d in docs:
            db.add(d)

        # 5. Create SchemeVerification record
        verif_id = f"VERIF-{new_scheme.scheme_id}-{uuid.uuid4().hex[:4]}"
        verif = SchemeVerification(
            id=verif_id,
            scheme_id=new_scheme.scheme_id,
            verification_status="VERIFIED",
            last_verified_date=today_str,
            data_confidence="HIGH",
            notes=notes or f"Promoted candidate '{candidate.candidate_id}' to canonical record after administrative approval.",
            normalization_note="Validated and normalized via Dynamic Large-Scale Scheme Ingestion Pipeline.",
            created_at=now
        )
        db.add(verif)

        # 6. Create SchemeChangelog entry
        changelog = SchemeChangelog(
            scheme_id=new_scheme.scheme_id,
            action="INITIAL_CANONICAL_INGESTION",
            field="ALL",
            old_value=None,
            new_value="CANONICAL_CREATED",
            reason=notes or f"Approved candidate {candidate.candidate_id} via large-scale intelligence pipeline.",
            admin_identifier=reviewer_id,
            source_url=candidate.official_source_url,
            source_document=new_scheme.source_document,
            verification_status="VERIFIED",
            created_at=now
        )
        db.add(changelog)

        # 7. Register in SchemeSource for continuous monitoring
        existing_src = db.query(SchemeSource).filter(SchemeSource.source_url == candidate.official_source_url).first()
        if not existing_src:
            src = SchemeSource(
                source_id=f"SRC-{new_scheme.scheme_id}-{uuid.uuid4().hex[:4]}",
                scheme_id=new_scheme.scheme_id,
                source_name=f"{new_scheme.scheme_name} Official Portal",
                source_url=candidate.official_source_url,
                authority=candidate.ministry,
                source_type=candidate.source_type,
                fetch_frequency_hours=24,
                is_active=True,
                last_status="SUCCESS",
                last_fetched_at=now
            )
            db.add(src)

        # 8. Update Candidate Scheme Status
        candidate.candidate_status = "APPROVED"
        candidate.reviewed_at = now
        candidate.reviewed_by = reviewer_id
        candidate.admin_notes = notes

        try:
            db.commit()
            db.refresh(new_scheme)
            db.refresh(candidate)
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction rolled back during candidate promotion for '{candidate_id}': {e}")
            raise

        # 9. Trigger instant RAG vector store re-indexing
        if sync_rag:
            try:
                IngestionSyncService.sync_rag_knowledge(db, new_scheme)
            except Exception as e:
                logger.warning(f"RAG re-indexing warning for newly promoted scheme {new_scheme.scheme_id}: {e}")

        logger.info(f"Successfully promoted candidate '{candidate_id}' to canonical scheme '{new_scheme.scheme_id}'!")
        return new_scheme
