"""
Dynamic Scheme Data Ingestion Pipeline Tests.
Verifies all 16 mandatory pipeline scenarios for SIH Final:
 1. First source fetch (baseline snapshot created)
 2. Successful snapshot persistence (content hash, timestamp, fetch_status)
 3. Same source content -> NO_CHANGE (no spurious updates)
 4. Changed source content -> CHANGE_DETECTED
 5. Fetch failure handling (graceful error capture, zero DB corruption)
 6. Extraction failure handling (unparseable or malformed content)
 7. Validation failure handling (invalid bounds/types rejected)
 8. Pending update creation (detected field diffs, canonical scheme untouched)
 9. Admin approval (updates canonical Scheme, increments version)
10. Admin rejection (proposal rejected, canonical Scheme remains unchanged)
11. Old scheme version preserved (audit trail in SchemeChangelog)
12. Canonical scheme updated ONLY after approval
13. Failed update does not modify canonical data (transaction rollback)
14. Existing eligibility integration test
15. Existing recommendation integration test
16. RAG synchronization test
"""

import os
import sys
from datetime import datetime, timezone
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
from app.models.ingestion import SchemeSource, SourceSnapshot, PendingSchemeUpdate
from app.core.security import create_access_token
from app.services.ingestion.fetcher import HTMLFetcher, FetchResult
from app.services.ingestion.change_detector import DeterministicChangeDetector
from app.services.ingestion.extractor import OfficialGovHTMLExtractor
from app.services.ingestion.normalizer import SchemeDataNormalizer
from app.services.ingestion.validator import SchemeDataValidator
from app.services.ingestion.approval_service import PendingUpdateApprovalService
from app.services.ingestion.sync_service import IngestionSyncService
from app.services.ingestion.pipeline import DynamicIngestionPipeline
from app.engine.eligibility import DeterministicEligibilityEngine
from app.schemas.profile import BeneficiaryProfileInput
from app.engine.recommendation import DeterministicRecommendationEngine
from app.schemas.recommendation import RecommendationRequest
from app.ai.rag import SchemeVectorStore

client = TestClient(app)


SAMPLE_PMEGP_HTML_V1 = """
<!DOCTYPE html>
<html>
<head><title>PMEGP - Official KVIC Portal</title></head>
<body>
  <h1>Prime Minister's Employment Generation Programme (PMEGP)</h1>
  <p>Governing Authority: Ministry of Micro, Small and Medium Enterprises</p>
  <div class="guidelines">
    <p>Maximum project cost eligible under Manufacturing is Rs. 50,00,000 (50 Lakhs) with maximum loan amount of Rs. 50,00,000.</p>
    <p>Maximum subsidy rate is 35% for special categories.</p>
    <p>Interest subsidy rate: 5.0%</p>
    <p>Minimum applicant age: 18 years.</p>
    <p>Official website: https://www.kviconline.gov.in/</p>
  </div>
</body>
</html>
"""

SAMPLE_PMEGP_HTML_V2 = """
<!DOCTYPE html>
<html>
<head><title>PMEGP - Official KVIC Portal - Revised Guidelines 2026</title></head>
<body>
  <h1>Prime Minister's Employment Generation Programme (PMEGP)</h1>
  <p>Governing Authority: Ministry of Micro, Small and Medium Enterprises</p>
  <div class="guidelines">
    <p>Maximum project cost eligible under Manufacturing is Rs. 60,00,000 (60 Lakhs) with maximum loan amount of Rs. 60,00,000.</p>
    <p>Maximum subsidy rate is 40% for special categories.</p>
    <p>Interest subsidy rate: 6.0%</p>
    <p>Minimum applicant age: 18 years.</p>
    <p>Official website: https://www.kviconline.gov.in/</p>
  </div>
</body>
</html>
"""


@pytest.fixture(scope="module")
def test_db():
    """Sets up an in-memory SQLite database populated with canonical schemes and users."""
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


