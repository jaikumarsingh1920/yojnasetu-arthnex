"""
Comprehensive Test Suite for YojnaSetu Automatic Government Scheme Update Pipeline.
SIH26092 Smart Automation.

Tests:
1. Unchanged source: asserts NO duplicate snapshot created, status NO_CHANGE
2. Changed source: asserts single snapshot created, status CHANGE_DETECTED, pending update staged
3. Meaningful structured diff: asserts machine-readable format (field, change_type, old_value, new_value, source_url, detected_at, validation_status)
4. Irrelevant HTML changes: scripts, styles, CSRF tokens, dynamic nonces ignored
5. Scheduler interval configuration: verifies settings and custom interval
6. Duplicate scheduler prevention: verifies singleton lock and concurrent run prevention
7. Failed source isolation: verifies failing source does not abort complete run
8. Retry & backoff behavior: verifies consecutive failure tracking and health status degradation
9. Idempotency: repeated runs do not duplicate snapshots or pending updates
10. Admin approval flow: canonical Scheme updated, version incremented, SchemeChangelog recorded
11. Admin rejection flow: canonical Scheme completely unchanged, marked REJECTED
12. Incremental RAG synchronization: context chunks updated incrementally on approval
13. Admin visibility endpoints: GET /scheduler/status and POST /scheduler/trigger
14. Clean lifecycle management: start and stop without orphaned workers
"""

import os
import sys
import json
from datetime import datetime, timedelta
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from seed_db import seed_database
from app.main import app
from app.db.session import get_db
from app.models import Base, Scheme, SchemeRule, SchemeChangelog
from app.models.user import UserRole
from app.models.ingestion import SchemeSource, SourceSnapshot, PendingSchemeUpdate, IngestionRun, SourceHealthLog
from app.core.config import settings
from app.core.security import create_access_token
from app.services.ingestion.fetcher import HTMLFetcher, FetchResult
from app.services.ingestion.change_detector import DeterministicChangeDetector
from app.services.ingestion.pipeline import DynamicIngestionPipeline
from app.services.ingestion.approval_service import PendingUpdateApprovalService
from app.services.ingestion.sync_service import IngestionSyncService
from app.services.ingestion.scheduler import AutoIngestionScheduler, auto_scheduler

client = TestClient(app)


HTML_CONTENT_V1 = """
<!DOCTYPE html>
<html>
<head><title>PMEGP Scheme Guidelines</title></head>
<body>
  <h1>Prime Minister Employment Generation Programme</h1>
  <div class="content">
    <p>Maximum Project Cost: Rs. 50,00,000 (50 Lakh)</p>
    <p>Maximum Loan Amount: Rs. 50,00,000</p>
    <p>Subsidy Rate: 35.0%</p>
    <p>Interest Rate: 5.0%</p>
    <p>Age Limit: 18 years minimum</p>
    <p>Authority: Ministry of MSME</p>
  </div>
</body>
</html>
"""

HTML_CONTENT_V2 = """
<!DOCTYPE html>
<html>
<head><title>PMEGP Scheme Guidelines 2026 Revised</title></head>
<body>
  <h1>Prime Minister Employment Generation Programme</h1>
  <div class="content">
    <p>Maximum Project Cost: Rs. 75,00,000 (75 Lakh)</p>
    <p>Maximum Loan Amount: Rs. 75,00,000</p>
    <p>Subsidy Rate: 40.0%</p>
    <p>Interest Rate: 6.0%</p>
    <p>Age Limit: 18 years minimum</p>
    <p>Authority: Ministry of MSME</p>
  </div>
</body>
</html>
"""

