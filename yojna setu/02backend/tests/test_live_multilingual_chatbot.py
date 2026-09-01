import pytest
import re
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.ai import AIChatRequest
from app.ai.copilot_router import AICopilotQueryRouter
from app.ai.agent import GPTCopilotAgent, sanitize_user_facing_text
from app.ai.copilot_service import AICopilotService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_language_detection_and_normalization():
    """Verifies that all variations of language change commands match LANGUAGE_CHANGE intent."""
    test_cases = [
        "🗣️ Speak to me in Hindi",
        "talk in hindi",
        "talk in english",
        "hindi me baat kro",
        "hindi me baaat kroo",
        "hindi mein baat karo",
        "hindi me likho",
        "hindi mein likho",
        "hindi me reply karo",
        "hindi mein jawab do",
        "hindi me batao",
        "hindi mein samjhao",
        "mujhe english nahi aati",
        "mujhe english nhi aati",
        "mujhe English nahi aati",
        "English samajh nahi aati",
        "Please reply in Hindi",
        "Please answer in Hindi",
        "Speak Hindi",
        "Write in Hindi",
        "हिंदी में बात करो",
        "हिंदी में लिखो",
        "मुझे अंग्रेज़ी नहीं आती",
        "english me baat karo",
        "speak english",
        "reply in english",
        "talk in bengali",
        "বাংলায় কথা বলো",
        "talk in tamil",
        "தமிழில் பேசுங்கள்",
        "talk in telugu",
        "मराठीत बोला",
        "ગુજરાતીમાં બોલો",
    ]

    for tc in test_cases:
        intent = AICopilotQueryRouter.classify_intent(tc)
        assert intent == "LANGUAGE_CHANGE", f"Query '{tc}' expected intent 'LANGUAGE_CHANGE', got '{intent}'"


def test_language_change_early_exit_zero_rag(db_session: Session):
    """Verifies that LANGUAGE_CHANGE queries produce 0 citations, 0 scheme cards, and clean localized answer."""
    language_queries = [
        ("🗣️ Speak to me in Hindi", "hi"),
        ("hindi me baaat kroo", "hi"),
        ("mujhe english nhi aati", "hi"),
        ("english me baat karo", "en"),
        ("speak english", "en"),
    ]

    for q, expected_lang in language_queries:
        req = AIChatRequest(message=q)
        res = GPTCopilotAgent.process_query(db_session, req)

        assert res.intent == "LANGUAGE_CHANGE"
        assert res.response_mode == "CASUAL"
        assert len(res.citations) == 0, f"Expected 0 citations for '{q}', got {len(res.citations)}"
        assert len(res.rich_cards) == 0, f"Expected 0 cards for '{q}', got {len(res.rich_cards)}"
        assert len(res.actions) == 0, f"Expected 0 actions for '{q}', got {len(res.actions)}"

        if expected_lang == "hi":
            assert any(word in res.answer for word in ["हिंदी", "योजनाओं", "बात करेंगे", "मदद"])
        elif expected_lang == "en":
            assert any(word in res.answer.lower() for word in ["english", "speak", "schemes"])


def test_active_scheme_isolation(db_session: Session):
    """Verifies that changing language does not repeat or query the active scheme from previous turns."""
    session_id = "test_active_scheme_session_999"

    # Turn 1: Ask about PM Vishwakarma
    req1 = AIChatRequest(message="What is PM Vishwakarma?", session_id=session_id)
    res1 = GPTCopilotAgent.process_query(db_session, req1)
    assert res1.intent in ("GENERAL_SCHEME_QUERY", "RECOMMENDATION_QUERY", "FACTUAL_QUERY")

    # Turn 2: Switch to Hindi
    req2 = AIChatRequest(message="hindi me baat kro", session_id=session_id)
    res2 = GPTCopilotAgent.process_query(db_session, req2)

    assert res2.intent == "LANGUAGE_CHANGE"
    assert len(res2.citations) == 0
    assert len(res2.rich_cards) == 0
    assert "PM Vishwakarma" not in res2.answer
    assert "RULE-" not in res2.answer


def test_generic_document_query_no_scheme_guessing(db_session: Session):
    """Verifies that 'documents kya kya lagenge' without active scheme clarifies rather than picking NSFDC."""
    req = AIChatRequest(message="documents kya kya lagenge")
    res = GPTCopilotAgent.process_query(db_session, req)

    assert res.intent == "DOCUMENT_QUERY"
    assert res.response_mode == "CLARIFICATION"
    assert len(res.citations) == 0
    assert len(res.rich_cards) == 0
    # Must ask for scheme name, NOT guess NSFDC or PM Vishwakarma
    assert "NSFDC Micro Finance Scheme" not in res.answer
    assert any(w in res.answer for w in ["योजना का नाम", "दस्तावेज़", "Checklist", "scheme name"])


