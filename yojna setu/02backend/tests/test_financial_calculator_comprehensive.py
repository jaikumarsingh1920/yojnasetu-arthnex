import pytest
import os
import sys
from decimal import Decimal
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
from app.models import Base
from app.db.session import get_db
from app.engine.calculator import DeterministicFinancialEngine
from app.schemas.financial import FinancialCalculationInput, FinancialCalculationStatus, RepaymentFrequency
from seed_db import seed_database


@pytest.fixture(scope="module")
def calc_db_session():
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


@pytest.fixture(scope="module")
def calc_client(calc_db_session):
    def override_get_db():
        yield calc_db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────
# 1. EXACT MATHEMATICAL EMI TESTS (ENGINE LEVEL)
# ─────────────────────────────────────────────────────────────

def test_exact_emi_standard_12_percent():
    """
    Standard textbook test:
    P = 100,000, R = 12% p.a., N = 12 months.
    r = 12 / 1200 = 0.01
    EMI = 100000 * 0.01 * (1.01)^12 / ((1.01)^12 - 1) = 8884.88
    """
    emi = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("100000"),
        annual_rate_percent=Decimal("12.0"),
        total_periods=12,
        periods_per_year=12
    )
    assert emi == Decimal("8884.88")


def test_exact_emi_mudra_7_percent():
    """
    P = 100,000, R = 7% p.a., N = 36 months.
    EMI = 3,087.71
    """
    emi = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("100000"),
        annual_rate_percent=Decimal("7.0"),
        total_periods=36,
        periods_per_year=12
    )
    assert emi == Decimal("3087.71")


def test_zero_percent_interest_emi():
    """
    P = 60,000, R = 0% p.a., N = 12 months.
    When R = 0, EMI = P / N = 60,000 / 12 = 5,000.00
    """
    emi = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("60000"),
        annual_rate_percent=Decimal("0.0"),
        total_periods=12,
        periods_per_year=12
    )
    assert emi == Decimal("5000.00")


def test_large_loan_value_emi():
    """
    P = 50,000,000 (5 Crore), R = 8.5% p.a., N = 120 months (10 Years).
    Exact Decimal reducing-balance EMI = 619,928.44
    """
    emi = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("50000000"),
        annual_rate_percent=Decimal("8.5"),
        total_periods=120,
        periods_per_year=12
    )
    assert emi == Decimal("619928.44")


def test_boundary_values_installment():
    # 1 Month tenure
    emi_1m = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("10000"),
        annual_rate_percent=Decimal("12.0"),
        total_periods=1,
        periods_per_year=12
    )
    # 10000 principal + 100 monthly interest = 10100.00
    assert emi_1m == Decimal("10100.00")

    # Negative / Zero Principal or Periods -> None
    assert DeterministicFinancialEngine.calculate_installment(Decimal("0"), Decimal("7.0"), 12, 12) is None
    assert DeterministicFinancialEngine.calculate_installment(Decimal("-1000"), Decimal("7.0"), 12, 12) is None
    assert DeterministicFinancialEngine.calculate_installment(Decimal("10000"), Decimal("7.0"), 0, 12) is None
    assert DeterministicFinancialEngine.calculate_installment(Decimal("10000"), Decimal("7.0"), -5, 12) is None


# ─────────────────────────────────────────────────────────────
# 2. AMORTIZATION SCHEDULE INTEGRITY
# ─────────────────────────────────────────────────────────────

def test_amortization_schedule_zero_interest_reconciliation():
    schedule, warnings = DeterministicFinancialEngine.generate_amortization_schedule(
        principal=Decimal("60000"),
        annual_rate_percent=Decimal("0.0"),
        total_periods=12,
        periods_per_year=12
    )
    assert len(schedule) == 12
    total_principal_paid = sum(e.principal_component for e in schedule)
    total_interest_paid = sum(e.interest_component for e in schedule)
    assert total_principal_paid == Decimal("60000.00")
    assert total_interest_paid == Decimal("0.00")
    assert schedule[-1].closing_principal == Decimal("0.00")


def test_amortization_schedule_reducing_balance_reconciliation():
    principal = Decimal("100000")
    schedule, warnings = DeterministicFinancialEngine.generate_amortization_schedule(
        principal=principal,
        annual_rate_percent=Decimal("10.0"),
        total_periods=24,
        periods_per_year=12
    )
    assert len(schedule) == 24
    total_principal_paid = sum(e.principal_component for e in schedule)
    assert total_principal_paid == principal
    assert schedule[-1].closing_principal == Decimal("0.00")

    # Verify interest decreases over time as principal reduces
    first_month_interest = schedule[0].interest_component
    last_month_interest = schedule[-1].interest_component
    assert first_month_interest > last_month_interest


# ─────────────────────────────────────────────────────────────
# 3. HTTP API END-TO-END TESTS WITH SCHEME INTEGRATION
# ─────────────────────────────────────────────────────────────

def test_api_calculate_normal_interest_override(calc_client):
    payload = {
        "scheme_id": "SIH26092-052",
        "project_cost": 100000.0,
        "requested_loan_amount": 90000.0,
        "interest_rate": 8.0,
        "repayment_period_months": 36,
        "repayment_frequency": "MONTHLY"
    }
    response = calc_client.post("/api/v1/calculator/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CALCULATED"
    assert data["eligible_loan_amount"] == 90000.0
    assert data["periodic_installment"] is not None
    assert data["periodic_installment"] > 0
    assert data["total_interest"] is not None
    assert data["total_interest"] > 0
    assert data["total_repayment"] == round(90000.0 + data["total_interest"], 2)
    assert len(data["amortization_schedule"]) == 36


def test_api_calculate_zero_interest_rate(calc_client):
    payload = {
        "scheme_id": "SIH26092-052",
        "project_cost": 100000.0,
        "requested_loan_amount": 60000.0,
        "interest_rate": 0.0,
        "repayment_period_months": 12,
        "repayment_frequency": "MONTHLY"
    }
    response = calc_client.post("/api/v1/calculator/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CALCULATED"
    assert data["periodic_installment"] == 5000.0
    assert data["total_interest"] == 0.0
    assert data["total_repayment"] == 60000.0
    assert len(data["amortization_schedule"]) == 12


def test_api_calculate_invalid_scheme(calc_client):
    payload = {
        "scheme_id": "NON_EXISTENT_SCHEME_XYZ",
        "project_cost": 100000.0,
        "requested_loan_amount": 50000.0,
        "repayment_period_months": 12
    }
    response = calc_client.post("/api/v1/calculator/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VALIDATION_FAILED"
    assert any("not found" in err["message"] for err in data["validation_errors"])


def test_api_calculate_loan_exceeds_project_cost(calc_client):
    payload = {
        "scheme_id": "SIH26092-052",
        "project_cost": 50000.0,
        "requested_loan_amount": 100000.0,
        "repayment_period_months": 24
    }
    response = calc_client.post("/api/v1/calculator/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VALIDATION_FAILED"
    assert len(data["validation_errors"]) > 0
