"""
TASK 9 — FINAL SIH26092 BACKEND DEMO VERIFICATION TEST SUITE

Validates the complete set of 12 citizen scenarios mandated for final SIH26092 certification:
- Scenario 1: Business Loan (young entrepreneur in UP, small business need, full end-to-end journey)
- Scenario 2: Women Entrepreneur (gender/category/business-stage isolation, zero rule leaks)
- Scenario 3: Student / Education Loan (education need, scheme discovery, loan terms, official channel)
- Scenario 4: Hindi (Devanagari Hindi input, language detection, eligibility, Hindi response)
- Scenario 5: Hinglish (Roman Hindi/Hinglish natural understanding and response)
- Scenario 6: Follow-up Chat (multi-turn progressive context retention across 6 turns)
- Scenario 7: Scheme Comparison (side-by-side financial + eligibility comparison)
- Scenario 8: Wrong / Unrelated Query (out-of-domain rejection, zero scheme hallucination)
- Scenario 9: Partner Discovery (scheme -> partner -> location -> coordinates -> distance -> map URL)
- Scenario 10: Dynamic Update (source change -> snapshot -> diff -> pending update -> approval -> version increment -> RAG incremental update)
- Scenario 11: Financial Health (DeterministicFinancialHealthEngine integration with scheme financial metadata)
- Scenario 12: Safety & Security (SSRF defense, admin authentication, secret validation, unsafe URL rejection)
"""

import os
import json
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models import Scheme, SchemeRule, SchemeDocument, Partner, PartnerSchemeMapping
from app.models.ingestion import SourceSnapshot, PendingSchemeUpdate, SchemeSource
from app.models.changelog import SchemeChangelog
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.ai.extractor import NaturalLanguageProfileExtractor
from app.ai.copilot_router import AICopilotQueryRouter
from app.ai.agent import GPTCopilotAgent
from app.ai.tools import CopilotTools
from app.engine.eligibility import DeterministicEligibilityEngine, SchemeEligibilityStatus
from app.engine.financial_health import DeterministicFinancialHealthEngine
from app.engine.calculator import DeterministicFinancialEngine
from app.services.geo_partner_service import GeoPartnerLocatorService
from app.services.ingestion.change_detector import DeterministicChangeDetector
from app.services.ingestion.approval_service import PendingUpdateApprovalService
from app.services.ingestion.fetcher import URLSecurityValidator


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.rollback()
        except Exception:
            pass
        db.close()


# ==============================================================================
# SCENARIO 1 — BUSINESS LOAN
# ==============================================================================

