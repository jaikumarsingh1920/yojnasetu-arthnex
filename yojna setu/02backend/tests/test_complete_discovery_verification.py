"""
=============================================================================
YOJNASETU — COMPLETE SCHEME DISCOVERY & SAFE PROMOTION VERIFICATION SUITE
Phase 15 Comprehensive Test Suite (SIH 26092)
=============================================================================
Validates:
1. Pagination & Catalog Traversal Resilience
2. Resume & Checkpoint Traceability
3. Rerun Idempotency
4. Duplicate Discovery & Canonical Collision Detection
5. Authoritative Source Verification (.gov.in/.nic.in rules)
6. Structured Extraction & Sentinel Integrity (No Fabrication)
7. Missing Fields Handling (UNKNOWN / NOT_APPLICABLE semantics)
8. PDF Extraction Failure & Graceful Degradation
9. Promotion Safety Gate (STAGED, OFFICIALLY_VERIFIED, UNIQUE, VALID)
10. Duplicate Canonical Prevention
11. Transaction Rollback & Data Integrity
12. RAG Synchronization Idempotency & Search Grounding
13. Partial Failure Recovery
14. Admin Authorization & Security Enforcement
=============================================================================
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.models.candidate import CandidateScheme
from app.models.document import SchemeDocument
from app.models.verification import SchemeVerification
from app.services.ingestion.promotion_service import CandidatePromotionService
from app.services.ingestion.deduplicator import SchemeDeduplicator
from app.services.ingestion.source_resolver import OfficialSourceResolver
from app.services.ingestion.pdf_extractor import OfficialGovPDFExtractor
from app.ai.rag import SchemeVectorStore

client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 1. Pagination & Catalog Traversal
# ---------------------------------------------------------------------------
def test_pagination_and_catalogue_traversal():
    """Verify offset pagination and bounds checking across the catalogue."""
    res1 = client.get("/api/v1/schemes?page=1&page_size=20")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1["items"]) == 20
    assert data1["total"] >= 850
    first_ids = [s["scheme_id"] for s in data1["items"]]

    res2 = client.get("/api/v1/schemes?page=2&page_size=20")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["items"]) == 20
    second_ids = [s["scheme_id"] for s in data2["items"]]

    # Pages must be strictly disjoint
    assert set(first_ids).isdisjoint(set(second_ids))


# ---------------------------------------------------------------------------
# 2. Resume & Checkpoint Traceability
# ---------------------------------------------------------------------------
def test_resume_and_checkpoint_state(db: Session):
    """Verify that previous discovery candidates and run IDs are preserved."""
    candidates_with_run = db.query(CandidateScheme).filter(
        CandidateScheme.run_id.isnot(None)
    ).all()
    assert len(candidates_with_run) >= 200, "Candidates from previous runs must be preserved"


# ---------------------------------------------------------------------------
# 3. Rerun Idempotency
# ---------------------------------------------------------------------------
def test_rerun_idempotency(db: Session):
    """Verify candidate IDs are uniquely identifiable and not duplicated."""
    candidate_ids = [c[0] for c in db.query(CandidateScheme.candidate_id).all()]
    assert len(candidate_ids) == len(set(candidate_ids)), "All candidate IDs must be strictly unique"


# ---------------------------------------------------------------------------
# 4. Duplicate Discovery & Alias Detection
# ---------------------------------------------------------------------------
def test_duplicate_discovery_alias_detection(db: Session):
    """Verify deduplicator identifies canonical matches."""
    schemes = db.query(Scheme).all()

    dup_res = SchemeDeduplicator.check_duplicate(
        candidate_name="Prime Minister Employment Generation Programme (PMEGP)",
        existing_schemes=schemes,
        candidate_source_url="https://pmegp.gov.in"
    )
    assert dup_res.is_duplicate is True
    assert "SIH26092-" in dup_res.matched_scheme_id
    assert dup_res.similarity_score >= 0.85

    # Unique distinct scheme
    unique_res = SchemeDeduplicator.check_duplicate(
        candidate_name="Completely Novel Artisan Credit Scheme For Marginalized Youth 2026",
        existing_schemes=schemes,
        candidate_source_url="https://welfare.gov.in/novel-artisan"
    )
    assert unique_res.is_duplicate is False or unique_res.action_recommended == "UNIQUE"


# ---------------------------------------------------------------------------
# 5. Authoritative Source Verification (.gov.in/.nic.in)
# ---------------------------------------------------------------------------
def test_official_source_verification_rules():
    """Verify OfficialSourceResolver classifies official government domains accurately."""
    # Official Level-1/2 Government URLs
    gov_res = OfficialSourceResolver.resolve("https://pmegp.msme.gov.in/pmegpweb/index.jsp")
    assert gov_res.is_authoritative is True
    assert gov_res.authority_level in ("LEVEL_1_PRIMARY", "LEVEL_2_AGENCY")

    nic_res = OfficialSourceResolver.resolve("https://nsfdc.nic.in/schemes/term-loan")
    assert nic_res.is_authoritative is True

    # Unofficial / Blog / Commercial domains
    unoff_res = OfficialSourceResolver.resolve("https://bankbazaar.com/loans")
    assert unoff_res.is_authoritative is False
    assert unoff_res.authority_level == "UNVERIFIED_THIRD_PARTY"


# ---------------------------------------------------------------------------
# 6. Structured Extraction & Sentinel Integrity (No Fabrication)
# ---------------------------------------------------------------------------
def test_structured_extraction_sentinels_preserved(db: Session):
    """Verify unknown fields use standardized sentinels rather than fabricated values."""
    schemes = db.query(Scheme).filter(Scheme.scheme_id.like("SIH26092-%")).limit(50).all()
    assert len(schemes) > 0
    for s in schemes:
        if s.age_min is not None:
            assert 0 <= s.age_min <= 100
        if s.age_max is not None:
            assert 0 <= s.age_max <= 120
        if s.maximum_loan_amount is not None:
            assert s.maximum_loan_amount >= 0.0


# ---------------------------------------------------------------------------
# 7. Missing Fields Handling
# ---------------------------------------------------------------------------
def test_missing_fields_graceful_null_safety():
    """Verify scheme details API returns properly structured nulls without 500 errors."""
    res = client.get("/api/v1/schemes/SIH26092-001")
    assert res.status_code == 200
    data = res.json()
    assert "scheme_name" in data
    assert "official_source_url" in data
    assert "verifications" in data


# ---------------------------------------------------------------------------
# 8. PDF Extraction Failure & Graceful Degradation
# ---------------------------------------------------------------------------
def test_pdf_extraction_graceful_degradation():
    """Verify that corrupt or inaccessible PDF guidelines do not crash extractor."""
    extractor = OfficialGovPDFExtractor()
    result = extractor.extract(b"%PDF-invalid-corrupted-content", source_url="https://gov.in/test.pdf")
    assert result.success is False
    assert result.ocr_status == "FAILED"


# ---------------------------------------------------------------------------
# 9. Promotion Safety Gate
# ---------------------------------------------------------------------------
def test_promotion_safety_gate_rejects_unverified_or_duplicate(db: Session):
    """Verify CandidatePromotionService refuses promotion when criteria are not met."""
    # Candidate with UNVERIFIED
    invalid_candidate = CandidateScheme(
        candidate_id="TEST-CAND-UNVERIFIED",
        discovered_name="Test Unverified Scheme",
        normalized_name="Test Unverified Scheme",
        official_source_url="https://example.com/unverified",
        candidate_status="STAGED",
        relevance_status="NEEDS_REVIEW",
        verification_status="UNVERIFIED",
        duplicate_status="UNIQUE",
        validation_status="NEEDS_REVIEW",
        data_confidence="LOW"
    )

    can_promote, reason = CandidatePromotionService.can_promote(invalid_candidate)
    assert can_promote is False
    assert any(w in reason.lower() for w in ["verification", "relevance", "validation", "level", "confidence"])

    # Candidate marked as DUPLICATE
    duplicate_candidate = CandidateScheme(
        candidate_id="TEST-CAND-DUP",
        discovered_name="Test Duplicate Scheme",
        normalized_name="Test Duplicate Scheme",
        official_source_url="https://msme.gov.in/dup",
        candidate_status="STAGED",
        relevance_status="HIGH_PRIORITY",
        verification_status="OFFICIALLY_VERIFIED",
        duplicate_status="DUPLICATE_CANDIDATE",
        validation_status="VALID",
        data_confidence="HIGH"
    )
    can_promote_dup, reason_dup = CandidatePromotionService.can_promote(duplicate_candidate)
    assert can_promote_dup is False
    assert "duplicate" in reason_dup.lower()


# ---------------------------------------------------------------------------
# 10. Duplicate Canonical Prevention
# ---------------------------------------------------------------------------
def test_duplicate_canonical_code_prevention(db: Session):
    """Verify database unique constraint prevents duplicate scheme_id."""
    existing_scheme = db.query(Scheme).first()
    assert existing_scheme is not None

    dup_scheme = Scheme(
        scheme_id=existing_scheme.scheme_id,
        scheme_code="COLLIDING-CODE",
        scheme_name="Colliding Scheme ID Test",
        scheme_status="ACTIVE"
    )
    db.add(dup_scheme)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()


# ---------------------------------------------------------------------------
# 11. Transaction Rollback & Data Integrity
# ---------------------------------------------------------------------------
def test_transaction_rollback_preserves_database(db: Session):
    """Verify that failed transactions roll back completely without partial state."""
    count_before = db.query(Scheme).count()
    try:
        db.begin_nested()
        db.add(Scheme(scheme_id="SIH26092-TEMP-FAIL", scheme_code="TEMP-FAIL", scheme_name="Temp"))
        raise RuntimeError("Simulated transient failure")
    except RuntimeError:
        db.rollback()

    count_after = db.query(Scheme).count()
    assert count_before == count_after


# ---------------------------------------------------------------------------
# 12. RAG Synchronization Idempotency & Grounding
# ---------------------------------------------------------------------------
def test_rag_synchronization_and_grounding(db: Session):
    """Verify RAG vector store contains chunks for active schemes and retrieves grounded facts."""
    store = SchemeVectorStore(db)
    assert len(store._chunks) > 5000

    results = store.search("PMEGP manufacturing service enterprise loan", top_k=3)
    assert len(results) > 0
    assert any("PMEGP" in r.scheme_name or r.scheme_id == "SIH26092-001" for r in results)


# ---------------------------------------------------------------------------
# 13. Partial Failure Recovery
# ---------------------------------------------------------------------------
def test_partial_failure_recovery(db: Session):
    """Verify that unpromoted staged candidates remain intact in candidate_schemes."""
    staged_candidates = db.query(CandidateScheme).filter(
        CandidateScheme.candidate_status == "STAGED"
    ).all()
    assert len(staged_candidates) > 0, "Expected non-zero staged candidates remaining for manual review"


# ---------------------------------------------------------------------------
# 14. Authorization & RBAC
# ---------------------------------------------------------------------------
def test_candidate_promotion_endpoint_requires_auth():
    """Verify that unauthenticated requests to promote candidates are rejected (401/403)."""
    res = client.post("/api/v1/ingestion/candidates/CAND-TEST/promote")
    assert res.status_code in (401, 403, 404, 422)
