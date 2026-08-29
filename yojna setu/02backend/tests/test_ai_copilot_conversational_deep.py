import os
import sys
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.ai.hybrid_rag import HybridSchemeRAG
from app.ai.agent import GPTCopilotAgent
from app.schemas.ai import AIChatRequest

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


def test_casual_queries_hard_gate(db):
    """Verify greetings, identity, and chit-chat queries produce 0 citations."""
    messages = [
        "hi", "hii", "hello bhai", "namaste", "who are you?", "tum kaun ho?",
        "naam kya hai?", "kya kar sakte ho?", "how are you?", "thanks", "bye"
    ]
    with patch.object(HybridSchemeRAG, "hybrid_search", return_value=[]) as mock_rag:
        for msg in messages:
            res = GPTCopilotAgent.process_query(db, AIChatRequest(message=msg))
            assert mock_rag.call_count == 0, f"RAG was called for casual message '{msg}'"
            assert len(res.citations) == 0
            assert res.response_mode in ["CASUAL", "CLARIFICATION"]


def test_hinglish_scheme_discovery_dialog(db):
    """Test Hinglish scheme discovery and profile accumulation."""
    session_id = "test-deep-hinglish-1"

    # Turn 1: Discovery Init
    r1 = GPTCopilotAgent.process_query(db, AIChatRequest(message="bhai scheme chahiye", session_id=session_id))
    assert r1.intent == "BUSINESS_PROFILE_INIT"
    assert "State" in r1.answer

    # Turn 2: State
    r2 = GPTCopilotAgent.process_query(db, AIChatRequest(message="mai UP se hu", session_id=session_id))
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["extracted_facts"].get("state") == "UTTAR PRADESH"

    # Turn 3: Age & Category
    r3 = GPTCopilotAgent.process_query(db, AIChatRequest(message="24 saal ka hu, SC category", session_id=session_id))
    assert mem["extracted_facts"].get("age") == 24
    assert mem["extracted_facts"].get("social_category") == "SC"


def test_profile_correction(db):
    """Test updating profile memory on correction."""
    session_id = "test-profile-correction-1"

    # Turn 1: Init age 24, category SC
    GPTCopilotAgent.process_query(db, AIChatRequest(message="24 saal, SC hu", session_id=session_id))
    mem = GPTCopilotAgent.get_session_memory(session_id)
    assert mem["extracted_facts"].get("age") == 24
    assert mem["extracted_facts"].get("social_category") == "SC"

    # Turn 2: Correction "actually meri age 26 hai, nahi OBC hu"
    GPTCopilotAgent.process_query(db, AIChatRequest(message="actually meri age 26 hai, nahi OBC hu", session_id=session_id))
    assert mem["extracted_facts"].get("age") == 26
    assert mem["extracted_facts"].get("social_category") == "OBC"


def test_contextual_pronoun_resolution(db):
    """Test resolving 'isme', 'iske' to current scheme context."""
    session_id = "test-pronoun-context-1"

    # Turn 1: Explicit scheme query
    r1 = GPTCopilotAgent.process_query(db, AIChatRequest(message="PMEGP kya hai?", session_id=session_id))
    assert "PMEGP" in r1.answer or len(r1.citations) > 0

    # Turn 2: "isme loan?"
    r2 = GPTCopilotAgent.process_query(db, AIChatRequest(message="isme loan?", session_id=session_id))
    assert r2.intent == "FINANCIAL_QUERY"
    assert r2.deterministic_used is True

    # Turn 3: "documents?"
    r3 = GPTCopilotAgent.process_query(db, AIChatRequest(message="documents?", session_id=session_id))
    assert r3.intent == "DOCUMENT_QUERY"

    # Turn 4: "apply kaise karu?"
    r4 = GPTCopilotAgent.process_query(db, AIChatRequest(message="apply kaise karu?", session_id=session_id))
    assert r4.intent == "APPLICATION_QUERY"
    assert "How to Apply" in r4.answer or "Official Portal" in r4.answer


def test_financial_query_deterministic_execution(db):
    """Test '2 lakh ka EMI' invokes deterministic engine."""
    res = GPTCopilotAgent.process_query(db, AIChatRequest(message="2 lakh ka EMI"))
    assert res.intent == "FINANCIAL_QUERY"
    assert res.deterministic_used is True
    assert res.financial_calculation is not None


def test_off_topic_query(db):
    """Test off-topic queries return 0 citations and polite redirection."""
    res = GPTCopilotAgent.process_query(db, AIChatRequest(message="who won the match?"))
    assert res.intent == "CASUAL_CONVERSATION"
    assert len(res.citations) == 0
    assert "schemes" in res.answer.lower()