def test_scenario_1_business_loan_citizen_journey(db_session: Session, client: TestClient):
    """
    User: young entrepreneur in Uttar Pradesh, wants to start a small business, needs financing.
    Verify:
      natural language extraction
      -> eligibility
      -> recommendation
      -> explanation
      -> financial fit
      -> EMI where possible
      -> application channel
      -> nearest partner
    """
    user_query = "I am a 24-year-old in Uttar Pradesh wanting to start a small manufacturing business and need a 5 lakh loan."
    
    # 1. Natural Language Extraction
    profile_out = NaturalLanguageProfileExtractor.extract_profile(user_query)
    extracted = profile_out.extracted_profile
    assert extracted.age == 24
    assert extracted.state == "UTTAR_PRADESH"
    assert extracted.requested_loan_amount == 500000.0
    assert extracted.business_stage == "NEW"

    profile = BeneficiaryProfileInput(
        age=24,
        state="UTTAR_PRADESH",
        requested_loan_amount=500000.0,
        business_stage="NEW",
        is_new_unit=True,
        social_category="GENERAL",
        annual_income=250000.0,
        activity_type="MANUFACTURING",
        sector="MANUFACTURING"
    )

    # 2. Eligibility for PMEGP
    sch_pmegp = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert sch_pmegp is not None
    rules_pmegp = db_session.query(SchemeRule).filter(SchemeRule.scheme_id == "SIH26092-001").all()
    eval_pmegp = DeterministicEligibilityEngine.evaluate_scheme(sch_pmegp, profile, active_rules=rules_pmegp)
    assert eval_pmegp.status in (SchemeEligibilityStatus.ELIGIBLE, SchemeEligibilityStatus.CONDITIONAL, SchemeEligibilityStatus.INSUFFICIENT_INFORMATION)

    # 3. Recommendation API
    rec_resp = client.post("/api/v1/recommendations", json={"profile": profile.model_dump()})
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    top_ids = [s["scheme_id"] for s in rec_data.get("recommendations", [])]
    assert "SIH26092-001" in top_ids

    # 4. Chatbot Explanation ("Why match?")
    chat_req = AIChatRequest(
        message="Why is PMEGP recommended for me?",
        scheme_id="SIH26092-001",
        profile=profile,
        session_id="sih_s1_session"
    )
    chat_res = GPTCopilotAgent.process_query(db_session, chat_req)
    assert chat_res.intent == "WHY_MATCH_QUERY"
    assert "PMEGP" in chat_res.answer or "Prime Minister" in chat_res.answer
    assert "Uttar Pradesh" in chat_res.answer or "UTTAR_PRADESH" in chat_res.answer or "Geography" in chat_res.answer

    # 5. Financial Fit & EMI Calculation (where possible)
    fin_fit = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
        scheme=sch_pmegp,
        project_cost=Decimal("500000"),
        requested_loan_amount=Decimal("500000"),
        own_contribution=Decimal("50000"),
        monthly_income=Decimal("35000")
    )
    assert fin_fit.suitability.value in ("STRONG_FIT", "POSSIBLE_FIT")
    assert fin_fit.available_subsidy is not None and fin_fit.available_subsidy > Decimal("0")

    # Schemes with published rates produce direct scheme-level EMI
    sch_vishwa = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-005").first()
    vishwa_fit = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
        scheme=sch_vishwa,
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("100000"),
        own_contribution=Decimal("10000"),
        monthly_income=Decimal("25000")
    )
    assert vishwa_fit.estimated_emi is not None and vishwa_fit.estimated_emi > Decimal("0")

    # Financial engine calculates indicative EMI for bank-determined loans
    indicative_emi = DeterministicFinancialEngine.calculate_installment(
        principal=Decimal("500000"),
        annual_rate_percent=Decimal("8.5"),
        total_periods=60,
        periods_per_year=12
    )
    assert indicative_emi > Decimal("0")

    # 6. Application Channel
    assert sch_pmegp.application_channel in ("District Industries Centre (DIC)", "Bank Branch / Financial Institution")
    assert "kviconline.gov.in" in sch_pmegp.official_portal

    # 7. Nearest Partner
    partner_res = GeoPartnerLocatorService.find_nearest_partners(
        db_session,
        latitude=26.8467,
        longitude=80.9462,  # Lucknow, UP
        scheme_id="SIH26092-001",
        limit=3
    )
    assert len(partner_res) > 0
    assert partner_res[0]["partner"].latitude is not None
    assert partner_res[0]["distance_km"] >= 0.0
    assert "google.com/maps" in partner_res[0]["google_maps_url"]


# ==============================================================================
# SCENARIO 2 — WOMEN ENTREPRENEUR (Gender/Category Rule Isolation)
# ==============================================================================

def test_scenario_2_women_entrepreneur_isolation(db_session: Session):
    """
    Verify gender/category/business-stage rules do not leak:
    - Women-only schemes (e.g. NSFDC MSY SIH26092-057) must be ELIGIBLE for eligible female.
    - Male profile must be STRICTLY INELIGIBLE for women-only schemes.
    """
    sch_msy = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-057").first()
    assert sch_msy is not None

    female_profile = BeneficiaryProfileInput(
        age=32,
        gender="FEMALE",
        social_category="SC",
        is_sc=True,
        state="MAHARASHTRA",
        annual_income=150000.0,
        business_stage="NEW",
        is_new_unit=True,
        requested_loan_amount=100000.0
    )
    
    male_profile = BeneficiaryProfileInput(
        age=32,
        gender="MALE",
        social_category="SC",
        is_sc=True,
        state="MAHARASHTRA",
        annual_income=150000.0,
        business_stage="NEW",
        is_new_unit=True,
        requested_loan_amount=100000.0
    )

    eval_female = DeterministicEligibilityEngine.evaluate_scheme(sch_msy, female_profile)
    assert eval_female.status == SchemeEligibilityStatus.ELIGIBLE, "Female SC profile must be eligible for Mahila Samriddhi Yojana"

    eval_male = DeterministicEligibilityEngine.evaluate_scheme(sch_msy, male_profile)
    assert eval_male.status == SchemeEligibilityStatus.INELIGIBLE, "Male profile must be ineligible for Mahila Samriddhi Yojana"
    assert any("gender" in f.lower() or "female" in f.lower() or "women" in f.lower() for f in eval_male.failed_rules)