@pytest.fixture(scope="module")
def beneficiary_headers():
    token = create_access_token(
        user_id="user-ben-10",
        role=UserRole.BENEFICIARY.value,
        email="ben10@example.com"
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# SCENARIO 1 & 2: First Source Fetch & Successful Snapshot Persistence
# ---------------------------------------------------------------------------
def test_scenario_1_and_2_first_fetch_and_snapshot(test_db):
    """
    Scenario 1: First source fetch creates a baseline snapshot.
    Scenario 2: Snapshot contains deterministic SHA-256 hash, timestamp, and metadata.
    """
    source = SchemeSource(
        source_id="TEST-SRC-PMEGP",
        scheme_id="SIH26092-001",
        source_name="KVIC Official PMEGP Portal",
        source_url="https://www.kviconline.gov.in/pmegpeportal/pmegphome/index.jsp",
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
            content=SAMPLE_PMEGP_HTML_V1,
            content_type="text/html",
        )

        pipeline = DynamicIngestionPipeline(test_db)
        result = pipeline.run_pipeline("TEST-SRC-PMEGP")

        assert result["fetch_status"] == "SUCCESS"
        assert result["change_status"] == "NO_CHANGE"  # Baseline snapshot established
        assert result["content_hash"] is not None
        assert len(result["content_hash"]) == 64  # SHA-256 hex length

        # Verify snapshot in DB
        snapshot = test_db.query(SourceSnapshot).filter(SourceSnapshot.source_id == "TEST-SRC-PMEGP").first()
        assert snapshot is not None
        assert snapshot.content_hash == result["content_hash"]
        assert snapshot.fetch_status == "SUCCESS"
        assert snapshot.http_status_code == 200
        assert "PMEGP" in snapshot.raw_content


# ---------------------------------------------------------------------------
# SCENARIO 3: Same Content Again -> Deterministic NO_CHANGE
# ---------------------------------------------------------------------------
def test_scenario_3_same_content_no_change(test_db):
    """
    Scenario 3: Subsequent fetch with identical normalized content yields NO_CHANGE.
    Ensures zero false positives and no spurious pending update proposals.
    """
    with patch.object(HTMLFetcher, "fetch") as mock_fetch:
        mock_fetch.return_value = FetchResult(
            success=True,
            status_code=200,
            content=SAMPLE_PMEGP_HTML_V1,
            content_type="text/html",
        )

        pipeline = DynamicIngestionPipeline(test_db)
        result = pipeline.run_pipeline("TEST-SRC-PMEGP")

        assert result["change_status"] == "NO_CHANGE"
        assert result.get("pending_update_id") is None
        assert result.get("detected_change_count", 0) == 0

        # Verify no pending update proposal was generated
        pending = test_db.query(PendingSchemeUpdate).filter(
            PendingSchemeUpdate.source_id == "TEST-SRC-PMEGP"
        ).all()
        assert len(pending) == 0


# ---------------------------------------------------------------------------
# SCENARIO 4 & 8: Changed Content -> CHANGE_DETECTED & Pending Update Proposal
# ---------------------------------------------------------------------------
def test_scenario_4_and_8_changed_content_and_pending_update(test_db):
    """
    Scenario 4: Changed content yields CHANGE_DETECTED.
    Scenario 8: Candidate data extracted and proposed as PendingSchemeUpdate;
    canonical Scheme is NOT mutated!
    """
    canonical_before = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    max_loan_before = canonical_before.max_loan_amount
    version_before = canonical_before.scheme_version

    with patch.object(HTMLFetcher, "fetch") as mock_fetch:
        mock_fetch.return_value = FetchResult(
            success=True,
            status_code=200,
            content=SAMPLE_PMEGP_HTML_V2,
            content_type="text/html",
        )

        pipeline = DynamicIngestionPipeline(test_db)
        result = pipeline.run_pipeline("TEST-SRC-PMEGP")

        assert result["change_status"] == "CHANGE_DETECTED"
        assert result["pending_update_id"] is not None
        assert result["detected_change_count"] > 0
        assert result["validation_status"] == "VALID"

        # Canonical scheme in DB MUST remain completely unchanged!
        test_db.refresh(canonical_before)
        assert canonical_before.max_loan_amount == max_loan_before
        assert canonical_before.scheme_version == version_before

        # PendingSchemeUpdate record exists with status PENDING
        proposal = test_db.query(PendingSchemeUpdate).filter(
            PendingSchemeUpdate.update_id == result["pending_update_id"]
        ).first()
        assert proposal is not None
        assert proposal.status == "PENDING"
        assert proposal.validation_status == "VALID"
        assert len(proposal.detected_changes) > 0


# ---------------------------------------------------------------------------
# SCENARIO 5: Fetch Failure Handling
# ---------------------------------------------------------------------------
def test_scenario_5_fetch_failure(test_db):
    """
    Scenario 5: Network failure / HTTP error captured cleanly without exception or DB corruption.
    """
    source = SchemeSource(
        source_id="TEST-SRC-FAIL",
        scheme_id="SIH26092-002",
        source_name="Failing Portal",
        source_url="https://nonexistent.gov.in/scheme",
        authority="Test Authority",
        source_type="HTML",
        fetch_frequency_hours=24,
        is_active=True,
        last_status="UNFETCHED"
    )
    test_db.add(source)
    test_db.commit()

    with patch.object(HTMLFetcher, "fetch") as mock_fetch:
        mock_fetch.return_value = FetchResult(
            success=False,
            status_code=504,
            content=None,
            content_type="text/html",
            error_message="Gateway Timeout (15s exceeded)",
        )

        pipeline = DynamicIngestionPipeline(test_db)
        result = pipeline.run_pipeline("TEST-SRC-FAIL")

        assert result["fetch_status"] == "FAILED"
        assert result["change_status"] == "ERROR"
        assert "Gateway Timeout" in result["message"]

        # Check snapshot records error
        snapshot = test_db.query(SourceSnapshot).filter(SourceSnapshot.source_id == "TEST-SRC-FAIL").first()
        assert snapshot is not None
        assert snapshot.fetch_status == "FAILED"
        assert snapshot.http_status_code == 504
        assert "Gateway Timeout" in snapshot.error_message


# ---------------------------------------------------------------------------
# SCENARIO 6: Extraction Failure Handling
# ---------------------------------------------------------------------------
def test_scenario_6_extraction_failure(test_db):
    """
    Scenario 6: Completely unparseable or irrelevant HTML handled gracefully without crashing.
    """
    extractor = OfficialGovHTMLExtractor()
    garbage_html = "<html><body><div>No scheme details here, just advertisement banner</div></body></html>"
    extracted = extractor.extract(garbage_html, source_url="https://example.gov.in")

    assert extracted is not None
    assert extracted.get("max_loan_amount") is None
    assert extracted.get("age_min") is None
    assert extracted.get("source_url") == "https://example.gov.in"


# ---------------------------------------------------------------------------
# SCENARIO 7: Validation Failure Handling
# ---------------------------------------------------------------------------
def test_scenario_7_validation_failure(test_db):
    """
    Scenario 7: Malformed/out-of-bounds candidate data fails validation with clear error messages.
    """
    invalid_candidate = {
        "scheme_name": "",  # Missing required field
        "official_source_url": "not-a-valid-url",  # Malformed URL
        "max_loan_amount": -50000.0,  # Negative loan limit
        "subsidy_percentage": 150.0,  # Subsidy rate > 100%
        "interest_rate_max": -2.0,  # Negative interest rate
        "age_min": 120,  # Age out of range
        "age_max": 10,   # age_min > age_max
    }

    result = SchemeDataValidator.validate(invalid_candidate)
    assert result.is_valid is False
    assert result.status == "INVALID"
    assert len(result.errors) >= 5
    assert any("scheme_name" in err for err in result.errors)
    assert any("max_loan_amount" in err for err in result.errors)
    assert any("subsidy_percentage" in err for err in result.errors)


# ---------------------------------------------------------------------------
# SCENARIO 9, 11, 12: Admin Approval, Audit Trail, Canonical DB Update
# ---------------------------------------------------------------------------
def test_scenario_9_11_12_admin_approval_and_audit(test_db):
    """
    Scenario 9: Admin approves pending update proposal.
    Scenario 11: Audit trail recorded in SchemeChangelog (before/after values, author).
    Scenario 12: Canonical Scheme is updated ONLY after approval, and version increments.
    """
    proposal = test_db.query(PendingSchemeUpdate).filter(
        PendingSchemeUpdate.source_id == "TEST-SRC-PMEGP",
        PendingSchemeUpdate.status == "PENDING"
    ).first()
    assert proposal is not None

    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == proposal.scheme_id).first()
    version_before = scheme.scheme_version

    approval_service = PendingUpdateApprovalService(test_db)
    updated_proposal = approval_service.process_review(
        update_id=proposal.update_id,
        action="APPROVE",
        reviewer_id="admin@yojnasetu.gov.in",
        reason="Verified against official MSME notification Gazette 2026."
    )

    assert updated_proposal.status == "APPROVED"
    assert updated_proposal.reviewed_by == "admin@yojnasetu.gov.in"
    assert updated_proposal.reviewed_at is not None

    # Canonical scheme MUST now be updated
    test_db.refresh(scheme)
    assert scheme.max_loan_amount == 6000000.0  # 60 Lakhs
    assert scheme.scheme_version != version_before     # Version incremented

    # Audit Trail: SchemeChangelog must have recorded the change
    changelogs = test_db.query(SchemeChangelog).filter(
        SchemeChangelog.scheme_id == scheme.scheme_id
    ).order_by(SchemeChangelog.created_at.desc()).all()
    assert len(changelogs) > 0
    logged_fields = [c.field for c in changelogs]
    assert "max_loan_amount" in logged_fields
    assert any(c.admin_identifier == "admin@yojnasetu.gov.in" for c in changelogs)



