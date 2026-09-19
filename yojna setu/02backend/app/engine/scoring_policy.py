"""
Configurable & Versioned Scoring Policy Engine for YojnaSetu.
Supports reproducible, auditable, and calibrated multi-dimensional recommendation scoring.
Policy Version: v2.1.0
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ScoringPolicy(BaseModel):
    """
    Versioned configuration defining weights, thresholds, penalties, and bonuses
    for the Deterministic Recommendation Engine.
    """
    policy_version: str = Field(default="v2.1.0", description="Semantic policy version tag")
    
    # Base Dimension Weights (7 Dimensions, Sum = 100.0)
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "sector_match": 20.0,
            "applicant_type_match": 15.0,
            "target_group_match": 15.0,
            "business_stage_match": 15.0,
            "activity_match": 10.0,
            "geography_match": 10.0,
            "financial_fit": 15.0,
        },
        description="Factual scoring weights across the 7 core dimensions summing to 100.0"
    )

    # Dimensional Specificity & Missing Data Parameters
    neutral_weight_ratio: float = Field(
        default=0.5,
        description="Fraction of weight assigned when an optional profile attribute was not provided"
    )
    general_scheme_ratio: float = Field(
        default=0.8,
        description="Fraction of weight earned by universal/all-category schemes to reward specialized schemes"
    )

    # Hard Gating Thresholds
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "loan_exceed_ratio_hard_fail": 1.5,
            "loan_below_ratio_hard_fail": 0.5,
            "project_cost_exceed_ratio_hard_fail": 1.5,
        },
        description="Multipliers for hard financial compatibility gates"
    )

    # Statutory Affirmative Action & Relevance Bonuses
    bonuses: Dict[str, float] = Field(
        default_factory=lambda: {
            "sc_woman_priority_bonus": 3.0,
            "rural_artisan_priority_bonus": 2.0,
            "semantic_resonance_max_bonus": 5.0,
        },
        description="Affirmative action and relevance score bonuses"
    )

    # Calibration Penalties
    penalties: Dict[str, float] = Field(
        default_factory=lambda: {
            "unverified_data_penalty": 0.10,
            "aging_data_penalty": 0.05,
        },
        description="Penalties for unverified or stale scheme metadata"
    )

    def total_base_weight(self) -> float:
        """Returns the sum of base weights."""
        return sum(self.weights.values())

    @classmethod
    def get_default_policy(cls) -> "ScoringPolicy":
        """Returns the authoritative v2.1.0 scoring policy instance."""
        return cls()


DEFAULT_SCORING_POLICY = ScoringPolicy.get_default_policy()
