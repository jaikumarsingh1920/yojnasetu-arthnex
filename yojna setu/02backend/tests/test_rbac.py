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
from app.models import Base, User, UserRole
from app.db.session import get_db
from app.core.security import hash_password, create_access_token


@pytest.fixture(scope="module")
def rbac_client():
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

    # Pre-seed 4 users with distinct roles
    db = TestingSessionLocal()
    users = {
        "beneficiary": User(email="ben@test.com", hashed_password=hash_password("Pass123!"), role="BENEFICIARY"),
        "partner_user": User(email="pu@test.com", hashed_password=hash_password("Pass123!"), role="PARTNER_USER"),
        "partner_admin": User(email="pa@test.com", hashed_password=hash_password("Pass123!"), role="PARTNER_ADMIN"),
        "system_admin": User(email="sa@test.com", hashed_password=hash_password("Pass123!"), role="SYSTEM_ADMIN"),
    }
    for u in users.values():
        db.add(u)
    db.commit()
    for key, u in users.items():
        db.refresh(u)
    db.close()

    with TestClient(app) as client:
        yield client, users, TestingSessionLocal

    app.dependency_overrides.clear()


def _get_auth_header(client, identifier, password="Pass123!"):
    res = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────
# 1. UNAUTHENTICATED ACCESS REJECTION
# ─────────────────────────────────────────────────────────────────

def test_unauthenticated_access_rejected(rbac_client):
    client, _, _ = rbac_client
    # Attempt accessing protected endpoints without token
    assert client.get("/api/v1/auth/test-beneficiary").status_code == 401
    assert client.get("/api/v1/auth/test-partner").status_code == 401
    assert client.get("/api/v1/auth/test-partner-admin").status_code == 401
    assert client.get("/api/v1/auth/test-system-admin").status_code == 401


# ─────────────────────────────────────────────────────────────────
# 2. BENEFICIARY ROLE ACCESS CONTROL
# ─────────────────────────────────────────────────────────────────

def test_beneficiary_role_access(rbac_client):
    client, _, _ = rbac_client
    headers = _get_auth_header(client, "ben@test.com")

    # BENEFICIARY can access beneficiary endpoint
    res_ben = client.get("/api/v1/auth/test-beneficiary", headers=headers)
    assert res_ben.status_code == 200
    assert res_ben.json()["resource"] == "beneficiary_data"

    # BENEFICIARY cannot access partner endpoint -> 403
    res_part = client.get("/api/v1/auth/test-partner", headers=headers)
    assert res_part.status_code == 403

    # BENEFICIARY cannot access partner admin endpoint -> 403
    res_padmin = client.get("/api/v1/auth/test-partner-admin", headers=headers)
    assert res_padmin.status_code == 403

    # BENEFICIARY cannot access system admin endpoint -> 403
    res_sys = client.get("/api/v1/auth/test-system-admin", headers=headers)
    assert res_sys.status_code == 403


# ─────────────────────────────────────────────────────────────────
# 3. PARTNER USER ROLE ACCESS CONTROL
# ─────────────────────────────────────────────────────────────────

def test_partner_user_role_access(rbac_client):
    client, _, _ = rbac_client
    headers = _get_auth_header(client, "pu@test.com")

    # PARTNER_USER can access partner endpoint
    res_part = client.get("/api/v1/auth/test-partner", headers=headers)
    assert res_part.status_code == 200
    assert res_part.json()["resource"] == "partner_assigned_data"

    # PARTNER_USER cannot access beneficiary endpoint -> 403
    assert client.get("/api/v1/auth/test-beneficiary", headers=headers).status_code == 403

    # PARTNER_USER cannot access partner admin endpoint -> 403
    assert client.get("/api/v1/auth/test-partner-admin", headers=headers).status_code == 403

    # PARTNER_USER cannot access system admin endpoint -> 403
    assert client.get("/api/v1/auth/test-system-admin", headers=headers).status_code == 403


# ─────────────────────────────────────────────────────────────────
# 4. PARTNER ADMIN ROLE ACCESS CONTROL
# ─────────────────────────────────────────────────────────────────

def test_partner_admin_role_access(rbac_client):
    client, _, _ = rbac_client
    headers = _get_auth_header(client, "pa@test.com")

    # PARTNER_ADMIN can access partner assigned endpoint
    assert client.get("/api/v1/auth/test-partner", headers=headers).status_code == 200

    # PARTNER_ADMIN can access partner admin endpoint
    res_padmin = client.get("/api/v1/auth/test-partner-admin", headers=headers)
    assert res_padmin.status_code == 200
    assert res_padmin.json()["resource"] == "partner_administration_data"

    # PARTNER_ADMIN cannot access beneficiary endpoint -> 403
    assert client.get("/api/v1/auth/test-beneficiary", headers=headers).status_code == 403

    # PARTNER_ADMIN cannot access system admin endpoint -> 403
    assert client.get("/api/v1/auth/test-system-admin", headers=headers).status_code == 403


# ─────────────────────────────────────────────────────────────────
# 5. SYSTEM ADMIN ROLE ACCESS CONTROL
# ─────────────────────────────────────────────────────────────────

def test_system_admin_role_access(rbac_client):
    client, _, _ = rbac_client
    headers = _get_auth_header(client, "sa@test.com")

    # SYSTEM_ADMIN can access all endpoints
    assert client.get("/api/v1/auth/test-beneficiary", headers=headers).status_code == 200
    assert client.get("/api/v1/auth/test-partner", headers=headers).status_code == 200
    assert client.get("/api/v1/auth/test-partner-admin", headers=headers).status_code == 200
    res_sys = client.get("/api/v1/auth/test-system-admin", headers=headers)
    assert res_sys.status_code == 200
    assert res_sys.json()["resource"] == "system_wide_administrative_data"


# ─────────────────────────────────────────────────────────────────
# 6. CROSS-USER DATA ISOLATION
# ─────────────────────────────────────────────────────────────────

def test_cross_user_data_isolation(rbac_client):
    client, users, _ = rbac_client

    # Token for beneficiary
    headers_ben = _get_auth_header(client, "ben@test.com")
    me_ben = client.get("/api/v1/auth/me", headers=headers_ben).json()

    # Token for partner user
    headers_pu = _get_auth_header(client, "pu@test.com")
    me_pu = client.get("/api/v1/auth/me", headers=headers_pu).json()

    # Verify user A cannot retrieve user B's identity from /me with user A's token
    assert me_ben["user_id"] == users["beneficiary"].user_id
    assert me_ben["email"] == "ben@test.com"

    assert me_pu["user_id"] == users["partner_user"].user_id
    assert me_pu["email"] == "pu@test.com"

    assert me_ben["user_id"] != me_pu["user_id"]
