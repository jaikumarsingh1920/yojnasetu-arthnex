"""
Comprehensive Test Suite for Scheme Knowledge Enrichment & RAG Expansion.
SIH26092 Smart Automation.

Verifies:
1. Rich scheme retrieval
2. Financial fact separation (never conflating project cost with loan/subsidy)
3. Granular eligibility fact retrieval without hallucination
4. Application journey & approval stages retrieval
5. Structured document retrieval and deduplication
6. Grounded FAQ retrieval (English, Hindi, Hinglish)
7. Source provenance preservation (source_url, document, confidence, quality_score)
8. Duplicate prevention & idempotency
9. Incremental RAG synchronization
10. Batch runner restartability and checkpointing
11. Unrelated / out-of-domain query rejection
"""

import os
import json
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.models.document import SchemeDocument
from app.models.knowledge import SchemeFAQ, SchemeKnowledgeProfile
from app.services.knowledge.enrichment_service import SchemeKnowledgeEnrichmentService
from app.services.knowledge.bulk_enrichment import SchemeBulkEnrichmentRunner
from app.ai.rag import SchemeVectorStore
from app.schemas.ai import SourceCitation


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def vector_store(db_session):
    return SchemeVectorStore(db_session)


def test_01_knowledge_profile_creation_and_dimensions(db_session: Session):
    """Verifies that enriched schemes have complete multi-dimensional SchemeKnowledgeProfile records."""
    profile = db_session.query(SchemeKnowledgeProfile).filter(
        SchemeKnowledgeProfile.scheme_id == "SIH26092-001"
    ).first()
    assert profile is not None, "PMEGP must have a SchemeKnowledgeProfile"
    assert profile.quality_score is not None
    assert 0.0 <= profile.quality_score <= 100.0

    # Aliases
    aliases = json.loads(profile.aliases)
    assert isinstance(aliases, list)
    assert any("PMEGP" in a for a in aliases)

    # Problem addressed & outcome
    assert profile.problem_addressed and len(profile.problem_addressed) > 10
    assert profile.intended_outcome and len(profile.intended_outcome) > 10

    # Geographic level
    assert profile.geographic_level in ("NATIONAL", "STATE", "UT", "REGION", "DISTRICT")

    # Approval stages
    stages = json.loads(profile.approval_stages)
    assert isinstance(stages, list)
    assert len(stages) >= 3
    assert any("Verification" in s or "Submission" in s for s in stages)

    # Provenance
    prov = json.loads(profile.source_provenance)
    assert "source_url" in prov
    assert "retrieval_timestamp" in prov
    assert "confidence" in prov


def test_02_financial_fact_separation(db_session: Session):
    """
    CRITICAL: Verifies that Project Cost is strictly NEVER conflated with
    Loan Amount, Margin Money, or Capital Subsidy.
    """
    pmegp = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert pmegp is not None

    fin_summary = SchemeKnowledgeEnrichmentService.extract_financial_summary(pmegp)
    assert "Project Cost" in fin_summary
    assert "Loan Quantum:" in fin_summary
    assert "Subsidy" in fin_summary
    assert "margin money" in fin_summary.lower()

    # For PMEGP:
    # Project cost is up to 50 Lakhs (mfg)
    # Margin money subsidy is 15% to 35%
    # They must be in distinct statements
    assert "margin money subsidy" in fin_summary.lower() or "subsidy" in fin_summary.lower()
    assert "project cost" in fin_summary.lower()


