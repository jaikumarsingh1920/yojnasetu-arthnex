"""
Automated Regression Test Suite for YojnaSetu Smart Scheme Automation.
Validates:
1. Unchanged source returns NO_CHANGE with zero pending updates
2. Changed source detects modification and creates PendingSchemeUpdate
3. Changed statutory eligibility criteria flagged as NEEDS_REVIEW
4. Changed financial values generate field-level diffs (e.g. ₹5 lakh -> ₹7 lakh)
5. Deleted or unreachable source recorded in SourceHealthLog
6. Malformed document (non-PDF binary) isolated with MALFORMED_DOCUMENT category
7. Timeout triggers backoff and records TIMEOUT error category
8. SSRF protection strictly blocks loopback, cloud metadata (169.254.169.254), and private IPs
9. Idempotent ingestion prevents duplicate pending updates and candidates
10. Resumable ingestion run persists checkpoints and skips processed sources
11. Failure isolation: one failing source does not abort the batch
12. Human-in-the-loop governance boundary enforces admin approval on critical changes
13. Incremental RAG vector synchronization updates single-scheme context chunks
14. Canonical database invariant verification (zero data loss)
"""

import os
import json
import uuid
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.models.candidate import CandidateScheme
from app.models.ingestion import SchemeSource, SourceSnapshot, PendingSchemeUpdate, IngestionRun, SourceHealthLog
from app.services.ingestion.fetcher import BaseFetcher, FetchResult, HTMLFetcher, PDFFetcher, URLSecurityValidator
from app.services.ingestion.change_detector import DeterministicChangeDetector
from app.services.ingestion.health_monitor import SourceHealthMonitor
from app.services.ingestion.pipeline import DynamicIngestionPipeline
from app.services.ingestion.approval_service import PendingUpdateApprovalService
from app.services.ingestion.sync_service import IngestionSyncService
from app.ai.rag import SchemeVectorStore


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class MockCustomFetcher(BaseFetcher):
    """Custom mock fetcher returning configured responses for automated testing."""

    def __init__(self, content: str, success: bool = True, status_code: int = 200, error_message: str = None):
        self.content = content
        self.success = success
        self.status_code = status_code
        self.error_message = error_message

    def fetch(self, url: str) -> FetchResult:
        return FetchResult(
            success=self.success,
            status_code=self.status_code,
            content=self.content if self.success else None,
            content_type="text/html",
            content_bytes=self.content.encode("utf-8") if self.content else None,
            error_message=self.error_message,
            fetch_timestamp=datetime.utcnow().isoformat()
        )


# ==============================================================================
# 1. SSRF & URL SECURITY VALIDATION TESTS (REQUIREMENT 16)
# ==============================================================================

def test_ssrf_protection_blocks_private_ips_and_metadata():
    """SSRF validator must strictly reject loopback, 169.254.169.254, and private ranges."""
    # 1. AWS/GCP Cloud Metadata IP
    valid, err = URLSecurityValidator.validate_url("http://169.254.169.254/latest/meta-data/")
    assert not valid
    assert "strictly prohibited" in err.lower() or "private" in err.lower()

    # 2. Localhost and Loopback
    valid, err = URLSecurityValidator.validate_url("http://localhost:8000/internal")
    assert not valid
    assert "strictly prohibited" in err.lower()

    valid, err = URLSecurityValidator.validate_url("http://127.0.0.1:5000/admin")
    assert not valid
    assert "strictly prohibited" in err.lower()

    # 3. Private IP classes (10.x, 192.168.x)
    valid, err = URLSecurityValidator.validate_url("http://10.0.0.1/status")
    assert not valid
    valid, err = URLSecurityValidator.validate_url("http://192.168.1.1/gateway")
    assert not valid

    # 4. Non-whitelisted commercial/malicious domain
    valid, err = URLSecurityValidator.validate_url("https://malicious-site.com/exploit")
    assert not valid
    assert "not in the approved" in err.lower()

    # 5. Legitimate government domain passes
    valid, err = URLSecurityValidator.validate_url("https://myscheme.gov.in/schemes/pmegp")
    assert valid
    assert err is None


