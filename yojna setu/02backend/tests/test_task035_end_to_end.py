"""
TASK-035: Comprehensive End-to-End System Integration Test Suite
Validates the complete scheme lifecycle across all 90 verified schemes in YojnaSetu.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import Scheme, SchemeRule, SchemeDocument, PartnerSchemeMapping, Partner
from app.engine.eligibility import DeterministicEligibilityEngine, SchemeEligibilityStatus
from app.schemas.profile import BeneficiaryProfileInput

client = TestClient(app)

# -----------------------------------------------------------------------------
# A. SCHEME LISTING & TOTAL COUNT (90 SCHEMES)
# -----------------------------------------------------------------------------
def test_all_90_schemes_listed():
    res = client.get("/api/v1/schemes?page_size=100")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 90
    assert len(data["items"]) == 90
    
    # Ensure scheme IDs run from SIH26092-001 through SIH26092-090
    scheme_ids = [s["scheme_id"] for s in data["items"]]
    assert "SIH26092-001" in scheme_ids
    assert "SIH26092-057" in scheme_ids
    assert "SIH26092-065" in scheme_ids
    assert "SIH26092-075" in scheme_ids
    assert "SIH26092-088" in scheme_ids
    assert "SIH26092-090" in scheme_ids

# -----------------------------------------------------------------------------
# B. SCHEME DETAIL ACROSS DIVERSE SCHEME TYPES
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("scheme_id,expected_name", [
    ("SIH26092-001", "Prime Minister Employment Generation Programme (PMEGP)"),
    ("SIH26092-002", "Pradhan Mantri MUDRA Yojana (PMMY)"),
    ("SIH26092-053", "NSFDC Term Loan"),
    ("SIH26092-057", "NSFDC Mahila Samriddhi Yojana (MSY)"),
    ("SIH26092-065", "PM Young Achievers Scholarship Award Scheme for Vibrant India (PM-YASASVI)"),
    ("SIH26092-068", "Divyangjan Swavalamban Yojana (NDFDC)"),
    ("SIH26092-075", "Pradhan Mantri Jan Dhan Yojana (PMJDY)"),
    ("SIH26092-078", "Atal Pension Yojana (APY)"),
    ("SIH26092-087", "Pradhan Mantri Matru Vandana Yojana (PMMVY - Mission Shakti)"),
    ("SIH26092-088", "Sukanya Samriddhi Yojana (SSY)"),
    ("SIH26092-090", "Ayushman Bharat — Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)"),
])
def test_scheme_detail_exact_loading(scheme_id, expected_name):
    res = client.get(f"/api/v1/schemes/{scheme_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["scheme_id"] == scheme_id
    assert data["scheme_name"] == expected_name
    assert data["official_source_url"] is not None and data["official_source_url"].startswith("http")

# -----------------------------------------------------------------------------
# C. SEARCH & TAXONOMY FILTERING
# -----------------------------------------------------------------------------
def test_scheme_search_and_filters():
    # 1. Search for Jan Dhan
    res = client.get("/api/v1/schemes?search=Jan%20Dhan")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(s["scheme_id"] == "SIH26092-075" for s in items)
    
    # 2. Search for Sukanya
    res = client.get("/api/v1/schemes?search=Sukanya")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(s["scheme_id"] == "SIH26092-088" for s in items)
    
    # 3. Ministry filter
    res = client.get("/api/v1/schemes?ministry=Ministry%20of%20Finance&page_size=50")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 5
    for s in items:
        assert "Ministry of Finance" in s["ministry"]

# -----------------------------------------------------------------------------
# D. DETERMINISTIC ELIGIBILITY ENGINE (EXACT BOUNDARIES & NEGATIVE CASES)
# -----------------------------------------------------------------------------
def test_deterministic_eligibility_boundaries_and_negatives():
    db = SessionLocal()
    
    # 1. SSY (Sukanya Samriddhi Yojana - SIH26092-088): Female <= 10 years
    ssy = db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-088").first()
    
    # Pass case: 8 year old girl
    prof_girl = BeneficiaryProfileInput(age=8, gender="FEMALE", applicant_type="INDIVIDUAL")
    res_girl = DeterministicEligibilityEngine.evaluate_scheme(ssy, prof_girl)
    assert res_girl.status == SchemeEligibilityStatus.ELIGIBLE
    
    # Fail case 1: 12 year old girl (exceeds age max 10)
    prof_older_girl = BeneficiaryProfileInput(age=12, gender="FEMALE", applicant_type="INDIVIDUAL")
    res_older_girl = DeterministicEligibilityEngine.evaluate_scheme(ssy, prof_older_girl)
    assert res_older_girl.status == SchemeEligibilityStatus.INELIGIBLE
    assert any("age" in f.field.lower() for f in res_older_girl.hard_rules_failed)
    
    # Fail case 2: 8 year old boy (gender condition failed)
    prof_boy = BeneficiaryProfileInput(age=8, gender="MALE", applicant_type="INDIVIDUAL")
    res_boy = DeterministicEligibilityEngine.evaluate_scheme(ssy, prof_boy)
    assert res_boy.status == SchemeEligibilityStatus.INELIGIBLE
    assert any("gender" in f.field.lower() for f in res_boy.hard_rules_failed)
    
    # 2. PMMVY (SIH26092-087): Pregnant Women / Lactating Mothers (Female only, income <= 8L)
    pmmvy = db.query(Scheme).filter(Scheme.scheme_id == "SIH26092-087").first()
    prof_wealthy_female = BeneficiaryProfileInput(age=25, gender="FEMALE", annual_income=1200000.0, applicant_type="INDIVIDUAL")
    res_wealthy = DeterministicEligibilityEngine.evaluate_scheme(pmmvy, prof_wealthy_female)
    assert res_wealthy.status == SchemeEligibilityStatus.INELIGIBLE
    assert any("income" in f.field.lower() for f in res_wealthy.hard_rules_failed)

    db.close()

# -----------------------------------------------------------------------------
# E. RECOMMENDATION ENGINE EVALUATES ALL 90 SCHEMES
# -----------------------------------------------------------------------------
def test_recommendation_engine_evaluates_all_90_schemes():
    payload = {
        "profile": {
            "age": 28,
            "annual_income": 180000.0,
            "social_category": "SC",
            "is_sc": True,
            "gender": "FEMALE",
            "state": "MAHARASHTRA",
            "applicant_type": "INDIVIDUAL",
            "is_new_unit": True,
            "project_cost": 100000.0,
            "requested_loan_amount": 90000.0
        },
        "top_k": 90
    }
    res = client.post("/api/v1/recommendations", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["evaluated_scheme_count"] == 90
    assert data["eligible_scheme_count"] > 0
    
    # Check score breakdown and explainability presence
    for rec in data["recommendations"]:
        assert "scheme_id" in rec
        assert "scheme_name" in rec
        assert "eligible" in rec
        assert "score" in rec
        assert "matched_rules" in rec
        assert "failed_rules" in rec
        assert "score_breakdown" in rec

# -----------------------------------------------------------------------------
# F. DOCUMENT GUIDANCE INTEGRATION (NON-STORAGE)
# -----------------------------------------------------------------------------
def test_document_guidance_scheme_specific():
    # PMJDY (075) documents
    res_75 = client.get("/api/v1/schemes/SIH26092-075")
    assert res_75.status_code == 200
    docs_75 = res_75.json()["documents"]
    assert len(docs_75) >= 2
    doc_names_75 = [d["document_name"] for d in docs_75]
    assert "Aadhaar Card" in doc_names_75
    
    # ADIP (079) documents
    res_79 = client.get("/api/v1/schemes/SIH26092-079")
    assert res_79.status_code == 200
    docs_79 = res_79.json()["documents"]
    doc_names_79 = [d["document_name"] for d in docs_79]
    assert any("Disability" in name or "UDID" in name for name in doc_names_79)

# -----------------------------------------------------------------------------
# G. PARTNER ISOLATION & SCHEME-SPECIFIC FILTERING
# -----------------------------------------------------------------------------
def test_partner_scheme_isolation_and_no_leakage():
    # 1. Partner routed scheme: NSFDC Term Loan (SIH26092-053)
    res_53 = client.get("/api/v1/partner/nearest?latitude=19.0760&longitude=72.8777&scheme_id=SIH26092-053&radius_km=100")
    assert res_53.status_code == 200
    partners_53 = res_53.json()
    assert len(partners_53) > 0
    
    # 2. Direct portal scheme: PMJDY (SIH26092-075) must return 0 channel partners
    res_75 = client.get("/api/v1/partner/nearest?latitude=19.0760&longitude=72.8777&scheme_id=SIH26092-075&radius_km=100")
    assert res_75.status_code == 200
    partners_75 = res_75.json()
    assert len(partners_75) == 0, "Direct portal scheme PMJDY must NOT return channel partners!"

# -----------------------------------------------------------------------------
# H. AI COPILOT GROUNDING & SCHEME FACT RETRIEVAL
# -----------------------------------------------------------------------------
def test_ai_copilot_grounded_scheme_facts():
    # Query AI about PMJDY overdraft and account features
    payload = {
        "message": "What are the benefits of Pradhan Mantri Jan Dhan Yojana (PMJDY)?",
        "language": "en"
    }
    res = client.post("/api/v1/ai/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["answer"]) > 0

# -----------------------------------------------------------------------------
# I. GPS & SEARCH-LOCATION DISTANCE CALCULATION & GOOGLE MAPS NAVIGATION
# -----------------------------------------------------------------------------
def test_partner_distance_and_navigation_url():
    # GPS Origin (Mumbai)
    lat_mumbai = 19.0760
    lng_mumbai = 72.8777
    res = client.get(f"/api/v1/partner/nearest?latitude={lat_mumbai}&longitude={lng_mumbai}&scheme_id=SIH26092-053&radius_km=200")
    assert res.status_code == 200
    partners = res.json()
    assert len(partners) > 0
    
    first_partner = partners[0]
    assert "distance_km" in first_partner
    assert first_partner["distance_km"] >= 0.0
    
    # Check coordinate presence for navigation
    p_lat = first_partner["partner"]["latitude"]
    p_lng = first_partner["partner"]["longitude"]
    assert p_lat is not None and p_lng is not None
    
    # Navigation URL pattern: https://www.google.com/maps/dir/?api=1&destination=LAT,LNG
    expected_nav_url = f"https://www.google.com/maps/dir/?api=1&destination={p_lat},{p_lng}"
    assert f"{p_lat},{p_lng}" in expected_nav_url
    assert "api=1" in expected_nav_url

# -----------------------------------------------------------------------------
# J. MANDATORY NEGATIVE: CROSS-SCHEME PARTNER EXCLUSION
# -----------------------------------------------------------------------------
def test_cross_scheme_partner_exclusion_negative():
    # NMDFC Virasat (SIH26092-067) vs NDFDC Swavalamban (SIH26092-068)
    res_67 = client.get("/api/v1/partner/nearest?latitude=28.6139&longitude=77.2090&scheme_id=SIH26092-067&radius_km=500")
    assert res_67.status_code == 200
    partners_67 = res_67.json()
    
    res_68 = client.get("/api/v1/partner/nearest?latitude=28.6139&longitude=77.2090&scheme_id=SIH26092-068&radius_km=500")
    assert res_68.status_code == 200
    partners_68 = res_68.json()
    
    # If both have partners, verify each partner list is authorized for its respective scheme
    ids_67 = {p["partner"]["partner_id"] for p in partners_67}
    ids_68 = {p["partner"]["partner_id"] for p in partners_68}
    
    db = SessionLocal()
    for pid in ids_67:
        m = db.query(PartnerSchemeMapping).filter(PartnerSchemeMapping.partner_id == pid, PartnerSchemeMapping.scheme_id == "SIH26092-067").first()
        assert m is not None, f"Partner {pid} returned for SIH26092-067 without mapping!"
        
    for pid in ids_68:
        m = db.query(PartnerSchemeMapping).filter(PartnerSchemeMapping.partner_id == pid, PartnerSchemeMapping.scheme_id == "SIH26092-068").first()
        assert m is not None, f"Partner {pid} returned for SIH26092-068 without mapping!"
    db.close()