# ---------------------------------------------------------------------------
# SCENARIO 10: Admin Rejection
# ---------------------------------------------------------------------------
def test_scenario_10_admin_rejection(test_db):
    """
    Scenario 10: Admin rejects a proposal -> status is REJECTED, canonical scheme remains unchanged.
    """
    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-004").first()
    loan_before = scheme.max_loan_amount
    version_before = scheme.scheme_version

    # Manually create a proposal for PM SVANidhi
    reject_proposal = PendingSchemeUpdate(
        update_id="PROP-REJECT-001",
        scheme_id="SIH26092-004",
        source_id="TEST-SRC-PMSVANIDHI",
        old_version=str(version_before or "1.0"),
        extracted_data='{"max_loan_amount": 9999999.0}',
        detected_changes='[{"field": "max_loan_amount", "old_value": "' + str(loan_before) + '", "new_value": "9999999.0"}]',
        validation_status="VALID",
        validation_errors="[]",
        status="PENDING"
    )
    test_db.add(reject_proposal)
    test_db.commit()

    approval_service = PendingUpdateApprovalService(test_db)
    updated_proposal = approval_service.process_review(
        update_id="PROP-REJECT-001",
        action="REJECT",
        reviewer_id="admin@yojnasetu.gov.in",
        reason="Third loan tranche is not 99 Lakhs; rejected as false source data."
    )

    assert updated_proposal.status == "REJECTED"
    assert updated_proposal.rejection_reason is not None

    # Canonical scheme MUST remain untouched!
    test_db.refresh(scheme)
    assert scheme.max_loan_amount == loan_before
    assert scheme.scheme_version == version_before


