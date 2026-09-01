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
    scheme_status: Mapped[Optional[str]] = mapped_column(String(50), default="ACTIVE", index=True)

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
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    verifications = relationship("SchemeVerification", back_populates="scheme", cascade="all, delete-orphan")
    rules = relationship("SchemeRule", back_populates="scheme", cascade="all, delete-orphan")
    documents = relationship("SchemeDocument", back_populates="scheme", cascade="all, delete-orphan")
    changelogs = relationship("SchemeChangelog", back_populates="scheme", cascade="all, delete-orphan")
    partner_mappings = relationship("PartnerSchemeMapping", back_populates="scheme", cascade="all, delete-orphan")

    @property
    def verification_status(self) -> str:
        if self.verifications and len(self.verifications) > 0:
            return self.verifications[0].verification_status
        return "VERIFIED"

    @property
    def partner_count(self) -> int:
        if self.partner_mappings is not None:
            return len(self.partner_mappings)
        return 0

    @property
    def application_route(self) -> str:
        if self.partner_count > 0:
            return "CHANNEL_PARTNER"
        portal = (self.application_url or self.official_portal or "").strip()
        if portal and (portal.startswith("http://") or portal.startswith("https://")):
            return "DIRECT_PORTAL"
        return "OFFICIAL_ROUTE_UNVERIFIED"

    @property
    def interest_rate(self) -> Optional[float]:
        if self.interest_rate_max is not None:
            return float(self.interest_rate_max)
        if self.interest_rate_min is not None:
            return float(self.interest_rate_min)
        return None

    @property
    def financial_category(self) -> str:
        name = (self.scheme_name or "").upper()
        st = (self.support_type or "").upper()
        la = str(self.loan_available or "").strip().upper()

        if "CGTMSE" in name or "CREDIT GUARANTEE" in name or "CREDIT ENHANCEMENT GUARANTEE" in name or "CGSSD" in name:
            return "GUARANTEE_CREDIT_SUPPORT"
        if "SCHOLARSHIP" in name or "FELLOWSHIP" in name or "SHREYAS" in name or "MEANS-CUM-MERIT" in name or "TOP CLASS EDUCATION" in name:
            return "SCHOLARSHIP"
        if "SAMARTH" in name or "GRAMODYOG VIKAS" in name or "MAHILA COIR" in name or "SKILL DEVELOPMENT" in name or "CAPACITY BUILDING" in st:
            if not (self.max_loan_amount or self.interest_rate_max):
                return "TRAINING_SKILL"
        if "SUKANYA SAMRIDDHI" in name:
            return "DIRECT_BENEFIT"
        if "ATAL PENSION" in name or "SURAKSHA BIMA" in name or "JEEVAN JYOTI BIMA" in name or "MATRU VANDANA" in name or "AYUSHMAN BHARAT" in name or "PM-JAY" in name or "PM-KISAN" in name:
            return "DIRECT_BENEFIT"
        if "MSME INNOVATIVE" in name or "LEAN" in name or "ZED" in name or "MSE-CDP" in name or "CLCSS" in name or "SCLCSS" in name or "VAN DHAN" in name or "PM-JANMAN" in name or "ADIP" in name or "DDRS" in name or "SIPDA" in name:
            if not (self.max_loan_amount or self.interest_rate_max):
                return "GRANT_SUBSIDY"
        if "PROCUREMENT AND MARKETING" in name or "IPR" in name or "TRADE ENABLEMENT" in name:
            return "NON_FINANCIAL"

        if (
            la in ["TRUE", "YES", "1"] or 
            self.max_loan_amount is not None or 
            self.interest_rate_max is not None or
            "LOAN" in st or "CREDIT" in st or "TERM LOAN" in name or "MICRO FINANCE" in name or
            "MUDRA" in name or "SVANIDHI" in name or "STAND-UP" in name or "PMEGP" in name or
            "VISHWAKARMA" in name or "CSIS" in name or "LAKHPATI DIDI" in name or "SHILP SAMPADA" in name or
            "SWAVALAMBAN" in name or "VIRASAT" in name or "MAHILA KISAN" in name or "MAHILA SAMRIDDHI" in name or
            "GREEN BUSINESS" in name or "ADIVASI SHIKSHA" in name or "SANITARY MARTS" in name or "KRISHI SAMPADA" in name
        ):
            return "LOAN_CREDIT"

        if "SUBSIDY" in st or "GRANT" in st or str(self.subsidy_available).upper() in ["TRUE", "YES"] or str(self.grant_available).upper() in ["TRUE", "YES"]:
            return "GRANT_SUBSIDY"
        elif "TRAINING" in st:
            return "TRAINING_SKILL"

        return "NON_FINANCIAL"

    @property
    def is_credit_scheme(self) -> bool:
        return self.financial_category == "LOAN_CREDIT"

    @property
    def calculator_applicable(self) -> bool:
        return self.financial_category == "LOAN_CREDIT"

    @property
    def financial_assistance_summary(self) -> str:
        cat = self.financial_category
        name = (self.scheme_name or "").upper()
        if cat == "LOAN_CREDIT":
            max_l = f"₹{self.max_loan_amount:,.2f}" if self.max_loan_amount is not None else "As per project appraisal / not specified in available official guidelines"
            if self.interest_rate_max is not None:
                if self.interest_rate_max == 0:
                    rate = "0% (Interest-Free)"
                elif self.interest_rate_min is not None and self.interest_rate_min != self.interest_rate_max:
                    rate = f"{self.interest_rate_min}% – {self.interest_rate_max}% p.a."
                else:
                    rate = f"{self.interest_rate_max}% p.a."
            else:
                rate = "As determined by financing institution / not specified in available official guidelines"
            return f"Loan limit up to {max_l} (Interest rate: {rate})"
        elif cat == "GRANT_SUBSIDY":
            if self.subsidy_percentage is not None:
                return f"Capital subsidy of {self.subsidy_percentage}% on eligible project cost"
            elif self.grant_amount is not None:
                return f"Direct financial grant of ₹{self.grant_amount:,.2f}"
            elif self.subsidy_details:
                return self.subsidy_details
            return "Government capital subsidy / financial grant assistance"
        elif cat == "SCHOLARSHIP":
            if self.subsidy_details:
                return self.subsidy_details
            return "Full/Partial scholarship assistance, tuition fee waiver and academic allowances"
        elif cat == "TRAINING_SKILL":
            if self.subsidy_details:
                return self.subsidy_details
            return "Free vocational skill training, modern toolkits and entrepreneurship development stipend"
        elif cat == "GUARANTEE_CREDIT_SUPPORT":
            if self.subsidy_details:
                return self.subsidy_details
            return "Credit guarantee coverage for collateral-free institutional borrowing"
        elif cat == "DIRECT_BENEFIT":
            if self.subsidy_details:
                return self.subsidy_details
            if "AYUSHMAN" in name:
                return "Comprehensive cashless health insurance cover of ₹5,00,000 per family per year"
            elif "MATRU VANDANA" in name:
                return "Direct cash incentive of ₹5,000 in two installments via DBT"
            elif "ATAL PENSION" in name:
                return "Guaranteed monthly pension of ₹1,000 - ₹5,000 post age 60"
            elif "SURAKSHA BIMA" in name or "JEEVAN JYOTI" in name:
                return "Direct insurance sum assured of ₹2,00,000"
            elif "SUKANYA" in name:
                return "High-yield government small savings deposit with 8.2% tax-free interest"
            return "Direct benefit transfer / social security coverage"
        return "Non-financial administrative, marketing, and institutional support"


