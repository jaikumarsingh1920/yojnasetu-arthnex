from typing import List, Optional, Any, Dict
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.schemas.profile import BeneficiaryProfileInput


class FinancialHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    MODERATE = "MODERATE"
    STRESSED = "STRESSED"
    HIGH_RISK = "HIGH_RISK"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class FinancialIndicatorStatus(str, Enum):
    HEALTHY = "HEALTHY"
    MODERATE = "MODERATE"
    STRESSED = "STRESSED"
    HIGH_RISK = "HIGH_RISK"
    NOT_EVALUATED = "NOT_EVALUATED"


class FinancialIndicatorResult(BaseModel):
    indicator_name: str = Field(..., description="Unique technical identifier of the metric (e.g. foir)")
    label: str = Field(..., description="Human-readable title (e.g. Fixed Obligation to Income Ratio)")
    value: Optional[Decimal] = Field(default=None, description="Computed raw numeric value")
    formatted_value: str = Field(..., description="Formatted string representation (e.g. '28.5%')")
    benchmark: str = Field(..., description="Target reference benchmark (e.g. '<= 30% Healthy')")
    status: FinancialIndicatorStatus = Field(..., description="Assessment status for this indicator")
    score: Optional[Decimal] = Field(default=None, description="Score contribution between 0.0 and 100.0")
    weight: Decimal = Field(..., description="Weight assigned to this indicator in total score")
    explanation: str = Field(..., description="Transparent factual explanation of this calculation")


class MissingFinancialField(BaseModel):
    field: str = Field(..., description="Missing attribute name")
    label: str = Field(..., description="User-friendly field label")
    impact_reason: str = Field(..., description="Explanation of why this field is required for financial health")


class FinancialHealthInput(BaseModel):
    """
    Input model for deterministic financial health assessment.
    Can be populated from a BeneficiaryProfileInput or with standalone explicit financial values.
    """
    annual_income: Optional[Decimal] = Field(default=None, description="Annual family income in INR (>= 0)")
    monthly_income: Optional[Decimal] = Field(default=None, description="Monthly income in INR (override or auto-derived from annual_income / 12)")
    requested_loan_amount: Optional[Decimal] = Field(default=None, description="Requested borrowing / loan amount in INR (>= 0)")
    project_cost: Optional[Decimal] = Field(default=None, description="Total project / enterprise setup cost in INR (>= 0)")
    existing_liabilities: Optional[Decimal] = Field(default=None, description="Total outstanding debt in INR (>= 0)")
    monthly_obligations: Optional[Decimal] = Field(default=None, description="Existing monthly debt service payments / EMIs in INR (>= 0)")
    monthly_expenses: Optional[Decimal] = Field(default=None, description="Monthly household or operational expenses in INR (>= 0)")
    liquid_savings: Optional[Decimal] = Field(default=None, description="Available liquid savings / emergency funds in INR (>= 0)")
    scheme_id: Optional[str] = Field(default=None, description="Optional scheme ID to evaluate scheme-specific loan installment impact")
    estimated_scheme_installment: Optional[Decimal] = Field(default=None, description="Estimated monthly EMI under the target scheme in INR (>= 0)")
    interest_rate: Optional[Decimal] = Field(default=None, description="Optional annual interest rate percentage (e.g. 8.5)")
    tenure_months: Optional[int] = Field(default=None, description="Optional repayment tenure in months (e.g. 36)")
    profile: Optional[BeneficiaryProfileInput] = Field(default=None, description="Optional full citizen profile to extract financial values from")

    @field_validator(
        "annual_income",
        "monthly_income",
        "requested_loan_amount",
        "project_cost",
        "existing_liabilities",
        "monthly_obligations",
        "monthly_expenses",
        "liquid_savings",
        "estimated_scheme_installment",
        mode="before"
    )
    @classmethod
    def validate_non_negative_decimals(cls, v: Any) -> Optional[Decimal]:
        if v is None or v == "" or v == "UNKNOWN" or v == "NOT_APPLICABLE":
            return None
        try:
            d = Decimal(str(v))
            if d.is_nan() or d.is_infinite():
                return None
            if d < Decimal("0"):
                raise ValueError("Financial amount cannot be negative.")
            return d
        except (ValueError, TypeError) as e:
            if isinstance(e, ValueError) and "cannot be negative" in str(e):
                raise
            raise ValueError("Invalid numeric value for financial parameter.")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(round(v, 2))
        }