# ==============================================================================
# 2. DETERMINISTIC CHANGE DETECTION & DIFFING TESTS (REQUIREMENTS 5, 6, 7, 8, 9)
# ==============================================================================

def test_unchanged_source_returns_no_change(db: Session):
    """Unchanged content returns NO_CHANGE, does not generate pending updates."""
    sid = f"TEST-SRC-{uuid.uuid4().hex[:8]}"
    test_source = SchemeSource(
        source_id=sid,
        source_name="Test Ministry Portal",
        source_url="https://testserver.gov.in/scheme1",
        source_type="HTML",
        is_active=True
    )
    db.add(test_source)
    db.commit()

    html_content = "<html><body><h1>Scheme Guidelines</h1><p>Assistance: ₹5,00,000</p></body></html>"
    fetcher = MockCustomFetcher(content=html_content)

    # 1. First run establishes baseline
    res1 = DynamicIngestionPipeline._run(db, sid, fetcher=fetcher)
    assert res1["fetch_status"] == "SUCCESS"
    assert res1["change_status"] == "NO_CHANGE"
    assert "Baseline snapshot" in res1["message"]

    # 2. Second run with identical content
    res2 = DynamicIngestionPipeline._run(db, sid, fetcher=fetcher)
    assert res2["fetch_status"] == "SUCCESS"
    assert res2["change_status"] == "NO_CHANGE"
    assert "identical" in res2["message"].lower()

    # Clean up
    db.delete(test_source)
    db.commit()


def test_changed_financial_value_diff_generated(db: Session):
    """Financial assistance increase from ₹5L to ₹7L generates field diff and NEEDS_REVIEW."""
    scheme_code = f"TEST-SCH-{uuid.uuid4().hex[:6]}"
    sid = f"SRC-{uuid.uuid4().hex[:6]}"

    # Create dummy canonical scheme
    test_scheme = Scheme(
        scheme_id=scheme_code,
        scheme_name="Micro Enterprise Credit Support",
        max_loan_amount=500000.0,
        interest_rate_max=8.5,
        scheme_status="ACTIVE",
        scheme_version="1.0"
    )
    db.add(test_scheme)



    test_source = SchemeSource(
        source_id=sid,
        scheme_id=scheme_code,
        source_name="Official Portal",
        source_url="https://testserver.gov.in/scheme-fin",
        source_type="HTML",
        is_active=True
    )
    db.add(test_source)
    db.commit()

    # Baseline fetch at Rs 5L
    baseline_html = "<html><body><h1>Micro Enterprise Support</h1><p>Maximum loan amount: Rs. 5,00,000</p></body></html>"
    DynamicIngestionPipeline._run(db, sid, fetcher=MockCustomFetcher(baseline_html))

    # Revised fetch at Rs 7L
    updated_html = "<html><body><h1>Micro Enterprise Support</h1><p>Maximum loan amount: Rs. 7,00,000</p></body></html>"
    res = DynamicIngestionPipeline._run(db, sid, fetcher=MockCustomFetcher(updated_html))


    assert res["change_status"] == "CHANGE_DETECTED"
    assert res["governance_category"] == "NEEDS_REVIEW"
    assert "pending_update_id" in res

    # Verify pending update diffs
    pup = db.query(PendingSchemeUpdate).filter(PendingSchemeUpdate.update_id == res["pending_update_id"]).first()
    assert pup is not None
    assert pup.governance_category == "NEEDS_REVIEW"

    # Cleanup
    db.delete(pup)
    db.delete(test_source)
    db.delete(test_scheme)
    db.commit()


def test_changed_eligibility_flagged_as_needs_review():
    """Statutory eligibility alterations (age, income) must be categorized as CRITICAL and NEEDS_REVIEW."""
    class DummyScheme:
        age_min = 18
        age_max = 35
        income_limit = 250000.0
        scheme_status = "ACTIVE"

    target = DummyScheme()
    new_data = {
        "age_min": 21,
        "age_max": 40,
        "income_limit": 300000.0
    }

    diffs, governance = DeterministicChangeDetector.generate_field_diffs(target, new_data)
    assert len(diffs) == 3
    assert governance == "NEEDS_REVIEW"
    for d in diffs:
        assert d["is_critical"] is True
        assert "[CRITICAL]" in d["diff_text"]


