import re
from typing import Any, Tuple, Optional
from app.schemas.eligibility import RuleEvaluationResult

# Recognized alias groups for standard Indian civic/demographic categories
ALIAS_GROUPS = [
    {"SC", "SCHEDULED CASTE", "SCHEDULED_CASTE", "SCHEDULED CASTES"},
    {"ST", "SCHEDULED TRIBE", "SCHEDULED_TRIBE", "SCHEDULED TRIBES", "ADIVASI"},
    {"OBC", "OTHER BACKWARD CLASS", "OTHER_BACKWARD_CLASSES", "BACKWARD_CLASS", "OTHER BACKWARD CLASSES"},
    {"FEMALE", "WOMAN", "WOMEN"},
    {"MALE", "MAN", "MEN"},
    {"PWD", "DIVYANG", "PERSONS_WITH_DISABILITIES", "HANDICAPPED", "DISABILITY", "DIVYANGJAN"},
    {"ALL_INDIA", "ALL INDIA", "PAN INDIA", "NATIONAL", "CENTRAL"},
    {"EXISTING", "EXISTING_UNIT", "EXPANSION", "MODERNIZATION", "DIVERSIFICATION", "BROWNFIELD", "EXISTING_BUSINESS", "EXISTING_ONLY"},
    {"NEW", "NEW_UNIT", "GREENFIELD", "STARTUP", "FRESH_PROJECT", "NEW_BUSINESS"},
    {"MICRO", "MICRO_ENTERPRISE", "MICRO_BUSINESS", "TINY_UNIT"},
    {"SMALL", "SMALL_ENTERPRISE", "SMALL_BUSINESS"},
    {"MEDIUM", "MEDIUM_ENTERPRISE"},
]


