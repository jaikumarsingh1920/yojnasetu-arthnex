import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.ai.copilot_router import AICopilotQueryRouter
from app.ai.tools import CopilotTools
from app.ai.hybrid_rag import HybridSchemeRAG
from app.ai.agent import GPTCopilotAgent
from app.schemas.ai import AIChatRequest
from app.schemas.recommendation import BeneficiaryProfileInput

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


def test_casual_queries_zero_rag_and_zero_citations_hard_gate(db):
    """Verify casual greetings, identity questions, insults, and chit-chat DO NOT call RAG or dump citations."""
    casual_messages = [
        "hi",
        "hello",
        "whats ur name",
        "who r u",
        "where are u from",
        "are u a fool",
        "what are u doing",
        "i love u"
    ]

    with patch.object(HybridSchemeRAG, "hybrid_search", return_value=[]) as mock_rag:
        for msg in casual_messages:
            res = GPTCopilotAgent.process_query(db, AIChatRequest(message=msg))

            # RAG call count MUST be EXACTLY 0
            assert mock_rag.call_count == 0, f"RAG was incorrectly called for casual query '{msg}'"
            assert res.response_mode == "CASUAL"
            assert len(res.citations) == 0, f"Citations were incorrectly returned for casual query '{msg}'"
            assert res.answer is not None


def test_scheme_query_invokes_rag(db):
    """Verify genuine scheme queries DO invoke RAG search."""
    with patch.object(HybridSchemeRAG, "hybrid_search", wraps=HybridSchemeRAG(db).hybrid_search) as spy_rag:
        res = GPTCopilotAgent.process_query(db, AIChatRequest(message="what is PMEGP?"))
        assert spy_rag.call_count > 0, "RAG was NOT invoked for genuine scheme query"
        assert res.response_mode == "GROUNDED"


def test_business_start_karna_hai_conversational_dialog(db):
    """Verify 'bhai mujhe business start karna hai' starts a single-question profile dialog without RAG or scheme dumps."""
    sess_id = "test-biz-dialog-1"

    with patch.object(HybridSchemeRAG, "hybrid_search", return_value=[]) as mock_rag:
        req = AIChatRequest(message="bhai mujhe business start karna hai", session_id=sess_id)
        res = GPTCopilotAgent.process_query(db, req)

        assert mock_rag.call_count == 0, "RAG should NOT be called for initial business profile dialog"
        assert res.intent == "BUSINESS_PROFILE_INIT"
        assert res.response_mode == "CLARIFICATION"
        assert len(res.citations) == 0
        assert len(res.rich_cards) == 0
        assert "State" in res.answer


def test_copilot_tools_execution(db):
    """Test typed internal tools execution."""
    schemes = CopilotTools.search_schemes(db, query="micro", limit=3)
    assert len(schemes) > 0
    assert "scheme_id" in schemes[0]

    details = CopilotTools.get_scheme_details(db, "SIH26092-052")
    assert details is not None
    assert details["scheme_id"] == "SIH26092-052"
    assert len(details["documents"]) > 0

    fin_calc = CopilotTools.calculate_financials(db, "SIH26092-052", 100000.0, 80000.0)
    assert fin_calc["status"] == "CALCULATED"
    assert fin_calc["eligible_loan_amount"] is not None


def test_hybrid_rag_reranker(db):
    """Test hybrid RAG search with query expansion and candidate reranking."""
    hybrid = HybridSchemeRAG(db)
    citations = hybrid.hybrid_search(
        query="tailoring business loan",
        state="UTTAR PRADESH",
        category="SC",
        top_k=3
    )
    assert len(citations) > 0
    assert citations[0].relevance_score > 0.0


def test_multi_turn_conversation_memory(db):
    """Test multi-turn conversational fact accumulation."""
    session_id = "test-gpt-sess-1"

    # Turn 1: Business intent
    req1 = AIChatRequest(message="bhai mujhe business start karna hai", session_id=session_id)
    res1 = GPTCopilotAgent.process_query(db, req1)
    assert res1.answer is not None

    # Turn 2: State
    req2 = AIChatRequest(message="UP", session_id=session_id)
    res2 = GPTCopilotAgent.process_query(db, req2)
    memory = GPTCopilotAgent.get_session_memory(session_id)
    assert memory["extracted_facts"].get("state") == "UTTAR PRADESH"

    # Turn 3: Category
    req3 = AIChatRequest(message="SC", session_id=session_id)
    res3 = GPTCopilotAgent.process_query(db, req3)
    assert memory["extracted_facts"].get("social_category") == "SC"

    # Turn 4: Income
    req4 = AIChatRequest(message="2 lakh", session_id=session_id)
    res4 = GPTCopilotAgent.process_query(db, req4)
    assert memory["extracted_facts"].get("annual_income") == 200000.0

    # Turn 5: Business activity (Completes profile -> triggers recommendation)
    req5 = AIChatRequest(message="tailoring shop", session_id=session_id)
    res5 = GPTCopilotAgent.process_query(db, req5)
    assert res5.deterministic_used is True
    assert len(res5.rich_cards) > 0


def test_sse_streaming_chunk_generation(db):
    """Test SSE streaming response chunk generator."""
    req = AIChatRequest(message="What documents are required for MSME schemes?")
    chunks = list(GPTCopilotAgent.generate_stream_chunks(db, req))

    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert "Required Documents" in full_text or "MSME" in full_text or "Scheme" in full_text
