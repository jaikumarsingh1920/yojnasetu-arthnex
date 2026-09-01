from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class BeneficiaryProfileInput(BaseModel):
    """
    Authoritative canonical citizen profile model used across:
    - Eligibility Engine (Question A)
    - Soft-Fit Recommendation Engine (Ranking & Scoring)
    - Scheme-Aware Financial Calculator (Loan pre-fill)
    - Official Channel Partner Locator (District/State routing)
    - Application Guidance Engine (Snapshot verification)
    """
    # 1. Personal & Social Identity
    age: Optional[int] = Field(default=None, description="Age in years (14 to 120)")
    gender: Optional[str] = Field(default=None, description="Gender: FEMALE, MALE, TRANSGENDER, OTHER")
    marital_status: Optional[str] = Field(default=None, description="Marital status: SINGLE, MARRIED, WIDOWED, DIVORCED")
    state: Optional[str] = Field(default=None, description="State of residence / enterprise (e.g. ALL_INDIA, UTTAR_PRADESH, MAHARASHTRA)")
    district: Optional[str] = Field(default=None, description="District of residence / enterprise")
    social_category: Optional[str] = Field(default=None, description="Social category: SC, ST, OBC, GENERAL, MINORITY, BACKWARD_CLASS")
    is_sc: Optional[bool] = Field(default=None, description="Flag indicating if applicant belongs to Scheduled Caste")
    is_pwd: Optional[bool] = Field(default=None, description="Flag indicating if applicant is a Person with Disabilities / Divyangjan")
    disability_status: Optional[str] = Field(default=None, description="Disability description / certification status")
    is_minority: Optional[bool] = Field(default=None, description="Flag indicating if applicant belongs to a notified minority community")

    # 2. Economic & Income
    annual_income: Optional[float] = Field(default=None, description="Annual family income in INR (>= 0)")
    employment_status: Optional[str] = Field(default=None, description="Employment status: UNEMPLOYED, SELF_EMPLOYED, SALARIED, STUDENT, DAILY_WAGE")
    occupation: Optional[str] = Field(default=None, description="Specific trade, job, or occupation title")

    # 3. Education & Vocation
    education_level: Optional[str] = Field(default=None, description="Education level: BELOW_8TH, 8TH_PASS, 10TH_PASS, 12TH_PASS, DIPLOMA, GRADUATE, POST_GRADUATE, DOCTORATE, ILLITERATE")
    applicant_type: Optional[str] = Field(default=None, description="Applicant type: INDIVIDUAL, STUDENT, FARMER, ARTISAN, STREET_VENDOR, WOMEN_ENTREPRENEUR, SHG, MICRO_ENTERPRISE, STARTUP")
    entrepreneur_type: Optional[str] = Field(default=None, description="Entrepreneur classification: MICRO, ARTISAN, SMALL, MEDIUM")
    
    # Specific Vocation Flags
    is_artisan: Optional[bool] = Field(default=None, description="Flag indicating if applicant is a traditional artisan / craftsman")
    is_farmer: Optional[bool] = Field(default=None, description="Flag indicating if applicant is a farmer / agricultural producer")
    is_street_vendor: Optional[bool] = Field(default=None, description="Flag indicating if applicant is an urban/rural street vendor")
    is_safai_karamchari: Optional[bool] = Field(default=None, description="Flag indicating if applicant is a sanitation worker / manual scavenger rehabilitation beneficiary")

    # 4. Enterprise / Project Parameters
    sector: Optional[str] = Field(default=None, description="Economic sector: MSME, AGRICULTURE, TEXTILES, HANDICRAFTS, EDUCATION, SERVICES, TRADING, DAIRY, FOOD_PROCESSING, SANITATION, HEALTHCARE, HOUSING, GREEN_ENERGY")
    activity_type: Optional[str] = Field(default=None, description="Specific trade or activity: TRADITIONAL_TRADE_18, DAIRY_FARMING, MICRO_RETAIL, MANUFACTURING, SERVICES, STREET_VENDING, HANDLOOM_WEAVING, SANITATION_WORK")
    business_stage: Optional[str] = Field(default=None, description="Business stage: NEW_BUSINESS, EXISTING_BUSINESS, EXPANSION")
    is_new_unit: Optional[bool] = Field(default=None, description="True if project is establishing a new unit")
    
    project_cost: Optional[float] = Field(default=None, description="Estimated total project/setup cost in INR (>= 0)")
    requested_loan_amount: Optional[float] = Field(default=None, description="Requested credit / loan amount in INR (>= 0)")
    collateral_available: Optional[bool] = Field(default=None, description="Flag indicating if collateral security is available")
    application_route: Optional[str] = Field(default=None, description="Channel route: DIRECT_PORTAL, PARTNER_ASSISTED")

    @field_validator("social_category", mode="before")
    @classmethod
    def normalize_social_category(cls, v: Any) -> Optional[str]:
        if not v or v == "UNKNOWN":
            return None
        return str(v).strip().upper()

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, v: Any) -> Optional[str]:
        if not v or v == "UNKNOWN":
            return None
        return str(v).strip().upper()

    @field_validator("annual_income", "project_cost", "requested_loan_amount", mode="before")
    @classmethod
    def validate_non_negative_floats(cls, v: Any) -> Optional[float]:
        if v is None or v == "" or v == "UNKNOWN":
            return None
        try:
            val = float(v)
            if val < 0:
                raise ValueError("Amount cannot be negative.")
            return val
        except (ValueError, TypeError) as e:
            if isinstance(e, ValueError) and "cannot be negative" in str(e):
                raise
            raise ValueError("Invalid numeric value.")

    @field_validator("age", mode="before")
    @classmethod
    def validate_age_bounds(cls, v: Any) -> Optional[int]:
        if v is None or v == "" or v == "UNKNOWN":
            return None
        try:
            val = int(v)
            if val < 0 or val > 120:
                raise ValueError("Age must be between 0 and 120 years.")
            return val
        except (ValueError, TypeError) as e:
            if isinstance(e, ValueError) and "between 0 and 120" in str(e):
                raise
            raise ValueError("Age must be a valid integer between 0 and 120.")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 28,
                "gender": "FEMALE",
                "state": "MAHARASHTRA",
                "social_category": "SC",
                "is_sc": True,
                "annual_income": 180000.0,
                "applicant_type": "INDIVIDUAL",
                "employment_status": "SELF_EMPLOYED",
                "education_level": "10TH_PASS",
                "sector": "TEXTILES",
                "activity_type": "TRADITIONAL_TRADE_18",
                "business_stage": "NEW_BUSINESS",
                "is_new_unit": True,
                "project_cost": 100000.0,
                "requested_loan_amount": 90000.0,
                "collateral_available": False,
                "application_route": "PARTNER_ASSISTED"
            }
        }


