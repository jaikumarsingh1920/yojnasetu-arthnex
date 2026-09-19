"""
Integration Test Suite for Citizen-Facing Financial Health Engine Flow (YojnaSetu).
Validates:
  TEST A: Standard complete citizen financial inputs -> Deterministic assessment displayed with all figures.
  TEST B: Missing income -> Asks for income and expenses, does not guess or fabricate numbers.
  TEST C: Missing interest rate -> Discloses lender rate is unstated, does not invent interest rate.
  TEST D: Non-credit scheme -> Financial Health is NOT_APPLICABLE (grants/subsidies/scholarships).
  TEST E: Multi-turn Chatbot collecting financial context over turns -> Executes deterministic engine on "Can I afford it?".
  TEST F: Two eligible schemes with different financial implications -> Explanation reflects financial fit without overriding statutory eligibility.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.financial_health import (
    FinancialHealthInput,
    FinancialHealthResponse,
    FinancialHealthStatus,
    SchemeFinancialSuitability,
)
from app.engine.financial_health import DeterministicFinancialHealthEngine
from app.engine.recommendation import DeterministicRecommendationEngine
from app.schemas.recommendation import RecommendationRequest
from app.schemas.ai import AIChatRequest
from app.ai.agent import GPTCopilotAgent
from app.ai.copilot_router import AICopilotQueryRouter


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


# ===========================================================================
# TEST A: Standard complete citizen financial inputs -> Full result displayed
# ===========================================================================
def test_A_complete_citizen_financial_health_result(client, db):
    """
    TEST A:
    Income ₹30,000, Expenses ₹18,000, Existing EMI ₹3,000, Loan ₹2,00,000, Valid rate/tenure
    -> Financial Health result displayed deterministically with all underlying numbers.
    """
    payload = {
        "monthly_income": 30000.0,
        "monthly_expenses": 18000.0,
        "monthly_obligations": 3000.0,
        "requested_loan_amount": 200000.0,
        "project_cost": 240000.0,
        "interest_rate": 8.5,
        "tenure_months": 36,
        "profile": {
            "monthly_income": 30000.0,
            "monthly_expenses": 18000.0,
            "monthly_obligations": 3000.0,
            "requested_loan_amount": 200000.0,
            "project_cost": 240000.0,
        }
    }

    res = client.post("/api/v1/financial-health/assess", json=payload)
    assert res.status_code == 200, f"Assess failed: {res.text}"
    data = res.json()

    # Verify status is one of the valid deterministic statuses
    assert data["status"] in ("HEALTHY", "MODERATE", "STRESSED")
    assert "summary_headline" in data
    assert len(data["summary_headline"]) > 0

    # Verify underlying numbers are transparently returned
    assert data["monthly_income"] == 30000.0
    assert data["monthly_expenses"] == 18000.0
    assert data["existing_monthly_obligations"] == 3000.0
    assert data["proposed_monthly_emi"] is not None
    assert data["proposed_monthly_emi"] > 0
    assert data["total_monthly_obligations"] == data["existing_monthly_obligations"] + data["proposed_monthly_emi"]

    # Verify disposable cushion reflects income - expenses - total obligations
    expected_disposable = 30000.0 - 18000.0 - data["total_monthly_obligations"]
    assert abs(data["estimated_disposable_income"] - expected_disposable) < 1.0

    # Verify repayment burden (debt to income ratio) is deterministically computed
    expected_dti = round((data["total_monthly_obligations"] / 30000.0) * 100, 1)
    assert abs(data["debt_to_income_ratio"] - expected_dti) < 0.5


# ===========================================================================
# TEST B: Missing income -> Asks for income, does not guess or fabricate
# ===========================================================================
def test_B_missing_income_asks_without_guessing(db):
    """
    TEST B:
    Missing income
    -> asks for income and expenses, does not guess.
    """
    session_id = "test_sess_missing_income"
    req = AIChatRequest(
        message="I need a ₹3 lakh loan. Can I afford it?",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)

    # Must ask citizen for income and expenses
    lower_reply = res.answer.lower()
    assert "income" in lower_reply or "earn" in lower_reply, f"Expected prompt for income, got: {res.answer}"
    assert "expense" in lower_reply or "spend" in lower_reply or "approximate" in lower_reply

    # Must NOT fabricate a healthy or stressed rating when income is unknown
    assert "status: healthy" not in lower_reply
    assert "comfortable" not in lower_reply


# ===========================================================================
# TEST C: Missing interest rate -> Does not invent interest rate
# ===========================================================================
def test_C_missing_interest_rate_discloses_without_inventing(db):
    """
    TEST C:
    Missing interest rate
    -> does not invent interest rate, discloses lender rate is unstated.
    """
    # Create or retrieve a credit scheme that has no specified interest rate
    scheme_unstated = Scheme(
        scheme_id="TEST-UNSTATED-RATE",
        scheme_name="Test Enterprise Credit Facility",
        loan_available="YES",
        max_loan_amount=Decimal("500000.00"),
        interest_rate_min=None,
        interest_rate_max=None,
        repayment_period_min_months=None,
        repayment_period_max_months=None,
    )

    profile = BeneficiaryProfileInput(
        monthly_income=35000.0,
        monthly_expenses=20000.0,
        monthly_obligations=2000.0,
        requested_loan_amount=200000.0,
    )

    suit_res = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
        scheme=scheme_unstated,
        profile=profile,
        db=db
    )

    # Reason must explicitly disclose that interest rate / tenure is not specified
    assert "interest rate/tenure is not specified" in suit_res.suitability_reason
    # Must NOT invent an EMI
    assert suit_res.estimated_emi is None


# ===========================================================================
# TEST D: Scheme is non-credit -> Financial Health is NOT APPLICABLE
# ===========================================================================
def test_D_non_credit_scheme_is_not_applicable(db):
    """
    TEST D:
    Scheme is non-credit (grant/subsidy/scholarship)
    -> Financial Health is NOT APPLICABLE.
    """
    non_credit_scheme = Scheme(
        scheme_id="TEST-GRANT-SCHEME",
        scheme_name="National Artisan Tool-Kit Grant",
        loan_available="NO",
        support_type="GRANT",
        grant_available="YES",
        grant_amount=Decimal("25000.00"),
    )

    profile = BeneficiaryProfileInput(
        monthly_income=25000.0,
        monthly_expenses=15000.0,
        requested_loan_amount=25000.0,
    )

    suit_res = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
        scheme=non_credit_scheme,
        profile=profile,
        db=db
    )

    assert suit_res.suitability == SchemeFinancialSuitability.NOT_APPLICABLE
    assert "not applicable" in suit_res.suitability_reason.lower()
    assert "non-credit" in suit_res.suitability_reason.lower()
    assert suit_res.estimated_emi is None


# ===========================================================================
# TEST E: Chatbot collects financial info across turns -> Executes deterministic engine
# ===========================================================================
def test_E_chatbot_multi_turn_affordability_flow(db):
    """
    TEST E:
    Chatbot collects financial information over multiple turns and then asks:
    'Can I afford this loan?'
    -> deterministic engine executes with grounded result.
    """
    session_id = "test_sess_multi_turn_fin_health"

    # Turn 1: Citizen provides income
    r1 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="I earn 30,000 per month.",
        session_id=session_id
    ))
    assert "30,000" in r1.answer or "30000" in r1.answer

    # Turn 2: Citizen provides expenses
    r2 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="My monthly expenses are around 18,000.",
        session_id=session_id
    ))
    assert "18,000" in r2.answer or "18000" in r2.answer

    # Turn 3: Citizen provides existing EMI obligations
    r3 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="I already pay 3,000 EMI.",
        session_id=session_id
    ))
    assert "3,000" in r3.answer or "3000" in r3.answer

    # Turn 4: Citizen requests loan amount
    r4 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="I need a 2 lakh loan.",
        session_id=session_id
    ))
    assert "200,000" in r4.answer or "2,00,000" in r4.answer or "200000" in r4.answer or "2 lakh" in r4.answer.lower()

    # Turn 5: Citizen asks: "Can I afford it?"
    r5 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="Can I afford it?",
        session_id=session_id
    ))

    # Must execute the deterministic financial health engine!
    reply_lower = r5.answer.lower()
    assert "financial health" in reply_lower or "affordability" in reply_lower
    # Must show status category
    assert any(status in reply_lower for status in ["comfortable", "manageable", "burden"])
    # Must display underlying numbers
    assert "30,000" in r5.answer
    assert "18,000" in r5.answer
    assert "3,000" in r5.answer
    assert "proposed emi" in reply_lower or "emi" in reply_lower
    assert "remaining" in reply_lower or "disposable" in reply_lower


# ===========================================================================
# TEST F: Two eligible schemes with different financial fit -> Explanation reflects fit
# ===========================================================================
def test_F_recommendation_reflects_financial_fit_without_overriding_eligibility(db):
    """
    TEST F:
    Two eligible schemes have different financial implications.
    -> recommendation explanation reflects financial fit without overriding statutory eligibility.
    -> financially unsuitable scheme is not ranked as 'BEST_MATCH'.
    """
    # Profile with moderate income (₹25,000/mo) and requested loan ₹50,000
    profile = BeneficiaryProfileInput(
        age=30,
        state="Uttar Pradesh",
        gender="MALE",
        applicant_type="INDIVIDUAL",
        monthly_income=25000.0,
        monthly_expenses=18000.0,
        monthly_obligations=5000.0,
        requested_loan_amount=50000.0,
    )

    req = RecommendationRequest(
        profile=profile,
        top_k=5
    )

    res = DeterministicRecommendationEngine.get_recommendations(db=db, req=req)
    assert len(res.recommendations) > 0, "Expected recommendations"

    # All returned recommendations must be statutorily eligible
    for rec in res.recommendations:
        assert rec.eligible is True
        assert rec.eligibility_status == "ELIGIBLE"

        # If a scheme is FINANCIALLY_UNSUITABLE, it must NOT be BEST_MATCH
        if rec.financial_suitability == "FINANCIALLY_UNSUITABLE":
            assert rec.match_tier != "BEST_MATCH", f"Scheme {rec.scheme_id} cannot be BEST_MATCH when financially unsuitable"
            assert "repayment burden" in (rec.comparative_ranking_reason or "").lower() or "high repayment" in (rec.financial_suitability_reason or "").lower()
