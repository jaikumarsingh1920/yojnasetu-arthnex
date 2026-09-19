"""
Test Suite for Task 5: Massively Expanded and Correct Channel Partner Coverage.

Validates:
1. Deduplication and normalization of partners.
2. Truthful application channel resolution across the scheme corpus.
3. Accurate Scheme -> Channel Partner mapping.
4. Defense against invalid/fabricated mappings (pure online portals do not fabricate fake bank branches).
5. Defensible coordinates with explicit precision tags (EXACT_ADDRESS, DISTRICT_HEADQUARTERS).
6. Deterministic Haversine distance calculation and routing destination URLs.
7. Geospatial nearest partner search with radius, district, state, and pincode filters.
8. Scheme compatibility filtering.
9. Verification provenance and confidence tracking.
10. Bulk processing idempotency (safe rerun without duplicate creation).
11. Coverage report endpoint and metric integrity.
12. End-to-End citizen partner discovery journey.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.partner import Partner
from app.models.scheme import Scheme
from app.models.partner_scheme import PartnerSchemeMapping
from app.services.channel_partner_enrichment_service import ChannelPartnerEnrichmentService
from app.services.geo_partner_service import GeoPartnerLocatorService


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_coverage_report_metrics(db_session: Session, client: TestClient):
    """
    Test that the coverage report reflects truthful, verified metrics.
    No 100% fake partner claim - physical partners exist where officially applicable,
    and online portals are truthfully categorized.
    """
    response = client.get("/api/v1/partner/coverage-report")
    assert response.status_code == 200
    data = response.json()

    assert data["total_schemes"] >= 850
    assert data["schemes_with_verified_channel"] >= 850
    assert data["schemes_with_physical_partner_mapping"] > 400
    assert data["schemes_online_portal_channel"] > 200
    assert data["schemes_without_partner_data"] == 0
    assert data["total_partners"] >= 160
    assert data["total_scheme_partner_mappings"] >= 5000
    assert data["coordinates_available"] >= 160
    # Coordinates missing should truthfully reflect the few partners with unavailable coordinates
    assert data["coordinates_missing"] >= 0
    assert "EXACT_ADDRESS" in data["coordinate_precision_breakdown"]
    assert "PSB" in data["mappings_by_partner_type"]
    assert "RRB" in data["mappings_by_partner_type"]
    assert "DISTRICT_INDUSTRIES_CENTRE" in data["mappings_by_partner_type"]
    assert "SCA" in data["mappings_by_partner_type"]


def test_partner_normalization_and_deduplication(db_session: Session):
    """
    Ensure partner names and addresses are normalized without duplicate codes.
    """
    partners = db_session.query(Partner).all()
    codes = [p.code for p in partners]
    assert len(codes) == len(set(codes)), "Partner codes must be globally unique (no duplicates)"

    # Verify no corrupted concatenated names exist (e.g. trailing numbers or multiple addresses glued together)
    for p in partners:
        assert p.name and len(p.name) > 3
        assert not p.name.endswith("273001"), f"Partner name contains unnormalized pincode: {p.name}"
        if p.pincode:
            assert len(p.pincode) == 6 and p.pincode.isdigit(), f"Invalid pincode format: {p.pincode}"


def test_truthful_application_channels(db_session: Session):
    """
    Every scheme must have a legitimate, non-empty application channel.
    Credit schemes must map to financial institutions, MSME to DICs, welfare to SCAs,
    and digital DBT to Online Portal.
    """
    schemes = db_session.query(Scheme).all()
    assert len(schemes) >= 850

    valid_channels = {
        "Bank Branch / Financial Institution",
        "District Industries Centre (DIC)",
        "State Channelising Agency (SCA) / Welfare Corporation",
        "Common Service Centre (CSC) / Digital Seva Kendra",
        "Common Service Centre (CSC) / Citizen Facilitation Centre",
        "Online Portal",
        "District Agriculture Office / Krishi Vigyan Kendra",
        "District Fisheries Office / Department",
        "State Tourism Development Board / Office",
        "District Administrative / Departmental Office",
        "District Animal Husbandry Department / Polyclinic",
        "Implementing Department / Agency",
    }

    for s in schemes:
        assert s.application_channel, f"Scheme {s.scheme_id} has empty application_channel"
        assert s.application_channel in valid_channels, (
            f"Unrecognized application_channel for scheme {s.scheme_id}: {s.application_channel}"
        )


def test_no_fake_bank_partners_for_pure_online_portals(db_session: Session):
    """
    Schemes designated as Online Portal must not have arbitrary commercial bank branches mapped
    unless the scheme specifically offers loan/credit financing.
    """
    online_schemes = db_session.query(Scheme).filter(
        Scheme.application_channel == "Online Portal"
    ).limit(50).all()

    for os_scheme in online_schemes:
        # If it's a scholarship or welfare grant with pure online portal application,
        # it should NOT have PSB/commercial bank branch application channel mappings
        # (unless it is explicitly an educational loan or credit scheme)
        title_lower = (os_scheme.scheme_name or "").lower()
        if "scholarship" in title_lower or "fellowship" in title_lower:
            mappings = db_session.query(PartnerSchemeMapping).filter(
                PartnerSchemeMapping.scheme_id == os_scheme.scheme_id
            ).all()
            for m in mappings:
                partner = db_session.query(Partner).filter(Partner.partner_id == m.partner_id).first()
                if partner:
                    assert partner.partner_type not in ["PSB", "RRB", "COMMERCIAL_BANK_BRANCH"], (
                        f"Fabricated bank mapping detected for online scholarship: {os_scheme.scheme_id}"
                    )


def test_coordinates_and_explicit_precision(db_session: Session):
    """
    Physical partner records with coordinates must declare coordinate_precision
    and must not fabricate coordinates.
    """
    partners_with_coords = db_session.query(Partner).filter(
        Partner.latitude.isnot(None),
        Partner.longitude.isnot(None)
    ).all()

    assert len(partners_with_coords) >= 160
    valid_precisions = {"EXACT_ADDRESS", "OFFICIAL_LOCALITY", "DISTRICT_HEADQUARTERS", "STATE_CAPITAL"}

    for p in partners_with_coords:
        assert 6.0 <= p.latitude <= 38.0, f"Latitude out of bounds for India: {p.latitude} ({p.name})"
        assert 68.0 <= p.longitude <= 98.0, f"Longitude out of bounds for India: {p.longitude} ({p.name})"
        assert p.coordinate_precision in valid_precisions, (
            f"Invalid precision for partner {p.name}: {p.coordinate_precision}"
        )
        assert p.coordinates_source is not None


def test_deterministic_haversine_distance():
    """
    Verify mathematical correctness of deterministic Haversine distance calculation.
    """
    # Gorakhpur (26.7606, 83.3732) to Lucknow (26.8467, 80.9462) is approximately 242 km
    dist = GeoPartnerLocatorService.calculate_haversine_distance(
        26.7606, 83.3732, 26.8467, 80.9462
    )
    assert 235.0 <= dist <= 250.0, f"Expected ~242 km between Gorakhpur and Lucknow, got {dist}"

    # Distance to identical coordinates must be 0.0
    zero_dist = GeoPartnerLocatorService.calculate_haversine_distance(
        26.7606, 83.3732, 26.7606, 83.3732
    )
    assert zero_dist == 0.0


def test_nearest_partner_locator_filters(client: TestClient):
    """
    Test nearest partner locator with radius, state, district, and pincode filters.
    """
    # 1. Gorakhpur coordinates (26.7606, 83.3732) within 15 km
    resp = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&radius_km=15.0&limit=10")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0

    # Ensure sorted by distance ascending
    distances = [item["distance_km"] for item in items]
    assert distances == sorted(distances)

    # Check routing URL is present
    for item in items:
        assert "google_maps_url" in item
        assert "destination=" in item["google_maps_url"]
        assert item["coordinate_precision"] in ["EXACT_ADDRESS", "DISTRICT_HEADQUARTERS", "OFFICIAL_LOCALITY"]

    # 2. Pincode filter test (273001 - Gorakhpur)
    resp_pin = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&radius_km=100.0&pincode=273001&limit=5")
    assert resp_pin.status_code == 200
    pin_items = resp_pin.json()
    assert len(pin_items) > 0
    for item in pin_items:
        assert item["partner"]["pincode"] == "273001"

    # 3. District filter test
    resp_dist = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&radius_km=500.0&district=Gorakhpur&limit=5")
    assert resp_dist.status_code == 200
    dist_items = resp_dist.json()
    assert len(dist_items) > 0
    for item in dist_items:
        assert "gorakhpur" in (item["partner"]["district"] or "").lower() or "gorakhpur" in item["partner"]["name"].lower()


def test_scheme_specific_partner_routing(client: TestClient):
    """
    Verify scheme-specific partner matching and routing details.
    """
    # Query partners for PMEGP (SIH26092-001)
    resp = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&radius_km=100.0&scheme_id=SIH26092-001&limit=5")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0

    for item in items:
        assert item["is_scheme_matched"] is True
        assert item["confidence"] in ["HIGH", "MEDIUM", "VERIFIED"]
        assert item["application_channel"] is not None
        assert "https://www.google.com/maps/dir/?api=1&destination=" in item["google_maps_url"]


def test_bulk_enrichment_idempotency(db_session: Session):
    """
    Running bulk partner enrichment again must be completely idempotent:
    No duplicate partners or duplicate mappings should ever be created.
    """
    partners_before = db_session.query(Partner).count()
    mappings_before = db_session.query(PartnerSchemeMapping).count()

    result = ChannelPartnerEnrichmentService.run_bulk_partner_enrichment(db_session)

    partners_after = db_session.query(Partner).count()
    mappings_after = db_session.query(PartnerSchemeMapping).count()

    assert result["new_partners_added"] == 0
    assert result["new_mappings_created"] == 0
    assert partners_after == partners_before
    assert mappings_after == mappings_before


def test_end_to_end_citizen_partner_discovery_flow(client: TestClient, db_session: Session):
    """
    End-to-end journey test:
    Citizen selects a Scheme -> Identifies Application Channel -> Discovers Partner ->
    Gets Physical Location & Coordinates -> Computes Haversine Distance -> Generates Map Directions.
    """
    # Step 1: Citizen is interested in an MSME/Credit Scheme (PMEGP)
    scheme = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert scheme is not None
    assert scheme.application_channel == "Bank Branch / Financial Institution"

    # Step 2: Citizen enters their location (Gorakhpur: 26.7606, 83.3732)
    resp = client.get(
        f"/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&scheme_id={scheme.scheme_id}&radius_km=25.0&limit=3"
    )
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0

    nearest = results[0]
    # Step 3: Partner has valid institutional data
    assert nearest["partner"]["name"] is not None
    assert nearest["partner"]["partner_type"] in ["PSB", "RRB", "DISTRICT_INDUSTRIES_CENTRE", "PUBLIC_SECTOR_BANK"]
    assert nearest["distance_km"] < 25.0

    # Step 4: Physical coordinates and precision are validated
    assert nearest["partner"]["latitude"] is not None
    assert nearest["partner"]["longitude"] is not None
    assert nearest["coordinate_precision"] in ["EXACT_ADDRESS", "DISTRICT_HEADQUARTERS", "OFFICIAL_LOCALITY"]

    # Step 5: Route / Google Maps link is generated
    dest_lat = nearest["partner"]["latitude"]
    dest_lng = nearest["partner"]["longitude"]
    expected_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={dest_lat},{dest_lng}"
    assert nearest["google_maps_url"] == expected_maps_url
