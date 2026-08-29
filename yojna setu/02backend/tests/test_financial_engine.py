"""
Comprehensive test suite for TASK-004: Deterministic Financial Calculation Engine.

Test categories per specification:
  1. Loan validation (below min, exactly min, within range, exactly max, above max)
  2. Financing percentage (valid financing, beneficiary contribution, financing gap)
  3. Interest (zero interest, positive interest, invalid interest)
  4. EMI (standard EMI, zero-interest installment, invalid principal, invalid tenure)
  5. UNKNOWN (unknown interest, unknown tenure, unknown loan limit, unknown financing %)
  6. CONDITIONAL (slab-dependent rule, missing slab info, resolved slab)
  7. Moratorium (UNKNOWN treatment flagged)
  8. Amortization (principal reduces, total matches, final balance zero)
  9. Determinism (50 repeated runs identical)
  10. Source traceability (every resolved parameter has rule ID / source)
"""

import pytest
import os
import sys
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from app.models import Base
from app.schemas.financial import (
    FinancialCalculationInput,
    FinancialCalculationResult,
    FinancialCalculationStatus,
    ParameterResolutionStatus,
    RepaymentFrequency,
)
from app.engine.calculator import DeterministicFinancialEngine
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


# ─────────────────────────────────────────────────────────────────
# 1. LOAN VALIDATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_loan_below_minimum(db_session):
    """SIH26092-053 (NSFDC Term Loan) has min_loan_amount = 125000."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-053",
        project_cost=Decimal("200000"),
        requested_loan_amount=Decimal("50000"),  # below 125000 minimum
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.VALIDATION_FAILED
    assert any(e.field == "requested_loan_amount" for e in result.validation_errors)
    assert any("below" in e.message.lower() for e in result.validation_errors)


def test_loan_exactly_minimum(db_session):
    """SIH26092-053: requested = exactly 125000 (minimum)."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-053",
        project_cost=Decimal("200000"),
        requested_loan_amount=Decimal("125000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    # Should not produce validation error for loan amount minimum
    loan_min_errors = [e for e in result.validation_errors if e.field == "requested_loan_amount" and "below" in e.message.lower()]
    assert len(loan_min_errors) == 0


def test_loan_within_range(db_session):
    """SIH26092-052 (MFS): loan 100000, within [UNKNOWN..125000]."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("120000"),
        requested_loan_amount=Decimal("100000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.CALCULATED
    assert len(result.validation_errors) == 0


def test_loan_exactly_maximum(db_session):
    """SIH26092-052: max_loan_amount = 125000. Requested = exactly 125000."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("140000"),
        requested_loan_amount=Decimal("125000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    # Should NOT fail validation for loan amount
    loan_max_errors = [e for e in result.validation_errors if e.field == "requested_loan_amount" and "exceeds" in e.message.lower()]
    assert len(loan_max_errors) == 0


def test_loan_above_maximum(db_session):
    """SIH26092-052: max_loan_amount = 125000. Requested = 130000 exceeds max."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("150000"),
        requested_loan_amount=Decimal("130000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.VALIDATION_FAILED
    assert any(e.field == "requested_loan_amount" for e in result.validation_errors)


def test_project_cost_above_maximum(db_session):
    """SIH26092-052: max_project_cost = 140000. Project cost = 200000 exceeds max."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("200000"),
        requested_loan_amount=Decimal("100000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.VALIDATION_FAILED
    assert any(e.field == "project_cost" for e in result.validation_errors)


# ─────────────────────────────────────────────────────────────────
# 2. FINANCING PERCENTAGE TESTS
# ─────────────────────────────────────────────────────────────────

def test_valid_financing_percentage(db_session):
    """SIH26092-052: 90% financing. Project=100000, Loan=90000 = exactly 90%."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("90000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.CALCULATED
    assert result.eligible_loan_amount == Decimal("90000")
    assert result.beneficiary_contribution_amount == Decimal("10000")


def test_financing_percentage_exceeded(db_session):
    """SIH26092-052: 90% of 100000 = 90000. Requested 95000 exceeds financing limit."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("95000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.VALIDATION_FAILED
    assert any("financing limit" in e.message.lower() or "exceeds" in e.message.lower()
               for e in result.validation_errors)


def test_beneficiary_contribution(db_session):
    """Verify beneficiary contribution = project_cost - eligible_loan."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("80000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.CALCULATED
    assert result.eligible_loan_amount == Decimal("80000")
    assert result.beneficiary_contribution_amount == Decimal("20000")


# ─────────────────────────────────────────────────────────────────
# 3. INTEREST TESTS
# ─────────────────────────────────────────────────────────────────

def test_zero_interest_installment():
    """Zero interest: equal principal installments."""
    installment = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("120000"),
        annual_rate_percent=Decimal("0"),
        total_periods=12,
        periods_per_year=12,
    )
    assert installment == Decimal("10000.00")


def test_positive_interest_installment():
    """Standard EMI calculation at 6.5% p.a. quarterly on 100000 over 12 quarters."""
    installment = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("100000"),
        annual_rate_percent=Decimal("6.5"),
        total_periods=12,
        periods_per_year=4,
    )
    assert installment is not None
    assert installment > Decimal("0")
    # Rough sanity: quarterly payment on 100k at 6.5% over 3 years should be ~9k-10k
    assert Decimal("8000") < installment < Decimal("11000")


def test_invalid_principal():
    """Invalid principal (0 or negative) returns None."""
    assert DeterministicFinancialEngine.calculate_installment(
        Decimal("0"), Decimal("7"), 12, 12
    ) is None
    assert DeterministicFinancialEngine.calculate_installment(
        Decimal("-1000"), Decimal("7"), 12, 12
    ) is None


def test_invalid_tenure():
    """Invalid tenure (0) returns None."""
    assert DeterministicFinancialEngine.calculate_installment(
        Decimal("100000"), Decimal("7"), 0, 12
    ) is None


# ─────────────────────────────────────────────────────────────────
# 4. EMI TESTS
# ─────────────────────────────────────────────────────────────────

def test_standard_emi():
    """Monthly EMI at 8% p.a. on 100000 over 84 months."""
    emi = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("100000"),
        annual_rate_percent=Decimal("8"),
        total_periods=84,
        periods_per_year=12,
    )
    assert emi is not None
    # Known approximation: ~1559
    assert Decimal("1500") < emi < Decimal("1650")


def test_zero_interest_emi():
    """Zero interest: EMI = principal / periods."""
    emi = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("84000"),
        annual_rate_percent=Decimal("0"),
        total_periods=84,
        periods_per_year=12,
    )
    assert emi == Decimal("1000.00")


# ─────────────────────────────────────────────────────────────────
# 5. UNKNOWN HANDLING TESTS
# ─────────────────────────────────────────────────────────────────

def test_unknown_interest_rate(db_session):
    """SIH26092-008 has UNKNOWN interest rate — must NOT default to 0 or any value."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-008",
        project_cost=Decimal("200000"),
        requested_loan_amount=Decimal("180000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.INSUFFICIENT_INFORMATION
    assert "interest_rate" in result.missing_parameters
    # Verify interest was NOT silently set to zero
    interest_param = next((p for p in result.resolved_parameters if p.field == "interest_rate"), None)
    assert interest_param is not None
    assert interest_param.value is None
    assert interest_param.status == ParameterResolutionStatus.UNKNOWN


def test_unknown_tenure(db_session):
    """SIH26092-008 has UNKNOWN repayment period — must not default."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-008",
        project_cost=Decimal("200000"),
        requested_loan_amount=Decimal("180000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.INSUFFICIENT_INFORMATION
    assert "repayment_period_max_months" in result.missing_parameters


def test_unknown_loan_limit(db_session):
    """SIH26092-008 has UNKNOWN max_loan_amount — must remain UNKNOWN, not 0."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-008",
        project_cost=Decimal("200000"),
        requested_loan_amount=Decimal("180000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    max_loan_param = next((p for p in result.resolved_parameters if p.field == "max_loan_amount"), None)
    assert max_loan_param is not None
    assert max_loan_param.value is None
    assert max_loan_param.status == ParameterResolutionStatus.UNKNOWN
    assert max_loan_param.value != 0


def test_unknown_financing_percentage(db_session):
    """SIH26092-008 has UNKNOWN financing_percentage — must remain UNKNOWN, not 0%."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-008",
        project_cost=Decimal("200000"),
        requested_loan_amount=Decimal("180000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    fin_param = next((p for p in result.resolved_parameters if p.field == "financing_percentage"), None)
    assert fin_param is not None
    assert fin_param.value is None
    assert fin_param.status == ParameterResolutionStatus.UNKNOWN
    assert fin_param.value != Decimal("0")


def test_missing_requested_loan_amount(db_session):
    """Missing requested_loan_amount returns INSUFFICIENT_INFORMATION."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=None,
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.INSUFFICIENT_INFORMATION
    assert "requested_loan_amount" in result.missing_parameters


def test_missing_project_cost(db_session):
    """Missing project_cost returns INSUFFICIENT_INFORMATION."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        requested_loan_amount=Decimal("90000"),
        project_cost=None,
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.INSUFFICIENT_INFORMATION
    assert "project_cost" in result.missing_parameters


# ─────────────────────────────────────────────────────────────────
# 6. CONDITIONAL / SLAB TESTS
# ─────────────────────────────────────────────────────────────────

def test_slab_resolved_low_loan(db_session):
    """SIH26092-015 (NBCFDC): loan ≤ 125000 → 7% interest, 48 months."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-015",
        project_cost=Decimal("120000"),
        requested_loan_amount=Decimal("100000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.CALCULATED
    assert result.interest_rate == Decimal("7")


def test_slab_resolved_high_loan(db_session):
    """SIH26092-015 (NBCFDC): loan > 125000 → 8% interest, 84 months."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-015",
        project_cost=Decimal("300000"),
        requested_loan_amount=Decimal("200000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.CALCULATED
    assert result.interest_rate == Decimal("8")


def test_slab_missing_loan_amount(db_session):
    """SIH26092-015: without loan amount, cannot resolve slab → INSUFFICIENT_INFORMATION."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-015",
        project_cost=Decimal("300000"),
        requested_loan_amount=None,
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.INSUFFICIENT_INFORMATION


def test_conditional_interest_rate_uny(db_session):
    """SIH26092-055 (UNY): interest rate is channel-dependent (COOP vs SFB) → CONDITIONAL."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-055",
        project_cost=Decimal("400000"),
        requested_loan_amount=Decimal("350000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    # Interest rate should be CONDITIONAL since channel type is unknown
    interest_param = next((p for p in result.resolved_parameters if p.field == "interest_rate"), None)
    assert interest_param is not None
    assert interest_param.status == ParameterResolutionStatus.CONDITIONAL


# ─────────────────────────────────────────────────────────────────
# 7. MORATORIUM TESTS
# ─────────────────────────────────────────────────────────────────

def test_moratorium_resolved_with_unknown_mode(db_session):
    """SIH26092-052 (MFS): moratorium = 3 months, but interest mode is UNKNOWN."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("90000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.CALCULATED
    assert result.moratorium_months == 3

    # Moratorium interest mode must be UNKNOWN
    mor_mode = next((p for p in result.resolved_parameters if p.field == "moratorium_interest_mode"), None)
    assert mor_mode is not None
    assert mor_mode.status == ParameterResolutionStatus.UNKNOWN

    # Warning about moratorium interest treatment
    assert any("moratorium" in w.lower() and "unknown" in w.lower() for w in result.warnings)


def test_moratorium_els_conditional(db_session):
    """SIH26092-056 (ELS): moratorium is TEXT sentinel (CONDITIONAL)."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-056",
        project_cost=Decimal("500000"),
        requested_loan_amount=Decimal("400000"),
        repayment_period_months=120,
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    mor_param = next((p for p in result.resolved_parameters if p.field == "moratorium_months"), None)
    assert mor_param is not None
    assert mor_param.status == ParameterResolutionStatus.CONDITIONAL


# ─────────────────────────────────────────────────────────────────
# 8. AMORTIZATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_amortization_principal_reduces_correctly():
    """Verify principal decreases monotonically and final balance = 0."""
    schedule, warnings = DeterministicFinancialEngine.generate_amortization_schedule(
        principal=Decimal("100000"),
        annual_rate_percent=Decimal("6.5"),
        total_periods=12,
        periods_per_year=4,
    )
    assert len(schedule) == 12
    # Opening of first == principal
    assert schedule[0].opening_principal == Decimal("100000")
    # Closing of last should be 0 (within tolerance)
    assert abs(schedule[-1].closing_principal) <= Decimal("0.01")
    # Principal should decrease
    for i in range(1, len(schedule)):
        assert schedule[i].opening_principal < schedule[i - 1].opening_principal


def test_amortization_total_principal_matches():
    """Sum of principal components must equal the original principal."""
    principal = Decimal("100000")
    schedule, _ = DeterministicFinancialEngine.generate_amortization_schedule(
        principal=principal,
        annual_rate_percent=Decimal("8"),
        total_periods=24,
        periods_per_year=4,
    )
    total_principal_paid = sum(e.principal_component for e in schedule)
    assert abs(total_principal_paid - principal) <= Decimal("0.01")


def test_amortization_zero_interest():
    """Zero-interest amortization: all installments equal, no interest component."""
    schedule, _ = DeterministicFinancialEngine.generate_amortization_schedule(
        principal=Decimal("12000"),
        annual_rate_percent=Decimal("0"),
        total_periods=12,
        periods_per_year=12,
    )
    assert len(schedule) == 12
    for entry in schedule:
        assert entry.interest_component == Decimal("0.00")
        assert entry.principal_component == Decimal("1000.00")
    assert schedule[-1].closing_principal == Decimal("0.00")


def test_full_calculation_with_amortization(db_session):
    """Full end-to-end: SIH26092-052 (MFS) with valid inputs produces amortization schedule."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("90000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.CALCULATED
    assert len(result.amortization_schedule) > 0
    assert result.total_interest > Decimal("0")
    assert result.total_repayment > result.eligible_loan_amount
    # Final balance should be zero
    assert abs(result.amortization_schedule[-1].closing_principal) <= Decimal("0.01")


# ─────────────────────────────────────────────────────────────────
# 9. DETERMINISM TESTS
# ─────────────────────────────────────────────────────────────────

def test_deterministic_repeated_execution(db_session):
    """Same input + same DB → identical output across 50 runs."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("90000"),
    )
    first = DeterministicFinancialEngine.calculate(db_session, inp)
    for _ in range(50):
        subsequent = DeterministicFinancialEngine.calculate(db_session, inp)
        assert subsequent.status == first.status
        assert subsequent.eligible_loan_amount == first.eligible_loan_amount
        assert subsequent.interest_rate == first.interest_rate
        assert subsequent.periodic_installment == first.periodic_installment
        assert subsequent.total_interest == first.total_interest
        assert subsequent.total_repayment == first.total_repayment
        assert len(subsequent.amortization_schedule) == len(first.amortization_schedule)


# ─────────────────────────────────────────────────────────────────
# 10. SOURCE TRACEABILITY TESTS
# ─────────────────────────────────────────────────────────────────

def test_every_resolved_parameter_has_source(db_session):
    """Every resolved parameter must have a source_rule_id."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("90000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.CALCULATED
    for param in result.resolved_parameters:
        assert param.source_rule_id is not None, f"Parameter '{param.field}' missing source_rule_id"
        assert param.reason is not None, f"Parameter '{param.field}' missing reason"


def test_interest_rate_traceable_to_rule(db_session):
    """Interest rate for SIH26092-052 (MFS) should trace to a specific rule."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("90000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    interest_param = next((p for p in result.resolved_parameters if p.field == "interest_rate"), None)
    assert interest_param is not None
    assert interest_param.status == ParameterResolutionStatus.RESOLVED
    assert interest_param.value == Decimal("6.5")
    assert interest_param.source_rule_id is not None


def test_slab_rule_traceability(db_session):
    """NBCFDC slab-resolved interest rate traces to the correct slab rule."""
    # Low slab
    inp_low = FinancialCalculationInput(
        scheme_id="SIH26092-015",
        project_cost=Decimal("120000"),
        requested_loan_amount=Decimal("100000"),
    )
    result_low = DeterministicFinancialEngine.calculate(db_session, inp_low)
    rate_low = next((p for p in result_low.resolved_parameters if p.field == "interest_rate"), None)
    assert rate_low is not None
    assert "LOAN_LTE_125000" in rate_low.reason

    # High slab
    inp_high = FinancialCalculationInput(
        scheme_id="SIH26092-015",
        project_cost=Decimal("300000"),
        requested_loan_amount=Decimal("200000"),
    )
    result_high = DeterministicFinancialEngine.calculate(db_session, inp_high)
    rate_high = next((p for p in result_high.resolved_parameters if p.field == "interest_rate"), None)
    assert rate_high is not None
    assert "LOAN_GT_125000" in rate_high.reason


def test_scheme_not_found(db_session):
    """Non-existent scheme_id returns VALIDATION_FAILED."""
    inp = FinancialCalculationInput(
        scheme_id="NONEXISTENT-999",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("90000"),
    )
    result = DeterministicFinancialEngine.calculate(db_session, inp)
    assert result.status == FinancialCalculationStatus.VALIDATION_FAILED
    assert any("not found" in e.message.lower() for e in result.validation_errors)
