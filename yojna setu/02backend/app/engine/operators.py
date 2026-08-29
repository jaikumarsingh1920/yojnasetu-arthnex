from typing import Any, Tuple, Optional
from app.schemas.eligibility import RuleEvaluationResult


def evaluate_operator(
    operator: str,
    required_value: str,
    value_type: str,
    actual_value: Optional[Any]
) -> Tuple[RuleEvaluationResult, str]:
    """
    Evaluates a single rule operator against beneficiary profile actual_value.
    Returns (RuleEvaluationResult, explanation_reason).
    """
    # 1. Missing / UNKNOWN actual value handling
    if actual_value is None:
        return (
            RuleEvaluationResult.UNKNOWN,
            f"Missing required profile input for field; condition requires '{operator} {required_value}'."
        )

    clean_op = operator.strip()
    clean_req = required_value.strip()

    # 2. BOOLEAN evaluation
    if value_type.upper() == "BOOLEAN":
        req_bool = clean_req.upper() in ("TRUE", "1", "YES")
        if isinstance(actual_value, bool):
            act_bool = actual_value
        elif isinstance(actual_value, str):
            act_bool = actual_value.strip().upper() in ("TRUE", "1", "YES")
        else:
            act_bool = bool(actual_value)

        if clean_op == "=":
            if act_bool == req_bool:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: Boolean flag matches requirement ({req_bool}).")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: Expected {req_bool}, but profile flag is {act_bool}.")

    # 3. ENUM / TEXT / IN evaluation
    if clean_op == "IN":
        allowed_items = [item.strip().upper() for item in clean_req.replace(";", ",").split(",") if item.strip()]
        act_str = str(actual_value).strip().upper()
        
        # Also handle mapped categories e.g. SC -> BACKWARD_CLASS or SC -> SCHEDULED_CASTE
        if act_str in allowed_items or any(item in act_str for item in allowed_items):
            return (RuleEvaluationResult.PASS, f"Condition satisfied: Value '{actual_value}' is allowed in [{clean_req}].")
        else:
            return (RuleEvaluationResult.FAIL, f"Condition failed: Value '{actual_value}' is not in required list [{clean_req}].")

    # 4. Numeric operators (INR, PERCENT, MONTHS, INR_PER_YEAR, PERCENT_PER_ANNUM)
    try:
        req_num = float(clean_req)
        act_num = float(actual_value)
    except (ValueError, TypeError):
        # Fallback to string equality if non-numeric string comparison
        if clean_op == "=":
            if str(actual_value).strip().upper() == clean_req.upper():
                return (RuleEvaluationResult.PASS, f"Condition satisfied: Value matches required '{clean_req}'.")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: Expected '{clean_req}', got '{actual_value}'.")
        return (
            RuleEvaluationResult.UNKNOWN,
            f"Could not perform numeric comparison '{operator}' between required '{clean_req}' and actual '{actual_value}'."
        )

    if clean_op == "=":
        if abs(act_num - req_num) < 1e-5:
            return (RuleEvaluationResult.PASS, f"Condition satisfied: Value {act_num} equals required {req_num}.")
        else:
            return (RuleEvaluationResult.FAIL, f"Condition failed: Expected {req_num}, got {act_num}.")

    elif clean_op == "<=":
        if act_num <= req_num:
            return (RuleEvaluationResult.PASS, f"Condition satisfied: {act_num} <= {req_num}.")
        else:
            return (RuleEvaluationResult.FAIL, f"Condition failed: {act_num} exceeds maximum limit of {req_num}.")

    elif clean_op == ">=":
        if act_num >= req_num:
            return (RuleEvaluationResult.PASS, f"Condition satisfied: {act_num} >= {req_num}.")
        else:
            return (RuleEvaluationResult.FAIL, f"Condition failed: {act_num} is below minimum requirement of {req_num}.")

    elif clean_op == ">":
        if act_num > req_num:
            return (RuleEvaluationResult.PASS, f"Condition satisfied: {act_num} > {req_num}.")
        else:
            return (RuleEvaluationResult.FAIL, f"Condition failed: {act_num} must be strictly greater than {req_num}.")

    return (RuleEvaluationResult.UNKNOWN, f"Unsupported operator '{operator}'.")
