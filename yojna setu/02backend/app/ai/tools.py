import logging
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
            "ministry": sch.ministry or sch.implementing_agency,
            "purpose": sch.purpose or sch.short_description,
            "target_groups": sch.target_groups,
            "state_coverage": sch.state_coverage or "ALL_INDIA",
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
        return {
            "scheme_id": sch.scheme_id,
            "scheme_name": sch.scheme_name,
            "status": eval_res.status.value,
            "is_eligible": eval_res.status.value == "ELIGIBLE",
            "explanations": eval_res.explanations,
            "hard_passed_count": len(eval_res.hard_rules_passed),
            "hard_failed_count": len(eval_res.hard_rules_failed)
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
    def compare_schemes(db: Session, scheme_ids: List[str]) -> List[Dict[str, Any]]:
        """Compares multiple schemes side-by-side."""
        results = []
        for sid in scheme_ids[:3]:
            details = CopilotTools.get_scheme_details(db, sid)
            if details:
                results.append(details)
        return results

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