# ==============================================================================
# SCENARIO 3 — STUDENT / EDUCATION LOAN
# ==============================================================================

def test_scenario_3_student_education_loan(db_session: Session):
    """
    Verify:
      education need
      -> applicable scheme
      -> loan details
      -> financial information
      -> application channel
    """
    sch_csis = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-083").first()
    assert sch_csis is not None

    student_profile = BeneficiaryProfileInput(
        age=20,
        applicant_type="STUDENT",
        employment_status="STUDENT",
        sector="EDUCATION",
        social_category="GENERAL",
        annual_income=300000.0,  # Below 4.5L ceiling
        state="TAMIL NADU",
        requested_loan_amount=600000.0
    )

    # 1. Discovery & Statutory Eligibility for CSIS (SIH26092-083)
    eval_csis = DeterministicEligibilityEngine.evaluate_scheme(sch_csis, student_profile)
    assert eval_csis.status == SchemeEligibilityStatus.ELIGIBLE

    # 2. Loan Details & Financial Information
    assert sch_csis.interest_subsidy == Decimal("100.00"), "CSIS provides 100% interest subsidy during moratorium"
    assert sch_csis.max_loan_amount == Decimal("750000.00"), "Collateral-free ceiling up to 7.5L under CGFSEL"

    # 3. Application Channel
    assert sch_csis.official_portal == "https://www.vidyalakshmi.co.in/"
    assert sch_csis.application_channel in ("Bank Branch / Financial Institution", "Online Portal")


# ==============================================================================
# SCENARIO 4 — HINDI (Devanagari)
# ==============================================================================

def test_scenario_4_devanagari_hindi_interaction(db_session: Session):
    """
    Use Devanagari Hindi.
    Verify:
      language detection
      -> retrieval
      -> eligibility
      -> response in Hindi
    """
    hindi_msg = "मुझे नया बिज़नेस शुरू करने के लिए लोन चाहिए"
    
    # Language Detection
    detected_lang = AICopilotQueryRouter.detect_language(hindi_msg)
    assert detected_lang == "hi"

    # Intent Routing
    intent = AICopilotQueryRouter.classify_intent(hindi_msg)
    assert intent in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY")

    # Copilot Response in Hindi
    req = AIChatRequest(
        message=hindi_msg,
        session_id="sih_hindi_session"
    )
    res = GPTCopilotAgent.process_query(db_session, req)
    assert res.language == "hi"
    assert "नमस्ते" in res.answer or "बिज़नेस" in res.answer or "राज्य" in res.answer or "योजना" in res.answer


# ==============================================================================
# SCENARIO 5 — HINGLISH (Roman Hindi)
# ==============================================================================

def test_scenario_5_hinglish_interaction(db_session: Session):
    """
    Use Roman Hindi / Hinglish.
    Verify natural understanding and response.
    """
    hinglish_msg = "bhai mujhe dairy farm ke liye loan chahiye UP me"
    
    # Language Detection
    detected_lang = AICopilotQueryRouter.detect_language(hinglish_msg)
    assert detected_lang == "hi"

    # Extraction
    extracted_profile = NaturalLanguageProfileExtractor.extract_profile(hinglish_msg).extracted_profile
    assert extracted_profile.state == "UTTAR_PRADESH"
    assert extracted_profile.sector == "AGRICULTURE"

    # Copilot Response
    req = AIChatRequest(
        message=hinglish_msg,
        session_id="sih_hinglish_session"
    )
    res = GPTCopilotAgent.process_query(db_session, req)
    assert len(res.answer) > 0
    assert res.response_mode in ("TOOL_RESULT", "GROUNDED", "CLARIFICATION")


# ==============================================================================
# SCENARIO 6 — FOLLOW-UP CHAT (Context Retention)
# ==============================================================================