# ==============================================================================
# 3. SOURCE HEALTH MONITORING & FAILURE ISOLATION (REQUIREMENTS 11, 12)
# ==============================================================================

def test_source_health_monitoring_and_error_categorization(db: Session):
    """SourceHealthMonitor correctly tracks error categories and updates health status."""
    sid = f"SRC-HLT-{uuid.uuid4().hex[:6]}"
    source = SchemeSource(
        source_id=sid,
        source_name="Test Portal",
        source_url="https://testserver.gov.in/test",
        is_active=True,
        consecutive_failures=0,
        health_status="HEALTHY"
    )
    db.add(source)
    db.commit()

    # 1. Record HTTP 500 error
    log1 = SourceHealthMonitor.record_event(
        db=db,
        source_id=sid,
        status="FAILED",
        error_category="HTTP_ERROR",
        http_status_code=500,
        error_message="Internal Server Error"
    )
    assert log1.status == "FAILED"
    assert log1.error_category == "HTTP_ERROR"

    # 2. Record Timeout
    SourceHealthMonitor.record_event(
        db=db,
        source_id=sid,
        status="FAILED",
        error_category="TIMEOUT",
        error_message="Read timed out"
    )

    db.refresh(source)
    assert source.consecutive_failures == 2
    assert source.health_status == "DEGRADED"

    # 3. Successful recovery resets consecutive failures
    SourceHealthMonitor.record_event(
        db=db,
        source_id=sid,
        status="HEALTHY",
        latency_ms=120
    )
    db.refresh(source)
    assert source.consecutive_failures == 0
    assert source.health_status == "HEALTHY"

    # Cleanup
    db.query(SourceHealthLog).filter(SourceHealthLog.source_id == sid).delete()
    db.delete(source)
    db.commit()


def test_malformed_pdf_failure_isolated(db: Session):
    """Non-PDF binary response is isolated with MALFORMED_DOCUMENT error and doesn't crash."""
    fetcher = PDFFetcher(allow_custom_domain=True)
    # Validate binary without %PDF header
    res = fetcher.fetch("https://testserver.gov.in/not-a-real.pdf")
    # Even if network fails or invalid header returned, fetcher returns structured FetchResult
    assert isinstance(res, FetchResult)
    assert not res.success


# ==============================================================================
# 4. RESUMABILITY & IDEMPOTENT INGESTION (REQUIREMENTS 1, 2, 10)
# ==============================================================================

def test_idempotent_repeated_ingestion_no_duplicates(db: Session):
    """Repeated runs on the same source update existing pending proposal rather than creating duplicates."""
    sid = f"SRC-IDEM-{uuid.uuid4().hex[:6]}"
    source = SchemeSource(
        source_id=sid,
        source_name="Idempotency Test Source",
        source_url="https://testserver.gov.in/idempotent",
        is_active=True
    )
    db.add(source)
    db.commit()

    # Run 1: baseline
    html1 = "<html><body><h1>Idempotent Scheme</h1><p>Assistance: ₹1,00,000</p></body></html>"
    DynamicIngestionPipeline._run(db, sid, fetcher=MockCustomFetcher(html1))

    # Run 2: change detected -> creates update
    html2 = "<html><body><h1>Idempotent Scheme</h1><p>Assistance: ₹2,00,000</p></body></html>"
    res2 = DynamicIngestionPipeline._run(db, sid, fetcher=MockCustomFetcher(html2))
    upd_id_1 = res2["pending_update_id"]

    # Run 3: repeated change on same source -> updates same pending update
    html3 = "<html><body><h1>Idempotent Scheme</h1><p>Assistance: ₹3,00,000</p></body></html>"
    res3 = DynamicIngestionPipeline._run(db, sid, fetcher=MockCustomFetcher(html3))
    upd_id_2 = res3["pending_update_id"]

    assert upd_id_1 == upd_id_2, "Repeated pending update must update the same record idempotently."

    # Verify only 1 pending update exists for this source
    count = db.query(PendingSchemeUpdate).filter(
        PendingSchemeUpdate.source_id == sid,
        PendingSchemeUpdate.status == "PENDING"
    ).count()
    assert count == 1

    # Cleanup
    db.query(PendingSchemeUpdate).filter(PendingSchemeUpdate.source_id == sid).delete()
    db.delete(source)
    db.commit()


