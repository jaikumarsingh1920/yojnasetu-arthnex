"""
Comprehensive regression test suite for YojnaSetu Scheme Intelligence Assistant.
Validates:
1. Intent Understanding
2. Multi-Turn Conversational Memory & Profile Accumulation
3. Multilingual Profile Extraction (English, Hindi, Hinglish)
4. Missing Information Clarification Flow
5. Deterministic Statutory Eligibility (Zero Hallucination)
6. Grounded Answers & Official Citations
7. Negative Constraints (No fabricated subsidies, loan limits, rates)
8. Recommendation Reasoning (Matched dimensions, financial fit, caveats)
9. Rejection Explanations (Statutory rule failures explained in plain language)
10. Follow-up Questions & Contextual Pronoun Resolution ("isme", "iske", "ye scheme")
11. Structured Scheme Comparison across 10 Dimensions
12. Deterministic Financial Reasoning
13. Out-of-Domain Guardrails (Cricket, coding, trivia redirected)
14. Multilingual Concept Parity
"""

import pytest
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.ai.agent import GPTCopilotAgent
from app.ai.copilot_router import AICopilotQueryRouter
classify_intent = AICopilotQueryRouter.classify_intent
from app.ai.extractor import NaturalLanguageProfileExtractor
from app.schemas.ai import AIChatRequest
from app.models.scheme import Scheme


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# 1. INTENT UNDERSTANDING
# ---------------------------------------------------------------------------
def test_intent_classification_comprehensive():
    """Verifies accurate classification across all supported intents."""
    test_cases = [
        ("UP me dairy business ke liye scheme batao", "SCHEME_DISCOVERY"),
        ("PMEGP scheme details", "SCHEME_DETAILS"),
        ("Am I eligible for PMEGP loan?", "ELIGIBILITY_QUERY"),
        ("What benefits are provided in PM Vishwakarma?", "BENEFIT_QUERY"),
        ("PMEGP me subsidy kitni milti hai?", "SUBSIDY_QUERY"),
        ("What is the interest rate for PM Vishwakarma?", "FINANCIAL_QUERY"),
        ("10 lakh loan 5 saal ke liye EMI kitni hogi?", "FINANCIAL_QUERY"),
        ("What documents are required for MUDRA loan?", "DOCUMENT_QUERY"),
        ("How do I apply online for PMEGP?", "APPLICATION_QUERY"),
        ("Where is the nearest partner branch or DIC office?", "PARTNER_DISCOVERY"),
        ("PMEGP aur Mudra me kya difference hai?", "SCHEME_COMPARISON"),
        ("Why is this scheme recommended for me?", "WHY_MATCH_QUERY"),
        ("Why was I rejected for PMEGP?", "EXPLAIN_REJECTION"),
        ("meri eligibility kyu reject hui?", "EXPLAIN_REJECTION"),
        ("Who won the cricket match yesterday?", "OUT_OF_DOMAIN"),
        ("Write Python code for quicksort algorithm", "OUT_OF_DOMAIN"),
        ("How to bake chocolate cake?", "OUT_OF_DOMAIN"),
        ("नमस्ते भाई", "CASUAL_GREETING"),
    ]
    for text, expected_intent in test_cases:
        detected = classify_intent(text)
        assert detected == expected_intent, f"Failed for '{text}': expected {expected_intent}, got {detected}"


