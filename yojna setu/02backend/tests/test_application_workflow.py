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

import json
from app.main import app
from app.models import Base, User, UserRole, Partner, Scheme, Application, ApplicationDocument, ApplicationStatusHistory
from app.db.session import get_db
from app.core.security import hash_password, create_access_token
from seed_db import seed_database


@pytest.fixture(scope="module")
def workflow_client():
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

    p1 = Partner(partner_id="wf-partner-1", name="Workflow Partner One", code="WF_PARTNER_1", partner_type="CHANNELIZING_AGENCY")
    session.add(p1)
    session.commit()

    from app.models import SchemeDocument
    doc_meta = SchemeDocument(
        document_id="doc-pmegp-aadhaar",
        scheme_id="SIH26092-001",
        document_name="Aadhaar Card",
        requirement_type="REQUIRED"

    )
    session.add(doc_meta)
    session.commit()


    users = [
        User(user_id="citizen-wf-user", email="citizen.wf@example.com", hashed_password=pwd_hash, role=UserRole.BENEFICIARY.value, profile_data=json.dumps({"name": "Test Citizen", "caste_category": "SC", "annual_income": 120000})),
        User(user_id="partner-wf-user", email="partner.wf@example.com", hashed_password=pwd_hash, role=UserRole.PARTNER_USER.value, partner_id="wf-partner-1"),
        User(user_id="partner-wf-admin", email="partner.admin@example.com", hashed_password=pwd_hash, role=UserRole.PARTNER_ADMIN.value, partner_id="wf-partner-1"),
    ]


    for u in users:
        session.add(u)
    session.commit()

    def override_get_db():
        try:
            db_sess = TestingSessionLocal()
            yield db_sess
        finally:
            db_sess.close()

    app.dependency_overrides[get_db] = override_get_db

    token_citizen = create_access_token(user_id="citizen-wf-user", role=UserRole.BENEFICIARY.value)
    token_p_user = create_access_token(user_id="partner-wf-user", role=UserRole.PARTNER_USER.value)
    token_p_admin = create_access_token(user_id="partner-wf-admin", role=UserRole.PARTNER_ADMIN.value)


    with TestClient(app) as client:
        client.token_citizen = token_citizen
        client.token_p_user = token_p_user
        client.token_p_admin = token_p_admin
        yield client

    app.dependency_overrides.clear()


