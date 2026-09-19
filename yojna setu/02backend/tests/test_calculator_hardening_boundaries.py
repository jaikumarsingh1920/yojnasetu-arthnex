import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from app.models import Base
from app.engine.calculator import DeterministicFinancialEngine
from app.schemas.financial import (
    FinancialCalculationInput,
    FinancialCalculationStatus,
    ParameterResolutionStatus,
    RepaymentFrequency,
)
from seed_db import seed_database


@pytest.fixture(scope="module")
def db_session():
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
    yield session
    session.close()


def test_zero_principal_validation(db_session):
    """Requested loan amount of 0 must fail validation cleanly."""
    calc_input = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("0"),
        repayment_period_months=24,
    )
    res = DeterministicFinancialEngine.calculate(db_session, calc_input)
    assert res.status == FinancialCalculationStatus.VALIDATION_FAILED
    assert any(err.field == "requested_loan_amount" for err in res.validation_errors)


def test_negative_principal_validation(db_session):
    """Negative loan amount must fail validation cleanly."""
    calc_input = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("-5000"),
        repayment_period_months=24,
    )
    res = DeterministicFinancialEngine.calculate(db_session, calc_input)
    assert res.status == FinancialCalculationStatus.VALIDATION_FAILED
    assert any(err.field == "requested_loan_amount" for err in res.validation_errors)


def test_loan_exceeds_project_cost(db_session):
    """Requested loan amount exceeding total project cost must fail validation."""
    calc_input = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("50000"),
        requested_loan_amount=Decimal("100000"),
        repayment_period_months=24,
    )
    res = DeterministicFinancialEngine.calculate(db_session, calc_input)
    assert res.status == FinancialCalculationStatus.VALIDATION_FAILED
    assert any("cannot exceed total project cost" in err.message for err in res.validation_errors)


def test_zero_interest_rate_calculation(db_session):
    """A zero-interest scenario calculates installment as simple principal / periods."""
    calc_input = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("50000"),
        interest_rate=Decimal("0.0"),
        repayment_period_months=10,
        repayment_frequency=RepaymentFrequency.MONTHLY,
    )
    res = DeterministicFinancialEngine.calculate(db_session, calc_input)
    assert res.status == FinancialCalculationStatus.CALCULATED
    assert res.interest_rate == Decimal("0.0")
    assert res.periodic_installment == Decimal("5000.00")
    assert res.total_interest == Decimal("0.00")
    assert res.total_repayment == Decimal("50000.00")


def test_decimal_interest_rate_precision(db_session):
    """Decimal interest rate (e.g. 8.25%) must calculate accurately with Decimal precision."""
    calc_input = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("50000"),
        interest_rate=Decimal("8.25"),
        repayment_period_months=12,
        repayment_frequency=RepaymentFrequency.MONTHLY,
    )
    res = DeterministicFinancialEngine.calculate(db_session, calc_input)
    assert res.status == FinancialCalculationStatus.CALCULATED
    assert res.interest_rate == Decimal("8.25")
    assert res.periodic_installment is not None
    # Verify closing principal of last entry is 0.00
    assert res.amortization_schedule[-1].closing_principal == Decimal("0.00")


def test_missing_parameters_insufficient_information(db_session):
    """When critical input like project_cost or requested_loan_amount is omitted, return INSUFFICIENT_INFORMATION."""
    calc_input = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=None,
        requested_loan_amount=None,
    )
    res = DeterministicFinancialEngine.calculate(db_session, calc_input)
    assert res.status == FinancialCalculationStatus.INSUFFICIENT_INFORMATION
    assert "project_cost" in res.missing_parameters
    assert "requested_loan_amount" in res.missing_parameters


def test_nonexistent_scheme_validation(db_session):
    """Invalid scheme ID must return VALIDATION_FAILED."""
    calc_input = FinancialCalculationInput(
        scheme_id="SCHEME-NONEXISTENT-9999",
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("50000"),
    )
    res = DeterministicFinancialEngine.calculate(db_session, calc_input)
    assert res.status == FinancialCalculationStatus.VALIDATION_FAILED
    assert any(err.field == "scheme_id" for err in res.validation_errors)
