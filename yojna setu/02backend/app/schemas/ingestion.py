import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator



class SourceCreateInput(BaseModel):
    source_id: str = Field(..., description="Unique source identifier (e.g. SRC-PMEGP-001)")
    scheme_id: Optional[str] = Field(None, description="Linked canonical scheme ID (e.g. SIH26092-001)")
    source_name: str = Field(..., description="Human readable name of official portal or guideline page")
    source_url: str = Field(..., description="Full HTTP/HTTPS URL of authoritative government source")
    authority: Optional[str] = Field(None, description="Governing ministry or department")
    source_type: str = Field("HTML", description="Source format: HTML, PDF, or JSON_API")
    fetch_frequency_hours: int = Field(24, ge=1, le=720, description="Recommended fetch frequency in hours")


class SourceUpdateInput(BaseModel):
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    authority: Optional[str] = None
    source_type: Optional[str] = None
    is_active: Optional[bool] = None
    fetch_frequency_hours: Optional[int] = Field(None, ge=1, le=720)


class SourceResponse(BaseModel):
    source_id: str
    scheme_id: Optional[str] = None
    source_name: str
    source_url: str
    authority: Optional[str] = None
    source_type: str
    is_active: bool
    fetch_frequency_hours: int
    fetch_priority: int = 1
    expected_content_type: Optional[str] = "text/html"
    last_fetched_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_snapshot_hash: Optional[str] = None
    last_http_status: Optional[int] = None
    last_status: str
    consecutive_failures: int = 0
    health_status: str = "HEALTHY"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    snapshot_id: str
    source_id: str
    fetched_at: datetime
    content_hash: str
    content_type: str
    fetch_status: str
    http_status_code: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DetectedFieldChange(BaseModel):
    field: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None


class PendingUpdateResponse(BaseModel):
    update_id: str
    scheme_id: str
    source_id: str
    snapshot_id: Optional[str] = None
    proposal_type: str = "MODIFICATION"
    change_classification: str = "MODIFIED"
    old_version: str
    extracted_data: Dict[str, Any]
    detected_changes: List[DetectedFieldChange]
    validation_status: str
    validation_errors: List[str]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("extracted_data", mode="before")
    @classmethod
    def parse_extracted_data(cls, v: Any) -> Dict[str, Any]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    @field_validator("detected_changes", mode="before")
    @classmethod
    def parse_detected_changes(cls, v: Any) -> List[Any]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []

    @field_validator("validation_errors", mode="before")
    @classmethod
    def parse_validation_errors(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []



class PendingUpdateReviewInput(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT)$", description="Review verdict: APPROVE or REJECT")
    reason: Optional[str] = Field(None, description="Explanation or justification for review decision")


class PipelineRunResponse(BaseModel):
    source_id: str
    fetch_status: str
    change_status: str  # NO_CHANGE, CHANGE_DETECTED, ERROR
    content_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    pending_update_id: Optional[str] = None
    detected_change_count: int = 0
    validation_status: Optional[str] = None
    message: str
