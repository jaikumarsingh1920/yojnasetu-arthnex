import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.ai import AIChatRequest
from app.ai.agent import GPTCopilotAgent
from app.ai.copilot_router import AICopilotQueryRouter
from app.engine.recommendation import DeterministicRecommendationEngine
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.recommendation import RecommendationRequest


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# SCENARIO A: Citizen wants a business loan
# ==============================================================================
def test_scenario_a_business_loan(db: Session):
    session_id = "test-scenario-a-biz-loan"
    req = AIChatRequest(
        message="I want to apply for a business loan to expand my manufacturing workshop.",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    assert res is not None
    assert res.intent in ["BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY", "FINANCIAL_QUERY"]
    # Should engage conversationally and ask relevant location/cost questions
    assert "manufacturing" in res.answer.lower() or "business" in res.answer.lower()
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["extracted_facts"].get("sector") in ["MANUFACTURING", "MICRO_ENTERPRISE"] or mem["extracted_facts"].get("project_cost") is not None or "expand" in str(mem["extracted_facts"])


# ==============================================================================
# SCENARIO B: Young SC entrepreneur from UP starting dairy business (Multi-turn)
# ==============================================================================
def test_scenario_b_dairy_farmer_gorakhpur_multi_turn(db: Session):
    session_id = "test-scenario-b-dairy-farmer"

    # Turn 1: Sector
    r1 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="I want to start a dairy business.",
        session_id=session_id
    ))
    assert r1.intent in ["BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY"]
    mem1 = GPTCopilotAgent.get_session_memory(session_id)
    assert mem1["extracted_facts"].get("sector") == "DAIRY"
    # Should not dump cards prematurely; should ask for location
    assert len(r1.rich_cards) == 0
    assert "location" in r1.answer.lower() or "state" in r1.answer.lower() or "district" in r1.answer.lower()

    # Turn 2: Location (Gorakhpur)
    r2 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="I'm from Gorakhpur.",
        session_id=session_id
    ))
    mem2 = GPTCopilotAgent.get_session_memory(session_id)
    assert str(mem2["extracted_facts"].get("district")).upper() == "GORAKHPUR"
    assert mem2["extracted_facts"].get("state") in ["UTTAR PRADESH", "UTTAR_PRADESH"]
    # Still progressive: asks age/category
    assert len(r2.rich_cards) == 0

    # Turn 3: Age & Category (24 and SC)
    r3 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="I'm 24 and SC.",
        session_id=session_id
    ))
    mem3 = GPTCopilotAgent.get_session_memory(session_id)
    assert mem3["extracted_facts"].get("age") == 24
    assert mem3["extracted_facts"].get("social_category") == "SC"
    # Asks for investment / project cost
    assert len(r3.rich_cards) == 0

    # Turn 4: Investment capacity (3 lakh)
    r4 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="I can invest around 3 lakh.",
        session_id=session_id
    ))
    mem4 = GPTCopilotAgent.get_session_memory(session_id)
    assert mem4["extracted_facts"].get("liquid_savings") == 300000.0 or mem4["extracted_facts"].get("project_cost") == 300000.0

    # Turn 5: Explicit recommendation trigger: "Now show me the best schemes."
    r5 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="Now show me the best schemes.",
        session_id=session_id
    ))
    assert len(r5.rich_cards) > 0, "Expected recommended schemes after explicit user request"

    card_titles = [c.title.lower() for c in r5.rich_cards]

    # Verify that dairy-relevant schemes are present (AHIDF, Gau Samvardhan, AIF, PMEGP, MUDRA, etc.)
    has_dairy_relevant = any(
        "agriculture infrastructure fund" in t or "pmegp" in t or "mudra" in t or "stand-up" in t or "aif" in t or "animal husbandry" in t or "ahidf" in t or "gau samvardhan" in t or "gopal ratna" in t
        for t in card_titles
    )
    assert has_dairy_relevant, f"Expected dairy schemes in recommendations, got: {card_titles}"

    # Verify that conflicting/irrelevant schemes (PMMSY fisheries, pig semen lab) are NOT present
    for title in card_titles:
        assert "matsya sampada" not in title, f"PMMSY (fisheries) erroneously recommended for dairy: {title}"
        assert "fisheries" not in title, f"Fisheries scheme erroneously recommended for dairy: {title}"
        assert "piggery" not in title and "pig" not in title, f"Piggery scheme erroneously recommended for dairy: {title}"

    # Verify card rich attributes
    top_card = r5.rich_cards[0]
    data = top_card.data
    assert data.get("match_tier") in ["BEST_MATCH", "ELIGIBLE", "POTENTIALLY_RELEVANT"]
    assert data.get("match_score", 0) > 0.4
    assert data.get("why_matches") is not None and len(data.get("why_matches")) > 0
    assert data.get("partner_availability") is not None
    assert data.get("key_conditions") is not None
    assert data.get("financial_fit") is not None