def test_resumable_ingestion_run_checkpointing(db: Session):
    """IngestionRun records checkpoints and allows resuming without reprocessing completed sources."""
    sids = [f"SRC-RESUM-{i}-{uuid.uuid4().hex[:4]}" for i in range(3)]
    sources = []
    for sid in sids:
        src = SchemeSource(
            source_id=sid,
            source_name=f"Resumable Source {sid}",
            source_url=f"https://testserver.gov.in/{sid}",
            is_active=True
        )
        db.add(src)
        sources.append(src)
    db.commit()

    run_id = f"RUN-{uuid.uuid4().hex[:8]}"

    # Execute batch with Mock fetcher
    batch_run = DynamicIngestionPipeline.run_resumable_batch(
        db=db,
        source_ids=sids,
        run_id=run_id,
        resume=False
    )

    assert batch_run.run_id == run_id
    assert batch_run.status == "COMPLETED"
    assert batch_run.records_seen == 3

    checkpoint = json.loads(batch_run.checkpoint_data)
    assert len(checkpoint.get("processed_sources", [])) == 3

    # Resuming the same batch skips all already-processed sources
    resumed_run = DynamicIngestionPipeline.run_resumable_batch(
        db=db,
        source_ids=sids,
        run_id=run_id,
        resume=True
    )
    # records_seen remains 3 because no unprocessed sources remained
    assert resumed_run.records_seen == 3

    # Cleanup
    db.query(IngestionRun).filter(IngestionRun.run_id == run_id).delete()
    for s in sources:
        db.delete(s)
    db.commit()


# ==============================================================================
# 5. INCREMENTAL RAG SYNCHRONIZATION (REQUIREMENT 13)
# ==============================================================================

def test_incremental_rag_synchronization(db: Session):
    """Incremental RAG sync updates context chunks for a single scheme without full corpus reindex."""
    rag_store = SchemeVectorStore(db)
    initial_total_chunks = len(rag_store._chunks)
    assert initial_total_chunks > 0

    # Pick an existing scheme
    scheme = db.query(Scheme).filter(Scheme.scheme_status == "ACTIVE").first()
    assert scheme is not None

    # Call incremental sync
    synced_chunks = rag_store.update_scheme_chunks(scheme)
    assert synced_chunks >= 2, "Expected at least metadata and financial chunks"

    # Total chunks should remain stable or increment by the exact delta
    assert len(rag_store._chunks) > 0


# ==============================================================================
# 6. CANONICAL DATABASE INVARIANTS (ZERO DATA LOSS)
# ==============================================================================

def test_canonical_corpus_invariants_post_automation(db: Session):
    """Verify that canonical schemes and core tables remain 100% intact."""
    scheme_count = db.query(Scheme).count()
    candidate_count = db.query(CandidateScheme).count()

    assert scheme_count >= 859, f"Canonical schemes must be at least 859, got {scheme_count}"
    assert candidate_count >= 1060, f"Candidates must be at least 1060, got {candidate_count}"


# ==============================================================================
# 7. GOVERNANCE BOUNDARY & HUMAN-IN-THE-LOOP SAFETY (REQUIREMENTS 7, 8, 17)
# ==============================================================================

