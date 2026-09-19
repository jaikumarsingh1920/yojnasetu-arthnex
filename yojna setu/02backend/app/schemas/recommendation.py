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
    eligibility_status: str = Field(..., description="ELIGIBLE, INELIGIBLE, INSUFFICIENT_INFORMATION, CONDITIONAL, or NOT_APPLICABLE")
    score: float = Field(..., description="Normalized soft-fit score between 0.0 and 100.0")
    eligible: bool = Field(default=True, description="True if eligibility_status is ELIGIBLE, else False")
    short_description: Optional[str] = Field(None, description="Short summary of scheme purpose")
    purpose: Optional[str] = Field(None, description="Official purpose or objective of the scheme")

    # Structured explainability rules for TASK-032
    matched_rules: List[str] = Field(default_factory=list, description="Factual reasons why applicant qualifies (passed rules)")
    failed_rules: List[str] = Field(default_factory=list, description="Factual reasons why applicant fails (failed rules)")
    missing_information: List[str] = Field(default_factory=list, description="Required profile fields that were not provided")

    # Multi-dimensional matching factors
    matched_factors: List[str] = Field(default_factory=list, description="List of dimensions that matched")
    unmatched_factors: List[str] = Field(default_factory=list, description="List of dimensions that did not match")
    not_evaluated_factors: List[str] = Field(default_factory=list, description="List of dimensions not evaluated due to missing data")

    eligibility_reasons: List[str] = Field(default_factory=list, description="Hard eligibility pass explanations")
    recommendation_reasons: List[str] = Field(default_factory=list, description="Key positive recommendation drivers")
    score_breakdown: List[ScoreDimensionBreakdown] = Field(default_factory=list, description="Per-dimension detailed scoring audit")

    # Financial and Scheme-Aware Calculator Fields
    financial_category: Optional[str] = Field("LOAN_CREDIT", description="LOAN_CREDIT, GRANT_SUBSIDY, SCHOLARSHIP, TRAINING_SKILL, GUARANTEE_CREDIT_SUPPORT, DIRECT_BENEFIT, NON_FINANCIAL")
    is_credit_scheme: bool = Field(default=True, description="True if loan/credit scheme where EMI applies")
    calculator_applicable: bool = Field(default=True, description="True if financial calculator is applicable")
    financial_assistance_summary: Optional[str] = Field(None, description="Factual financial assistance / benefit summary")
    max_loan_amount: Optional[float] = Field(None, description="Official max loan amount")
    interest_rate: Optional[float] = Field(None, description="Official interest rate % p.a.")
    repayment_period_max_months: Optional[int] = Field(None, description="Official max repayment period in months")
    subsidy_percentage: Optional[float] = Field(None, description="Official subsidy percentage")
    grant_amount: Optional[float] = Field(None, description="Official grant amount")

    # Provenance and official portal links
    ministry: Optional[str] = Field(None, description="Governing Ministry / Department")
    source_organization: Optional[str] = Field(None, description="Nodal implementing organization e.g. NSFDC")
    official_portal: Optional[str] = Field(None, description="Official government scheme portal URL")
    application_url: Optional[str] = Field(None, description="Direct online application URL")
    official_source_url: Optional[str] = Field(None, description="Official scheme guidelines reference URL")
    source_document: Optional[str] = Field(None, description="Official source document name")
    is_direct_portal_scheme: bool = Field(default=False, description="True if applications are submitted directly on government portal")
    has_verified_partner_mapping: bool = Field(default=False, description="True if verified channel partner mapping exists")
    application_channel: str = Field("OFFICIAL_DIRECT_PORTAL", description="OFFICIAL_DIRECT_PORTAL or CHANNEL_PARTNER_LOCATOR")

    # Financial Health Suitability Advisory
    financial_health_status: Optional[str] = Field(None, description="Citizen financial health rating: HEALTHY, MODERATE, STRESSED, HIGH_RISK, INSUFFICIENT_INFORMATION")
    financial_health_advisory: Optional[str] = Field(None, description="Advisory guidance on financial suitability for this scheme")
    financial_suitability: Optional[str] = Field(None, description="STRONG_FIT, POSSIBLE_FIT, INSUFFICIENT_INFORMATION, FINANCIALLY_UNSUITABLE")
    financial_suitability_reason: Optional[str] = Field(None, description="Deterministic factual explanation of scheme financial fit")
    estimated_monthly_installment: Optional[float] = Field(None, description="Estimated monthly repayment installment under this scheme")
    available_subsidy_amount: Optional[float] = Field(None, description="Estimated capital/margin subsidy in INR")
    required_own_contribution: Optional[float] = Field(None, description="Required promoter margin money in INR")
    min_project_cost: Optional[float] = Field(None, description="Official minimum project cost")
    max_project_cost: Optional[float] = Field(None, description="Official maximum project cost")
    min_loan_amount: Optional[float] = Field(None, description="Official minimum loan limit")
    collateral_requirement: Optional[str] = Field(None, description="Collateral policy (NO, YES, CONDITIONAL, NOT_PUBLICLY_AVAILABLE)")
    guarantee_requirement: Optional[str] = Field(None, description="Credit guarantee coverage (e.g. CGTMSE) or status")
    processing_fee: Optional[str] = Field(None, description="Processing fee details")

    # Auditability, Policy Versioning & Ranking Explanation
    scoring_policy_version: Optional[str] = Field("v2.1.0", description="Scoring policy version used for evaluation")
    data_quality_score: Optional[float] = Field(None, description="Objective scheme data quality and completeness score (0-100)")
    comparative_ranking_reason: Optional[str] = Field(None, description="Factual explanation of why this scheme earned its relative ranking")
    match_tier: Optional[str] = Field("ELIGIBLE", description="BEST_MATCH, ELIGIBLE, or POTENTIALLY_RELEVANT")
    required_documents: List[str] = Field(default_factory=list, description="Documents required for application")
    partner_availability: Optional[str] = Field(None, description="Availability of physical or online partner channel")
    key_conditions: List[str] = Field(default_factory=list, description="Important statutory conditions or guidelines")
    bonuses: List[str] = Field(default_factory=list, description="List of affirmative policy bonuses earned")
    penalties: List[str] = Field(default_factory=list, description="List of policy penalties applied")


