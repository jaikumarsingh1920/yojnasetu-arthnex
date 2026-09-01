import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.schemas.application import ApplicationDocumentResponse, StatusHistoryResponse


class PartnerResponse(BaseModel):
    partner_id: str
    name: str
    code: str
    partner_type: str
    partner_sub_type: Optional[str] = None
    institution_type: Optional[str] = None
    partner_category: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    service_type: Optional[str] = None
    last_verified_date: Optional[str] = None
    scheme_authorization_level: Optional[str] = None
    coordinates_status: Optional[str] = None
    source_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    npa_percentage: Optional[float] = None
    overdue_percentage: Optional[float] = None
    is_accepting_applications: bool
    is_active: bool
    verification_status: Optional[str] = None
    coordinates_source: Optional[str] = None
    coordinates_verified: Optional[bool] = None
    geocoding_provider: Optional[str] = None
    geocoding_status: Optional[str] = None
    geocoding_confidence: Optional[str] = None
    geocoding_display_name: Optional[str] = None
    scheme_specific_mapping_available: Optional[bool] = None
    supported_schemes: Optional[List[str]] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class NearestPartnerResponse(BaseModel):
    partner: PartnerResponse
    distance_km: float
    is_scheme_matched: bool = False
    partner_category: Optional[str] = None
    supported_schemes: Optional[List[str]] = Field(default_factory=list)
    service_type: Optional[str] = None
    authorization_level: Optional[str] = None
    scheme_authorized_category: Optional[str] = None
    scheme_mapping_notes: Optional[str] = None
    suitability_reason: Optional[str] = None
    lending_capacity_status: Optional[str] = None

    class Config:
        from_attributes = True


class PartnerCreateInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    partner_type: str = Field(default="PUBLIC_SECTOR_BANK")
    partner_sub_type: Optional[str] = None
    institution_type: Optional[str] = None
    partner_category: str = Field(default="AUTHORIZED_SCHEME_PARTNER")
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    service_type: Optional[str] = None
    scheme_authorization_level: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: Optional[str] = None
    verification_status: str = Field(default="VERIFIED_OFFICIAL")


class PartnerUpdateInput(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    partner_type: Optional[str] = None
    partner_sub_type: Optional[str] = None
    institution_type: Optional[str] = None
    partner_category: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    service_type: Optional[str] = None
    scheme_authorization_level: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: Optional[str] = None
    verification_status: Optional[str] = None
    is_active: Optional[bool] = None


class PartnerStatusUpdateInput(BaseModel):
    is_active: bool
    reason: Optional[str] = None


class PartnerSchemeMappingInput(BaseModel):
    scheme_id: str
    service_type: Optional[str] = "FINANCING"
    authorization_level: Optional[str] = "SCHEME_ROUTE_VERIFIED"
    verification_notes: Optional[str] = None
    source_url: Optional[str] = None


class PartnerApplicationListItem(BaseModel):
    application_id: str
    user_id: str
    scheme_id: str
    scheme_name: Optional[str] = None
    status: str
    assigned_partner_id: Optional[str] = None
    assigned_reviewer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedPartnerApplicationListResponse(BaseModel):
    items: List[PartnerApplicationListItem]
    total: int
    page: int
    page_size: int
    pages: int


class DocumentReviewRequest(BaseModel):
    verification_status: str = Field(..., description="VERIFIED or REJECTED")
    reason: Optional[str] = Field(None, description="Detailed explanation (required when verification_status is REJECTED)")


class DocumentReviewResponse(BaseModel):
    app_document_id: str
    application_id: str
    document_name: str
    verification_status: str
    rejection_reason: Optional[str] = None
    verified_by: str
    verified_at: datetime
    message: str


class ApplicationAssignmentRequest(BaseModel):
    partner_id: Optional[str] = Field(None, description="Target Partner Organization UUID")
    reviewer_id: Optional[str] = Field(None, description="Target Reviewer User UUID")


class ApplicationReviewNoteCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Internal review note content")


class ApplicationReviewNoteResponse(BaseModel):
    note_id: str
    application_id: str
    author_id: str
    author_role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationReviewDecisionRequest(BaseModel):
    decision: Optional[str] = Field(None, description="APPROVED or REJECTED")
    reason: Optional[str] = Field(None, description="Decision justification / rejection reason (required for REJECTED)")


class RequestCorrectionRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Reason why application or documents need correction")
    correction_fields: Optional[List[str]] = Field(default_factory=list, description="List of document or profile fields requiring update")


class AdminStatsResponse(BaseModel):
    total_applications: int
    drafts: int
    submitted: int
    under_review: int
    correction_required: int
    approved: int
    rejected: int
    pending_document_verification: int
    applications_by_scheme: Dict[str, int] = Field(default_factory=dict)
    applications_by_status: Dict[str, int] = Field(default_factory=dict)


class ApprovalReadinessResponse(BaseModel):
    application_id: str
    status: str
    can_approve: bool
    blocking_documents: List[str] = Field(default_factory=list)
    message: str


class PartnerApplicationDetailResponse(BaseModel):
    application_id: str
    user_id: str
    scheme_id: str
    scheme_name: Optional[str] = None
    status: str
    assigned_partner_id: Optional[str] = None
    assigned_reviewer_id: Optional[str] = None
    profile_snapshot: Optional[Dict[str, Any]] = None
    eligibility_snapshot: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None
    correction_reason: Optional[str] = None
    correction_fields: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    documents: List[ApplicationDocumentResponse] = Field(default_factory=list)
    status_history: List[StatusHistoryResponse] = Field(default_factory=list)
    review_notes: List[ApplicationReviewNoteResponse] = Field(default_factory=list)

    @field_validator("profile_snapshot", "eligibility_snapshot", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return None
        return v

    class Config:
        from_attributes = True