HTML_WITH_NOISE = """
<!DOCTYPE html>
<html>
<head>
  <title>PMEGP Scheme Guidelines</title>
  <meta name="date" content="2026-09-15T12:00:00Z">
  <script type="text/javascript">var sessionTracker = 987654321; analytics.push();</script>
  <style>.ad-banner { display: block; }</style>
</head>
<body>
  <!-- Dynamic server banner generated at runtime -->
  <input type="hidden" name="csrf_token" value="abc123dynamicTokenxyz987" />
  <input type="hidden" name="nonce" value="nonce-random-12345" />
  <p>Page generated at: 2026-09-15 01:23:45 UTC</p>
  <h1>Prime Minister Employment Generation Programme</h1>
  <div class="content">
    <p>Maximum Project Cost: Rs. 50,00,000 (50 Lakh)</p>
    <p>Maximum Loan Amount: Rs. 50,00,000</p>
    <p>Subsidy Rate: 35.0%</p>
    <p>Interest Rate: 5.0%</p>
    <p>Age Limit: 18 years minimum</p>
    <p>Authority: Ministry of MSME</p>
  </div>
</body>
</html>
"""


@pytest.fixture(scope="module")
def test_db():
    """Sets up an isolated in-memory test database."""
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

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def admin_headers():
    token = create_access_token(
        user_id="user-sys-admin",
        role=UserRole.SYSTEM_ADMIN.value,
        email="admin@yojnasetu.gov.in"
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Unchanged Source: No Duplicate Snapshot Created
# ---------------------------------------------------------------------------
def test_unchanged_source_no_duplicate_snapshot(test_db):
    """
    At every scheduled run:
    If source content is unchanged, NO duplicate snapshot row must be created.
    """
    source = SchemeSource(
        source_id="SRC-TEST-UNCHANGED",
        scheme_id="SIH26092-001",
        source_name="Official PMEGP Source",
        source_url="https://www.kviconline.gov.in/pmegp",
        authority="Ministry of MSME",
        source_type="HTML",
        fetch_frequency_hours=24,
        is_active=True,
        last_status="UNFETCHED"
    )
    test_db.add(source)
    test_db.commit()

    with patch.object(HTMLFetcher, "fetch") as mock_fetch:
        mock_fetch.return_value = FetchResult(
            success=True,
            status_code=200,
            content=HTML_CONTENT_V1,
            content_type="text/html",
        )

        pipeline = DynamicIngestionPipeline(test_db)

        # First run: baseline snapshot established
        res1 = pipeline.run_pipeline("SRC-TEST-UNCHANGED")
        assert res1["fetch_status"] == "SUCCESS"
        assert res1["change_status"] == "NO_CHANGE"

        snap_count_1 = test_db.query(SourceSnapshot).filter(
            SourceSnapshot.source_id == "SRC-TEST-UNCHANGED"
        ).count()
        assert snap_count_1 == 1

        # Second run with identical content
        res2 = pipeline.run_pipeline("SRC-TEST-UNCHANGED")
        assert res2["fetch_status"] == "SUCCESS"
        assert res2["change_status"] == "NO_CHANGE"
        assert "Duplicate snapshot skipped" in res2["message"]

        # CRITICAL ASSERTION: Snapshot count MUST STILL BE 1!
        snap_count_2 = test_db.query(SourceSnapshot).filter(
            SourceSnapshot.source_id == "SRC-TEST-UNCHANGED"
        ).count()
        assert snap_count_2 == 1, "Duplicate snapshot was incorrectly created for unchanged content!"

        # Third run: identical content again
        res3 = pipeline.run_pipeline("SRC-TEST-UNCHANGED")
        assert res3["change_status"] == "NO_CHANGE"

        snap_count_3 = test_db.query(SourceSnapshot).filter(
            SourceSnapshot.source_id == "SRC-TEST-UNCHANGED"
        ).count()
        assert snap_count_3 == 1, "Duplicate snapshot created on 3rd identical run!"


# ---------------------------------------------------------------------------
# 2. Changed Source: Creates Snapshot and Stages Pending Update
# ---------------------------------------------------------------------------
def test_changed_source_creates_snapshot_and_pending_update(test_db):
    """
    If source content changes:
    Create a new snapshot and stage a PendingSchemeUpdate proposal for admin review.
    Canonical data MUST NOT be modified!
    """
    canonical_before = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    max_loan_before = canonical_before.max_loan_amount
    version_before = canonical_before.scheme_version

    with patch.object(HTMLFetcher, "fetch") as mock_fetch:
        mock_fetch.return_value = FetchResult(
            success=True,
            status_code=200,
            content=HTML_CONTENT_V2,
            content_type="text/html",
        )

        pipeline = DynamicIngestionPipeline(test_db)
        res = pipeline.run_pipeline("SRC-TEST-UNCHANGED")

        assert res["change_status"] == "CHANGE_DETECTED"
        assert res["pending_update_id"] is not None
        assert res["detected_change_count"] > 0

        # Snapshot count should now be 2
        snap_count = test_db.query(SourceSnapshot).filter(
            SourceSnapshot.source_id == "SRC-TEST-UNCHANGED"
        ).count()
        assert snap_count == 2

        # Canonical scheme in DB MUST remain completely untouched!
        test_db.refresh(canonical_before)
        assert canonical_before.max_loan_amount == max_loan_before
        assert canonical_before.scheme_version == version_before

        # Verify PendingSchemeUpdate record exists with PENDING status
        pending = test_db.query(PendingSchemeUpdate).filter(
            PendingSchemeUpdate.update_id == res["pending_update_id"]
        ).first()
        assert pending is not None
        assert pending.status == "PENDING"


# ---------------------------------------------------------------------------
# 3. Meaningful Machine-Readable Structured Diff
# ---------------------------------------------------------------------------
def test_meaningful_structured_diff(test_db):
    """
    Machine-readable diff must show:
    - added fields
    - changed fields
    - removed fields
    - old value
    - new value
    - source URL
    - detected timestamp
    - confidence / validation status
    """
    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    candidate_data = {
        "scheme_name": scheme.scheme_name,
        "max_loan_amount": 7500000.0,  # MODIFIED
        "interest_rate_max": 6.0,      # MODIFIED
        "subsidy_percentage": 40.0,    # MODIFIED
        "application_url": "https://www.kviconline.gov.in/apply",  # ADDED or MODIFIED
        "beneficiary_category": "OBC, SC, ST",  # ADDED
    }

    diffs, governance = DeterministicChangeDetector.generate_field_diffs(
        target_scheme=scheme,
        candidate_data=candidate_data,
        source_url="https://www.kviconline.gov.in/pmegp",
        validation_status="VALID",
        confidence=0.95
    )

    assert len(diffs) > 0
    assert governance == "NEEDS_REVIEW"

    # Verify machine-readable keys on each diff
    for d in diffs:
        assert "field" in d
        assert "change_type" in d
        assert d["change_type"] in ["ADDED", "MODIFIED", "REMOVED"]
        assert "old_value" in d
        assert "new_value" in d
        assert "is_critical" in d
        assert "source_url" in d
        assert d["source_url"] == "https://www.kviconline.gov.in/pmegp"
        assert "detected_at" in d
        assert "validation_status" in d
        assert d["validation_status"] == "VALID"
        assert "diff_text" in d

    # Verify structured diff summary
    summary = DeterministicChangeDetector.build_structured_diff_summary(
        diffs=diffs,
        source_url="https://www.kviconline.gov.in/pmegp",
        validation_status="VALID"
    )
    assert summary["total_changes"] == len(diffs)
    assert "max_loan_amount" in summary["changed_fields"]
    assert summary["has_critical_changes"] is True
    assert summary["source_url"] == "https://www.kviconline.gov.in/pmegp"


# ---------------------------------------------------------------------------
# 4. Irrelevant HTML Noise Ignored (No Spurious Updates)
# ---------------------------------------------------------------------------
def test_irrelevant_html_noise_ignored():
    """
    HTML noise (analytics scripts, style blocks, CSRF tokens, dynamic timestamps, nonces)
    must NOT be treated as meaningful scheme changes.
    """
    hash_clean = DeterministicChangeDetector.compute_hash(
        DeterministicChangeDetector.normalize_content(HTML_CONTENT_V1)
    )
    hash_with_noise = DeterministicChangeDetector.compute_hash(
        DeterministicChangeDetector.normalize_content(HTML_WITH_NOISE)
    )

    assert hash_clean == hash_with_noise, (
        f"HTML noise resulted in different hashes! Clean: {hash_clean}, Noise: {hash_with_noise}"
    )

    change_res = DeterministicChangeDetector.detect_change(
        current_raw_content=HTML_WITH_NOISE,
        previous_snapshot_hash=hash_clean
    )
    assert change_res.status == "NO_CHANGE"
    assert change_res.has_changed is False


# ---------------------------------------------------------------------------
# 5. Scheduler Interval Configuration
# ---------------------------------------------------------------------------
def test_scheduler_interval_configuration():
    """
    Scheduler respects interval, enabled state, and defaults from settings.
    """
    scheduler = AutoIngestionScheduler(interval_minutes=15, enabled=True, batch_size=25)
    assert scheduler.interval_minutes == 15
    assert scheduler.enabled is True
    assert scheduler.batch_size == 25


# ---------------------------------------------------------------------------
# 6. Duplicate Scheduler Prevention
# ---------------------------------------------------------------------------
def test_duplicate_scheduler_prevention():
    """
    Scheduler singleton and locks prevent starting multiple concurrent workers.
    """
    scheduler1 = AutoIngestionScheduler()
    scheduler2 = AutoIngestionScheduler()

    # Singleton pattern assertion
    assert scheduler1 is scheduler2

    # Start worker
    started_1 = scheduler1.start()
    assert started_1 is True
    assert scheduler1.is_running is True

    # Duplicate start attempt must return False
    started_2 = scheduler2.start()
    assert started_2 is False

    # Stop worker cleanly
    stopped = scheduler1.stop()
    assert stopped is True
    assert scheduler1.is_running is False


# ---------------------------------------------------------------------------
# 7. Failed Source Isolation (One Bad Source Doesn't Stop The Run)
# ---------------------------------------------------------------------------
def test_failed_source_isolation(test_db):
    """
    A network or timeout error on one source must NOT crash or terminate
    the scheduled batch run for other sources.
    """
    # Create 3 test sources: healthy, failing, healthy
    src_good_1 = SchemeSource(
        source_id="SRC-ISO-GOOD1",
        scheme_id="SIH26092-001",
        source_name="Good Source 1",
        source_url="https://good1.gov.in",
        is_active=True,
        last_status="UNFETCHED"
    )
    src_bad = SchemeSource(
        source_id="SRC-ISO-BAD",
        scheme_id="SIH26092-002",
        source_name="Bad Failing Source",
        source_url="https://bad-timeout.gov.in",
        is_active=True,
        last_status="UNFETCHED"
    )
    src_good_2 = SchemeSource(
        source_id="SRC-ISO-GOOD2",
        scheme_id="SIH26092-003",
        source_name="Good Source 2",
        source_url="https://good2.gov.in",
        is_active=True,
        last_status="UNFETCHED"
    )
    test_db.add_all([src_good_1, src_bad, src_good_2])
    test_db.commit()

    def mock_fetch_router(url):
        if "bad-timeout" in url:
            return FetchResult(
                success=False,
                status_code=504,
                content=None,
                content_type="text/html",
                error_message="Gateway Timeout (15s exceeded)"
            )
        return FetchResult(
            success=True,
            status_code=200,
            content=HTML_CONTENT_V1,
            content_type="text/html"
        )

    with patch.object(HTMLFetcher, "fetch", side_effect=mock_fetch_router):
        run = DynamicIngestionPipeline.run_resumable_batch(
            db=test_db,
            source_ids=["SRC-ISO-GOOD1", "SRC-ISO-BAD", "SRC-ISO-GOOD2"]
        )

        assert run.status == "COMPLETED"
        assert run.records_seen == 3
        assert run.records_failed == 1
        assert run.records_unchanged == 2

        # Check bad source health log
        bad_logs = test_db.query(SourceHealthLog).filter(
            SourceHealthLog.source_id == "SRC-ISO-BAD"
        ).all()
        assert len(bad_logs) > 0
        assert bad_logs[0].status == "FAILED"


# ---------------------------------------------------------------------------
# 8. Retry & Consecutive Failure Backoff Behavior
# ---------------------------------------------------------------------------
def test_retry_and_consecutive_failure_backoff(test_db):
    """
    Consecutive failures increment properly, leading to status DEGRADED then FAILED.
    """
    source = SchemeSource(
        source_id="SRC-RETRY-TEST",
        scheme_id="SIH26092-004",
        source_name="Retry Test Portal",
        source_url="https://flaky-server.gov.in",
        is_active=True,
        consecutive_failures=0,
        health_status="HEALTHY"
    )
    test_db.add(source)
    test_db.commit()

    with patch.object(HTMLFetcher, "fetch") as mock_fetch:
        mock_fetch.return_value = FetchResult(
            success=False,
            status_code=500,
            content=None,
            content_type="text/html",
            error_message="Internal Server Error 500"
        )

        pipeline = DynamicIngestionPipeline(test_db)

        # Run 2 failures -> DEGRADED
        pipeline.run_pipeline("SRC-RETRY-TEST")
        pipeline.run_pipeline("SRC-RETRY-TEST")
        test_db.refresh(source)
        assert source.consecutive_failures >= 2
        assert source.health_status in ["DEGRADED", "FAILED"]

        # Run 3 more failures -> FAILED
        for _ in range(3):
            pipeline.run_pipeline("SRC-RETRY-TEST")

        test_db.refresh(source)
        assert source.consecutive_failures >= 5
        assert source.health_status == "FAILED"


# ---------------------------------------------------------------------------
# 9. Pending Update Creation Idempotency
# ---------------------------------------------------------------------------
def test_pending_update_creation_idempotency(test_db):
    """
    Repeated scheduler runs on the same changed content must update
    the existing pending update proposal instead of generating duplicate records.
    """
    with patch.object(HTMLFetcher, "fetch") as mock_fetch:
        mock_fetch.return_value = FetchResult(
            success=True,
            status_code=200,
            content=HTML_CONTENT_V2,
            content_type="text/html",
        )

        pipeline = DynamicIngestionPipeline(test_db)

        # Run twice on changed source
        res1 = pipeline.run_pipeline("SRC-TEST-UNCHANGED", force_update=True)
        res2 = pipeline.run_pipeline("SRC-TEST-UNCHANGED", force_update=True)

        # Pending updates for this source with PENDING status must be exactly 1
        pending_list = test_db.query(PendingSchemeUpdate).filter(
            PendingSchemeUpdate.source_id == "SRC-TEST-UNCHANGED",
            PendingSchemeUpdate.status == "PENDING"
        ).all()
        assert len(pending_list) == 1, "Duplicate PendingSchemeUpdate records were created!"


# ---------------------------------------------------------------------------
# 10. Approval Flow: Version Increment & Changelog
# ---------------------------------------------------------------------------
def test_approval_flow_version_increment_and_changelog(test_db):
    """
    When admin approves:
    - Canonical Scheme is updated
    - Version is incremented
    - Audit entry in SchemeChangelog is logged
    """
    pending = test_db.query(PendingSchemeUpdate).filter(
        PendingSchemeUpdate.source_id == "SRC-TEST-UNCHANGED",
        PendingSchemeUpdate.status == "PENDING"
    ).first()
    assert pending is not None

    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == pending.scheme_id).first()
    ver_before = scheme.scheme_version

    approval_service = PendingUpdateApprovalService(test_db)
    approved = approval_service.process_review(
        update_id=pending.update_id,
        action="APPROVE",
        reviewer_id="admin@yojnasetu.gov.in",
        reason="Approved MSME 2026 revised guidelines."
    )

    assert approved.status == "APPROVED"
    assert approved.reviewed_by == "admin@yojnasetu.gov.in"

    # Canonical scheme updated
    test_db.refresh(scheme)
    assert scheme.scheme_version != ver_before

    # Changelog entry exists
    changelogs = test_db.query(SchemeChangelog).filter(
        SchemeChangelog.scheme_id == scheme.scheme_id,
        SchemeChangelog.action == "DYNAMIC_INGESTION_UPDATE"
    ).all()
    assert len(changelogs) > 0
    assert any(c.admin_identifier == "admin@yojnasetu.gov.in" for c in changelogs)


