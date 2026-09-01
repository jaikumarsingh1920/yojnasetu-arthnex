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


# -------------------------------------------------------------
# 7. TASK-033: ELIGIBILITY ENGINE EDGE CASE HARDENING TESTS
# -------------------------------------------------------------

def test_edge_case_income_boundaries(db_session):
    """Verify income boundaries: exactly at limit (PASS), just below limit (PASS), just above limit (FAIL)."""
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-053").first()
    assert scheme is not None
    limit = scheme.income_limit # 500,000.0

    # 1. Exactly at limit (500,000.0) -> ELIGIBLE
    p_exact = BeneficiaryProfileInput(is_sc=True, social_category="SC", annual_income=float(limit), age=25)
    res_exact = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_exact)
    assert res_exact.status == SchemeEligibilityStatus.ELIGIBLE
    assert any("satisfies limit" in r for r in res_exact.matched_rules)
    assert len(res_exact.failed_rules) == 0

    # 2. Just below limit (499,999.0) -> ELIGIBLE
    p_below = BeneficiaryProfileInput(is_sc=True, social_category="SC", annual_income=float(limit) - 1.0, age=25)
    res_below = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_below)
    assert res_below.status == SchemeEligibilityStatus.ELIGIBLE
    assert len(res_below.failed_rules) == 0

    # 3. Just above limit (500,001.0) -> INELIGIBLE
    p_above = BeneficiaryProfileInput(is_sc=True, social_category="SC", annual_income=float(limit) + 1.0, age=25)
    res_above = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_above)
    assert res_above.status == SchemeEligibilityStatus.INELIGIBLE
    assert any("exceeds limit" in r for r in res_above.failed_rules)


def test_edge_case_age_boundaries(db_session):
    """Verify age boundaries: minimum age exact, min age below, max age exact, max age above."""
    # Find scheme with both age_min or age_max or create custom rule evaluation
    scheme = db_session.query(Scheme).filter(Scheme.age_min.isnot(None)).first()
    if not scheme:
        scheme = db_session.query(Scheme).first()
        scheme.age_min = 18
        scheme.age_max = 50

    min_age = scheme.age_min or 18
    max_age = scheme.age_max or 50

    # 1. Min age exact boundary (18) -> PASSES age rule
    p_min_exact = BeneficiaryProfileInput(age=min_age, is_sc=True, social_category="SC", annual_income=100000.0)
    res_min = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_min_exact)
    assert not any("below minimum requirement" in r for r in res_min.failed_rules)

    # 2. Min age below boundary (17) -> FAILS age rule
    p_min_below = BeneficiaryProfileInput(age=min_age - 1, is_sc=True, social_category="SC", annual_income=100000.0)
    res_min_below = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_min_below)
    assert res_min_below.status == SchemeEligibilityStatus.INELIGIBLE
    assert any("below minimum requirement" in r for r in res_min_below.failed_rules)

    # 3. Max age exact boundary (50) -> PASSES age max rule
    if scheme.age_max is not None:
        p_max_exact = BeneficiaryProfileInput(age=max_age, is_sc=True, social_category="SC", annual_income=100000.0)
        res_max = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_max_exact)
        assert not any("exceeds maximum limit" in r for r in res_max.failed_rules)

        # 4. Max age above boundary (51) -> FAILS age max rule
        p_max_above = BeneficiaryProfileInput(age=max_age + 1, is_sc=True, social_category="SC", annual_income=100000.0)
        res_max_above = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_max_above)
        assert res_max_above.status == SchemeEligibilityStatus.INELIGIBLE
        assert any("exceeds maximum limit" in r for r in res_max_above.failed_rules)


def test_edge_case_missing_income_insufficient_info(db_session):
    """Verify missing income produces INSUFFICIENT_INFORMATION, never silently eligible or falsely failed."""
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-053").first()
    assert scheme is not None

    p_missing_income = BeneficiaryProfileInput(
        age=25,
        social_category="SC",
        is_sc=True,
        annual_income=None # Explicitly missing
    )
    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_missing_income)
    assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
    assert len(res.missing_information) > 0
    assert any("annual income" in r.lower() for r in res.missing_information)
    assert len(res.failed_rules) == 0


def test_edge_case_missing_category_and_education(db_session):
    """Verify missing social category and education are handled without silent true."""
    # Test SC required rule evaluation with missing category
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-053").first()
    assert scheme is not None

    p_no_category = BeneficiaryProfileInput(
        age=25,
        annual_income=100000.0,
        social_category=None,
        is_sc=None
    )
    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_no_category)
    assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
    assert len(res.missing_information) > 0

    # Test education level resolution
    p_with_edu = BeneficiaryProfileInput(
        age=25,
        education_level="10TH_PASS"
    )
    act_val = DeterministicEligibilityEngine.resolve_field_value("education_level", p_with_edu)
    assert act_val == "10TH_PASS"


def test_edge_case_unsupported_activity(db_session):
    """Verify unsupported activity fails operator IN evaluation."""
    res_pass, _ = evaluate_operator("IN", "TAILORING, CARPENTRY, WEAVING", "ENUM", "TAILORING")
    assert res_pass == RuleEvaluationResult.PASS

    res_fail, reason = evaluate_operator("IN", "TAILORING, CARPENTRY, WEAVING", "ENUM", "NUCLEAR_RESEARCH")
    assert res_fail == RuleEvaluationResult.FAIL
    assert "not in required list" in reason


def test_edge_case_multiple_simultaneous_failures(db_session):
    """Verify profile with multiple simultaneous rule violations returns ALL failure reasons."""
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-053").first()
    assert scheme is not None

    # Fails both income limit (2,000,000 > 500,000) and SC requirement (GENERAL != SC)
    p_multi_fail = BeneficiaryProfileInput(
        age=25,
        annual_income=2000000.0,
        social_category="GENERAL",
        is_sc=False
    )
    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_multi_fail)
    assert res.status == SchemeEligibilityStatus.INELIGIBLE
    assert len(res.failed_rules) >= 2
    assert any("exceeds limit" in r for r in res.failed_rules)
    assert any("Expected True" in r or "flag is False" in r for r in res.failed_rules)


def test_edge_case_incomplete_profile_never_silently_eligible(db_session):
    """Verify completely empty profile never evaluates to ELIGIBLE on schemes with mandatory criteria."""
    empty_profile = BeneficiaryProfileInput()
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-053").first()
    assert scheme is not None

    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, empty_profile)
    assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
    assert len(res.missing_information) > 0
    assert res.status != SchemeEligibilityStatus.ELIGIBLE