class FinancialHealthResponse(BaseModel):
    """
    Transparent, explainable output model for financial health status.
    Every indicator provides exact benchmarks, values, and rationale.
    """
    status: FinancialHealthStatus = Field(..., description="HEALTHY, MODERATE, STRESSED, HIGH_RISK, or INSUFFICIENT_INFORMATION")
    score: Optional[Decimal] = Field(default=None, description="Deterministic financial health score (0.0 to 100.0) or None if insufficient info")
    summary_headline: str = Field(..., description="Concise executive summary of financial suitability")
    indicators: List[FinancialIndicatorResult] = Field(default_factory=list, description="Detailed breakdown of evaluated financial dimensions")
    risk_flags: List[str] = Field(default_factory=list, description="Factual warnings and financial stress signals")
    positive_factors: List[str] = Field(default_factory=list, description="Factual strengths supporting borrowing capacity")
    recommendations: List[str] = Field(default_factory=list, description="Actionable financial guidance for the citizen")
    missing_fields: List[MissingFinancialField] = Field(default_factory=list, description="Required fields missing to unlock complete assessment")

    # Core monthly metrics
    monthly_income: Optional[Decimal] = Field(default=None, description="Calculated monthly family income in INR")
    monthly_expenses: Optional[Decimal] = Field(default=None, description="Declared monthly household or operational expenses in INR")
    existing_monthly_obligations: Optional[Decimal] = Field(default=None, description="Existing monthly debt obligations in INR")
    proposed_monthly_emi: Optional[Decimal] = Field(default=None, description="Calculated new monthly EMI in INR")
    total_monthly_obligations: Optional[Decimal] = Field(default=None, description="Total monthly debt service (existing obligations + proposed EMI)")
    debt_to_income_ratio: Optional[Decimal] = Field(default=None, description="Total debt-to-income ratio (FOIR) in percentage")
    estimated_disposable_income: Optional[Decimal] = Field(default=None, description="Monthly income remaining after debt service and living expenses")
    required_margin_money: Optional[Decimal] = Field(default=None, description="Beneficiary equity contribution needed (project_cost - loan)")
    margin_money_gap: Optional[Decimal] = Field(default=None, description="Shortfall between required margin and liquid savings")

    # Provenance and methodology audit
    calculation_version: str = Field(default="v1.0-SIH-DETERMINISTIC", description="Version of the deterministic financial health evaluation algorithm")
    evaluated_at: str = Field(..., description="UTC ISO timestamp of evaluation")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(round(v, 2))
        }


class SchemeFinancialSuitability(str, Enum):
    STRONG_FIT = "STRONG_FIT"
    POSSIBLE_FIT = "POSSIBLE_FIT"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    FINANCIALLY_UNSUITABLE = "FINANCIALLY_UNSUITABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SchemeFinancialAssessment(BaseModel):
    """
    Evaluates citizen financial profile against a specific scheme's financial parameters.
    """
    scheme_id: str = Field(..., description="Unique scheme ID")
    scheme_name: str = Field(..., description="Official scheme name")
    suitability: SchemeFinancialSuitability = Field(..., description="STRONG_FIT, POSSIBLE_FIT, INSUFFICIENT_INFORMATION, or FINANCIALLY_UNSUITABLE")
    suitability_reason: str = Field(..., description="Transparent deterministic reason for financial fit")

    project_cost: Optional[Decimal] = Field(default=None, description="Citizen's project cost")
    own_contribution: Optional[Decimal] = Field(default=None, description="Citizen's declared own contribution / liquid savings")
    required_margin_money: Optional[Decimal] = Field(default=None, description="Required promoter equity/margin under scheme rules")
    margin_money_gap: Optional[Decimal] = Field(default=None, description="Shortfall in margin money if any")
    required_loan: Optional[Decimal] = Field(default=None, description="Net borrowing required after subsidy and own contribution")

    available_subsidy: Optional[Decimal] = Field(default=None, description="Estimated capital / margin subsidy in INR")
    subsidy_percentage: Optional[Decimal] = Field(default=None, description="Official subsidy percentage if available")
    available_grant: Optional[Decimal] = Field(default=None, description="Direct capital grant amount if available")

    estimated_emi: Optional[Decimal] = Field(default=None, description="Estimated monthly repayment installment if rate/tenure available")
    interest_rate_display: str = Field(default="NOT_PUBLICLY_AVAILABLE", description="Interest rate range or status")
    repayment_tenure_display: str = Field(default="NOT_PUBLICLY_AVAILABLE", description="Repayment tenure in months/years")
    moratorium_display: str = Field(default="NOT_PUBLICLY_AVAILABLE", description="Moratorium period")
    collateral_requirement_display: str = Field(default="NOT_PUBLICLY_AVAILABLE", description="Collateral policy (NO, YES, CONDITIONAL, NOT_PUBLICLY_AVAILABLE)")
    guarantee_requirement_display: str = Field(default="NOT_PUBLICLY_AVAILABLE", description="Guarantee coverage (e.g. CGTMSE) or status")
    processing_fee_display: str = Field(default="NOT_PUBLICLY_AVAILABLE", description="Processing fee details or status")

    max_project_cost: Optional[Decimal] = Field(default=None, description="Scheme maximum project cost ceiling")
    min_project_cost: Optional[Decimal] = Field(default=None, description="Scheme minimum project cost threshold")
    max_loan_amount: Optional[Decimal] = Field(default=None, description="Scheme maximum loan limit")
    min_loan_amount: Optional[Decimal] = Field(default=None, description="Scheme minimum loan limit")

    is_project_cost_eligible: Optional[bool] = Field(default=None, description="True if project cost within scheme limits")
    is_loan_amount_eligible: Optional[bool] = Field(default=None, description="True if required loan within scheme limits")
    is_own_contribution_sufficient: Optional[bool] = Field(default=None, description="True if citizen has enough margin money")

    missing_parameters: List[str] = Field(default_factory=list, description="Parameters unstated in official guidelines")
    unmet_criteria: List[str] = Field(default_factory=list, description="Specific financial limits exceeded or violated")
    positive_factors: List[str] = Field(default_factory=list, description="Financial strengths aligning with this scheme")

    @property
    def available_subsidy_amount(self) -> Optional[Decimal]:
        return self.available_subsidy

    class Config:
        json_encoders = {
            Decimal: lambda v: float(round(v, 2))
        }

