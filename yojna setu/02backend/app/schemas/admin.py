from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


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
    total_schemes: int = 90
    verified_schemes: int = 90
    total_rules: int = 126
    total_documents: int = 98
    avg_parameter_completeness: float
    total_ministries: int
    total_changelogs: int
    system_health: SystemHealthResponse


class SchemeAuditItem(BaseModel):
    scheme_id: str
    scheme_name: str
    ministry: str
    sector: str
    state_coverage: str
    verification_status: str = "VERIFIED"
    scheme_status: str = "ACTIVE"
    scheme_type: Optional[str] = None
    loan_available: Optional[str] = None
    rule_count: int
    document_count: int
    completeness_score: float
    known_fields_count: int
    unknown_fields_count: int
    conditional_fields_count: int
    last_verified_date: str
    official_source_url: Optional[str] = None
    has_official_source: bool = False
    official_portal: Optional[str] = None
    updated_at: Optional[datetime] = None


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
    official_source_url: Optional[str] = None
    official_portal: Optional[str] = None


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
    action: Optional[str] = "UPDATE"
    field: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None
    admin_identifier: Optional[str] = None
    source_document: Optional[str] = None
    verification_status: Optional[str] = None
    created_at: datetime


class PaginatedChangelogResponse(BaseModel):
    items: List[ChangelogItem]
    total: int
    page: int
    page_size: int
    pages: int


class SchemeCreateInput(BaseModel):
    scheme_id: str = Field(..., min_length=3, max_length=50, description="Unique scheme identifier (e.g. SIH26092-091)")
    scheme_name: str = Field(..., min_length=3, max_length=255, description="Official scheme title")
    ministry: str = Field(..., min_length=2, max_length=255, description="Governing Ministry or Department")
    scheme_type: Optional[str] = Field(None, description="Primary scheme classification/sector")
    source_organization: Optional[str] = None
    implementing_agency: Optional[str] = None
    purpose: Optional[str] = None
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    target_beneficiary: Optional[str] = None
    applicant_types: Optional[str] = None
    marginalized_group: Optional[str] = None
    target_groups: Optional[str] = None
    social_category: Optional[str] = None
    gender_condition: Optional[str] = None
    state_restriction: Optional[str] = "ALL_INDIA"
    state_coverage: Optional[str] = "All India"
    sector: Optional[str] = None
    activity_type: Optional[str] = None
    business_stage: Optional[str] = None
    support_type: Optional[str] = None
    benefit_description: Optional[str] = None
    loan_available: str = Field("NO", description="YES or NO")
    minimum_loan_amount: Optional[float] = None
    maximum_loan_amount: Optional[float] = None
    interest_rate_min: Optional[float] = None
    interest_rate_max: Optional[float] = None
    interest_rate_type: Optional[str] = None
    repayment_period_min_months: Optional[int] = None
    repayment_period_max_months: Optional[int] = None
    subsidy_available: Optional[str] = "NO"
    subsidy_percentage: Optional[float] = None
    subsidy_details: Optional[str] = None
    grant_available: Optional[str] = "NO"
    grant_amount: Optional[float] = None
    application_mode: Optional[str] = "ONLINE"
    application_url: Optional[str] = None
    official_portal: Optional[str] = None
    official_source_url: str = Field(..., description="Official government gazette or portal URL")
    source_title: Optional[str] = None
    source_document: Optional[str] = None
    verification_status: Optional[str] = "VERIFIED"
    last_verified_date: Optional[str] = None
    required_documents: Optional[str] = None
    scheme_status: Optional[str] = "ACTIVE"
    reason: Optional[str] = Field(None, description="Audit reason for creating this scheme")

    @field_validator("scheme_id")
    @classmethod
    def validate_scheme_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean or any(c in clean for c in " \t\n\r\"'<>"):
            raise ValueError("Scheme ID must be a valid non-empty identifier without spaces or special symbols.")
        return clean.upper()

    @field_validator("official_source_url")
    @classmethod
    def validate_official_source_url(cls, v: str) -> str:
        clean = v.strip()
        if not clean.startswith("http://") and not clean.startswith("https://"):
            raise ValueError("Official source URL must begin with http:// or https://")
        return clean

    @field_validator("application_url", "official_portal")
    @classmethod
    def validate_optional_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        if not clean:
            return None
        if not clean.startswith("http://") and not clean.startswith("https://"):
            raise ValueError("URL must begin with http:// or https://")
        return clean

    @model_validator(mode="after")
    def validate_credit_and_financials(self) -> "SchemeCreateInput":
        la = str(self.loan_available or "").strip().upper()
        if la in ("NO", "FALSE", "0", "N"):
            self.loan_available = "NO"
            self.minimum_loan_amount = None
            self.maximum_loan_amount = None
            self.interest_rate_min = None
            self.interest_rate_max = None
            self.repayment_period_min_months = None
            self.repayment_period_max_months = None
        else:
            self.loan_available = "YES"
            if self.minimum_loan_amount is not None and self.maximum_loan_amount is not None:
                if self.minimum_loan_amount > self.maximum_loan_amount:
                    raise ValueError("Minimum loan amount cannot exceed maximum loan amount.")
            if self.interest_rate_min is not None and self.interest_rate_max is not None:
                if self.interest_rate_min > self.interest_rate_max:
                    raise ValueError("Minimum interest rate cannot exceed maximum interest rate.")
            if self.repayment_period_min_months is not None and self.repayment_period_max_months is not None:
                if self.repayment_period_min_months > self.repayment_period_max_months:
                    raise ValueError("Minimum repayment period cannot exceed maximum repayment period.")

        if self.subsidy_percentage is not None:
            if self.subsidy_percentage < 0.0 or self.subsidy_percentage > 100.0:
                raise ValueError("Subsidy percentage must be between 0 and 100%.")

        return self


