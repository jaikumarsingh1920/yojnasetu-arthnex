"""
Unit and Integration Tests for Scheme Comparison API (TASK-035)
Verifies GET /api/v1/schemes/compare endpoint logic, input validation,
deduplication, error handling, credit/non-credit formatting, and personalized eligibility.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_compare_schemes_missing_ids():
    """Test GET /api/v1/schemes/compare with missing ids parameter returns 422 or 400."""
    response = client.get("/api/v1/schemes/compare")
    assert response.status_code in (400, 422)

def test_compare_schemes_empty_ids():
    """Test GET /api/v1/schemes/compare with empty ids parameter returns 400 or 422."""
    response = client.get("/api/v1/schemes/compare?ids=")
    assert response.status_code in (400, 422)

def test_compare_schemes_exceeds_max_limit():
    """Test comparing more than 4 schemes returns HTTP 400."""
    response = client.get("/api/v1/schemes/compare?ids=SCH1,SCH2,SCH3,SCH4,SCH5")
    assert response.status_code == 400
    assert "maximum of 4" in response.json()["detail"].lower()

def test_compare_schemes_two_valid_schemes():
    """Test comparing 2 valid schemes returns correct side-by-side structures."""
    schemes_resp = client.get("/api/v1/schemes?limit=2")
    assert schemes_resp.status_code == 200
    items = schemes_resp.json()["items"]
    assert len(items) >= 2, "Database must have at least 2 schemes"

    id1 = items[0]["scheme_id"]
    id2 = items[1]["scheme_id"]

    response = client.get(f"/api/v1/schemes/compare?ids={id1},{id2}")
    assert response.status_code == 200
    data = response.json()

    assert "compared_schemes" in data
    assert len(data["compared_schemes"]) == 2
    assert data["invalid_ids"] == []

    for item in data["compared_schemes"]:
        sch = item["scheme"]
        assert "scheme_id" in sch
        assert "scheme_name" in sch
        assert "is_credit_scheme" in sch
        assert "rules" in sch
        assert "documents" in sch
        assert item["personalized_eligibility"] is None

def test_compare_schemes_deduplication():
    """Test duplicate IDs in query string are deduplicated gracefully."""
    schemes_resp = client.get("/api/v1/schemes?limit=1")
    id1 = schemes_resp.json()["items"][0]["scheme_id"]

    response = client.get(f"/api/v1/schemes/compare?ids={id1},{id1},{id1}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["compared_schemes"]) == 1
    assert data["compared_schemes"][0]["scheme"]["scheme_id"] == id1

def test_compare_schemes_invalid_and_valid_ids():
    """Test non-existent scheme IDs are returned in invalid_ids array without breaking valid schemes."""
    schemes_resp = client.get("/api/v1/schemes?limit=1")
    valid_id = schemes_resp.json()["items"][0]["scheme_id"]
    invalid_id = "INVALID-SCHEME-ID-9999"

    response = client.get(f"/api/v1/schemes/compare?ids={valid_id},{invalid_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["compared_schemes"]) == 1
    assert data["compared_schemes"][0]["scheme"]["scheme_id"] == valid_id
    assert invalid_id in data["invalid_ids"]

def test_compare_schemes_credit_vs_non_credit_fields():
    """Test credit and non-credit comparison field structure formatting."""
    schemes_resp = client.get("/api/v1/schemes?limit=50")
    items = schemes_resp.json()["items"]
    
    credit_scheme = next((s for s in items if s.get("is_credit_scheme")), None)
    non_credit_scheme = next((s for s in items if not s.get("is_credit_scheme")), None)

    if credit_scheme and non_credit_scheme:
        response = client.get(f"/api/v1/schemes/compare?ids={credit_scheme['scheme_id']},{non_credit_scheme['scheme_id']}")
        assert response.status_code == 200
        data = response.json()
        
        # Credit scheme checks
        cs_item = next(s for s in data["compared_schemes"] if s["scheme"]["scheme_id"] == credit_scheme["scheme_id"])
        assert cs_item["scheme"]["is_credit_scheme"] is True
        
        # Non-credit scheme checks
        ncs_item = next(s for s in data["compared_schemes"] if s["scheme"]["scheme_id"] == non_credit_scheme["scheme_id"])
        assert ncs_item["scheme"]["is_credit_scheme"] is False
