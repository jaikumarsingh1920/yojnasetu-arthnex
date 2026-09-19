import pytest
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.eligibility import RuleEvaluationResult, SchemeEligibilityStatus
from app.engine.operators import evaluate_operator
from app.engine.eligibility import DeterministicEligibilityEngine
from app.models.scheme import Scheme
from app.models.rule import SchemeRule


def test_operator_strict_less_than():
    """Verify < operator is strictly less than, not less than or equal."""
    res, reason = evaluate_operator("<", "15.0", "PERCENT", 14.99)
    assert res == RuleEvaluationResult.PASS

    res, reason = evaluate_operator("<", "15.0", "PERCENT", 15.0)
    assert res == RuleEvaluationResult.FAIL

    res, reason = evaluate_operator("<", "15.0", "PERCENT", 15.01)
    assert res == RuleEvaluationResult.FAIL


def test_operator_less_than_or_equal():
    """Verify <= operator includes the boundary."""
    res, reason = evaluate_operator("<=", "15.0", "PERCENT", 15.0)
    assert res == RuleEvaluationResult.PASS

    res, reason = evaluate_operator("<=", "15.0", "PERCENT", 15.01)
    assert res == RuleEvaluationResult.FAIL


def test_operator_strict_greater_than():
    """Verify > operator is strictly greater than."""
    res, reason = evaluate_operator(">", "18", "INT", 18)
    assert res == RuleEvaluationResult.FAIL

    res, reason = evaluate_operator(">", "18", "INT", 19)
    assert res == RuleEvaluationResult.PASS


def test_operator_greater_than_or_equal():
    """Verify >= operator includes the boundary."""
    res, reason = evaluate_operator(">=", "18", "INT", 18)
    assert res == RuleEvaluationResult.PASS

    res, reason = evaluate_operator(">=", "18", "INT", 17)
    assert res == RuleEvaluationResult.FAIL


def test_operator_equality_variants():
    """Verify == and = work identically for numbers, booleans, and strings."""
    assert evaluate_operator("==", "100", "INT", 100)[0] == RuleEvaluationResult.PASS
    assert evaluate_operator("=", "100", "INT", 100)[0] == RuleEvaluationResult.PASS
    assert evaluate_operator("==", "TRUE", "BOOLEAN", True)[0] == RuleEvaluationResult.PASS
    assert evaluate_operator("!=", "TRUE", "BOOLEAN", False)[0] == RuleEvaluationResult.PASS
    assert evaluate_operator("<>", "100", "INT", 99)[0] == RuleEvaluationResult.PASS


def test_operator_contains():
    """Verify CONTAINS operator handles tokens, categories, and booleans."""
    assert evaluate_operator("CONTAINS", "PWD", "STRING", "PWD, SC, WOMEN")[0] == RuleEvaluationResult.PASS
    assert evaluate_operator("CONTAINS", "PWD", "STRING", "DIVYANGJAN")[0] == RuleEvaluationResult.PASS
    assert evaluate_operator("CONTAINS", "PWD", "STRING", "SC, GENERAL")[0] == RuleEvaluationResult.FAIL
    assert evaluate_operator("CONTAINS", "PWD", "STRING", True)[0] == RuleEvaluationResult.PASS
    assert evaluate_operator("CONTAINS", "PWD", "STRING", False)[0] == RuleEvaluationResult.FAIL


def test_operator_not_in():
    """Verify NOT IN operator excludes restricted items."""
    assert evaluate_operator("NOT IN", "MINORITY, ST", "STRING", "SC")[0] == RuleEvaluationResult.PASS
    assert evaluate_operator("NOT IN", "MINORITY, ST", "STRING", "ST")[0] == RuleEvaluationResult.FAIL


def test_missing_data_never_evaluates_to_pass():
    """Anti-Fabrication Rule: None/UNKNOWN/NULL inputs MUST produce UNKNOWN, never PASS."""
    for sentinel in [None, "UNKNOWN", "NONE", "NULL", "", "NOT_SPECIFIED"]:
        res, reason = evaluate_operator("<=", "300000", "INR", sentinel)
        assert res == RuleEvaluationResult.UNKNOWN
        assert "Missing required profile input" in reason


