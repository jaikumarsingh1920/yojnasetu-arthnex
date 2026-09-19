import pytest
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.recommendation import RecommendationRequest
from app.engine.recommendation import DeterministicRecommendationEngine
from app.models.scheme import Scheme
from app.db.session import SessionLocal


def test_ineligible_scheme_never_receives_affirmative_score():
    """CRITICAL INVARIANT: Ineligible schemes must NEVER receive an affirmative fit score (must be 0.0)."""
    db = SessionLocal()
    try:
        # Profile: wealthy applicant with 5,000,000 income, 75 years old
        # Guaranteed to fail nearly all government subsidized loan schemes
        wealthy_elderly_profile = BeneficiaryProfileInput(
            annual_income=5000000.0,
            age=75,
            state="UTTAR_PRADESH",
            social_category="GENERAL"
        )

        req = RecommendationRequest(profile=wealthy_elderly_profile, top_k=5)
        response = DeterministicRecommendationEngine.get_recommendations(db, req)

        # Ineligible schemes list
        assert len(response.ineligible_schemes) > 0, "Should have identified ineligible schemes"
        for item in response.ineligible_schemes:
            assert item.score == 0.0, f"Ineligible scheme {item.scheme_id} must have score 0.0, got {item.score}"
            assert item.eligible is False, f"Ineligible scheme {item.scheme_id} must have eligible=False"
            assert item.eligibility_status == "INELIGIBLE"
            assert len(item.failed_rules) > 0, f"Ineligible scheme {item.scheme_id} must expose exact failed rules"
    finally:
        db.close()


def test_eligible_scheme_score_transparency_and_structure():
    """Verify recommendation response exposes all required audit components."""
    db = SessionLocal()
    try:
        # Standard eligible profile: 25 yo rural artisan in UP
        profile = BeneficiaryProfileInput(
            age=25,
            gender="FEMALE",
            annual_income=120000.0,
            state="UTTAR_PRADESH",
            social_category="OBC",
            is_artisan=True,
            requested_loan_amount=50000.0,
            sector="HANDICRAFTS"
        )

        req = RecommendationRequest(profile=profile, top_k=5)
        response = DeterministicRecommendationEngine.get_recommendations(db, req)

        assert len(response.recommendations) > 0, "Should return eligible recommendations"
        for item in response.recommendations:
            # 1. Scheme ID
            assert item.scheme_id is not None
            # 2. Eligibility status & reasons
            assert item.eligibility_status == "ELIGIBLE"
            assert item.eligible is True
            assert isinstance(item.eligibility_reasons, list)
            assert len(item.eligibility_reasons) > 0
            # 3. Soft-fit score & score breakdown
            assert item.score >= 0.0
            assert isinstance(item.score_breakdown, list)
            assert len(item.score_breakdown) > 0
            # 4. Final rank
            assert item.rank >= 1
    finally:
        db.close()
