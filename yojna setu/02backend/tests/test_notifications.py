import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy.pool import StaticPool
from app.main import app
from app.models import (
    Base, User, UserRole, Scheme, SchemeVerification, Application, ApplicationDocument, Notification, NotificationPreference
)
from app.db.session import get_db
from app.core.security import hash_password, create_access_token
from app.notifications.service import NotificationService


@pytest.fixture(scope="module")
def notif_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    # Seed users
    u_ben = User(user_id="USER-BEN-NOTIF-01", email="ben_notif@test.com", hashed_password=hash_password("Pass123!"), role="BENEFICIARY")
    u_partner = User(user_id="USER-PARTNER-NOTIF-01", email="partner_notif@test.com", hashed_password=hash_password("Pass123!"), role="PARTNER_USER", partner_id="PARTNER-01")
    u_padmin = User(user_id="USER-PADMIN-NOTIF-01", email="padmin_notif@test.com", hashed_password=hash_password("Pass123!"), role="PARTNER_ADMIN", partner_id="PARTNER-01")
    db.add_all([u_ben, u_partner, u_padmin])

    # Seed scheme
    scheme = Scheme(
        scheme_id="SCHEME-NOTIF-01",
        scheme_name="National Artisans Credit Guarantee Scheme",
        scheme_code="NACGS-2026",
        ministry="Ministry of MSME",
        scheme_type="CREDIT_GUARANTEE",
        sector="MICRO_FINANCE"
    )
    scheme_verif = SchemeVerification(id="VERIF-NOTIF-01", scheme_id="SCHEME-NOTIF-01", verification_status="VERIFIED")
    db.add_all([scheme, scheme_verif])

    db.commit()
    db.close()

    with TestClient(app) as client:
        yield client, TestingSessionLocal

    app.dependency_overrides.clear()


