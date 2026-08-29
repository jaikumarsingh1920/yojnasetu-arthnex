from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Numeric, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import engine
from app.db.base_class import Base


class Scheme(Base):
    __tablename__ = "schemes"

    # Identity
    scheme_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    scheme_code: Mapped[str] = mapped_column(String(50), default="UNKNOWN")
    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    scheme_type: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    source_organization: Mapped[Optional[str]] = mapped_column(String(255))
    ministry: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    implementing_agency: Mapped[Optional[str]] = mapped_column(String(255))
    scheme_status: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # Description
    short_description: Mapped[Optional[str]] = mapped_column(Text)
    detailed_description: Mapped[Optional[str]] = mapped_column(Text)
    purpose: Mapped[Optional[str]] = mapped_column(Text)

    # Beneficiary & Eligibility Parameters
    target_beneficiary: Mapped[Optional[str]] = mapped_column(Text)
    applicant_types: Mapped[Optional[str]] = mapped_column(Text)
    marginalized_group: Mapped[Optional[str]] = mapped_column(String(100))
    target_groups: Mapped[Optional[str]] = mapped_column(Text)
    entrepreneur_type: Mapped[Optional[str]] = mapped_column(String(100))
    sc_required: Mapped[Optional[str]] = mapped_column(String(50))
    social_category: Mapped[Optional[str]] = mapped_column(Text)
    gender_condition: Mapped[Optional[str]] = mapped_column(String(50))
    gender_requirement: Mapped[Optional[str]] = mapped_column(String(50))

    age_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    age_min_raw: Mapped[Optional[str]] = mapped_column(String(50))
    age_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    age_max_raw: Mapped[Optional[str]] = mapped_column(String(50))

    income_limit: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    income_limit_raw: Mapped[Optional[str]] = mapped_column(String(50))
    income_operator: Mapped[Optional[str]] = mapped_column(String(20))
    income_definition: Mapped[Optional[str]] = mapped_column(String(100))

    state_restriction: Mapped[Optional[str]] = mapped_column(String(50))
    state_coverage: Mapped[Optional[str]] = mapped_column(Text)
    district_restriction: Mapped[Optional[str]] = mapped_column(String(50))
    district_coverage: Mapped[Optional[str]] = mapped_column(Text)
    sector: Mapped[Optional[str]] = mapped_column(Text, index=True)
    activity_type: Mapped[Optional[str]] = mapped_column(Text)
    business_types: Mapped[Optional[str]] = mapped_column(Text)
    business_stage: Mapped[Optional[str]] = mapped_column(String(50))

    new_unit_required: Mapped[Optional[str]] = mapped_column(String(50))
    new_business_allowed: Mapped[Optional[str]] = mapped_column(String(50))
    existing_unit_allowed: Mapped[Optional[str]] = mapped_column(String(50))
    existing_business_allowed: Mapped[Optional[str]] = mapped_column(String(50))
    business_registration_required: Mapped[Optional[str]] = mapped_column(String(50))
    enterprise_size_requirement: Mapped[Optional[str]] = mapped_column(String(100))
    education_applicable: Mapped[Optional[str]] = mapped_column(String(100))
    vocational_training_applicable: Mapped[Optional[str]] = mapped_column(String(100))

    # Financial Terms
    support_type: Mapped[Optional[str]] = mapped_column(Text)
    benefit_description: Mapped[Optional[str]] = mapped_column(Text)
    loan_available: Mapped[Optional[str]] = mapped_column(String(50))

    min_project_cost: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    min_project_cost_raw: Mapped[Optional[str]] = mapped_column(String(50))
    max_project_cost: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    max_project_cost_raw: Mapped[Optional[str]] = mapped_column(String(50))

    minimum_loan_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    minimum_loan_amount_raw: Mapped[Optional[str]] = mapped_column(String(50))
    maximum_loan_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    maximum_loan_amount_raw: Mapped[Optional[str]] = mapped_column(String(50))

    min_loan_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    min_loan_amount_raw: Mapped[Optional[str]] = mapped_column(String(50))
    max_loan_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    max_loan_amount_raw: Mapped[Optional[str]] = mapped_column(String(50))

    financing_percentage: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    financing_percentage_raw: Mapped[Optional[str]] = mapped_column(String(50))
    beneficiary_contribution_percentage: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    beneficiary_contribution_percentage_raw: Mapped[Optional[str]] = mapped_column(String(50))

    subsidy_available: Mapped[Optional[str]] = mapped_column(String(50))
    subsidy_percentage: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    subsidy_percentage_raw: Mapped[Optional[str]] = mapped_column(String(50))
    subsidy_details: Mapped[Optional[str]] = mapped_column(Text)

    grant_available: Mapped[Optional[str]] = mapped_column(String(50))
    grant_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    grant_amount_raw: Mapped[Optional[str]] = mapped_column(String(50))

    interest_rate_min: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    interest_rate_min_raw: Mapped[Optional[str]] = mapped_column(String(50))
    interest_rate_max: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    interest_rate_max_raw: Mapped[Optional[str]] = mapped_column(String(50))
    interest_rate_type: Mapped[Optional[str]] = mapped_column(String(50))

    repayment_period_min_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    repayment_period_min_months_raw: Mapped[Optional[str]] = mapped_column(String(50))
    repayment_period_max_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    repayment_period_max_months_raw: Mapped[Optional[str]] = mapped_column(String(50))
    repayment_frequency: Mapped[Optional[str]] = mapped_column(String(50))

    moratorium_min_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    moratorium_min_months_raw: Mapped[Optional[str]] = mapped_column(String(50))
    moratorium_max_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    moratorium_max_months_raw: Mapped[Optional[str]] = mapped_column(String(50))
    moratorium_interest_mode: Mapped[Optional[str]] = mapped_column(String(100))

    collateral_required: Mapped[Optional[str]] = mapped_column(String(50))
    security_required: Mapped[Optional[str]] = mapped_column(Text)

    # Non-Financial Supports
    training_available: Mapped[Optional[str]] = mapped_column(String(50))
    equipment_support: Mapped[Optional[str]] = mapped_column(String(50))
    market_support: Mapped[Optional[str]] = mapped_column(String(50))
    working_capital_support: Mapped[Optional[str]] = mapped_column(String(50))

    # Application Route & Portal
    application_mode: Mapped[Optional[str]] = mapped_column(String(100))
    application_url: Mapped[Optional[str]] = mapped_column(Text)
    official_portal: Mapped[Optional[str]] = mapped_column(Text)
    application_steps: Mapped[Optional[str]] = mapped_column(Text)
    required_documents: Mapped[Optional[str]] = mapped_column(Text)
    helpline: Mapped[Optional[str]] = mapped_column(String(255))

    # Provenance & Version Metadata
    official_source_url: Mapped[Optional[str]] = mapped_column(Text)
    source_title: Mapped[Optional[str]] = mapped_column(Text)
    source_document: Mapped[Optional[str]] = mapped_column(Text)
    source_page: Mapped[Optional[str]] = mapped_column(String(100))
    source_section: Mapped[Optional[str]] = mapped_column(String(255))
    source_published_date: Mapped[Optional[str]] = mapped_column(String(50))
    effective_from: Mapped[Optional[str]] = mapped_column(String(50))
    effective_to: Mapped[Optional[str]] = mapped_column(String(50))
    scheme_version: Mapped[Optional[str]] = mapped_column(String(50))
    previous_version: Mapped[Optional[str]] = mapped_column(String(50))
    change_summary: Mapped[Optional[str]] = mapped_column(Text)
    last_verified_date: Mapped[Optional[str]] = mapped_column(String(50))
    searchable_tags: Mapped[Optional[str]] = mapped_column(Text)
    raw_source_row: Mapped[Optional[str]] = mapped_column(Text)
    legacy_priority_raw: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    verifications = relationship("SchemeVerification", back_populates="scheme", cascade="all, delete-orphan")
    rules = relationship("SchemeRule", back_populates="scheme", cascade="all, delete-orphan")
    documents = relationship("SchemeDocument", back_populates="scheme", cascade="all, delete-orphan")
    changelogs = relationship("SchemeChangelog", back_populates="scheme", cascade="all, delete-orphan")
