import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.ai.provider import GeminiProvider, get_ai_provider, DevFallbackProvider
from app.ai.copilot_router import AICopilotQueryRouter
from app.core.config import settings

client = TestClient(app)


def test_gemini_provider_init_and_generate_mock():
    """Verify GeminiProvider initializes with model setting and sends system_instruction payload."""
    provider = GeminiProvider(api_key="test_mock_gemini_key", model="gemini-1.5-flash")
    assert provider.name == "google_gemini"
    assert provider.is_fallback is False

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "PMEGP provides up to 35% capital subsidy for setting up new micro-enterprises."}
                    ]
                }
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        result = provider.generate(
            prompt="What is PMEGP?",
            system_prompt="GROUNDED CONTEXT: PMEGP provides capital subsidy."
        )
        assert "35% capital subsidy" in result
        assert mock_post.call_count == 1
        call_kwargs = mock_post.call_args[1]
        json_body = call_kwargs["json"]
        assert "contents" in json_body
        assert "system_instruction" in json_body
        assert json_body["system_instruction"]["parts"][0]["text"].startswith("GROUNDED CONTEXT:")


def test_get_ai_provider_factory():
    """Verify factory returns GeminiProvider when GEMINI_API_KEY is configured."""
    with patch.object(settings, "GEMINI_API_KEY", "test_key_123"):
        provider = get_ai_provider()
        assert isinstance(provider, GeminiProvider)
        assert provider.name == "google_gemini"

    with patch.object(settings, "GEMINI_API_KEY", None), patch.object(settings, "OPENAI_API_KEY", None):
        provider = get_ai_provider()
        assert isinstance(provider, DevFallbackProvider)
        assert provider.is_fallback is True


def test_casual_chat_bypass_zero_rag_citations():
    """Verify simple casual queries bypass RAG and Gemini generation with 0 citations."""
    casual_inputs = ["hi", "hello", "how are you?", "thanks", "bye", "you are fool"]
    for msg in casual_inputs:
        res = client.post("/api/v1/ai/chat", json={"message": msg})
        assert res.status_code == 200
        data = res.json()
        assert len(data["citations"]) == 0, f"Failed for casual input '{msg}'"
        assert len(data["answer"]) > 5
        assert "SIH26092" not in data["answer"]


def test_deterministic_tool_priority_over_llm():
    """Verify deterministic tools are authoritative for eligibility, financials, and documents."""
    # 1. Financial Calculation Tool
    res_fin = client.post("/api/v1/ai/chat", json={
        "message": "Calculate EMI for ₹1 lakh",
        "scheme_id": "SIH26092-001"
    })
    assert res_fin.status_code == 200
    data_fin = res_fin.json()
    assert data_fin["intent"] == "FINANCIAL_QUERY"
    assert data_fin["deterministic_used"] is True
    assert data_fin["financial_calculation"] is not None

    # 2. Document Checklist Tool
    res_doc = client.post("/api/v1/ai/chat", json={
        "message": "What documents do I need?",
        "scheme_id": "SIH26092-001"
    })
    assert res_doc.status_code == 200
    data_doc = res_doc.json()
    assert data_doc["intent"] == "DOCUMENT_QUERY"
    assert "RULE-0002" not in data_doc["answer"]

    # 3. Partner Discovery Tool
    res_part = client.post("/api/v1/ai/chat", json={
        "message": "Where is the nearest authorized partner?"
    })
    assert res_part.status_code == 200
    data_part = res_part.json()
    assert data_part["intent"] == "PARTNER_DISCOVERY"


def test_grounded_rag_with_gemini_mocked():
    """Test grounded RAG flow passes retrieved context to Gemini and maintains source attribution."""
    mock_gemini_text = "PMEGP is a major credit-linked subsidy scheme by the MSME Ministry to help individuals start new micro-enterprises."

    with patch.object(settings, "GEMINI_API_KEY", "mock_key_gemini"), \
         patch.object(GeminiProvider, "generate", return_value=mock_gemini_text):
        res = client.post("/api/v1/ai/chat", json={
            "message": "What is PMEGP?",
            "scheme_id": "SIH26092-001"
        })
        assert res.status_code == 200
        data = res.json()
        assert mock_gemini_text in data["answer"]
        assert len(data["citations"]) > 0
        assert data["citations"][0]["scheme_id"] == "SIH26092-001"


