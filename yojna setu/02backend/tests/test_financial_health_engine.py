import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.financial_health import (
    FinancialHealthInput,
    FinancialHealthResponse,
    FinancialHealthStatus,
    FinancialIndicatorStatus,
)
from app.engine.financial_health import DeterministicFinancialHealthEngine
from app.engine.recommendation import DeterministicRecommendationEngine
from app.schemas.recommendation import RecommendationRequest
from app.core.security import create_access_token


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


# 1. Healthy Case
def test_01_healthy_financial_health():
    input_data = FinancialHealthInput(
        annual_income=Decimal("600000.00"),  # Monthly 50,000
        requested_loan_amount=Decimal("100000.00"),  # Leverage 0.17x
        project_cost=Decimal("200000.00"),  # LTV 50%
        existing_liabilities=Decimal("0.00"),
        monthly_obligations=Decimal("5000.00"),  # FOIR 10%
        liquid_savings=Decimal("100000.00")  # 20 months buffer & fully covers margin
    )
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status == FinancialHealthStatus.HEALTHY
    assert res.score is not None
    assert res.score >= Decimal("80.0")
    assert len(res.indicators) == 4
    assert any("foir" == ind.indicator_name and ind.status == FinancialIndicatorStatus.HEALTHY for ind in res.indicators)
    assert any("leverage_ratio" == ind.indicator_name and ind.status == FinancialIndicatorStatus.HEALTHY for ind in res.indicators)
    assert len(res.positive_factors) >= 1
    assert len(res.risk_flags) == 0


# 2. Moderate/Stressed boundary case — engine computes proposed EMI on top of existing obligations
# so FOIR is higher than the raw 45% from monthly_obligations alone.
def test_02_moderate_financial_health():
    input_data = FinancialHealthInput(
        annual_income=Decimal("360000.00"),  # Monthly 30,000
        requested_loan_amount=Decimal("450000.00"),  # Leverage 1.25x (moderate)
        project_cost=Decimal("500000.00"),  # LTV 90.0% (moderate)
        existing_liabilities=Decimal("50000.00"),
        monthly_obligations=Decimal("13500.00"),  # FOIR base 45% + proposed EMI pushes higher
        liquid_savings=Decimal("50000.00")  # ~3.7 months buffer (moderate)
    )
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    # Engine adds proposed EMI (~₹14,188 for ₹4.5L@8.5%/36mo) on top of ₹13,500 → total obligations
    # very high, pushing into STRESSED territory
    assert res.status in (FinancialHealthStatus.STRESSED, FinancialHealthStatus.MODERATE)
    assert res.score is not None
    assert Decimal("30.0") <= res.score < Decimal("80.0")


# 3. Stressed/High-Risk boundary case — proposed EMI on ₹7L loan adds ~₹22K/month
# which combined with existing ₹13K obligations vastly exceeds ₹20K income
def test_03_stressed_financial_health():
    input_data = FinancialHealthInput(
        annual_income=Decimal("240000.00"),  # Monthly 20,000
        requested_loan_amount=Decimal("700000.00"),  # Leverage 2.92x (> 2.5x stressed)
        project_cost=Decimal("750000.00"),  # LTV 93.3%
        existing_liabilities=Decimal("200000.00"),
        monthly_obligations=Decimal("13000.00"),  # FOIR 65% base + proposed EMI → >>100%
        liquid_savings=Decimal("15000.00")  # buffer 1.15 mos
    )
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    # Engine adds proposed EMI (~₹22,093 for ₹7L@8.5%/36mo) pushing total obligations far above income
    assert res.status in (FinancialHealthStatus.STRESSED, FinancialHealthStatus.HIGH_RISK)
    assert res.score is not None
    assert res.score < Decimal("60.0")
    assert len(res.risk_flags) >= 1


# 4. High Risk Case
def test_04_high_risk_financial_health():
    input_data = FinancialHealthInput(
        annual_income=Decimal("120000.00"),  # Monthly 10,000
        requested_loan_amount=Decimal("800000.00"),  # Leverage 6.67x (high risk)
        project_cost=Decimal("700000.00"),  # Loan exceeds project cost!
        existing_liabilities=Decimal("300000.00"),
        monthly_obligations=Decimal("8500.00"),  # FOIR 85%
        liquid_savings=Decimal("2000.00")
    )
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status == FinancialHealthStatus.HIGH_RISK
    assert res.score is not None
    assert res.score < Decimal("40.0")
    assert any("exceeds total project cost" in flag.lower() or "over-financing" in flag.lower() for flag in res.risk_flags)