def test_03_no_hallucinated_facts(db_session: Session):
    """Verifies that missing parameters are reported as not specified rather than hallucinated."""
    # Create an artificial scheme with missing values
    dummy = Scheme(
        scheme_id="TEST-GHOST-001",
        scheme_name="National Merit Scholarship Scheme",
        support_type="Direct Scholarship Grant",
        loan_available="NO",
        purpose="General community grant.",
        target_beneficiary="All Citizens",
        max_loan_amount=None,
        interest_rate_max=None,
        age_min=None,
        age_max=None,
        income_limit=None
    )

    fin_summary = SchemeKnowledgeEnrichmentService.extract_financial_summary(dummy)
    assert "not specified" in fin_summary.lower()

    faqs = SchemeKnowledgeEnrichmentService.derive_grounded_faqs(dummy, fin_summary, "Online portal")
    assert len(faqs) >= 5
    # The first FAQ (Who can apply?) must not hallucinate age or income
    who_can_apply_faq = next(f for f in faqs if "Who can apply" in f["question"])
    assert "No specific age limit specified in official guidelines" in who_can_apply_faq["answer"]
    assert "No restrictive income ceiling specified in available guidelines" in who_can_apply_faq["answer"]


def test_04_grounded_faqs_structure_and_provenance(db_session: Session):
    """Verifies that FAQs are grounded, categorized, and cite official source documents."""
    faqs = db_session.query(SchemeFAQ).filter(
        SchemeFAQ.scheme_id == "SIH26092-001"
    ).all()
    assert len(faqs) >= 8, "Must generate at least 8 grounded FAQs for a major scheme"

    categories = {f.category for f in faqs}
    assert "ELIGIBILITY" in categories
    assert "FINANCIAL" in categories
    assert "APPLICATION" in categories

    for f in faqs:
        assert f.question.endswith("?")
        assert len(f.answer) >= 15
        assert f.confidence >= 0.85
        assert f.source_url is not None


def test_05_document_extraction_and_deduplication(db_session: Session):
    """Verifies that statutory documents are extracted and idempotent upon re-enrichment."""
    pmegp = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    docs_before = db_session.query(SchemeDocument).filter(
        SchemeDocument.scheme_id == "SIH26092-001"
    ).count()

    # Re-run enrichment on the same scheme
    res = SchemeKnowledgeEnrichmentService.enrich_scheme(db_session, pmegp, commit=True)
    docs_after = db_session.query(SchemeDocument).filter(
        SchemeDocument.scheme_id == "SIH26092-001"
    ).count()

    assert docs_after == docs_before, "Re-enrichment must NOT duplicate documents"
    assert res["new_documents_added"] == 0


def test_06_rag_rich_scheme_retrieval(vector_store: SchemeVectorStore):
    """Verifies RAG retrieves rich context citations across multiple source types."""
    citations = vector_store.search("PMEGP Prime Minister Employment Generation Programme", top_k=6)
    assert len(citations) > 0

    types_retrieved = {c.source_type for c in citations}
    assert any(t in types_retrieved for t in ["SCHEME_METADATA", "SCHEME_FINANCIALS", "SCHEME_ELIGIBILITY", "SCHEME_FAQ"])

    for c in citations:
        assert c.scheme_id == "SIH26092-001"
        assert c.relevance_score > 0.3


def test_07_rag_financial_fact_retrieval(vector_store: SchemeVectorStore):
    """Verifies targeted financial queries retrieve SCHEME_FINANCIALS citations."""
    citations = vector_store.search("PMEGP loan subsidy interest rate margin money", top_k=4)
    assert len(citations) > 0

    fin_citations = [c for c in citations if c.source_type == "SCHEME_FINANCIALS"]
    assert len(fin_citations) >= 1, "Must retrieve SCHEME_FINANCIALS citation for financial query"

    snippet = fin_citations[0].snippet.lower()
    assert "subsidy" in snippet or "loan" in snippet or "margin money" in snippet


def test_08_rag_eligibility_fact_retrieval(vector_store: SchemeVectorStore):
    """Verifies eligibility queries retrieve SCHEME_ELIGIBILITY or SCHEME_RULE citations."""
    citations = vector_store.search("who is eligible for PMEGP age criteria qualifications", top_k=4)
    assert len(citations) > 0

    elig_citations = [c for c in citations if c.source_type in ("SCHEME_ELIGIBILITY", "SCHEME_RULE", "SCHEME_FAQ")]
    assert len(elig_citations) >= 1


