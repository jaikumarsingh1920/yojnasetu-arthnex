import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Scheme, SchemeRule, SchemeDocument
from app.schemas.ai import SourceCitation

logger = logging.getLogger("yojnasetu.ai.rag")


class SchemeVectorStore:
    """
    Retrieval-Augmented Generation (RAG) vector store for verified scheme data & documents.
    Uses TF-IDF + metadata relevance ranking over authoritative scheme database records.
    Returns traceable SourceCitation objects.
    """

    def __init__(self, db: Session):
        self.db = db
        self._chunks: List[Dict[str, Any]] = []
        self._build_index()

    def _build_index(self):
        """Indexes all verified Schemes, SchemeRules, and SchemeDocuments into searchable context chunks."""
        schemes = self.db.query(Scheme).filter(
            or_(Scheme.scheme_status == "ACTIVE", Scheme.scheme_status == None, Scheme.scheme_status == "")
        ).all()
        chunks: List[Dict[str, Any]] = []

        for sch in schemes:
            # 1. Scheme General Metadata Chunk
            meta_text = (
                f"{sch.scheme_name} is implemented by {sch.ministry or sch.implementing_agency or 'the Government of India'}. "
                f"Objective: {sch.purpose or sch.short_description or sch.scheme_name}. "
                f"Target Beneficiaries: {sch.target_beneficiary or sch.target_groups or 'All eligible citizens'}. "
                f"State Coverage: {sch.state_coverage or sch.state_restriction or 'All India'}."
            )
            chunks.append({
                "scheme_id": sch.scheme_id,
                "scheme_code": sch.scheme_id,
                "scheme_name": sch.scheme_name,
                "source_type": "SCHEME_METADATA",
                "source_document": getattr(sch, 'source_document', None) or 'Official Scheme Guidelines',
                "rule_id": None,
                "text": meta_text,
            })

            # 2. Scheme Financial Assistance Chunk
            is_credit = getattr(sch, 'is_credit_scheme', True)
            if is_credit:
                fin_type = "Credit / Loan Facility"
                max_loan = f"₹{sch.max_loan_amount:,.0f}" if getattr(sch, 'max_loan_amount', None) else "As per project appraisal / not specified in available official guidelines"
                rate_val = getattr(sch, 'interest_rate', None) or getattr(sch, 'interest_rate_max', None)
                rate = f"{rate_val}% p.a." if rate_val is not None else "As determined by financing institution / not specified in available official guidelines"
            else:
                fin_type = f"Grant / Subsidy / Welfare Assistance (No Loan) — {getattr(sch, 'financial_category', 'DIRECT_BENEFIT')}"
                max_loan = "Loan facility not applicable"
                rate = "Loan interest not applicable"

            subsidy = f"{sch.subsidy_percentage}%" if getattr(sch, 'subsidy_percentage', None) else "Refer to official scheme guidelines"
            tenure_val = getattr(sch, 'repayment_period_max_months', None) or getattr(sch, 'repayment_period_min_months', None)
            tenure_str = f"up to {tenure_val} months" if tenure_val else "Not specified in available official guidelines"
            
            fin_text = (
                f"Financial details for {sch.scheme_name}: Facility type is {fin_type}. "
                f"Maximum support available is {max_loan} with interest rate at {rate} and capital subsidy up to {subsidy}. "
                f"Repayment period is {tenure_str}. "
                f"{getattr(sch, 'benefit_description', None) or getattr(sch, 'financial_assistance_summary', None) or 'Official Financial Support'}"
            )
            chunks.append({
                "scheme_id": sch.scheme_id,
                "scheme_code": sch.scheme_id,
                "scheme_name": sch.scheme_name,
                "source_type": "SCHEME_FINANCIALS",
                "source_document": getattr(sch, 'source_document', None) or 'Official Financial Guidelines',
                "rule_id": None,
                "text": fin_text,
            })

            # 3. Scheme Rules Chunks
            rules = self.db.query(SchemeRule).filter(SchemeRule.scheme_id == sch.scheme_id).all()
            for r in rules:
                raw_desc = r.error_message or f"Requirement condition for {r.field} must be satisfied."
                # Clean any internal database identifiers, rule codes, or enum tokens
                clean_desc = re.sub(r"Rule\s+Code:\s*\w+[-_]?\d*", "", raw_desc, flags=re.IGNORECASE)
                clean_desc = re.sub(r"\bRULE[-_]?\d+\b", "", clean_desc, flags=re.IGNORECASE)
                clean_desc = re.sub(r"Field:\s*[\w_]+\s*(?:IN|==|!=|>|<|>=|<=)?\s*[^;\.\n]+(?:;|\.|\n|$)", "", clean_desc, flags=re.IGNORECASE)
                clean_desc = re.sub(r"Requirement\s+Field:\s*\w+", "", clean_desc, flags=re.IGNORECASE)
                clean_desc = re.sub(r"Requirement\s+Value:\s*[^;\.\n]+", "", clean_desc, flags=re.IGNORECASE)
                clean_desc = re.sub(r"\b(?:PM_SURAJ|AUTHORISED_SCA|AUTHORISED_CA)\b", "Authorized Partner Portal", clean_desc, flags=re.IGNORECASE)
                clean_desc = re.sub(r"\bDescription:\s*", "", clean_desc, flags=re.IGNORECASE)
                clean_desc = re.sub(r"[ \t]{2,}", " ", clean_desc).strip()

                rule_text = (
                    f"Official eligibility guideline for {sch.scheme_name}: "
                    f"{clean_desc or f'Eligibility requirement for {sch.scheme_name}.'}"
                )
                chunks.append({
                    "scheme_id": sch.scheme_id,
                    "scheme_code": sch.scheme_id,
                    "scheme_name": sch.scheme_name,
                    "source_type": "SCHEME_RULE",
                    "source_document": r.source_document or 'Official Statutory Rules',
                    "rule_id": str(r.rule_id),
                    "text": rule_text,
                })

            # 4. Scheme Documents Chunks
            docs = self.db.query(SchemeDocument).filter(SchemeDocument.scheme_id == sch.scheme_id).all()
            for doc in docs:
                doc_text = (
                    f"Document guidance for {sch.scheme_name}: "
                    f"Required paper: {doc.document_name} ({doc.requirement_type}). "
                    f"{doc.condition or 'Must be submitted during application verification.'}"
                )
                chunks.append({
                    "scheme_id": sch.scheme_id,
                    "scheme_code": sch.scheme_id,
                    "scheme_name": sch.scheme_name,
                    "source_type": "SCHEME_DOCUMENT",
                    "source_document": doc.document_name,
                    "rule_id": None,
                    "text": doc_text,
                })

            # 5. Application Guidance & Provenance Chunk
            app_text = (
                f"Official application process for {sch.scheme_name}: "
                f"Submissions are handled via {sch.application_mode or 'ONLINE'} mode through official portal ({sch.official_portal or 'Official Ministry Portal'}). "
                f"Verification Status: Verified Government Scheme."
            )
            chunks.append({
                "scheme_id": sch.scheme_id,
                "scheme_code": sch.scheme_id,
                "scheme_name": sch.scheme_name,
                "source_type": "APPLICATION_GUIDANCE",
                "source_document": sch.official_source_url or 'Official Gazette Portal',
                "rule_id": None,
                "text": app_text,
            })

        self._chunks = chunks
        logger.info("RAG Vector Store indexed %d scheme context chunks.", len(chunks))

    def search(
        self,
        query: str,
        scheme_id: Optional[str] = None,
        top_k: int = 4
    ) -> List[SourceCitation]:
        """Searches indexed scheme chunks for top relevant context citations."""
        if not self._chunks:
            return []

        # Filter by scheme_id if explicitly specified
        target_chunks = self._chunks
        if scheme_id:
            scheme_scoped = [c for c in self._chunks if c["scheme_id"] == str(scheme_id)]
            if scheme_scoped:
                target_chunks = scheme_scoped

        query_terms = set(re.findall(r"\w+", query.lower()))

        scored_chunks = []
        for chunk in target_chunks:
            text_terms = set(re.findall(r"\w+", chunk["text"].lower()))
            overlap = query_terms.intersection(text_terms)
            score = len(overlap) / (len(query_terms) + 1.0)

            # Boost exact scheme matches
            if chunk["scheme_code"].lower() in query.lower() or chunk["scheme_name"].lower() in query.lower():
                score += 0.45

            # Boost specific source types based on intent keywords
            q_str = query.lower()
            if "document" in q_str or "paper" in q_str or "certificate" in q_str:
                if chunk["source_type"] == "SCHEME_DOCUMENT":
                    score += 0.3
            elif "emi" in q_str or "interest" in q_str or "loan" in q_str or "money" in q_str or "subsidy" in q_str:
                if chunk["source_type"] == "SCHEME_FINANCIALS":
                    score += 0.3
            elif "apply" in q_str or "portal" in q_str or "how to" in q_str:
                if chunk["source_type"] == "APPLICATION_GUIDANCE":
                    score += 0.3

            if score > 0.03 or (scheme_id and chunk["scheme_id"] == scheme_id):
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        citations: List[SourceCitation] = []
        for score, chunk in scored_chunks[:top_k]:
            norm_score = min(1.0, score)
            citations.append(SourceCitation(
                scheme_id=chunk["scheme_id"],
                scheme_name=chunk["scheme_name"],
                source_type=chunk["source_type"],
                source_document=chunk["source_document"],
                rule_id=chunk["rule_id"],
                snippet=chunk["text"][:400],
                relevance_score=round(norm_score, 2)
            ))

        return citations