def test_unsupported_factual_question_grounding_fallback():
    """Test out-of-domain unverified queries return grounded fallback notice without hallucinations."""
    res = client.post("/api/v1/ai/chat", json={
        "message": "What is the secret alien code for spaceship teleportation in year 2099?"
    })
    assert res.status_code == 200
    data = res.json()
    ans_lower = data["answer"].lower()
    assert any(term in ans_lower for term in ["couldn't verify", "official scheme", "official verified information", "guide", "schemes", "loan"])


def test_api_security_no_key_leakage():
    """Verify GEMINI_API_KEY is NEVER exposed in API response payload or headers."""
    test_key = "SECRET_GEMINI_KEY_999"
    with patch.object(settings, "GEMINI_API_KEY", test_key), \
         patch.object(GeminiProvider, "generate", return_value="Verified PMEGP details."):
        res = client.post("/api/v1/ai/chat", json={"message": "What is PMEGP?"})
        assert res.status_code == 200
        res_str = res.text
        assert test_key not in res_str


def test_multilingual_generation():
    """Verify multi-language handling returns localized answer structure across languages."""
    languages = [
        ("hi", "PMEGP ke baare mein batao"),
        ("bn", "PMEGP সম্পর্কে বলুন"),
        ("ta", "PMEGP பற்றி கூறுங்கள்"),
    ]
    for lang_code, msg in languages:
        res = client.post("/api/v1/ai/chat", json={
            "message": msg,
            "preferred_language": lang_code,
            "scheme_id": "SIH26092-001"
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data["answer"]) > 5


def test_language_change_zero_rag_citations():
    """Verify language change queries produce 0 citations, 0 scheme cards, 0 RAG search."""
    queries = ["talk in hindi", "talk in english", "हिंदी में बात करो", "talk in bengali"]
    for q in queries:
        res = client.post("/api/v1/ai/chat", json={"message": q})
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "LANGUAGE_CHANGE"
        assert len(data["citations"]) == 0
        assert len(data["rich_cards"]) == 0


def test_casual_insults_handling():
    """Verify casual insults return friendly responses with 0 citations."""
    insults = ["tum gadhe ho", "u r fool", "you are stupid", "ullu ho kya"]
    for ins in insults:
        res = client.post("/api/v1/ai/chat", json={"message": ins})
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "CASUAL_CONVERSATION"
        assert len(data["citations"]) == 0


def test_internal_metadata_sanitization():
    """Verify internal RAG metadata like RULE-0002 or Field: activity_type are NEVER exposed."""
    res = client.post("/api/v1/ai/chat", json={
        "message": "Am I eligible for PM Vishwakarma?",
        "scheme_id": "SIH26092-005"
    })
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"]
    assert "RULE-" not in ans
    assert "Field:" not in ans
    assert "TRADITIONAL_TRADE" not in ans
    assert "activity_type" not in ans


def test_generic_document_query_asking_clarification():
    """Verify generic document query without active scheme context asks clarification instead of default guessing."""
    res = client.post("/api/v1/ai/chat", json={"message": "documents kya kya lagenge"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "DOCUMENT_QUERY"
    assert "NSFDC Micro Finance" not in data["answer"]
    assert "which scheme" in data["answer"].lower() or "किस योजना" in data["answer"].lower() or "document checklist" in data["answer"].lower()


def test_conversational_discovery_onboarding():
    """Verify new business prompt triggers conversational discovery onboarding."""
    res = client.post("/api/v1/ai/chat", json={"message": "bhai mujhe ek naya kaam shuru krna h"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY")
    assert "State" in data["answer"] or "राज्य" in data["answer"]

