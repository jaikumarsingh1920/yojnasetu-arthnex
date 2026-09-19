"""
Regression tests verifying the historical test data cleanup:
- Confirms canonical scheme count baseline is 859 (001-859).
- Confirms test artifacts SIH26092-860 through 880 are absent from active tables.
- Confirms archived tables exist and preserve the removed test records.
- Confirms zero foreign key violations across all scheme-related child tables.
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
from app.models import Scheme, SchemeRule, SchemeDocument, CandidateScheme

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_canonical_scheme_count_baseline(db_session: Session):
    total_schemes = db_session.query(Scheme).count()
    assert total_schemes == 859, f"Expected 859 canonical schemes, got {total_schemes}"

def test_no_test_schemes_in_active_tables(db_session: Session):
    test_schemes = db_session.query(Scheme).filter(Scheme.scheme_id >= "SIH26092-860").all()
    assert len(test_schemes) == 0, f"Found {len(test_schemes)} unexpected test schemes >= 860"

def test_seed_and_discovered_schemes_preserved(db_session: Session):
    # Verify first and last seed scheme
    scheme_001 = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert scheme_001 is not None
    assert "Prime Minister" in scheme_001.scheme_name and "PMEGP" in scheme_001.scheme_name

    scheme_090 = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-090").first()
    assert scheme_090 is not None

    # Verify discovered schemes
    scheme_091 = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-091").first()
    assert scheme_091 is not None

    scheme_859 = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-859").first()
    assert scheme_859 is not None

def test_no_test_candidates_in_active_table(db_session: Session):
    test_cands = db_session.query(CandidateScheme).filter(CandidateScheme.candidate_id.like("CAND-TEST%")).all()
    assert len(test_cands) == 0, f"Found {len(test_cands)} active CAND-TEST candidates"

def test_archived_tables_preserve_provenance(db_session: Session):
    archived_schemes_cnt = db_session.execute(text("SELECT COUNT(*) FROM archived_test_schemes")).scalar()
    assert archived_schemes_cnt == 21, f"Expected 21 archived test schemes, got {archived_schemes_cnt}"

    archived_cands_cnt = db_session.execute(text("SELECT COUNT(*) FROM archived_test_candidate_schemes")).scalar()
    assert archived_cands_cnt == 31, f"Expected 31 archived test candidates, got {archived_cands_cnt}"

def test_scheme_child_tables_referential_integrity(db_session: Session):
    child_tables = [
        'scheme_rules', 'scheme_documents', 'scheme_sources',
        'scheme_verifications', 'scheme_changelogs', 'partner_scheme_mappings',
        'saved_schemes'
    ]
    for tbl in child_tables:
        fk_errors = db_session.execute(text(f"PRAGMA foreign_key_check({tbl})")).fetchall()
        assert len(fk_errors) == 0, f"Table {tbl} has {len(fk_errors)} FK errors"