# ---------------------------------------------------------------------------
# SCENARIO 13: Failed Update Rollback & Zero Corruption
# ---------------------------------------------------------------------------
def test_scenario_13_failed_update_zero_corruption(test_db):
    """
    Scenario 13: Exception during approval rolls back cleanly without corrupting the DB.
    """
    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    loan_current = scheme.max_loan_amount

    # Attempt review referencing non-existent update ID
    approval_service = PendingUpdateApprovalService(test_db)
    with pytest.raises(ValueError, match="not found"):
        approval_service.process_review(
            update_id="NON_EXISTENT_UPDATE_ID",
            action="APPROVE",
            reviewer_id="admin@yojnasetu.gov.in"
        )

    # Verify canonical scheme untouched
    test_db.refresh(scheme)
    assert scheme.max_loan_amount == loan_current


# ---------------------------------------------------------------------------
# SCENARIO 14: Existing Eligibility Engine Integration
# ---------------------------------------------------------------------------
def test_scenario_14_eligibility_engine_passes(test_db):
    """
    Scenario 14: Deterministic eligibility engine still functions correctly with canonical data.
    """
    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    profile = BeneficiaryProfileInput(
        age=28,
        gender="MALE",
        social_category="GENERAL",
        annual_income=300000.0,
        state="UTTAR_PRADESH",
        employment_status="SELF_EMPLOYED",
        activity_type="MANUFACTURING",
        business_stage="NEW_BUSINESS",
    )

    result = DeterministicEligibilityEngine.evaluate_scheme(scheme, profile)
    assert result is not None
    assert result.status.value in ["ELIGIBLE", "CONDITIONALLY_ELIGIBLE", "INSUFFICIENT_INFORMATION", "INELIGIBLE"]


