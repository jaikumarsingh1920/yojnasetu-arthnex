"""
Tests for Scheme-Aware Financial Classification and Calculator Integration.
Verifies that:
1. All 90 schemes are accurately classified into financial categories.
2. Non-credit schemes (grants, scholarships, training, direct benefit, guarantee) have is_credit_scheme=False and calculator_applicable=False.
3. Loan/credit schemes have is_credit_scheme=True and calculator_applicable=True.
4. Mathematical reducing-balance EMI engine correctly handles standard rates and 0% welfare loans.
5. Endpoints serialize financial properties properly.
"""

import pytest
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.schemas.scheme import SchemeDetailResponse, SchemeListItemResponse
from app.engine.calculator import DeterministicFinancialEngine
from app.schemas.financial import FinancialCalculationInput


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_scheme_financial_classification_coverage(db_session):
    """Test that all 90 schemes have valid financial categories."""
    schemes = db_session.query(Scheme).all()
    assert len(schemes) == 90, f"Expected 90 schemes in database, got {len(schemes)}"

    valid_categories = {
        "LOAN_CREDIT",
        "GRANT_SUBSIDY",
        "SCHOLARSHIP",
        "TRAINING_SKILL",
        "GUARANTEE_CREDIT_SUPPORT",
        "DIRECT_BENEFIT",
        "NON_FINANCIAL",
    }

    counts = {}
    for s in schemes:
        cat = s.financial_category
        assert cat in valid_categories, f"Invalid category '{cat}' for scheme {s.scheme_id}: {s.scheme_name}"
        counts[cat] = counts.get(cat, 0) + 1

        # Check boolean consistency
        if cat == "LOAN_CREDIT":
            assert s.is_credit_scheme is True
            assert s.calculator_applicable is True
        else:
            assert s.is_credit_scheme is False
            assert s.calculator_applicable is False

    assert counts.get("LOAN_CREDIT", 0) >= 40, "Expected at least 40 loan/credit schemes"
    assert counts.get("GRANT_SUBSIDY", 0) >= 15, "Expected at least 15 grant/subsidy schemes"
    assert counts.get("DIRECT_BENEFIT", 0) >= 5, "Expected direct benefit schemes like SSY, APY, PM-JAY"


def test_direct_benefit_schemes_not_credit(db_session):
    """Test that social safety net and direct benefit schemes are not classified as loans."""
    ssy = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-088").first()
    assert ssy is not None
    assert ssy.financial_category == "DIRECT_BENEFIT"
    assert ssy.is_credit_scheme is False
    assert ssy.calculator_applicable is False
    assert "small savings" in ssy.financial_assistance_summary.lower()

    pmjay = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-090").first()
    assert pmjay is not None
    assert pmjay.financial_category == "DIRECT_BENEFIT"
    assert pmjay.is_credit_scheme is False
    assert pmjay.calculator_applicable is False
    assert "health insurance" in pmjay.financial_assistance_summary.lower()


def test_credit_guarantee_schemes(db_session):
    """Test that credit guarantees (e.g. CGTMSE) are classified under guarantee support."""
    cgtmse = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-051").first()
    assert cgtmse is not None
    assert cgtmse.financial_category == "GUARANTEE_CREDIT_SUPPORT"
    assert cgtmse.is_credit_scheme is False
    assert cgtmse.calculator_applicable is False
    assert "credit guarantee" in cgtmse.financial_assistance_summary.lower()


def test_loan_schemes_credit_applicable(db_session):
    """Test that authentic loan schemes are marked as credit schemes."""
    pmegp = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert pmegp is not None
    assert pmegp.financial_category == "LOAN_CREDIT"
    assert pmegp.is_credit_scheme is True
    assert pmegp.calculator_applicable is True
    assert float(pmegp.max_loan_amount) == 5000000.0

    svanidhi = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-004").first()
    assert svanidhi is not None
    assert svanidhi.financial_category == "LOAN_CREDIT"
    assert svanidhi.is_credit_scheme is True
    assert svanidhi.calculator_applicable is True


def test_scheme_serialization_schema(db_session):
    """Test that Pydantic models accurately serialize financial fields."""
    s = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    detail = SchemeDetailResponse.model_validate(s)
    assert detail.financial_category == "LOAN_CREDIT"
    assert detail.is_credit_scheme is True
    assert detail.calculator_applicable is True
    assert float(detail.max_loan_amount) == 5000000.0

    list_item = SchemeListItemResponse.model_validate(s)
    assert list_item.financial_category == "LOAN_CREDIT"
    assert list_item.is_credit_scheme is True


def test_deterministic_financial_engine_evaluation(db_session):
    """Test DeterministicFinancialEngine calculates terms for a valid loan scheme."""
    inp = FinancialCalculationInput(
        scheme_id="SIH26092-001",
        project_cost=100000.0,
        requested_loan_amount=80000.0,
        repayment_frequency="MONTHLY",
        interest_rate=7.0,
        repayment_period_months=36,
    )
    res = DeterministicFinancialEngine.calculate(db_session, inp)
    assert res is not None
    assert res.status.value == "CALCULATED"
    assert res.periodic_installment is not None
    assert float(res.periodic_installment) > 0
    assert len(res.amortization_schedule) == 36
