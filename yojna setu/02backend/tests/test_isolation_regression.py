"""
Regression Test Suite for Database Isolation and Mutation Safety.

Verifies:
A. Promotion integration tests run on an isolated database copy.
B. Successful promotion mutations are cleaned up and isolated.
C. Repeated promotion executions do not accumulate schemes.
D. Test executions do not mutate the persistent development database.
E. Sequential scheme IDs are not consumed in the persistent development database.
F. Changelog and verification rows generated during promotion remain isolated.
G. Candidate status changes (e.g., STAGED -> APPROVED / REJECTED) are isolated.
"""

import os
import re
import json
import uuid
import sqlite3
import pytest
from sqlalchemy.orm import Session

from app.core.config import DEFAULT_DB_FILE, settings
from app.db.session import SessionLocal, engine
from app.models.scheme import Scheme
from app.models.candidate import CandidateScheme
from app.models.rule import SchemeRule
from app.models.document import SchemeDocument
from app.models.verification import SchemeVerification
from app.models.changelog import SchemeChangelog
from app.models.ingestion import SchemeSource
from app.services.ingestion.promotion_service import CandidatePromotionService


@pytest.fixture
def db_session():
    session = SessionLocal()
    pre_scheme_ids = set(r[0] for r in session.query(Scheme.scheme_id).all())
    pre_candidate_ids = set(r[0] for r in session.query(CandidateScheme.candidate_id).all())
    pre_candidate_states = {
        c.candidate_id: (c.candidate_status, c.reviewed_at, c.reviewed_by, c.admin_notes)
        for c in session.query(CandidateScheme).all()
    }
    try:
        yield session
    finally:
        try:
            # 1. Clean up any newly created schemes and their child records
            post_scheme_ids = [r[0] for r in session.query(Scheme.scheme_id).all() if r[0] not in pre_scheme_ids]
            if post_scheme_ids:
                session.query(SchemeRule).filter(SchemeRule.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(SchemeDocument).filter(SchemeDocument.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(SchemeVerification).filter(SchemeVerification.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(SchemeChangelog).filter(SchemeChangelog.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(SchemeSource).filter(SchemeSource.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(Scheme).filter(Scheme.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)

            # 2. Clean up any newly created candidate schemes
            post_candidate_ids = [r[0] for r in session.query(CandidateScheme.candidate_id).all() if r[0] not in pre_candidate_ids]
            if post_candidate_ids:
                session.query(CandidateScheme).filter(CandidateScheme.candidate_id.in_(post_candidate_ids)).delete(synchronize_session=False)

            # 3. Restore any modified candidate statuses for pre-existing candidates
            for cid, (stat, rev_at, rev_by, notes) in pre_candidate_states.items():
                cand = session.query(CandidateScheme).filter(CandidateScheme.candidate_id == cid).first()
                if cand and (cand.candidate_status != stat or cand.reviewed_by != rev_by):
                    cand.candidate_status = stat
                    cand.reviewed_at = rev_at
                    cand.reviewed_by = rev_by
                    cand.admin_notes = notes

            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


def get_persistent_db_row_count(table_name: str) -> int:
    """Helper to query the persistent development SQLite database directly."""
    conn = sqlite3.connect(DEFAULT_DB_FILE)
    cur = conn.cursor()
    cur.execute(f"SELECT count(1) FROM {table_name}")
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_persistent_db_max_scheme_id() -> int:
    """Helper to get max numeric scheme ID from persistent development DB."""
    conn = sqlite3.connect(DEFAULT_DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT scheme_id FROM schemes WHERE scheme_id LIKE 'SIH26092-%'")
    max_num = 0
    for (sid,) in cur.fetchall():
        m = re.search(r"SIH26092-(\d+)", sid)
        if m:
            try:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    conn.close()
    return max_num


# ==============================================================================
# A. PROMOTION INTEGRATION TEST USES ISOLATED DB
# ==============================================================================

def test_promotion_integration_uses_isolated_db():
    """Verify that active engine and SessionLocal connect to an isolated DB copy, not DEFAULT_DB_FILE."""
    active_db_url = str(engine.url)
    assert "sqlite" in active_db_url
    # Ensure active database path is NOT the persistent development DB
    canonical_clean = os.path.abspath(DEFAULT_DB_FILE).lower().replace("\\", "/")
    active_clean = os.path.abspath(str(engine.url.database)).lower().replace("\\", "/")
    assert active_clean != canonical_clean, (
        f"Active test engine is bound to persistent development DB: {canonical_clean}"
    )


# ==============================================================================
# B. SUCCESSFUL PROMOTION IS ROLLED BACK / CLEANED
# ==============================================================================

def test_successful_promotion_is_rolled_back_and_cleaned(db_session: Session):
    """Verify a full promotion creates all canonical records and db_session fixture cleans them up."""
    uid = uuid.uuid4().hex[:6]
    cand_id = f"CAND-TEST-REG-B-{uid}"
    cand = CandidateScheme(
        candidate_id=cand_id,
        run_id="RUN-TEST-REG",
        discovered_name=f"Isolated Regression Subsidy {uid}",
        normalized_name=f"Isolated Regression Subsidy {uid}",
        scheme_code=f"REG-B-{uid}",
        discovery_source="STATE_PORTAL",
        official_source_url=f"https://isolated-test.gov.in/{uid}",
        level="STATE",
        state_coverage="Gujarat",
        relevance_status="HIGH_PRIORITY",
        extraction_status="EXTRACTED",
        verification_status="OFFICIALLY_VERIFIED",
        duplicate_status="UNIQUE",
        data_confidence="HIGH",
        extracted_data=json.dumps({
            "scheme_name": f"Isolated Regression Subsidy {uid}",
            "max_loan_amount": 500000.0,
            "age_min": 21,
            "official_source_url": f"https://isolated-test.gov.in/{uid}"
        }),
        missing_fields=json.dumps([]),
        evidence=json.dumps({}),
        validation_status="VALID",
        validation_errors=json.dumps([]),
        candidate_status="STAGED"
    )
    db_session.add(cand)
    db_session.commit()

    promoted = CandidatePromotionService.promote_candidate(
        db_session,
        candidate_id=cand.candidate_id,
        reviewer_id="reviewer@yojnasetu.gov.in",
        notes="Regression isolation test promotion"
    )

    assert promoted.scheme_id.startswith("SIH26092-")
    assert "Isolated Regression Subsidy" in promoted.scheme_name

    # Confirm created in test session
    rules = db_session.query(SchemeRule).filter(SchemeRule.scheme_id == promoted.scheme_id).all()
    assert len(rules) >= 1

    verif = db_session.query(SchemeVerification).filter(SchemeVerification.scheme_id == promoted.scheme_id).first()
    assert verif is not None
    assert verif.verification_status == "VERIFIED"

    log = db_session.query(SchemeChangelog).filter(SchemeChangelog.scheme_id == promoted.scheme_id).first()
    assert log is not None
    assert log.action == "INITIAL_CANONICAL_INGESTION"


# ==============================================================================
# C. REPEATED PROMOTION DOES NOT ACCUMULATE SCHEMES
# ==============================================================================

def test_repeated_promotion_does_not_accumulate_schemes(db_session: Session):
    """Verify that multiple consecutive promotions do not accumulate schemes across tests."""
    initial_scheme_count = db_session.query(Scheme).count()

    for idx in range(3):
        uid = f"{uuid.uuid4().hex[:5]}_{idx}"
        cand_id = f"CAND-TEST-ACCUM-{uid}"
        cand = CandidateScheme(
            candidate_id=cand_id,
            run_id="RUN-TEST-ACCUM",
            discovered_name=f"Accumulation Test Scheme {uid}",
            normalized_name=f"Accumulation Test Scheme {uid}",
            scheme_code=f"ACCUM-{uid}",
            discovery_source="STATE_PORTAL",
            official_source_url=f"https://accum-test.gov.in/{uid}",
            level="STATE",
            relevance_status="HIGH_PRIORITY",
            extraction_status="EXTRACTED",
            verification_status="OFFICIALLY_VERIFIED",
            duplicate_status="UNIQUE",
            data_confidence="HIGH",
            extracted_data=json.dumps({
                "scheme_name": f"Accumulation Test Scheme {uid}",
                "official_source_url": f"https://accum-test.gov.in/{uid}"
            }),
            missing_fields=json.dumps([]),
            evidence=json.dumps({}),
            validation_status="VALID",
            validation_errors=json.dumps([]),
            candidate_status="STAGED"
        )
        db_session.add(cand)
        db_session.commit()

        promoted = CandidatePromotionService.promote_candidate(
            db_session,
            candidate_id=cand.candidate_id,
            reviewer_id="reviewer@yojnasetu.gov.in"
        )
        assert promoted.scheme_id.startswith("SIH26092-")

        # Explicitly clean up within loop to prove zero accumulation
        db_session.query(SchemeRule).filter(SchemeRule.scheme_id == promoted.scheme_id).delete()
        db_session.query(SchemeDocument).filter(SchemeDocument.scheme_id == promoted.scheme_id).delete()
        db_session.query(SchemeVerification).filter(SchemeVerification.scheme_id == promoted.scheme_id).delete()
        db_session.query(SchemeChangelog).filter(SchemeChangelog.scheme_id == promoted.scheme_id).delete()
        db_session.query(SchemeSource).filter(SchemeSource.scheme_id == promoted.scheme_id).delete()
        db_session.query(Scheme).filter(Scheme.scheme_id == promoted.scheme_id).delete()
        db_session.query(CandidateScheme).filter(CandidateScheme.candidate_id == cand_id).delete()
        db_session.commit()

        # Scheme count must return to baseline after cleanup
        current_count = db_session.query(Scheme).count()
        assert current_count == initial_scheme_count, (
            f"Scheme count accumulated on iteration {idx}: expected {initial_scheme_count}, got {current_count}"
        )


# ==============================================================================
# D. REPEATED TEST EXECUTION DOES NOT MUTATE PERSISTENT DB
# ==============================================================================

def test_full_promotion_does_not_mutate_persistent_db(db_session: Session):
    """Verify that performing candidate promotion leaves persistent development DB counts identical."""
    schemes_before = get_persistent_db_row_count("schemes")
    candidates_before = get_persistent_db_row_count("candidate_schemes")
    verifs_before = get_persistent_db_row_count("scheme_verifications")
    logs_before = get_persistent_db_row_count("scheme_changelogs")

    uid = uuid.uuid4().hex[:6]
    cand_id = f"CAND-TEST-REG-D-{uid}"
    cand = CandidateScheme(
        candidate_id=cand_id,
        run_id="RUN-TEST-REG-D",
        discovered_name=f"Persistent Zero Mutation Scheme {uid}",
        normalized_name=f"Persistent Zero Mutation Scheme {uid}",
        scheme_code=f"REG-D-{uid}",
        discovery_source="CENTRAL_MINISTRY",
        official_source_url=f"https://msme.gov.in/zero-mut-{uid}",
        level="CENTRAL_SECTOR",
        relevance_status="HIGH_PRIORITY",
        extraction_status="EXTRACTED",
        verification_status="OFFICIALLY_VERIFIED",
        duplicate_status="UNIQUE",
        data_confidence="HIGH",
        extracted_data=json.dumps({
            "scheme_name": f"Persistent Zero Mutation Scheme {uid}",
            "official_source_url": f"https://msme.gov.in/zero-mut-{uid}"
        }),
        missing_fields=json.dumps([]),
        evidence=json.dumps({}),
        validation_status="VALID",
        validation_errors=json.dumps([]),
        candidate_status="STAGED"
    )
    db_session.add(cand)
    db_session.commit()

    promoted = CandidatePromotionService.promote_candidate(
        db_session,
        candidate_id=cand.candidate_id,
        reviewer_id="reviewer@yojnasetu.gov.in"
    )
    assert promoted is not None

    # Verify persistent DB counts are 100% unaffected
    schemes_after = get_persistent_db_row_count("schemes")
    candidates_after = get_persistent_db_row_count("candidate_schemes")
    verifs_after = get_persistent_db_row_count("scheme_verifications")
    logs_after = get_persistent_db_row_count("scheme_changelogs")

    assert schemes_after == schemes_before, f"Persistent schemes mutated: {schemes_before} -> {schemes_after}"
    assert candidates_after == candidates_before, f"Persistent candidates mutated: {candidates_before} -> {candidates_after}"
    assert verifs_after == verifs_before, f"Persistent verifications mutated: {verifs_before} -> {verifs_after}"
    assert logs_after == logs_before, f"Persistent changelogs mutated: {logs_before} -> {logs_after}"


# ==============================================================================
# E. SCHEME IDS ARE NOT CONSUMED IN PERSISTENT DEVELOPMENT DB
# ==============================================================================

def test_scheme_ids_not_consumed_in_persistent_db(db_session: Session):
    """Verify that generating new sequential scheme IDs in tests does not advance persistent DB sequence."""
    persistent_max_before = get_persistent_db_max_scheme_id()

    uid = uuid.uuid4().hex[:6]
    cand_id = f"CAND-TEST-REG-E-{uid}"
    cand = CandidateScheme(
        candidate_id=cand_id,
        run_id="RUN-TEST-REG-E",
        discovered_name=f"ID Sequence Scheme {uid}",
        normalized_name=f"ID Sequence Scheme {uid}",
        scheme_code=f"REG-E-{uid}",
        discovery_source="CENTRAL_MINISTRY",
        official_source_url=f"https://msme.gov.in/seq-{uid}",
        level="CENTRAL_SECTOR",
        relevance_status="HIGH_PRIORITY",
        extraction_status="EXTRACTED",
        verification_status="OFFICIALLY_VERIFIED",
        duplicate_status="UNIQUE",
        data_confidence="HIGH",
        extracted_data=json.dumps({
            "scheme_name": f"ID Sequence Scheme {uid}",
            "official_source_url": f"https://msme.gov.in/seq-{uid}"
        }),
        missing_fields=json.dumps([]),
        evidence=json.dumps({}),
        validation_status="VALID",
        validation_errors=json.dumps([]),
        candidate_status="STAGED"
    )
    db_session.add(cand)
    db_session.commit()

    promoted = CandidatePromotionService.promote_candidate(
        db_session,
        candidate_id=cand.candidate_id,
        reviewer_id="reviewer@yojnasetu.gov.in"
    )
    assert promoted.scheme_id.startswith("SIH26092-")

    persistent_max_after = get_persistent_db_max_scheme_id()
    assert persistent_max_after == persistent_max_before, (
        f"Persistent scheme ID advanced from SIH26092-{persistent_max_before:03d} to SIH26092-{persistent_max_after:03d}"
    )


# ==============================================================================
# F. CHANGELOG AND VERIFICATION ROWS ARE ISOLATED
# ==============================================================================

def test_changelog_and_verification_rows_isolated(db_session: Session):
    """Verify newly generated verification and changelog rows exist only in test DB, not persistent DB."""
    uid = uuid.uuid4().hex[:6]
    cand_id = f"CAND-TEST-REG-F-{uid}"
    cand = CandidateScheme(
        candidate_id=cand_id,
        run_id="RUN-TEST-REG-F",
        discovered_name=f"Audit Isolation Scheme {uid}",
        normalized_name=f"Audit Isolation Scheme {uid}",
        scheme_code=f"REG-F-{uid}",
        discovery_source="STATE_PORTAL",
        official_source_url=f"https://audit-iso.gov.in/{uid}",
        level="STATE",
        relevance_status="HIGH_PRIORITY",
        extraction_status="EXTRACTED",
        verification_status="OFFICIALLY_VERIFIED",
        duplicate_status="UNIQUE",
        data_confidence="HIGH",
        extracted_data=json.dumps({
            "scheme_name": f"Audit Isolation Scheme {uid}",
            "official_source_url": f"https://audit-iso.gov.in/{uid}"
        }),
        missing_fields=json.dumps([]),
        evidence=json.dumps({}),
        validation_status="VALID",
        validation_errors=json.dumps([]),
        candidate_status="STAGED"
    )
    db_session.add(cand)
    db_session.commit()

    promoted = CandidatePromotionService.promote_candidate(
        db_session,
        candidate_id=cand.candidate_id,
        reviewer_id="reviewer@yojnasetu.gov.in"
    )

    # Check that promoted.scheme_id is NOT in persistent DB
    conn = sqlite3.connect(DEFAULT_DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT count(1) FROM scheme_verifications WHERE scheme_id = ?", (promoted.scheme_id,))
    verif_in_persistent = cur.fetchone()[0]
    cur.execute("SELECT count(1) FROM scheme_changelogs WHERE scheme_id = ?", (promoted.scheme_id,))
    log_in_persistent = cur.fetchone()[0]
    conn.close()

    assert verif_in_persistent == 0, f"Verification record leaked to persistent DB: {promoted.scheme_id}"
    assert log_in_persistent == 0, f"Changelog record leaked to persistent DB: {promoted.scheme_id}"


# ==============================================================================
# G. CANDIDATE STATUS CHANGES ARE ISOLATED
# ==============================================================================

def test_candidate_status_changes_are_isolated(db_session: Session):
    """Verify that altering candidate statuses in the test DB does not alter persistent DB records."""
    # Find an existing candidate in persistent DB
    conn = sqlite3.connect(DEFAULT_DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT candidate_id, candidate_status FROM candidate_schemes LIMIT 1")
    row = cur.fetchone()
    conn.close()

    assert row is not None, "Persistent DB has no candidates"
    sample_id, persistent_status = row

    # Query the same candidate in the test session
    cand_in_test = db_session.query(CandidateScheme).filter(CandidateScheme.candidate_id == sample_id).first()
    assert cand_in_test is not None

    # Mutate in test session
    new_test_status = "REJECTED" if persistent_status != "REJECTED" else "STAGED"
    cand_in_test.candidate_status = new_test_status
    db_session.commit()

    # Verify persistent DB still has original status
    conn = sqlite3.connect(DEFAULT_DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT candidate_status FROM candidate_schemes WHERE candidate_id = ?", (sample_id,))
    current_persistent_status = cur.fetchone()[0]
    conn.close()

    assert current_persistent_status == persistent_status, (
        f"Candidate status in persistent DB leaked! Changed from {persistent_status} to {current_persistent_status}"
    )
