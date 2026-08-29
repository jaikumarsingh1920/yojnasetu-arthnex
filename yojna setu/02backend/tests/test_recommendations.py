import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from app.main import app
from app.models import Base, Scheme
from app.db.session import get_db
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.recommendation import RecommendationRequest
from app.engine.recommendation import DeterministicRecommendationEngine, SCORING_WEIGHTS
from seed_db import seed_database


@pytest.fixture(scope="module")
def rec_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    seed_database(session)
    session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.fixture
def sample_profile():
    return BeneficiaryProfileInput(
        age=28,
        annual_income=180000.0,
        social_category="SC",
        is_sc=True,
        gender="MALE",
        state="MAHARASHTRA",
        applicant_type="INDIVIDUAL",
        business_stage="NEW",
        is_new_unit=True,
        sector="MICRO_FINANCE",
        activity_type="SMALL_MICRO_BUSINESS",
        project_cost=100000.0,
        requested_loan_amount=90000.0,
    )


# ─────────────────────────────────────────────────────────────────
# 1. ELIGIBILITY INTEGRATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_evaluate_all_56_schemes(rec_client, sample_profile):
    _, session_factory = rec_client
    db = session_factory()
    req = RecommendationRequest(profile=sample_profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert res.evaluated_scheme_count == 56
    assert res.eligible_scheme_count > 0
    assert res.excluded_scheme_count > 0
    assert res.eligible_scheme_count + res.excluded_scheme_count + res.insufficient_info_scheme_count == 56


def test_hard_ineligible_schemes_excluded(rec_client):
    """Profile with high income (₹10,000,000) exceeds all income ceilings."""
    _, session_factory = rec_client
    db = session_factory()
    high_income_profile = BeneficiaryProfileInput(
        age=30,
        annual_income=10000000.0,  # Exceeds income limit of all schemes with income ceilings
        social_category="GENERAL",
        is_sc=False,
    )
    req = RecommendationRequest(profile=high_income_profile, top_k=10)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    for item in res.recommendations:
        assert item.eligibility_status == "ELIGIBLE"
        assert item.scheme_id not in [s.scheme_id for s in db.query(Scheme).all() if s.income_limit and s.income_limit < 10000000.0]


# ─────────────────────────────────────────────────────────────────
# 2. SCORING DIMENSION TESTS
# ─────────────────────────────────────────────────────────────────

def test_scoring_weights_total_100():
    """Verify sum of configured weights equals exactly 100.0."""
    total_weight = sum(SCORING_WEIGHTS.values())
    assert total_weight == 100.0


def test_matching_dimensions_increase_score(rec_client, sample_profile):
    _, session_factory = rec_client
    db = session_factory()

    # Base profile
    req_base = RecommendationRequest(profile=sample_profile, top_k=50)
    res_base = DeterministicRecommendationEngine.get_recommendations(db, req_base)

    # Sparse profile with missing fields
    sparse_profile = BeneficiaryProfileInput(
        age=28,
        annual_income=180000.0,
        social_category="SC",
        is_sc=True,
    )
    req_sparse = RecommendationRequest(profile=sparse_profile, top_k=50)
    res_sparse = DeterministicRecommendationEngine.get_recommendations(db, req_sparse)

    db.close()

    mfs_base = next(r for r in res_base.recommendations if r.scheme_id == "SIH26092-052")
    mfs_sparse = next(r for r in res_sparse.recommendations if r.scheme_id == "SIH26092-052")

    # Rich matching profile yields more matched factors than sparse profile
    assert len(mfs_base.matched_factors) > len(mfs_sparse.matched_factors)


# ─────────────────────────────────────────────────────────────────
# 3. MISSING DATA & SENTINEL TESTS
# ─────────────────────────────────────────────────────────────────

def test_missing_profile_fields_tracked(rec_client):
    _, session_factory = rec_client
    db = session_factory()
    profile = BeneficiaryProfileInput(age=25, social_category="SC", is_sc=True)
    req = RecommendationRequest(profile=profile, top_k=3)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert "annual_income" in res.missing_profile_fields
    assert "sector" in res.missing_profile_fields
    assert "state" in res.missing_profile_fields
    assert "project_cost" in res.missing_profile_fields


def test_unknown_scheme_fields_not_penalized(rec_client, sample_profile):
    """Verify UNKNOWN scheme fields result in NOT_EVALUATED and are not penalized as NO_MATCH."""
    _, session_factory = rec_client
    db = session_factory()
    req = RecommendationRequest(profile=sample_profile, top_k=10)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    for item in res.recommendations:
        for breakdown in item.score_breakdown:
            if breakdown.result == "NOT_EVALUATED":
                assert breakdown.score == 0.0
                assert "UNKNOWN" in breakdown.reason or "not specified" in breakdown.reason or "NOT_APPLICABLE" in breakdown.reason


# ─────────────────────────────────────────────────────────────────
# 4. RANKING & TIE-BREAKER TESTS
# ─────────────────────────────────────────────────────────────────

def test_deterministic_ranking_order(rec_client, sample_profile):
    _, session_factory = rec_client
    db = session_factory()
    req = RecommendationRequest(profile=sample_profile, top_k=20)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    recs = res.recommendations
    for i in range(len(recs) - 1):
        # Primary: score DESC
        assert recs[i].score >= recs[i + 1].score
        # Tie-breaker: scheme_id ASC when scores are equal
        if recs[i].score == recs[i + 1].score:
            assert recs[i].scheme_id < recs[i + 1].scheme_id


def test_repeated_execution_determinism(rec_client, sample_profile):
    """Verify 50 repeated evaluations produce 100% identical rankings and scores."""
    _, session_factory = rec_client
    db = session_factory()
    req = RecommendationRequest(profile=sample_profile, top_k=5)

    first_res = DeterministicRecommendationEngine.get_recommendations(db, req)
    for _ in range(50):
        subsequent_res = DeterministicRecommendationEngine.get_recommendations(db, req)
        assert subsequent_res.eligible_scheme_count == first_res.eligible_scheme_count
        assert [r.scheme_id for r in subsequent_res.recommendations] == [r.scheme_id for r in first_res.recommendations]
        assert [r.score for r in subsequent_res.recommendations] == [r.score for r in first_res.recommendations]
    db.close()


# ─────────────────────────────────────────────────────────────────
# 5. TOP-K TESTS
# ─────────────────────────────────────────────────────────────────

def test_top_k_variations(rec_client, sample_profile):
    _, session_factory = rec_client
    db = session_factory()

    res1 = DeterministicRecommendationEngine.get_recommendations(db, RecommendationRequest(profile=sample_profile, top_k=1))
    res3 = DeterministicRecommendationEngine.get_recommendations(db, RecommendationRequest(profile=sample_profile, top_k=3))
    res5 = DeterministicRecommendationEngine.get_recommendations(db, RecommendationRequest(profile=sample_profile, top_k=5))
    res50 = DeterministicRecommendationEngine.get_recommendations(db, RecommendationRequest(profile=sample_profile, top_k=50))

    db.close()

    assert len(res1.recommendations) == 1
    assert len(res3.recommendations) == 3
    assert len(res5.recommendations) == 5
    assert len(res50.recommendations) <= res50.eligible_scheme_count


# ─────────────────────────────────────────────────────────────────
# 6. ZERO-RESULT TEST
# ─────────────────────────────────────────────────────────────────

def test_zero_eligible_schemes(rec_client, monkeypatch):
    """Verify recommendation engine handles 0 eligible schemes correctly."""
    from app.schemas.eligibility import SchemeEligibilityStatus, SchemeEligibilityResult
    from app.engine.eligibility import DeterministicEligibilityEngine

    _, session_factory = rec_client
    db = session_factory()

    def mock_ineligible(scheme, profile, active_rules=None):
        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.scheme_name,
            verification_status="VERIFIED",
            status=SchemeEligibilityStatus.INELIGIBLE,
            explanations=["Ineligible for all schemes in zero test."]
        )

    monkeypatch.setattr(DeterministicEligibilityEngine, "evaluate_scheme", mock_ineligible)

    profile = BeneficiaryProfileInput(age=5)
    req = RecommendationRequest(profile=profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert res.evaluated_scheme_count == 56
    assert res.eligible_scheme_count == 0
    assert res.recommendations == []
    assert res.excluded_scheme_count == 56


# ─────────────────────────────────────────────────────────────────
# 7. EXPLANATION & BREAKDOWN TESTS
# ─────────────────────────────────────────────────────────────────

def test_explanations_populated(rec_client, sample_profile):
    _, session_factory = rec_client
    db = session_factory()
    req = RecommendationRequest(profile=sample_profile, top_k=3)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    for rec in res.recommendations:
        assert len(rec.score_breakdown) == len(SCORING_WEIGHTS)
        assert len(rec.eligibility_reasons) > 0
        assert len(rec.recommendation_reasons) > 0
        for breakdown in rec.score_breakdown:
            assert breakdown.dimension in SCORING_WEIGHTS
            assert breakdown.result in ("MATCH", "PARTIAL_MATCH", "NO_MATCH", "NOT_EVALUATED")
            assert len(breakdown.reason) > 0


# ─────────────────────────────────────────────────────────────────
# 8. REST API ENDPOINT TESTS
# ─────────────────────────────────────────────────────────────────

def test_recommendation_api_post(rec_client):
    client, _ = rec_client
    payload = {
        "profile": {
            "age": 28,
            "annual_income": 180000.0,
            "social_category": "SC",
            "is_sc": True,
            "gender": "MALE",
            "state": "MAHARASHTRA",
            "applicant_type": "INDIVIDUAL",
            "is_new_unit": True,
            "project_cost": 100000.0,
            "requested_loan_amount": 90000.0
        },
        "top_k": 3
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["evaluated_scheme_count"] == 56
    assert data["eligible_scheme_count"] > 0
    assert len(data["recommendations"]) == 3

    # Check rank order
    recs = data["recommendations"]
    assert recs[0]["rank"] == 1
    assert recs[1]["rank"] == 2
    assert recs[2]["rank"] == 3
    assert recs[0]["score"] >= recs[1]["score"] >= recs[2]["score"]

    # Verify no internal database or security fields are leaked
    for item in recs:
        assert "hashed_password" not in item
        assert "raw_source_row" not in item


def test_recommendation_api_invalid_payload(rec_client):
    client, _ = rec_client
    # top_k = 0 invalid (ge=1)
    res = client.post("/api/v1/recommendations", json={"profile": {}, "top_k": 0})
    assert res.status_code == 422
