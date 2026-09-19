import os
import sys
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.ai.agent import GPTCopilotAgent
from app.schemas.ai import AIChatRequest
from app.ai.hybrid_rag import HybridSchemeRAG

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from seed_db import seed_database


@pytest.fixture(scope="module")
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    seed_database(session)
    yield session
    session.close()


def test_01_greeting_no_rag_no_random_scheme(db):
    """TEST 1: User says 'hi' -> GREETING, no scheme retrieval, no random scheme."""
    with patch.object(HybridSchemeRAG, "hybrid_search", return_value=[]) as mock_rag:
        res = GPTCopilotAgent.process_query(db, AIChatRequest(message="hi"))
        assert mock_rag.call_count == 0, "RAG hybrid_search must not be called for greeting"
        assert res.intent in ("GREETING", "CASUAL_GREETING")
        assert len(res.citations) == 0
        assert len(res.rich_cards) == 0
        assert "Namaste" in res.answer or "Assistant" in res.answer


def test_02_language_switch_no_rag(db):
    """TEST 2: User says 'hindi' -> LANGUAGE_SWITCH, no scheme retrieval."""
    with patch.object(HybridSchemeRAG, "hybrid_search", return_value=[]) as mock_rag:
        res = GPTCopilotAgent.process_query(db, AIChatRequest(message="hindi"))
        assert mock_rag.call_count == 0, "RAG hybrid_search must not be called for language switch"
        assert res.intent in ("LANGUAGE_SWITCH", "LANGUAGE_CHANGE")
        assert len(res.citations) == 0
        assert len(res.rich_cards) == 0
        assert "हिंदी" in res.answer


def test_03_profile_update_name(db):
    """TEST 3: User says 'my name is Jai' -> PROFILE_UPDATE, profile.name == 'Jai', no scheme retrieval."""
    session_id = "test-prof-name-1"
    with patch.object(HybridSchemeRAG, "hybrid_search", return_value=[]) as mock_rag:
        res = GPTCopilotAgent.process_query(db, AIChatRequest(message="my name is Jai", session_id=session_id))
        assert mock_rag.call_count == 0, "RAG must not be called for name introduction"
        assert res.intent in ("PROFILE_UPDATE", "PROFILE_CORRECTION")
        assert len(res.citations) == 0
        mem = GPTCopilotAgent.get_session_memory(session_id)
        assert mem["extracted_facts"].get("name") == "Jai"
        assert "Jai" in res.answer


def test_04_profile_update_location(db):
    """TEST 4: User says 'i am from Gorakhpur' -> PROFILE_UPDATE, district == 'Gorakhpur', state == 'Uttar Pradesh', no scheme retrieval."""
    session_id = "test-prof-loc-1"
    with patch.object(HybridSchemeRAG, "hybrid_search", return_value=[]) as mock_rag:
        res = GPTCopilotAgent.process_query(db, AIChatRequest(message="i am from Gorakhpur", session_id=session_id))
        assert mock_rag.call_count == 0, "RAG must not be called for location statement"
        assert res.intent in ("PROFILE_UPDATE", "PROFILE_CORRECTION")
        assert len(res.citations) == 0
        mem = GPTCopilotAgent.get_session_memory(session_id)
        assert mem["extracted_facts"].get("district") == "Gorakhpur"
        assert mem["extracted_facts"].get("state") in ("UTTAR PRADESH", "Uttar Pradesh")
        assert "Gorakhpur" in res.answer


def test_05_incremental_profile_accumulation(db):
    """
    TEST 5:
    my name is Jai
    i am from Gorakhpur
    I am 24
    I am SC
    I want to start a dairy business
    I need a 3 lakh loan
    Expected final profile contains all available values and does not erase previous turns.
    """
    session_id = "test-multi-turn-accum-5"
    turns = [
        "my name is Jai",
        "i am from Gorakhpur",
        "I am 24",
        "I am SC",
        "I want to start a dairy business",
        "I need a 3 lakh loan"
    ]
    for msg in turns:
        GPTCopilotAgent.process_query(db, AIChatRequest(message=msg, session_id=session_id))

    mem = GPTCopilotAgent.get_session_memory(session_id)
    facts = mem["extracted_facts"]
    assert facts.get("name") == "Jai", f"Expected name 'Jai', got {facts.get('name')}"
    assert facts.get("district") == "Gorakhpur", f"Expected district 'Gorakhpur', got {facts.get('district')}"
    assert facts.get("state") in ("UTTAR PRADESH", "Uttar Pradesh"), f"Expected UP, got {facts.get('state')}"
    assert facts.get("age") == 24, f"Expected age 24, got {facts.get('age')}"
    assert facts.get("social_category") == "SC", f"Expected category 'SC', got {facts.get('social_category')}"
    assert facts.get("sector") == "DAIRY" or facts.get("activity_type") == "DAIRY_FARMING"
    assert facts.get("requested_loan_amount") == 300000.0, f"Expected 300000.0 loan, got {facts.get('requested_loan_amount')}"

    # Build full profile
    profile = GPTCopilotAgent.build_profile_from_memory(session_id, None)
    assert profile.name == "Jai"
    assert profile.district == "Gorakhpur"
    assert profile.state == "UTTAR PRADESH"
    assert profile.age == 24
    assert profile.social_category == "SC"
    assert profile.is_sc is True
    assert profile.requested_loan_amount == 300000.0


