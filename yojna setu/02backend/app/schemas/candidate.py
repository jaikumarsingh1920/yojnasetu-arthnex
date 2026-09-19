from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CandidateSchemeResponse(BaseModel):
    candidate_id: str
    run_id: Optional[str] = None
    discovered_name: str
    normalized_name: str
    scheme_code: str
    discovery_source: str
    discovery_url: Optional[str] = None
    official_source_url: str
    source_document: Optional[str] = None
    source_type: str
    ministry: Optional[str] = None
    implementing_agency: Optional[str] = None
    level: str
    state_coverage: Optional[str] = None
    district_coverage: Optional[str] = None
    sector: Optional[str] = None
    scheme_category: Optional[str] = None
    target_beneficiaries: Optional[str] = None
    stated_benefits: Optional[str] = None
    relevance_status: str
    relevance_reason: Optional[str] = None
    extraction_status: str
    verification_status: str
    duplicate_status: str
    duplicate_of_scheme_id: Optional[str] = None
    data_confidence: str
    extracted_data: Dict[str, Any]
    missing_fields: List[str]
    evidence: Dict[str, Any]
    validation_status: str
    validation_errors: List[str]
    candidate_status: str
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    class Config:
        from_attributes = True


class CandidateReviewInput(BaseModel):
    action: str = Field(..., description="Review action: APPROVE, REJECT, or NEEDS_REVIEW")
    notes: Optional[str] = Field(None, description="Optional administrative notes or justification")
    rejection_reason: Optional[str] = Field(None, description="Reason if rejected")


class CandidateReviewResponse(BaseModel):
    candidate_id: str
    candidate_status: str
    canonical_scheme_id: Optional[str] = None
    message: str


class DiscoveryBatchRunInput(BaseModel):
    target_source: Optional[str] = Field(None, description="Filter by discovery source: CENTRAL_MINISTRY, STATE_PORTAL, IMPLEMENTING_AGENCY, or ALL")
    max_candidates: int = Field(50, ge=1, le=500, description="Maximum schemes to discover in this batch")


class DiscoveryBatchRunResponse(BaseModel):
    run_id: str
    total_discovered: int
    relevant_count: int
    low_priority_or_irrelevant: int
    officially_verified: int
    duplicate_candidates: int
    staged_for_review: int
    failed_count: int
    candidates_created: List[str]
    message: str


class IngestionQualityMetricsResponse(BaseModel):
    total_canonical_schemes: int
    total_candidates_discovered: int
    candidates_staged_for_review: int
    candidates_approved: int
    candidates_rejected: int
    candidates_officially_verified: int
    candidates_duplicate_flagged: int
    canonical_schemes_with_rules: int
    canonical_schemes_with_documents: int
    canonical_schemes_with_official_evidence: int
    coverage_by_level: Dict[str, int]
    top_ministries: Dict[str, int]
    top_categories: Dict[str, int]
    state_coverage_count: int
