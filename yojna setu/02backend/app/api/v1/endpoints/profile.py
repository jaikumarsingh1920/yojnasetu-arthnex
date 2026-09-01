import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.profile import (
    BeneficiaryProfileInput,
    CitizenProfileResponse,
    calculate_profile_completion,
)
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.engine.recommendation import DeterministicRecommendationEngine

router = APIRouter()


@router.get(
    "",
    response_model=CitizenProfileResponse,
    summary="Get current user's canonical citizen profile",
    description="Returns structured citizen profile, deterministic completion percentage, and annotated missing field list."
)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns stored citizen profile for the authenticated user.
    If no profile has been created yet, returns an initialized empty profile.
    """
    if current_user.profile_data:
        try:
            data = json.loads(current_user.profile_data)
            profile = BeneficiaryProfileInput(**data)
        except Exception:
            profile = BeneficiaryProfileInput()
    else:
        profile = BeneficiaryProfileInput()

    return calculate_profile_completion(profile)


@router.put(
    "",
    response_model=CitizenProfileResponse,
    summary="Update citizen profile with strict backend validation",
    description="Validates and persists citizen profile parameters for deterministic eligibility and smart matching."
)
def update_user_profile(
    profile_input: BeneficiaryProfileInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the authenticated user's citizen profile.
    Enforces validation on all numeric bounds (e.g. non-negative income, valid age).
    Handles partial and complete updates safely without data loss.
    Saves JSON snapshot in the database.
    """
    existing_data = {}
    if current_user.profile_data:
        try:
            existing_data = json.loads(current_user.profile_data)
        except Exception:
            existing_data = {}

    incoming_data = profile_input.model_dump(exclude_unset=True)
    updated_data = {**existing_data, **incoming_data}

    # Auto-align is_sc flag with social_category
    if "social_category" in updated_data and updated_data["social_category"]:
        cat = str(updated_data["social_category"]).upper()
        if cat == "SC":
            updated_data["is_sc"] = True
        elif cat in ["ST", "OBC", "GENERAL", "MINORITY"]:
            updated_data["is_sc"] = False

    validated_profile = BeneficiaryProfileInput(**updated_data)

    # Persist JSON serialized profile
    current_user.profile_data = json.dumps(validated_profile.model_dump())
    db.commit()
    db.refresh(current_user)

    return calculate_profile_completion(validated_profile)


@router.post(
    "/match",
    response_model=RecommendationResponse,
    summary="Perform Smart Matching for current citizen profile",
    description="Evaluates all 90 schemes against the citizen profile using the deterministic Rule Engine."
)
def match_profile_schemes(
    profile_override: Optional[BeneficiaryProfileInput] = None,
    top_k: int = 10,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates current profile against all 90 verified schemes.
    Uses profile_override if provided; otherwise loads user's persisted profile.
    Returns:
    1. Eligible schemes ranked by soft-fit score with verified reasons.
    2. Insufficient information schemes with explicit required fields.
    3. Ineligible schemes with exact deterministic failure explanations.
    """
    if profile_override:
        active_profile = profile_override
    elif current_user and current_user.profile_data:
        try:
            active_profile = BeneficiaryProfileInput(**json.loads(current_user.profile_data))
        except Exception:
            active_profile = BeneficiaryProfileInput()
    else:
        active_profile = BeneficiaryProfileInput()

    req = RecommendationRequest(
        profile=active_profile,
        top_k=top_k,
        include_ineligible=True
    )

    return DeterministicRecommendationEngine.get_recommendations(db, req)