def get_token_headers(user_id: str, role: str) -> dict:
    token = create_access_token(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_notification_creation_and_service_methods(notif_client):
    _, session_factory = notif_client
    db = session_factory()

    # 1. Create notification
    notif = NotificationService.create_notification(
        db=db,
        recipient_user_id="USER-BEN-NOTIF-01",
        notification_type="SYSTEM_INFO",
        extra_context={"title": "Test Alert", "message": "This is a test notification."}
    )
    db.commit()

    assert notif is not None
    assert notif.recipient_user_id == "USER-BEN-NOTIF-01"
    assert notif.is_read is False

    # 2. Check unread count
    count = NotificationService.get_unread_count(db, "USER-BEN-NOTIF-01")
    assert count >= 1

    # 3. Mark read
    marked = NotificationService.mark_read(db, notif.notification_id, "USER-BEN-NOTIF-01")
    db.commit()
    assert marked.is_read is True
    assert marked.read_at is not None

    db.close()


def test_notification_api_endpoints(notif_client):
    client, session_factory = notif_client
    db = session_factory()

    # Create additional notification
    notif = NotificationService.create_notification(
        db=db,
        recipient_user_id="USER-BEN-NOTIF-01",
        notification_type="APPLICATION_SUBMITTED",
        application_id="APP-TEST-99",
        scheme_name="National Artisans Credit Scheme"
    )
    db.commit()
    notif_id = notif.notification_id
    db.close()

    headers = get_token_headers("USER-BEN-NOTIF-01", UserRole.BENEFICIARY.value)

    # GET /api/v1/notifications
    res = client.get("/api/v1/notifications", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["unread_count"] >= 1

    # GET /api/v1/notifications/unread-count
    res_count = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res_count.status_code == 200
    assert "unread_count" in res_count.json()

    # POST /api/v1/notifications/{id}/read
    res_read = client.post(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    # POST /api/v1/notifications/read-all
    res_all = client.post("/api/v1/notifications/read-all", headers=headers)
    assert res_all.status_code == 200
    assert res_all.json()["message"] == "All notifications marked as read."


def test_notification_recipient_data_isolation(notif_client):
    client, session_factory = notif_client
    db = session_factory()

    # Create notification for User A
    notif = NotificationService.create_notification(
        db=db,
        recipient_user_id="USER-BEN-NOTIF-01",
        notification_type="SYSTEM_INFO"
    )
    db.commit()
    notif_id = notif.notification_id
    db.close()

    # User B attempts accessing User A's notification
    partner_headers = get_token_headers("USER-PARTNER-NOTIF-01", UserRole.PARTNER_USER.value)
    res = client.get(f"/api/v1/notifications/{notif_id}", headers=partner_headers)
    assert res.status_code == 404
    assert "was not found" in res.json()["detail"]

    # User B attempts marking User A's notification read
    res_read = client.post(f"/api/v1/notifications/{notif_id}/read", headers=partner_headers)
    assert res_read.status_code == 404


def test_notification_preferences(notif_client):
    client, _ = notif_client
    headers = get_token_headers("USER-BEN-NOTIF-01", UserRole.BENEFICIARY.value)

    # Get preferences
    res = client.get("/api/v1/notifications/preferences", headers=headers)
    assert res.status_code == 200
    assert res.json()["in_app_enabled"] is True

    # Update preferences
    res_up = client.put("/api/v1/notifications/preferences", json={"email_enabled": False, "push_enabled": True}, headers=headers)
    assert res_up.status_code == 200
    assert res_up.json()["email_enabled"] is False
    assert res_up.json()["push_enabled"] is True


def test_full_application_lifecycle_notification_triggers(notif_client):
    client, _ = notif_client
    ben_headers = get_token_headers("USER-BEN-NOTIF-01", UserRole.BENEFICIARY.value)
    partner_headers = get_token_headers("USER-PARTNER-NOTIF-01", UserRole.PARTNER_USER.value)
    padmin_headers = get_token_headers("USER-PADMIN-NOTIF-01", UserRole.PARTNER_ADMIN.value)

    # 1. Beneficiary creates and submits application
    create_res = client.post("/api/v1/applications", json={
        "scheme_id": "SCHEME-NOTIF-01",
        "profile": {"age": 30, "annual_income": 120000.0, "social_category": "OBC", "gender": "MALE", "state": "MH", "sector": "MICRO_FINANCE", "project_cost": 100000.0, "requested_loan_amount": 80000.0}
    }, headers=ben_headers)
    assert create_res.status_code == 201
    app_id = create_res.json()["application_id"]

    sub_res = client.post(f"/api/v1/applications/{app_id}/submit", headers=ben_headers)
    assert sub_res.status_code == 200

    # Beneficiary receives APPLICATION_SUBMITTED notification
    ben_notifs = client.get("/api/v1/notifications", headers=ben_headers).json()["items"]
    assert any(n["notification_type"] == "APPLICATION_SUBMITTED" and n["application_id"] == app_id for n in ben_notifs)

    # 2. Partner assigns application to partner reviewer
    assign_res = client.post(f"/api/v1/partner/applications/{app_id}/assign", json={"reviewer_id": "USER-PARTNER-NOTIF-01"}, headers=padmin_headers)
    assert assign_res.status_code == 200

    # Reviewer receives APPLICATION_ASSIGNED notification
    partner_notifs = client.get("/api/v1/notifications", headers=partner_headers).json()["items"]
    assert any(n["notification_type"] == "APPLICATION_ASSIGNED" and n["application_id"] == app_id for n in partner_notifs)

    # 3. Partner starts review
    client.post(f"/api/v1/partner/applications/{app_id}/start-review", headers=partner_headers)
    ben_notifs_after_review = client.get("/api/v1/notifications", headers=ben_headers).json()["items"]
    assert any(n["notification_type"] == "APPLICATION_UNDER_REVIEW" and n["application_id"] == app_id for n in ben_notifs_after_review)

    # 4. Partner requests correction
    client.post(f"/api/v1/partner/applications/{app_id}/request-correction", json={"reason": "Upload legible address proof.", "correction_fields": ["Address Proof"]}, headers=partner_headers)
    ben_notifs_after_corr = client.get("/api/v1/notifications", headers=ben_headers).json()["items"]
    assert any(n["notification_type"] == "CORRECTION_REQUIRED" and n["application_id"] == app_id for n in ben_notifs_after_corr)

    # 5. Beneficiary resubmits
    client.post(f"/api/v1/applications/{app_id}/submit", headers=ben_headers)
    partner_notifs_after_resub = client.get("/api/v1/notifications", headers=partner_headers).json()["items"]
    assert any(n["notification_type"] == "APPLICATION_RESUBMITTED" and n["application_id"] == app_id for n in partner_notifs_after_resub)

    # 6. Partner Admin approves application
    client.post(f"/api/v1/partner/applications/{app_id}/approve", headers=padmin_headers)
    ben_notifs_final = client.get("/api/v1/notifications", headers=ben_headers).json()["items"]
    assert any(n["notification_type"] == "APPLICATION_APPROVED" and n["application_id"] == app_id for n in ben_notifs_final)
