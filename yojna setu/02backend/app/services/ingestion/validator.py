import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List

logger = logging.getLogger("yojnasetu.ingestion.validator")


@dataclass
class ValidationResult:
    is_valid: bool
    status: str  # VALID, NEEDS_REVIEW, INVALID
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SchemeDataValidator:
    """
    Deterministic Validator for extracted scheme data prior to pending update creation.
    Enforces required identity attributes, URL syntax, and realistic statutory bounds.
    Does NOT invent domain rules.
    """

    URL_REGEX = re.compile(
        r"^https?://[a-zA-Z0-9\-\.]+(?:\.[a-zA-Z]{2,})+(?:/[^\s]*)?$"
    )

    @classmethod
    def validate(cls, candidate: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Mandatory Identity Fields
        name = candidate.get("scheme_name")
        if not name or not isinstance(name, str) or len(name.strip()) < 3:
            errors.append("Mandatory field 'scheme_name' is missing or has fewer than 3 characters.")

        ministry = candidate.get("ministry")
        if not ministry or not isinstance(ministry, str) or len(ministry.strip()) < 3:
            warnings.append("Field 'ministry' is missing or unverified.")

        # 2. Source & Official URL Validation
        source_url = candidate.get("official_source_url")
        if not source_url or not cls.URL_REGEX.match(source_url):
            errors.append(f"Official source URL '{source_url}' is invalid or missing.")

        app_url = candidate.get("application_url")
        if app_url and not cls.URL_REGEX.match(app_url):
            warnings.append(f"Application URL '{app_url}' does not conform to valid URL structure.")

        # 3. Age Limit Bounds
        age_min = candidate.get("age_min")
        if age_min is not None:
            if not isinstance(age_min, int) or age_min < 0 or age_min > 100:
                errors.append(f"Invalid age_min value '{age_min}'. Must be between 0 and 100.")

        age_max = candidate.get("age_max")
        if age_max is not None:
            if not isinstance(age_max, int) or age_max < 0 or age_max > 120:
                errors.append(f"Invalid age_max value '{age_max}'. Must be between 0 and 120.")

        if age_min is not None and age_max is not None:
            if age_min > age_max:
                errors.append(f"Inconsistent age limits: age_min ({age_min}) cannot exceed age_max ({age_max}).")

        # 4. Financial Limit Bounds
        max_loan = candidate.get("max_loan_amount")
        if max_loan is not None:
            if not isinstance(max_loan, (int, float)) or max_loan <= 0:
                errors.append(f"Invalid max_loan_amount '{max_loan}'. Must be a positive numeric value.")
            elif max_loan > 10_000_000_000:  # 1000 Crores
                errors.append(f"max_loan_amount '{max_loan}' exceeds plausible statutory cap (₹1,000 Cr).")

        min_loan = candidate.get("min_loan_amount")
        if min_loan is not None:
            if not isinstance(min_loan, (int, float)) or min_loan < 0:
                errors.append(f"Invalid min_loan_amount '{min_loan}'. Must be non-negative.")

        if min_loan is not None and max_loan is not None:
            if min_loan > max_loan:
                errors.append(f"Inconsistent loan limits: min_loan_amount ({min_loan}) exceeds max_loan_amount ({max_loan}).")

        # 5. Percentage Bounds
        subsidy = candidate.get("subsidy_percentage")
        if subsidy is not None:
            if not isinstance(subsidy, (int, float)) or subsidy < 0.0 or subsidy > 100.0:
                errors.append(f"Invalid subsidy_percentage '{subsidy}'. Must be between 0.0% and 100.0%.")

        interest = candidate.get("interest_rate_max")
        if interest is not None:
            if not isinstance(interest, (int, float)) or interest < 0.0 or interest > 100.0:
                errors.append(f"Invalid interest_rate_max '{interest}'. Must be between 0.0% and 100.0%.")

        # 6. Income Limit Bounds
        income = candidate.get("income_limit")
        if income is not None:
            if not isinstance(income, (int, float)) or income <= 0:
                errors.append(f"Invalid income_limit '{income}'. Must be a positive numeric amount.")

        # Determine Status
        if len(errors) > 0:
            status = "INVALID"
            is_valid = False
        elif len(warnings) > 0:
            status = "NEEDS_REVIEW"
            is_valid = True
        else:
            status = "VALID"
            is_valid = True

        return ValidationResult(
            is_valid=is_valid,
            status=status,
            errors=errors,
            warnings=warnings
        )