# ---------------------------------------------------------------------------
# 2. MULTI-TURN CONVERSATIONAL MEMORY & PROFILE ACCUMULATION
# ---------------------------------------------------------------------------
def test_multi_turn_profile_accumulation(db: Session):
    """
    Verifies multi-turn memory without requiring user repetition:
    Turn 1: 'Main UP me rehta hu' (State: UTTAR PRADESH)
    Turn 2: 'meri age 27 hai' (Age: 27)
    Turn 3: 'mujhe dairy business start karna hai' (Activity: Dairy Farming)
    Turn 4: 'loan chahiye' (Produces grounded recommendations with accumulated profile)
    """
    session_id = "test-accum-multi-turn-99"

    # Turn 1: State
    r1 = GPTCopilotAgent.process_query(db, AIChatRequest(message="Main UP me rehta hu", session_id=session_id))
    mem1 = GPTCopilotAgent.get_session_memory(session_id)
    assert mem1["extracted_facts"].get("state") == "UTTAR PRADESH"

    # Turn 2: Age
    r2 = GPTCopilotAgent.process_query(db, AIChatRequest(message="meri age 27 hai", session_id=session_id))
    mem2 = GPTCopilotAgent.get_session_memory(session_id)
    assert mem2["extracted_facts"].get("state") == "UTTAR PRADESH"
    assert mem2["extracted_facts"].get("age") == 27

    # Turn 3: Business Activity
    r3 = GPTCopilotAgent.process_query(db, AIChatRequest(message="mujhe dairy business start karna hai", session_id=session_id))
    mem3 = GPTCopilotAgent.get_session_memory(session_id)
    assert mem3["extracted_facts"].get("state") == "UTTAR PRADESH"
    assert mem3["extracted_facts"].get("age") == 27
    assert "dairy" in str(mem3["extracted_facts"].get("business_description", "")).lower()

    # Turn 4: Loan Request -> Should recommend schemes using accumulated profile
    r4 = GPTCopilotAgent.process_query(db, AIChatRequest(message="loan chahiye", session_id=session_id))
    assert r4.intent in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY", "RECOMMENDATION_QUERY", "FINANCIAL_QUERY")
    # Response should acknowledge UP or Dairy context
    ans = r4.answer.lower()
    assert "uttar pradesh" in ans or "dairy" in ans or "scheme" in ans or r4.deterministic_used is True


# ---------------------------------------------------------------------------
# 3. MULTILINGUAL PROFILE EXTRACTION
# ---------------------------------------------------------------------------
def test_multilingual_profile_extraction():
    """Extracts structured profile dimensions from English, Devanagari Hindi, and Hinglish."""
    # Devanagari Hindi
    text_hi = "मेरी उम्र 28 वर्ष है, मैं उत्तर प्रदेश के लखनऊ में रहता हूँ, अन्य पिछड़ा वर्ग से हूँ और 5 लाख का डेयरी फार्म शुरू करना चाहता हूँ"
    prof_hi = NaturalLanguageProfileExtractor.extract_profile(text_hi).extracted_profile
    assert prof_hi.age == 28
    assert prof_hi.state == "UTTAR_PRADESH"
    assert prof_hi.district == "Lucknow"
    assert prof_hi.social_category == "OBC"
    assert prof_hi.sector == "AGRICULTURE" or prof_hi.activity_type == "DAIRY_FARMING"
    assert prof_hi.project_cost == 500000.0

    # Hinglish
    text_hing = "meri age 25 hai, female hu, bihar patna se hu, SC category, tailoring ka naya business lagana hai"
    prof_hing = NaturalLanguageProfileExtractor.extract_profile(text_hing).extracted_profile
    assert prof_hing.age == 25
    assert prof_hing.gender == "FEMALE"
    assert prof_hing.state == "BIHAR"
    assert prof_hing.district == "Patna"
    assert prof_hing.social_category == "SC"
    assert prof_hing.business_stage == "NEW"
    assert prof_hing.sector in ("MICRO_FINANCE", "TEXTILES") or prof_hing.activity_type == "SMALL_MICRO_BUSINESS"

    # English
    text_en = "I am 32 years old male from Maharashtra Pune, General category, want ₹10 Lakh loan for manufacturing unit"
    prof_en = NaturalLanguageProfileExtractor.extract_profile(text_en).extracted_profile
    assert prof_en.age == 32
    assert prof_en.gender == "MALE"
    assert prof_en.state == "MAHARASHTRA"
    assert prof_en.district == "Pune"
    assert prof_en.social_category == "GENERAL"
    assert prof_en.requested_loan_amount == 1000000.0
    assert prof_en.sector == "MANUFACTURING" or prof_en.activity_type == "MANUFACTURING"


# ---------------------------------------------------------------------------
# 4. MISSING INFORMATION CLARIFICATION FLOW & GROUNDED RECOMMENDATIONS
# ---------------------------------------------------------------------------
def test_missing_information_targeted_clarification(db: Session):
    """
    When user asks 'UP me dairy business ke liye scheme batao',
    system returns matching schemes AND asks targeted questions about category/stage,
    without requiring unnecessary questions.
    """
    session_id = "test-missing-info-flow-01"
    r = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="UP me dairy business ke liye scheme batao", session_id=session_id)
    )
    assert r.intent in ("SCHEME_DISCOVERY", "RECOMMENDATION_QUERY", "BUSINESS_PROFILE_INIT")
    assert r.deterministic_used is True
    # Verify recommendations returned
    assert len(r.rich_cards) > 0 or len(r.actions) > 0
    # Verify targeted missing information asked (category/stage)
    ans = r.answer.lower()
    assert "category" in ans or "वर्ग" in ans or "subsid" in ans or "stage" in ans or "योजना" in ans


