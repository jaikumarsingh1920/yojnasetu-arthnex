import pytest
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.eligibility import SchemeEligibilityStatus
from app.schemas.recommendation import RecommendationRequest
from app.engine.eligibility import DeterministicEligibilityEngine
from app.engine.recommendation import DeterministicRecommendationEngine


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_national_scheme_passes_all_states(db_session):
    """National/All-India schemes must pass applicants from any state."""
    sch = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()  # PMEGP (All India)
    assert sch is not None

    for state in ["Rajasthan", "Gujarat", "Tamil Nadu", "Bihar", "Assam"]:
        profile = BeneficiaryProfileInput(
            state=state,
            age=30,
            social_category="GENERAL",
            gender="MALE"
        )
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        # Geography must be in hard_rules_passed
        geo_passes = [r for r in res.hard_rules_passed if r.field == "state"]
        assert len(geo_passes) == 1, f"State {state} did not pass geography for national scheme {sch.scheme_name}"
        assert geo_passes[0].result.value == "PASS"


def test_state_specific_scheme_fails_other_states(db_session):
    """A Gujarat-only scheme must strictly fail a Rajasthan applicant."""
    sch = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-109").first()  # Gujarat
    assert sch is not None
    assert "Gujarat" in (sch.state_coverage or "")

    # Test applicant from Rajasthan
    profile_rj = BeneficiaryProfileInput(
        state="Rajasthan",
        age=30,
        social_category="SC",
        is_sc=True,
        gender="MALE"
    )
    res_rj = DeterministicEligibilityEngine.evaluate_scheme(sch, profile_rj)
    assert res_rj.status == SchemeEligibilityStatus.INELIGIBLE
    geo_fails = [r for r in res_rj.hard_rules_failed if r.field == "state"]
    assert len(geo_fails) == 1
    assert "restricted to Gujarat" in geo_fails[0].reason

    # Test applicant from Gujarat
    profile_gj = BeneficiaryProfileInput(
        state="Gujarat",
        age=30,
        social_category="SC",
        is_sc=True,
        gender="MALE"
    )
    res_gj = DeterministicEligibilityEngine.evaluate_scheme(sch, profile_gj)
    geo_passes = [r for r in res_gj.hard_rules_passed if r.field == "state"]
    assert len(geo_passes) == 1
    assert geo_passes[0].result.value == "PASS"


def test_profile_c_rajasthan_no_geography_leakage(db_session):
    """Profile C (SC Youth, Rajasthan, Education Loan) must never receive Gujarat or Tamil Nadu schemes as eligible."""
    prof_c = BeneficiaryProfileInput(
        social_category="SC",
        gender="MALE",
        age=22,
        state="Rajasthan",
        annual_income=150000.0,
        requested_loan_amount=200000.0,
        project_cost=250000.0,
        sector="Education",
        is_sc=True
    )
    req = RecommendationRequest(profile=prof_c, top_k=50)
    res = DeterministicRecommendationEngine.get_recommendations(db_session, req)

    for rec in res.recommendations:
        sch = db_session.query(Scheme).filter(Scheme.scheme_id == rec.scheme_id).first()
        cov = (sch.state_coverage or "").strip()
        # Coverage must be either National, Rajasthan, or empty central ministry
        is_valid = (
            not cov
            or "All" in cov
            or "ALL" in cov
            or "National" in cov
            or "Rajasthan" in cov
        )
        assert is_valid, (
            f"Recommendation leakage: Scheme '{rec.scheme_name}' (ID: {rec.scheme_id}) "
            f"has state_coverage '{cov}' but was recommended to a Rajasthan applicant!"
        )


def test_missing_state_triggers_unknown_for_state_scheme(db_session):
    """Missing applicant state on profile should trigger unknown_eligibility for state-specific schemes."""
    sch = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-109").first()  # Gujarat
    assert sch is not None

    profile_no_state = BeneficiaryProfileInput(
        state=None,
        age=30,
        social_category="SC",
        is_sc=True,
        gender="MALE"
    )
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile_no_state)
    geo_unknown = [r for r in res.unknown_eligibility_rules if r.field == "state"]
    assert len(geo_unknown) == 1
    assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
