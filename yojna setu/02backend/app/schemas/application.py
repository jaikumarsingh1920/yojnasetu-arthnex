import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.schemas.profile import BeneficiaryProfileInput


class ApplicationCreateRequest(BaseModel):
    scheme_id: str = Field(..., description="Target scheme ID")
    profile: BeneficiaryProfileInput = Field(..., description="Beneficiary profile details for application snapshot")


class ApplicationUpdateRequest(BaseModel):
    profile: BeneficiaryProfileInput = Field(..., description="Updated beneficiary profile details for draft application")


class ApplicationSubmitRequest(BaseModel):
    partner_id: str = Field(..., description="Target Channel Partner UUID for routing funds")


class ApplicationWithdrawRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Optional withdrawal reason")


class ApplicationDocumentResponse(BaseModel):
    app_document_id: str
    application_id: str
    document_id: Optional[str] = None
    document_name: str
    requirement_type: str
    condition: Optional[str] = None
    is_uploaded: bool
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    verification_status: str
    rejection_reason: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StatusHistoryResponse(BaseModel):
    history_id: str
    application_id: str
    old_status: Optional[str] = None
    new_status: str
    changed_by: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationResponse(BaseModel):
    application_id: str
    user_id: str
    scheme_id: str
    scheme_name: Optional[str] = None
    status: str
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


class PaginatedApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SubmissionValidationResponse(BaseModel):
    application_id: str
    status: str
    can_submit: bool
    missing_documents: List[str] = Field(default_factory=list)
    message: str


class DocumentUploadResponse(BaseModel):
    app_document_id: str
    application_id: str
    is_uploaded: bool
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime
    application_status: str
    message: str