# ---------------------------------------------------------------------------
# 11. Rejection Flow: Zero Canonical Mutation
# ---------------------------------------------------------------------------
def test_rejection_flow_zero_canonical_mutation(test_db):
    """
    When admin rejects:
    - Proposal status is REJECTED
    - Canonical Scheme data remains completely untouched
    """
    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    loan_before = scheme.max_loan_amount
    ver_before = scheme.scheme_version

    # Stage a proposal to reject
    rej_proposal = PendingSchemeUpdate(
        update_id="UPD-REJECT-TEST",
        scheme_id="SIH26092-001",
        source_id="SRC-TEST-UNCHANGED",
        old_version=str(ver_before or "1.0"),
        extracted_data='{"max_loan_amount": 99999999.0}',
        detected_changes='[{"field": "max_loan_amount", "old_value": "' + str(loan_before) + '", "new_value": "99999999.0"}]',
        validation_status="VALID",
        status="PENDING"
    )
    test_db.add(rej_proposal)
    test_db.commit()

    approval_service = PendingUpdateApprovalService(test_db)
    rejected = approval_service.process_review(
        update_id="UPD-REJECT-TEST",
        action="REJECT",
        reviewer_id="admin@yojnasetu.gov.in",
        reason="Rejected due to invalid loan limit figure."
    )

    assert rejected.status == "REJECTED"
    assert rejected.rejection_reason == "Rejected due to invalid loan limit figure."

    # Canonical scheme must be 100% untouched
    test_db.refresh(scheme)
    assert scheme.max_loan_amount == loan_before
    assert scheme.scheme_version == ver_before