def test_scenario_6_follow_up_context_retention(db_session: Session):
    """
    Progressive conversation turns:
      Turn 1: "mujhe UP me business start karna hai"
      Turn 2: "meri age 25 hai"
      Turn 3: "mere paas 2 lakh hain"
      Turn 4: "loan chahiye"
      Turn 5: "EMI kitni hogi?"
      Turn 6: "iske liye nearest bank kaha hai?"
    Verify conversation context is retained across turns.
    """
    session_id = "sih_multiturn_demo"

    # Turn 1
    t1 = GPTCopilotAgent.process_query(db_session, AIChatRequest(message="mujhe UP me business start karna hai", session_id=session_id))
    # Turn 2
    t2 = GPTCopilotAgent.process_query(db_session, AIChatRequest(message="meri age 25 hai", session_id=session_id))
    # Turn 3
    t3 = GPTCopilotAgent.process_query(db_session, AIChatRequest(message="mere paas 2 lakh hain", session_id=session_id))
    # Turn 4
    t4 = GPTCopilotAgent.process_query(db_session, AIChatRequest(message="5 lakh ka loan chahiye", session_id=session_id))
    
    # Verify accumulated session facts
    mem = GPTCopilotAgent.get_session_memory(session_id)
    facts = mem.get("extracted_facts", {})
    assert facts.get("state") == "UTTAR PRADESH" or facts.get("state") == "UTTAR_PRADESH"
    assert facts.get("age") == 25
    assert facts.get("liquid_savings") == 200000.0 or facts.get("liquid_savings") == 200000
    assert facts.get("requested_loan_amount") == 500000.0

    # Turn 5: EMI Query
    t5 = GPTCopilotAgent.process_query(db_session, AIChatRequest(message="EMI kitni hogi?", session_id=session_id))
    assert t5.intent == "FINANCIAL_QUERY"
    assert "EMI" in t5.answer or "किस्त" in t5.answer

    # Turn 6: Partner Locator Query
    t6 = GPTCopilotAgent.process_query(db_session, AIChatRequest(message="iske liye nearest bank kaha hai?", session_id=session_id))
    assert t6.intent in ("PARTNER_DISCOVERY", "APPLICATION_QUERY")
    assert any(act.action_type == "LOCATE_PARTNER" for act in t6.actions)


# ==============================================================================
# SCENARIO 7 — SCHEME COMPARISON
# ==============================================================================

def test_scenario_7_scheme_comparison(db_session: Session, client: TestClient):
    """
    Compare two relevant schemes (e.g. PMEGP vs Mudra) and verify financial + eligibility differences.
    """
    resp = client.get("/api/v1/schemes/compare?ids=SIH26092-001,SIH26092-002&project_cost=1000000&requested_loan_amount=800000&own_contribution=200000")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["compared_schemes"]) == 2

    s1 = data["compared_schemes"][0]
    s2 = data["compared_schemes"][1]
    
    # Verify distinct financial structures returned
    assert s1["scheme"]["scheme_id"] != s2["scheme"]["scheme_id"]
    assert "financial_assessment" in s1
    assert "financial_assessment" in s2
    assert s1["financial_assessment"]["suitability"] in ("STRONG_FIT", "POSSIBLE_FIT", "INSUFFICIENT_INFORMATION", "FINANCIALLY_UNSUITABLE")


# ==============================================================================
# SCENARIO 8 — WRONG / UNRELATED QUERY (Out-of-Domain Guardrail)
# ==============================================================================

def test_scenario_8_out_of_domain_no_hallucination(db_session: Session):
    """
    Ask unrelated questions (cricket, coding, cooking).
    Verify chatbot does not fabricate scheme information or call RAG.
    """
    unrelated_queries = [
        "Who won the cricket match yesterday?",
        "Write a quicksort algorithm in python",
        "How to bake a chocolate cake at home?"
    ]

    for q in unrelated_queries:
        intent = AICopilotQueryRouter.classify_intent(q)
        assert intent == "OUT_OF_DOMAIN"

        req = AIChatRequest(message=q, session_id="sih_ood_test")
        res = GPTCopilotAgent.process_query(db_session, req)
        assert res.intent == "OUT_OF_DOMAIN"
        assert res.response_mode == "CASUAL"
        assert len(res.citations) == 0, "No citations for out-of-domain query"
        assert len(res.rich_cards) == 0, "No scheme cards for out-of-domain query"
        assert "government" in res.answer.lower() or "scheme" in res.answer.lower() or "योजना" in res.answer


# ==============================================================================
# SCENARIO 9 — PARTNER DISCOVERY (End-to-End Coordinates & Mapping)
# ==============================================================================

