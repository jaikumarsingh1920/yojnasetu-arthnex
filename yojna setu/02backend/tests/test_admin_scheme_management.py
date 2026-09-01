import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.models import Base, Scheme, SchemeChangelog
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

client = TestClient(app)


@pytest.fixture(scope="module")
def test_db():
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

    # Seed Admin and Beneficiary users
    admin_user = User(
        user_id="user-admin-mgmt",
        email="sysadmin@yojnasetu.gov.in",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.SYSTEM_ADMIN.value,
        is_active=True
    )
    beneficiary_user = User(
        user_id="user-ben-mgmt",
        email="citizen@example.com",
        hashed_password=hash_password("CitizenPass123!"),
        role=UserRole.BENEFICIARY.value,
        is_active=True
    )
    session.add_all([admin_user, beneficiary_user])
    session.commit()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session
    app.dependency_overrides.clear()
    session.close()


@pytest.fixture(scope="module")
def admin_headers(test_db):
    token = create_access_token(user_id="user-admin-mgmt", role=UserRole.SYSTEM_ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def beneficiary_headers(test_db):
    token = create_access_token(user_id="user-ben-mgmt", role=UserRole.BENEFICIARY.value)
    return {"Authorization": f"Bearer {token}"}


def test_admin_create_scheme_success(test_db, admin_headers):
    """Admin can create a new scheme with full validation and audit logging."""
    payload = {
        "scheme_id": "SIH26092-999",
        "scheme_name": "National Digital Artisan Support Scheme",
        "ministry": "Ministry of Micro, Small & Medium Enterprises",
        "scheme_type": "Skill Training & Financial Inclusion",
        "purpose": "Comprehensive digital toolkits and concessional credit support for rural artisans.",
        "target_beneficiary": "Rural Artisans & Craftsmen",
        "marginalized_group": "ARTISANS",
        "social_category": "ALL",
        "gender_condition": "ALL",
        "state_restriction": "ALL_INDIA",
        "state_coverage": "All India",
        "loan_available": "YES",
        "minimum_loan_amount": 25000.0,
        "maximum_loan_amount": 200000.0,
        "interest_rate_min": 5.0,
        "interest_rate_max": 8.5,
        "repayment_period_max_months": 36,
        "subsidy_available": "YES",
        "subsidy_percentage": 25.0,
        "application_mode": "ONLINE",
        "official_source_url": "https://msme.gov.in/schemes/artisan-support",
        "official_portal": "https://artisanportal.gov.in/",
        "required_documents": "Aadhaar Card; Artisan Card; Bank Passbook",
        "verification_status": "VERIFIED",
        "scheme_status": "ACTIVE",
        "reason": "New national pilot scheme registration"
    }

    res = client.post("/api/v1/admin/schemes", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["scheme_id"] == "SIH26092-999"
    assert data["scheme_name"] == "National Digital Artisan Support Scheme"

    # Verify DB persistence
    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-999").first()
    assert scheme is not None
    assert scheme.scheme_status == "ACTIVE"
    assert scheme.max_loan_amount == 200000.0

    # Verify Changelog record
    cl = test_db.query(SchemeChangelog).filter(
        SchemeChangelog.scheme_id == "SIH26092-999",
        SchemeChangelog.action == "CREATE"
    ).first()
    assert cl is not None
    assert cl.admin_identifier == "sysadmin@yojnasetu.gov.in"


def test_admin_create_scheme_validation_failure(test_db, admin_headers):
    """Validation rejects invalid URLs, duplicate IDs, and invalid loan ranges."""
    # 1. Duplicate Scheme ID
    duplicate_payload = {
        "scheme_id": "SIH26092-999",
        "scheme_name": "Another Scheme",
        "ministry": "Ministry of Finance",
        "official_source_url": "https://finmin.gov.in/schemes",
        "loan_available": "NO"
    }
    res_dup = client.post("/api/v1/admin/schemes", json=duplicate_payload, headers=admin_headers)
    assert res_dup.status_code == 400

    # 2. Invalid Official Source URL (not http/https)
    invalid_url_payload = {
        "scheme_id": "SIH26092-998",
        "scheme_name": "Invalid URL Scheme",
        "ministry": "Ministry of MSME",
        "official_source_url": "not-a-valid-url",
        "loan_available": "NO"
    }
    res_url = client.post("/api/v1/admin/schemes", json=invalid_url_payload, headers=admin_headers)
    assert res_url.status_code == 422

    # 3. Min loan amount > Max loan amount
    invalid_range_payload = {
        "scheme_id": "SIH26092-997",
        "scheme_name": "Invalid Range Scheme",
        "ministry": "Ministry of MSME",
        "official_source_url": "https://msme.gov.in/test",
        "loan_available": "YES",
        "minimum_loan_amount": 500000.0,
        "maximum_loan_amount": 100000.0
    }
    res_range = client.post("/api/v1/admin/schemes", json=invalid_range_payload, headers=admin_headers)
    assert res_range.status_code == 422


def test_admin_update_scheme_success(test_db, admin_headers):
    """Admin can edit an existing scheme and generate granular changelog history."""
    update_payload = {
        "scheme_name": "National Digital Artisan Support Scheme (Revised 2026)",
        "maximum_loan_amount": 250000.0,
        "subsidy_percentage": 30.0,
        "change_reason": "Statutory limit enhancement under Budget 2026 notification"
    }

    res = client.put("/api/v1/admin/schemes/SIH26092-999", json=update_payload, headers=admin_headers)
    assert res.status_code == 200

    # Verify DB update
    scheme = test_db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-999").first()
    assert scheme.scheme_name == "National Digital Artisan Support Scheme (Revised 2026)"
    assert scheme.max_loan_amount == 250000.0
    assert scheme.subsidy_percentage == 30.0

    # Verify Changelog records for changed fields
    changelogs = test_db.query(SchemeChangelog).filter(
        SchemeChangelog.scheme_id == "SIH26092-999",
        SchemeChangelog.action == "UPDATE"
    ).all()
    assert len(changelogs) >= 2
    fields_changed = {c.field for c in changelogs}
    assert "scheme_name" in fields_changed
    assert "maximum_loan_amount" in fields_changed or "max_loan_amount" in fields_changed


def test_admin_scheme_lifecycle_deactivate_and_activate(test_db, admin_headers):
    """Deactivating a scheme hides it from public routes, and activating restores it."""
    # 1. Verify scheme is currently in public directory
    res_pub_before = client.get("/api/v1/schemes?search=SIH26092-999")
    assert res_pub_before.status_code == 200
    assert any(s["scheme_id"] == "SIH26092-999" for s in res_pub_before.json()["items"])

    # 2. Deactivate scheme
    deact_res = client.patch(
        "/api/v1/admin/schemes/SIH26092-999/status",
        json={"status": "INACTIVE", "reason": "Pilot scheme funding window closed"},
        headers=admin_headers
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["scheme_status"] == "INACTIVE"

    # Verify changelog has DEACTIVATE action
    deact_cl = test_db.query(SchemeChangelog).filter(
        SchemeChangelog.scheme_id == "SIH26092-999",
        SchemeChangelog.action == "DEACTIVATE"
    ).first()
    assert deact_cl is not None

    # 3. Verify deactivated scheme is hidden from public directory
    res_pub_after = client.get("/api/v1/schemes?search=SIH26092-999")
    assert res_pub_after.status_code == 200
    assert not any(s["scheme_id"] == "SIH26092-999" for s in res_pub_after.json()["items"])

    # 4. Verify deactivated scheme detail returns 404 to public citizen
    res_detail = client.get("/api/v1/schemes/SIH26092-999")
    assert res_detail.status_code == 404

    # 5. Verify admin CAN still view it in Admin Scheme Audit
    res_admin = client.get("/api/v1/admin/schemes/SIH26092-999", headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.json()["scheme_id"] == "SIH26092-999"

    # 6. Re-activate scheme
    act_res = client.patch(
        "/api/v1/admin/schemes/SIH26092-999/status",
        json={"status": "ACTIVE", "reason": "Pilot funding renewed"},
        headers=admin_headers
    )
    assert act_res.status_code == 200
    assert act_res.json()["scheme_status"] == "ACTIVE"

    # 7. Verify scheme is back in public directory
    res_restored = client.get("/api/v1/schemes?search=SIH26092-999")
    assert res_restored.status_code == 200
    assert any(s["scheme_id"] == "SIH26092-999" for s in res_restored.json()["items"])


def test_admin_rbac_enforcement(test_db, beneficiary_headers):
    """Non-admin citizens cannot create, update, or change scheme status."""
    res_post = client.post(
        "/api/v1/admin/schemes",
        json={"scheme_id": "SIH26092-HACK", "scheme_name": "Hack", "ministry": "Fake", "official_source_url": "https://gov.in", "loan_available": "NO"},
        headers=beneficiary_headers
    )
    assert res_post.status_code == 403

    res_put = client.put(
        "/api/v1/admin/schemes/SIH26092-001",
        json={"scheme_name": "Tampered Name"},
        headers=beneficiary_headers
    )
    assert res_put.status_code == 403

    res_patch = client.patch(
        "/api/v1/admin/schemes/SIH26092-001/status",
        json={"status": "INACTIVE"},
        headers=beneficiary_headers
    )
    assert res_patch.status_code == 403
