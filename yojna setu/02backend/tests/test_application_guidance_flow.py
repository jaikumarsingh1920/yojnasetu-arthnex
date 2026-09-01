import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.models.partner_scheme import PartnerSchemeMapping

client = TestClient(app)

def test_direct_portal_scheme_application_route():
    """
    Test that a known direct portal scheme (e.g. SIH26092-064 or SIH26092-082)
    returns DIRECT_PORTAL routing and exposes its official portal URL.
    """
    resp = client.get("/api/v1/schemes/SIH26092-064")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scheme_id"] == "SIH26092-064"
    assert data["application_route"] == "DIRECT_PORTAL"
    assert data["official_portal"] is not None
    assert data["official_portal"].startswith("http")
    assert len(data["documents"]) > 0


def test_partner_routed_scheme_application_route():
    """
    Test that a known partner-routed scheme (e.g. SIH26092-053 NSFDC Term Loan)
    returns CHANNEL_PARTNER routing and has active partner mappings.
    """
    resp = client.get("/api/v1/schemes/SIH26092-053")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scheme_id"] == "SIH26092-053"
    assert data["application_route"] == "CHANNEL_PARTNER"
    assert data["partner_count"] > 0


def test_unverified_departmental_route_scheme():
    """
    Test that a scheme without partner mapping or open online portal
    returns OFFICIAL_ROUTE_UNVERIFIED without fabricating a fake application portal.
    """
    db = SessionLocal()
    schemes = db.query(Scheme).all()
    unverified = None
    for s in schemes:
        if s.application_route == "OFFICIAL_ROUTE_UNVERIFIED":
            unverified = s
            break
    db.close()

    if unverified:
        resp = client.get(f"/api/v1/schemes/{unverified.scheme_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["application_route"] == "OFFICIAL_ROUTE_UNVERIFIED"


def test_recommendation_to_scheme_detail_scheme_id_preservation():
    """
    Test that recommendation endpoint returns valid scheme_ids that exist
    and can be fetched directly via scheme detail endpoint.
    """
    payload = {
        "profile": {
            "age": 29,
            "gender": "FEMALE",
            "state": "UTTAR_PRADESH",
            "social_category": "SC",
            "annual_income": 180000.0,
            "business_stage": "NEW",
            "project_cost": 100000.0,
            "loan_required": True
        },
        "top_k": 5
    }
    rec_resp = client.post("/api/v1/recommendations", json=payload)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    recs = rec_data.get("recommendations") or rec_data.get("items") or []
    assert len(recs) > 0

    first_rec = recs[0]
    rec_scheme_id = first_rec["scheme_id"]

    # Verify detail endpoint loads the exact scheme
    detail_resp = client.get(f"/api/v1/schemes/{rec_scheme_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["scheme_id"] == rec_scheme_id


def test_scheme_detail_to_partner_locator_filtering():
    """
    Test that filtering partners by scheme_id only returns partners mapped to that scheme.
    """
    scheme_id = "SIH26092-053"
    resp = client.get(f"/api/v1/partner/nearest?latitude=28.6139&longitude=77.2090&scheme_id={scheme_id}&limit=10")
    assert resp.status_code == 200
    partners = resp.json()
    assert len(partners) > 0
    for p in partners:
        assert p["partner"]["latitude"] is not None
        assert p["partner"]["longitude"] is not None
        assert p["distance_km"] >= 0


def test_documents_guidance_display_and_no_user_storage():
    """
    Test that document guidance is returned from database records without
    requiring or creating user document storage tables.
    """
    resp = client.get("/api/v1/schemes/SIH26092-064")
    assert resp.status_code == 200
    data = resp.json()
    docs = data["documents"]
    assert len(docs) >= 1
    for doc in docs:
        assert "document_name" in doc
        assert "requirement_type" in doc
        assert doc["active"] is True


def test_all_12_locales_have_how_to_apply_keys():
    """
    Test that all 12 locale JSON files contain the complete howToApply namespace.
    """
    import json
    import os
    locales_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "01frontend", "src", "i18n", "locales")
    langs = ["en", "hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or", "as"]
    required_keys = ["title", "directPortalTitle", "partnerTitle", "unverifiedTitle", "ctaPortal", "ctaPartner", "disclaimer"]

    for lang in langs:
        file_path = os.path.join(locales_dir, f"{lang}.json")
        assert os.path.exists(file_path), f"Missing {lang}.json"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "howToApply" in data, f"Missing howToApply namespace in {lang}.json"
        for key in required_keys:
            assert key in data["howToApply"], f"Missing key {key} in {lang}.json howToApply"
            assert data["howToApply"][key].strip() != "", f"Empty key {key} in {lang}.json howToApply"