def test_scenario_9_partner_coordinates_and_distance(db_session: Session, client: TestClient):
    """
    For a scheme with verified partner mapping:
      scheme -> partner -> location -> coordinates -> distance -> map destination
    must work truthfully.
    """
    resp = client.get("/api/v1/partner/nearest?latitude=26.4499&longitude=80.3319&scheme_id=SIH26092-001&limit=3")
    assert resp.status_code == 200
    partners = resp.json()
    assert len(partners) > 0

    nearest = partners[0]
    assert nearest["partner"]["name"] is not None
    assert nearest["partner"]["latitude"] is not None and 20.0 <= nearest["partner"]["latitude"] <= 30.0
    assert nearest["partner"]["longitude"] is not None and 75.0 <= nearest["partner"]["longitude"] <= 85.0
    assert nearest["distance_km"] >= 0.0
    assert "https://www.google.com/maps/dir/" in nearest["google_maps_url"]
    assert nearest["coordinate_precision"] in ("EXACT_ADDRESS", "DISTRICT_HEADQUARTERS", "CITY_CENTROID")


# ==============================================================================
# SCENARIO 10 — DYNAMIC UPDATE LIFECYCLE
# ==============================================================================

def test_scenario_10_dynamic_update_lifecycle(db_session: Session):
    """
    Simulate:
      official source change
      -> snapshot
      -> diff
      -> pending update
      -> approval
      -> version increment
      -> RAG incremental update
    """
    target_sid = "SIH26092-001"
    sch_before = db_session.query(Scheme).filter(Scheme.scheme_id == target_sid).first()
    old_version = sch_before.scheme_version or "1.0"
    old_prev_version = sch_before.previous_version
    old_name = sch_before.scheme_name

    # Ensure source_id exists for non-nullable FK
    src = db_session.query(SchemeSource).filter(SchemeSource.scheme_id == target_sid).first()
    if not src:
        src = db_session.query(SchemeSource).first()
    source_id = src.source_id if src else "SRC-SIH26092-001"

    extracted_new_data = {
        "scheme_name": old_name,
        "max_project_cost": 5000000.0,
        "subsidy_percentage": 35.0,
        "official_source_url": "https://www.kviconline.gov.in/pmegpeportal/"
    }
    
    diffs, gov_cat = DeterministicChangeDetector.generate_field_diffs(
        target_scheme=sch_before,
        candidate_data=extracted_new_data
    )
    assert diffs is not None

    pending_upd = PendingSchemeUpdate(
        update_id="UPD-TEST-DEMO-S10",
        scheme_id=target_sid,
        source_id=source_id,
        old_version=old_version,
        extracted_data=json.dumps(extracted_new_data, default=str),
        detected_changes=json.dumps(diffs, default=str),
        status="PENDING",
        governance_category=gov_cat
    )
    db_session.merge(pending_upd)
    db_session.commit()

    try:
        approved_upd = PendingUpdateApprovalService(db_session).process_review(
            update_id="UPD-TEST-DEMO-S10",
            action="APPROVE",
            reviewer_id="sih_lead_evaluator"
        )
        assert approved_upd.status == "APPROVED"
        assert sch_before.scheme_version != old_version
    finally:
        # Revert changes made during test to preserve baseline data integrity
        sch_before.scheme_version = old_version
        sch_before.previous_version = old_prev_version
        db_session.query(SchemeChangelog).filter(SchemeChangelog.admin_identifier == "sih_lead_evaluator").delete()
        db_session.query(PendingSchemeUpdate).filter(PendingSchemeUpdate.update_id == "UPD-TEST-DEMO-S10").delete()
        db_session.commit()


# ==============================================================================
# SCENARIO 11 — FINANCIAL HEALTH ENGINE INTEGRATION
# ==============================================================================