def test_metadata_sanitization_defense_in_depth():
    """Verifies that internal rule IDs, SQL operators, and ENUM constants are completely stripped."""
    dirty_text = (
        "Scheme: NSFDC Micro Finance Scheme (MFS) "
        "Rule Code: RULE-0015 Field: application_route IN PM_SURAJ; AUTHORISED_SCA; AUTHORISED_CA "
        "Description: Direct application to NSFDC is not accepted. "
        "Requirement Field: activity_type Requirement Value: TRADITIONAL_TRADE_18 "
        "Verification Status: UNKNOWN"
    )

    clean = sanitize_user_facing_text(dirty_text)

    assert "RULE-0015" not in clean
    assert "Rule Code:" not in clean
    assert "Field:" not in clean
    assert "Requirement Field:" not in clean
    assert "Requirement Value:" not in clean
    assert "Verification Status:" not in clean
    assert "PM_SURAJ;" not in clean
    assert "AUTHORISED_SCA;" not in clean
    assert "TRADITIONAL_TRADE_18" not in clean
    assert "Direct application to NSFDC is not accepted." in clean


def test_full_exact_matrix_flow(db_session: Session):
    """Runs all 12 test matrix prompts from the specification."""
    session_id = "test_full_matrix_flow_123"

    # TEST 1: hi
    r1 = AICopilotService.process_chat(db_session, AIChatRequest(message="hi", session_id=session_id))
    assert r1.intent == "CASUAL_GREETING"
    assert len(r1.citations) == 0

    # TEST 2: whats your name
    r2 = AICopilotService.process_chat(db_session, AIChatRequest(message="whats your name", session_id=session_id))
    assert r2.intent == "IDENTITY_QUERY"
    assert len(r2.citations) == 0

    # TEST 3: hindi me baat kro
    r3 = AICopilotService.process_chat(db_session, AIChatRequest(message="hindi me baat kro", session_id=session_id))
    assert r3.intent == "LANGUAGE_CHANGE"
    assert len(r3.citations) == 0
    assert len(r3.rich_cards) == 0

    # TEST 4: mujhe english nhi aati
    r4 = AICopilotService.process_chat(db_session, AIChatRequest(message="mujhe english nhi aati", session_id=session_id))
    assert r4.intent == "LANGUAGE_CHANGE"
    assert len(r4.citations) == 0

    # TEST 5: hindi me baaat kroo
    r5 = AICopilotService.process_chat(db_session, AIChatRequest(message="hindi me baaat kroo", session_id=session_id))
    assert r5.intent == "LANGUAGE_CHANGE"
    assert len(r5.citations) == 0

    # TEST 6: mujhe business start karna hai
    r6 = AICopilotService.process_chat(db_session, AIChatRequest(message="mujhe business start karna hai", session_id=session_id))
    assert r6.intent in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY")
    assert len(r6.citations) == 0

    # TEST 7: documents kya kya lagenge
    r7 = AICopilotService.process_chat(db_session, AIChatRequest(message="documents kya kya lagenge", session_id=session_id))
    assert r7.intent == "DOCUMENT_QUERY"
    assert len(r7.citations) == 0
    assert "NSFDC" not in r7.answer

    # TEST 8: PMEGP kya hai?
    r8 = AICopilotService.process_chat(db_session, AIChatRequest(message="PMEGP kya hai?", session_id=session_id))
    assert "RULE-" not in r8.answer
    assert "Field:" not in r8.answer

    # TEST 9: PMEGP me loan kitna milega?
    r9 = AICopilotService.process_chat(db_session, AIChatRequest(message="PMEGP me loan kitna milega?", session_id=session_id))
    assert r9.intent in ("FINANCIAL_QUERY", "GENERAL_SCHEME_QUERY")

    # TEST 10: Calculate EMI for ₹2 lakh at 7% for 5 years
    r10 = AICopilotService.process_chat(db_session, AIChatRequest(message="Calculate EMI for ₹2 lakh at 7% for 5 years", session_id=session_id))
    assert r10.intent == "FINANCIAL_QUERY"
    assert r10.deterministic_used is True

    # TEST 11: Am I eligible for PMEGP?
    r11 = AICopilotService.process_chat(db_session, AIChatRequest(message="Am I eligible for PMEGP?", session_id=session_id))
    assert r11.intent == "ELIGIBILITY_QUERY"
    assert r11.deterministic_used is True

    # TEST 12: english me baat karo
    r12 = AICopilotService.process_chat(db_session, AIChatRequest(message="english me baat karo", session_id=session_id))
    assert r12.intent == "LANGUAGE_CHANGE"
    assert len(r12.citations) == 0
    assert len(r12.rich_cards) == 0
