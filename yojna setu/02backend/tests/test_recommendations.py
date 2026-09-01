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

def test_evaluate_all_schemes(rec_client, sample_profile):
    _, session_factory = rec_client
    db = session_factory()
    total_schemes = db.query(Scheme).count()
    req = RecommendationRequest(profile=sample_profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert res.evaluated_scheme_count == total_schemes
    assert res.eligible_scheme_count > 0
    assert res.excluded_scheme_count > 0
    assert res.eligible_scheme_count + res.excluded_scheme_count + res.insufficient_info_scheme_count == total_schemes


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
    total_schemes = db.query(Scheme).count()
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert res.evaluated_scheme_count == total_schemes
    assert res.eligible_scheme_count == 0
    assert res.recommendations == []
    assert res.excluded_scheme_count == total_schemes


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
    client, session_factory = rec_client
    db = session_factory()
    total_schemes = db.query(Scheme).count()
    db.close()

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

    assert data["evaluated_scheme_count"] == total_schemes
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


# ─────────────────────────────────────────────────────────────────
# 9. TASK-032: EXPLAINABLE SCHEME RECOMMENDATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_clearly_eligible_scheme_has_matched_rules_and_no_failed_rules(rec_client, sample_profile):
    """Test 1: Clearly eligible applicant has eligible=True, matched_rules populated, failed_rules empty."""
    _, session_factory = rec_client
    db = session_factory()
    req = RecommendationRequest(profile=sample_profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert len(res.recommendations) > 0
    top_item = res.recommendations[0]
    assert top_item.eligible is True
    assert top_item.eligibility_status == "ELIGIBLE"
    assert len(top_item.matched_rules) > 0
    assert len(top_item.failed_rules) == 0
    assert len(top_item.missing_information) == 0
    # Every passed rule is factual
    assert any("satisfies" in r or "within" in r or "eligible" in r.lower() for r in top_item.matched_rules)


def test_clearly_ineligible_scheme_has_failed_rules(rec_client):
    """Test 2: Clearly ineligible profile has eligible=False and failed_rules populated with exact factual reason."""
    _, session_factory = rec_client
    db = session_factory()

    # Profile with age 17 (below minimum 18) and annual income ₹10,00,000 (exceeds ₹3,00,000 ceiling)
    ineligible_profile = BeneficiaryProfileInput(
        age=17,
        annual_income=1000000.0,
        social_category="GENERAL",
        is_sc=False,
    )
    req = RecommendationRequest(profile=ineligible_profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert len(res.ineligible_schemes) > 0
    # Check term loan scheme (SIH26092-053) in ineligibles
    term_loan = next((item for item in res.ineligible_schemes if item.scheme_id == "SIH26092-053"), None)
    assert term_loan is not None
    assert term_loan.eligible is False
    assert term_loan.eligibility_status == "INELIGIBLE"
    assert len(term_loan.failed_rules) > 0
    # Must contain age failure or income failure
    reasons_text = " ".join(term_loan.failed_rules)
    assert "below minimum requirement of 18" in reasons_text or "exceeds limit" in reasons_text


def test_missing_income_tracked_in_missing_information_without_false_failure(rec_client):
    """Test 3: Missing income must produce missing_information note and NOT a false 'income exceeds limit'."""
    _, session_factory = rec_client
    db = session_factory()

    # Profile with no income provided
    missing_income_profile = BeneficiaryProfileInput(
        age=28,
        annual_income=None,
        social_category="SC",
        is_sc=True,
    )
    req = RecommendationRequest(profile=missing_income_profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    # Find scheme with income limit in insufficient info list
    insufficient_items = res.insufficient_info_schemes
    assert len(insufficient_items) > 0

    income_limited_scheme = next((s for s in insufficient_items if any("income" in r.lower() for r in s.missing_information)), None)
    assert income_limited_scheme is not None
    assert income_limited_scheme.eligible is False
    assert income_limited_scheme.eligibility_status == "INSUFFICIENT_INFORMATION"

    # Crucial: Must NOT contain false failure "exceeds limit"
    all_missing_text = " ".join(income_limited_scheme.missing_information)
    assert "Missing annual income" in all_missing_text or "income" in all_missing_text.lower()
    assert len(income_limited_scheme.failed_rules) == 0


def test_missing_project_cost_tracked_in_missing_information(rec_client):
    """Test 4: Missing project cost tracked without false rejection."""
    _, session_factory = rec_client
    db = session_factory()

    missing_cost_profile = BeneficiaryProfileInput(
        age=28,
        annual_income=180000.0,
        social_category="SC",
        is_sc=True,
        project_cost=None,
        requested_loan_amount=None,
    )
    req = RecommendationRequest(profile=missing_cost_profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert "project_cost" in res.missing_profile_fields
    assert "requested_loan_amount" in res.missing_profile_fields
    # Top recommendations are still evaluated for hard eligibility
    assert len(res.recommendations) > 0


def test_multiple_rule_failures_all_returned(rec_client):
    """Test 5: Profile that fails multiple rules returns ALL relevant failed rules."""
    _, session_factory = rec_client
    db = session_factory()

    multi_fail_profile = BeneficiaryProfileInput(
        age=16,                       # Fails age_min (18) on PMEGP
        annual_income=2500000.0,      # Fails income ceiling (500000) on Term Loan
        social_category="GENERAL",    # Fails SC requirement on Term Loan
        is_sc=False,
    )
    req = RecommendationRequest(profile=multi_fail_profile, top_k=50)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    # Check SIH26092-053 (Term Loan) which fails both income ceiling and SC requirement
    term_loan = next((item for item in res.ineligible_schemes if item.scheme_id == "SIH26092-053"), None)
    assert term_loan is not None
    assert term_loan.eligible is False
    assert len(term_loan.failed_rules) >= 2
    failed_text = " ".join(term_loan.failed_rules)
    assert "income" in failed_text.lower() or "500,000" in failed_text

    # Check SIH26092-001 (PMEGP) which fails age requirement (min 18)
    pmegp = next((item for item in res.ineligible_schemes if item.scheme_id == "SIH26092-001"), None)
    if pmegp:
        pmegp_text = " ".join(pmegp.failed_rules)
        assert "age" in pmegp_text.lower() or "18" in pmegp_text


def test_boundary_value_exactly_at_limit(rec_client):
    """Test 6: Boundary value exactly at limit satisfies official eligibility criteria."""
    _, session_factory = rec_client
    db = session_factory()

    # Exact boundary: age = 18, annual_income = 500,000.0 (exact limit of ₹500,000 for NSFDC Term Loan)
    boundary_profile = BeneficiaryProfileInput(
        age=18,
        annual_income=500000.0,
        social_category="SC",
        is_sc=True,
        applicant_type="INDIVIDUAL",
        sector="MICRO_FINANCE",
        activity_type="SMALL_MICRO_BUSINESS",
        project_cost=100000.0,
        requested_loan_amount=90000.0,
    )
    req = RecommendationRequest(profile=boundary_profile, top_k=50)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    term_loan = next((item for item in res.recommendations if item.scheme_id == "SIH26092-053"), None)
    assert term_loan is not None
    assert term_loan.eligible is True
    assert term_loan.eligibility_status == "ELIGIBLE"
    # Income rule passed
    income_passed = any("500,000.00" in r and "satisfies" in r for r in term_loan.matched_rules)
    assert income_passed


def test_boundary_value_just_above_limit(rec_client):
    """Test 7: Boundary value just above limit (₹500,001) fails eligibility."""
    _, session_factory = rec_client
    db = session_factory()

    above_boundary_profile = BeneficiaryProfileInput(
        age=18,
        annual_income=500001.0,  # ₹1 over limit of ₹500,000
        social_category="SC",
        is_sc=True,
        applicant_type="INDIVIDUAL",
    )
    req = RecommendationRequest(profile=above_boundary_profile, top_k=50)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    # Should NOT be in eligible recommendations for term loan
    term_loan_eligible = next((item for item in res.recommendations if item.scheme_id == "SIH26092-053"), None)
    assert term_loan_eligible is None

    # Must be in ineligibles with exact exceeded amount
    term_loan_ineligible = next((item for item in res.ineligible_schemes if item.scheme_id == "SIH26092-053"), None)
    assert term_loan_ineligible is not None
    assert term_loan_ineligible.eligible is False
    assert any("500,000.00" in r and "exceeds" in r.lower() for r in term_loan_ineligible.failed_rules)


def test_selected_scheme_id_preservation_to_partner_locator(rec_client, sample_profile):
    """Test 8: Recommendation item preserves exact scheme_id for seamless partner locator query."""
    client, session_factory = rec_client
    db = session_factory()
    req = RecommendationRequest(profile=sample_profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    for item in res.recommendations:
        assert item.scheme_id.startswith("SIH26092-")
        # Query nearest partners with this exact scheme_id
        partner_res = client.get(f"/api/v1/partner/nearest?latitude=28.6139&longitude=77.2090&scheme_id={item.scheme_id}")
        assert partner_res.status_code == 200
        partners = partner_res.json()
        if len(partners) > 0:
            for p in partners:
                assert p["is_scheme_matched"] is True

