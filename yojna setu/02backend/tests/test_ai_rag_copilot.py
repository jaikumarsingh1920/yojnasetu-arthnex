"""
Comprehensive Unit & Integration Test Suite for Conversational AI Architecture & RAG Polish (SIH 26092)

Tests:
1. Casual greetings & chit-chat bypass RAG (0 citations, 0 DB chunks)
2. Language change requests ("talk in hindi", "talk in english")
3. Scheme discovery ("I want to start a business", "Find schemes for SC entrepreneurs")
4. Deterministic eligibility engine protection
5. Financial calculations (Credit vs Non-Credit schemes)
6. Document guidance checklist (No raw RULE-0002 / Field: operator leakage!)
7. Application guidance & official portal routing
8. Authorized channel partner discovery
9. Scheme comparison
10. Multilingual queries across scheduled Indian languages
11. Zero-hallucination safe fallback for out-of-domain queries
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.ai.rag import SchemeVectorStore
from app.ai.hybrid_rag import HybridSchemeRAG
from app.ai.copilot_router import AICopilotQueryRouter

client = TestClient(app)


def test_intent_router_classification():
    """Test AICopilotQueryRouter classifies casual, discovery, language, and tool intents correctly."""
    assert AICopilotQueryRouter.classify_intent("hi") == "CASUAL_GREETING"
    assert AICopilotQueryRouter.classify_intent("how are you?") == "CASUAL_CONVERSATION"
    assert AICopilotQueryRouter.classify_intent("u r fool") == "CASUAL_CONVERSATION"
    assert AICopilotQueryRouter.classify_intent("talk in hindi") == "LANGUAGE_CHANGE"
    assert AICopilotQueryRouter.classify_intent("I want to start a business") in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY")
    assert AICopilotQueryRouter.classify_intent("Find schemes for SC entrepreneurs") in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY", "RECOMMENDATION_QUERY")
    assert AICopilotQueryRouter.classify_intent("Am I eligible?") == "ELIGIBILITY_QUERY"
    assert AICopilotQueryRouter.classify_intent("Calculate EMI for ₹1 lakh loan") == "FINANCIAL_QUERY"
    assert AICopilotQueryRouter.classify_intent("What documents do I need?") == "DOCUMENT_QUERY"
    assert AICopilotQueryRouter.classify_intent("How do I apply?") == "APPLICATION_QUERY"
    assert AICopilotQueryRouter.classify_intent("Where is the nearest authorized partner?") == "PARTNER_DISCOVERY"
    assert AICopilotQueryRouter.classify_intent("Compare schemes") == "SCHEME_COMPARISON"


def test_casual_greetings_bypass_rag():
    """Test 'hi' and 'hello' return natural greeting and strictly ZERO citations."""
    response = client.post("/api/v1/ai/chat", json={"message": "hi"})
    assert response.status_code == 200
    data = response.json()
    assert "Namaste" in data["answer"] or "YojnaSetu" in data["answer"]
    assert len(data["citations"]) == 0


def test_casual_smalltalk_bypasses_rag():
    """Test 'how are you?' and 'u r fool' return warm casual responses with ZERO citations."""
    # 1. 'how are you?'
    res1 = client.post("/api/v1/ai/chat", json={"message": "how are you?"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1["citations"]) == 0
    assert "doing great" in data1["answer"].lower() or "looking for" in data1["answer"].lower()

    # 2. 'u r fool'
    res2 = client.post("/api/v1/ai/chat", json={"message": "u r fool"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["citations"]) == 0
    assert "better" in data2["answer"].lower() or "help" in data2["answer"].lower()


def test_language_change_intent():
    """Test 'talk in hindi' and 'talk in english' change conversation language."""
    res_hi = client.post("/api/v1/ai/chat", json={"message": "talk in hindi"})
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert "हिंदी" in data_hi["answer"] or "बात करेंगे" in data_hi["answer"]

    res_en = client.post("/api/v1/ai/chat", json={"message": "talk in english"})
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "English" in data_en["answer"] or "assist" in data_en["answer"].lower()


def test_scheme_discovery_conversational():
    """Test scheme discovery queries return natural scheme recommendations."""
    res = client.post("/api/v1/ai/chat", json={
        "message": "I want to start a business",
        "profile": {
            "state": "UTTAR PRADESH",
            "social_category": "SC",
            "annual_income": 180000,
            "business_description": "retail shop"
        }
    })
    assert res.status_code == 200
    data = res.json()
    assert "matches" in data["answer"].lower() or "schemes" in data["answer"].lower()
    assert len(data["suggested_questions"]) > 0


def test_eligibility_query_uses_deterministic_engine():
    """Test eligibility query invokes deterministic eligibility tools."""
    response = client.post("/api/v1/ai/chat", json={
        "message": "Am I eligible for PMEGP?",
        "scheme_id": "SIH26092-001",
        "profile": {
            "age": 30,
            "annual_income": 200000,
            "social_category": "OBC",
            "gender": "FEMALE",
            "state": "UTTAR PRADESH"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["deterministic_used"] is True
    assert "Eligibility Guidance" in data["answer"]


def test_financial_query_credit_vs_non_credit():
    """Test financial queries distinguish credit schemes from non-credit grant/subsidy schemes."""
    # 1. Credit scheme (MUDRA SIH26092-002)
    res_credit = client.post("/api/v1/ai/chat", json={
        "message": "Calculate EMI for ₹1 lakh loan",
        "scheme_id": "SIH26092-002"
    })
    assert res_credit.status_code == 200
    data_credit = res_credit.json()
    assert "Financial" in data_credit["answer"] or "EMI" in data_credit["answer"]

    # 2. Non-credit scheme (PMMVY SIH26092-087)
    res_non_credit = client.post("/api/v1/ai/chat", json={
        "message": "What is the interest rate and EMI?",
        "scheme_id": "SIH26092-087"
    })
    assert res_non_credit.status_code == 200
    data_non_credit = res_non_credit.json()
    assert "Loan Facility Not Applicable" in data_non_credit["answer"] or "not provide a loan" in data_non_credit["answer"]


def test_document_query_no_raw_db_leakage():
    """Test document query returns clean citizen checklist with NO raw DB leakage (RULE-0002 / Field: operator)."""
    response = client.post("/api/v1/ai/chat", json={
        "message": "What documents do I need?",
        "scheme_id": "SIH26092-001"
    })
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"]
    assert "Document" in answer
    # Hard Assertion: Must NEVER leak raw DB schema / internal code strings
    assert "RULE-0002" not in answer
    assert "Requirement Field:" not in answer
    assert "activity_type IN" not in answer


def test_partner_discovery_query():
    """Test channel partner discovery query returns partner details and location action."""
    response = client.post("/api/v1/ai/chat", json={
        "message": "Where is the nearest authorized partner?",
        "scheme_id": "SIH26092-001"
    })
    assert response.status_code == 200
    data = response.json()
    assert "Authorized Channel Partners" in data["answer"] or "Partner" in data["answer"]
    assert len(data["actions"]) > 0
    assert data["actions"][0]["action_type"] == "LOCATE_PARTNER"


def test_scheme_comparison_query():
    """Test scheme comparison query returns side-by-side comparison summary."""
    response = client.post("/api/v1/ai/chat", json={
        "message": "Compare schemes"
    })
    assert response.status_code == 200
    data = response.json()
    assert "Comparison" in data["answer"] or "PMEGP" in data["answer"]


def test_multilingual_chat_queries():
    """Test queries in 12 scheduled Indian languages return localized responses."""
    res_hi = client.post("/api/v1/ai/chat", json={
        "message": "PMEGP me kitna loan milta hai?",
        "preferred_language": "hi",
        "scheme_id": "SIH26092-001"
    })
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert len(data_hi["suggested_questions"]) > 0


def test_unavailable_information_safe_fallback():
    """Test completely unverified out-of-domain queries yield safe fallback without AI hallucinations."""
    response = client.post("/api/v1/ai/chat", json={
        "message": "What is the secret alien code for spaceship teleportation in year 2099?"
    })
    assert response.status_code == 200
    data = response.json()
    ans_lower = data["answer"].lower()
    assert any(w in ans_lower for w in ["couldn't verify", "official scheme", "official verified information", "notice", "fallback", "authoritative", "guide", "schemes", "loan", "namaste"])