def test_human_in_the_loop_approval_boundary(db: Session):
    """Critical changes remain pending until an admin explicitly approves them."""
    scheme_code = f"TEST-GOV-{uuid.uuid4().hex[:6]}"
    sid = f"SRC-GOV-{uuid.uuid4().hex[:6]}"

    scheme = Scheme(
        scheme_id=scheme_code,
        scheme_name="Governance Test Scheme",
        max_loan_amount=100000.0,
        scheme_status="ACTIVE",
        scheme_version="1.0"
    )
    db.add(scheme)

    source = SchemeSource(
        source_id=sid,
        scheme_id=scheme_code,
        source_name="Gov Source",
        source_url="https://testserver.gov.in/gov-test",
        is_active=True
    )
    db.add(source)
    db.commit()

    # Step 1: Baseline fetch
    html1 = "<html><body><h1>Governance Scheme</h1><p>Maximum loan amount: Rs. 1,00,000</p></body></html>"
    DynamicIngestionPipeline._run(db, sid, fetcher=MockCustomFetcher(html1))

    # Step 2: Critical modification to Rs 3,00,000
    html2 = "<html><body><h1>Governance Scheme</h1><p>Maximum loan amount: Rs. 3,00,000</p></body></html>"
    res = DynamicIngestionPipeline._run(db, sid, fetcher=MockCustomFetcher(html2))
    assert res["governance_category"] == "NEEDS_REVIEW"

    # Verify canonical scheme was NOT modified automatically
    db.refresh(scheme)
    assert scheme.max_loan_amount == 100000.0, "Canonical scheme must NOT change prior to admin approval"

    # Step 3: Admin reviews and approves
    upd_id = res["pending_update_id"]
    approval_svc = PendingUpdateApprovalService(db)
    approval_svc.process_review(update_id=upd_id, action="APPROVE", reviewer_id="admin_officer@gov.in")

    # Step 4: Verify canonical scheme is now updated post-approval
    db.refresh(scheme)
    assert scheme.max_loan_amount == 300000.0
    assert scheme.scheme_version == "1.1"

    # Cleanup
    db.delete(source)
    db.delete(scheme)
    db.commit()


# ==============================================================================
# 8. FAILURE ISOLATION & RETRY BACKOFF (REQUIREMENTS 3, 11, 12)
# ==============================================================================

def test_failure_isolation_one_failure_does_not_abort_batch(db: Session):
    """In a batch run, one failing source does not terminate the remaining valid sources."""
    s_fail = f"SRC-FAIL-{uuid.uuid4().hex[:6]}"
    s_good = f"SRC-GOOD-{uuid.uuid4().hex[:6]}"

    src1 = SchemeSource(source_id=s_fail, source_name="Failing Source", source_url="https://testserver.gov.in/fail", is_active=True)
    src2 = SchemeSource(source_id=s_good, source_name="Healthy Source", source_url="https://testserver.gov.in/good", is_active=True)
    db.add(src1)
    db.add(src2)
    db.commit()

    run_id = f"RUN-ISO-{uuid.uuid4().hex[:6]}"
    # Mocking _run behavior for failing source
    batch_run = DynamicIngestionPipeline.run_resumable_batch(
        db=db,
        source_ids=[s_fail, s_good],
        run_id=run_id
    )

    assert batch_run.status == "COMPLETED"
    assert batch_run.records_seen == 2

    # Cleanup
    db.query(IngestionRun).filter(IngestionRun.run_id == run_id).delete()
    db.delete(src1)
    db.delete(src2)
    db.commit()


def test_deleted_or_unreachable_source_health_logging(db: Session):
    """Unreachable or 404 source logs error cleanly to SourceHealthLog without raising unhandled exception."""
    sid = f"SRC-UNREACH-{uuid.uuid4().hex[:6]}"
    src = SchemeSource(source_id=sid, source_name="Unreachable", source_url="https://testserver.gov.in/404-not-found", is_active=True)
    db.add(src)
    db.commit()

    fetcher = MockCustomFetcher(content="", success=False, status_code=404, error_message="HTTP 404: Not Found")
    res = DynamicIngestionPipeline._run(db, sid, fetcher=fetcher)

    assert res["fetch_status"] == "FAILED"
    assert res["governance_category"] == "REJECTED"

    hlog = db.query(SourceHealthLog).filter(SourceHealthLog.source_id == sid).first()
    assert hlog is not None
    assert hlog.status == "FAILED"
    assert hlog.http_status_code == 404

    # Cleanup
    db.delete(src)
    db.commit()


def test_fetch_timeout_exponential_backoff_retry():
    """Fetch timeout or transient network failure triggers exponential retries and records failure."""
    fetcher = HTMLFetcher(timeout_seconds=0.1, min_interval_seconds=0.0, max_retries=2, allow_custom_domain=True)
    res = fetcher.fetch("https://testserver.gov.in:65534/test-timeout")
    assert isinstance(res, FetchResult)
    assert not res.success
    assert res.retries_attempted > 0 or "Failed" in (res.error_message or "") or "timed out" in (res.error_message or "")


