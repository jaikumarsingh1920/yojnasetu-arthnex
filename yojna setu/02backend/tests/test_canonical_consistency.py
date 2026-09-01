import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add 04data/scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "04data", "scripts"))
from seed_db import seed_database

from app.models import Scheme, SchemeRule, SchemeDocument, SchemeVerification, Partner, PartnerSchemeMapping, Base
from app.engine.calculator import DeterministicFinancialEngine
from app.schemas.financial import FinancialCalculationInput, FinancialCalculationStatus
from app.engine.eligibility import DeterministicEligibilityEngine
from app.schemas.eligibility import SchemeEligibilityStatus
from app.schemas.profile import BeneficiaryProfileInput
from app.ai.rag import SchemeVectorStore
from app.ai.agent import sanitize_user_facing_text
from app.services.admin_service import AdminService


@pytest.fixture(scope="module")
def db_session():
    """Sets up an in-memory SQLite database seeded with canonical data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    seed_database(session)

    yield session
    session.close()


def test_canonical_scheme_count_and_provenance(db_session):
    """Assert all 90 schemes exist and have 100% verified provenance records."""
    total_schemes = db_session.query(Scheme).count()
    assert total_schemes == 90, f"Expected 90 schemes, got {total_schemes}"

    verifications = db_session.query(SchemeVerification).count()
    assert verifications == 90, f"Expected 90 verification records, got {verifications}"

    for v in db_session.query(SchemeVerification).all():
        assert v.verification_status == "VERIFIED"
        assert v.data_confidence == "HIGH"


def test_credit_vs_non_credit_separation(db_session):
    """Assert non-credit schemes return NOT_APPLICABLE in calculator and have loan_available == 'NO'."""
    # Test non-credit schemes: e.g. SIH26092-008 (PM-DAKSH), SIH26092-010 (MSME ZED), SIH26092-050 (MSE-CDP)
    non_credit_ids = ["SIH26092-008", "SIH26092-010", "SIH26092-050"]
    for sid in non_credit_ids:
        scheme = db_session.query(Scheme).filter(Scheme.scheme_id == sid).first()
        assert scheme is not None, f"Scheme {sid} not found"
        assert scheme.loan_available == "NO", f"Scheme {sid} must have loan_available == 'NO'"
        assert scheme.is_credit_scheme is False, f"Scheme {sid} is_credit_scheme must be False"
        assert scheme.max_loan_amount is None or scheme.max_loan_amount == 0

        # Calculation engine check
        res = DeterministicFinancialEngine.calculate(db_session, FinancialCalculationInput(
            scheme_id=sid,
            project_cost=100000.0,
            requested_loan_amount=80000.0,
            annual_family_income=150000.0
        ))
        assert res.status == FinancialCalculationStatus.NOT_APPLICABLE
        assert any("Loan / EMI calculation is not applicable" in w for w in res.warnings)

    # Test credit schemes: e.g. SIH26092-001 (PMEGP), SIH26092-002 (PMMY)
    credit_ids = ["SIH26092-001", "SIH26092-002"]
    for sid in credit_ids:
        scheme = db_session.query(Scheme).filter(Scheme.scheme_id == sid).first()
        assert scheme is not None
        assert scheme.loan_available == "YES"
        assert scheme.is_credit_scheme is True


def test_no_fake_zero_interest_rate_defaults(db_session):
    """Credit schemes without fixed statutory interest rates must have interest_rate as None, not 0.0%."""
    # SIH26092-002 (PMMY) interest rate is set by individual lending banks as per RBI/Mudra guidelines
    mudra = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-002").first()
    assert mudra is not None
    assert mudra.interest_rate is None
    assert mudra.interest_rate_min is None


def test_document_requirements_derived_from_canonical_data(db_session):
    """Document guidance must come from statutory scheme_documents."""
    total_docs = db_session.query(SchemeDocument).count()
    assert total_docs >= 50

    s57_docs = db_session.query(SchemeDocument).filter(SchemeDocument.scheme_id == "SIH26092-057").all()
    assert len(s57_docs) >= 1
    doc_names = [d.document_name for d in s57_docs]
    assert any("Identity" in d or "Aadhaar" in d or "Caste" in d or "Income" in d or "Quotation" in d for d in doc_names)


def test_deterministic_eligibility_engine_consistency(db_session):
    """Assert deterministic eligibility returns strictly ELIGIBLE, INELIGIBLE, or INSUFFICIENT_INFORMATION."""
    # Profile: SC Female, 28 years, ₹1,80,000 income, UP
    profile = BeneficiaryProfileInput(
        age=28,
        gender="FEMALE",
        social_category="SC",
        annual_income=180000.0,
        state="UTTAR_PRADESH",
        loan_amount_requested=100000.0
    )

    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-057").first()
    rules = db_session.query(SchemeRule).filter(SchemeRule.scheme_id == "SIH26092-057", SchemeRule.active == True).all()

    # NSFDC Mahila Samriddhi Yojana (SIH26092-057) - requires SC Female, age 18-50, income <= 300000
    res = DeterministicEligibilityEngine.evaluate_scheme(scheme, profile, rules)
    assert res.status == SchemeEligibilityStatus.ELIGIBLE

    # Ineligible check: General Male against NSFDC MSY
    male_profile = BeneficiaryProfileInput(
        age=28,
        gender="MALE",
        social_category="GENERAL",
        annual_income=180000.0,
        state="UTTAR_PRADESH"
    )
    res_ineligible = DeterministicEligibilityEngine.evaluate_scheme(scheme, male_profile, rules)
    assert res_ineligible.status == SchemeEligibilityStatus.INELIGIBLE


def test_rag_dynamic_index_builder(db_session):
    """Assert RAG context store builds index directly from canonical SQLite database."""
    rag_store = SchemeVectorStore(db_session)
    assert len(rag_store._chunks) > 100

    # Search for PMEGP documents
    citations = rag_store.search("PMEGP project report documents", scheme_id="SIH26092-001")
    assert len(citations) > 0
    assert citations[0].scheme_id == "SIH26092-001"
    assert "PMEGP" in citations[0].scheme_name or "Prime Minister" in citations[0].scheme_name


def test_sanitization_removes_internal_technical_identifiers():
    """Assert text sanitizer removes RULE-XXXX, SQL, and internal fields."""
    raw_text = "Applicant must satisfy condition: Rule Code: RULE-0015; Field: annual_income <= 500000; Verification Status: VERIFIED"
    clean = sanitize_user_facing_text(raw_text)
    assert "RULE-0015" not in clean
    assert "Rule Code:" not in clean
    assert "Field:" not in clean
    assert "Verification Status:" not in clean


def test_completeness_scoring_does_not_penalize_non_credit_schemes(db_session):
    """Non-credit schemes with NOT_APPLICABLE fields must not be unfairly penalized."""
    pmmvy = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-020").first()
    res = AdminService.compute_scheme_completeness(pmmvy)
    assert res["not_applicable_count"] >= 1
    score = res["score"]
    assert score >= 50.0, f"Completeness score for PMMVY ({score}) should be computed fairly"
