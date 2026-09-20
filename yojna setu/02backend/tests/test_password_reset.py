import os
import sys
import hashlib
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.security import hash_password, verify_password
from app.db.base_class import Base
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.password_reset import PasswordResetToken


@pytest.fixture
def client_and_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    # Seed test user
    test_user = User(
        user_id="test-citizen-user",
        email="citizen@yojnasetu.org",
        phone="9876543210",
        full_name="Rajesh Kumar",
        hashed_password=hash_password("OldPassword@123"),
        role=UserRole.BENEFICIARY.value,
        is_active=True,
    )
    session.add(test_user)
    session.commit()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client, session

    app.dependency_overrides.clear()
    session.close()


def test_forgot_password_existing_email_creates_token_and_returns_generic_message(client_and_session):
    client, session = client_and_session

    response = client.post("/api/v1/auth/forgot-password", json={"email": "citizen@yojnasetu.org"})
    assert response.status_code == 200
    data = response.json()
    assert "If an account exists for this email" in data["message"]

    # Verify token was stored in DB as a SHA-256 hash
    tokens = session.query(PasswordResetToken).filter(PasswordResetToken.user_id == "test-citizen-user").all()
    assert len(tokens) == 1
    assert tokens[0].is_used is False
    assert len(tokens[0].token_hash) == 64  # SHA-256 hex string


def test_forgot_password_non_existing_email_anti_enumeration(client_and_session):
    client, session = client_and_session

    response = client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent@example.com"})
    assert response.status_code == 200
    data = response.json()
    # Must return exact same message to prevent enumeration
    assert "If an account exists for this email" in data["message"]

    # Verify no token was created
    tokens = session.query(PasswordResetToken).all()
    assert len(tokens) == 0


def test_forgot_password_invalid_email_format(client_and_session):
    client, _ = client_and_session
    response = client.post("/api/v1/auth/forgot-password", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_forgot_password_rate_limiting(client_and_session):
    client, session = client_and_session

    # First request
    r1 = client.post("/api/v1/auth/forgot-password", json={"email": "citizen@yojnasetu.org"})
    assert r1.status_code == 200

    # Rapid second request within 60s
    r2 = client.post("/api/v1/auth/forgot-password", json={"email": "citizen@yojnasetu.org"})
    assert r2.status_code == 200

    # Still only 1 token created due to rate-limit deduplication
    tokens = session.query(PasswordResetToken).filter(PasswordResetToken.user_id == "test-citizen-user").all()
    assert len(tokens) == 1


def test_verify_reset_token_valid(client_and_session):
    client, session = client_and_session

    raw_token = "secure-random-token-xyz-1234567890"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    token_record = PasswordResetToken(
        user_id="test-citizen-user",
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=False,
    )
    session.add(token_record)
    session.commit()

    resp = client.get(f"/api/v1/auth/verify-reset-token?token={raw_token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert "citizen" in data["email"] or "***" in data["email"]


def test_verify_reset_token_invalid_or_expired(client_and_session):
    client, session = client_and_session

    # 1. Non-existent token
    resp = client.get("/api/v1/auth/verify-reset-token?token=unknown-token-123456789")
    assert resp.status_code == 200
    assert resp.json()["valid"] is False

    # 2. Expired token
    raw_token = "expired-token-xyz-1234567890"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    session.add(PasswordResetToken(user_id="test-citizen-user", token_hash=token_hash, expires_at=expired_at, is_used=False))
    session.commit()

    resp = client.get(f"/api/v1/auth/verify-reset-token?token={raw_token}")
    assert resp.status_code == 200
    assert resp.json()["valid"] is False
    assert "expired" in resp.json()["message"].lower()


def test_reset_password_end_to_end(client_and_session):
    client, session = client_and_session

    raw_token = "valid-reset-token-for-citizen-12345"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    session.add(PasswordResetToken(
        user_id="test-citizen-user",
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=False,
    ))
    session.commit()

    # Reset password with valid new password
    new_password = "NewStrongPassword@2026"
    resp = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": new_password,
    })
    assert resp.status_code == 200
    assert "Password reset successfully" in resp.json()["message"]

    # Verify token is now marked used
    token_record = session.query(PasswordResetToken).filter_by(token_hash=token_hash).first()
    assert token_record.is_used is True

    # Verify user password hash was updated
    user = session.query(User).filter_by(user_id="test-citizen-user").first()
    assert verify_password(new_password, user.hashed_password)
    assert not verify_password("OldPassword@123", user.hashed_password)

    # Verify old password login fails
    login_old = client.post("/api/v1/auth/login", json={
        "identifier": "citizen@yojnasetu.org",
        "password": "OldPassword@123",
    })
    assert login_old.status_code == 401

    # Verify new password login succeeds
    login_new = client.post("/api/v1/auth/login", json={
        "identifier": "citizen@yojnasetu.org",
        "password": new_password,
    })
    assert login_new.status_code == 200
    assert "access_token" in login_new.json()

    # Verify token cannot be reused
    reuse_attempt = client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "AnotherPassword@999",
    })
    assert reuse_attempt.status_code == 400
