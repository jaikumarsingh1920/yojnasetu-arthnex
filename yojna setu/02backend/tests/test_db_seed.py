import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add 02backend and 04data to path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from app.models import Base, Scheme, SchemeVerification, SchemeRule, SchemeDocument, SchemeChangelog
from seed_db import seed_database, validate_csv_files


@pytest.fixture(scope="module")
def db_session():
    # Use in-memory or file-based sqlite session for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    seed_database(session)
    try:
        yield session
    finally:
        session.close()


def test_csv_validation():
    # Verify CSV pre-ingestion validation runs without throwing
    validate_csv_files()


def test_seed_database_counts_and_verification(db_session):
    # 1. Seed counts
    schemes_count = db_session.query(Scheme).count()
    rules_count = db_session.query(SchemeRule).count()
    docs_count = db_session.query(SchemeDocument).count()
    verifs_count = db_session.query(SchemeVerification).count()
    logs_count = db_session.query(SchemeChangelog).count()

    assert schemes_count >= 56, f"Expected at least 56 schemes, got {schemes_count}"
    assert rules_count >= 57, f"Expected at least 57 rules, got {rules_count}"
    assert docs_count >= 20, f"Expected at least 20 documents, got {docs_count}"
    assert verifs_count >= 56, f"Expected at least 56 verifications, got {verifs_count}"
    assert logs_count >= 212, f"Expected at least 212 changelogs, got {logs_count}"

    # 2. Verification status verification
    verified_schemes_count = db_session.query(SchemeVerification).filter(
        SchemeVerification.verification_status == "VERIFIED"
    ).count()
    assert verified_schemes_count >= 56, f"Expected at least 56 VERIFIED schemes, got {verified_schemes_count}"


def test_scheme_uniqueness_and_foreign_keys(db_session):
    scheme_ids = [s.scheme_id for s in db_session.query(Scheme.scheme_id).all()]
    assert len(scheme_ids) == len(set(scheme_ids)), "Duplicate scheme IDs detected"

    master_set = set(scheme_ids)

    # FK checks
    for r in db_session.query(SchemeRule).all():
        assert r.scheme_id in master_set, f"Rule {r.rule_id} references unmapped scheme {r.scheme_id}"

    for d in db_session.query(SchemeDocument).all():
        assert d.scheme_id in master_set, f"Document {d.document_id} references unmapped scheme {d.scheme_id}"

    for v in db_session.query(SchemeVerification).all():
        assert v.scheme_id in master_set, f"Verification {v.id} references unmapped scheme {v.scheme_id}"

    for c in db_session.query(SchemeChangelog).all():
        assert c.scheme_id in master_set, f"Changelog {c.id} references unmapped scheme {c.scheme_id}"


def test_sentinel_values_survival(db_session):
    # Verify UNKNOWN, NOT_APPLICABLE and CONDITIONAL survived ETL
    unknown_repay_scheme = db_session.query(Scheme).filter(Scheme.repayment_period_min_months_raw == "UNKNOWN").first()
    assert unknown_repay_scheme is not None, "Sentinel value UNKNOWN lost in repayment_period_min_months_raw"

    # Check raw sentinel fields
    unknown_income_scheme = db_session.query(Scheme).filter(Scheme.income_limit_raw == "UNKNOWN").first()
    assert unknown_income_scheme is not None, "Sentinel UNKNOWN lost in income_limit_raw"

    conditional_moratorium_scheme = db_session.query(Scheme).filter(Scheme.moratorium_min_months_raw == "CONDITIONAL").first()
    assert conditional_moratorium_scheme is not None, "Sentinel CONDITIONAL lost in moratorium_min_months_raw"

    not_app_grant_scheme = db_session.query(Scheme).filter(Scheme.grant_amount_raw == "NOT_APPLICABLE").first()
    assert not_app_grant_scheme is not None, "Sentinel NOT_APPLICABLE lost in grant_amount_raw"


def test_seed_idempotency(db_session):
    count_before = db_session.query(Scheme).count()
    rules_before = db_session.query(SchemeRule).count()
    docs_before = db_session.query(SchemeDocument).count()
    verifs_before = db_session.query(SchemeVerification).count()

    # Run seed script a second time
    seed_database(db_session)

    # Verify counts did NOT double
    assert db_session.query(Scheme).count() == count_before
    assert db_session.query(SchemeRule).count() == rules_before
    assert db_session.query(SchemeDocument).count() == docs_before
    assert db_session.query(SchemeVerification).count() == verifs_before