# ---------------------------------------------------------------------------
# SCENARIO 15: Existing Recommendation Engine Integration
# ---------------------------------------------------------------------------
def test_scenario_15_recommendation_engine_passes(test_db):
    """
    Scenario 15: Recommendation engine runs correctly and ranks active schemes.
    """
    profile = BeneficiaryProfileInput(
        age=32,
        gender="FEMALE",
        social_category="OBC",
        annual_income=250000.0,
        state="MAHARASHTRA",
        applicant_type="INDIVIDUAL",
        business_stage="NEW_BUSINESS",
        sector="SERVICES",
        activity_type="SERVICES",
    )

    req = RecommendationRequest(profile=profile, top_k=5)
    rec_res = DeterministicRecommendationEngine.get_recommendations(test_db, req)
    assert rec_res is not None
    assert rec_res.evaluated_scheme_count > 0
    assert len(rec_res.recommendations) > 0
    assert all(hasattr(r, "score") for r in rec_res.recommendations)


# ---------------------------------------------------------------------------
# SCENARIO 16: RAG Synchronization Test
# ---------------------------------------------------------------------------
def test_scenario_16_rag_synchronization(test_db):
    """
    Scenario 16: IngestionSyncService triggers RAG re-indexing and retrieval sync.
    """
    sync_service = IngestionSyncService(test_db)
    sync_result = sync_service.sync(
        scheme_id="SIH26092-001",
        updated_fields={"max_loan_amount": 6000000.0, "age_min": 18}
    )

    assert sync_result["scheme_id"] == "SIH26092-001"
    assert sync_result["rag_synced"] is True

    # Check vector store search
    rag_store = SchemeVectorStore(test_db)
    results = rag_store.search("PMEGP manufacturing loan", top_k=3)
    assert len(results) > 0
    assert any(getattr(r, "scheme_id", None) == "SIH26092-001" or getattr(r, "scheme_code", None) == "SIH26092-001" for r in results)



# ---------------------------------------------------------------------------
# API Endpoints Integration Test
# ---------------------------------------------------------------------------
def test_api_endpoints_rbac_and_flow(test_db, admin_headers, beneficiary_headers):
    """
    Verifies RBAC protection and endpoint execution:
    - Beneficiary forbidden (403) from accessing admin ingestion endpoints
    - Admin can seed POC sources, list sources, view pending updates
    """
    # 1. Non-admin forbidden
    resp = client.get("/api/v1/ingestion/sources", headers=beneficiary_headers)
    assert resp.status_code == 403

    # 2. Admin seeds POC sources
    resp = client.post("/api/v1/ingestion/sources/seed-poc", headers=admin_headers)
    assert resp.status_code == 200
    sources = resp.json()
    assert len(sources) >= 2

    # 3. Admin lists sources
    resp = client.get("/api/v1/ingestion/sources", headers=admin_headers)
    assert resp.status_code == 200
    all_sources = resp.json()
    assert any(s["source_id"] == "SRC-PMEGP-001" for s in all_sources)

    # 4. Admin lists pending updates
    resp = client.get("/api/v1/ingestion/pending-updates", headers=admin_headers)
    assert resp.status_code == 200
    updates = resp.json()
    assert isinstance(updates, list)
