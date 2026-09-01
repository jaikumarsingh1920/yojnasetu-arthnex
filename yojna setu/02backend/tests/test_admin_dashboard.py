import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.models import Base
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
def db():
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

    # Seed Admin, Beneficiary, and Partner users
    admin_user = User(
        user_id="user-admin-001",
        email="sysadmin@yojnasetu.gov.in",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.SYSTEM_ADMIN.value,
        is_active=True
    )
    beneficiary_user = User(
        user_id="user-ben-001",
        email="beneficiary@example.com",
        hashed_password=hash_password("BenPass123!"),
        role=UserRole.BENEFICIARY.value,
        is_active=True
    )
    partner_user = User(
        user_id="user-partner-001",
        email="partner@agency.gov.in",
        hashed_password=hash_password("PartnerPass123!"),
        role=UserRole.PARTNER_USER.value,
        is_active=True
    )
    session.add_all([admin_user, beneficiary_user, partner_user])
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
def admin_headers(db):
    token = create_access_token(user_id="user-admin-001", role=UserRole.SYSTEM_ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def beneficiary_headers(db):
    token = create_access_token(user_id="user-ben-001", role=UserRole.BENEFICIARY.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def partner_headers(db):
    token = create_access_token(user_id="user-partner-001", role=UserRole.PARTNER_USER.value)
    return {"Authorization": f"Bearer {token}"}


def test_admin_rbac_access_control(db, admin_headers, beneficiary_headers, partner_headers):
    """Verify strict server-side RBAC access control for admin endpoints."""
    # 1. Unauthenticated -> 401
    resp1 = client.get("/api/v1/admin/dashboard")
    assert resp1.status_code == 401

    # 2. Beneficiary -> 403
    resp2 = client.get("/api/v1/admin/dashboard", headers=beneficiary_headers)
    assert resp2.status_code == 403

    # 3. Partner User -> 403
    resp3 = client.get("/api/v1/admin/dashboard", headers=partner_headers)
    assert resp3.status_code == 403

    # 4. System Admin -> 200
    resp4 = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert resp4.status_code == 200


def test_admin_dashboard_summary_metrics(db, admin_headers):
    """Verify Dashboard Summary API returns accurate database governance metrics without application tracking."""
    res = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_schemes"] >= 90
    assert data["verified_schemes"] >= 90
    assert data["total_rules"] >= 126
    assert data["total_documents"] >= 98
    assert data["total_ministries"] >= 10
    assert data["total_changelogs"] >= 200
    assert data["avg_parameter_completeness"] > 0.0
    assert "system_health" in data
    assert data["system_health"]["overall_status"] == "ONLINE"

    # Verify out-of-scope application tracking fields are strictly removed
    assert "applications_total" not in data
    assert "applications_by_status" not in data
    assert "pending_document_verifications" not in data


def test_removed_admin_application_processing_endpoints(db, admin_headers):
    """Verify that out-of-scope application processing endpoints have been removed from admin router."""
    resp1 = client.get("/api/v1/admin/applications", headers=admin_headers)
    assert resp1.status_code == 404

    resp2 = client.get("/api/v1/admin/applications/stats", headers=admin_headers)
    assert resp2.status_code == 404

    resp3 = client.post("/api/v1/admin/applications/app-123/reassign", headers=admin_headers, json={})
    assert resp3.status_code == 404


def test_scheme_audit_list(db, admin_headers):
    """Verify Scheme Audit List API returns schemes with VERIFIED status and completeness scores."""
    res = client.get("/api/v1/admin/schemes?page_size=100", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total"] >= 90
    assert len(data["items"]) >= 90

    # Verify schemes maintain VERIFIED status
    for item in data["items"]:
        assert item["verification_status"] == "VERIFIED"
        assert item["completeness_score"] >= 0.0
        assert item["rule_count"] >= 0
        assert item["document_count"] >= 0


def test_scheme_audit_detail(db, admin_headers):
    """Verify Scheme Audit Detail API returns parameter completeness, rules, documents, and data quality warnings."""
    res = client.get("/api/v1/admin/schemes/SIH26092-052", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["scheme_id"] == "SIH26092-052"
    assert data["verification_status"] == "VERIFIED"
    assert "known_fields" in data
    assert "unknown_fields" in data
    assert "rules" in data
    assert "documents" in data
    assert "data_quality_warnings" in data

    # Verify data quality warnings use "Parameter requires completion", NOT "unverified"
    for warn in data["data_quality_warnings"]:
        assert "unverified" not in warn.lower()


def test_rule_audit_list(db, admin_headers):
    """Verify Rule Audit List API returns database rules."""
    res = client.get("/api/v1/admin/rules?page_size=100", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total"] >= 126
    assert len(data["items"]) >= 100
    assert "field" in data["items"][0]
    assert "operator" in data["items"][0]


def test_document_audit_list(db, admin_headers):
    """Verify Document Audit List API returns document requirements."""
    res = client.get("/api/v1/admin/documents?page_size=100", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total"] >= 98
    assert len(data["items"]) >= 98
    assert "document_name" in data["items"][0]


def test_system_health_observability(db, admin_headers):
    """Verify System Health Endpoint returns real operational health indicators."""
    res = client.get("/api/v1/admin/system-health", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["overall_status"] == "ONLINE"
    assert len(data["components"]) >= 4

    comp_names = [c["name"] for c in data["components"]]
    assert "PostgreSQL Database" in comp_names
    assert "Deterministic Eligibility Engine" in comp_names
    assert "Deterministic Financial Engine" in comp_names
    assert "YojnaSetu AI & RAG Engine" in comp_names
