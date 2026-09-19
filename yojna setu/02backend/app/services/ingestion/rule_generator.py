import uuid
import logging
from typing import Dict, Any, List, Optional
from app.models.rule import SchemeRule

logger = logging.getLogger("yojnasetu.ingestion.rule_generator")


class SchemeRuleGenerator:
    """
    Deterministic Statutory Rule Generator.
    Converts extracted and verified candidate eligibility criteria into canonical SchemeRule records.
    Never invents conditions; attaches exact source document citations.
    """

    @classmethod
    def generate_rules_for_scheme(
        cls,
        scheme_id: str,
        data: Dict[str, Any],
        source_doc: Optional[str] = None,
        source_page: Optional[str] = None,
        source_sec: Optional[str] = None
    ) -> List[SchemeRule]:
        rules: List[SchemeRule] = []
        doc = source_doc or data.get("source_document") or "Official Scheme Guidelines"
        page = source_page or data.get("source_page") or "Guidelines Document"
        sec = source_sec or data.get("source_section") or "Eligibility Criteria"

        # 1. Minimum Age Rule
        age_min = data.get("age_min")
        if age_min is not None and isinstance(age_min, (int, float)) and age_min > 0:
            rules.append(SchemeRule(
                rule_id=f"RULE-{uuid.uuid4().hex[:10]}",
                scheme_id=scheme_id,
                parent_product_id="NOT_APPLICABLE",
                field="age",
                operator=">=",
                value=str(int(age_min)),
                value_type="INT",
                rule_type="ELIGIBILITY",
                priority="HIGH",
                condition_group="BASE",
                error_message=f"Applicant must be at least {int(age_min)} years of age.",
                source_document=doc,
                source_page=page,
                source_section=sec,
                active=True
            ))

        # 2. Maximum Age Rule
        age_max = data.get("age_max")
        if age_max is not None and isinstance(age_max, (int, float)) and age_max > 0:
            rules.append(SchemeRule(
                rule_id=f"RULE-{uuid.uuid4().hex[:10]}",
                scheme_id=scheme_id,
                parent_product_id="NOT_APPLICABLE",
                field="age",
                operator="<=",
                value=str(int(age_max)),
                value_type="INT",
                rule_type="ELIGIBILITY",
                priority="HIGH",
                condition_group="BASE",
                error_message=f"Applicant age must not exceed {int(age_max)} years.",
                source_document=doc,
                source_page=page,
                source_section=sec,
                active=True
            ))

        # 3. Income Ceiling Rule
        income = data.get("income_limit")
        if income is not None and isinstance(income, (int, float)) and income > 0:
            rules.append(SchemeRule(
                rule_id=f"RULE-{uuid.uuid4().hex[:10]}",
                scheme_id=scheme_id,
                parent_product_id="NOT_APPLICABLE",
                field="annual_income",
                operator="<=",
                value=str(float(income)),
                value_type="FLOAT",
                rule_type="ELIGIBILITY",
                priority="HIGH",
                condition_group="BASE",
                error_message=f"Annual family income must not exceed ₹{float(income):,.2f}.",
                source_document=doc,
                source_page=page,
                source_section=sec,
                active=True
            ))

        # 4. Social Category / Caste Requirement
        sc_req = data.get("sc_required") or data.get("social_category")
        if sc_req and str(sc_req).upper() not in ["NONE", "ANY", "ALL", "NOT_APPLICABLE", "UNKNOWN"]:
            rules.append(SchemeRule(
                rule_id=f"RULE-{uuid.uuid4().hex[:10]}",
                scheme_id=scheme_id,
                parent_product_id="NOT_APPLICABLE",
                field="social_category",
                operator="IN",
                value=str(sc_req).strip(),
                value_type="STRING",
                rule_type="ELIGIBILITY",
                priority="HIGH",
                condition_group="BASE",
                error_message=f"Applicant must belong to eligible social category ({sc_req}).",
                source_document=doc,
                source_page=page,
                source_section=sec,
                active=True
            ))

        # 5. Gender Requirement
        gender = data.get("gender_requirement") or data.get("gender_condition")
        if gender and str(gender).upper() in ["FEMALE", "WOMEN"]:
            rules.append(SchemeRule(
                rule_id=f"RULE-{uuid.uuid4().hex[:10]}",
                scheme_id=scheme_id,
                parent_product_id="NOT_APPLICABLE",
                field="gender",
                operator="=",
                value="FEMALE",
                value_type="STRING",
                rule_type="ELIGIBILITY",
                priority="HIGH",
                condition_group="BASE",
                error_message="Scheme is exclusively available for female applicants / women entrepreneurs.",
                source_document=doc,
                source_page=page,
                source_section=sec,
                active=True
            ))

        # 6. New Unit Requirement
        new_unit = data.get("new_unit_required")
        if new_unit and str(new_unit).upper() in ["YES", "TRUE", "REQUIRED"]:
            rules.append(SchemeRule(
                rule_id=f"RULE-{uuid.uuid4().hex[:10]}",
                scheme_id=scheme_id,
                parent_product_id="NOT_APPLICABLE",
                field="new_unit_required",
                operator="=",
                value="TRUE",
                value_type="BOOLEAN",
                rule_type="ELIGIBILITY",
                priority="HIGH",
                condition_group="BASE",
                error_message="Financing is restricted to newly established enterprise units (greenfield projects).",
                source_document=doc,
                source_page=page,
                source_section=sec,
                active=True
            ))

        logger.info(f"Generated {len(rules)} statutory SchemeRule records for scheme {scheme_id}")
        return rules