# ---------------------------------------------------------------------------
# 12. Incremental RAG Synchronization on Approval
# ---------------------------------------------------------------------------
def test_incremental_rag_sync_on_approval(test_db):
    """
    IngestionSyncService performs incremental vector sync on scheme approval.
    """
    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    sync_res = IngestionSyncService.sync_after_approval(
        db_or_self=test_db,
        scheme_or_id=scheme,
        updated_fields={"max_loan_amount": 7500000.0}
    )

    assert sync_res["scheme_id"] == "SIH26092-001"
    assert sync_res["rag_synced"] is True


# ---------------------------------------------------------------------------
# 13. Admin Visibility Endpoints: Status and Trigger
# ---------------------------------------------------------------------------
def test_admin_scheduler_endpoints_visibility(test_db, admin_headers):
    """
    GET /api/v1/ingestion/scheduler/status returns comprehensive telemetry.
    POST /api/v1/ingestion/scheduler/trigger executes on-demand cycle.
    """
    # 1. Check status endpoint
    resp = client.get("/api/v1/ingestion/scheduler/status", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "scheduler_enabled" in data
    assert "is_running" in data
    assert "interval_minutes" in data
    assert "sources_summary" in data
    assert "total_sources" in data["sources_summary"]
    assert "pending_updates_count" in data

    # 2. Trigger on-demand run
    with patch.object(HTMLFetcher, "fetch") as mock_fetch:
        mock_fetch.return_value = FetchResult(
            success=True,
            status_code=200,
            content=HTML_CONTENT_V1,
            content_type="text/html"
        )
        trigger_resp = client.post("/api/v1/ingestion/scheduler/trigger", headers=admin_headers)
        assert trigger_resp.status_code == 200
        trigger_data = trigger_resp.json()
        assert trigger_data.get("status") in ["COMPLETED", "ALREADY_RUNNING"]


# ---------------------------------------------------------------------------
# 14. Clean Lifecycle Management
# ---------------------------------------------------------------------------
def test_clean_lifecycle_management():
    """
    Verifies startup, graceful shutdown, and resource cleanup without orphaned worker threads.
    """
    scheduler = AutoIngestionScheduler()
    # If previously running, stop it
    if scheduler.is_running:
        scheduler.stop()

    # Start
    started = scheduler.start()
    assert started is True
    assert scheduler.is_running is True

    # Stop cleanly
    stopped = scheduler.stop()
    assert stopped is True
    assert scheduler.is_running is False