# ==============================================================================
# SCENARIO C: Woman entrepreneur asking for schemes
# ==============================================================================
def test_scenario_c_woman_entrepreneur(db: Session):
    session_id = "test-scenario-c-woman-ent"
    req = AIChatRequest(
        message="I am a 32-year-old woman entrepreneur from Jaipur looking to start a textile manufacturing unit.",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["extracted_facts"].get("gender") == "FEMALE"
    assert mem["extracted_facts"].get("age") == 32
    assert mem["extracted_facts"].get("state") == "RAJASTHAN"

    # When asking for schemes, verify women-focused benefits or Stand-Up India / PMEGP special rates
    req2 = AIChatRequest(
        message="Show me schemes with special subsidies for women.",
        session_id=session_id
    )
    res2 = GPTCopilotAgent.process_query(db, req2)
    assert len(res2.rich_cards) > 0
    card_titles = [c.title.lower() for c in res2.rich_cards]
    has_women_scheme = any("stand-up" in t or "pmegp" in t or "mudra" in t for t in card_titles)
    assert has_women_scheme, f"Expected Stand-Up India or PMEGP for woman entrepreneur, got: {card_titles}"


# ==============================================================================
# SCENARIO D: Student asking about education loan
# ==============================================================================
def test_scenario_d_student_education_loan(db: Session):
    session_id = "test-scenario-d-student"
    req = AIChatRequest(
        message="I am a 20 year old college student from Bihar needing an education loan for B.Tech.",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["extracted_facts"].get("applicant_type") == "STUDENT"

    req2 = AIChatRequest(
        message="What are the education loan schemes and interest subsidies available?",
        session_id=session_id
    )
    res2 = GPTCopilotAgent.process_query(db, req2)
    assert "vidya lakshmi" in res2.answer.lower() or "education loan" in res2.answer.lower() or "interest subsidy" in res2.answer.lower() or len(res2.rich_cards) > 0


# ==============================================================================
# SCENARIO E: Hindi conversation
# ==============================================================================
def test_scenario_e_hindi_conversation(db: Session):
    session_id = "test-scenario-e-hindi"
    req = AIChatRequest(
        message="मुझे डेयरी का बिजनेस शुरू करना है और मैं उत्तर प्रदेश से हूं",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    assert res.language == "hi"
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["extracted_facts"].get("sector") == "DAIRY"
    assert mem["extracted_facts"].get("state") in ["UTTAR PRADESH", "UTTAR_PRADESH"]
    # The answer should contain Hindi text
    assert any('\u0900' <= char <= '\u097f' for char in res.answer)


# ==============================================================================
# SCENARIO F: Hinglish conversation
# ==============================================================================
def test_scenario_f_hinglish_conversation(db: Session):
    session_id = "test-scenario-f-hinglish"
    req = AIChatRequest(
        message="mai gorakhpur me dairy business start karna chahta hu aur mere paas 3 lakh hai",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert str(mem["extracted_facts"].get("district")).upper() == "GORAKHPUR"
    assert mem["extracted_facts"].get("state") in ["UTTAR PRADESH", "UTTAR_PRADESH"]
    assert mem["extracted_facts"].get("liquid_savings") == 300000.0 or mem["extracted_facts"].get("project_cost") == 300000.0


# ==============================================================================
# SCENARIO G: User asks "Why am I eligible?"
# ==============================================================================
def test_scenario_g_why_am_i_eligible(db: Session):
    session_id = "test-scenario-g-why-eligible"
    # Seed session memory with a known profile
    GPTCopilotAgent.update_session_facts(session_id, {
        "age": 24,
        "state": "UTTAR PRADESH",
        "district": "GORAKHPUR",
        "social_category": "SC",
        "sector": "DAIRY",
        "current_scheme": "PMEGP"
    })
    req = AIChatRequest(
        message="Why am I eligible for PMEGP?",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    assert res is not None
    # Explains dimension-level eligibility
    ans = res.answer.lower()
    assert "eligible" in ans or "criteria" in ans or "subsidy" in ans or "sc" in ans or "pmegp" in ans


# ==============================================================================
# SCENARIO H: User asks "Why am I not eligible?"
# ==============================================================================
def test_scenario_h_why_am_i_not_eligible(db: Session):
    session_id = "test-scenario-h-why-not-eligible"
    # Set profile to General Male
    GPTCopilotAgent.update_session_facts(session_id, {
        "age": 35,
        "gender": "MALE",
        "social_category": "GENERAL",
        "state": "UTTAR PRADESH"
    })
    req = AIChatRequest(
        message="Why am I not eligible for Stand-Up India?",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    ans = res.answer.lower()
    # Should explain that Stand-Up India is strictly for SC/ST or Women entrepreneurs
    assert "sc/st" in ans or "sc" in ans or "woman" in ans or "women" in ans or "not eligible" in ans or "criteria" in ans


# ==============================================================================
# SCENARIO I: Scheme comparison ("Which one is better between these two?")
# ==============================================================================
def test_scenario_i_scheme_comparison(db: Session):
    session_id = "test-scenario-i-compare"
    req = AIChatRequest(
        message="Which one is better between PMEGP and MUDRA for my dairy business?",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    assert res is not None
    ans = res.answer.lower()
    assert "pmegp" in ans
    assert "mudra" in ans


# ==============================================================================
# SCENARIO J: Nearest place to proceed (Partner Intelligence)
# ==============================================================================
def test_scenario_j_nearest_place_to_proceed(db: Session):
    session_id = "test-scenario-j-partner"
    GPTCopilotAgent.update_session_facts(session_id, {
        "district": "GORAKHPUR",
        "state": "UTTAR PRADESH",
        "current_scheme": "PMEGP"
    })
    req = AIChatRequest(
        message="Where is the nearest branch or bank to apply for PMEGP in Gorakhpur?",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    assert res.intent == "PARTNER_DISCOVERY"
    ans = res.answer
    # Should mention verified physical partner institutions or online route
    assert "Partner" in ans or "Bank" in ans or "Gorakhpur" in ans or "KVIB" in ans or "DIC" in ans or "Portal" in ans
    # Distinguishes exact branch vs district centroid or online route
    assert "Exact" in ans or "Centroid" in ans or "km" in ans or "portal" in ans.lower()


# ==============================================================================
# SCENARIO K: Financial affordability evaluation
# ==============================================================================
def test_scenario_k_financial_affordability(db: Session):
    session_id = "test-scenario-k-affordability"
    req = AIChatRequest(
        message="My monthly income is 40000 and existing EMI is 5000. Can I afford a 5 lakh loan for 5 years?",
        session_id=session_id
    )
    res = GPTCopilotAgent.process_query(db, req)
    assert res.intent == "AFFORDABILITY_QUERY"
    ans = res.answer
    # Deterministic calculation of FOIR / Debt-to-Income / EMI
    assert "FOIR" in ans or "Debt-to-Income" in ans or "Affordability" in ans or "EMI" in ans
    assert "%" in ans
    assert res.deterministic_used is True


# ==============================================================================
# SCENARIO L: Completely unrelated query (Guardrail)
# ==============================================================================
def test_scenario_l_unrelated_query(db: Session):
    req = AIChatRequest(message="Who won the cricket world cup yesterday?")
    res = GPTCopilotAgent.process_query(db, req)
    assert res.intent in ["OUT_OF_DOMAIN", "CASUAL_CONVERSATION"]
    assert len(res.citations) == 0
    assert len(res.rich_cards) == 0
    # Politely redirects to government schemes and subsidies
    assert "schemes" in res.answer.lower() or "yojna" in res.answer.lower() or "assist" in res.answer.lower()


# ==============================================================================
# MULTILINGUAL PROFILE PRESERVATION ACROSS LANGUAGE SWITCHES
# ==============================================================================
def test_multilingual_context_switch_across_languages(db: Session):
    session_id = "test-lang-switch-persists"

    # Turn 1: Hindi
    GPTCopilotAgent.process_query(db, AIChatRequest(
        message="मुझे उत्तर प्रदेश में डेयरी शुरू करनी है",
        session_id=session_id
    ))
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["extracted_facts"].get("state") in ["UTTAR PRADESH", "UTTAR_PRADESH"]
    assert mem["extracted_facts"].get("sector") == "DAIRY"

    # Turn 2: English
    GPTCopilotAgent.process_query(db, AIChatRequest(
        message="My age is 24 and category is SC",
        session_id=session_id
    ))
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["extracted_facts"].get("age") == 24
    assert mem["extracted_facts"].get("social_category") == "SC"
    assert mem["extracted_facts"].get("state") in ["UTTAR PRADESH", "UTTAR_PRADESH"]
    assert mem["extracted_facts"].get("sector") == "DAIRY"

    # Turn 3: Hinglish
    GPTCopilotAgent.process_query(db, AIChatRequest(
        message="mera budget 3 lakh hai",
        session_id=session_id
    ))
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["extracted_facts"].get("liquid_savings") == 300000.0 or mem["extracted_facts"].get("project_cost") == 300000.0

    # Turn 4: Tamil (User switches language to Tamil)
    r4 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="திட்டங்களை காட்டுங்கள்",  # "Show schemes"
        session_id=session_id
    ))
    mem = GPTCopilotAgent.get_session_memory(session_id)
    # State, sector, age, category, savings remain completely intact!
    assert mem["extracted_facts"].get("age") == 24
    assert mem["extracted_facts"].get("social_category") == "SC"
    assert mem["extracted_facts"].get("state") in ["UTTAR PRADESH", "UTTAR_PRADESH"]
    assert mem["extracted_facts"].get("sector") == "DAIRY"

    # Turn 5: Back to English
    r5 = GPTCopilotAgent.process_query(db, AIChatRequest(
        message="Now show me the best schemes",
        session_id=session_id
    ))
    # Still produces accurate recommendations from the accumulated profile
    assert len(r5.rich_cards) > 0
    top_card = r5.rich_cards[0]
    assert top_card.data.get("match_tier") in ["BEST_MATCH", "ELIGIBLE", "POTENTIALLY_RELEVANT"]