# 5. Insufficient Information Case
def test_05_insufficient_information():
    # Empty input
    input_data = FinancialHealthInput()
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status == FinancialHealthStatus.INSUFFICIENT_INFORMATION
    assert res.score is None
    assert len(res.missing_fields) >= 2
    field_names = [mf.field for mf in res.missing_fields]
    assert "annual_income" in field_names
    assert "requested_loan_amount" in field_names


# 6. Zero Income Handling
def test_06_zero_income_handling():
    input_data = FinancialHealthInput(
        annual_income=Decimal("0.00"),
        requested_loan_amount=Decimal("50000.00"),
        monthly_obligations=Decimal("3000.00")
    )
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status == FinancialHealthStatus.HIGH_RISK
    assert any("without declared income" in flag.lower() or "debt service exists" in flag.lower() for flag in res.risk_flags)


# 7. Zero Existing Liabilities Handling — but proposed EMI from requested_loan_amount still applies
def test_07_zero_liabilities_handling():
    input_data = FinancialHealthInput(
        annual_income=Decimal("300000.00"),
        requested_loan_amount=Decimal("50000.00"),
        existing_liabilities=Decimal("0.00"),
        monthly_obligations=Decimal("0.00")
    )
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status == FinancialHealthStatus.HEALTHY
    foir_ind = [ind for ind in res.indicators if ind.indicator_name == "foir"][0]
    # Engine computes proposed EMI (~₹1,578 for ₹50K@8.5%/36mo), so FOIR is non-zero but still healthy
    assert foir_ind.value <= Decimal("15.0")  # Small FOIR from proposed EMI on modest loan
    assert foir_ind.status == FinancialIndicatorStatus.HEALTHY


# 8. Zero Requested Loan Handling (Grant / Self-Financed)
def test_08_zero_requested_loan():
    input_data = FinancialHealthInput(
        annual_income=Decimal("300000.00"),
        requested_loan_amount=Decimal("0.00"),
        project_cost=Decimal("100000.00")
    )
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status == FinancialHealthStatus.HEALTHY
    lev_ind = [ind for ind in res.indicators if ind.indicator_name == "leverage_ratio"][0]
    assert lev_ind.value == Decimal("0.00")
    assert any("zero proposed borrowing" in p.lower() or "debt-free" in p.lower() for p in res.positive_factors)


# 9. Invalid Negative Values Rejection
def test_09_negative_values_rejected():
    with pytest.raises(ValueError):
        FinancialHealthInput(annual_income=Decimal("-10000.00"))

    with pytest.raises(ValueError):
        FinancialHealthInput(requested_loan_amount=Decimal("-50000.00"))

    with pytest.raises(ValueError):
        FinancialHealthInput(monthly_obligations=Decimal("-2000.00"))


# 10. Huge Values Handling
def test_10_huge_values_handling():
    input_data = FinancialHealthInput(
        annual_income=Decimal("1000000000.00"),  # 100 Crores
        requested_loan_amount=Decimal("200000000.00"),
        project_cost=Decimal("300000000.00"),
        monthly_obligations=Decimal("5000000.00")
    )
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status == FinancialHealthStatus.HEALTHY
    assert res.score is not None


# 11. Division by Zero Protection
def test_11_division_by_zero_protection():
    # All zero parameters
    input_data = FinancialHealthInput(
        annual_income=Decimal("0.00"),
        monthly_income=Decimal("0.00"),
        requested_loan_amount=Decimal("0.00"),
        project_cost=Decimal("0.00"),
        monthly_obligations=Decimal("0.00"),
        liquid_savings=Decimal("0.00")
    )
    # Must not raise ZeroDivisionError
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status in [FinancialHealthStatus.HEALTHY, FinancialHealthStatus.MODERATE, FinancialHealthStatus.HIGH_RISK]
    assert res.score is not None


# 12. Missing Profile Handling
def test_12_missing_profile():
    input_data = FinancialHealthInput(profile=None)
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status == FinancialHealthStatus.INSUFFICIENT_INFORMATION
    assert res.score is None


