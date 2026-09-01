import pytest
import os
import sys
import io
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
from app.models import Base, User, UserRole, Scheme, Application, ApplicationDocument, ApplicationStatusHistory, ApplicationStatus
from app.db.session import get_db
from app.core.security import hash_password, create_access_token
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

    # Seed test users
    pwd_hash = hash_password("Secret123!")

    ben1 = User(user_id="user-ben-1", email="ben1@example.com", hashed_password=pwd_hash, role=UserRole.BENEFICIARY.value)
    ben2 = User(user_id="user-ben-2", email="ben2@example.com", hashed_password=pwd_hash, role=UserRole.BENEFICIARY.value)
    partner = User(user_id="user-partner-1", email="partner1@example.com", hashed_password=pwd_hash, role=UserRole.PARTNER_USER.value)
    admin = User(user_id="user-admin-1", email="admin1@example.com", hashed_password=pwd_hash, role=UserRole.SYSTEM_ADMIN.value)

    session.add_all([ben1, ben2, partner, admin])
    session.commit()
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


@pytest.fixture
def ben1_headers():
    token = create_access_token(user_id="user-ben-1", role=UserRole.BENEFICIARY.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ben2_headers():
    token = create_access_token(user_id="user-ben-2", role=UserRole.BENEFICIARY.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def partner_headers():
    token = create_access_token(user_id="user-partner-1", role=UserRole.PARTNER_USER.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    token = create_access_token(user_id="user-admin-1", role=UserRole.SYSTEM_ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_payload():
    return {
        "scheme_id": "SIH26092-052",  # NSFDC Micro Finance Scheme
        "profile": {
            "age": 28,
            "annual_income": 180000.0,
            "social_category": "SC",
            "is_sc": True,
            "gender": "MALE",
            "state": "MAHARASHTRA",
            "applicant_type": "INDIVIDUAL",
            "business_stage": "NEW",
            "is_new_unit": True,
            "sector": "MICRO_FINANCE",
            "activity_type": "SMALL_MICRO_BUSINESS",
            "project_cost": 100000.0,
            "requested_loan_amount": 90000.0
        }
    }


# ─────────────────────────────────────────────────────────────────
# 1. APPLICATION CREATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_create_application_valid(app_client, ben1_headers, sample_payload):
    client, _ = app_client
    res = client.post("/api/v1/applications", json=sample_payload, headers=ben1_headers)
    assert res.status_code == 201
    data = res.json()

    assert data["user_id"] == "user-ben-1"
    assert data["scheme_id"] == "SIH26092-052"
    assert data["status"] in ("DOCUMENTS_PENDING", "READY_FOR_SUBMISSION")
    assert data["profile_snapshot"]["annual_income"] == 180000.0
    assert data["eligibility_snapshot"]["status"] == "ELIGIBLE"
    assert len(data["documents"]) > 0
    assert len(data["status_history"]) > 0


def test_create_application_nonexistent_scheme(app_client, ben1_headers, sample_payload):
    client, _ = app_client
    invalid_payload = dict(sample_payload)
    invalid_payload["scheme_id"] = "NONEXISTENT-SCHEME-999"

    res = client.post("/api/v1/applications", json=invalid_payload, headers=ben1_headers)
    assert res.status_code == 404
    assert "was not found" in res.json()["detail"]


def test_create_application_unauthenticated(app_client, sample_payload):
    client, _ = app_client
    res = client.post("/api/v1/applications", json=sample_payload)
    assert res.status_code == 401


def test_create_application_non_beneficiary_role(app_client, partner_headers, sample_payload):
    client, _ = app_client
    res = client.post("/api/v1/applications", json=sample_payload, headers=partner_headers)
    assert res.status_code == 403


def test_create_duplicate_active_application_rejected(app_client, ben1_headers, sample_payload):
    client, _ = app_client
    # Attempting to create duplicate active application for same scheme SIH26092-052
    res = client.post("/api/v1/applications", json=sample_payload, headers=ben1_headers)
    assert res.status_code == 400
    assert "An active application already exists" in res.json()["detail"]


# ─────────────────────────────────────────────────────────────────
# 2. OWNERSHIP & SECURITY ISOLATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_beneficiary_access_own_application(app_client, ben1_headers, sample_payload):
    client, _ = app_client
    # Get user 1's active application ID
    list_res = client.get("/api/v1/applications", headers=ben1_headers)
    assert list_res.status_code == 200
    app_id = list_res.json()["items"][0]["application_id"]

    detail_res = client.get(f"/api/v1/applications/{app_id}", headers=ben1_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["application_id"] == app_id


def test_beneficiary_cannot_access_another_user_application(app_client, ben1_headers, ben2_headers):
    client, _ = app_client
    list_res = client.get("/api/v1/applications", headers=ben1_headers)
    ben1_app_id = list_res.json()["items"][0]["application_id"]

    # Ben 2 attempts to view Ben 1's application
    detail_res = client.get(f"/api/v1/applications/{ben1_app_id}", headers=ben2_headers)
    assert detail_res.status_code == 403
    assert "Access denied" in detail_res.json()["detail"]


def test_beneficiary_cannot_modify_another_user_application(app_client, ben1_headers, ben2_headers):
    client, _ = app_client
    list_res = client.get("/api/v1/applications", headers=ben1_headers)
    ben1_app_id = list_res.json()["items"][0]["application_id"]

    update_payload = {
        "profile": {
            "age": 30,
            "annual_income": 200000.0,
            "social_category": "SC",
            "is_sc": True
        }
    }
    # Ben 2 attempts to update Ben 1's application
    res = client.put(f"/api/v1/applications/{ben1_app_id}", json=update_payload, headers=ben2_headers)
    assert res.status_code == 403


# ─────────────────────────────────────────────────────────────────
# 3. DRAFT UPDATE TESTS
# ─────────────────────────────────────────────────────────────────

def test_update_draft_application_valid(app_client, ben1_headers):
    client, _ = app_client
    list_res = client.get("/api/v1/applications", headers=ben1_headers)
    app_id = list_res.json()["items"][0]["application_id"]

    update_payload = {
        "profile": {
            "age": 30,
            "annual_income": 210000.0,
            "social_category": "SC",
            "is_sc": True,
            "gender": "MALE",
            "state": "MAHARASHTRA",
            "applicant_type": "INDIVIDUAL",
            "business_stage": "NEW",
            "is_new_unit": True,
            "sector": "MICRO_FINANCE",
            "activity_type": "SMALL_MICRO_BUSINESS",
            "project_cost": 120000.0,
            "requested_loan_amount": 100000.0
        }
    }
    res = client.put(f"/api/v1/applications/{app_id}", json=update_payload, headers=ben1_headers)
    assert res.status_code == 200
    assert res.json()["profile_snapshot"]["annual_income"] == 210000.0


# ─────────────────────────────────────────────────────────────────
# 4. DOCUMENT UPLOAD & SUBMISSION VALIDATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_document_requirements_initialized(app_client, ben1_headers):
    client, _ = app_client
    list_res = client.get("/api/v1/applications", headers=ben1_headers)
    app_data = list_res.json()["items"][0]

    assert "documents" in app_data
    docs = app_data["documents"]
    assert len(docs) > 0
    # Every doc initialized with is_uploaded = False
    assert any(d["requirement_type"] == "REQUIRED" for d in docs)
    assert all(d["is_uploaded"] is False for d in docs)


def test_submission_prevented_when_mandatory_documents_missing(app_client, ben1_headers):
    client, _ = app_client
    list_res = client.get("/api/v1/applications", headers=ben1_headers)
    app_id = list_res.json()["items"][0]["application_id"]

    # Check validation endpoint
    val_res = client.get(f"/api/v1/applications/{app_id}/validate", headers=ben1_headers)
    assert val_res.status_code == 200
    assert val_res.json()["can_submit"] is False
    assert len(val_res.json()["missing_documents"]) > 0

    # Submit request should fail HTTP 400
    sub_res = client.post(f"/api/v1/applications/{app_id}/submit", headers=ben1_headers, json={"partner_id": "PARTNER-001"})
    assert sub_res.status_code == 400
    assert "missing" in sub_res.json()["detail"]


def test_upload_mandatory_documents_and_submit(app_client, ben1_headers):
    client, _ = app_client
    list_res = client.get("/api/v1/applications", headers=ben1_headers)
    app_data = list_res.json()["items"][0]
    app_id = app_data["application_id"]

    # Upload all required documents
    for doc in app_data["documents"]:
        if doc["requirement_type"] == "REQUIRED":
            file_content = b"Mock document content PDF bytes"
            files = {"file": ("test_doc.pdf", io.BytesIO(file_content), "application/pdf")}
            up_res = client.post(
                f"/api/v1/applications/{app_id}/documents/{doc['app_document_id']}/upload",
                files=files,
                headers=ben1_headers
            )
            assert up_res.status_code == 200
            assert up_res.json()["is_uploaded"] is True

    # Validate readiness
    val_res = client.get(f"/api/v1/applications/{app_id}/validate", headers=ben1_headers)
    assert val_res.status_code == 200
    assert val_res.json()["can_submit"] is True
    assert len(val_res.json()["missing_documents"]) == 0

    # Submit application
    sub_res = client.post(f"/api/v1/applications/{app_id}/submit", headers=ben1_headers, json={"partner_id": "PARTNER-001"})
    assert sub_res.status_code == 200
    sub_data = sub_res.json()

    assert sub_data["status"] == "SUBMITTED"
    assert sub_data["submitted_at"] is not None
    assert len(sub_data["status_history"]) >= 2


def test_duplicate_submission_rejected(app_client, ben1_headers):
    client, _ = app_client
    list_res = client.get("/api/v1/applications", headers=ben1_headers)
    app_id = list_res.json()["items"][0]["application_id"]

    # Attempting second submit on SUBMITTED application
    sub_res = client.post(f"/api/v1/applications/{app_id}/submit", headers=ben1_headers, json={"partner_id": "PARTNER-001"})
    assert sub_res.status_code == 400
    assert "already been submitted" in sub_res.json()["detail"]


def test_submitted_application_is_immutable(app_client, ben1_headers):
    client, _ = app_client
    list_res = client.get("/api/v1/applications", headers=ben1_headers)
    app_id = list_res.json()["items"][0]["application_id"]

    update_payload = {
        "profile": {
            "age": 35,
            "annual_income": 300000.0,
            "social_category": "SC",
            "is_sc": True
        }
    }
    res = client.put(f"/api/v1/applications/{app_id}", json=update_payload, headers=ben1_headers)
    assert res.status_code == 400
    assert "immutable" in res.json()["detail"]


# ─────────────────────────────────────────────────────────────────
# 5. LISTING & PAGINATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_list_my_applications_isolation(app_client, ben1_headers, ben2_headers):
    client, _ = app_client

    res1 = client.get("/api/v1/applications", headers=ben1_headers)
    assert res1.status_code == 200
    items1 = res1.json()["items"]
    assert all(item["user_id"] == "user-ben-1" for item in items1)

    res2 = client.get("/api/v1/applications", headers=ben2_headers)
    assert res2.status_code == 200
    items2 = res2.json()["items"]
    assert len(items2) == 0  # Ben 2 has no applications yet


def test_status_filter_applications(app_client, ben1_headers):
    client, _ = app_client
    res_sub = client.get("/api/v1/applications?status=SUBMITTED", headers=ben1_headers)
    assert res_sub.status_code == 200
    assert all(item["status"] == "SUBMITTED" for item in res_sub.json()["items"])

    res_draft = client.get("/api/v1/applications?status=DRAFT", headers=ben1_headers)
    assert res_draft.status_code == 200
    assert len(res_draft.json()["items"]) == 0
