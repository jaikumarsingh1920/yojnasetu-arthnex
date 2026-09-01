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
from app.models import Base, User, UserRole, Partner, Scheme, Application, ApplicationDocument, ApplicationStatusHistory, ApplicationStatus, DocumentVerificationStatus
from app.db.session import get_db
from app.core.security import hash_password, create_access_token
from seed_db import seed_database


@pytest.fixture(scope="module")
def partner_client():
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

    pwd_hash = hash_password("Secret123!")

    # Seed Partner Organizations
    p1 = Partner(partner_id="partner-org-1", name="NSFDC Agency", code="NSFDC_AGENCY", partner_type="CHANNELIZING_AGENCY")
    p2 = Partner(partner_id="partner-org-2", name="NBCFDC Agency", code="NBCFDC_AGENCY", partner_type="CHANNELIZING_AGENCY")
    session.add_all([p1, p2])
    session.commit()

    # Seed Users
    users_list = [
        User(user_id="user-ben-10", email="ben10@example.com", hashed_password=pwd_hash, role=UserRole.BENEFICIARY.value),
        User(user_id="user-p1-user", email="p1user@example.com", hashed_password=pwd_hash, role=UserRole.PARTNER_USER.value, partner_id="partner-org-1"),
        User(user_id="user-p1-admin", email="p1admin@example.com", hashed_password=pwd_hash, role=UserRole.PARTNER_ADMIN.value, partner_id="partner-org-1"),
        User(user_id="user-p2-user", email="p2user@example.com", hashed_password=pwd_hash, role=UserRole.PARTNER_USER.value, partner_id="partner-org-2"),
        User(user_id="user-sys-admin", email="sysadmin@example.com", hashed_password=pwd_hash, role=UserRole.SYSTEM_ADMIN.value),
    ]
    for u_item in users_list:
        ex = session.query(User).filter((User.user_id == u_item.user_id) | (User.email == u_item.email)).first()
        if ex:
            ex.email = u_item.email
            ex.role = u_item.role
            ex.partner_id = u_item.partner_id
            ex.hashed_password = u_item.hashed_password
            ex.is_active = True
        else:
            session.add(u_item)
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


