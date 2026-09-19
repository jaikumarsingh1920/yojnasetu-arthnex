"""
Regression and verification test suite for RAG multilingual search (Devanagari Hindi, Hinglish, English)
and false positive query rejection.
"""
import pytest
from app.db.session import SessionLocal
from app.ai.rag import SchemeVectorStore


@pytest.fixture(scope="module")
def rag_store():
    db = SessionLocal()
    vs = SchemeVectorStore(db)
    yield vs
    db.close()


def test_rag_devanagari_hindi_retrieval(rag_store):
    """Verify that Devanagari Hindi queries successfully retrieve grounded citations."""
    hindi_queries = [
        "अनुसूचित जाति के लिए व्यवसाय ऋण",
        "स्वरोजगार और ऋण",
        "महिला उद्यमी व्यवसाय",
        "दस्तावेज और प्रमाण पत्र",
        "कारीगर और शिल्पकार",
    ]
    for q in hindi_queries:
        citations = rag_store.search(q, top_k=3)
        assert len(citations) > 0, f"Expected non-zero citations for Hindi query: '{q}'"
        assert citations[0].relevance_score > 0.20
        assert citations[0].snippet is not None


def test_rag_english_and_hinglish_regression(rag_store):
    """Verify that existing English and Hinglish queries remain highly accurate and intact."""
    benchmark_queries = [
        "loan for scheduled caste business",
        "SC category ke liye business loan chahiye",
        "maximum loan for MSME",
        "SC woman business loan",
        "PMEGP eligibility",
    ]
    for q in benchmark_queries:
        citations = rag_store.search(q, top_k=3)
        assert len(citations) > 0, f"Expected non-zero citations for query: '{q}'"
        assert citations[0].relevance_score >= 0.50


def test_rag_out_of_domain_false_positives_rejected(rag_store):
    """Verify that completely unrelated/out-of-domain queries return zero citations."""
    irrelevant_queries = [
        "how to cook hyderabadi biryani recipe",
        "quantum mechanics schrodinger wave equation",
        "best cryptocurrency trading bot python",
        "football match tonight",
    ]
    for q in irrelevant_queries:
        citations = rag_store.search(q, top_k=3)
        assert len(citations) == 0, (
            f"Expected 0 citations for out-of-domain query '{q}', got {len(citations)}: "
            f"{[c.scheme_name for c in citations]}"
        )