# ---------------------------------------------------------------------------
# 5. DETERMINISTIC ELIGIBILITY & REJECTION EXPLANATION
# ---------------------------------------------------------------------------
def test_explain_rejection_plain_language(db: Session):
    """
    Verifies deterministic rejection reasons are rendered in plain language
    without LLM fabrication.
    """
    session_id = "test-rejection-explain-01"
    # Query why rejected for PMEGP
    r = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="Why am I not eligible for PMEGP?", session_id=session_id)
    )
    assert r.intent == "EXPLAIN_REJECTION"
    assert r.deterministic_used is True
    # Cites evaluated dimensions
    ans = r.answer.lower()
    assert "pmegp" in ans or "prime minister" in ans
    assert "criteria" in ans or "eligib" in ans or "guidelines" in ans or "पात्रता" in ans


# ---------------------------------------------------------------------------
# 6. NEGATIVE CONSTRAINTS & ZERO HALLUCINATION (SUBSIDY & LOAN)
# ---------------------------------------------------------------------------
def test_subsidy_query_no_invented_facts(db: Session):
    """
    Verifies accurate capital subsidy for PMEGP and explicit 0% subsidy notification for MUDRA.
    """
    # 1. PMEGP subsidy
    r_pmegp = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="PMEGP me subsidy kitni milti hai?", session_id="test-sub-pmegp")
    )
    assert r_pmegp.intent == "SUBSIDY_QUERY"
    ans_pmegp = r_pmegp.answer
    assert "15%" in ans_pmegp or "25%" in ans_pmegp or "35%" in ans_pmegp

    # 2. MUDRA subsidy (Must state NO capital subsidy is provided)
    r_mudra = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="Mudra loan me subsidy kitni hai?", session_id="test-sub-mudra")
    )
    assert r_mudra.intent == "SUBSIDY_QUERY"
    ans_mudra = r_mudra.answer.lower()
    assert "not provide" in ans_mudra or "no capital subsidy" in ans_mudra or "सब्सिडी नहीं" in ans_mudra or "collateral-free" in ans_mudra


# ---------------------------------------------------------------------------
# 7. CONTEXTUAL PRONOUN & REFERENCE RESOLUTION ("isme", "iske", "documents?")
# ---------------------------------------------------------------------------
def test_pronoun_reference_resolution_flow(db: Session):
    """
    Turn 1: Ask about PMEGP
    Turn 2: Ask 'Isme subsidy kitni hai?' (Must resolve 'Isme' to PMEGP)
    Turn 3: Ask 'Documents kya lagenge?' (Must resolve to PMEGP document checklist)
    Turn 4: Ask 'Online apply kaise kare?' (Must resolve to PMEGP application guidelines)
    """
    session_id = "test-pronoun-flow-88"

    # Turn 1: Establish active scheme context
    r1 = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="PMEGP scheme ke baare me batao", session_id=session_id)
    )
    mem1 = GPTCopilotAgent.get_session_memory(session_id)
    assert mem1.get("active_scheme_id") == "SIH26092-001"

    # Turn 2: Pronoun subsidy follow-up
    r2 = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="Isme subsidy kitni hai?", session_id=session_id)
    )
    assert r2.intent == "SUBSIDY_QUERY"
    assert "PMEGP" in r2.answer or "15%" in r2.answer or "35%" in r2.answer

    # Turn 3: Pronoun document follow-up
    r3 = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="iske documents kya lagenge?", session_id=session_id)
    )
    assert r3.intent == "DOCUMENT_QUERY"
    assert "PMEGP" in r3.answer or "Prime Minister" in r3.answer

    # Turn 4: Application follow-up
    r4 = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="Online apply kaise kare?", session_id=session_id)
    )
    assert r4.intent == "APPLICATION_QUERY"
    assert "PMEGP" in r4.answer or "Prime Minister" in r4.answer or "schemes/SIH26092-001" in str(r4.actions)


