from typing import Optional
from pydantic import BaseModel, Field


class BeneficiaryProfileInput(BaseModel):
    """
    Typed beneficiary profile model containing fields required by current scheme rules.
    Missing fields are represented as None (Explicit UNKNOWN state).
    """
    age: Optional[int] = Field(default=None, description="Age in years")
    annual_income: Optional[float] = Field(default=None, description="Annual family income in INR")
    social_category: Optional[str] = Field(default=None, description="Social category e.g. SC, ST, OBC, BACKWARD_CLASS, GENERAL")
    is_sc: Optional[bool] = Field(default=None, description="Flag indicating if applicant belongs to Scheduled Caste")
    gender: Optional[str] = Field(default=None, description="Gender e.g. FEMALE, MALE, TRANSGENDER")
    state: Optional[str] = Field(default=None, description="State of residence/business")
    district: Optional[str] = Field(default=None, description="District of residence/business")
    
    applicant_type: Optional[str] = Field(default=None, description="Applicant type e.g. INDIVIDUAL, STUDENT, SHG")
    entrepreneur_type: Optional[str] = Field(default=None, description="Entrepreneur classification e.g. MICRO, ARTISAN")
    business_stage: Optional[str] = Field(default=None, description="Business stage e.g. NEW, EXISTING")
    is_new_unit: Optional[bool] = Field(default=None, description="True if project is a new unit")
    
    sector: Optional[str] = Field(default=None, description="Business sector e.g. MSME, TRADITIONAL_TRADE, AGRICULTURE")
    activity_type: Optional[str] = Field(default=None, description="Activity or trade type e.g. TRADITIONAL_TRADE_18")
    
    project_cost: Optional[float] = Field(default=None, description="Total project cost in INR")
    requested_loan_amount: Optional[float] = Field(default=None, description="Requested loan amount in INR")
    collateral_available: Optional[bool] = Field(default=None, description="Flag indicating collateral availability")
    application_route: Optional[str] = Field(default=None, description="Channel route e.g. AUTHORISED_SCA, PM_SURAJ")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 28,
                "annual_income": 180000.0,
                "social_category": "SC",
                "is_sc": True,
                "gender": "MALE",
                "state": "MAHARASHTRA",
                "applicant_type": "INDIVIDUAL",
                "is_new_unit": True,
                "activity_type": "TRADITIONAL_TRADE_18",
                "project_cost": 100000.0,
                "requested_loan_amount": 90000.0,
                "application_route": "AUTHORISED_SCA"
            }
        }