class SchemeUpdateInput(BaseModel):
    scheme_name: Optional[str] = Field(None, min_length=3, max_length=255)
    ministry: Optional[str] = Field(None, min_length=2, max_length=255)
    scheme_type: Optional[str] = None
    source_organization: Optional[str] = None
    implementing_agency: Optional[str] = None
    purpose: Optional[str] = None
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    target_beneficiary: Optional[str] = None
    applicant_types: Optional[str] = None
    marginalized_group: Optional[str] = None
    target_groups: Optional[str] = None
    social_category: Optional[str] = None
    gender_condition: Optional[str] = None
    state_restriction: Optional[str] = None
    state_coverage: Optional[str] = None
    sector: Optional[str] = None
    activity_type: Optional[str] = None
    business_stage: Optional[str] = None
    support_type: Optional[str] = None
    benefit_description: Optional[str] = None
    loan_available: Optional[str] = None
    minimum_loan_amount: Optional[float] = None
    maximum_loan_amount: Optional[float] = None
    interest_rate_min: Optional[float] = None
    interest_rate_max: Optional[float] = None
    interest_rate_type: Optional[str] = None
    repayment_period_min_months: Optional[int] = None
    repayment_period_max_months: Optional[int] = None
    subsidy_available: Optional[str] = None
    subsidy_percentage: Optional[float] = None
    subsidy_details: Optional[str] = None
    grant_available: Optional[str] = None
    grant_amount: Optional[float] = None
    application_mode: Optional[str] = None
    application_url: Optional[str] = None
    official_portal: Optional[str] = None
    official_source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_document: Optional[str] = None
    verification_status: Optional[str] = None
    last_verified_date: Optional[str] = None
    required_documents: Optional[str] = None
    scheme_status: Optional[str] = None
    change_reason: Optional[str] = Field("Official administrative update", description="Reason for audit changelog")

    @field_validator("official_source_url", "application_url", "official_portal")
    @classmethod
    def validate_optional_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        if not clean:
            return None
        if not clean.startswith("http://") and not clean.startswith("https://"):
            raise ValueError("URL must begin with http:// or https://")
        return clean

    @model_validator(mode="after")
    def validate_credit_and_financials(self) -> "SchemeUpdateInput":
        if self.loan_available is not None:
            la = str(self.loan_available).strip().upper()
            if la in ("NO", "FALSE", "0", "N"):
                self.loan_available = "NO"
                self.minimum_loan_amount = None
                self.maximum_loan_amount = None
                self.interest_rate_min = None
                self.interest_rate_max = None
                self.repayment_period_min_months = None
                self.repayment_period_max_months = None
            else:
                self.loan_available = "YES"

        if self.minimum_loan_amount is not None and self.maximum_loan_amount is not None:
            if self.minimum_loan_amount > self.maximum_loan_amount:
                raise ValueError("Minimum loan amount cannot exceed maximum loan amount.")
        if self.interest_rate_min is not None and self.interest_rate_max is not None:
            if self.interest_rate_min > self.interest_rate_max:
                raise ValueError("Minimum interest rate cannot exceed maximum interest rate.")
        if self.repayment_period_min_months is not None and self.repayment_period_max_months is not None:
            if self.repayment_period_min_months > self.repayment_period_max_months:
                raise ValueError("Minimum repayment period cannot exceed maximum repayment period.")
        if self.subsidy_percentage is not None:
            if self.subsidy_percentage < 0.0 or self.subsidy_percentage > 100.0:
                raise ValueError("Subsidy percentage must be between 0 and 100%.")

        return self


