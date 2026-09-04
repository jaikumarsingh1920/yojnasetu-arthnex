from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator, EmailStr


# ─────────────────────────────────────────────────────────────
# Related Models Response Schemas
# ─────────────────────────────────────────────────────────────

class SchemeVerificationResponse(BaseModel):
    id: str
    scheme_id: str
    verification_status: str
    last_verified_date: Optional[str] = None
    data_confidence: str
    notes: Optional[str] = None
    normalization_note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SchemeRuleResponse(BaseModel):
    rule_id: str
    scheme_id: str
    parent_product_id: Optional[str] = None
    field: str
    operator: str
    value: str
    value_type: str
    rule_type: str
    priority: str
    condition_group: str
    error_message: Optional[str] = None
    source_document: Optional[str] = None
    source_page: Optional[str] = None
    source_section: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True


class SchemeDocumentResponse(BaseModel):
    document_id: str
    scheme_id: str
    document_name: str
    requirement_type: str
    condition: Optional[str] = None
    applicant_type: Optional[str] = None
    source_document: Optional[str] = None
    source_page: Optional[str] = None
    source_section: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────
# Scheme List & Detail Response Schemas
# ─────────────────────────────────────────────────────────────

class SchemeListItemResponse(BaseModel):
    scheme_id: str
    scheme_code: str
    scheme_name: str
    scheme_type: Optional[str] = None
    source_organization: Optional[str] = None
    ministry: Optional[str] = None
    implementing_agency: Optional[str] = None
    scheme_status: Optional[str] = None
    short_description: Optional[str] = None
    sector: Optional[str] = None
    marginalized_group: Optional[str] = None
    target_groups: Optional[str] = None
    target_beneficiary: Optional[str] = None
    business_stage: Optional[str] = None
    state_restriction: Optional[str] = None
    support_type: Optional[str] = None
    loan_available: Optional[str] = None
    max_loan_amount: Optional[float] = None
    min_loan_amount: Optional[float] = None
    max_loan_amount_raw: Optional[str] = None
    interest_rate: Optional[float] = None
    interest_rate_min: Optional[float] = None
    interest_rate_max: Optional[float] = None
    interest_rate_type: Optional[str] = None
    interest_rate_min_raw: Optional[str] = None
    interest_rate_max_raw: Optional[str] = None
    subsidy_available: Optional[str] = None
    subsidy_percentage: Optional[float] = None
    benefit_description: Optional[str] = None
    financial_category: Optional[str] = "LOAN_CREDIT"
    is_credit_scheme: Optional[bool] = True
    calculator_applicable: Optional[bool] = True
    financial_assistance_summary: Optional[str] = None
    application_url: Optional[str] = None
    official_portal: Optional[str] = None
    application_route: Optional[str] = "OFFICIAL_ROUTE_UNVERIFIED"
    partner_count: Optional[int] = 0
    verification_status: Optional[str] = "VERIFIED"
    last_verified_date: Optional[str] = None
    created_at: datetime

    @field_validator("scheme_type", mode="before")
    @classmethod
    def sanitize_scheme_type(cls, v: Any) -> Optional[str]:
        if v == "UNKNOWN" or not v:
            return None
        return v

    @field_validator("marginalized_group", mode="before")
    @classmethod
    def sanitize_marginalized_group(cls, v: Any) -> Optional[str]:
        if v == "UNKNOWN" or not v:
            return None
        return v

    class Config:
        from_attributes = True


