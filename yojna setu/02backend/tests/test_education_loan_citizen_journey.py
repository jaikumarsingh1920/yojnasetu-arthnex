"""
End-to-End Test Suite for Education Loan and 13-Step Citizen Journey.

Verifies end-to-end backend behavior for the complete Citizen Journey:
Step 1: User describes need in natural language.
Step 2: Profile information is extracted.
Step 3: Relevant schemes are identified.
Step 4: Statutory eligibility is checked.
Step 5: Financial fit is checked.
Step 6: Recommendations are ranked.
Step 7: Chatbot explains why.
Step 8: User can ask follow-up questions.
Step 9: User can compare schemes.
Step 10: User can discover application channel.
Step 11: User can find nearest suitable partner.
Step 12: Partner coordinates/distance are returned.
Step 13: Correct official application destination is returned.

Strict Guardrail:
Zero fake application tracking states (NO submitted, under review, approved, rejected).
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.recommendation import RecommendationRequest
from app.schemas.eligibility import SchemeEligibilityStatus
from app.schemas.financial_health import SchemeFinancialSuitability
from app.schemas.ai import AIChatRequest
from app.ai.extractor import NaturalLanguageProfileExtractor
from app.ai.copilot_router import AICopilotQueryRouter
from app.ai.agent import GPTCopilotAgent
from app.ai.tools import CopilotTools
from app.engine.recommendation import DeterministicRecommendationEngine
from app.engine.eligibility import DeterministicEligibilityEngine
from app.engine.financial_health import DeterministicFinancialHealthEngine
from app.services.geo_partner_service import GeoPartnerLocatorService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. NATURAL LANGUAGE NEED -> STRUCTURED PROFILE EXTRACTION (Steps 1 & 2)
# ==============================================================================

def test_step_1_and_2_natural_language_to_profile_extraction():
    """
    Step 1: User describes need in natural language.
    Step 2: Profile information is extracted with deterministic confidence.
    """
    query = (
        "I am a 21-year-old student from Uttar Pradesh belonging to SC category "
        "with family income 2.5 lakh. I got admission in B.Tech engineering and need 5 lakh education loan."
    )

    result = NaturalLanguageProfileExtractor.extract_profile(query)
    profile = result.extracted_profile

    # Verifications of extracted fields
    assert profile.age == 21, f"Expected age 21, got {profile.age}"
    assert profile.state == "UTTAR_PRADESH", f"Expected UTTAR_PRADESH, got {profile.state}"
    assert profile.social_category == "SC", f"Expected SC, got {profile.social_category}"
    assert profile.is_sc is True, "Expected is_sc to be True"
    assert profile.annual_income == 250000.0, f"Expected annual income 250000, got {profile.annual_income}"
    assert profile.applicant_type == "STUDENT", f"Expected STUDENT, got {profile.applicant_type}"
    assert profile.employment_status == "STUDENT", f"Expected STUDENT, got {profile.employment_status}"
    assert profile.education_level == "GRADUATE", f"Expected GRADUATE for B.Tech, got {profile.education_level}"
    assert profile.sector == "EDUCATION", f"Expected EDUCATION sector, got {profile.sector}"
    assert profile.activity_type == "EDUCATION", f"Expected EDUCATION activity, got {profile.activity_type}"
    assert profile.requested_loan_amount == 500000.0, f"Expected loan 500000, got {profile.requested_loan_amount}"


def test_hindi_natural_language_student_extraction():
    """
    Verifies Hindi natural language extraction for a student needing an education loan.
    """
    query = "मैं उत्तर प्रदेश से 20 साल का छात्र हूँ, अनुसूचित जाति वर्ग से, आय 2 लाख है, बीटेक के लिए 4 लाख का शिक्षा ऋण चाहिए।"
    result = NaturalLanguageProfileExtractor.extract_profile(query)
    p = result.extracted_profile

    assert p.age == 20
    assert p.state == "UTTAR_PRADESH"
    assert p.social_category == "SC"
    assert p.is_sc is True
    assert p.annual_income == 200000.0
    assert p.applicant_type == "STUDENT"
    assert p.sector == "EDUCATION"
    assert p.requested_loan_amount == 400000.0


# ==============================================================================
# 2. SCHEME DISCOVERY, STATUTORY ELIGIBILITY & RANKING (Steps 3, 4, 5, 6)
# ==============================================================================

def test_step_3_4_5_6_discovery_eligibility_financial_fit_and_ranking(db_session):
    """
    Step 3: Relevant schemes are identified from candidate universe.
    Step 4: Statutory eligibility is strictly checked.
    Step 5: Financial fit and feasibility are evaluated.
    Step 6: Recommendations are ranked deterministically.
    """
    profile = BeneficiaryProfileInput(
        age=21,
        gender="MALE",
        social_category="SC",
        is_sc=True,
        state="UTTAR_PRADESH",
        annual_income=250000.0,
        requested_loan_amount=500000.0,
        applicant_type="STUDENT",
        employment_status="STUDENT",
        education_level="GRADUATE",
        sector="EDUCATION"
    )

    # Step 3 & 4: Statutory Eligibility Engine
    csis_scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-083").first()
    nsfdc_scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-056").first()
    nstfdc_scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-059").first()
    ambedkar_scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-196").first()

    assert csis_scheme is not None
    assert nsfdc_scheme is not None
    assert nstfdc_scheme is not None
    assert ambedkar_scheme is not None

    # Evaluate CSIS (Central Sector Interest Subsidy) -> Must be ELIGIBLE (income 2.5L <= 4.5L)
    csis_elig = DeterministicEligibilityEngine.evaluate_scheme(csis_scheme, profile)
    assert csis_elig.status == SchemeEligibilityStatus.ELIGIBLE

    # Evaluate NSFDC ELS (for SC students) -> Must be ELIGIBLE
    nsfdc_elig = DeterministicEligibilityEngine.evaluate_scheme(nsfdc_scheme, profile)
    assert nsfdc_elig.status == SchemeEligibilityStatus.ELIGIBLE

    # Evaluate NSTFDC ASRY (for ST students) -> Must be INELIGIBLE for SC student
    nstfdc_elig = DeterministicEligibilityEngine.evaluate_scheme(nstfdc_scheme, profile)
    assert nstfdc_elig.status == SchemeEligibilityStatus.INELIGIBLE

    # Evaluate Dr. Ambedkar Scheme (for OBC/EBC overseas) -> Must be INELIGIBLE for SC student
    ambedkar_elig = DeterministicEligibilityEngine.evaluate_scheme(ambedkar_scheme, profile)
    assert ambedkar_elig.status == SchemeEligibilityStatus.INELIGIBLE

    # Step 5: Financial Fit Evaluation
    csis_fin = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
        scheme=csis_scheme,
        profile=profile,
        db=db_session
    )
    assert csis_fin.suitability == SchemeFinancialSuitability.STRONG_FIT
    assert csis_fin.estimated_emi is not None
    assert csis_fin.estimated_emi > 0

    nsfdc_fin = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
        scheme=nsfdc_scheme,
        profile=profile,
        db=db_session
    )
    assert nsfdc_fin.suitability in (SchemeFinancialSuitability.STRONG_FIT, SchemeFinancialSuitability.POSSIBLE_FIT)

    # Step 6: Recommendation Ranking
    req = RecommendationRequest(profile=profile, top_k=5)
    rec_res = DeterministicRecommendationEngine.get_recommendations(db_session, req)

    assert rec_res.eligible_scheme_count > 0
    top_ids = [r.scheme_id for r in rec_res.recommendations]

    # CSIS and NSFDC ELS must occupy the top ranks
    assert "SIH26092-083" in top_ids[:2], "CSIS must be in top 2 recommendations"
    assert "SIH26092-056" in top_ids[:2], "NSFDC ELS must be in top 2 recommendations"
    # Tribal and OBC exclusive schemes must NOT leak into SC recommendations
    assert "SIH26092-059" not in top_ids, "NSTFDC (ST) must not leak to SC student"
    assert "SIH26092-196" not in top_ids, "Dr. Ambedkar (OBC) must not leak to SC student"

    # Top item verification
    top_item = rec_res.recommendations[0]
    assert top_item.eligible is True
    assert top_item.financial_category == "LOAN_CREDIT"
    assert top_item.is_credit_scheme is True
    assert top_item.calculator_applicable is True
    assert top_item.official_portal is not None


# ==============================================================================
# 3. CHATBOT EXPLAINABILITY & FOLLOW-UPS (Steps 7 & 8)
# ==============================================================================

def test_step_7_chatbot_explains_why(db_session):
    """
    Step 7: Chatbot explains why the education loan scheme was recommended.
    """
    profile = BeneficiaryProfileInput(
        age=21,
        social_category="SC",
        is_sc=True,
        state="UTTAR_PRADESH",
        annual_income=250000.0,
        requested_loan_amount=500000.0,
        applicant_type="STUDENT",
        employment_status="STUDENT",
        education_level="GRADUATE",
        sector="EDUCATION"
    )

    chat_req = AIChatRequest(
        message="Why is CSIS recommended for me?",
        scheme_id="SIH26092-083",
        profile=profile,
        session_id="session_test_why_match"
    )
    res = GPTCopilotAgent.process_query(db_session, chat_req)

    assert res.intent == "WHY_MATCH_QUERY"
    # Grounded explanation must mention key statutory facts
    assert "100% Interest Subsidy" in res.answer or "Interest Subsidy" in res.answer
    assert "moratorium" in res.answer.lower()
    assert "vidyalakshmi" in res.answer.lower()
    assert res.actions is not None
    assert len(res.actions) > 0


def test_step_8_follow_up_documents_and_financials(db_session):
    """
    Step 8: User can ask follow-up questions (documents checklist and financial terms).
    """
    profile = BeneficiaryProfileInput(
        age=21,
        social_category="SC",
        is_sc=True,
        state="UTTAR_PRADESH",
        annual_income=250000.0,
        requested_loan_amount=500000.0,
        applicant_type="STUDENT",
        employment_status="STUDENT",
        sector="EDUCATION"
    )

    # Follow-up A: Documents
    doc_req = AIChatRequest(
        message="What documents are required for this scheme?",
        scheme_id="SIH26092-083",
        profile=profile,
        session_id="session_test_followup"
    )
    doc_res = GPTCopilotAgent.process_query(db_session, doc_req)

    assert doc_res.intent == "DOCUMENT_QUERY"
    assert "Income Certificate" in doc_res.answer or "Admission Letter" in doc_res.answer
    assert any(card.card_type == "DOCUMENT_CHECKLIST" for card in doc_res.rich_cards)

    # Follow-up B: Financial / EMI Calculation
    fin_req = AIChatRequest(
        message="Calculate EMI for 5 lakh loan at 11.5% for 5 years",
        scheme_id="SIH26092-083",
        profile=profile,
        session_id="session_test_followup"
    )
    fin_res = GPTCopilotAgent.process_query(db_session, fin_req)
    assert fin_res.intent == "FINANCIAL_QUERY"
    assert fin_res.financial_calculation is not None
    sched = fin_res.financial_calculation.get("amortization_schedule") or fin_res.financial_calculation.get("schedule", [])
    assert len(sched) > 0
    assert sched[0]["installment_amount"] > 0


# ==============================================================================
# 4. SCHEME COMPARISON (Step 9)
# ==============================================================================

def test_step_9_scheme_comparison(db_session, client):
    """
    Step 9: User can compare education schemes side-by-side.
    Tests both CopilotTools internal service and GET /api/v1/schemes/compare endpoint.
    """
    # 1. CopilotTools comparison
    comp = CopilotTools.compare_schemes_structured(db_session, ["SIH26092-083", "SIH26092-056"])
    assert comp["compared_count"] == 2
    items = {s["scheme_id"]: s for s in comp["schemes"]}

    csis = items["SIH26092-083"]
    nsfdc = items["SIH26092-056"]

    # Comparative assertions
    assert "750,000" in csis["funding"]
    assert "4,000,000" in nsfdc["funding"]
    assert "100.00%" in csis["subsidy"]
    assert "6.5%" in nsfdc["interest"]
    assert "vidyalakshmi" in csis["official_portal"]
    assert "pmsuraj" in nsfdc["official_portal"]

    # 2. API Endpoint comparison
    resp = client.get("/api/v1/schemes/compare?ids=SIH26092-083,SIH26092-056")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["compared_schemes"]) == 2
    assert {s["scheme"]["scheme_id"] for s in data["compared_schemes"]} == {"SIH26092-083", "SIH26092-056"}


# ==============================================================================
# 5. APPLICATION CHANNEL & NEAREST PARTNER DISCOVERY (Steps 10, 11, 12, 13)
# ==============================================================================

def test_steps_10_11_12_13_partner_discovery_and_official_destination(db_session, client):
    """
    Step 10: User discovers authorized application channel.
    Step 11: User finds nearest suitable partner.
    Step 12: Partner coordinates and distance are returned.
    Step 13: Correct official application destination is returned.
    """
    # Coordinates for Lucknow, Uttar Pradesh
    lat, lon = 26.8467, 80.9462

    # API lookup: /api/v1/partner/nearest
    resp = client.get(f"/api/v1/partner/nearest?latitude={lat}&longitude={lon}&scheme_id=SIH26092-083&limit=5")
    assert resp.status_code == 200
    partners = resp.json()

    assert len(partners) > 0, "Nearest partner must be found for CSIS in Lucknow"
    nearest = partners[0]

    # Step 10 & 11: Partner discovered
    assert nearest["partner"]["name"] is not None
    assert nearest["distance_km"] >= 0.0

    # Step 12: Coordinates & Distance returned
    p_lat = nearest["partner"]["latitude"]
    p_lon = nearest["partner"]["longitude"]
    assert p_lat is not None and 20.0 <= p_lat <= 32.0, f"Invalid latitude: {p_lat}"
    assert p_lon is not None and 70.0 <= p_lon <= 90.0, f"Invalid longitude: {p_lon}"
    assert nearest["google_maps_url"] is not None
    assert "google.com/maps" in nearest["google_maps_url"]
    assert nearest["coordinate_precision"] is not None

    # Step 13: Official application destination
    sch = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-083").first()
    assert sch is not None
    assert sch.official_portal == "https://www.vidyalakshmi.co.in/"
    assert sch.application_channel == "Bank Branch / Financial Institution"


# ==============================================================================
# 6. ANTI-FAKE-TRACKING GUARDRAIL (Zero fake status policy)
# ==============================================================================

def test_anti_fake_application_tracking_guardrail(db_session):
    """
    Strict Guardrail Verification:
    YojnaSetu must NOT return fake application tracking states (submitted, under review, approved, rejected).
    Chatbot must explicitly clarify that YojnaSetu is a discovery platform and route users to the official portal.
    """
    profile = BeneficiaryProfileInput(
        age=21,
        social_category="SC",
        state="UTTAR_PRADESH",
        annual_income=250000.0,
        applicant_type="STUDENT",
        sector="EDUCATION"
    )

    # Test queries asking for status / tracking
    tracking_queries = [
        "Track my application",
        "What is my application status?",
        "Mera application status check karo",
        "Where is my application under review?"
    ]

    for q in tracking_queries:
        req = AIChatRequest(
            message=q,
            scheme_id="SIH26092-083",
            profile=profile,
            session_id="session_test_anti_fake"
        )
        res = GPTCopilotAgent.process_query(db_session, req)

        assert res.intent in ("APPLICATION_QUERY", "APPLICATION_TRACKING_INQUIRY")
        # Assert chatbot explicitly mentions the policy
        assert "not directly integrated" in res.answer.lower() or "does not maintain" in res.answer.lower() or "does not track" in res.answer.lower()
        # Assert no fake status is claimed
        assert "your application is approved" not in res.answer.lower()
        assert "your application is under review" not in res.answer.lower()
        assert "your application is submitted" not in res.answer.lower()
        # Assert direction to official portal
        assert "vidyalakshmi" in res.answer.lower() or "official" in res.answer.lower()
        assert any("vidyalakshmi" in (act.target_url or "") or "/locator" in (act.target_url or "") for act in res.actions)


# ==============================================================================
# 7. DETERMINISTIC FINANCIAL CALCULATIONS FOR EDUCATION LOANS
# ==============================================================================

def test_deterministic_education_loan_calculations():
    """
    Verifies that education loan EMI and interest calculations are 100% deterministic
    and use the verified financial engine formulas.
    """
    from app.engine.calculator import DeterministicFinancialEngine

    # ₹5 Lakh loan at 11.5% for 5 years (60 months)
    emi = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("500000"),
        annual_rate_percent=Decimal("11.5"),
        total_periods=60,
        periods_per_year=12
    )
    # Expected EMI formula result ~ ₹10,996.90
    assert 10900.0 <= float(emi) <= 11100.0, f"Unexpected EMI: {emi}"

    # NSFDC Concessional Rate: ₹5 Lakh loan at 6.5% for 10 years (120 months)
    emi_nsfdc = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("500000"),
        annual_rate_percent=Decimal("6.5"),
        total_periods=120,
        periods_per_year=12
    )
    # Expected EMI around ₹5,677.40
    assert 5600.0 <= float(emi_nsfdc) <= 5800.0, f"Unexpected concessional EMI: {emi_nsfdc}"