def test_scenario_11_financial_health_integration(db_session: Session):
    """
    Verify existing Financial Health Engine works with scheme financial metadata:
    - computes margin money, net debt, and EMI where published interest rate exists
    - classifies into STRONG_FIT / POSSIBLE_FIT / INSUFFICIENT_INFORMATION / FINANCIALLY_UNSUITABLE
    - adheres strictly to truthful unknown handling when rate is bank-determined
    """
    # 1. Scheme with subsidy & loan limits (PMEGP)
    sch_pmegp = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert sch_pmegp is not None

    suitability_pmegp = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
        scheme=sch_pmegp,
        project_cost=Decimal("1000000"),
        requested_loan_amount=Decimal("600000"),
        own_contribution=Decimal("50000"),
        monthly_income=Decimal("50000")
    )
    assert suitability_pmegp.suitability.value in ("STRONG_FIT", "POSSIBLE_FIT")
    assert suitability_pmegp.available_subsidy == Decimal("350000.00")
    assert suitability_pmegp.required_margin_money == Decimal("50000.00")
    assert suitability_pmegp.margin_money_gap == Decimal("0.00")
    # PMEGP interest rate is determined by lending bank under RBI guidelines, so engine correctly handles missing parameter
    assert "interest_rate" in suitability_pmegp.missing_parameters

    # 2. Scheme with published interest rate (PM Vishwakarma - 5.0% concessional interest)
    sch_vishwa = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-005").first()
    assert sch_vishwa is not None

    suitability_vishwa = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
        scheme=sch_vishwa,
        project_cost=Decimal("100000"),
        requested_loan_amount=Decimal("100000"),
        own_contribution=Decimal("10000"),
        monthly_income=Decimal("25000")
    )
    assert suitability_vishwa.suitability.value in ("STRONG_FIT", "POSSIBLE_FIT")
    assert suitability_vishwa.estimated_emi is not None and suitability_vishwa.estimated_emi > Decimal("0")
    assert "5.0" in suitability_vishwa.interest_rate_display


# ==============================================================================
# SCENARIO 12 — SAFETY & SECURITY HARDENING
# ==============================================================================

def test_scenario_12_safety_and_security(client: TestClient):
    """
    Verify:
      - SSRF protection (private/loopback IPs blocked)
      - Unsafe URLs rejected
      - Admin endpoints protected
      - Production secret validation
    """
    # 1. SSRF Protection: Loopback and metadata IPs must be rejected
    is_valid, err = URLSecurityValidator.validate_url("http://127.0.0.1:8000/admin")
    assert not is_valid, "Loopback IP must be rejected by SSRF validator"

    is_valid, err = URLSecurityValidator.validate_url("http://169.254.169.254/latest/meta-data")
    assert not is_valid, "Cloud metadata IP must be rejected by SSRF validator"

    is_valid, err = URLSecurityValidator.validate_url("http://localhost:5432")
    assert not is_valid, "Localhost must be rejected by SSRF validator"

    # Legitimate government domain must pass
    is_valid, err = URLSecurityValidator.validate_url("https://www.myscheme.gov.in/schemes")
    assert is_valid, f"Official gov.in domain must be valid, got error: {err}"

    # 2. Admin endpoint protection (must reject unauthenticated requests)
    unauth_resp = client.get("/api/v1/admin/dashboard")
    assert unauth_resp.status_code in (401, 403), f"Admin dashboard must reject unauthenticated requests, got {unauth_resp.status_code}"
    unauth_resp2 = client.get("/api/v1/admin/schemes")
    assert unauth_resp2.status_code in (401, 403), f"Admin schemes must reject unauthenticated requests, got {unauth_resp2.status_code}"

    # 3. Secret validation
    from app.core.config import settings
    assert settings.SECRET_KEY is not None and len(settings.SECRET_KEY) >= 16


# ==============================================================================
# SCENARIO 13 — REGIONAL-LANGUAGE CITIZEN (Bengali & Tamil)
# ==============================================================================

def test_scenario_13_regional_language_citizen(db_session: Session):
    """
    Verify regional language processing:
    - Language detection for Bengali ('bn') and Tamil ('ta')
    - Intent routing
    - Native response delivery
    - Preservation of statutory scheme facts without distortion
    """
    # 1. Bengali Query
    user_query_bn = "আমি ব্যবসা শুরু করতে চাই, আমাকে সাহায্য করুন"
    lang_bn = AICopilotQueryRouter.detect_language(user_query_bn)
    assert lang_bn == "bn"

    chat_req_bn = AIChatRequest(
        message=user_query_bn,
        session_id="sih_s13_bn"
    )
    chat_res_bn = GPTCopilotAgent.process_query(db_session, chat_req_bn)
    assert chat_res_bn.language in ("bn", "en")
    assert len(chat_res_bn.answer) > 0

    # 2. Tamil Query
    user_query_ta = "எனக்கு தொழில் தொடங்க கடன் வேண்டும்"
    lang_ta = AICopilotQueryRouter.detect_language(user_query_ta)
    assert lang_ta == "ta"

    chat_req_ta = AIChatRequest(
        message=user_query_ta,
        session_id="sih_s13_ta"
    )
    chat_res_ta = GPTCopilotAgent.process_query(db_session, chat_req_ta)
    assert chat_res_ta.language in ("ta", "en")
    assert len(chat_res_ta.answer) > 0


