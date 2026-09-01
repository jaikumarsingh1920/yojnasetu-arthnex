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
from app.models import Base, User, UserRole
from app.db.session import get_db
from app.core.security import hash_password, create_access_token

@pytest.fixture(scope="module")
def app_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    
    # Insert partner
    from seed_db import seed_database
    # Mock some basic partner data if needed or rely on seed_partners() if it works on sqlite
    try:
        seed_database(session)
    except Exception as e:
        print(f"Skipping seed_database: {e}")

    # Seed test users
    pwd_hash = hash_password("Secret123!")
    ben1 = User(user_id="user-ben-1", email="ben1@example.com", hashed_password=pwd_hash, role=UserRole.BENEFICIARY.value)
    session.add(ben1)
    session.commit()
    session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, TestingSessionLocal
    app.dependency_overrides.clear()

@pytest.fixture
def ben1_headers():
    token = create_access_token(user_id="user-ben-1", role=UserRole.BENEFICIARY.value)
    return {"Authorization": f"Bearer {token}"}

def test_nearest_partners_valid_coordinates(app_client, ben1_headers):
    client, _ = app_client
    res = client.get("/api/v1/partner/nearest?latitude=19.0760&longitude=72.8777", headers=ben1_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if len(data) > 1:
        assert data[0]["distance_km"] <= data[1]["distance_km"]

def test_nearest_partners_with_scheme(app_client, ben1_headers):
    client, _ = app_client
    res = client.get("/api/v1/partner/nearest?latitude=19.0760&longitude=72.8777&scheme_id=SCHEME-01&loan_category=TERM_LOAN", headers=ben1_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_nearest_partners_invalid_coordinates(app_client, ben1_headers):
    client, _ = app_client
    res = client.get("/api/v1/partner/nearest?latitude=invalid&longitude=72.8777", headers=ben1_headers)
    assert res.status_code == 422

def test_geocoding_classification_logic():
    from scripts.geocode_official_partners import classify_nominatim_result
    
    # 1. High confidence test
    high_mock = [{
        "lat": "28.6139",
        "lon": "77.2090",
        "display_name": "UCO Bank, Parliament Street, New Delhi, Delhi, 110001, India",
        "address": {"country_code": "in", "country": "India", "city": "New Delhi", "state": "Delhi"},
        "addresstype": "amenity",
        "class": "amenity",
        "type": "bank"
    }]
    status, lat, lon, name, conf = classify_nominatim_result(high_mock, "UCO Bank New Delhi")
    assert status == "HIGH"
    assert lat == 28.6139
    assert lon == 77.2090
    assert conf == "HIGH"
    
    # 2. Medium confidence (broad state level) test
    state_mock = [{
        "lat": "20.5937",
        "lon": "78.9629",
        "display_name": "Maharashtra, India",
        "address": {"country_code": "in", "country": "India", "state": "Maharashtra"},
        "addresstype": "state",
        "class": "boundary",
        "type": "administrative"
    }]
    status, lat, lon, name, conf = classify_nominatim_result(state_mock, "Maharashtra Agency")
    assert status == "MEDIUM"
    assert lat is None # Coordinates must be NULL for state-level matches
    
    # 3. Failed outside India test
    intl_mock = [{
        "lat": "51.5074",
        "lon": "-0.1278",
        "display_name": "London, UK",
        "address": {"country_code": "gb", "country": "United Kingdom"},
        "addresstype": "city"
    }]
    status, lat, lon, name, conf = classify_nominatim_result(intl_mock, "International")
    assert status == "FAILED"
    assert lat is None

def test_partner_service_excludes_unverified_coordinates(app_client):
    _, TestingSessionLocal = app_client
    from app.services.geo_partner_service import GeoPartnerLocatorService
    from app.models.partner import Partner
    
    db = TestingSessionLocal()
    
    # Add an unverified partner with coordinates
    unverified = Partner(
        partner_id="p-unverified-test",
        name="Unverified Partner",
        code="UNVERIFIED-TEST",
        partner_type="SCA",
        latitude=28.6139,
        longitude=77.2090,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=False, # Explicitly unverified
        is_active=True,
        is_accepting_applications=True
    )
    # Add a verified partner with coordinates
    verified = Partner(
        partner_id="p-verified-test",
        name="Verified Partner",
        code="VERIFIED-TEST",
        partner_type="PSB",
        latitude=28.6140,
        longitude=77.2091,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_source="NOMINATIM_OSM_OFFICIAL_ADDRESS",
        geocoding_provider="OSM_NOMINATIM",
        geocoding_status="SUCCESS",
        coordinates_verified=True, # Verified
        is_active=True,
        is_accepting_applications=True
    )
    db.add(unverified)
    db.add(verified)
    db.commit()
    
    results = GeoPartnerLocatorService.find_nearest_partners(db, 28.6139, 77.2090, radius_km=10.0)
    returned_ids = [r["partner"].partner_id for r in results]
    
    assert "p-verified-test" in returned_ids
    assert "p-unverified-test" not in returned_ids # Unverified must be excluded
    db.close()

def test_prototype_partner_strictly_excluded(app_client):
    _, TestingSessionLocal = app_client
    from app.services.geo_partner_service import GeoPartnerLocatorService
    from app.models.partner import Partner
    
    db = TestingSessionLocal()
    
    # Add a prototype partner
    proto = Partner(
        partner_id="p-proto-leak-test",
        name="Prototype Demo Partner",
        code="PROTO-TEST",
        partner_type="PSB",
        latitude=28.6139,
        longitude=77.2090,
        verification_status="PROTOTYPE", # Prototype status
        coordinates_verified=True,
        is_active=True,
        is_accepting_applications=True
    )
    db.add(proto)
    db.commit()
    
    results = GeoPartnerLocatorService.find_nearest_partners(db, 28.6139, 77.2090, radius_km=10.0)
    returned_ids = [r["partner"].partner_id for r in results]
    
    assert "p-proto-leak-test" not in returned_ids # Prototype records MUST NEVER be returned
    db.close()

def test_null_coordinates_and_npa_filtering(app_client):
    _, TestingSessionLocal = app_client
    from app.services.geo_partner_service import GeoPartnerLocatorService
    from app.models.partner import Partner
    
    db = TestingSessionLocal()
    
    # Add partner with NULL coords
    null_coords = Partner(
        partner_id="p-null-coords",
        name="Official Partner Null Coords",
        code="OFFICIAL-NULL",
        partner_type="PSB",
        latitude=None,
        longitude=None,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=False,
        is_active=True,
        is_accepting_applications=True
    )
    # Add partner with excessive NPA (> 10%)
    high_npa = Partner(
        partner_id="p-high-npa",
        name="Official Partner High NPA",
        code="OFFICIAL-HIGH-NPA",
        partner_type="PSB",
        latitude=28.6140,
        longitude=77.2091,
        npa_percentage=15.5, # Exceeds 10% max_npa
        verification_status="VERIFIED_OFFICIAL",
        coordinates_source="NOMINATIM_OSM_OFFICIAL_ADDRESS",
        geocoding_provider="OSM_NOMINATIM",
        geocoding_status="SUCCESS",
        coordinates_verified=True,
        is_active=True,
        is_accepting_applications=True
    )
    db.add(null_coords)
    db.add(high_npa)
    db.commit()
    
    results = GeoPartnerLocatorService.find_nearest_partners(db, 28.6139, 77.2090, radius_km=10.0, max_npa=10.0)
    returned_ids = [r["partner"].partner_id for r in results]
    
    assert "p-null-coords" not in returned_ids
    assert "p-high-npa" not in returned_ids
    db.close()

def test_web_researched_coordinates_provenance(app_client):
    _, TestingSessionLocal = app_client
    from app.services.geo_partner_service import GeoPartnerLocatorService
    from app.models.partner import Partner
    
    db = TestingSessionLocal()
    web_partner = Partner(
        partner_id="p-web-research-test",
        name="SIDBI Lucknow Office",
        code="SIDBI-LKO",
        partner_type="OTHER_AGENCY",
        latitude=26.84307,
        longitude=80.942095,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_source="WEB_RESEARCH",
        coordinates_verified=True,
        geocoding_provider="PUBLIC_WEB_SOURCE",
        geocoding_status="SUCCESS",
        geocoding_confidence="HIGH",
        geocoding_display_name="Ashok Marg, Hazratganj, Lucknow, 226001",
        is_active=True,
        is_accepting_applications=True
    )
    db.add(web_partner)
    db.commit()
    
    results = GeoPartnerLocatorService.find_nearest_partners(db, 26.8467, 80.9462, radius_km=10.0)
    matched = [r for r in results if r["partner"].partner_id == "p-web-research-test"]
    
    assert len(matched) == 1
    res_p = matched[0]["partner"]
    assert res_p.coordinates_source == "WEB_RESEARCH"
    assert res_p.geocoding_provider == "PUBLIC_WEB_SOURCE"
    assert res_p.geocoding_confidence == "HIGH"
    assert matched[0]["distance_km"] < 1.0 # ~0.57 km
    db.close()

def test_haversine_distance_accuracy():
    from app.services.geo_partner_service import haversine_distance
    # Distance between New Delhi (28.6139, 77.2090) and Connaught Place (28.6315, 77.2167) is ~2.09 km
    dist = haversine_distance(28.6139, 77.2090, 28.6315, 77.2167)
    assert 1.9 <= dist <= 2.2

def test_osrm_compatible_coordinates_format(app_client):
    client, _ = app_client
    # Authenticated request to /api/v1/partner/nearest
    res = client.get("/api/v1/partner/nearest?latitude=28.6139&longitude=77.2090&radius_km=50")
    assert res.status_code == 200
    data = res.json()
    for item in data:
        partner = item["partner"]
        assert -90.0 <= partner["latitude"] <= 90.0
        assert -180.0 <= partner["longitude"] <= 180.0
        assert item["distance_km"] >= 0.0

def test_partner_locator_empty_radius_response(app_client):
    client, _ = app_client
    # Point in the Indian ocean where no partners exist
    res = client.get("/api/v1/partner/nearest?latitude=0.0&longitude=80.0&radius_km=10")
    assert res.status_code == 200
    data = res.json()
    assert data == [] # Empty compliant list without fake partners

def test_zero_fabricated_coordinates_guarantee(app_client):
    _, TestingSessionLocal = app_client
    from app.models.partner import Partner
    db = TestingSessionLocal()
    mapped = db.query(Partner).filter(
        Partner.verification_status == "VERIFIED_OFFICIAL",
        Partner.coordinates_verified == True
    ).all()
    assert len(mapped) > 0
    for p in mapped:
        assert p.latitude is not None and p.longitude is not None
        assert p.coordinates_source in ["NOMINATIM_OSM_OFFICIAL_ADDRESS", "WEB_RESEARCH"]
        assert p.geocoding_provider in ["OSM_NOMINATIM", "PUBLIC_WEB_SOURCE", "NOMINATIM_OSM"]
    db.close()

def test_scheme_specific_partner_filtering_and_provenance(app_client):
    _, TestingSessionLocal = app_client
    from app.services.geo_partner_service import GeoPartnerLocatorService
    from app.models.partner import Partner
    from app.models.partner_scheme import PartnerSchemeMapping

    db = TestingSessionLocal()
    # Create test partner with scheme mapping
    p1 = Partner(
        partner_id="p-scheme-test-1",
        name="NSFDC State Channelising Agency Delhi",
        code="SCA-DEL-01",
        partner_type="SCA",
        latitude=28.6139,
        longitude=77.2090,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=True,
        is_active=True,
        is_accepting_applications=True
    )
    p2 = Partner(
        partner_id="p-scheme-test-2",
        name="Microfinance Special MFI Delhi",
        code="MFI-DEL-01",
        partner_type="NBFC_MFI",
        latitude=28.6200,
        longitude=77.2100,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=True,
        is_active=True,
        is_accepting_applications=True
    )
    db.add_all([p1, p2])
    db.commit()

    # Map p1 to Term Loan (SIH26092-053), p2 to Micro Finance (SIH26092-052)
    m1 = PartnerSchemeMapping(
        partner_id=p1.partner_id,
        scheme_id="SIH26092-053",
        authorized_category="TERM_LOAN",
        verification_status="VERIFIED_OFFICIAL",
        verification_notes="State Agency authorized for Term Loan"
    )
    m2 = PartnerSchemeMapping(
        partner_id=p2.partner_id,
        scheme_id="SIH26092-052",
        authorized_category="MICRO_FINANCE",
        verification_status="VERIFIED_OFFICIAL",
        verification_notes="NBFC-MFI authorized for Micro Finance"
    )
    db.add_all([m1, m2])
    db.commit()

    # Query 1: Filter by Term Loan (SIH26092-053)
    results_term = GeoPartnerLocatorService.find_nearest_partners(
        db, 28.6139, 77.2090, radius_km=5.0, scheme_id="SIH26092-053"
    )
    term_partner_ids = [r["partner"].partner_id for r in results_term]
    assert "p-scheme-test-1" in term_partner_ids
    assert "p-scheme-test-2" not in term_partner_ids
    assert results_term[0]["is_scheme_matched"] is True

    # Query 2: Filter by Micro Finance (SIH26092-052)
    results_mfi = GeoPartnerLocatorService.find_nearest_partners(
        db, 28.6139, 77.2090, radius_km=5.0, scheme_id="SIH26092-052"
    )
    mfi_partner_ids = [r["partner"].partner_id for r in results_mfi]
    assert "p-scheme-test-2" in mfi_partner_ids
    assert "p-scheme-test-1" not in mfi_partner_ids
    assert results_mfi[0]["is_scheme_matched"] is True

    # Query 3: Filter by unmapped scheme (Unknown != Supports All)
    results_unmapped = GeoPartnerLocatorService.find_nearest_partners(
        db, 28.6139, 77.2090, radius_km=5.0, scheme_id="SIH26092-UNMAPPED-SCHEME"
    )
    assert len(results_unmapped) == 0

    db.close()

def test_distance_origin_preservation_gorakhpur_vs_kerala():
    from app.services.geo_partner_service import haversine_distance
    # User actual GPS in Gorakhpur: 26.7606, 83.3732
    # Partner in Kerala (Thrissur): 10.3454, 76.2111
    # Search centroid for Kerala: 10.8505, 76.2711

    user_gps_lat, user_gps_lng = 26.7606, 83.3732
    kerala_search_lat, kerala_search_lng = 10.8505, 76.2711
    partner_lat, partner_lng = 10.3454, 76.2111

    # Distance from actual GPS to partner
    real_distance = haversine_distance(user_gps_lat, user_gps_lng, partner_lat, partner_lng)
    
    # Distance from Kerala search centroid to partner
    search_distance = haversine_distance(kerala_search_lat, kerala_search_lng, partner_lat, partner_lng)

    # Real distance is ~1960 km, while search centroid distance is ~56 km
    assert real_distance > 1800.0, f"Distance from Gorakhpur must be >1800km, got {real_distance}"
    assert search_distance < 100.0, f"Search centroid distance must be <100km, got {search_distance}"
    assert real_distance != search_distance, "GPS distance must never equal search centroid distance"

def test_distance_origin_preservation_delhi_vs_kerala():
    from app.services.geo_partner_service import haversine_distance
    # User actual GPS in Delhi: 28.6139, 77.2090
    # Partner in Kerala (Thrissur): 10.3454, 76.2111

    user_delhi_lat, user_delhi_lng = 28.6139, 77.2090
    partner_lat, partner_lng = 10.3454, 76.2111

    real_distance = haversine_distance(user_delhi_lat, user_delhi_lng, partner_lat, partner_lng)
    assert real_distance > 2000.0, f"Distance from Delhi must be >2000km, got {real_distance}"

def test_critical_negative_partner_exclusion_across_schemes(app_client):
    """
    Mandatory Negative Test:
    Partner X mapped to Scheme A (SIH26092-053) but NOT mapped to Scheme B (SIH26092-052).
    Scheme A selected -> Partner X MUST appear.
    Scheme B selected -> Partner X MUST NOT appear.
    """
    _, TestingSessionLocal = app_client
    from app.models.partner import Partner
    from app.models.partner_scheme import PartnerSchemeMapping
    from app.services.geo_partner_service import GeoPartnerLocatorService

    db = TestingSessionLocal()

    # Clean up if already exists to ensure idempotency
    existing_partners = db.query(Partner).filter((Partner.partner_id == "p-neg-test-x") | (Partner.code == "NEG-TEST-X")).all()
    for ep in existing_partners:
        db.query(PartnerSchemeMapping).filter(PartnerSchemeMapping.partner_id == ep.partner_id).delete()
        db.delete(ep)
    db.commit()

    # Create Partner X exclusively mapped to Scheme A
    px = Partner(
        partner_id="p-neg-test-x",
        name="Exclusive Term Loan Partner X",
        code="NEG-TEST-X",
        partner_type="PSB",
        latitude=28.6139,
        longitude=77.2090,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=True,
        is_active=True,
        is_accepting_applications=True
    )
    db.add(px)
    db.commit()

    # Map Partner X strictly to Scheme A (SIH26092-053)
    mx = PartnerSchemeMapping(
        partner_id=px.partner_id,
        scheme_id="SIH26092-053",
        authorized_category="TERM_LOAN",
        verification_status="VERIFIED_OFFICIAL",
        verification_notes="Exclusively mapped to Scheme A"
    )
    db.add(mx)
    db.commit()

    # 1. Query Scheme A (SIH26092-053) -> Partner X MUST appear
    results_a = GeoPartnerLocatorService.find_nearest_partners(
        db, 28.6139, 77.2090, radius_km=10.0, scheme_id="SIH26092-053"
    )
    p_ids_a = [r["partner"].partner_id for r in results_a]
    assert "p-neg-test-x" in p_ids_a, "Partner X must appear when querying Scheme A"

    # 2. Query Scheme B (SIH26092-052) -> Partner X MUST NOT appear
    results_b = GeoPartnerLocatorService.find_nearest_partners(
        db, 28.6139, 77.2090, radius_km=10.0, scheme_id="SIH26092-052"
    )
    p_ids_b = [r["partner"].partner_id for r in results_b]
    assert "p-neg-test-x" not in p_ids_b, "Partner X must NOT appear when querying Scheme B"

    # 3. Query Direct Portal Scheme (SIH26092-049) -> 0 partners must appear
    results_direct = GeoPartnerLocatorService.find_nearest_partners(
        db, 28.6139, 77.2090, radius_km=50.0, scheme_id="SIH26092-049"
    )
    assert len(results_direct) == 0, "Direct portal scheme must have 0 channel partner results"

    db.close()






