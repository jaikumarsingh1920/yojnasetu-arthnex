import pytest
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.engine.relevance_policy import (
    SIH26092RecommendationRelevancePolicy,
    SIH26092RecommendationStatus
)
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.recommendation import RecommendationRequest
from app.engine.recommendation import DeterministicRecommendationEngine


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_out_of_scope_schemes_excluded_from_recommendation_universe(db_session):
    """Pilgrimage tours and sports prize schemes must be classified as OUT_OF_SCOPE."""
    # 1. Sri Lanka's Sita Temple Tour
    sita = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-407").first()
    assert sita is not None
    is_el, status, _ = SIH26092RecommendationRelevancePolicy.is_recommendation_universe_eligible(sita)
    assert not is_el
    assert status == SIH26092RecommendationStatus.OUT_OF_SCOPE

    # 2. Hinglaj Devi Temple Yatra
    hinglaj = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-422").first()
    assert hinglaj is not None
    is_el, status, _ = SIH26092RecommendationRelevancePolicy.is_recommendation_universe_eligible(hinglaj)
    assert not is_el
    assert status == SIH26092RecommendationStatus.OUT_OF_SCOPE

    # 3. Sports Excellence Cash Award
    sports = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-354").first()
    assert sports is not None
    is_el, status, _ = SIH26092RecommendationRelevancePolicy.is_recommendation_universe_eligible(sports)
    assert not is_el
    assert status == SIH26092RecommendationStatus.OUT_OF_SCOPE


def test_core_schemes_are_directly_relevant(db_session):
    """Core enterprise credit and marginalized empowerment schemes must be DIRECTLY_RELEVANT."""
    pmegp = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert pmegp is not None
    is_el, status, _ = SIH26092RecommendationRelevancePolicy.is_recommendation_universe_eligible(pmegp)
    assert is_el
    assert status == SIH26092RecommendationStatus.DIRECTLY_RELEVANT


def test_recommendation_engine_excludes_out_of_scope_schemes(db_session):
    """Verify that get_recommendations never returns out-of-scope schemes even with matching profile."""
    profile = BeneficiaryProfileInput(
        state="Madhya Pradesh",
        age=65,
        social_category="GENERAL",
        gender="MALE",
        annual_income=100000.0
    )
    req = RecommendationRequest(profile=profile, top_k=100)
    res = DeterministicRecommendationEngine.get_recommendations(db_session, req)

    rec_ids = {rec.scheme_id for rec in res.recommendations}
    assert "SIH26092-407" not in rec_ids, "Sita Temple Tour must not appear in recommendations"
    assert "SIH26092-422" not in rec_ids, "Hinglaj Devi Temple Yatra must not appear in recommendations"
    assert "SIH26092-354" not in rec_ids, "Sports cash award must not appear in recommendations"