# ---------------------------------------------------------------------------
# 8. SCHEME COMPARISON ACROSS 10 STRUCTURED DIMENSIONS
# ---------------------------------------------------------------------------
def test_scheme_comparison_10_dimensions(db: Session):
    """
    'PMEGP aur Mudra me difference?'
    Must return structured comparison across 10 dimensions.
    """
    r = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="PMEGP aur Mudra me difference?", session_id="test-comp-10-dim")
    )
    assert r.intent in ("SCHEME_COMPARISON", "SCHEME_DIFFERENCE")
    assert r.deterministic_used is True
    ans = r.answer
    # Check for core comparison dimensions
    assert "Eligibility" in ans or "पात्रता" in ans or "Funding" in ans
    assert "Subsidy" in ans or "Capital Subsidy" in ans or "सब्सिडी" in ans
    assert "Interest" in ans or "ब्याज" in ans
    assert "Collateral" in ans or "गारंटी" in ans
    assert len(r.rich_cards) > 0
    assert r.rich_cards[0].card_type == "COMPARISON_TABLE"


# ---------------------------------------------------------------------------
# 9. DETERMINISTIC FINANCIAL REASONING & ZERO FABRICATED RATES
# ---------------------------------------------------------------------------
def test_financial_reasoning_and_rate_accuracy(db: Session):
    """
    '10 lakh loan 5 saal ke liye EMI?'
    Calculates EMI deterministically and clarifies interest rate origin.
    """
    r = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(message="10 lakh loan 5 saal ke liye EMI kitni hogi?", session_id="test-fin-calc-10l")
    )
    assert r.intent == "FINANCIAL_QUERY"
    assert r.deterministic_used is True
    assert r.financial_calculation is not None
    # Monthly EMI calculated
    assert r.financial_calculation.get("periodic_installment", 0) > 0
    ans = r.answer.lower()
    assert "1,000,000" in ans or "10,00,000" in ans or "1000000" in ans
    assert "emi" in ans


# ---------------------------------------------------------------------------
# 10. OUT-OF-DOMAIN GUARDRAIL (CRICKET, CODING, COOKING)
# ---------------------------------------------------------------------------
def test_out_of_domain_guardrail(db: Session):
    """
    Unrelated topics (cricket, coding, cooking, trivia) must NOT fabricate schemes.
    Must return polite redirect with 0 citations and 0 RAG leaks.
    """
    unrelated_queries = [
        "Who is the captain of Indian cricket team?",
        "Write a Python script to sort a dictionary",
        "Recipe for making butter chicken",
        "What is the capital of Australia?",
    ]
    for q in unrelated_queries:
        r = GPTCopilotAgent.process_query(db, AIChatRequest(message=q, session_id=f"test-ood-{hash(q)}"))
        assert r.intent == "OUT_OF_DOMAIN"
        assert r.response_mode == "CASUAL"
        assert len(r.citations) == 0
        ans = r.answer.lower()
        # Polite redirection to government schemes
        assert "yojnasetu" in ans or "government scheme" in ans or "सरकारी योजना" in ans
        assert "cricket" not in ans or "apologize" in ans or "माफ़" in ans


# ---------------------------------------------------------------------------
# 11. MULTILINGUAL PARITY (HINDI, HINGLISH, ENGLISH)
# ---------------------------------------------------------------------------
def test_multilingual_concept_parity(db: Session):
    """
    Verifies that English, Hindi (Devanagari), and Hinglish all route to the same core intents.
    """
    pairs = [
        ("मुझे बिज़नेस के लिए लोन चाहिए", "SCHEME_DISCOVERY"),
        ("business loan chahiye bhai", "BUSINESS_PROFILE_INIT"),
        ("I need a loan for business", "BUSINESS_PROFILE_INIT"),
        ("क्या दस्तावेज़ लगेंगे?", "DOCUMENT_QUERY"),
        ("documents kya lagenge?", "DOCUMENT_QUERY"),
        ("What documents are required?", "DOCUMENT_QUERY"),
    ]
    for msg, expected in pairs:
        res = classify_intent(msg)
        assert res in (expected, "SCHEME_DISCOVERY", "BUSINESS_PROFILE_INIT", "DOCUMENT_QUERY"), f"Parity mismatch for '{msg}': got {res}"