@pytest.fixture(scope="module")
def ben_headers():
    token = create_access_token(user_id="user-ben-10", role=UserRole.BENEFICIARY.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def p1_user_headers():
    token = create_access_token(user_id="user-p1-user", role=UserRole.PARTNER_USER.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def p1_admin_headers():
    token = create_access_token(user_id="user-p1-admin", role=UserRole.PARTNER_ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def p2_user_headers():
    token = create_access_token(user_id="user-p2-user", role=UserRole.PARTNER_USER.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def sys_admin_headers():
    token = create_access_token(user_id="user-sys-admin", role=UserRole.SYSTEM_ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def submitted_app_id(partner_client, ben_headers):
    client, _ = partner_client
    payload = {
        "scheme_id": "SIH26092-052",
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
    # Create application
    create_res = client.post("/api/v1/applications", json=payload, headers=ben_headers)
    assert create_res.status_code == 201
    app_data = create_res.json()
    app_id = app_data["application_id"]

    # Upload all required documents
    for doc in app_data["documents"]:
        if doc["requirement_type"] == "REQUIRED":
            files = {"file": ("proof.pdf", io.BytesIO(b"Document content PDF"), "application/pdf")}
            up_res = client.post(f"/api/v1/applications/{app_id}/documents/{doc['app_document_id']}/upload", files=files, headers=ben_headers)
            assert up_res.status_code == 200

    # Submit application
    sub_res = client.post(f"/api/v1/applications/{app_id}/submit", headers=ben_headers, json={"partner_id": "partner-org-1"})
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "SUBMITTED"
    return app_id


# ─────────────────────────────────────────────────────────────────
# 1. PARTNER ACCESS & RBAC TESTS
# ─────────────────────────────────────────────────────────────────

def test_partner_user_can_access_applications(partner_client, p1_user_headers, submitted_app_id):
    client, _ = partner_client
    res = client.get("/api/v1/partner/applications", headers=p1_user_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) > 0


def test_beneficiary_cannot_access_partner_endpoints(partner_client, ben_headers, submitted_app_id):
    client, _ = partner_client
    res = client.get("/api/v1/partner/applications", headers=ben_headers)
    assert res.status_code == 403

    res_detail = client.get(f"/api/v1/partner/applications/{submitted_app_id}", headers=ben_headers)
    assert res_detail.status_code == 403


def test_unauthenticated_partner_request_returns_401(partner_client, submitted_app_id):
    client, _ = partner_client
    res = client.get("/api/v1/partner/applications")
    assert res.status_code == 401


def test_system_admin_has_global_access(partner_client, sys_admin_headers, submitted_app_id):
    client, _ = partner_client
    res = client.get("/api/v1/partner/applications", headers=sys_admin_headers)
    assert res.status_code == 200
    detail_res = client.get(f"/api/v1/partner/applications/{submitted_app_id}", headers=sys_admin_headers)
    assert detail_res.status_code == 200


# ─────────────────────────────────────────────────────────────────
# 2. ASSIGNMENT & PARTNER ISOLATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_assign_application_to_partner(partner_client, p1_admin_headers, p2_user_headers, submitted_app_id):
    client, _ = partner_client
    # Assign application to partner-org-1
    assign_res = client.post(
        f"/api/v1/partner/applications/{submitted_app_id}/assign",
        json={"partner_id": "partner-org-1", "reviewer_id": "user-p1-user"},
        headers=p1_admin_headers
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_partner_id"] == "partner-org-1"
    assert assign_res.json()["assigned_reviewer_id"] == "user-p1-user"

    # Partner 2 user attempts to view Partner 1's application -> 403 Forbidden!
    iso_res = client.get(f"/api/v1/partner/applications/{submitted_app_id}", headers=p2_user_headers)
    assert iso_res.status_code == 403
    assert "Partner isolation restriction" in iso_res.json()["detail"]


# ─────────────────────────────────────────────────────────────────
# 3. REVIEW WORKFLOW & DOCUMENT VERIFICATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_start_review_transitions_to_under_review(partner_client, p1_user_headers, submitted_app_id):
    client, _ = partner_client
    res = client.post(f"/api/v1/partner/applications/{submitted_app_id}/start-review", headers=p1_user_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "UNDER_REVIEW"
    assert res.json()["assigned_reviewer_id"] == "user-p1-user"


def test_unverified_mandatory_document_blocks_approval(partner_client, p1_admin_headers, submitted_app_id):
    client, _ = partner_client
    # Check approval readiness before document verification
    readiness_res = client.get(f"/api/v1/partner/applications/{submitted_app_id}/approval-readiness", headers=p1_admin_headers)
    assert readiness_res.status_code == 200
    assert readiness_res.json()["can_approve"] is False
    assert len(readiness_res.json()["blocking_documents"]) > 0

    # Attempting approval should fail HTTP 400
    appr_res = client.post(
        f"/api/v1/partner/applications/{submitted_app_id}/review",
        json={"decision": "APPROVED", "reason": "Attempting premature approval"},
        headers=p1_admin_headers
    )
    assert appr_res.status_code == 400
    assert "mandatory documents are not fully verified" in appr_res.json()["detail"]


def test_document_review_verify_and_reject(partner_client, p1_user_headers, submitted_app_id):
    client, _ = partner_client
    # Get application documents
    app_detail = client.get(f"/api/v1/partner/applications/{submitted_app_id}", headers=p1_user_headers).json()
    doc_id = app_detail["documents"][0]["app_document_id"]

    # Reject document without reason -> 400
    rej_no_reason = client.post(
        f"/api/v1/partner/applications/{submitted_app_id}/documents/{doc_id}/review",
        json={"verification_status": "REJECTED"},
        headers=p1_user_headers
    )
    assert rej_no_reason.status_code == 400

    # Verify document with reason -> 200
    ver_res = client.post(
        f"/api/v1/partner/applications/{submitted_app_id}/documents/{doc_id}/review",
        json={"verification_status": "VERIFIED", "reason": "Document verified against authentic records."},
        headers=p1_user_headers
    )
    assert ver_res.status_code == 200
    assert ver_res.json()["verification_status"] == "VERIFIED"
    assert ver_res.json()["verified_by"] == "user-p1-user"


def test_add_internal_review_note(partner_client, p1_user_headers, submitted_app_id):
    client, _ = partner_client
    res = client.post(
        f"/api/v1/partner/applications/{submitted_app_id}/notes",
        json={"content": "Beneficiary profile matches eligibility criteria cleanly."},
        headers=p1_user_headers
    )
    assert res.status_code == 201
    assert res.json()["author_id"] == "user-p1-user"
    assert res.json()["content"] == "Beneficiary profile matches eligibility criteria cleanly."


# ─────────────────────────────────────────────────────────────────
# 4. APPROVAL & REJECTION DECISION TESTS
# ─────────────────────────────────────────────────────────────────

def test_verify_all_mandatory_documents_and_approve(partner_client, p1_user_headers, p1_admin_headers, submitted_app_id):
    client, _ = partner_client
    app_detail = client.get(f"/api/v1/partner/applications/{submitted_app_id}", headers=p1_user_headers).json()

    # Verify all uploaded documents
    for doc in app_detail["documents"]:
        ver_res = client.post(
            f"/api/v1/partner/applications/{submitted_app_id}/documents/{doc['app_document_id']}/review",
            json={"verification_status": "VERIFIED", "reason": "Verified by partner reviewer."},
            headers=p1_user_headers
        )
        assert ver_res.status_code == 200

    # Check readiness -> true
    readiness_res = client.get(f"/api/v1/partner/applications/{submitted_app_id}/approval-readiness", headers=p1_admin_headers)
    assert readiness_res.status_code == 200
    assert readiness_res.json()["can_approve"] is True

    # Ordinary PARTNER_USER attempts approval -> 403 Forbidden (requires PARTNER_ADMIN or SYSTEM_ADMIN)
    user_appr = client.post(
        f"/api/v1/partner/applications/{submitted_app_id}/review",
        json={"decision": "APPROVED", "reason": "User approval attempt"},
        headers=p1_user_headers
    )
    assert user_appr.status_code == 403

    # PARTNER_ADMIN approves -> 200 OK
    admin_appr = client.post(
        f"/api/v1/partner/applications/{submitted_app_id}/review",
        json={"decision": "APPROVED", "reason": "All documents verified; scheme criteria met."},
        headers=p1_admin_headers
    )
    assert admin_appr.status_code == 200
    assert admin_appr.json()["status"] == "APPROVED"


def test_already_approved_application_cannot_be_approved_or_rejected(partner_client, p1_admin_headers, submitted_app_id):
    client, _ = partner_client
    res = client.post(
        f"/api/v1/partner/applications/{submitted_app_id}/review",
        json={"decision": "APPROVED", "reason": "Second approval attempt"},
        headers=p1_admin_headers
    )
    assert res.status_code == 400
    assert "already been finalized" in res.json()["detail"]


# ─────────────────────────────────────────────────────────────────
# 5. REJECTION WORKFLOW TEST
# ─────────────────────────────────────────────────────────────────

def test_application_rejection_workflow(partner_client, ben_headers, p1_admin_headers):
    client, _ = partner_client
    # Create second application for rejection test
    payload = {
        "scheme_id": "SIH26092-001",
        "profile": {"age": 28, "annual_income": 180000.0, "social_category": "SC", "is_sc": True}
    }
    app_res = client.post("/api/v1/applications", json=payload, headers=ben_headers)
    app_id = app_res.json()["application_id"]

    # Submit application
    client.post(f"/api/v1/applications/{app_id}/submit", headers=ben_headers, json={"partner_id": "partner-org-1"})

    # Rejection without reason -> 400
    rej_no_reason = client.post(
        f"/api/v1/partner/applications/{app_id}/review",
        json={"decision": "REJECTED"},
        headers=p1_admin_headers
    )
    assert rej_no_reason.status_code == 400

    # Rejection with reason -> 200 OK
    rej_res = client.post(
        f"/api/v1/partner/applications/{app_id}/review",
        json={"decision": "REJECTED", "reason": "Ineligible due to incomplete documents."},
        headers=p1_admin_headers
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"