class PaginatedSchemeListResponse(BaseModel):
    items: List[SchemeListItemResponse]
    total: int = Field(..., description="Total matching records count")
    page: int = Field(..., description="Current page index (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class SchemeDetailResponse(BaseModel):
    # Identity
    scheme_id: str
    scheme_code: str
    scheme_name: str
    scheme_type: Optional[str] = None
    source_organization: Optional[str] = None
    ministry: Optional[str] = None
    implementing_agency: Optional[str] = None
    scheme_status: Optional[str] = None

    # Description
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    purpose: Optional[str] = None

    # Beneficiary & Eligibility Parameters
    target_beneficiary: Optional[str] = None
    applicant_types: Optional[str] = None
    marginalized_group: Optional[str] = None
    target_groups: Optional[str] = None
    entrepreneur_type: Optional[str] = None
    sc_required: Optional[str] = None
    social_category: Optional[str] = None
    gender_condition: Optional[str] = None
    gender_requirement: Optional[str] = None

    age_min: Optional[int] = None
    age_min_raw: Optional[str] = None
    age_max: Optional[int] = None
    age_max_raw: Optional[str] = None

    income_limit: Optional[float] = None
    income_limit_raw: Optional[str] = None
    income_operator: Optional[str] = None
    income_definition: Optional[str] = None

    state_restriction: Optional[str] = None
    state_coverage: Optional[str] = None
    district_restriction: Optional[str] = None
    district_coverage: Optional[str] = None
    sector: Optional[str] = None
    activity_type: Optional[str] = None
    business_types: Optional[str] = None
    business_stage: Optional[str] = None

    new_unit_required: Optional[str] = None
    new_business_allowed: Optional[str] = None
    existing_unit_allowed: Optional[str] = None
    existing_business_allowed: Optional[str] = None
    business_registration_required: Optional[str] = None
    enterprise_size_requirement: Optional[str] = None
    education_applicable: Optional[str] = None
    vocational_training_applicable: Optional[str] = None

    # Financial Terms
    support_type: Optional[str] = None
    benefit_description: Optional[str] = None
    loan_available: Optional[str] = None

    min_project_cost: Optional[float] = None
    min_project_cost_raw: Optional[str] = None
    max_project_cost: Optional[float] = None
    max_project_cost_raw: Optional[str] = None

    minimum_loan_amount: Optional[float] = None
    minimum_loan_amount_raw: Optional[str] = None
    maximum_loan_amount: Optional[float] = None
    maximum_loan_amount_raw: Optional[str] = None

    min_loan_amount: Optional[float] = None
    min_loan_amount_raw: Optional[str] = None
    max_loan_amount: Optional[float] = None
    max_loan_amount_raw: Optional[str] = None

    financing_percentage: Optional[float] = None
    financing_percentage_raw: Optional[str] = None
    beneficiary_contribution_percentage: Optional[float] = None
    beneficiary_contribution_percentage_raw: Optional[str] = None

    subsidy_available: Optional[str] = None
    subsidy_percentage: Optional[float] = None
    subsidy_percentage_raw: Optional[str] = None
    subsidy_details: Optional[str] = None

    grant_available: Optional[str] = None
    grant_amount: Optional[float] = None
    grant_amount_raw: Optional[str] = None

    interest_rate_min: Optional[float] = None
    interest_rate_min_raw: Optional[str] = None
    interest_rate_max: Optional[float] = None
    interest_rate_max_raw: Optional[str] = None
    interest_rate_type: Optional[str] = None

    repayment_period_min_months: Optional[int] = None
    repayment_period_min_months_raw: Optional[str] = None
    repayment_period_max_months: Optional[int] = None
    repayment_period_max_months_raw: Optional[str] = None
    repayment_frequency: Optional[str] = None

    moratorium_min_months: Optional[int] = None
    moratorium_min_months_raw: Optional[str] = None
    moratorium_max_months: Optional[int] = None
    moratorium_max_months_raw: Optional[str] = None
    moratorium_interest_mode: Optional[str] = None

    collateral_required: Optional[str] = None
    security_required: Optional[str] = None

    # Non-Financial Supports
    training_available: Optional[str] = None
    equipment_support: Optional[str] = None
    market_support: Optional[str] = None
    working_capital_support: Optional[str] = None

    # Application Route & Portal
    financial_category: Optional[str] = "LOAN_CREDIT"
    is_credit_scheme: Optional[bool] = True
    calculator_applicable: Optional[bool] = True
    financial_assistance_summary: Optional[str] = None
    application_mode: Optional[str] = None
    application_url: Optional[str] = None
    official_portal: Optional[str] = None
    application_route: Optional[str] = "OFFICIAL_ROUTE_UNVERIFIED"
    partner_count: Optional[int] = 0
    application_steps: Optional[str] = None
    required_documents: Optional[str] = None
    helpline: Optional[str] = None

    # Provenance & Version Metadata
    official_source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_document: Optional[str] = None
    source_page: Optional[str] = None
    source_section: Optional[str] = None
    source_published_date: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    scheme_version: Optional[str] = None
    previous_version: Optional[str] = None
    change_summary: Optional[str] = None
    last_verified_date: Optional[str] = None
    searchable_tags: Optional[str] = None
    verification_status: Optional[str] = "VERIFIED"
    created_at: datetime

    # Related Entities
    verifications: List[SchemeVerificationResponse] = []
    rules: List[SchemeRuleResponse] = []
    documents: List[SchemeDocumentResponse] = []

    @field_validator("scheme_type", mode="before")
    @classmethod
    def sanitize_detail_scheme_type(cls, v: Any) -> Optional[str]:
        if v == "UNKNOWN" or not v:
            return None
        return v

    @field_validator("marginalized_group", mode="before")
    @classmethod
    def sanitize_detail_marginalized_group(cls, v: Any) -> Optional[str]:
        if v == "UNKNOWN" or not v:
            return None
        return v

    class Config:
        from_attributes = True


class FilterOptionItem(BaseModel):
    label: str
    value: str
    count: int


class FilterOptionsResponse(BaseModel):
    ministries: List[FilterOptionItem]
    sectors: List[FilterOptionItem]
    financial_types: List[FilterOptionItem]
    beneficiary_categories: List[FilterOptionItem]
    states: List[FilterOptionItem]
    application_routes: List[FilterOptionItem]
    total_schemes: int


# ─────────────────────────────────────────────────────────────
# Scheme Comparison Response Schemas
# ─────────────────────────────────────────────────────────────

class SchemePersonalizedEligibility(BaseModel):
    status: str = Field(..., description="ELIGIBLE, INSUFFICIENT_INFORMATION, or INELIGIBLE")
    reasons: List[str] = Field(default_factory=list, description="Factual eligibility or ineligibility explanation rules")
    missing_fields: List[str] = Field(default_factory=list, description="Profile attributes missing for conclusive evaluation")


class SchemeComparisonItem(BaseModel):
    scheme: SchemeDetailResponse
    personalized_eligibility: Optional[SchemePersonalizedEligibility] = None


class SchemeComparisonResponse(BaseModel):
    compared_schemes: List[SchemeComparisonItem]
    invalid_ids: List[str] = Field(default_factory=list, description="IDs requested that were invalid or not found")


# ─────────────────────────────────────────────────────────────
# Email Scheme Request Schema
# ─────────────────────────────────────────────────────────────

class EmailSchemeRequest(BaseModel):
    recipient_email: EmailStr = Field(..., description="Valid recipient email address")
    language_code: Optional[str] = Field("en", description="Preferred language code for email content (e.g. en, hi)")


class EmailSchemeResponse(BaseModel):
    sent: bool
    message: str
    recipient_email: Optional[str] = None