def evaluate_operator(
    operator: str,
    required_value: str,
    value_type: str,
    actual_value: Optional[Any]
) -> Tuple[RuleEvaluationResult, str]:
    """
    Evaluates a single rule operator deterministically against beneficiary profile actual_value.
    
    Adheres strictly to Anti-Fabrication Rule:
    - Missing or undefined actual_value NEVER converts to PASS.
    - Ambiguous comparisons produce explainable UNKNOWN status.
    - Exact boundary semantics (<, <=, >, >=, ==, !=, IN, CONTAINS, BETWEEN).
    
    Returns:
        (RuleEvaluationResult, explanation_reason)
    """
    # 1. Missing / UNKNOWN actual value handling -> strictly UNKNOWN
    if actual_value is None or (
        isinstance(actual_value, str)
        and actual_value.strip().upper() in ("UNKNOWN", "NONE", "NULL", "", "NOT_SPECIFIED", "NOT_PUBLICLY_AVAILABLE")
    ):
        return (
            RuleEvaluationResult.UNKNOWN,
            f"Missing required profile input for field; condition requires '{operator} {required_value}'."
        )

    clean_op = operator.strip().upper()
    clean_req = str(required_value).strip()
    clean_val_type = (value_type or "STRING").strip().upper()

    # 2. BOOLEAN evaluation
    if clean_val_type in ("BOOLEAN", "BOOL"):
        req_bool = clean_req.upper() in ("TRUE", "1", "YES")
        if isinstance(actual_value, bool):
            act_bool = actual_value
        elif isinstance(actual_value, str):
            act_bool = actual_value.strip().upper() in ("TRUE", "1", "YES")
        else:
            act_bool = bool(actual_value)

        if clean_op in ("=", "=="):
            if act_bool == req_bool:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: Boolean flag matches requirement ({req_bool}).")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: Expected {req_bool}, but profile flag is {act_bool}.")
        elif clean_op in ("!=", "<>"):
            if act_bool != req_bool:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: Boolean flag correctly differs from {req_bool}.")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: Boolean flag is {act_bool}, but requirement specifies not {req_bool}.")

    # 3. CONTAINS evaluation (Tag, Token or Multivalue Membership)
    if clean_op == "CONTAINS":
        target_token = clean_req.upper()
        # If actual_value is boolean (e.g. is_pwd passed for target_groups CONTAINS PWD)
        if isinstance(actual_value, bool):
            if actual_value:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: Profile satisfies requirement '{clean_req}'.")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: Profile does not satisfy requirement '{clean_req}'.")

        act_str = str(actual_value).strip().upper()
        act_tokens = [t.strip().upper() for t in re.split(r"[,;/\s]+", act_str) if t.strip()]

        # Explicit negative token check (e.g. NON_PWD, NON_SC, NOT_ELIGIBLE)
        if f"NON_{target_token}" in act_tokens or f"NOT_{target_token}" in act_tokens or act_str in (f"NON_{target_token}", f"NOT_{target_token}", "NONE", "NO"):
            return (RuleEvaluationResult.FAIL, f"Condition failed: '{actual_value}' does not satisfy requirement '{clean_req}'.")

        # Word-boundary or exact token match
        if target_token in act_tokens or bool(re.search(rf"\b{re.escape(target_token)}\b", act_str)):
            return (RuleEvaluationResult.PASS, f"Condition satisfied: '{actual_value}' contains required '{clean_req}'.")

        # Alias-aware token match
        for grp in ALIAS_GROUPS:
            if target_token in grp:
                if any(t in grp for t in act_tokens) or any(bool(re.search(rf"\b{re.escape(item)}\b", act_str)) for item in grp):
                    return (RuleEvaluationResult.PASS, f"Condition satisfied: '{actual_value}' matches category '{clean_req}'.")

        return (RuleEvaluationResult.FAIL, f"Condition failed: '{actual_value}' does not contain required '{clean_req}'.")

    # 4. ENUM / TEXT / IN / NOT IN evaluation
    if clean_op in ("IN", "NOT IN", "NOT_IN"):
        allowed_items = [item.strip().upper() for item in clean_req.replace(";", ",").split(",") if item.strip()]
        act_str = str(actual_value).strip().upper()
        act_clean = act_str.replace("_", " ")

        matched = False
        if act_str in allowed_items:
            matched = True
        else:
            for item in allowed_items:
                item_clean = item.replace("_", " ")
                if act_str == item or act_clean == item_clean:
                    matched = True
                    break
                # Check alias groups
                for grp in ALIAS_GROUPS:
                    if (item in grp or item_clean in grp) and (act_str in grp or act_clean in grp):
                        matched = True
                        break
                if matched:
                    break

        if clean_op == "IN":
            if matched:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: Value '{actual_value}' is allowed in [{clean_req}].")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: Value '{actual_value}' is not in required list [{clean_req}].")
        else:  # NOT IN
            if not matched:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: Value '{actual_value}' is excluded from [{clean_req}].")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: Value '{actual_value}' is restricted in [{clean_req}].")

    # 5. BETWEEN / RANGE evaluation
    if clean_op in ("BETWEEN", "RANGE"):
        parts = re.split(r"[-–,;\s]+", clean_req)
        if len(parts) >= 2:
            try:
                b_min = float(parts[0])
                b_max = float(parts[1])
                act_num = float(actual_value)
                if b_min <= act_num <= b_max:
                    return (RuleEvaluationResult.PASS, f"Condition satisfied: Value {act_num} is within range [{b_min}, {b_max}].")
                else:
                    return (RuleEvaluationResult.FAIL, f"Condition failed: Value {act_num} is outside range [{b_min}, {b_max}].")
            except (ValueError, TypeError):
                return (RuleEvaluationResult.UNKNOWN, f"Cannot parse numeric range '{clean_req}' for operator '{operator}'.")

    # 6. Numeric comparisons (INR, PERCENT, MONTHS, INT, FLOAT, COUNT, etc.)
    try:
        req_num = float(clean_req)
        act_num = float(actual_value)
        is_numeric = True
    except (ValueError, TypeError):
        is_numeric = False

    if is_numeric:
        if clean_op in ("=", "=="):
            if abs(act_num - req_num) < 1e-5:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: Value {act_num} equals required {req_num}.")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: Expected {req_num}, got {act_num}.")

        elif clean_op in ("!=", "<>"):
            if abs(act_num - req_num) >= 1e-5:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: Value {act_num} != {req_num}.")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: Value {act_num} must not equal {req_num}.")

        elif clean_op == "<":
            if act_num < req_num:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: {act_num} < {req_num}.")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: {act_num} must be strictly less than {req_num}.")

        elif clean_op == "<=":
            if act_num <= req_num:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: {act_num} <= {req_num}.")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: {act_num} exceeds maximum limit of {req_num}.")

        elif clean_op == ">":
            if act_num > req_num:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: {act_num} > {req_num}.")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: {act_num} must be strictly greater than {req_num}.")

        elif clean_op == ">=":
            if act_num >= req_num:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: {act_num} >= {req_num}.")
            else:
                return (RuleEvaluationResult.FAIL, f"Condition failed: {act_num} is below minimum requirement of {req_num}.")

    # 7. Non-numeric string equality / inequality fallback
    act_str_clean = str(actual_value).strip().upper()
    req_str_clean = clean_req.upper()

    if clean_op in ("=", "=="):
        # Direct string equality or alias group match
        if act_str_clean == req_str_clean:
            return (RuleEvaluationResult.PASS, f"Condition satisfied: Value matches required '{clean_req}'.")
        for grp in ALIAS_GROUPS:
            if act_str_clean in grp and req_str_clean in grp:
                return (RuleEvaluationResult.PASS, f"Condition satisfied: '{actual_value}' matches canonical category '{clean_req}'.")
        return (RuleEvaluationResult.FAIL, f"Condition failed: Expected '{clean_req}', got '{actual_value}'.")

    elif clean_op in ("!=", "<>"):
        if act_str_clean != req_str_clean:
            return (RuleEvaluationResult.PASS, f"Condition satisfied: Value '{actual_value}' != '{clean_req}'.")
        else:
            return (RuleEvaluationResult.FAIL, f"Condition failed: Value must not equal '{clean_req}'.")

    return (RuleEvaluationResult.UNKNOWN, f"Unsupported operator '{operator}'.")
