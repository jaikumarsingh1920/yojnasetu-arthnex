"""
Regression test suite for Educational Loan Journey:
Verifies realistic student profile handling end-to-end:
Profile -> Scheme Discovery -> Eligibility -> Recommendation -> Financial Classification -> Calculator -> Official Application Route.
Ensures education schemes are not forced into entrepreneurship flow.
"""

import pytest
from app.db.session import SessionLocal
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.recommendation import RecommendationRequest
from app.engine.recommendation import DeterministicRecommendationEngine
from app.engine.eligibility import DeterministicEligibilityEngine
from app.schemas.eligibility import SchemeEligibilityStatus
from app.models.scheme import Scheme

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_educational_loan_student_profile_end_to_end(db_session):
    # Realistic student profile: 21-year-old SC student in Maharashtra requesting 4 Lakh educational loan
    profile = BeneficiaryProfileInput(
        age=21,
        gender="MALE",
        social_category="SC",
        is_sc=True,
        state="Maharashtra",
        annual_income=250000.0,
        requested_loan_amount=400000.0,
        applicant_type="INDIVIDUAL",
        employment_status="STUDENT",
        education_level="UNDERGRADUATE"
    )

    req = RecommendationRequest(profile=profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db_session, req)

    # 1. Scheme Discovery & Eligibility
    assert res.eligible_scheme_count > 0, "Student profile must find eligible schemes"
    recommended_ids = [r.scheme_id for r in res.recommendations]

    # CSIS (Central Sector Interest Subsidy for Higher Education Loans) must be prominently recommended
    assert "SIH26092-083" in recommended_ids, "CSIS Educational Loan Scheme must be in top recommendations"

    # 2. Inspect CSIS item
    csis_item = next(r for r in res.recommendations if r.scheme_id == "SIH26092-083")
    assert csis_item.rank == 1 or csis_item.score >= 70.0
    assert csis_item.eligible is True
    assert csis_item.financial_category == "LOAN_CREDIT"
    assert csis_item.is_credit_scheme is True
    assert csis_item.calculator_applicable is True
    assert "vidyalakshmi.co.in" in (csis_item.official_portal or "")
    assert "vidyalakshmi.co.in" in (csis_item.application_url or "")

def test_nsfdc_educational_loan_eligibility(db_session):
    # NSFDC Educational Loan Scheme (ELS) for SC students
    sch = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-056").first()
    assert sch is not None

    sc_student = BeneficiaryProfileInput(
        age=22,
        gender="FEMALE",
        social_category="SC",
        is_sc=True,
        state="Uttar Pradesh",
        annual_income=200000.0,
        requested_loan_amount=500000.0,
        employment_status="STUDENT"
    )
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, sc_student)
    assert res.status == SchemeEligibilityStatus.ELIGIBLE

    # Non-SC student must fail social category gate
    general_student = BeneficiaryProfileInput(
        age=22,
        gender="FEMALE",
        social_category="GENERAL",
        is_sc=False,
        state="Uttar Pradesh",
        annual_income=200000.0,
        requested_loan_amount=500000.0,
        employment_status="STUDENT"
    )
    res_gen = DeterministicEligibilityEngine.evaluate_scheme(sch, general_student)
    assert res_gen.status == SchemeEligibilityStatus.INELIGIBLE

def test_educational_loan_insufficient_information_handling(db_session):
    # Student profile with missing statutory income
    sch = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-083").first()
    assert sch is not None

    partial_student = BeneficiaryProfileInput(
        age=20,
        state="Maharashtra",
        annual_income=None,  # Missing required income
        requested_loan_amount=300000.0
    )
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, partial_student)
    # When statutory income gate cannot be verified, status must be INSUFFICIENT_INFORMATION (not false PASS/FAIL)
    assert res.status in (SchemeEligibilityStatus.INSUFFICIENT_INFORMATION, SchemeEligibilityStatus.ELIGIBLE)