def test_06_casual_tum_pagal_ho(db):
    """TEST 6: User says 'tum pagal ho' -> CASUAL_CONVERSATION, no scheme retrieval."""
    with patch.object(HybridSchemeRAG, "hybrid_search", return_value=[]) as mock_rag:
        res = GPTCopilotAgent.process_query(db, AIChatRequest(message="tum pagal ho"))
        assert mock_rag.call_count == 0
        assert res.intent in ("CASUAL_CONVERSATION",)
        assert len(res.citations) == 0
        assert len(res.rich_cards) == 0
        assert any(c in res.answer for c in ["Fair enough", "मदद", "help", "😂"])


def test_07_casual_you_are_lame(db):
    """TEST 7: User says 'you are lame' -> CASUAL_CONVERSATION, no scheme retrieval."""
    with patch.object(HybridSchemeRAG, "hybrid_search", return_value=[]) as mock_rag:
        res = GPTCopilotAgent.process_query(db, AIChatRequest(message="you are lame"))
        assert mock_rag.call_count == 0
        assert res.intent in ("CASUAL_CONVERSATION",)
        assert len(res.citations) == 0
        assert len(res.rich_cards) == 0
        assert any(c in res.answer for c in ["Fair enough", "help", "😂"])


def test_08_scheme_discovery_executes(db):
    """TEST 8: User says 'Which government schemes can I get for a dairy business?' -> SCHEME_DISCOVERY executes."""
    res = GPTCopilotAgent.process_query(db, AIChatRequest(message="Which government schemes can I get for a dairy business?"))
    assert res.intent in ("SCHEME_DISCOVERY", "BUSINESS_PROFILE_INIT")
    assert res.deterministic_used is True
    assert "AHIDF" in res.answer or "Dairy" in res.answer or "PMEGP" in res.answer or "Animal Husbandry" in res.answer or len(res.rich_cards) > 0


def test_09_financial_calculation_deterministic(db):
    """TEST 9: User says 'Calculate EMI for ₹2 lakh.' -> FINANCIAL_CALCULATION deterministic engine executes."""
    res = GPTCopilotAgent.process_query(db, AIChatRequest(message="Calculate EMI for ₹2 lakh."))
    assert res.intent in ("FINANCIAL_CALCULATION", "FINANCIAL_QUERY")
    assert res.deterministic_used is True
    assert res.financial_calculation is not None or "EMI" in res.answer
    assert "₹" in res.answer or "Rs" in res.answer or "2,00,000" in res.answer or "200000" in res.answer


def test_10_partner_location_routing(db):
    """TEST 10: User says 'Where is the nearest place to apply?' -> PARTNER_LOCATION routing executes."""
    res = GPTCopilotAgent.process_query(
        db,
        AIChatRequest(
            message="Where is the nearest place to apply?",
            scheme_id="SIH26092-001"
        )
    )
    assert res.intent in ("PARTNER_LOCATION", "PARTNER_DISCOVERY")
    assert res.deterministic_used is True
    assert "Bank" in res.answer or "Branch" in res.answer or "Portal" in res.answer or "KVIB" in res.answer or "DIC" in res.answer or "CSC" in res.answer


def test_11_scheme_comparison(db):
    """TEST 11: User says 'Compare PMEGP and MUDRA.' -> SCHEME_COMPARISON executes."""
    res = GPTCopilotAgent.process_query(db, AIChatRequest(message="Compare PMEGP and MUDRA."))
    assert res.intent in ("SCHEME_COMPARISON", "SCHEME_DIFFERENCE")
    assert res.deterministic_used is True
    assert "PMEGP" in res.answer and ("MUDRA" in res.answer or "PMMY" in res.answer)


def test_12_language_switch_preserves_profile_and_scheme_context(db):
    """
    TEST 12: User changes language during an existing conversation.
    Expected: Language changes to Hindi, but citizen profile and scheme context remain intact.
    """
    session_id = "test-lang-switch-persist-12"

    # Turn 1: Name and location
    GPTCopilotAgent.process_query(db, AIChatRequest(message="my name is Jai", session_id=session_id))
    GPTCopilotAgent.process_query(db, AIChatRequest(message="i am from Gorakhpur", session_id=session_id))

    # Turn 2: Switch language to Hindi
    r_lang = GPTCopilotAgent.process_query(db, AIChatRequest(message="hindi", session_id=session_id))
    assert r_lang.intent in ("LANGUAGE_SWITCH", "LANGUAGE_CHANGE")
    assert r_lang.language == "hi"

    # Check memory still has profile
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["preferred_language"] == "hi"
    assert mem["extracted_facts"].get("name") == "Jai"
    assert mem["extracted_facts"].get("district") == "Gorakhpur"
    assert mem["extracted_facts"].get("state") == "UTTAR PRADESH"

    # Turn 3: Follow-up in Hindi/Hinglish
    r3 = GPTCopilotAgent.process_query(db, AIChatRequest(message="meri umar 24 hai", session_id=session_id))
    mem3 = GPTCopilotAgent.get_session_memory(session_id)
    assert mem3["extracted_facts"].get("name") == "Jai"
    assert mem3["extracted_facts"].get("district") == "Gorakhpur"
    assert mem3["extracted_facts"].get("age") == 24
    assert r3.language == "hi"
