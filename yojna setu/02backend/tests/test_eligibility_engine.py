import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from app.models import Base, Scheme, SchemeRule, SchemeVerification
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.eligibility import (
    RuleEvaluationResult,
    SchemeEligibilityStatus,
    SchemeEligibilityResult
)
from app.engine.operators import evaluate_operator
from app.engine.eligibility import DeterministicEligibilityEngine
from seed_db import seed_database


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        seed_database(session)
        yield session
    finally:
        session.close()


# -------------------------------------------------------------
# 1. Operator Unit Tests
# -------------------------------------------------------------
def test_operator_numeric_comparisons():
    # <= tests
    res, _ = evaluate_operator("<=", "500000", "INR_PER_YEAR", 400000)
    assert res == RuleEvaluationResult.PASS

    res, _ = evaluate_operator("<=", "500000", "INR_PER_YEAR", 500000)
    assert res == RuleEvaluationResult.PASS

    res, _ = evaluate_operator("<=", "500000", "INR_PER_YEAR", 500001)
    assert res == RuleEvaluationResult.FAIL

    res, _ = evaluate_operator("<=", "500000", "INR_PER_YEAR", None)
    assert res == RuleEvaluationResult.UNKNOWN

    # >= tests
    res, _ = evaluate_operator(">=", "18", "INT", 20)
    assert res == RuleEvaluationResult.PASS

    res, _ = evaluate_operator(">=", "18", "INT", 17)
    assert res == RuleEvaluationResult.FAIL

    # > tests
    res, _ = evaluate_operator(">", "140000", "INR", 150000)
    assert res == RuleEvaluationResult.PASS

    res, _ = evaluate_operator(">", "140000", "INR", 140000)
    assert res == RuleEvaluationResult.FAIL


def test_operator_boolean_and_enum():
    # Boolean =
    res, _ = evaluate_operator("=", "TRUE", "BOOLEAN", True)
    assert res == RuleEvaluationResult.PASS

    res, _ = evaluate_operator("=", "TRUE", "BOOLEAN", False)
    assert res == RuleEvaluationResult.FAIL

    # ENUM IN
    res, _ = evaluate_operator("IN", "PM_SURAJ; AUTHORISED_SCA; AUTHORISED_CA", "ENUM", "AUTHORISED_SCA")
    assert res == RuleEvaluationResult.PASS

    res, _ = evaluate_operator("IN", "PM_SURAJ; AUTHORISED_SCA; AUTHORISED_CA", "ENUM", "OTHER_CHANNEL")
    assert res == RuleEvaluationResult.FAIL


# -------------------------------------------------------------
# 2. REQUIRED AUDIT TEST 1: Eligible beneficiary + UNKNOWN financial parameter
# -------------------------------------------------------------
def test_eligible_beneficiary_unknown_financial_parameter(db_session):
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-052").first()
    assert scheme is not None

    # Beneficiary satisfies all hard eligibility conditions (SC=True, Income <= 500k),
    # but has missing/UNKNOWN financial profile fields (project_cost=None, requested_loan_amount=None)
    p_eligible = BeneficiaryProfileInput(
        is_sc=True,
        social_category="SC",
        annual_income=180000.0,
        project_cost=None,
        requested_loan_amount=None
    )

    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_eligible)
    
    # Must be ELIGIBLE (Unknown financial parameter does NOT downgrade hard eligibility status)
    assert res.status == SchemeEligibilityStatus.ELIGIBLE
    assert len(res.hard_rules_failed) == 0
    assert len(res.unknown_eligibility_rules) == 0
    assert len(res.financial_rules) > 0

    # Financial rules must return UNKNOWN without converting to zero or failing
    unknown_fin_rule = [r for r in res.financial_rules if r.field == "max_loan_amount"][0]
    assert unknown_fin_rule.result == RuleEvaluationResult.UNKNOWN
    assert unknown_fin_rule.actual_value is None


# -------------------------------------------------------------
# 3. REQUIRED AUDIT TEST 2: Ineligible beneficiary due to actual hard eligibility rule
# -------------------------------------------------------------
def test_ineligible_beneficiary_hard_rule_fail(db_session):
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-052").first()
    assert scheme is not None

    # Fails hard income limit (600,000 > 500,000)
    p_high_income = BeneficiaryProfileInput(
        is_sc=True,
        social_category="SC",
        annual_income=600000.0
    )

    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_high_income)
    assert res.status == SchemeEligibilityStatus.INELIGIBLE
    assert len(res.hard_rules_failed) >= 1
    assert any(r.field == "income_limit" for r in res.hard_rules_failed)


# -------------------------------------------------------------
# 4. REQUIRED AUDIT TEST 3: Eligible beneficiary + conditional financial rule
# -------------------------------------------------------------
def test_eligible_beneficiary_conditional_financial_rule(db_session):
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-015").first()
    assert scheme is not None

    # Profile qualifies for NBCFDC scheme, requested loan = 100,000 triggers LOAN_LTE_125000 7% interest rate rule
    p_conditional_loan = BeneficiaryProfileInput(
        social_category="BACKWARD_CLASS",
        annual_income=300000.0,
        requested_loan_amount=100000.0
    )

    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_conditional_loan)
    assert res.status == SchemeEligibilityStatus.ELIGIBLE
    assert len(res.hard_rules_failed) == 0

    # Financial rules contain evaluated loan slab parameters
    rate_rules = [r for r in res.financial_rules if r.field == "interest_rate_max" and r.condition_group == "LOAN_LTE_125000"]
    assert len(rate_rules) == 1
    assert rate_rules[0].required_value == "7"


# -------------------------------------------------------------
# 5. REQUIRED AUDIT TEST 4: Missing financial profile field does not convert to zero
# -------------------------------------------------------------
def test_missing_financial_profile_field(db_session):
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-053").first()
    assert scheme is not None

    p_no_fin = BeneficiaryProfileInput(
        is_sc=True,
        annual_income=250000.0,
        project_cost=None,
        requested_loan_amount=None
    )

    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_no_fin)
    assert res.status == SchemeEligibilityStatus.ELIGIBLE

    for fin_rule in res.financial_rules:
        if fin_rule.actual_value is None:
            assert fin_rule.result == RuleEvaluationResult.UNKNOWN
            assert fin_rule.actual_value != 0, "UNKNOWN financial value was incorrectly converted to 0"


# -------------------------------------------------------------
# 6. REQUIRED AUDIT TEST 5: Deterministic repeated execution
# -------------------------------------------------------------
def test_deterministic_repeated_execution(db_session):
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-056").first()
    p_input = BeneficiaryProfileInput(
        is_sc=True,
        annual_income=200000.0,
        applicant_type="STUDENT",
        requested_loan_amount=2500000.0
    )

    first_res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_input)
    for _ in range(50):
        subsequent_res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_input)
        assert subsequent_res.status == first_res.status
        assert len(subsequent_res.hard_rules_passed) == len(first_res.hard_rules_passed)
        assert len(subsequent_res.financial_rules) == len(first_res.financial_rules)
        assert subsequent_res.explanations == first_res.explanations
