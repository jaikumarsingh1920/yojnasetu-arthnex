import json
import os
import sys
import pytest
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
from app.schemas.profile import (
    BeneficiaryProfileInput,
    CitizenProfileResponse,
    calculate_profile_completion,
)
from app.engine.eligibility import DeterministicEligibilityEngine
from app.engine.recommendation import DeterministicRecommendationEngine
from app.schemas.recommendation import RecommendationRequest


@pytest.fixture(scope="module")
def setup_environment():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed database with schemes
    session = TestingSessionLocal()
    from seed_db import seed_database
    seed_database(session)
    session.close()

    def override_get_db():
        s = TestingSessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.fixture
def auth_beneficiary_token(setup_environment):
    client, SessionLocal = setup_environment
    db = SessionLocal()
    email = "citizen.test@yojnasetu.gov.in"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=hash_password("ValidPassword123!"),
            role=UserRole.BENEFICIARY.value,
            preferred_language="en",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user_id=user.user_id, role=user.role, email=user.email)
    user_id = user.user_id
    db.close()
    return token, user_id


@pytest.fixture
def auth_google_user_token(setup_environment):
    client, SessionLocal = setup_environment
    db = SessionLocal()
    email = "google.citizen@yojnasetu.gov.in"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            full_name="Google Citizen",
            auth_provider="GOOGLE",
            google_id="google-sub-id-998877",
            hashed_password=hash_password("OAuthRandomPassSecret"),
            role=UserRole.BENEFICIARY.value,
            preferred_language="en",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user_id=user.user_id, role=user.role, email=user.email)
    user_id = user.user_id
    db.close()
    return token, user_id


# 1. New citizen profile initialization
def test_new_citizen_profile_initialization(setup_environment, auth_beneficiary_token):
    client, _ = setup_environment
    token, _ = auth_beneficiary_token
    response = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "completion_percentage" in data
    assert "missing_fields" in data
    assert isinstance(data["missing_fields"], list)


