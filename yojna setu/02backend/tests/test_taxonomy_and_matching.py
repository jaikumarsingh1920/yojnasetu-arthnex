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

from app.models import Base
from app.db.session import get_db
from seed_db import seed_database
from app.models.scheme import Scheme
from app.schemas.profile import BeneficiaryProfileInput
from app.engine.taxonomy import TaxonomyMatcher, SECTORS, ACTIVITY_ALIASES, OCCUPATION_MAP
from app.engine.normalization import SchemeNormalizedProfileBuilder
from app.engine.recommendation import DeterministicRecommendationEngine
from app.engine.data_quality_report import DataQualityAuditReport


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


def test_geography_normalization():
    assert TaxonomyMatcher.normalize_geography("UP") == "UTTAR_PRADESH"
    assert TaxonomyMatcher.normalize_geography("U.P.") == "UTTAR_PRADESH"
    assert TaxonomyMatcher.normalize_geography("Uttar Pradesh") == "UTTAR_PRADESH"
    assert TaxonomyMatcher.normalize_geography("NCT Delhi") == "DELHI"
    assert TaxonomyMatcher.normalize_geography("PAN India") == "ALL_INDIA"
    assert TaxonomyMatcher.normalize_geography("UNKNOWN") == "UNKNOWN_GEOGRAPHY"


def test_tailoring_stitching_synonym_matching():
    status, score_factor, explanation = TaxonomyMatcher.match_sector_or_activity(
        user_input="tailoring and stitching shop",
        scheme_sectors=["TEXTILES", "TAILORING"],
        scheme_activities=["STITCHING", "GARMENT_MAKING"],
        scheme_aliases=["tailoring", "sewing", "garment stitching"]
    )
    assert status == "MATCH"
    assert score_factor >= 0.9
    assert "tailoring" in explanation.lower() or "stitching" in explanation.lower()


def test_dairy_milk_production_matching():
    status, score_factor, explanation = TaxonomyMatcher.match_sector_or_activity(
        user_input="milk business and dairy farming",
        scheme_sectors=["DAIRY", "ANIMAL_HUSBANDRY"],
        scheme_activities=["MILK_PRODUCTION"],
        scheme_aliases=["dairy farming", "milk production"]
    )
    assert status == "MATCH"
    assert score_factor >= 0.9


def test_artisan_craftsperson_target_group_matching():
    status, score_factor, explanation = TaxonomyMatcher.match_target_group(
        user_category="ARTISAN",
        user_is_sc=False,
        scheme_target_groups=["ARTISAN", "VISHWAKARMA"]
    )
    assert status == "MATCH"
    assert score_factor == 1.0


def test_sc_target_group_normalization():
    status, score_factor, explanation = TaxonomyMatcher.match_target_group(
        user_category="SC",
        user_is_sc=True,
        scheme_target_groups=["SCHEDULED_CASTE"]
    )
    assert status == "MATCH"
    assert score_factor == 1.0


def test_parent_child_sector_matching():
    # Scheme is ANIMAL_HUSBANDRY, user input is DAIRY (a child of ANIMAL_HUSBANDRY)
    status, score_factor, explanation = TaxonomyMatcher.match_sector_or_activity(
        user_input="dairy",
        scheme_sectors=["ANIMAL_HUSBANDRY"],
        scheme_activities=["LIVESTOCK"],
        scheme_aliases=[]
    )
    assert status == "MATCH"
    assert score_factor >= 0.8


def test_partial_semantic_matching():
    # Related industry/activity match
    status, score_factor, explanation = TaxonomyMatcher.match_sector_or_activity(
        user_input="micro enterprise",
        scheme_sectors=["MSME", "SMALL_BUSINESS"],
        scheme_activities=["SMALL_MICRO_BUSINESS"],
        scheme_aliases=["small business"]
    )
    assert status in ("MATCH", "PARTIAL_MATCH")
    assert score_factor > 0.0


def test_genuine_mismatch():
    status, score_factor, explanation = TaxonomyMatcher.match_sector_or_activity(
        user_input="IT consultancy software",
        scheme_sectors=["DAIRY"],
        scheme_activities=["MILK_PRODUCTION"],
        scheme_aliases=["dairy"]
    )
    assert status == "MISMATCH"
    assert score_factor == 0.0


def test_scheme_normalized_profile_builder(db: Session):
    nsfdc_mfs = db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-052").first()
    assert nsfdc_mfs is not None

    norm = SchemeNormalizedProfileBuilder.build_profile(nsfdc_mfs)
    assert "MICRO_FINANCE" in norm.normalized_sectors or "MICRO_ENTERPRISE" in norm.normalized_sectors
    assert len(norm.normalized_activity_aliases) > 0
    assert len(norm.semantic_tags) > 0
    assert norm.financial_requirement_category in ["LOW_LOAN_REQUIREMENT", "MEDIUM_LOAN_REQUIREMENT", "HIGH_LOAN_REQUIREMENT"]


def test_data_quality_audit_report(db: Session):
    report = DataQualityAuditReport.generate_report(db)
    assert report["total_schemes_evaluated"] == 56
    assert report["totals"]["total_aliases"] > 0
    assert report["totals"]["total_semantic_tags"] > 0
    assert report["totals"]["total_normalized_sectors"] > 0
    assert len(report["scheme_summaries"]) > 0


def test_soft_fit_recommendation_with_rich_normalization(db: Session):
    profile = BeneficiaryProfileInput(
        age=28,
        annual_income=180000,
        social_category="SC",
        is_sc=True,
        gender="FEMALE",
        state="UTTAR_PRADESH",
        sector="TAILORING",
        activity_type="STITCHING",
        project_cost=100000,
        requested_loan_amount=90000
    )

    nsfdc_mfs = db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-052").first()
    assert nsfdc_mfs is not None

    from app.engine.eligibility import DeterministicEligibilityEngine
    elig_res = DeterministicEligibilityEngine.evaluate_scheme(nsfdc_mfs, profile)
    score, matched, unmatched, not_eval, rec_reasons, breakdown = DeterministicRecommendationEngine.evaluate_soft_fit(
        nsfdc_mfs, profile, elig_res
    )

    assert score > 70.0
    assert "sector_match" in matched or "target_group_match" in matched
    assert len(breakdown) == 7
