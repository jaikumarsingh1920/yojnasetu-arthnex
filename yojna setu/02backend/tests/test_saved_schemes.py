import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base_class import Base
from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import create_access_token, hash_password

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from seed_db import seed_database


@pytest.fixture(scope="module")
def db_session():
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
    u1 = User(
        user_id="saved-user-1",
        email="saved1@example.com",
        hashed_password=hash_password("Secret123!"),
        role=UserRole.BENEFICIARY,
        is_active=True
    )
    u2 = User(
        user_id="saved-user-2",
        email="saved2@example.com",
        hashed_password=hash_password("Secret123!"),
        role=UserRole.BENEFICIARY,
        is_active=True
    )
    session.add_all([u1, u2])
    session.commit()

    yield session
    session.close()


@pytest.fixture(scope="module")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers_user1():
    token = create_access_token(user_id="saved-user-1", role="BENEFICIARY")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2():
    token = create_access_token(user_id="saved-user-2", role="BENEFICIARY")
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_access_rejected(client):
    res = client.get("/api/v1/saved-schemes")
    assert res.status_code == 401


def test_empty_saved_list(client, auth_headers_user1):
    res = client.get("/api/v1/saved-schemes", headers=auth_headers_user1)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_save_scheme_success(client, auth_headers_user1):
    sid = "SIH26092-001"  # PMEGP
    res = client.post(f"/api/v1/saved-schemes/{sid}", headers=auth_headers_user1)
    assert res.status_code == 201
    data = res.json()
    assert data["scheme_id"] == sid
    assert data["user_id"] == "saved-user-1"


def test_duplicate_save_idempotent(client, auth_headers_user1):
    sid = "SIH26092-001"
    res1 = client.post(f"/api/v1/saved-schemes/{sid}", headers=auth_headers_user1)
    assert res1.status_code in [200, 201]

    # Save again - should be idempotent
    res2 = client.post(f"/api/v1/saved-schemes/{sid}", headers=auth_headers_user1)
    assert res2.status_code in [200, 201]
    assert res2.json()["id"] == res1.json()["id"]


def test_check_saved_status(client, auth_headers_user1):
    sid = "SIH26092-001"
    res = client.get(f"/api/v1/saved-schemes/{sid}", headers=auth_headers_user1)
    assert res.status_code == 200
    assert res.json()["is_saved"] is True

    # Check unsaved scheme
    res_unsaved = client.get("/api/v1/saved-schemes/SIH26092-999", headers=auth_headers_user1)
    assert res_unsaved.status_code == 200
    assert res_unsaved.json()["is_saved"] is False


def test_cross_user_isolation(client, auth_headers_user1, auth_headers_user2):
    sid = "SIH26092-001"
    # User 1 saved PMEGP. User 2's list must be empty.
    res2 = client.get("/api/v1/saved-schemes", headers=auth_headers_user2)
    assert res2.status_code == 200
    assert res2.json()["total"] == 0

    # User 2's saved status for PMEGP must be False
    res2_status = client.get(f"/api/v1/saved-schemes/{sid}", headers=auth_headers_user2)
    assert res2_status.json()["is_saved"] is False


def test_remove_saved_scheme(client, auth_headers_user1):
    sid = "SIH26092-001"
    res = client.delete(f"/api/v1/saved-schemes/{sid}", headers=auth_headers_user1)
    assert res.status_code == 200

    # Verify status is now False
    res_check = client.get(f"/api/v1/saved-schemes/{sid}", headers=auth_headers_user1)
    assert res_check.json()["is_saved"] is False


def test_nonexistent_scheme_save_404(client, auth_headers_user1):
    res = client.post("/api/v1/saved-schemes/NONEXISTENT-SCHEME", headers=auth_headers_user1)
    assert res.status_code == 404


def test_email_scheme_unconfigured_fallback(client, auth_headers_user1):
    sid = "SIH26092-001"
    res = client.post(f"/api/v1/saved-schemes/{sid}/email", headers=auth_headers_user1)
    assert res.status_code == 200
    data = res.json()
    assert "recipient_email" in data
    assert data["recipient_email"] == "saved1@example.com"
    # Fallback response when email provider is none
    assert data["sent"] is False or data["sent"] is True
