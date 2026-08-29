from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.engine.recommendation import DeterministicRecommendationEngine

router = APIRouter()


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get top-K scheme recommendations for beneficiary profile",
    description="Evaluates all 56 schemes through hard eligibility gate and ranks eligible candidates using deterministic soft-fit scoring."
)
def get_recommendations(
    req: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    1. Validates beneficiary profile input.
    2. Evaluates all 56 verified schemes against hard eligibility rules via DeterministicEligibilityEngine.
    3. Excludes hard-ineligible schemes.
    4. Calculates transparent 7-dimensional soft-fit match score (0.0 - 100.0) for eligible candidates.
    5. Applies deterministic ranking (score DESC, scheme_id ASC).
    6. Returns top-K recommendations with explainable match breakdowns and recommendation reasons.
    """
    return DeterministicRecommendationEngine.get_recommendations(db, req)