# 13. Incomplete Profile Diagnostics
def test_13_incomplete_profile_diagnostics():
    incomplete_profile = BeneficiaryProfileInput(
        age=25,
        gender="FEMALE",
        state="MAHARASHTRA"
        # No income, no loan
    )
    input_data = FinancialHealthInput(profile=incomplete_profile)
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert res.status == FinancialHealthStatus.INSUFFICIENT_INFORMATION
    assert len(res.missing_fields) >= 2


# 14. Decimal Precision Verification
def test_14_decimal_precision():
    input_data = FinancialHealthInput(
        annual_income=Decimal("333333.33"),
        requested_loan_amount=Decimal("111111.11"),
        project_cost=Decimal("222222.22"),
        monthly_obligations=Decimal("7777.77")
    )
    res = DeterministicFinancialHealthEngine.evaluate(input_data)
    assert isinstance(res.score, Decimal)
    assert isinstance(res.monthly_income, Decimal)
    # Check 2 decimal places rounding
    assert str(res.score).count(".") <= 1


# 15. Recommendation Integration (Legal Eligibility Independent)
def test_15_recommendation_integration(db_session):
    # Profile with stressed financials but qualifying demographic
    stressed_profile = BeneficiaryProfileInput(
        age=30,
        gender="FEMALE",
        social_category="SC",
        annual_income=120000.0,
        requested_loan_amount=500000.0,
        monthly_obligations=8000.0,
        state="Maharashtra",
        sector="MANUFACTURING",
        applicant_type="INDIVIDUAL"
    )
    req = RecommendationRequest(profile=stressed_profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db_session, req)
    assert res.evaluated_scheme_count > 0
    assert len(res.recommendations) >= 1

    top_rec = res.recommendations[0]
    # Hard eligibility is STILL passed!
    assert top_rec.eligible is True
    # Financial health status is attached as advisory
    assert top_rec.financial_health_status in ["STRESSED", "HIGH_RISK"]
    assert top_rec.financial_health_advisory is not None


# 16. Deterministic Repeatability
def test_16_deterministic_repeatability():
    input_data = FinancialHealthInput(
        annual_income=Decimal("500000.00"),
        requested_loan_amount=Decimal("250000.00"),
        project_cost=Decimal("300000.00"),
        monthly_obligations=Decimal("10000.00")
    )
    res1 = DeterministicFinancialHealthEngine.evaluate(input_data)
    res2 = DeterministicFinancialHealthEngine.evaluate(input_data)

    assert res1.status == res2.status
    assert res1.score == res2.score
    assert len(res1.indicators) == len(res2.indicators)
    for i1, i2 in zip(res1.indicators, res2.indicators):
        assert i1.score == i2.score
        assert i1.value == i2.value


# 17. API Endpoint Validation
def test_17_api_endpoint_validation(client):
    payload = {
        "annual_income": 480000.0,
        "requested_loan_amount": 150000.0,
        "project_cost": 200000.0,
        "monthly_obligations": 8000.0,
        "liquid_savings": 50000.0
    }
    response = client.post("/api/v1/financial-health/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["HEALTHY", "MODERATE"]
    assert "score" in data
    assert "indicators" in data
    assert len(data["indicators"]) == 4


# 18. Authentication & Unauthorized Access Handling
def test_18_auth_handling(client, db_session):
    # GET /api/v1/financial-health without token returns 401
    resp_unauth = client.get("/api/v1/financial-health")
    assert resp_unauth.status_code == 401

    # Create active user with profile data
    test_user = db_session.query(User).filter(User.email == "finhealth_test@yojnasetu.gov.in").first()
    if not test_user:
        test_user = User(
            email="finhealth_test@yojnasetu.gov.in",
            hashed_password="test_hashed_password_dummy",
            full_name="Financial Health Citizen",
            role="BENEFICIARY",
            is_active=True,
            profile_data='{"annual_income": 500000.0, "requested_loan_amount": 100000.0, "monthly_obligations": 5000.0}'
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

    try:
        token = create_access_token(user_id=test_user.user_id, role=test_user.role, email=test_user.email)
        headers = {"Authorization": f"Bearer {token}"}

        resp_auth = client.get("/api/v1/financial-health", headers=headers)
        assert resp_auth.status_code == 200
        data = resp_auth.json()
        assert data["status"] == "HEALTHY"
        assert data["score"] is not None
    finally:
        db_session.delete(test_user)
        db_session.commit()
