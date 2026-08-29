from typing import List, Optional, Any
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# Input Model
# ─────────────────────────────────────────────────────────────

class RepaymentFrequency(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"


class FinancialCalculationInput(BaseModel):
    """
    Input model for deterministic financial calculation.
    Only beneficiary-scenario fields are accepted here.
    Scheme-authoritative financial parameters (interest rate, financing %,
    moratorium, etc.) are loaded exclusively from the database.
    """
    scheme_id: str = Field(..., description="Scheme ID to calculate financing for")
    project_cost: Optional[Decimal] = Field(default=None, description="Total project cost in INR")
    requested_loan_amount: Optional[Decimal] = Field(default=None, description="Requested loan amount in INR")
    repayment_period_months: Optional[int] = Field(default=None, description="Requested repayment tenure in months")
    repayment_frequency: Optional[RepaymentFrequency] = Field(
        default=None,
        description="Repayment frequency override — only used when scheme allows multiple frequencies"
    )


# ─────────────────────────────────────────────────────────────
# Traceability & Resolved Parameter Models
# ─────────────────────────────────────────────────────────────

class ParameterResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    UNKNOWN = "UNKNOWN"
    CONDITIONAL = "CONDITIONAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResolvedFinancialParameter(BaseModel):
    """
    A single scheme-authoritative financial parameter, resolved from
    the database rules or master scheme attributes, with full provenance.
    """
    field: str
    value: Optional[Any] = None
    status: ParameterResolutionStatus
    source_rule_id: Optional[str] = Field(default=None, description="Rule ID that produced this value")
    source_document: Optional[str] = Field(default=None, description="Source document reference")
    source_page: Optional[str] = Field(default=None, description="Source page reference")
    reason: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────

class ValidationError(BaseModel):
    field: str
    message: str
    requested_value: Optional[Any] = None
    authoritative_limit: Optional[Any] = None


# ─────────────────────────────────────────────────────────────
# Amortization
# ─────────────────────────────────────────────────────────────

class AmortizationEntry(BaseModel):
    installment_number: int
    period_label: str
    opening_principal: Decimal
    installment_amount: Decimal
    interest_component: Decimal
    principal_component: Decimal
    closing_principal: Decimal


# ─────────────────────────────────────────────────────────────
# Output Model
# ─────────────────────────────────────────────────────────────

class FinancialCalculationStatus(str, Enum):
    CALCULATED = "CALCULATED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class FinancialCalculationResult(BaseModel):
    """
    Complete result of a deterministic financial calculation for a scheme.
    Every resolved parameter carries full traceability to its authoritative source.
    """
    status: FinancialCalculationStatus
    scheme_id: str
    scheme_name: str

    # Resolved authoritative parameters (with traceability)
    resolved_parameters: List[ResolvedFinancialParameter] = Field(default_factory=list)

    # Computed amounts (only populated when status = CALCULATED)
    project_cost: Optional[Decimal] = None
    requested_loan_amount: Optional[Decimal] = None
    eligible_loan_amount: Optional[Decimal] = None
    beneficiary_contribution_amount: Optional[Decimal] = None
    subsidy_amount: Optional[Decimal] = None
    grant_amount: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    repayment_period_months: Optional[int] = None
    repayment_frequency: Optional[str] = None
    moratorium_months: Optional[int] = None
    moratorium_interest_mode: Optional[str] = None
    periodic_installment: Optional[Decimal] = None
    total_interest: Optional[Decimal] = None
    total_repayment: Optional[Decimal] = None

    # Amortization schedule
    amortization_schedule: List[AmortizationEntry] = Field(default_factory=list)

    # Diagnostic fields
    validation_errors: List[ValidationError] = Field(default_factory=list)
    missing_parameters: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(round(v, 2))
        }