def test_complete_end_to_end_application_lifecycle(workflow_client):
    client = workflow_client
    c_headers = {"Authorization": f"Bearer {client.token_citizen}"}
    p_user_headers = {"Authorization": f"Bearer {client.token_p_user}"}
    p_admin_headers = {"Authorization": f"Bearer {client.token_p_admin}"}

    # 1. Citizen creates application for PMEGP (SIH26092-001)
    resp = client.post(
        "/api/v1/applications",
        json={
            "scheme_id": "SIH26092-001",
            "profile": {"name": "Test Citizen", "caste_category": "SC", "annual_income": 120000}
        },
        headers=c_headers
    )
    assert resp.status_code == 201, resp.text
    app_data = resp.json()
    app_id = app_data["application_id"]
    assert app_data["status"] in ["DRAFT", "DOCUMENTS_PENDING", "READY_FOR_SUBMISSION"]

    assert len(app_data["documents"]) > 0

    first_doc = app_data["documents"][0]
    first_doc_id = first_doc["app_document_id"]

    # 2. Upload document file
    file_bytes = b"%PDF-1.4 Fake PDF Content for Test"
    upload_resp = client.post(
        f"/api/v1/applications/{app_id}/documents/{first_doc_id}/upload",
        files={"file": ("test_aadhaar.pdf", io.BytesIO(file_bytes), "application/pdf")},
        headers=c_headers
    )
    assert upload_resp.status_code == 200, upload_resp.text
    assert upload_resp.json()["is_uploaded"] is True

    # 3. Validate submission
    val_resp = client.get(f"/api/v1/applications/{app_id}/validate", headers=c_headers)
    assert val_resp.status_code == 200
    assert val_resp.json()["can_submit"] is True

    # 4. Submit application to partner
    sub_resp = client.post(
        f"/api/v1/applications/{app_id}/submit",
        json={"partner_id": "wf-partner-1"},
        headers=c_headers
    )
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "SUBMITTED"
    assert sub_resp.json()["submitted_at"] is not None



    # 5. Partner user starts review
    start_resp = client.post(f"/api/v1/partner/applications/{app_id}/start-review", headers=p_user_headers)
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "UNDER_REVIEW"

    # 6. Partner user requests correction
    corr_resp = client.post(
        f"/api/v1/partner/applications/{app_id}/request-correction",
        json={"reason": "Aadhaar image is blurry", "correction_fields": ["Identity Proof"]},
        headers=p_user_headers
    )
    assert corr_resp.status_code == 200
    assert corr_resp.json()["status"] == "CORRECTION_REQUIRED"
    assert corr_resp.json()["correction_reason"] == "Aadhaar image is blurry"

    # 7. Beneficiary resubmits & Partner starts review again
    resub_resp = client.post(
        f"/api/v1/applications/{app_id}/submit",
        json={"partner_id": "wf-partner-1"},
        headers=c_headers
    )
    assert resub_resp.status_code == 200

    start_resp2 = client.post(f"/api/v1/partner/applications/{app_id}/start-review", headers=p_user_headers)
    assert start_resp2.status_code == 200
    assert start_resp2.json()["status"] == "UNDER_REVIEW"

    # 8. Partner verifies document
    v_resp = client.post(
        f"/api/v1/partner/applications/{app_id}/documents/{first_doc_id}/review",
        json={"verification_status": "VERIFIED", "reason": "Verified manually"},
        headers=p_user_headers
    )
    assert v_resp.status_code == 200

    # 9. Check approval readiness
    r_resp = client.get(f"/api/v1/partner/applications/{app_id}/approval-readiness", headers=p_admin_headers)
    assert r_resp.status_code == 200
    assert r_resp.json()["can_approve"] is True

    # 10. Partner admin approves application
    appr_resp = client.post(
        f"/api/v1/partner/applications/{app_id}/review",
        json={"decision": "APPROVED", "reason": "All checks passed"},
        headers=p_admin_headers
    )
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "APPROVED"


    # 10. Partner admin marks application completed / benefit disbursed
    comp_resp = client.post(
        f"/api/v1/partner/applications/{app_id}/complete?notes=Disbursed+via+DBT",
        headers=p_admin_headers
    )
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "COMPLETED"


def test_application_withdrawal(workflow_client):
    client = workflow_client
    c_headers = {"Authorization": f"Bearer {client.token_citizen}"}

    # Citizen creates another application
    resp = client.post(
        "/api/v1/applications",
        json={
            "scheme_id": "SIH26092-053",
            "profile": {"name": "Test Citizen", "caste_category": "SC", "annual_income": 120000}
        },
        headers=c_headers
    )
    assert resp.status_code == 201
    app_id = resp.json()["application_id"]

    # Citizen withdraws application
    w_resp = client.post(
        f"/api/v1/applications/{app_id}/withdraw",
        json={"reason": "No longer needed"},
        headers=c_headers
    )
    assert w_resp.status_code == 200
    assert w_resp.json()["status"] == "WITHDRAWN"

    # Verify withdrawing an already withdrawn application returns 400
    w2_resp = client.post(
        f"/api/v1/applications/{app_id}/withdraw",
        json={"reason": "Try again"},
        headers=c_headers
    )
    assert w2_resp.status_code == 400


def test_application_rejection(workflow_client):
    client = workflow_client
    c_headers = {"Authorization": f"Bearer {client.token_citizen}"}
    p_user_headers = {"Authorization": f"Bearer {client.token_p_user}"}
    p_admin_headers = {"Authorization": f"Bearer {client.token_p_admin}"}

    resp = client.post(
        "/api/v1/applications",
        json={
            "scheme_id": "SIH26092-075",
            "profile": {"name": "Test Citizen", "caste_category": "SC", "annual_income": 120000}
        },
        headers=c_headers
    )
    assert resp.status_code == 201
    app_id = resp.json()["application_id"]

    # Submit to partner
    client.post(
        f"/api/v1/applications/{app_id}/submit",
        json={"partner_id": "wf-partner-1"},
        headers=c_headers
    )

    # Partner admin rejects application
    rej_resp = client.post(
        f"/api/v1/partner/applications/{app_id}/review",
        json={"decision": "REJECTED", "reason": "Income proof does not match database"},
        headers=p_admin_headers
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "REJECTED"
    assert rej_resp.json()["rejection_reason"] == "Income proof does not match database"