# ==============================================================================
# SCENARIO 14 — INSUFFICIENT USER INFORMATION (Targeted Clarification)
# ==============================================================================

def test_scenario_14_insufficient_user_information(db_session: Session):
    """
    Verify handling when citizen provides partial/ambiguous information:
    - Deterministic engine flags INSUFFICIENT_INFORMATION
    - Engine lists exact missing parameters (e.g. age, annual_income)
    - Zero guessing or hallucination of missing values
    """
    # Profile with missing age and missing income
    partial_profile = BeneficiaryProfileInput(
        state="UTTAR_PRADESH",
        requested_loan_amount=500000.0,
        business_stage="NEW"
    )

    sch_pmegp = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert sch_pmegp is not None

    rules_pmegp = db_session.query(SchemeRule).filter(SchemeRule.scheme_id == "SIH26092-001").all()
    eval_res = DeterministicEligibilityEngine.evaluate_scheme(sch_pmegp, partial_profile, active_rules=rules_pmegp)

    # Status must be CONDITIONAL or INSUFFICIENT_INFORMATION
    assert eval_res.status in (SchemeEligibilityStatus.CONDITIONAL, SchemeEligibilityStatus.INSUFFICIENT_INFORMATION)
    assert len(eval_res.unknown_eligibility_rules) > 0

    # Chatbot provides targeted clarification
    chat_req = AIChatRequest(
        message="Am I eligible for PMEGP?",
        scheme_id="SIH26092-001",
        profile=partial_profile,
        session_id="sih_s14_session"
    )
    chat_res = GPTCopilotAgent.process_query(db_session, chat_req)
    assert chat_res.intent == "ELIGIBILITY_QUERY"
    assert len(chat_res.answer) > 0


# ==============================================================================
# SCENARIO 15 — STATUTORY INELIGIBLE USER (Zero Leakage & Hard Gate)
# ==============================================================================

def test_scenario_15_statutory_ineligible_user(db_session: Session, client: TestClient):
    """
    Verify hard gate enforcement when applicant does not meet statutory criteria:
    - Underage applicant (e.g. age 15 where min age is 18 for NSFDC MSY SIH26092-057)
    - High-income applicant (e.g. income ₹12L where ceiling is ₹4.5L for CSIS SIH26092-083)
    - Rejection explanation explicitly cites failed statutory rule
    - Ineligible scheme is strictly excluded from top recommendations
    """
    # 1. Underage applicant for NSFDC MSY (min age 18)
    underage_profile = BeneficiaryProfileInput(
        age=15,
        gender="FEMALE",
        social_category="SC",
        state="UTTAR_PRADESH",
        annual_income=200000.0
    )

    sch_msy = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-057").first()
    assert sch_msy is not None
    rules_msy = db_session.query(SchemeRule).filter(SchemeRule.scheme_id == "SIH26092-057").all()
    eval_underage = DeterministicEligibilityEngine.evaluate_scheme(sch_msy, underage_profile, active_rules=rules_msy)

    assert eval_underage.status == SchemeEligibilityStatus.INELIGIBLE
    assert len(eval_underage.hard_rules_failed) > 0
    failed_reasons = [f.reason for f in eval_underage.hard_rules_failed]
    assert any("18" in r or "age" in r.lower() for r in failed_reasons)

    # 2. High-income applicant for CSIS education interest subsidy (income ceiling ₹4.5L)
    high_income_student = BeneficiaryProfileInput(
        age=20,
        state="DELHI",
        annual_income=1200000.0,  # ₹12 Lakh > ₹4.5 Lakh limit
        applicant_type="STUDENT",
        sector="EDUCATION"
    )
    sch_csis = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-083").first()
    if sch_csis:
        rules_csis = db_session.query(SchemeRule).filter(SchemeRule.scheme_id == "SIH26092-083").all()
        eval_csis = DeterministicEligibilityEngine.evaluate_scheme(sch_csis, high_income_student, active_rules=rules_csis)
        assert eval_csis.status == SchemeEligibilityStatus.INELIGIBLE
