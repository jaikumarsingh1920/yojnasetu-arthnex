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
def setup_env():
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
def user_a_token(setup_env):
    client, SessionLocal = setup_env
    db = SessionLocal()
    email = "citizen.a@yojnasetu.gov.in"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=hash_password("Pass123!"),
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
def user_b_token(setup_env):
    client, SessionLocal = setup_env
    db = SessionLocal()
    email = "citizen.b@yojnasetu.gov.in"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=hash_password("Pass456!"),
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


# 1. Unauthenticated profile access rejected with 401
def test_unauthenticated_profile_rejected(setup_env):
    client, _ = setup_env
    res1 = client.get("/api/v1/auth/profile")
    assert res1.status_code == 401

    res2 = client.put("/api/v1/auth/profile", json={"age": 30})
    assert res2.status_code == 401

    res3 = client.get("/api/v1/profile")
    assert res3.status_code == 401


# 2. Authenticated user can read own initial profile
def test_read_initial_empty_profile(setup_env, user_a_token):
    client, _ = setup_env
    token, _ = user_a_token
    res = client.get("/api/v1/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "profile" in data
    assert "completion_percentage" in data
    assert "missing_fields" in data
    assert data["completion_percentage"] == 0
    assert len(data["missing_fields"]) == 10


# 3. Create and update citizen profile
def test_update_citizen_profile_auth_endpoint(setup_env, user_a_token):
    client, _ = setup_env
    token, _ = user_a_token
    payload = {
        "age": 28,
        "gender": "FEMALE",
        "state": "UTTAR_PRADESH",
        "district": "Lucknow",
        "social_category": "SC",
        "annual_income": 180000.0,
        "applicant_type": "INDIVIDUAL",
        "employment_status": "SELF_EMPLOYED",
        "education_level": "10TH_PASS",
        "sector": "TEXTILES",
        "business_stage": "NEW_BUSINESS",
        "project_cost": 100000.0,
        "requested_loan_amount": 90000.0,
        "marital_status": "MARRIED",
        "occupation": "Tailor"
    }

    res = client.put(
        "/api/v1/auth/profile",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["profile"]["age"] == 28
    assert data["profile"]["gender"] == "FEMALE"
    assert data["profile"]["state"] == "UTTAR_PRADESH"
    assert data["profile"]["social_category"] == "SC"
    assert data["profile"]["is_sc"] is True
    assert data["profile"]["annual_income"] == 180000.0
    assert data["profile"]["marital_status"] == "MARRIED"
    assert data["completion_percentage"] == 100
    assert len(data["missing_fields"]) == 0


# 4. Partial update does not overwrite existing fields
def test_partial_profile_update(setup_env, user_a_token):
    client, _ = setup_env
    token, _ = user_a_token
    # Only update income and occupation
    partial_payload = {
        "annual_income": 220000.0,
        "occupation": "Master Craftsman"
    }
    res = client.put(
        "/api/v1/auth/profile",
        json=partial_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    # Updated fields
    assert data["profile"]["annual_income"] == 220000.0
    assert data["profile"]["occupation"] == "Master Craftsman"
    # Preserved fields
    assert data["profile"]["age"] == 28
    assert data["profile"]["gender"] == "FEMALE"
    assert data["profile"]["state"] == "UTTAR_PRADESH"
    assert data["profile"]["social_category"] == "SC"
    assert data["profile"]["is_sc"] is True


# 5. User isolation: User B cannot access or see User A's profile
def test_user_profile_isolation(setup_env, user_a_token, user_b_token):
    client, _ = setup_env
    token_a, _ = user_a_token
    token_b, _ = user_b_token

    # User A has profile
    res_a = client.get("/api/v1/auth/profile", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    assert res_a.json()["profile"]["annual_income"] == 220000.0

    # User B gets their own profile (which is empty)
    res_b = client.get("/api/v1/auth/profile", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    assert res_b.json()["profile"]["annual_income"] is None
    assert res_b.json()["completion_percentage"] == 0

    # User B updates their profile to different values
    res_b_update = client.put(
        "/api/v1/auth/profile",
        json={"age": 45, "gender": "MALE", "state": "MAHARASHTRA", "social_category": "OBC"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b_update.status_code == 200
    assert res_b_update.json()["profile"]["age"] == 45
    assert res_b_update.json()["profile"]["gender"] == "MALE"

    # User A's profile remains strictly intact and unchanged
    res_a_check = client.get("/api/v1/auth/profile", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_check.json()["profile"]["age"] == 28
    assert res_a_check.json()["profile"]["gender"] == "FEMALE"


# 6. Validation errors for invalid bounds
def test_profile_validation_errors(setup_env, user_a_token):
    client, _ = setup_env
    token, _ = user_a_token

    # Negative income
    bad_income = client.put(
        "/api/v1/auth/profile",
        json={"annual_income": -10000},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bad_income.status_code in [400, 422]

    # Negative project cost
    bad_cost = client.put(
        "/api/v1/auth/profile",
        json={"project_cost": -50000},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bad_cost.status_code in [400, 422]

    # Age out of range
    bad_age = client.put(
        "/api/v1/auth/profile",
        json={"age": 140},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bad_age.status_code in [400, 422]


# 7. Recommendations automatic evaluation using user profile
def test_recommendation_uses_stored_profile(setup_env, user_a_token):
    client, _ = setup_env
    token, _ = user_a_token

    # Call smart match without explicit override -> uses stored profile
    res = client.post(
        "/api/v1/profile/match?top_k=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["evaluated_scheme_count"] >= 56
    assert data["eligible_scheme_count"] > 0
    assert len(data["recommendations"]) > 0


# 8. Temporary recommendation override does NOT overwrite stored profile
def test_temporary_override_does_not_overwrite_profile(setup_env, user_a_token):
    client, _ = setup_env
    token, _ = user_a_token

    # Simulate with override profile (e.g. Age 65, Male, Gujarat, General)
    temp_profile = {
        "age": 65,
        "gender": "MALE",
        "state": "GUJARAT",
        "social_category": "GENERAL",
        "annual_income": 600000.0,
        "project_cost": 500000.0
    }
    res = client.post(
        "/api/v1/profile/match?top_k=5",
        json=temp_profile,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200

    # Confirm User A's stored profile is still the original (Age 28, Female, UP, SC)
    check_profile = client.get("/api/v1/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert check_profile.status_code == 200
    prof = check_profile.json()["profile"]
    assert prof["age"] == 28
    assert prof["gender"] == "FEMALE"
    assert prof["state"] == "UTTAR_PRADESH"
    assert prof["social_category"] == "SC"
