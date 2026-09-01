"""
TESTS FOR GOOGLE AUTHENTICATION (OAUTH 2.0 / OPENID CONNECT)
Mocks Google token verification to test all token validation branches, account creation,
same-email account linking, and RBAC token session issuance without calling live Google endpoints.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from app.main import app
from app.services.google_auth_service import GoogleUserInfo
from app.models.user import User, UserRole
from app.db.session import SessionLocal

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_google_login_new_user_creation(db_session):
    """
    Test that a valid Google ID token for a new citizen creates a BENEFICIARY user
    and returns a valid YojnaSetu JWT access token.
    """
    mock_info = GoogleUserInfo(
        google_id="google-sub-1001",
        email="new.google.citizen@example.com",
        email_verified=True,
        full_name="Rajesh Kumar",
        avatar_url="https://lh3.googleusercontent.com/a/photo1"
    )

    # Clean up prior test data if exists
    existing = db_session.query(User).filter(User.email == mock_info.email).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    with patch("app.api.v1.endpoints.auth.verify_google_id_token", return_value=mock_info):
        resp = client.post("/api/v1/auth/google", json={
            "id_token": "valid.sample.id_token",
            "preferred_language": "hi"
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "new.google.citizen@example.com"
    assert data["user"]["role"] == "BENEFICIARY"
    assert data["user"]["full_name"] == "Rajesh Kumar"
    assert data["user"]["avatar_url"] == "https://lh3.googleusercontent.com/a/photo1"
    assert data["user"]["auth_provider"] == "GOOGLE"

    # Verify protected route works with the issued access token
    token = data["access_token"]
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "new.google.citizen@example.com"


def test_google_login_existing_google_user(db_session):
    """
    Test that subsequent Google logins for an existing Google user succeed and return fresh JWT.
    """
    mock_info = GoogleUserInfo(
        google_id="google-sub-1001",
        email="new.google.citizen@example.com",
        email_verified=True,
        full_name="Rajesh Kumar",
        avatar_url="https://lh3.googleusercontent.com/a/photo1"
    )

    with patch("app.api.v1.endpoints.auth.verify_google_id_token", return_value=mock_info):
        resp = client.post("/api/v1/auth/google", json={
            "id_token": "valid.sample.id_token"
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "new.google.citizen@example.com"


def test_google_account_linking_same_verified_email(db_session):
    """
    Test that if a citizen originally registered via password with email 'priya@example.com',
    logging in via Google with the same email safely links the accounts without duplication.
    """
    # 1. Create standard password user
    register_resp = client.post("/api/v1/auth/register", json={
        "email": "priya.sharma@example.com",
        "password": "SecurePassword123!",
        "preferred_language": "mr"
    })
    # Either created or already exists
    assert register_resp.status_code in (201, 400)

    # 2. Login with Google using same email
    mock_info = GoogleUserInfo(
        google_id="google-sub-2002",
        email="priya.sharma@example.com",
        email_verified=True,
        full_name="Priya Sharma",
        avatar_url="https://lh3.googleusercontent.com/a/photo2"
    )

    with patch("app.api.v1.endpoints.auth.verify_google_id_token", return_value=mock_info):
        google_resp = client.post("/api/v1/auth/google", json={
            "id_token": "valid.priya.id_token"
        })

    assert google_resp.status_code == 200
    data = google_resp.json()
    assert data["user"]["email"] == "priya.sharma@example.com"
    assert data["user"]["full_name"] == "Priya Sharma"

    # Verify no duplicate user was created in database
    users_with_email = db_session.query(User).filter(User.email == "priya.sharma@example.com").all()
    assert len(users_with_email) == 1
    assert users_with_email[0].google_id == "google-sub-2002"


def test_google_login_unverified_email_rejection():
    """
    Test that Google accounts with unverified emails are strictly rejected.
    """
    from app.core.config import settings
    with patch("app.services.google_auth_service.get_jwk_client") as mock_jwks:
        mock_jwks.side_effect = Exception("Fallback to tokeninfo")
        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "sub": "google-unverified-123",
                "email": "unverified@example.com",
                "email_verified": "false",
                "aud": settings.GOOGLE_CLIENT_ID or "test-client-id",
                "iss": "https://accounts.google.com"
            }

            resp = client.post("/api/v1/auth/google", json={"id_token": "unverified.id.token"})
            assert resp.status_code == 400
            assert "verified" in resp.json()["detail"].lower()


def test_google_login_invalid_token():
    """
    Test that invalid/malformed Google tokens are rejected with 401.
    """
    with patch("app.services.google_auth_service.get_jwk_client") as mock_jwks:
        mock_jwks.side_effect = Exception("Invalid signature")
        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value.status_code = 400
            mock_get.return_value.json.return_value = {"error_description": "Invalid Value"}

            resp = client.post("/api/v1/auth/google", json={"id_token": "malformed.token"})
            assert resp.status_code == 401


def test_google_login_invalid_issuer():
    """
    Test that tokens from unknown issuers are rejected.
    """
    from app.core.config import settings
    with patch("app.services.google_auth_service.get_jwk_client") as mock_jwks:
        mock_jwks.side_effect = Exception("Fallback")
        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "sub": "google-bad-iss",
                "email": "hacker@example.com",
                "email_verified": "true",
                "aud": settings.GOOGLE_CLIENT_ID or "test-client-id",
                "iss": "https://evil-issuer.com"
            }

            resp = client.post("/api/v1/auth/google", json={"id_token": "bad.issuer.token"})
            assert resp.status_code == 401
            assert "issuer" in resp.json()["detail"].lower()


def test_google_login_empty_token():
    """
    Test that missing id_token is rejected with 422 Unprocessable Entity.
    """
    resp = client.post("/api/v1/auth/google", json={})
    assert resp.status_code == 422
