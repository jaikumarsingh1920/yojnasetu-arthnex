import pytest
from app.db.session import SessionLocal
from app.schemas.ai import AIChatRequest
from app.ai.copilot_router import AICopilotQueryRouter
from app.ai.agent import GPTCopilotAgent, sanitize_user_facing_text


@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_router_language_change_normalization_variants():
    """Verifies that all conversational Roman Hindi, Hinglish, voice shorthand, and regional phrases map to LANGUAGE_CHANGE."""
    test_phrases = [
        "hindi m baat kr",
        "hindi me baat kr",
        "hindi mein baat karo",
        "hindi me baat karo",
        "hindi m likh",
        "hindi me likho",
        "hindi mein likho",
        "mujhe english nhi aati",
        "mujhe english nahi aati",
        "english m baat kr",
        "english me baat karo",
        "talk in hindi",
        "talk in english",
        "hindi m baaat krooo",
        "speak to me in hindi",
        "speak in english",
        "switch to hindi",
        "বাংলায় কথা বলো",
        "தமிழில் பேசுங்கள்",
        "తెలుగులో మాట్లాడు",
        "मराठीत बोला",
        "ગુજરાતીમાં બોલો",
        "🗣️ Speak to me in Hindi",
    ]

    for phrase in test_phrases:
        intent = AICopilotQueryRouter.classify_intent(phrase)
        assert intent == "LANGUAGE_CHANGE", f"Failed for phrase: {phrase!r}, got: {intent}"


def test_router_casual_feedback_normalization():
    """Verifies that casual feedback and frustration expressions map to CASUAL_CONVERSATION without triggering RAG."""
    feedback_phrases = [
        "nhi chal rha h bhaiii",
        "nahi chal raha",
        "chal nahi raha bhai",
        "kuch nahi chal raha",
        "not working",
        "arre bhai",
        "kya yaar",
    ]

    for phrase in feedback_phrases:
        intent = AICopilotQueryRouter.classify_intent(phrase)
        assert intent in ("CASUAL_CONVERSATION", "EMOTIONAL_HELP"), f"Failed for feedback: {phrase!r}, got: {intent}"


def test_agent_language_change_absolute_early_exit(db_session):
    """
    Verifies that LANGUAGE_CHANGE results in strict 0 RAG, 0 Citations, 0 Cards,
    and updates session language properly.
    """
    session_id = "test-lang-early-exit-1"
    req = AIChatRequest(
        message="hindi m baat kr",
        session_id=session_id
    )

    res = GPTCopilotAgent.process_query(db_session, req)

    assert res.intent == "LANGUAGE_CHANGE"
    assert res.response_mode == "CASUAL"
    assert len(res.citations) == 0, "LANGUAGE_CHANGE must not return citations"
    assert len(res.rich_cards) == 0, "LANGUAGE_CHANGE must not return rich cards"
    assert res.deterministic_used is False
    assert "हिंदी" in res.answer or "Hindi" in res.answer or "बात" in res.answer

    # Verify session memory has updated preferred language
    memory = GPTCopilotAgent.get_session_memory(session_id)
    assert memory.get("preferred_language") == "hi"


def test_agent_context_isolation_prevents_stale_rag_leak(db_session):
    """
    Verifies that a prior scheme query (PMEGP) does NOT pollute subsequent
    language change or casual feedback queries with stale PMEGP citations.
    """
    session_id = "test-context-isolation-1"

    # Turn 1: PMEGP Scheme query
    req1 = AIChatRequest(
        message="PMEGP kya hai?",
        session_id=session_id
    )
    res1 = GPTCopilotAgent.process_query(db_session, req1)
    assert res1.intent == "GENERAL_SCHEME_QUERY"
    assert len(res1.citations) > 0, "PMEGP query should return grounded citations"

    # Turn 2: Language change request
    req2 = AIChatRequest(
        message="hindi m baaat krooo",
        session_id=session_id
    )
    res2 = GPTCopilotAgent.process_query(db_session, req2)
    assert res2.intent == "LANGUAGE_CHANGE"
    assert len(res2.citations) == 0, "Language change must not inherit PMEGP citations"
    assert len(res2.rich_cards) == 0

    # Turn 3: Casual feedback
    req3 = AIChatRequest(
        message="nhi chal rha h bhaiii",
        session_id=session_id
    )
    res3 = GPTCopilotAgent.process_query(db_session, req3)
    assert res3.intent == "CASUAL_CONVERSATION"
    assert len(res3.citations) == 0, "Casual feedback must not inherit PMEGP citations"
    assert "Official verified information for Prime Minister" not in res3.answer
    assert "PMEGP" not in res3.answer or "योजना" in res3.answer


def test_metadata_leak_sanitization():
    """Verifies that internal rule IDs and field tokens are thoroughly stripped."""
    raw_leak = "Rule Code: RULE-0015; Requirement Field: application_route; Field: annual_income <= 300000; Verification Status: VERIFIED"
    cleaned = sanitize_user_facing_text(raw_leak)
    assert "RULE-0015" not in cleaned
    assert "Requirement Field:" not in cleaned
    assert "Rule Code:" not in cleaned
    assert "Field:" not in cleaned
    assert "annual_income" not in cleaned
