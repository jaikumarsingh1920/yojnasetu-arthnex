from typing import List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class RuleEvaluationResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONDITIONAL = "CONDITIONAL"


class SchemeEligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class RuleEvaluationDetail(BaseModel):
    rule_id: str
    field: str
    operator: str
    required_value: Any
    value_type: str
    rule_type: str
    priority: str
    condition_group: str
    actual_value: Optional[Any] = None
    result: RuleEvaluationResult
    reason: str


class SchemeEligibilityResult(BaseModel):
    scheme_id: str
    scheme_name: str
    verification_status: str
    status: SchemeEligibilityStatus
    
    # Question A: Hard Eligibility Rule Evaluations
    hard_rules_passed: List[RuleEvaluationDetail] = Field(default_factory=list)
    hard_rules_failed: List[RuleEvaluationDetail] = Field(default_factory=list)
    unknown_eligibility_rules: List[RuleEvaluationDetail] = Field(default_factory=list)
    
    # Question B: Financial & Application Evaluations (Independent of Eligibility Status)
    financial_rules: List[RuleEvaluationDetail] = Field(default_factory=list)
    application_rules: List[RuleEvaluationDetail] = Field(default_factory=list)
    
    explanations: List[str] = Field(default_factory=list)


class BatchEligibilityResponse(BaseModel):
    total_evaluated: int
    eligible_count: int
    ineligible_count: int
    insufficient_info_count: int
    results: List[SchemeEligibilityResult]
