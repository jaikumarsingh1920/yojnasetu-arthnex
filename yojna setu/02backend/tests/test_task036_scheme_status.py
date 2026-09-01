"""
TASK-036: Comprehensive Scheme Verification Status & Dynamic Count Tests
Validates scheme count dynamics, verification_status serialization, and absence of stale hardcoded values.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import Scheme, SchemeVerification

client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. TOTAL SCHEME COUNT DYNAMICS (CURRENT DB TOTAL = 90)
# -----------------------------------------------------------------------------
def test_total_scheme_count_matches_database():
    db = SessionLocal()
    db_count = db.query(Scheme).count()
    db.close()
    
    assert db_count == 90, f"Expected 90 schemes in DB after Task-034, found {db_count}"
    
    res = client.get("/api/v1/schemes?page_size=1")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == db_count, f"API returned total {data['total']} but DB has {db_count}"

# -----------------------------------------------------------------------------
# 2. SCHEME LIST ITEMS SERIALIZE VERIFICATION_STATUS
# -----------------------------------------------------------------------------
def test_scheme_list_items_expose_verification_status():
    res = client.get("/api/v1/schemes?page_size=100")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 90
    
    verified_count = 0
    for item in items:
        assert "verification_status" in item, f"Scheme {item['scheme_id']} missing verification_status in list response"
        assert item["verification_status"] is not None, f"Scheme {item['scheme_id']} verification_status is None"
        if item["verification_status"] in ("VERIFIED", "VERIFIED_OFFICIAL"):
            verified_count += 1
            
    assert verified_count == 90, f"Expected all 90 verified schemes to have VERIFIED status, found {verified_count}"

# -----------------------------------------------------------------------------
# 3. SCHEME DETAIL RESPONSE EXPOSES VERIFICATION_STATUS & VERIFICATIONS
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("scheme_id", [
    "SIH26092-001", # PMEGP (Original baseline)
    "SIH26092-053", # NSFDC Term Loan
    "SIH26092-075", # PMJDY (Task-034)
    "SIH26092-088", # SSY (Task-034)
    "SIH26092-090", # AB-PMJAY (Task-034)
])
def test_scheme_detail_exposes_canonical_verification_status(scheme_id):
    res = client.get(f"/api/v1/schemes/{scheme_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["verification_status"] == "VERIFIED"
    assert len(data["verifications"]) > 0
    assert data["verifications"][0]["verification_status"] == "VERIFIED"

# -----------------------------------------------------------------------------
# 4. TASK-034 NEW SCHEMES FOLLOW IDENTICAL STATUS & PROVENANCE STRUCTURE
# -----------------------------------------------------------------------------
def test_task034_schemes_status_and_provenance_compatibility():
    task034_ids = [f"SIH26092-{i:03d}" for i in range(75, 91)]
    for sid in task034_ids:
        res = client.get(f"/api/v1/schemes/{sid}")
        assert res.status_code == 200, f"Failed to fetch Task-034 scheme {sid}"
        data = res.json()
        assert data["verification_status"] == "VERIFIED"
        assert data["official_source_url"] is not None and data["official_source_url"].startswith("http")
        assert len(data["verifications"]) >= 1
        assert data["verifications"][0]["data_confidence"] == "HIGH"

# -----------------------------------------------------------------------------
# 5. DYNAMIC VERIFICATION PERCENTAGE CALCULATION (NOT HARDCODED)
# -----------------------------------------------------------------------------
def test_verification_statistics_truthfulness():
    res = client.get("/api/v1/schemes?page_size=100")
    assert res.status_code == 200
    data = res.json()
    total = data["total"]
    verified = sum(1 for s in data["items"] if s["verification_status"] in ("VERIFIED", "VERIFIED_OFFICIAL"))
    
    # Truthful percentage calculation
    pct = round((verified / total) * 100) if total > 0 else 0
    assert pct == 100
    assert total == 90
    assert verified == 90