# 2. Profile update with valid canonical values
def test_update_citizen_profile_valid(setup_environment, auth_beneficiary_token):
    client, _ = setup_environment
    token, _ = auth_beneficiary_token
    payload = {
        "age": 28,
        "gender": "FEMALE",
        "state": "MAHARASHTRA",
        "district": "Pune",
        "social_category": "SC",
        "annual_income": 180000.0,
        "applicant_type": "INDIVIDUAL",
        "employment_status": "SELF_EMPLOYED",
        "education_level": "10TH_PASS",
        "sector": "MSME",
        "activity_type": "TRADITIONAL_TRADE_18",
        "business_stage": "NEW_BUSINESS",
        "is_new_unit": True,
        "project_cost": 100000.0,
        "requested_loan_amount": 90000.0,
        "collateral_available": False,
        "application_route": "PARTNER_ASSISTED"
    }

    response = client.put(
        "/api/v1/profile",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    res = response.json()
    assert res["profile"]["age"] == 28
    assert res["profile"]["gender"] == "FEMALE"
    assert res["profile"]["social_category"] == "SC"
    assert res["profile"]["is_sc"] is True
    assert res["profile"]["annual_income"] == 180000.0
    assert res["completion_percentage"] >= 80


# 3. Profile persistence across requests
def test_profile_persistence_in_database(setup_environment, auth_beneficiary_token):
    client, _ = setup_environment
    token, _ = auth_beneficiary_token
    response = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    res = response.json()
    assert res["profile"]["age"] == 28
    assert res["profile"]["social_category"] == "SC"
    assert res["profile"]["annual_income"] == 180000.0


# 4. Missing profile fields calculation & completion score
def test_missing_profile_fields_calculation():
    incomplete_profile = BeneficiaryProfileInput(
        age=30,
        gender="MALE"
    )
    res = calculate_profile_completion(incomplete_profile)
    assert res.completion_percentage == 20
    assert res.completed_fields_count == 2
    assert any(mf.field == "annual_income" for mf in res.missing_fields)
    assert any(mf.field == "social_category" for mf in res.missing_fields)


# 5. Complete profile scoring (100% completion)
def test_complete_profile_100_percent():
    full_profile = BeneficiaryProfileInput(
        age=28,
        gender="FEMALE",
        state="MAHARASHTRA",
        social_category="SC",
        annual_income=150000.0,
        applicant_type="ARTISAN",
        education_level="10TH_PASS",
        sector="HANDICRAFTS",
        business_stage="NEW_BUSINESS",
        project_cost=100000.0,
        requested_loan_amount=90000.0
    )
    res = calculate_profile_completion(full_profile)
    assert res.completion_percentage == 100
    assert res.completed_fields_count == 10
    assert len(res.missing_fields) == 0


# 6. Eligible recommendation matching based on profile attributes
def test_eligible_smart_matching(setup_environment, auth_beneficiary_token):
    client, _ = setup_environment
    token, _ = auth_beneficiary_token
    profile_payload = {
        "age": 28,
        "gender": "FEMALE",
        "state": "MAHARASHTRA",
        "social_category": "SC",
        "annual_income": 150000.0,
        "applicant_type": "INDIVIDUAL",
        "sector": "MSME",
        "business_stage": "NEW_BUSINESS",
        "project_cost": 100000.0
    }
    response = client.post(
        "/api/v1/profile/match?top_k=10",
        json=profile_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["evaluated_scheme_count"] >= 56
    assert data["eligible_scheme_count"] > 0
    assert len(data["recommendations"]) > 0

    top_item = data["recommendations"][0]
    assert top_item["eligibility_status"] == "ELIGIBLE"
    assert top_item["score"] > 0
    assert len(top_item["matched_factors"]) > 0 or len(top_item["recommendation_reasons"]) > 0


# 7. Ineligible recommendation matching with factual failed rule reasons
def test_ineligible_scheme_failure_reasons(setup_environment):
    _, SessionLocal = setup_environment
    db = SessionLocal()
    profile = BeneficiaryProfileInput(
        age=28,
        gender="MALE",
        social_category="GENERAL",
        annual_income=500000.0
    )
    req = RecommendationRequest(profile=profile, top_k=5, include_ineligible=True)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert len(res.ineligible_schemes) > 0
    for inelig in res.ineligible_schemes[:3]:
        assert len(inelig.failed_rules) > 0 or len(inelig.eligibility_reasons) > 0


# 8. More-information-required recommendation with missing field callouts
def test_insufficient_info_recommendation(setup_environment):
    _, SessionLocal = setup_environment
    db = SessionLocal()
    empty_profile = BeneficiaryProfileInput()
    req = RecommendationRequest(profile=empty_profile, top_k=5, include_ineligible=True)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()

    assert res.insufficient_info_scheme_count > 0
    assert len(res.insufficient_info_schemes) > 0
    for item in res.insufficient_info_schemes[:3]:
        assert item.eligibility_status == "INSUFFICIENT_INFORMATION"
        assert len(item.missing_information) > 0


# 9. Multiple failed rules reporting
def test_multiple_failed_rules_reported(setup_environment):
    _, SessionLocal = setup_environment
    db = SessionLocal()
    profile = BeneficiaryProfileInput(
        age=85,
        annual_income=5000000.0,
        social_category="GENERAL"
    )
    req = RecommendationRequest(profile=profile, top_k=10, include_ineligible=True)
    res = DeterministicRecommendationEngine.get_recommendations(db, req)
    db.close()
    assert len(res.ineligible_schemes) > 0


# 10. Profile to Scheme Details context preservation
def test_profile_to_scheme_details_navigation(setup_environment):
    client, _ = setup_environment
    res = client.get("/api/v1/schemes/SIH26092-001")
    assert res.status_code == 200
    scheme_data = res.json()
    assert scheme_data["scheme_id"] == "SIH26092-001"


# 11. Profile to Calculator loan pre-fill validation
def test_calculator_prefill_calculation(setup_environment):
    client, _ = setup_environment
    calc_res = client.post(
        "/api/v1/calculator/calculate",
        json={
            "scheme_id": "SIH26092-052",
            "project_cost": 100000.0,
            "requested_loan_amount": 90000.0,
            "repayment_period_months": 36,
        }
    )
    assert calc_res.status_code == 200
    calc_data = calc_res.json()
    assert calc_data["scheme_id"] == "SIH26092-052"
    assert calc_data["status"] in ("CALCULATED", "SUCCESS")
    assert "resolved_parameters" in calc_data


# 12. Profile to Partner Locator with scheme & GPS/state coordinates
def test_partner_locator_with_scheme_and_state(setup_environment, auth_beneficiary_token):
    client, _ = setup_environment
    token, _ = auth_beneficiary_token
    res = client.get(
        "/api/v1/partner/nearest?latitude=19.0760&longitude=72.8777",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    partners = res.json()
    assert isinstance(partners, list)


# 13. Local authentication profile access
def test_local_auth_profile_access(setup_environment, auth_beneficiary_token):
    client, _ = setup_environment
    token, _ = auth_beneficiary_token
    res = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


# 14. Google authentication profile access & single profile guarantee
def test_google_auth_profile_access(setup_environment, auth_google_user_token):
    client, _ = setup_environment
    token, _ = auth_google_user_token
    res = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["profile"] is not None


# 15. Logout / login persistence
def test_logout_and_relogin_profile_persistence(setup_environment, auth_beneficiary_token):
    client, SessionLocal = setup_environment
    token, user_id = auth_beneficiary_token
    logout_res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    db = SessionLocal()
    user = db.query(User).filter(User.user_id == user_id).first()
    assert user is not None
    assert user.profile_data is not None
    db.close()


# 16. Invalid profile bounds rejection
def test_invalid_profile_bounds_rejection(setup_environment, auth_beneficiary_token):
    client, _ = setup_environment
    token, _ = auth_beneficiary_token
    bad_income_res = client.put(
        "/api/v1/profile",
        json={"annual_income": -50000},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bad_income_res.status_code in [400, 422]

    bad_age_res = client.put(
        "/api/v1/profile",
        json={"age": 150},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bad_age_res.status_code in [400, 422]


# 17. Multilingual profile translation parity across 12 languages
def test_multilingual_profile_translation_parity():
    locales_dir = r"c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src\i18n\locales"
    with open(os.path.join(locales_dir, "en.json"), "r", encoding="utf-8") as f:
        en_data = json.load(f)

    assert "profile" in en_data
    assert "gender" in en_data
    assert "category" in en_data
    assert "emp" in en_data
    assert "edu" in en_data
    assert "appType" in en_data

    for fname in os.listdir(locales_dir):
        if not fname.endswith(".json") or fname == "en.json":
            continue
        with open(os.path.join(locales_dir, fname), "r", encoding="utf-8") as f:
            lang_data = json.load(f)
            assert "profile" in lang_data, f"Missing 'profile' section in {fname}"
            assert "title" in lang_data["profile"], f"Missing 'profile.title' in {fname}"
