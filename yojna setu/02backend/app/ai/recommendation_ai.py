import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.schemas.recommendation import BeneficiaryProfileInput, RecommendationRequest
from app.schemas.ai import (
    AIExplainableRecommendationRequest,
    AIExplainableRecommendationResponse,
    AIRecommendationItem,
    SourceCitation,
)
from app.engine import (
    DeterministicEligibilityEngine,
    DeterministicFinancialEngine,
    DeterministicRecommendationEngine,
)
from app.ai.extractor import NaturalLanguageProfileExtractor
from app.ai.clarifier import ConversationalFollowUpService
from app.ai.rag import SchemeVectorStore
from app.ai.provider import get_ai_provider

logger = logging.getLogger("yojnasetu.ai.recommendation")


class AIExplainableRecommendationService:
    """
    Combines AI Natural Language understanding with authoritative backend Deterministic Engines:
    - Hard Eligibility Gate: DeterministicEligibilityEngine
    - Soft-Fit Scoring: DeterministicRecommendationEngine
    - Financial Terms: DeterministicFinancialEngine
    - RAG Knowledge: SchemeVectorStore
    """

    @classmethod
    def get_ai_recommendations(
        cls,
        db: Session,
        req: AIExplainableRecommendationRequest
    ) -> AIExplainableRecommendationResponse:
        provider = get_ai_provider()

        # 1. Profile Extraction if natural language user_text supplied
        profile = req.profile or BeneficiaryProfileInput()
        missing_fields: List[str] = []

        if req.user_text:
            extracted_res = NaturalLanguageProfileExtractor.extract_profile(req.user_text)
            # Merge extracted attributes into profile (explicit req.profile overrides)
            ext_prof = extracted_res.extracted_profile
            for field in ext_prof.model_fields.keys():
                val = getattr(ext_prof, field, None)
                if val is not None and getattr(profile, field, None) is None:
                    setattr(profile, field, val)
            missing_fields = extracted_res.missing_high_priority_fields
        else:
            high_priority = ["annual_income", "social_category", "state", "sector", "project_cost", "age"]
            missing_fields = [f for f in high_priority if getattr(profile, f, None) is None]

        # 2. Run Deterministic Recommendation Engine (Hard Eligibility + Soft-Fit Scoring)
        rec_request = RecommendationRequest(
            profile=profile,
            limit=req.top_k,
            min_soft_score=0.0
        )
        rec_response = DeterministicRecommendationEngine.get_recommendations(db, rec_request)

        # 3. RAG Search for Citations
        vector_store = SchemeVectorStore(db)

        # 4. Construct AI Recommendation Items grounded in backend calculations
        items: List[AIRecommendationItem] = []
        for idx, item in enumerate(rec_response.recommendations, start=1):
            scheme_id = item.scheme_id

            # RAG context citations
            citations = vector_store.search(
                query=f"{item.scheme_name} {item.scheme_id} eligibility financial subsidy",
                scheme_id=scheme_id,
                top_k=2
            )

            # Grounded AI explanation construction
            if item.eligibility_status == "ELIGIBLE":
                explanation = (
                    f"Recommended #{idx}: {item.scheme_name} matches your profile with a soft-fit score of {item.score:.1f}/100. "
                    f"HARD ELIGIBILITY STATUS: 100% Deterministically Eligible. "
                    f"Matched dimensions include {', '.join(item.matched_factors or ['Category', 'Sector'])}."
                )
            else:
                explanation = (
                    f"Scheme {item.scheme_name} is currently deterministically INELIGIBLE. "
                    f"REASON: {'; '.join(item.eligibility_reasons or ['Does not meet scheme eligibility rules'])}. "
                    f"AI Note: The backend deterministic engine strictly forbids claiming eligibility when rules are broken."
                )

            fin_summary = f"Scheme ID: {item.scheme_id} | Rank #{idx} | Score: {item.score:.1f}/100"

            items.append(AIRecommendationItem(
                rank=idx,
                scheme_id=scheme_id,
                scheme_name=item.scheme_name,
                eligibility_status=item.eligibility_status,
                score=item.score,
                ai_explanation=explanation,
                matched_factors=item.matched_factors,
                eligibility_reasons=item.eligibility_reasons,
                financial_fit_summary=fin_summary,
                citations=citations
            ))

        # 5. Generate Clarification Questions
        clarify_res = ConversationalFollowUpService.generate_clarifications(profile, missing_fields)

        return AIExplainableRecommendationResponse(
            evaluated_scheme_count=rec_response.evaluated_scheme_count,
            eligible_scheme_count=rec_response.eligible_scheme_count,
            recommendations=items[:req.top_k],
            missing_profile_fields=missing_fields,
            clarification_questions=clarify_res.questions,
            is_fallback=provider.is_fallback,
            provider_name=provider.name
        )