class MissingFieldDetail(BaseModel):
    field: str
    label: str
    impact_reason: str
    category: str


class CitizenProfileResponse(BaseModel):
    profile: BeneficiaryProfileInput
    completion_percentage: int
    completed_fields_count: int
    total_fields_count: int
    missing_fields: List[MissingFieldDetail]
    is_eligible_for_smart_matching: bool


# Core high-impact fields evaluated across eligibility and recommendation rules
CORE_PROFILE_FIELD_METADATA = [
    {
        "field": "age",
        "label": "Age",
        "category": "Personal & Identity",
        "impact_reason": "Required to check minimum and maximum entry age criteria for 90 government schemes."
    },
    {
        "field": "gender",
        "label": "Gender",
        "category": "Personal & Identity",
        "impact_reason": "Enables unlocking exclusive women welfare schemes, Stand-Up India, and maternal benefits."
    },
    {
        "field": "state",
        "label": "State of Residence / Enterprise",
        "category": "Location & Geography",
        "impact_reason": "Verifies state-level eligibility versus Central Pan-India applicability."
    },
    {
        "field": "social_category",
        "label": "Social Category (SC/ST/OBC/General)",
        "category": "Social Background",
        "impact_reason": "Unlocks targeted apex corporation credit lines (NSFDC, NSTFDC, NBCFDC, NMDFC)."
    },
    {
        "field": "annual_income",
        "label": "Annual Family Income",
        "category": "Economic Status",
        "impact_reason": "Determines eligibility for income-capped welfare, BPL subsidies, and scholarships."
    },
    {
        "field": "applicant_type",
        "label": "Applicant Category / Vocation",
        "category": "Employment & Vocation",
        "impact_reason": "Identifies if you are an artisan, farmer, student, street vendor, or entrepreneur."
    },
    {
        "field": "education_level",
        "label": "Education Level",
        "category": "Education & Skills",
        "impact_reason": "Required for schemes requiring 8th pass (e.g. PMEGP) or scholarships."
    },
    {
        "field": "sector",
        "label": "Business / Economic Sector",
        "category": "Enterprise & Project",
        "impact_reason": "Matches schemes in MSME, Agriculture, Traditional Trades, or Services."
    },
    {
        "field": "business_stage",
        "label": "Business Stage",
        "category": "Enterprise & Project",
        "impact_reason": "Distinguishes new greenfield units from existing enterprise expansion credit."
    },
    {
        "field": "project_cost",
        "label": "Project Cost / Loan Requirement",
        "category": "Enterprise & Project",
        "impact_reason": "Aligns project scale with official loan ceilings and calculates exact margin money."
    },
]


def calculate_profile_completion(profile: BeneficiaryProfileInput) -> CitizenProfileResponse:
    """
    Computes deterministic completion percentage and missing fields list.
    """
    missing: List[MissingFieldDetail] = []
    completed_count = 0
    total_count = len(CORE_PROFILE_FIELD_METADATA)

    for item in CORE_PROFILE_FIELD_METADATA:
        field_name = item["field"]
        val = getattr(profile, field_name, None)
        if val is not None and val != "" and val != "UNKNOWN":
            completed_count += 1
        else:
            missing.append(MissingFieldDetail(
                field=field_name,
                label=item["label"],
                category=item["category"],
                impact_reason=item["impact_reason"]
            ))

    percentage = int(round((completed_count / total_count) * 100)) if total_count > 0 else 0

    return CitizenProfileResponse(
        profile=profile,
        completion_percentage=percentage,
        completed_fields_count=completed_count,
        total_fields_count=total_count,
        missing_fields=missing,
        is_eligible_for_smart_matching=completed_count >= 3
    )