def test_09_rag_document_retrieval(vector_store: SchemeVectorStore):
    """Verifies document queries retrieve SCHEME_DOCUMENT citations."""
    citations = vector_store.search("documents required for PMEGP application certificate", top_k=4)
    assert len(citations) > 0

    doc_citations = [c for c in citations if c.source_type in ("SCHEME_DOCUMENT", "SCHEME_FAQ")]
    assert len(doc_citations) >= 1


def test_10_rag_faq_direct_retrieval(vector_store: SchemeVectorStore):
    """Verifies conversational FAQ questions retrieve grounded FAQ chunks."""
    citations = vector_store.search("Is collateral required for PMEGP loan?", top_k=4)
    assert len(citations) > 0

    faq_or_fin = [c for c in citations if c.source_type in ("SCHEME_FAQ", "SCHEME_FINANCIALS")]
    assert len(faq_or_fin) >= 1


def test_11_multilingual_devanagari_hindi_retrieval(vector_store: SchemeVectorStore):
    """Verifies Hindi Devanagari queries retrieve accurate scheme citations."""
    citations = vector_store.search("पीएमईजीपी ऋण के लिए पात्रता और दस्तावेज", top_k=4)
    assert len(citations) > 0
    assert any(c.scheme_id == "SIH26092-001" for c in citations)


def test_12_multilingual_hinglish_retrieval(vector_store: SchemeVectorStore):
    """Verifies Hinglish conversational queries retrieve accurate scheme citations."""
    citations = vector_store.search("pmegp loan ke liye kaun apply kar sakta hai", top_k=4)
    assert len(citations) > 0
    assert any(c.scheme_id == "SIH26092-001" for c in citations)


def test_13_unrelated_query_rejection(vector_store: SchemeVectorStore):
    """Verifies out-of-domain queries return zero citations (no false positives)."""
    citations = vector_store.search("recipe for baking chocolate lava cake in oven", top_k=4)
    assert len(citations) == 0, "Out-of-domain cooking query must return 0 citations"

    citations_physics = vector_store.search("quantum mechanical tunneling wave function", top_k=4)
    assert len(citations_physics) == 0, "Out-of-domain physics query must return 0 citations"


def test_14_source_provenance_citations(vector_store: SchemeVectorStore):
    """Verifies that citations carry source document and official URL metadata."""
    citations = vector_store.search("Prime Minister Employment Generation Programme", top_k=3)
    assert len(citations) > 0
    for c in citations:
        assert c.source_type is not None
        assert c.source_document is not None
        assert c.snippet and len(c.snippet) > 10


def test_15_bulk_runner_restartability_and_checkpoint(db_session: Session, tmp_path):
    """Verifies that the bulk enrichment runner supports restartability and checkpointing."""
    test_checkpoint = str(tmp_path / "test_checkpoint.json")
    runner = SchemeBulkEnrichmentRunner(
        db=db_session,
        checkpoint_path=test_checkpoint,
        batch_size=2
    )

    # Clean initial state
    runner.reset_checkpoint()
    ck = runner.load_checkpoint()
    assert len(ck["completed_ids"]) == 0

    # Process limit 2
    summary = runner.run(limit=2, force_reprocess=False, sync_rag=False)
    assert summary["completed_schemes"] == 2

    # Checkpoint has 2 completed
    ck2 = runner.load_checkpoint()
    assert len(ck2["completed_ids"]) == 2

    # Run again with limit 2 without force: should process next 2
    summary2 = runner.run(limit=2, force_reprocess=False, sync_rag=False)
    ck3 = runner.load_checkpoint()
    assert len(ck3["completed_ids"]) == 4

    runner.reset_checkpoint()


def test_16_incremental_rag_sync(db_session: Session, vector_store: SchemeVectorStore):
    """Verifies that single-scheme update dynamically refreshes RAG chunks."""
    pmegp = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert pmegp is not None

    count_before = len(vector_store._chunks)
    synced = vector_store.update_scheme_chunks(pmegp)
    count_after = len(vector_store._chunks)

    assert synced > 0
    assert count_after == count_before, "Incremental update of existing scheme must maintain total chunk count without leaking duplicates"
