import pytest
import os
import sys
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from sqlalchemy.pool import StaticPool
from app.main import app
from app.models import Base, User, UserRole
from app.db.session import get_db
from app.core.security import hash_password, verify_password, create_access_token


@pytest.fixture(scope="module")
def test_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed database with schemes and development test accounts
    session = TestingSessionLocal()
    from seed_db import seed_database
    seed_database(session)
    session.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, TestingSessionLocal
    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────
# 1. PASSWORD SECURITY TESTS
# ─────────────────────────────────────────────────────────────────

def test_password_hashing_security():
    """Verify plaintext password is never stored and bcrypt hashing operates correctly."""
    password = "MySecurePassword123!"
    hashed = hash_password(password)

    # 1. Plaintext is not stored
    assert password not in hashed
    assert hashed != password

    # 2. Hash differs from original password and has bcrypt prefix
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    # 3. Verification succeeds for correct password
    assert verify_password(password, hashed) is True

    # 4. Verification fails for incorrect password
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


# ─────────────────────────────────────────────────────────────────
# 2. USER REGISTRATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_successful_user_registration(test_client):
    client, _ = test_client
    payload = {
        "email": "beneficiary1@example.com",
        "phone": "9876543210",
        "password": "Password123!",
        "role": "BENEFICIARY"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "beneficiary1@example.com"
    assert data["phone"] == "9876543210"
    assert data["role"] == "BENEFICIARY"
    assert data["is_active"] is True
    assert "user_id" in data
    # Password hash must not be leaked in response
    assert "hashed_password" not in data
    assert "password" not in data


def test_duplicate_registration_rejection(test_client):
    client, _ = test_client
    # Attempt registering with duplicate email
    payload_dup_email = {
        "email": "beneficiary1@example.com",
        "phone": "9111111111",
        "password": "Password123!"
    }
    res_email = client.post("/api/v1/auth/register", json=payload_dup_email)
    assert res_email.status_code == 400
    assert "already exists" in res_email.json()["detail"].lower()

    # Attempt registering with duplicate phone
    payload_dup_phone = {
        "email": "another@example.com",
        "phone": "9876543210",
        "password": "Password123!"
    }
    res_phone = client.post("/api/v1/auth/register", json=payload_dup_phone)
    assert res_phone.status_code == 400
    assert "already exists" in res_phone.json()["detail"].lower()


def test_public_registration_role_escalation_prevented(test_client):
    client, _ = test_client
    payload = {
        "email": "hacker@example.com",
        "phone": "9998887776",
        "password": "Password123!",
        "role": "SYSTEM_ADMIN"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    # Public registration MUST force BENEFICIARY role
    assert data["role"] == "BENEFICIARY"


def test_invalid_registration_payloads(test_client):
    client, _ = test_client
    # No email and no phone
    res_no_ident = client.post("/api/v1/auth/register", json={"password": "Password123!"})
    assert res_no_ident.status_code == 422  # Pydantic validation error

    # Password too short (< 8 chars)
    res_short_pwd = client.post("/api/v1/auth/register", json={
        "email": "short@example.com",
        "password": "123"
    })
    assert res_short_pwd.status_code == 422


# ─────────────────────────────────────────────────────────────────
# 3. LOGIN & TOKEN TESTS
# ─────────────────────────────────────────────────────────────────

def test_successful_login_with_email(test_client):
    client, _ = test_client
    login_payload = {
        "identifier": "beneficiary1@example.com",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600
    assert data["user"]["email"] == "beneficiary1@example.com"
    assert data["user"]["role"] == "BENEFICIARY"
    assert "hashed_password" not in data["user"]


def test_successful_login_with_phone(test_client):
    client, _ = test_client
    login_payload = {
        "identifier": "9876543210",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["phone"] == "9876543210"


def test_successful_login_with_username_field(test_client):
    client, _ = test_client
    login_payload = {
        "username": "beneficiary1@example.com",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "beneficiary1@example.com"


def test_login_incorrect_password(test_client):
    client, _ = test_client
    login_payload = {
        "identifier": "beneficiary1@example.com",
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid identifier or password" in response.json()["detail"]


def test_login_nonexistent_user(test_client):
    client, _ = test_client
    login_payload = {
        "identifier": "nonexistent@example.com",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid identifier or password" in response.json()["detail"]


def test_login_inactive_user(test_client):
    client, session_factory = test_client

    # Create inactive user directly in DB
    db = session_factory()
    inactive_user = User(
        email="inactive@example.com",
        hashed_password=hash_password("Password123!"),
        role="BENEFICIARY",
        is_active=False
    )
    db.add(inactive_user)
    db.commit()
    db.close()

    # Attempt login
    login_payload = {
        "identifier": "inactive@example.com",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"].lower()


# ─────────────────────────────────────────────────────────────────
# 4. CURRENT USER & TOKEN VALIDATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_get_current_user_me(test_client):
    client, _ = test_client
    # First login to get valid token
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "beneficiary1@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]

    # Access /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "beneficiary1@example.com"
    assert user_data["role"] == "BENEFICIARY"


def test_expired_token_rejection(test_client):
    client, _ = test_client
    # Generate token that expired 10 minutes ago
    expired_token = create_access_token(
        user_id="fake-uuid",
        role="BENEFICIARY",
        expires_delta=timedelta(minutes=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_malformed_token_rejection(test_client):
    client, _ = test_client
    headers = {"Authorization": "Bearer invalid.malformed.token"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401


def test_logout_endpoint(test_client):
    client, _ = test_client
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "beneficiary1@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Successfully logged out."


# ─────────────────────────────────────────────────────────────────
# 5. DEVELOPMENT TEST ACCOUNTS & IDEMPOTENCY TESTS
# ─────────────────────────────────────────────────────────────────

def test_development_test_accounts_login(test_client):
    client, _ = test_client

    dev_accounts = [
        ("ben10@example.com", "Secret123!", "BENEFICIARY"),
        ("p1user@example.com", "Secret123!", "PARTNER_USER"),
        ("p1admin@example.com", "Secret123!", "PARTNER_ADMIN"),
        ("admin@yojnasetu.gov.in", "Secret123!", "SYSTEM_ADMIN"),
    ]

    for email, password, expected_role in dev_accounts:
        res = client.post("/api/v1/auth/login", json={"identifier": email, "password": password})
        assert res.status_code == 200, f"Login failed for {email}"
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == email
        assert data["user"]["role"] == expected_role


def test_dev_accounts_me_and_rbac(test_client):
    client, _ = test_client

    # 1. Login as BENEFICIARY
    ben_res = client.post("/api/v1/auth/login", json={"identifier": "ben10@example.com", "password": "Secret123!"})
    ben_token = ben_res.json()["access_token"]
    ben_headers = {"Authorization": f"Bearer {ben_token}"}

    # Verify /me
    me_res = client.get("/api/v1/auth/me", headers=ben_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "ben10@example.com"
    assert me_res.json()["role"] == "BENEFICIARY"

    # Beneficiary accessing admin dashboard -> 403
    admin_access_res = client.get("/api/v1/admin/dashboard", headers=ben_headers)
    assert admin_access_res.status_code == 403

    # 2. Login as SYSTEM_ADMIN
    admin_res = client.post("/api/v1/auth/login", json={"identifier": "admin@yojnasetu.gov.in", "password": "Secret123!"})
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # System Admin accessing admin dashboard -> 200
    admin_dash_res = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert admin_dash_res.status_code == 200


def test_seed_database_idempotency(test_client):
    _, session_factory = test_client
    session = session_factory()
    from seed_db import seed_database

    # Re-run seed_database
    seed_database(session)
    session.close()

    # Verify accounts still valid
    session2 = session_factory()
    u = session2.query(User).filter(User.email == "admin@yojnasetu.gov.in").first()
    assert u is not None
    assert u.role == "SYSTEM_ADMIN"
    assert verify_password("Secret123!", u.hashed_password) is True
    session2.close()

