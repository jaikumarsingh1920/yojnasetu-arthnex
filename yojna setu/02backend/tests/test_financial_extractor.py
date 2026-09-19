"""
Unit tests for FinancialFactExtractor and Partner Channel Navigation Separation.
"""
import pytest
from app.services.ingestion.financial_extractor import FinancialFactExtractor
from app.engine.recommendation import DeterministicRecommendationEngine
from app.schemas.recommendation import RecommendationRequest
from app.schemas.profile import BeneficiaryProfileInput
from app.db.session import SessionLocal


def test_inr_normalization():
    extractor = FinancialFactExtractor()

    assert extractor.parse_inr_amount("10", "lakh") == 1000000.0
    assert extractor.parse_inr_amount("10", "lakhs") == 1000000.0
    assert extractor.parse_inr_amount("10,00,000") == 1000000.0
    assert extractor.parse_inr_amount("1", "million") == 1000000.0
    assert extractor.parse_inr_amount("1.5", "crore") == 15000000.0
    assert extractor.parse_inr_amount("50", "thousand") == 50000.0


def test_strict_loan_vs_project_cost_distinction():
    extractor = FinancialFactExtractor()

    # Case 1: Project cost only
    text_proj = "Under this scheme, maximum project cost up to ₹25 lakh is eligible for manufacturing."
    facts_proj = extractor.extract_financial_facts(text_proj)
    assert facts_proj["max_project_cost"] == 2500000.0
    assert facts_proj["max_loan_amount"] is None
    assert "max_project_cost" in facts_proj["provenance"]

    # Case 2: Loan amount only
    text_loan = "Beneficiaries can avail term loan up to ₹10 lakh with bank assistance."
    facts_loan = extractor.extract_financial_facts(text_loan)
    assert facts_loan["max_loan_amount"] == 1000000.0
    assert facts_loan["max_project_cost"] is None
    assert "max_loan_amount" in facts_loan["provenance"]

    # Case 3: Both project cost and loan facility distinguished
    text_both = (
        "Project cost ceiling of Rs. 50 Lakh for infrastructure. "
        "Maximum loan amount is ₹40 lakh with capital subsidy of 25%."
    )
    facts_both = extractor.extract_financial_facts(text_both)
    assert facts_both["max_project_cost"] == 5000000.0
    assert facts_both["max_loan_amount"] == 4000000.0
    assert facts_both["subsidy_percentage"] == 25.0


def test_subsidy_margin_and_tenure_extraction():
    extractor = FinancialFactExtractor()
    text = (
        "Government provides margin money subsidy of 35% for rural areas. "
        "Promoter contribution is 5%. "
        "Interest rate of 6% p.a. with repayment period of 7 years."
    )
    facts = extractor.extract_financial_facts(text)
    assert facts["subsidy_percentage"] == 35.0
    assert facts["margin_money_percentage"] == 5.0
    assert facts["interest_rate"] == 6.0
    assert facts["repayment_period_months"] == 84  # 7 * 12


def test_partner_channel_navigation_separation():
    """Verify that schemes without verified partner mappings route to OFFICIAL_DIRECT_PORTAL."""
    db = SessionLocal()

    profile = BeneficiaryProfileInput(
        age=28,
        gender="MALE",
        social_category="SC",
        state="Maharashtra",
        business_type="NEW",
        annual_family_income=90000.0,
        required_loan_amount=90000.0
    )

    req = RecommendationRequest(profile=profile, top_k=5)
    response = DeterministicRecommendationEngine.get_recommendations(db, req)
    assert len(response.recommendations) > 0

    for rec in response.recommendations:
        if rec.has_verified_partner_mapping:
            assert rec.application_channel == "CHANNEL_PARTNER_LOCATOR"
        else:
            assert rec.application_channel == "OFFICIAL_DIRECT_PORTAL"
            assert rec.is_direct_portal_scheme is True

    db.close()
