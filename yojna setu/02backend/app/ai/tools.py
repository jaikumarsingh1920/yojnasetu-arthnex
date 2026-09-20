import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.scheme import Scheme
from app.models.application import Application
from app.schemas.recommendation import BeneficiaryProfileInput, RecommendationRequest
from app.schemas.financial import FinancialCalculationInput
from app.engine import DeterministicFinancialEngine, DeterministicEligibilityEngine, DeterministicRecommendationEngine

logger = logging.getLogger("yojnasetu.ai.tools")


class CopilotTools:
    """
    Typed, safe internal tools invoked by the GPT-level AI Copilot.
    All eligibility, financial, scheme parameters, and application state queries
    must execute through these tools.
    Zero direct LLM database mutations.
    """

    @staticmethod
    def search_schemes(
        db: Session,
        query: Optional[str] = None,
        state: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Searches master schemes by text query, state, and target category."""
        q = db.query(Scheme)
        if query:
            pattern = f"%{query.strip()}%"
            q = q.filter(
                (Scheme.scheme_name.ilike(pattern)) |
                (Scheme.purpose.ilike(pattern)) |
                (Scheme.target_groups.ilike(pattern))
            )
        if state and state.upper() != "ALL_INDIA":
            q = q.filter((Scheme.state_coverage == "ALL_INDIA") | (Scheme.state_coverage.ilike(f"%{state}%")))

        schemes = q.limit(limit).all()
        return [
            {
                "scheme_id": s.scheme_id,
                "scheme_name": s.scheme_name,
                "ministry": s.ministry or s.implementing_agency,
                "purpose": s.purpose or s.short_description,
                "target_groups": s.target_groups,
                "state_coverage": s.state_coverage or "ALL_INDIA"
            }
            for s in schemes
        ]

    @staticmethod
    def get_scheme_details(db: Session, scheme_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves authoritative metadata, rules, and documents for a scheme."""
        sch = db.query(Scheme).filter(Scheme.scheme_id == scheme_id).first()
        if not sch:
            return None

        rules = [
            {
                "rule_id": r.rule_id,
                "field": r.field,
                "operator": r.operator,
                "value": r.value,
                "description": r.error_message
            }
            for r in sch.rules
        ]
        documents = [
            {
                "document_name": d.document_name,
                "requirement_type": d.requirement_type,
                "condition": d.condition
            }
            for d in sch.documents if d.active
        ]

        return {
            "scheme_id": sch.scheme_id,
            "scheme_name": sch.scheme_name,
            "ministry": sch.ministry or sch.implementing_agency or "Government of India",
            "purpose": sch.purpose or sch.short_description,
            "detailed_description": sch.detailed_description,
            "target_beneficiary": sch.target_beneficiary,
            "target_groups": sch.target_groups,
            "sector": sch.sector,
            "activity_type": sch.activity_type,
            "business_stage": sch.business_stage,
            "state_coverage": sch.state_coverage or "ALL_INDIA",
            "age_min": sch.age_min,
            "age_max": sch.age_max,
            "income_limit": float(sch.income_limit) if sch.income_limit is not None else None,
            "financial_category": sch.financial_category,
            "is_credit_scheme": sch.is_credit_scheme,
            "max_loan_amount": float(sch.max_loan_amount) if sch.max_loan_amount is not None else None,
            "min_loan_amount": float(sch.min_loan_amount) if sch.min_loan_amount is not None else None,
            "max_project_cost": float(sch.max_project_cost) if sch.max_project_cost is not None else None,
            "min_project_cost": float(sch.min_project_cost) if sch.min_project_cost is not None else None,
            "subsidy_percentage": float(sch.subsidy_percentage) if sch.subsidy_percentage is not None else None,
            "subsidy_details": sch.subsidy_details,
            "interest_rate": float(sch.interest_rate) if sch.interest_rate is not None else None,
            "interest_rate_max": float(sch.interest_rate_max) if sch.interest_rate_max is not None else None,
            "repayment_period_max_months": sch.repayment_period_max_months,
            "margin_money_percentage": sch.margin_money_percentage,
            "collateral_required": sch.collateral_required,
            "application_route": sch.application_route,
            "application_url": sch.application_url,
            "official_portal": sch.official_portal,
            "official_source_url": sch.official_source_url,
            "source_document": sch.source_document,
            "partner_mappings_count": len(sch.partner_mappings) if sch.partner_mappings else 0,
            "has_verified_partner_mapping": bool(sch.partner_mappings and len(sch.partner_mappings) > 0),
            "verification_status": sch.scheme_status or "VERIFIED",
            "rules": rules,
            "documents": documents
        }

    @staticmethod
    def check_eligibility(db: Session, scheme_id: str, profile: BeneficiaryProfileInput) -> Dict[str, Any]:
        """Invokes DeterministicEligibilityEngine to evaluate scheme eligibility."""
        sch = db.query(Scheme).filter(Scheme.scheme_id == scheme_id).first()
        if not sch:
            return {"error": f"Scheme '{scheme_id}' not found."}

        eval_res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        passed_reasons = [r.reason for r in eval_res.hard_rules_passed]
        failed_reasons = [r.reason for r in eval_res.hard_rules_failed]
        unknown_reasons = [r.reason for r in eval_res.unknown_eligibility_rules]

        return {
            "scheme_id": sch.scheme_id,
            "scheme_name": sch.scheme_name,
            "status": eval_res.status.value,
            "is_eligible": eval_res.status.value == "ELIGIBLE",
            "matched_rules": passed_reasons,
            "failed_rules": failed_reasons,
            "missing_information": unknown_reasons,
            "explanations": eval_res.explanations,
            "hard_passed_count": len(eval_res.hard_rules_passed),
            "hard_failed_count": len(eval_res.hard_rules_failed),
            "unknown_count": len(eval_res.unknown_eligibility_rules),
            "official_source": sch.source_document or "Official Scheme Guidelines",
            "official_source_url": sch.official_source_url,
            "official_portal": sch.official_portal
        }

    @staticmethod
    def calculate_financials(
        db: Session,
        scheme_id: str,
        project_cost: float = 100000.0,
        requested_loan_amount: float = 80000.0
    ) -> Dict[str, Any]:
        """Invokes DeterministicFinancialEngine for EMI and subsidy calculation."""
        fin_req = FinancialCalculationInput(
            scheme_id=scheme_id,
            project_cost=project_cost,
            requested_loan_amount=requested_loan_amount
        )
        calc_res = DeterministicFinancialEngine.calculate(db, fin_req)
        return calc_res.model_dump()

    @staticmethod
    def get_recommendations(db: Session, profile: BeneficiaryProfileInput, top_k: int = 5) -> Dict[str, Any]:
        """Invokes DeterministicRecommendationEngine to score and rank schemes for profile."""
        rec_req = RecommendationRequest(profile=profile, limit=top_k, min_soft_score=0.0)
        rec_res = DeterministicRecommendationEngine.get_recommendations(db, rec_req)
        return rec_res.model_dump()

    @staticmethod
    def resolve_scheme_by_name(db: Session, text: str) -> Optional[Scheme]:
        """Dynamically resolves a Scheme model by acronym, common alias, or title substring."""
        if not text:
            return None
        text_clean = text.lower().strip()

        # Known authoritative acronyms
        alias_map = {
            "pmegp": "SIH26092-001",
            "mudra": "SIH26092-002",
            "pmmy": "SIH26092-002",
            "stand up india": "SIH26092-003",
            "stand-up india": "SIH26092-003",
            "standup india": "SIH26092-003",
            "standup": "SIH26092-003",
            "svanidhi": "SIH26092-004",
            "pm svanidhi": "SIH26092-004",
            "vishwakarma": "SIH26092-005",
            "pm vishwakarma": "SIH26092-005",
            "nsfdc": "SIH26092-052",
        }
        for alias, sid in alias_map.items():
            if re.search(r"\b" + re.escape(alias) + r"\b", text_clean):
                sch = db.query(Scheme).filter(Scheme.scheme_id == sid).first()
                if sch:
                    return sch

        # Match by distinctive words in title (excluding generic stop words)
        GENERIC_STOPWORDS = {
            "loan", "yojna", "yojana", "scheme", "batao", "chahiye", "isme", "iske", "iski", "iska",
            "usme", "uska", "uski", "karna", "start", "business", "detail", "details", "subsidy", "capital",
            "credit", "finance", "financial", "india", "bharat", "pradhan", "mantri", "national", "state",
            "central", "government", "sarkar", "sarkari", "online", "apply", "document", "documents",
            "eligibility", "eligible", "patra", "patrata", "kya", "hai", "kitna", "kitni", "saal", "year",
            "years", "lakh", "lakhs", "crore", "about", "which", "what", "where", "when", "tell", "need",
            "give", "help", "hogi", "hoga", "hain", "kare", "karen", "kaise", "milega", "milti",
            "month", "months", "monthly", "income", "expense", "expenses", "around", "already",
            "obligation", "obligations", "repay", "repayment", "afford", "affordability", "living",
            "household", "family", "salary", "salaried", "earning", "earnings", "rupees", "amount",
            "borrow", "borrowing", "person", "persons", "people", "existing", "current", "currently",
            "active", "pending", "previous", "exist"
        }
        tokens = [t for t in re.findall(r"\w+", text_clean) if len(t) >= 5 and t not in GENERIC_STOPWORDS]
        for t in tokens:
            sch = db.query(Scheme).filter(Scheme.scheme_name.ilike(f"%{t}%")).first()
            if sch:
                return sch
        return None

    @staticmethod
    def compare_schemes(db: Session, scheme_ids: List[str]) -> List[Dict[str, Any]]:
        """Compares multiple schemes side-by-side."""
        results = []
        for sid in scheme_ids[:4]:
            details = CopilotTools.get_scheme_details(db, sid)
            if details:
                results.append(details)
        return results

    @staticmethod
    def compare_schemes_structured(db: Session, scheme_ids: List[str]) -> Dict[str, Any]:
        """
        Authoritative side-by-side comparison of schemes across 10 structured dimensions:
        1. Eligibility
        2. Funding / Project Cost
        3. Capital Subsidy
        4. Interest Rate
        5. Repayment Tenure
        6. Collateral Requirement
        7. Target Beneficiaries
        8. Application Channel
        9. Geography
        10. Business Stage
        """
        schemes = db.query(Scheme).filter(Scheme.scheme_id.in_(scheme_ids[:4])).all()
        if not schemes:
            return {"schemes": [], "dimensions": []}

        items = []
        for s in schemes:
            # Funding limit
            if s.max_loan_amount and s.max_loan_amount > 0:
                funding_str = f"Up to ₹{s.max_loan_amount:,.0f}"
                if s.max_project_cost and s.max_project_cost > s.max_loan_amount:
                    funding_str += f" (Project Cost up to ₹{s.max_project_cost:,.0f})"
            elif s.max_project_cost and s.max_project_cost > 0:
                funding_str = f"Project Cost up to ₹{s.max_project_cost:,.0f}"
            else:
                funding_str = "As per project appraisal / guidelines"

            # Capital Subsidy
            if s.subsidy_percentage and s.subsidy_percentage > 0:
                sub_str = f"{s.subsidy_percentage}% on eligible project cost"
                if "pmegp" in s.scheme_name.lower():
                    sub_str = "15% - 25% (General) / 25% - 35% (Special Category SC/ST/OBC/Women)"
            else:
                sub_str = "No capital subsidy (Credit/Assistance facility)"

            # Interest Rate
            if s.interest_rate is not None and s.interest_rate > 0:
                int_str = f"{s.interest_rate}% p.a. (Concessional)"
                if "vishwakarma" in s.scheme_name.lower():
                    int_str = "5.0% p.a. (Concessional with 8% GoI subvention)"
            elif s.interest_rate == 0.0:
                int_str = "0% (Interest-Free)"
            else:
                int_str = "Commercial Bank lending rates (RBI/MCLR linked, approx 8.5% - 11.5% p.a.)"

            # Repayment
            if s.repayment_period_max_months:
                yrs = s.repayment_period_max_months // 12
                rem_m = s.repayment_period_max_months % 12
                rep_str = f"Up to {yrs} years" + (f" {rem_m} months" if rem_m else "")
            else:
                rep_str = "3 to 5 years standard bank tenure"

            # Collateral
            if s.collateral_required is False:
                coll_str = "Collateral-free (Covered under Credit Guarantee Trust CGTMSE / CGFMU)"
            elif s.collateral_required is True:
                coll_str = "Collateral / third-party guarantee required as per bank policy"
            else:
                coll_str = "Collateral-free for loans up to statutory threshold (₹10 Lakh under RBI guidelines)"

            # Business stage
            stage_str = "New Units (Greenfield)" if "pmegp" in s.scheme_name.lower() else "New and Existing Enterprises"

            items.append({
                "scheme_id": s.scheme_id,
                "scheme_name": s.scheme_name,
                "ministry": s.ministry or "Government of India",
                "eligibility": s.target_groups or "Indian citizens meeting statutory criteria",
                "funding": funding_str,
                "subsidy": sub_str,
                "interest": int_str,
                "repayment": rep_str,
                "collateral": coll_str,
                "target_users": s.target_groups or "Micro & Small Entrepreneurs",
                "application_channel": f"Online portal ({s.official_portal or 'Official Portal'}) & Authorized Bank Branches",
                "geography": s.state_coverage or "All-India",
                "business_stage": stage_str,
                "official_portal": s.official_portal,
                "official_source": s.source_document or "Official Scheme Guidelines"
            })

        return {
            "schemes": items,
            "compared_count": len(items)
        }

    @staticmethod
    def get_application_status(db: Session, application_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
        """Gets application status with authorization check."""
        q = db.query(Application).filter(Application.application_id == application_id)
        if current_user_id:
            q = q.filter(Application.user_id == current_user_id)
        app_obj = q.first()

        if not app_obj:
            return {"error": "Application not found or unauthorized access."}

        return {
            "application_id": app_obj.application_id,
            "scheme_id": app_obj.scheme_id,
            "status": app_obj.status,
            "created_at": app_obj.created_at.strftime("%Y-%m-%d %H:%M"),
            "updated_at": app_obj.updated_at.strftime("%Y-%m-%d %H:%M"),
            "documents_count": len(app_obj.documents)
        }
