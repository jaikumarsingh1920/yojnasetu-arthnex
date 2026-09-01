"""
Unit tests verifying Data Enrichment, Rule Synchronization, and Scheme Verification status.
"""

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from app.models import Base, Scheme, SchemeVerification, SchemeRule, SchemeDocument
from app.db.session import get_db
from seed_db import seed_database
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.recommendation import RecommendationRequest
from app.schemas.financial import FinancialCalculationInput
from app.engine.recommendation import DeterministicRecommendationEngine
from app.engine import DeterministicFinancialEngine
from app.engine.normalization import SchemeNormalizedProfileBuilder


@pytest.fixture(scope="module")
def db():
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
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_all_56_schemes_verified(db: Session):
    """Verify schemes exist and have status VERIFIED."""
    schemes = db.query(Scheme).all()
    assert len(schemes) >= 56, f"Expected at least 56 schemes, found {len(schemes)}"

    verifications = db.query(SchemeVerification).all()
    assert len(verifications) >= 56, f"Expected at least 56 verifications, found {len(verifications)}"

    for v in verifications:
        assert v.verification_status == "VERIFIED", f"Scheme {v.scheme_id} verification status is {v.verification_status}"


def test_database_counts_exact(db: Session):
    """Verify count of rules and documents."""
    rules_cnt = db.query(SchemeRule).count()
    docs_cnt = db.query(SchemeDocument).count()
    assert rules_cnt >= 57, f"Expected at least 57 rules, found {rules_cnt}"
    assert docs_cnt >= 20, f"Expected at least 20 documents, found {docs_cnt}"


def test_rule_derived_and_conditional_values(db: Session):
    """Verify rule-derived numeric values and preservation of CONDITIONAL values."""
    # SIH26092-052: NSFDC Micro Finance Scheme (MFS) has max_loan_amount 125000
    mfs = db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-052").first()
    assert mfs is not None
    assert mfs.max_loan_amount == 125000.0

    # SIH26092-015: NBCFDC Individual Term Loan has CONDITIONAL interest rate & repayment
    nbcfdc = db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-015").first()
    assert nbcfdc is not None
    assert nbcfdc.interest_rate_min_raw == "CONDITIONAL" or nbcfdc.interest_rate_type == "CONDITIONAL"


def test_no_generic_description_used(db: Session):
    """Verify schemes have scheme-specific non-generic short descriptions."""
    schemes = db.query(Scheme).all()
    for s in schemes:
        assert s.short_description is not None
        assert s.short_description != "UNKNOWN"
        assert len(s.short_description) > 15
        assert "Promoting welfare, micro-enterprise growth" not in s.short_description


def test_normalized_matching_metadata(db: Session):
    """Verify normalized matching metadata is populated for all schemes."""
    schemes = db.query(Scheme).all()
    for s in schemes:
        norm_profile = SchemeNormalizedProfileBuilder.build_profile(s)
        assert len(norm_profile.normalized_sectors) > 0, f"Scheme {s.scheme_id} has empty normalized sectors"
        assert len(norm_profile.normalized_applicant_types) > 0, f"Scheme {s.scheme_id} has empty applicant types"
        assert len(norm_profile.normalized_target_groups) > 0, f"Scheme {s.scheme_id} has empty target groups"


def test_recommendation_and_financial_engines_work(db: Session):
    """Verify recommendation and financial calculation engines produce valid outputs."""
    profile = BeneficiaryProfileInput(
        age=28,
        annual_income=180000.0,
        social_category="SC",
        is_sc=True,
        gender="FEMALE",
        state="UTTAR_PRADESH",
        sector="MICRO_FINANCE",
        activity_type="SMALL_MICRO_BUSINESS",
        project_cost=100000.0,
        requested_loan_amount=90000.0
    )
    rec_req = RecommendationRequest(profile=profile, top_k=5)
    rec_res = DeterministicRecommendationEngine.get_recommendations(db, rec_req)

    assert rec_res.evaluated_scheme_count >= 56
    assert rec_res.eligible_scheme_count > 0
    assert len(rec_res.recommendations) > 0

    fin_req = FinancialCalculationInput(
        scheme_id="SIH26092-052",
        project_cost=100000.0,
        requested_loan_amount=90000.0
    )
    fin_res = DeterministicFinancialEngine.calculate(db, fin_req)
    assert fin_res.status == "CALCULATED"
    assert fin_res.eligible_loan_amount == 90000.0
