from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.profile import BeneficiaryProfileInput


class ScoreDimensionResult(str):
    MATCH = "MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NO_MATCH = "NO_MATCH"
    NOT_EVALUATED = "NOT_EVALUATED"


class ScoreDimensionBreakdown(BaseModel):
    dimension: str = Field(..., description="Name of the scoring dimension e.g. sector_match")
    max_weight: float = Field(..., description="Maximum configurable weight assigned to this dimension")
    score: float = Field(..., description="Actual score earned for this dimension")
    result: str = Field(..., description="MATCH, PARTIAL_MATCH, NO_MATCH, or NOT_EVALUATED")
    reason: str = Field(..., description="Factual explanation for the dimension result")


class RecommendationItem(BaseModel):
    rank: int = Field(..., description="1-indexed recommendation rank")
    scheme_id: str = Field(..., description="Authoritative scheme ID")
    scheme_name: str = Field(..., description="Official scheme name")
    eligibility_status: str = Field(..., description="ELIGIBLE or CONDITIONAL")
    score: float = Field(..., description="Normalized soft-fit score between 0.0 and 100.0")

    matched_factors: List[str] = Field(default_factory=list, description="List of dimensions that matched")
    unmatched_factors: List[str] = Field(default_factory=list, description="List of dimensions that did not match")
    not_evaluated_factors: List[str] = Field(default_factory=list, description="List of dimensions not evaluated due to missing data")

    eligibility_reasons: List[str] = Field(default_factory=list, description="Hard eligibility pass explanations")
    recommendation_reasons: List[str] = Field(default_factory=list, description="Key positive recommendation drivers")
    score_breakdown: List[ScoreDimensionBreakdown] = Field(default_factory=list, description="Per-dimension detailed scoring audit")


class RecommendationRequest(BaseModel):
    profile: BeneficiaryProfileInput = Field(..., description="Beneficiary profile attributes")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of top recommendations to return")


class RecommendationResponse(BaseModel):
    profile_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of provided beneficiary profile fields")
    evaluated_scheme_count: int = Field(..., description="Total schemes evaluated against hard eligibility gate (always 56)")
    eligible_scheme_count: int = Field(..., description="Count of schemes passing hard eligibility gate")
    excluded_scheme_count: int = Field(..., description="Count of schemes excluded by hard eligibility gate")
    insufficient_info_scheme_count: int = Field(..., description="Count of schemes with insufficient eligibility information")
    recommendations: List[RecommendationItem] = Field(default_factory=list, description="Top-K ranked scheme recommendations")
    missing_profile_fields: List[str] = Field(default_factory=list, description="Beneficiary profile fields that were missing/None")