def test_eligibility_target_group_pwd_resolution():
    """Target groups PWD rule resolution with explicit true, false, and unknown states."""
    scheme = Scheme(
        scheme_id="TEST-PWD-001",
        scheme_name="Divyangjan Enterprise Scheme",
        scheme_status="ACTIVE",
        state_coverage="ALL_INDIA",
    )
    rule = SchemeRule(
        rule_id="RULE-PWD-1",
        scheme_id="TEST-PWD-001",
        field="target_groups",
        operator="CONTAINS",
        value="PWD",
        value_type="STRING",
        rule_type="ELIGIBILITY",
        priority="HIGH",
        condition_group="BASE",
        active=True
    )

    # 1. Citizen is PWD -> PASS
    p_pwd = BeneficiaryProfileInput(is_pwd=True)
    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_pwd, active_rules=[rule])
    assert res.status == SchemeEligibilityStatus.ELIGIBLE

    # 2. Citizen is NOT PWD -> INELIGIBLE
    p_not_pwd = BeneficiaryProfileInput(is_pwd=False)
    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_not_pwd, active_rules=[rule])
    assert res.status == SchemeEligibilityStatus.INELIGIBLE

    # 3. Citizen omitted PWD status -> INSUFFICIENT_INFORMATION (never false pass)
    p_unknown = BeneficiaryProfileInput(is_pwd=None)
    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, p_unknown, active_rules=[rule])
    assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION


def test_eligibility_income_boundary():
    """Income <= ceiling boundary conditions."""
    scheme = Scheme(
        scheme_id="TEST-INC-001",
        scheme_name="Micro Credit Scheme",
        income_limit=300000.0,
        scheme_status="ACTIVE",
        state_coverage="ALL_INDIA",
    )

    # Exact boundary
    p_boundary = BeneficiaryProfileInput(annual_income=300000.0)
    assert DeterministicEligibilityEngine.evaluate_scheme(scheme, p_boundary).status == SchemeEligibilityStatus.ELIGIBLE

    # 1 Rupee over boundary
    p_over = BeneficiaryProfileInput(annual_income=300001.0)
    assert DeterministicEligibilityEngine.evaluate_scheme(scheme, p_over).status == SchemeEligibilityStatus.INELIGIBLE

    # Missing income
    p_none = BeneficiaryProfileInput(annual_income=None)
    assert DeterministicEligibilityEngine.evaluate_scheme(scheme, p_none).status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION


def test_eligibility_age_boundaries():
    """Age min and max exact boundaries."""
    scheme = Scheme(
        scheme_id="TEST-AGE-001",
        scheme_name="Youth Entrepreneur Scheme",
        age_min=18,
        age_max=40,
        scheme_status="ACTIVE",
        state_coverage="ALL_INDIA",
    )

    # Exact lower boundary (18)
    assert DeterministicEligibilityEngine.evaluate_scheme(scheme, BeneficiaryProfileInput(age=18)).status == SchemeEligibilityStatus.ELIGIBLE
    # Below lower boundary (17)
    assert DeterministicEligibilityEngine.evaluate_scheme(scheme, BeneficiaryProfileInput(age=17)).status == SchemeEligibilityStatus.INELIGIBLE

    # Exact upper boundary (40)
    assert DeterministicEligibilityEngine.evaluate_scheme(scheme, BeneficiaryProfileInput(age=40)).status == SchemeEligibilityStatus.ELIGIBLE
    # Above upper boundary (41)
    assert DeterministicEligibilityEngine.evaluate_scheme(scheme, BeneficiaryProfileInput(age=41)).status == SchemeEligibilityStatus.INELIGIBLE

    # Missing age
    assert DeterministicEligibilityEngine.evaluate_scheme(scheme, BeneficiaryProfileInput(age=None)).status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
