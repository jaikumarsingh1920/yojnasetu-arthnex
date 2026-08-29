from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SystemHealthComponent(BaseModel):
    name: str
    status: str = Field(..., description="ONLINE, DEGRADED, OFFLINE")
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class SystemHealthResponse(BaseModel):
    overall_status: str
    timestamp: datetime
    components: List[SystemHealthComponent]


class AdminDashboardSummaryResponse(BaseModel):
    total_schemes: int = 56
    verified_schemes: int = 56
    total_rules: int = 57
    total_documents: int = 20
    avg_parameter_completeness: float
    applications_total: int
    applications_by_status: Dict[str, int]
    pending_document_verifications: int
    unread_notifications: int
    system_health: SystemHealthResponse


class SchemeAuditItem(BaseModel):
    scheme_id: str
    scheme_name: str
    ministry: str
    sector: str
    state_coverage: str
    verification_status: str = "VERIFIED"
    rule_count: int
    document_count: int
    completeness_score: float
    known_fields_count: int
    unknown_fields_count: int
    conditional_fields_count: int
    last_verified_date: str


class PaginatedSchemeAuditResponse(BaseModel):
    items: List[SchemeAuditItem]
    total: int
    page: int
    page_size: int
    pages: int
    avg_completeness: float


class SchemeAuditDetailResponse(BaseModel):
    scheme_id: str
    scheme_name: str
    ministry: str
    sector: str
    state_coverage: str
    verification_status: str = "VERIFIED"
    purpose: Optional[str]
    target_groups: Optional[str]
    completeness_score: float
    known_fields: Dict[str, Any]
    unknown_fields: List[str]
    conditional_fields: List[str]
    not_applicable_fields: List[str]
    rules: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    changelogs: List[Dict[str, Any]]
    data_quality_warnings: List[str]


class RuleAuditItem(BaseModel):
    rule_id: str
    scheme_id: str
    scheme_name: str
    field: str
    operator: str
    value: str
    value_type: str
    rule_type: str
    priority: str
    condition_group: str
    error_message: Optional[str]


class PaginatedRuleAuditResponse(BaseModel):
    items: List[RuleAuditItem]
    total: int
    page: int
    page_size: int
    pages: int


class DocumentAuditItem(BaseModel):
    document_id: str
    scheme_id: str
    scheme_name: str
    document_name: str
    requirement_type: str
    applicant_type: Optional[str]
    source_document: Optional[str]
    active: bool
    verification_status: str = "VERIFIED"


class PaginatedDocumentAuditResponse(BaseModel):
    items: List[DocumentAuditItem]
    total: int
    page: int
    page_size: int
    pages: int


class ChangelogItem(BaseModel):
    id: int
    scheme_id: str
    scheme_name: str
    field: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    reason: Optional[str]
    source_document: Optional[str]
    verification_status: Optional[str]
    created_at: datetime


class PaginatedChangelogResponse(BaseModel):
    items: List[ChangelogItem]
    total: int
    page: int
    page_size: int
    pages: int
