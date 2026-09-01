import os
import sys
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.models import Base, User, UserRole, Scheme, SchemeVerification, Partner, Application, ApplicationDocument, ApplicationStatus, DocumentVerificationStatus, AuditLog
from app.db.session import get_db
from app.core.security import create_access_token, hash_password


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()

    # Seed test users
    pass_hash = hash_password("Password123!")

    partner_org = Partner(
        partner_id="PARTNER-001",
        name="State Channelizing Agency",
        code="SCA01",
        partner_type="STATE_AGENCY",
        is_active=True
    )
    session.add(partner_org)

    ben_user = User(
        user_id="USER-BEN-01",
        email="ben@test.com",
        phone="9876543210",
        hashed_password=pass_hash,
        role=UserRole.BENEFICIARY.value,
        is_active=True
    )
    partner_user = User(
        user_id="USER-PARTNER-01",
        email="partner@test.com",
        hashed_password=pass_hash,
        role=UserRole.PARTNER_USER.value,
        partner_id="PARTNER-001",
        is_active=True
    )
    partner_admin = User(
        user_id="USER-PADMIN-01",
        email="padmin@test.com",
        hashed_password=pass_hash,
        role=UserRole.PARTNER_ADMIN.value,
        partner_id="PARTNER-001",
        is_active=True
    )
    sys_admin = User(
        user_id="USER-SYSADMIN-01",
        email="admin@test.com",
        hashed_password=pass_hash,
        role=UserRole.SYSTEM_ADMIN.value,
        is_active=True
    )
    session.add_all([ben_user, partner_user, partner_admin, sys_admin])

    # Seed test scheme
    scheme = Scheme(
        scheme_id="SCHEME-TEST-01",
        scheme_name="Test Welfare Scheme",
        ministry="Ministry of Social Justice",
        implementing_agency="NSFDC",
        scheme_type="CENTRAL",
        sector="MICRO_FINANCE"
    )
    scheme_verif = SchemeVerification(
        id="VERIF-01",
        scheme_id="SCHEME-TEST-01",
        verification_status="VERIFIED"
    )
    session.add_all([scheme, scheme_verif])

    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)


@pytest.fixture
def client(db):
    def _get_db_override():
        return db
    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def get_token_headers(user_id: str, role: str) -> dict:
    token = create_access_token(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_rbac_and_partner_access_control(client: TestClient, db: Session):
    """Test 1-4: Auth & RBAC isolation."""
    ben_headers = get_token_headers("USER-BEN-01", UserRole.BENEFICIARY.value)
    partner_headers = get_token_headers("USER-PARTNER-01", UserRole.PARTNER_USER.value)
    admin_headers = get_token_headers("USER-SYSADMIN-01", UserRole.SYSTEM_ADMIN.value)

    # Beneficiary accessing partner route -> 403
    res = client.get("/api/v1/partner/applications", headers=ben_headers)
    assert res.status_code == 403

    # Partner accessing admin route -> 403
    res = client.get("/api/v1/admin/dashboard", headers=partner_headers)
    assert res.status_code == 403

    # System Admin accessing admin route -> 200
    res = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200


def test_full_end_to_end_lifecycle_with_corrections(client: TestClient, db: Session):
    """Test 5-20: Full lifecycle: Draft -> Submit -> Review -> Correction -> Resubmit -> Verify -> Approve."""
    ben_headers = get_token_headers("USER-BEN-01", UserRole.BENEFICIARY.value)
    partner_headers = get_token_headers("USER-PARTNER-01", UserRole.PARTNER_USER.value)
    padmin_headers = get_token_headers("USER-PADMIN-01", UserRole.PARTNER_ADMIN.value)
    admin_headers = get_token_headers("USER-SYSADMIN-01", UserRole.SYSTEM_ADMIN.value)

    # 1. Create Application
    create_payload = {
        "scheme_id": "SCHEME-TEST-01",
        "profile": {
            "age": 28,
            "annual_income": 150000.0,
            "social_category": "SC",
            "gender": "FEMALE",
            "state": "UTTAR_PRADESH",
            "sector": "MICRO_FINANCE",
            "project_cost": 100000.0,
            "requested_loan_amount": 90000.0
        }
    }
    res = client.post("/api/v1/applications", json=create_payload, headers=ben_headers)
    assert res.status_code == 201
    app_data = res.json()
    app_id = app_data["application_id"]
    assert app_data["status"] in ("READY_FOR_SUBMISSION", "DRAFT", "DOCUMENTS_PENDING")

    # 2. Submit Application
    res = client.post(f"/api/v1/applications/{app_id}/submit", headers=ben_headers, json={"partner_id": "PARTNER-001"})
    assert res.status_code == 200
    assert res.json()["status"] == "SUBMITTED"

    # 3. Partner Start Review
    res = client.post(f"/api/v1/partner/applications/{app_id}/start-review", headers=partner_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "UNDER_REVIEW"

    # 4. Request Correction from Partner
    res = client.post(
        f"/api/v1/partner/applications/{app_id}/request-correction",
        json={"reason": "Aadhaar Card copy is blurry. Please upload clear scan.", "correction_fields": ["Identity Proof"]},
        headers=partner_headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CORRECTION_REQUIRED"

    # 5. Beneficiary Resubmits Application after correction
    res = client.post(f"/api/v1/applications/{app_id}/submit", headers=ben_headers, json={"partner_id": "PARTNER-001"})
    assert res.status_code == 200
    assert res.json()["status"] == "SUBMITTED"

    # 6. Partner Re-initiates Review
    res = client.post(f"/api/v1/partner/applications/{app_id}/start-review", headers=partner_headers)
    assert res.status_code == 200

    # 7. Approve Application from Partner Admin
    res = client.post(f"/api/v1/partner/applications/{app_id}/approve", headers=padmin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

    # 8. Check Partner Queue Status
    res = client.get("/api/v1/partner/applications?status=APPROVED", headers=padmin_headers)
    assert res.status_code == 200
    apps = res.json()["items"]
    assert any(a["application_id"] == app_id for a in apps)


def test_rejection_workflow(client: TestClient, db: Session):
    """Test rejection lifecycle."""
    ben_headers = get_token_headers("USER-BEN-01", UserRole.BENEFICIARY.value)
    padmin_headers = get_token_headers("USER-PADMIN-01", UserRole.PARTNER_ADMIN.value)

    res = client.post("/api/v1/applications", json={
        "scheme_id": "SCHEME-TEST-01",
        "profile": {"age": 28, "annual_income": 150000.0, "social_category": "SC", "gender": "FEMALE", "state": "UP", "sector": "MICRO_FINANCE", "project_cost": 100000.0, "requested_loan_amount": 90000.0}
    }, headers=ben_headers)
    app_id = res.json()["application_id"]

    client.post(f"/api/v1/applications/{app_id}/submit", headers=ben_headers, json={"partner_id": "PARTNER-001"})
    client.post(f"/api/v1/partner/applications/{app_id}/start-review", headers=padmin_headers)

    res = client.post(f"/api/v1/partner/applications/{app_id}/reject", json={"reason": "Project cost exceeds threshold."}, headers=padmin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"