class RecommendationRequest(BaseModel):
    profile: BeneficiaryProfileInput = Field(..., description="Beneficiary profile attributes")
    top_k: int = Field(default=5, ge=1, le=100, description="Maximum number of top recommendations to return")
    include_ineligible: bool = Field(default=True, description="Whether to include evaluated ineligible schemes with failure explanations")
    semantic_query: Optional[str] = Field(None, description="Optional natural language query or description for semantic relevance ranking")


class RecommendationResponse(BaseModel):
    profile_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of provided beneficiary profile fields")
    scoring_policy_version: Optional[str] = Field("v2.1.0", description="Scoring policy version applied")
    recommendation_trace_id: Optional[str] = Field(None, description="Unique deterministic trace ID for auditability")
    candidate_shortlist_count: Optional[int] = Field(None, description="Candidate schemes pre-filtered before in-memory scoring")
    evaluated_scheme_count: int = Field(..., description="Total schemes evaluated against hard eligibility gate")
    eligible_scheme_count: int = Field(..., description="Count of schemes passing hard eligibility gate")
    excluded_scheme_count: int = Field(..., description="Count of schemes excluded by hard eligibility gate")
    insufficient_info_scheme_count: int = Field(..., description="Count of schemes with insufficient eligibility information")
    conditional_scheme_count: int = Field(default=0, description="Count of conditional schemes")
    not_applicable_scheme_count: int = Field(default=0, description="Count of not-applicable schemes")
    recommendations: List[RecommendationItem] = Field(default_factory=list, description="Top-K ranked scheme recommendations")
    ineligible_schemes: List[RecommendationItem] = Field(default_factory=list, description="Evaluated schemes that failed eligibility with exact failed rules")
    insufficient_info_schemes: List[RecommendationItem] = Field(default_factory=list, description="Evaluated schemes requiring more information")
    conditional_schemes: List[RecommendationItem] = Field(default_factory=list, description="Conditional schemes requiring special conditions")
    not_applicable_schemes: List[RecommendationItem] = Field(default_factory=list, description="Non-applicable/discontinued schemes")
    missing_profile_fields: List[str] = Field(default_factory=list, description="Beneficiary profile fields that were missing/None")
