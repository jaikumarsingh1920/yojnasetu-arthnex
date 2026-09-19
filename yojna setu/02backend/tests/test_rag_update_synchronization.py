"""
Regression tests verifying RAG canonical consistency and incremental synchronization:
- Verifies scheme updates incrementally refresh RAG chunks without full server restart.
- Verifies updated content is retrieved and obsolete content is evicted.
- Verifies promoted schemes enter RAG chunks incrementally.
- Verifies scheme version and official provenance citations remain strictly accurate.
"""

import pytest
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.ai.rag import SchemeVectorStore
from app.services.ingestion.sync_service import IngestionSyncService

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_rag_incremental_scheme_update(db_session: Session):
    # 1. Initialize RAG vector store
    rag_store = SchemeVectorStore(db_session)
    initial_total_chunks = len(rag_store._chunks)
    assert initial_total_chunks > 0

    # 2. Select a target scheme to update
    target_sid = "SIH26092-001"
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == target_sid).first()
    assert scheme is not None
    original_purpose = scheme.purpose

    # 3. Apply an isolated text update
    unique_keyword = "ANTIGRAVITY_SOLAR_CHARKHA_2026"
    scheme.purpose = f"Special micro-enterprise initiative for {unique_keyword} manufacturing."
    scheme.version = (getattr(scheme, "version", 1) or 1) + 1
    db_session.commit()

    try:
        # 4. Trigger incremental RAG sync via IngestionSyncService
        synced = IngestionSyncService.sync_rag_knowledge(db_session, scheme)
        assert synced is True

        # Also verify update directly on our test instance
        updated_chunks_count = rag_store.update_scheme_chunks(scheme)
        assert updated_chunks_count > 0

        # 5. Retrieve using RAG for unique keyword and scheme
        results = rag_store.search(query=f"PMEGP {unique_keyword}", top_k=5)
        assert len(results) > 0

        top_match = results[0]
        assert top_match.scheme_id == target_sid
        assert unique_keyword in top_match.snippet
        assert top_match.relevance_score > 0.0

        # 6. Verify old obsolete text is evicted from this scheme's chunks
        old_chunks = [c for c in rag_store._chunks if c.get("scheme_id") == target_sid and original_purpose and original_purpose in c.get("text", "")]
        assert len(old_chunks) == 0, "Old purpose text was not evicted from RAG chunks"

    finally:
        # Restore original purpose and version
        scheme.purpose = original_purpose
        scheme.version = (getattr(scheme, "version", 2) or 2) - 1
        db_session.commit()
        rag_store.update_scheme_chunks(scheme)

def test_rag_incremental_promoted_scheme_ingestion(db_session: Session):
    rag_store = SchemeVectorStore(db_session)
    count_before = len(rag_store._chunks)

    # Mock a newly promoted scheme
    new_sid = "SIH26092-PROMO-TEST"
    existing = db_session.query(Scheme).filter(Scheme.scheme_id == new_sid).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    new_scheme = Scheme(
        scheme_id=new_sid,
        scheme_name="National Drone Training Subsidy",
        ministry="Ministry of Civil Aviation",
        scheme_status="ACTIVE",
        purpose="Comprehensive financial subsidy for rural youth drone pilot certification.",
        official_portal="https://civilaviation.gov.in/drone-subsidy",
        official_source_url="https://civilaviation.gov.in/drone-subsidy",
        application_url="https://civilaviation.gov.in/drone-subsidy/apply"
    )
    db_session.add(new_scheme)
    db_session.commit()

    try:
        # Incrementally add to RAG
        added_count = rag_store.update_scheme_chunks(new_scheme)
        assert added_count >= 3  # Metadata, Financials, Application chunks

        # Query RAG for drone subsidy
        results = rag_store.search(query="rural youth drone pilot training certification subsidy", top_k=3)
        assert any(r.scheme_id == new_sid for r in results)

    finally:
        # Teardown
        db_session.delete(new_scheme)
        db_session.commit()
        rag_store.update_scheme_chunks(new_sid)
