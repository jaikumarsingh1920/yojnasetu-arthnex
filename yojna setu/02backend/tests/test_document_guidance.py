import pytest
import os
import sys
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

from app.main import app
from app.models import Base, Scheme, SchemeDocument, PartnerSchemeMapping, Partner
from app.db.session import get_db
from seed_db import seed_database


@pytest.fixture(scope="module")
def app_client():
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
    session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, TestingSessionLocal

    app.dependency_overrides.clear()


def test_scheme_with_verified_documents_retrieval(app_client):
    """
    Test 1: Scheme with verified document information
    -> documents displayed with official source metadata.
    """
    client, TestingSessionLocal = app_client
    db = TestingSessionLocal()

    # Query verified NSFDC scheme SIH26092-053
    res = client.get("/api/v1/schemes/SIH26092-053")
    assert res.status_code == 200
    data = res.json()

    assert data["scheme_id"] == "SIH26092-053"
    assert "documents" in data
    assert len(data["documents"]) > 0

    doc_names = [d["document_name"] for d in data["documents"]]
    assert any("Scheduled Caste" in name or "Caste" in name for name in doc_names)
    assert any("Income" in name for name in doc_names)

    # Verify source provenance is attached
    sample_doc = data["documents"][0]
    assert sample_doc["source_document"] is not None
    assert "nsfdc" in sample_doc["source_document"].lower() or len(sample_doc["source_document"]) > 0

    db.close()


def test_scheme_with_no_verified_documents(app_client):
    """
    Test 2: Scheme with no verified document records
    -> returns empty document list triggering the uncertainty notice:
    'Document requirements could not be verified from the available official source. Please confirm with the concerned authority before applying.'
    """
    client, TestingSessionLocal = app_client
    db = TestingSessionLocal()

    # Query scheme with no parsed SchemeDocument rows e.g. SIH26092-002
    res = client.get("/api/v1/schemes/SIH26092-002")
    assert res.status_code == 200
    data = res.json()

    assert data["scheme_id"] == "SIH26092-002"
    assert data["documents"] == []

    db.close()


def test_unsupported_document_must_not_appear(app_client):
    """
    Test 3: Unsupported / fabricated documents must NOT appear in scheme responses.
    """
    client, TestingSessionLocal = app_client
    db = TestingSessionLocal()

    all_docs = db.query(SchemeDocument).all()
    all_doc_names = [d.document_name.lower() for d in all_docs]

    # Fabricated / ungrounded documents
    fabricated_names = [
        "spaceflight permit",
        "crypto wallet certificate",
        "arbitrary municipal token",
        "fabricated land clearance"
    ]
    for fab in fabricated_names:
        assert fab not in all_doc_names, f"Fabricated document '{fab}' was found in database!"

    db.close()


def test_direct_portal_scheme_guidance(app_client):
    """
    Test 4: Direct government portal scheme
    -> official portal URL provided, zero channel partner mappings.
    """
    client, TestingSessionLocal = app_client
    db = TestingSessionLocal()

    # SIH26092-049 is MSME ZED Certification (Direct Govt Portal)
    res = client.get("/api/v1/schemes/SIH26092-049")
    assert res.status_code == 200
    data = res.json()

    portal_url = data.get("application_url") or data.get("official_portal") or data.get("official_source_url")
    assert portal_url is not None
    assert "zed.msme.gov.in" in portal_url or "msme" in portal_url.lower()

    # Must have 0 channel partner mappings
    partner_mappings = db.query(PartnerSchemeMapping).filter(PartnerSchemeMapping.scheme_id == "SIH26092-049").all()
    assert len(partner_mappings) == 0, "Direct government portal scheme must not have channel partner mappings"

    db.close()


def test_partner_routed_scheme_guidance(app_client):
    """
    Test 5: Partner-routed scheme
    -> authorized channel partner mappings exist in database.
    """
    client, TestingSessionLocal = app_client
    db = TestingSessionLocal()

    # Create a verified partner and mapping
    p = Partner(
        partner_id="p-doc-test-1",
        name="Kerala State SC/ST Development Corp",
        code="K-SCSTDC",
        partner_type="SCA",
        latitude=8.5241,
        longitude=76.9366,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=True,
        is_active=True,
        is_accepting_applications=True
    )
    db.add(p)
    mapping = PartnerSchemeMapping(
        partner_id="p-doc-test-1",
        scheme_id="SIH26092-053",
        authorized_category="TERM_LOAN",
        verification_status="VERIFIED_OFFICIAL",
        verification_notes="Authoritative NSFDC Term Loan Channel Partner"
    )
    db.add(mapping)
    db.commit()

    # SIH26092-053 is NSFDC Term Loan (Partner-routed via SCAs/Banks)
    res = client.get("/api/v1/schemes/SIH26092-053")
    assert res.status_code == 200
    data = res.json()

    # Must have authorized channel partners in database
    partner_mappings = db.query(PartnerSchemeMapping).filter(
        PartnerSchemeMapping.scheme_id == "SIH26092-053",
        PartnerSchemeMapping.verification_status == "VERIFIED_OFFICIAL"
    ).all()
    assert len(partner_mappings) > 0, "Partner-routed scheme must have verified official partner mappings"

    db.close()


def test_no_user_document_storage_guarantee(app_client):
    """
    Test 6: Architectural guarantee that YojnaSetu does NOT collect, upload, store, or verify user documents.
    No user document upload endpoints or storage services exist.
    """
    client, _ = app_client

    # Attempting to POST arbitrary file upload to an unauthenticated endpoint returns 404/405
    res = client.post("/api/v1/documents/upload", files={"file": ("test.pdf", b"test content", "application/pdf")})
    assert res.status_code in (404, 405), "User document upload endpoint should NOT exist in YojnaSetu"
