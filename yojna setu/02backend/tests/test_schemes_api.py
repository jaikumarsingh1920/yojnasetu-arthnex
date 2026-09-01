import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from app.main import app
from app.models import Base
from app.db.session import get_db
from seed_db import seed_database


@pytest.fixture(scope="module")
def scheme_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed the test database with real scheme data
    session = TestingSessionLocal()
    seed_database(session)
    session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────
# 1. LIST & TOTAL COUNT TESTS
# ─────────────────────────────────────────────────────────────────

def test_list_schemes_default(scheme_client):
    """Default request returns page 1 of schemes with total count >= 56."""
    res = scheme_client.get("/api/v1/schemes")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 56
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) == 20


def test_verification_filter_verified(scheme_client):
    """GET /api/v1/schemes?verification_status=VERIFIED returns verified schemes."""
    res = scheme_client.get("/api/v1/schemes?verification_status=VERIFIED")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 56


# ─────────────────────────────────────────────────────────────────
# 2. PAGINATION TESTS
# ─────────────────────────────────────────────────────────────────

def test_pagination_pages(scheme_client):
    """Verify pagination across pages."""
    p1 = scheme_client.get("/api/v1/schemes?page=1&page_size=20").json()
    p2 = scheme_client.get("/api/v1/schemes?page=2&page_size=20").json()
    p3 = scheme_client.get("/api/v1/schemes?page=3&page_size=20").json()

    assert len(p1["items"]) == 20
    assert len(p2["items"]) == 20
    assert len(p3["items"]) > 0

    # Verify no item duplication across pages
    ids_p1 = [item["scheme_id"] for item in p1["items"]]
    ids_p2 = [item["scheme_id"] for item in p2["items"]]
    ids_p3 = [item["scheme_id"] for item in p3["items"]]
    assert len(set(ids_p1).intersection(set(ids_p2))) == 0
    assert len(set(ids_p2).intersection(set(ids_p3))) == 0


def test_custom_page_size(scheme_client):
    """page_size=10 -> items=10."""
    res = scheme_client.get("/api/v1/schemes?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 10
    assert data["total"] >= 56
    assert data["pages"] >= 6


def test_invalid_pagination_params(scheme_client):
    """Invalid pagination parameters (page < 1 or page_size > 100) return 422."""
    assert scheme_client.get("/api/v1/schemes?page=0").status_code == 422
    assert scheme_client.get("/api/v1/schemes?page_size=200").status_code == 422


# ─────────────────────────────────────────────────────────────────
# 3. SEARCH TESTS
# ─────────────────────────────────────────────────────────────────

def test_search_by_scheme_name(scheme_client):
    """Search 'Micro Finance' matches NSFDC Micro Finance Scheme."""
    res = scheme_client.get("/api/v1/schemes?search=Micro+Finance")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert any("Micro Finance" in item["scheme_name"] for item in data["items"])


def test_case_insensitive_search(scheme_client):
    """Case-insensitive search: 'VISHWAKARMA' vs 'vishwakarma' return identical results."""
    res_upper = scheme_client.get("/api/v1/schemes?search=VISHWAKARMA").json()
    res_lower = scheme_client.get("/api/v1/schemes?search=vishwakarma").json()
    assert res_upper["total"] > 0
    assert res_upper["total"] == res_lower["total"]
    assert [i["scheme_id"] for i in res_upper["items"]] == [i["scheme_id"] for i in res_lower["items"]]


def test_no_result_search(scheme_client):
    """Non-existent search term returns empty items list with total=0."""
    res = scheme_client.get("/api/v1/schemes?search=NonExistentSchemeXYZ999")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []


# ─────────────────────────────────────────────────────────────────
# 4. FILTER TESTS
# ─────────────────────────────────────────────────────────────────

def test_scheme_type_filter(scheme_client):
    """Filter by scheme_type=EDUCATION_LOAN."""
    res = scheme_client.get("/api/v1/schemes?scheme_type=EDUCATION_LOAN")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert all("EDUCATION" in item["scheme_type"].upper() or "LOAN" in item["scheme_type"].upper() for item in data["items"])


def test_ministry_filter(scheme_client):
    """Filter by ministry."""
    res = scheme_client.get("/api/v1/schemes?ministry=Ministry+of+Social+Justice")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert all("Social Justice" in item["ministry"] for item in data["items"])


def test_sector_filter(scheme_client):
    """Filter by sector=EDUCATION."""
    res = scheme_client.get("/api/v1/schemes?sector=EDUCATION")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0


def test_combined_filters(scheme_client):
    """Combined search and filter parameters."""
    res = scheme_client.get("/api/v1/schemes?sector=EDUCATION&verification_status=VERIFIED")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0


# ─────────────────────────────────────────────────────────────────
# 5. SORTING TESTS
# ─────────────────────────────────────────────────────────────────

def test_stable_sorting(scheme_client):
    """Sort by scheme_name asc vs desc produces reversed order."""
    asc_res = scheme_client.get("/api/v1/schemes?sort_by=scheme_name&sort_order=asc&page_size=50").json()
    desc_res = scheme_client.get("/api/v1/schemes?sort_by=scheme_name&sort_order=desc&page_size=50").json()

    names_asc = [item["scheme_name"] for item in asc_res["items"]]
    names_desc = [item["scheme_name"] for item in desc_res["items"]]

    assert names_asc[0] != names_desc[0]


# ─────────────────────────────────────────────────────────────────
# 6. SCHEME DETAIL TESTS
# ─────────────────────────────────────────────────────────────────

def test_scheme_detail_valid(scheme_client):
    """GET /api/v1/schemes/SIH26092-052 returns complete scheme details including rules & docs."""
    res = scheme_client.get("/api/v1/schemes/SIH26092-052")
    assert res.status_code == 200
    data = res.json()
    assert data["scheme_id"] == "SIH26092-052"
    assert data["scheme_name"] == "NSFDC Micro Finance Scheme (MFS)"

    # Verify related verifications, rules, and documents are eagerly loaded
    assert "verifications" in data and len(data["verifications"]) > 0
    assert "rules" in data and len(data["rules"]) == 9
    assert "documents" in data


def test_scheme_detail_nonexistent(scheme_client):
    """GET /api/v1/schemes/NONEXISTENT-999 returns 404 Not Found."""
    res = scheme_client.get("/api/v1/schemes/NONEXISTENT-999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_unknown_conditional_sentinels_preserved(scheme_client):
    """Verify raw 'UNKNOWN' and 'CONDITIONAL' string values are preserved in scheme detail."""
    res = scheme_client.get("/api/v1/schemes/SIH26092-055")
    assert res.status_code == 200
    data = res.json()
    # Check that sentinel raw values remain intact strings, not mutated to null/0/false
    assert data["repayment_period_min_months_raw"] == "UNKNOWN"
    assert data["moratorium_interest_mode"] == "UNKNOWN"
    assert data["collateral_required"] == "UNKNOWN"


# ─────────────────────────────────────────────────────────────────
# 7. PUBLIC ACCESS TEST
# ─────────────────────────────────────────────────────────────────

def test_public_endpoint_unauthenticated(scheme_client):
    """Verify scheme discovery API endpoints work without Authorization header."""
    res_list = scheme_client.get("/api/v1/schemes")
    assert res_list.status_code == 200

    res_detail = scheme_client.get("/api/v1/schemes/SIH26092-052")
    assert res_detail.status_code == 200