class SchemeStatusUpdateInput(BaseModel):
    status: str = Field(..., description="ACTIVE or INACTIVE")
    reason: Optional[str] = Field(None, description="Audit reason for status change")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in ("ACTIVE", "INACTIVE"):
            raise ValueError("Status must be either 'ACTIVE' or 'INACTIVE'.")
        return clean


class PartnerAuditItem(BaseModel):
    partner_id: str
    name: str
    code: str
    partner_type: str
    institution_type: Optional[str] = None
    partner_category: str = "AUTHORIZED_SCHEME_PARTNER"
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    verification_status: str = "VERIFIED_OFFICIAL"
    source_url: Optional[str] = None
    last_verified_date: Optional[str] = None
    is_active: bool = True
    mapped_schemes_count: int = 0
    supported_schemes: List[str] = Field(default_factory=list)


class PaginatedPartnerAuditResponse(BaseModel):
    items: List[PartnerAuditItem]
    total: int
    page: int
    page_size: int
    pages: int
    total_active: int
    total_inactive: int


class PartnerCreateAdminInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    partner_type: str = Field(default="PUBLIC_SECTOR_BANK")
    institution_type: Optional[str] = None
    partner_category: str = Field(default="AUTHORIZED_SCHEME_PARTNER")
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: Optional[str] = None
    verification_status: str = Field(default="VERIFIED_OFFICIAL")
    change_reason: Optional[str] = Field("Official admin addition", description="Reason for changelog")


class PartnerUpdateAdminInput(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    partner_type: Optional[str] = None
    institution_type: Optional[str] = None
    partner_category: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: Optional[str] = None
    verification_status: Optional[str] = None
    is_active: Optional[bool] = None
    change_reason: Optional[str] = Field("Official admin update", description="Reason for changelog")


class PartnerStatusAdminInput(BaseModel):
    is_active: bool
    reason: Optional[str] = Field(None, description="Audit reason for status change")


class PartnerMappingAdminInput(BaseModel):
    scheme_id: str
    service_type: Optional[str] = "FINANCING"
    authorization_level: Optional[str] = "SCHEME_ROUTE_VERIFIED"
    verification_notes: Optional[str] = None
    source_url: Optional[str] = None
    reason: Optional[str] = Field("Official scheme mapping link", description="Reason for changelog")

