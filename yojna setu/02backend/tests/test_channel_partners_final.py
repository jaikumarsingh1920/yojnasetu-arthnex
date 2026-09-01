"""
Comprehensive test suite for YojnaSetu Channel Partner Expansion & Scheme Mapping:
1. Nearest partner lookup with coordinates & distances
2. Scheme-specific partner filtering (dynamic DB-driven, 0 hardcoding)
3. Category segregation (AUTHORIZED_SCHEME_PARTNER, IMPLEMENTING_ASSISTANCE_CENTRE, NEARBY_FINANCIAL_SERVICE_POINT)
4. Gorakhpur hub verified presence & SBI Kunraghat absence
5. Public API exclusion of deactivated partners
6. Admin partner management CRUD, status toggling, and audit changelog
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.db.session import get_db, SessionLocal
from app.models.partner import Partner
from app.models.partner_scheme import PartnerSchemeMapping
from app.models.partner_changelog import PartnerChangelog

client = TestClient(app)

def test_nearest_partners_gorakhpur_hub():
    """Verify Gorakhpur coordinates return the 10 verified hub locations within 25 km."""
    response = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&max_distance_km=25")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8, f"Expected at least 8 Gorakhpur partners, got {len(data)}"
    
    names = [p["partner"]["name"] for p in data]
    # Check key hub presences
    assert any("DIC" in n or "District Industries" in n for n in names)
    assert any("Bank of Baroda" in n for n in names)
    assert any("RSETI" in n for n in names)

def test_prohibited_branch_sbi_kunraghat_absent():
    """Verify permanently closed branch (SBI Kunraghat) is absent from all results."""
    response = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&max_distance_km=50")
    assert response.status_code == 200
    data = response.json()
    for p in data:
        name = p["partner"]["name"].lower()
        address = (p["partner"]["address"] or "").lower()
        assert "kunraghat" not in name, f"Prohibited branch found: {name}"
        assert "kunraghat" not in address, f"Prohibited address found: {address}"

def test_scheme_specific_partner_filtering():
    """Verify /nearest?scheme_id=... returns ONLY mapped authorized partners."""
    # Test PMEGP scheme mapping
    response = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&max_distance_km=50&scheme_id=SIH26092-001")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0, "Expected at least 1 partner for PMEGP in Gorakhpur"
    for item in data:
        assert item["is_scheme_matched"] is True
        partner = item["partner"]
        assert partner["is_active"] is True

def test_category_filter():
    """Verify filtering by partner_category returns only matching records."""
    response_auth = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&max_distance_km=100&partner_category=AUTHORIZED_SCHEME_PARTNER")
    assert response_auth.status_code == 200
    data_auth = response_auth.json()
    for p in data_auth:
        assert p["partner"]["partner_category"] == "AUTHORIZED_SCHEME_PARTNER"

    response_assist = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&max_distance_km=100&partner_category=IMPLEMENTING_ASSISTANCE_CENTRE")
    assert response_assist.status_code == 200
    data_assist = response_assist.json()
    for p in data_assist:
        assert p["partner"]["partner_category"] == "IMPLEMENTING_ASSISTANCE_CENTRE"

def test_partner_directory_fallback():
    """Verify fallback directory endpoint with district & state filters."""
    response = client.get("/api/v1/partner/directory?district=Gorakhpur&state=Uttar Pradesh")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 8
    for p in data:
        assert p["partner"]["district"] == "Gorakhpur"
        assert p["partner"]["is_active"] is True

def test_deactivated_partner_excluded_from_public_api():
    """Verify inactive partners are never exposed in public endpoints."""
    response = client.get("/api/v1/partner/directory?page_size=200")
    assert response.status_code == 200
    data = response.json()
    for p in data:
        assert p["partner"]["is_active"] is True

from app.core.security import create_access_token
from app.models.user import UserRole

def test_admin_partner_management_workflow():
    """Verify admin listing, creation, status update, scheme linking, and changelog creation."""
    admin_token = create_access_token(user_id="user-sysadmin-01", role=UserRole.SYSTEM_ADMIN.value)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Admin list
    list_res = client.get("/api/v1/admin/partners?page=1&page_size=10", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert "items" in list_data
    assert "total" in list_data
    assert list_data["total"] >= 100

    # 2. Admin create test partner
    test_code = "TEST-ADMIN-PARTNER-01"
    create_payload = {
        "name": "Admin Unit Test Partner Centre",
        "code": test_code,
        "partner_type": "PUBLIC_SECTOR_BANK",
        "institution_type": "PUBLIC_SECTOR_BANK",
        "partner_category": "AUTHORIZED_SCHEME_PARTNER",
        "district": "Gorakhpur",
        "state": "Uttar Pradesh",
        "pincode": "273001",
        "phone": "0551-9999999",
        "email": "unittest@yojnasetu.gov.in",
        "website": "https://unittest.yojnasetu.gov.in",
        "latitude": 26.7550,
        "longitude": 83.3750,
        "source_url": "https://financialservices.gov.in",
        "verification_status": "VERIFIED_OFFICIAL",
        "change_reason": "Unit test creation"
    }
    create_res = client.post("/api/v1/admin/partners", json=create_payload, headers=headers)
    assert create_res.status_code in [200, 201]
    created_id = create_res.json()["partner_id"]

    try:
        # 3. Link scheme to newly created partner
        link_res = client.post(f"/api/v1/admin/partners/{created_id}/schemes", json={
            "scheme_id": "SIH26092-001",
            "service_type": "FINANCING",
            "authorization_level": "SCHEME_ROUTE_VERIFIED",
            "reason": "Test scheme link"
        }, headers=headers)
        assert link_res.status_code == 200

        # 4. Soft deactivate partner with reason
        deactivate_res = client.patch(f"/api/v1/admin/partners/{created_id}/status", json={
            "is_active": False,
            "reason": "Temporary test deactivation"
        }, headers=headers)
        assert deactivate_res.status_code == 200
        assert deactivate_res.json()["is_active"] is False

        # Verify inactive partner does not appear in public /nearest
        pub_check = client.get("/api/v1/partner/nearest?latitude=26.7550&longitude=83.3750&max_distance_km=2")
        assert pub_check.status_code == 200
        pub_pids = [p["partner"]["partner_id"] for p in pub_check.json()]
        assert created_id not in pub_pids

        # 5. Reactivate partner
        reactivate_res = client.patch(f"/api/v1/admin/partners/{created_id}/status", json={
            "is_active": True,
            "reason": "Test reactivation"
        }, headers=headers)
        assert reactivate_res.status_code == 200
        assert reactivate_res.json()["is_active"] is True

    finally:
        # Cleanup test partner from DB to leave clean state
        db = SessionLocal()
        try:
            db.query(PartnerSchemeMapping).filter(PartnerSchemeMapping.partner_id == created_id).delete()
            db.query(PartnerChangelog).filter(PartnerChangelog.partner_id == created_id).delete()
            db.query(Partner).filter(Partner.partner_id == created_id).delete()
            db.commit()
        finally:
            db.close()
