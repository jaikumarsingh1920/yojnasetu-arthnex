import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.scheme import Scheme
from app.models.rule import SchemeRule
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.eligibility import (
    RuleEvaluationResult,
    SchemeEligibilityStatus,
    RuleEvaluationDetail,
    SchemeEligibilityResult,
    BatchEligibilityResponse
)
from app.engine.operators import evaluate_operator
from app.engine.taxonomy import TaxonomyMatcher


class DeterministicEligibilityEngine:
    """
    Core Deterministic Eligibility Engine for YojnaSetu.
    Enforces strict separation between Hard Eligibility Rules (Question A: "Can beneficiary qualify?")
    and Financial/Application Rules (Question B: "What terms apply?").
    Zero LLM/AI dependencies.
    """

    @staticmethod
    def resolve_field_value(field_name: str, profile: BeneficiaryProfileInput, required_value: Optional[str] = None) -> Optional[Any]:
        """
        Maps a rule field name to the corresponding field value on beneficiary profile.
        Returns None if field is missing/unknown on profile.
        Never converts unknown values into affirmative passes.
        """
        fn = field_name.strip().lower()

        if fn in ("annual_income", "income_limit", "income"):
            return profile.annual_income
        elif fn in ("age", "age_min", "age_max"):
            return profile.age
        elif fn in ("social_category", "category", "caste"):
            return profile.social_category
        elif fn == "sc_required":
            if profile.is_sc is not None:
                return profile.is_sc
            if profile.social_category:
                return profile.social_category.strip().upper() == "SC"
            return None
        elif fn in ("gender", "gender_requirement", "gender_condition"):
            return profile.gender
        elif fn == "state":
            return profile.state
        elif fn == "district":
            return profile.district
        elif fn == "applicant_type":
            return profile.applicant_type
        elif fn in ("entrepreneur_type", "enterprise_size_requirement", "enterprise_size"):
            return profile.entrepreneur_type or profile.applicant_type
        elif fn == "business_stage":
            return profile.business_stage
        elif fn in ("new_unit_required", "is_new_unit"):
            return profile.is_new_unit
        elif fn == "sector":
            return profile.sector
        elif fn in ("activity_type", "activity", "activity_supported"):
            return profile.activity_type
        elif fn in ("project_cost", "max_project_cost", "cost_limit"):
            return profile.project_cost
        elif fn in ("requested_loan_amount", "max_loan_amount", "loan_amount"):
            return profile.requested_loan_amount
        elif fn in ("collateral_required", "collateral_available"):
            return profile.collateral_available
        elif fn == "application_route":
            return profile.application_route
        elif fn in ("education", "education_level", "education_qualification", "minimum_education"):
            return profile.education_level
        elif fn in ("employment_status", "employment"):
            return profile.employment_status
        elif fn in ("pwd", "is_pwd", "disability", "disability_status", "divyangjan"):
            return profile.is_pwd
        elif fn in ("minority", "is_minority", "minority_status"):
            if profile.is_minority is not None:
                return profile.is_minority
            if profile.social_category:
                return profile.social_category.strip().upper() == "MINORITY"
            return None
        elif fn in ("artisan", "is_artisan", "craftsman", "artisan_status"):
            if profile.is_artisan is not None:
                return profile.is_artisan
            if profile.applicant_type:
                return profile.applicant_type.strip().upper() in ["ARTISAN", "CRAFTSMAN"]
            return None
        elif fn in ("farmer", "is_farmer", "kisan", "agriculture"):
            if profile.is_farmer is not None:
                return profile.is_farmer
            if profile.applicant_type:
                return profile.applicant_type.strip().upper() == "FARMER"
            return None
        elif fn in ("street_vendor", "is_street_vendor", "vendor", "svanidhi"):
            if profile.is_street_vendor is not None:
                return profile.is_street_vendor
            if profile.applicant_type:
                return profile.applicant_type.strip().upper() == "STREET_VENDOR"
            return None
        elif fn in ("safai_karamchari", "is_safai_karamchari", "sanitation_worker", "manual_scavenger"):
            return profile.is_safai_karamchari
        elif fn in ("target_group", "target_groups"):
            req_upper = (required_value or "").upper().strip()
            if "PWD" in req_upper or "DIVYANG" in req_upper:
                if profile.is_pwd is None:
                    return None
                return "PWD" if profile.is_pwd else "NON_PWD"
            elif "WOMEN" in req_upper or "FEMALE" in req_upper:
                if profile.gender is None or str(profile.gender).strip().upper() in ("UNKNOWN", "NONE", "NULL", ""):
                    return None
                return "WOMEN" if str(profile.gender).strip().upper() in ("FEMALE", "WOMAN", "WOMEN") else "NON_WOMEN"
            elif "SC" in req_upper and "SCHEDULED" in req_upper:
                if profile.is_sc is None and not profile.social_category:
                    return None
                is_sc = bool(profile.is_sc is True or (profile.social_category and profile.social_category.upper() in ("SC", "SCHEDULED CASTE", "SCHEDULED_CASTE")))
                return "SC" if is_sc else "NON_SC"
            elif "ST" in req_upper:
                user_st = getattr(profile, "is_st", None)
                if user_st is None and not profile.social_category:
                    return None
                is_st = bool(user_st is True or (profile.social_category and bool(re.search(r"\bST\b|SCHEDULED[_\s]+TRIBE|ADIVASI", profile.social_category, re.IGNORECASE))))
                return "ST" if is_st else "NON_ST"
            elif "OBC" in req_upper:
                if not profile.social_category:
                    return None
                is_obc = bool(re.search(r"\bOBC\b|(?:OTHER[_\s]+)?BACKWARD[_\s]+CLASS(?:ES)?", profile.social_category, re.IGNORECASE))
                return "OBC" if is_obc else "NON_OBC"

            # General target groups aggregation
            groups = []
            if profile.is_pwd is True:
                groups.append("PWD")
            if profile.is_sc is True or (profile.social_category and profile.social_category.upper() in ("SC", "SCHEDULED CASTE")):
                groups.append("SC")
            if getattr(profile, "is_st", None) is True or (profile.social_category and "ST" in profile.social_category.upper()):
                groups.append("ST")
            if profile.social_category and "OBC" in profile.social_category.upper():
                groups.append("OBC")
            if profile.gender and profile.gender.upper() in ("FEMALE", "WOMAN", "WOMEN"):
                groups.append("WOMEN")
            if profile.is_artisan is True or (profile.applicant_type and profile.applicant_type.upper() in ("ARTISAN", "CRAFTSMAN")):
                groups.append("ARTISAN")
            if profile.is_farmer is True or (profile.applicant_type and profile.applicant_type.upper() == "FARMER"):
                groups.append("FARMER")
            if profile.is_street_vendor is True or (profile.applicant_type and profile.applicant_type.upper() == "STREET_VENDOR"):
                groups.append("STREET_VENDOR")
            if profile.is_safai_karamchari is True:
                groups.append("SAFAI_KARAMCHARI")
            if profile.is_minority is True:
                groups.append("MINORITY")

            if not groups and profile.is_pwd is None and profile.is_sc is None and profile.social_category is None:
                return None
            return ", ".join(groups) if groups else "GENERAL"

        if hasattr(profile, fn):
            return getattr(profile, fn)

        return None

    @classmethod
    def evaluate_scheme(
        cls,
        scheme: Scheme,
        profile: BeneficiaryProfileInput,
        active_rules: Optional[List[SchemeRule]] = None
    ) -> SchemeEligibilityResult:
        """
        Evaluates a single scheme deterministically against a beneficiary profile.
        Separates Question A (Hard Eligibility) from Question B (Financial & Application Terms).
        """
        hard_passed: List[RuleEvaluationDetail] = []
        hard_failed: List[RuleEvaluationDetail] = []
        unknown_eligibility: List[RuleEvaluationDetail] = []

        financial_evals: List[RuleEvaluationDetail] = []
        application_evals: List[RuleEvaluationDetail] = []
        explanations: List[str] = []

        rules_to_eval = active_rules if active_rules is not None else scheme.rules

        # -------------------------------------------------------------
        # 1. Master Scheme Attribute Evaluation (Hard Eligibility Rules)
        # -------------------------------------------------------------

        # A. Age Bounds
        if scheme.age_min is not None:
            if profile.age is None:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-AGE-MIN",
                    field="age",
                    operator=">=",
                    required_value=scheme.age_min,
                    value_type="INT",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=None,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason=f"Missing applicant age; scheme requires minimum age of {scheme.age_min} years."
                ))
            elif profile.age < scheme.age_min:
                hard_failed.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-AGE-MIN",
                    field="age",
                    operator=">=",
                    required_value=scheme.age_min,
                    value_type="INT",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=profile.age,
                    result=RuleEvaluationResult.FAIL,
                    reason=f"Applicant age {profile.age} is below minimum requirement of {scheme.age_min} years."
                ))
            else:
                hard_passed.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-AGE-MIN",
                    field="age",
                    operator=">=",
                    required_value=scheme.age_min,
                    value_type="INT",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=profile.age,
                    result=RuleEvaluationResult.PASS,
                    reason=f"Applicant age {profile.age} satisfies minimum age {scheme.age_min}."
                ))

        if scheme.age_max is not None:
            if profile.age is None:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-AGE-MAX",
                    field="age",
                    operator="<=",
                    required_value=scheme.age_max,
                    value_type="INT",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=None,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason=f"Missing applicant age; scheme requires maximum age of {scheme.age_max} years."
                ))
            elif profile.age > scheme.age_max:
                hard_failed.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-AGE-MAX",
                    field="age",
                    operator="<=",
                    required_value=scheme.age_max,
                    value_type="INT",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=profile.age,
                    result=RuleEvaluationResult.FAIL,
                    reason=f"Applicant age {profile.age} exceeds maximum limit of {scheme.age_max} years."
                ))
            else:
                hard_passed.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-AGE-MAX",
                    field="age",
                    operator="<=",
                    required_value=scheme.age_max,
                    value_type="INT",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=profile.age,
                    result=RuleEvaluationResult.PASS,
                    reason=f"Applicant age {profile.age} satisfies maximum age {scheme.age_max}."
                ))

        # B. Income Ceiling
        if scheme.income_limit is not None:
            if profile.annual_income is None:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-INCOME",
                    field="annual_income",
                    operator="<=",
                    required_value=float(scheme.income_limit),
                    value_type="INR_PER_YEAR",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=None,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason=f"Missing annual income; scheme requires family income <= ₹{scheme.income_limit:,.2f}."
                ))
            elif profile.annual_income > scheme.income_limit:
                hard_failed.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-INCOME",
                    field="annual_income",
                    operator="<=",
                    required_value=float(scheme.income_limit),
                    value_type="INR_PER_YEAR",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=profile.annual_income,
                    result=RuleEvaluationResult.FAIL,
                    reason=f"Annual family income ₹{profile.annual_income:,.2f} exceeds limit of ₹{scheme.income_limit:,.2f}."
                ))
            else:
                hard_passed.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-INCOME",
                    field="annual_income",
                    operator="<=",
                    required_value=float(scheme.income_limit),
                    value_type="INR_PER_YEAR",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=profile.annual_income,
                    result=RuleEvaluationResult.PASS,
                    reason=f"Annual family income ₹{profile.annual_income:,.2f} satisfies limit of ₹{scheme.income_limit:,.2f}."
                ))

        # C. Geography Bounds (State Coverage / Restriction)
        geo_raw = scheme.state_coverage
        # Discard boolean indicators from state_restriction if erroneously passed
        if not geo_raw and scheme.state_restriction and str(scheme.state_restriction).strip().upper() not in ("YES", "NO", "TRUE", "FALSE"):
            geo_raw = scheme.state_restriction

        # Check if national/central
        is_central_ministry = bool(
            scheme.ministry and any(scheme.ministry.strip().lower().startswith(p) for p in ["ministry of", "department of"])
        ) or str(getattr(scheme, "level", "") or "").upper() == "CENTRAL_SECTOR"

        geo_clean = str(geo_raw or "").strip().upper()
        geo_norm = str(geo_raw or "").replace("_", " ").strip().lower()

        is_national = (
            any(k in geo_norm for k in ["all india", "all states", "national", "pan india", "any state", "entire country", "all ut"])
            or geo_clean in ("INDIA", "CENTRAL", "NATIONAL", "ALL_INDIA", "ALL_STATES", "PAN_INDIA", "ALL STATES AND UNION TERRITORIES OF INDIA")
            or (not geo_raw and is_central_ministry and str(scheme.state_restriction or "").strip().upper() != "YES")
        )

        user_state_raw = profile.state
        user_state_is_missing = (user_state_raw is None or str(user_state_raw).strip().upper() in ("UNKNOWN", "NONE", "NULL", "", "NOT_SPECIFIED"))

        if is_national:
            hard_passed.append(RuleEvaluationDetail(
                rule_id=f"MASTER-{scheme.scheme_id}-STATE",
                field="state",
                operator="IN",
                required_value="ALL_INDIA",
                value_type="STRING",
                rule_type="ELIGIBILITY",
                priority="HIGH",
                condition_group="BASE",
                actual_value=profile.state or "ANY",
                result=RuleEvaluationResult.PASS,
                reason="Scheme is applicable nationwide across all States and Union Territories."
            ))
        elif geo_raw:
            # Scheme has explicit state/UT coverage
            allowed_raw_states = [s.strip() for s in geo_raw.replace("/", ",").replace(";", ",").split(",") if s.strip()]
            allowed_norm_states = set()
            for s in allowed_raw_states:
                n_geo = TaxonomyMatcher.normalize_geography(s)
                if n_geo != "UNKNOWN_GEOGRAPHY":
                    allowed_norm_states.update(TaxonomyMatcher.expands_to_states(n_geo))

            # Malformed/ambiguous coverage check: if none of the parsed items represent a recognized state, UT, or region
            if not allowed_norm_states:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-STATE",
                    field="state",
                    operator="IN",
                    required_value=geo_raw,
                    value_type="STRING",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=profile.state,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason=f"Scheme geographical coverage '{geo_raw}' is ambiguous or unverified in authoritative records; requires verification."
                ))
            elif user_state_is_missing:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-STATE",
                    field="state",
                    operator="IN",
                    required_value=geo_raw,
                    value_type="STRING",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=None,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason=f"Scheme is geographically restricted to {geo_raw}; applicant state is missing from profile."
                ))
            else:
                user_norm_state = TaxonomyMatcher.normalize_geography(user_state_raw)
                if user_norm_state in allowed_norm_states:
                    hard_passed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-STATE",
                        field="state",
                        operator="IN",
                        required_value=geo_raw,
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value=profile.state,
                        result=RuleEvaluationResult.PASS,
                        reason=f"Applicant state '{profile.state}' matches scheme state coverage ({geo_raw})."
                    ))
                else:
                    hard_failed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-STATE",
                        field="state",
                        operator="IN",
                        required_value=geo_raw,
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value=profile.state,
                        result=RuleEvaluationResult.FAIL,
                        reason=f"Scheme is restricted to {geo_raw}; applicant resides in {profile.state}."
                    ))
        else:
            # Scheme geography is genuinely unknown / unspecified and not central
            unknown_eligibility.append(RuleEvaluationDetail(
                rule_id=f"MASTER-{scheme.scheme_id}-STATE",
                field="state",
                operator="IN",
                required_value="SPECIFIED_STATE",
                value_type="STRING",
                rule_type="ELIGIBILITY",
                priority="MEDIUM",
                condition_group="BASE",
                actual_value=profile.state,
                result=RuleEvaluationResult.UNKNOWN,
                reason="Scheme geographical coverage is unspecified in authoritative records; state eligibility requires verification."
            ))

        # D. Social Category / Caste / Mandatory SC Requirement
        sc_req_val = str(scheme.sc_required).strip().upper() if scheme.sc_required is not None else None
        if sc_req_val in ("TRUE", "1", "YES", "SC_ONLY", "SC"):
            caste_unknown = False
            if profile.is_sc is None:
                if profile.social_category is None or str(profile.social_category).strip().upper() in ("UNKNOWN", "NONE", "NULL", "", "NOT_SPECIFIED"):
                    caste_unknown = True

            if caste_unknown:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-SC-REQUIRED",
                    field="social_category",
                    operator="==",
                    required_value="SC",
                    value_type="STRING",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=None,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason="Scheme strictly mandates Scheduled Caste (SC) category; category was not specified on profile."
                ))
            else:
                user_is_sc = bool(profile.is_sc is True or (profile.social_category and str(profile.social_category).strip().upper() in ("SC", "SCHEDULED CASTE", "SCHEDULED_CASTE")))
                if not user_is_sc:
                    hard_failed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-SC-REQUIRED",
                        field="social_category",
                        operator="==",
                        required_value="SC",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value=profile.social_category,
                        result=RuleEvaluationResult.FAIL,
                        reason=f"Scheme mandates Scheduled Caste (SC) category; applicant category is '{profile.social_category or 'NON-SC'}'."
                    ))
                else:
                    hard_passed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-SC-REQUIRED",
                        field="social_category",
                        operator="==",
                        required_value="SC",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value="SC",
                        result=RuleEvaluationResult.PASS,
                        reason="Applicant satisfies mandatory Scheduled Caste (SC) category requirement."
                    ))

        # D2. Mandatory ST (Scheduled Tribe) Requirement
        is_st_mandatory = bool(
            (scheme.target_groups and scheme.target_groups.strip().upper() in ("ST", "ST, WOMEN", "ST, STUDENTS, YOUTH", "ST, SHG"))
            or (scheme.scheme_name and "NSTFDC" in scheme.scheme_name.upper())
            or (
                scheme.social_category
                and bool(re.search(r"\bST\b|SCHEDULED\s+TRIBE|ADIVASI", scheme.social_category, re.IGNORECASE))
                and not bool(re.search(r"\bSC\b|SCHEDULED\s+CASTE|\bALL\b|\bGENERAL\b|\bOBC\b", scheme.social_category, re.IGNORECASE))
            )
        )
        if is_st_mandatory:
            caste_unknown = False
            user_is_st_flag = getattr(profile, "is_st", None)
            if user_is_st_flag is None:
                if profile.social_category is None or str(profile.social_category).strip().upper() in ("UNKNOWN", "NONE", "NULL", "", "NOT_SPECIFIED"):
                    caste_unknown = True

            if caste_unknown:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-ST-REQUIRED",
                    field="social_category",
                    operator="==",
                    required_value="ST",
                    value_type="STRING",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=None,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason="Scheme strictly mandates Scheduled Tribe (ST) category; category was not specified on profile."
                ))
            else:
                user_is_st = bool(user_is_st_flag is True or (profile.social_category and bool(re.search(r"\bST\b|SCHEDULED[_\s]+TRIBE|ADIVASI", profile.social_category, re.IGNORECASE))))
                if not user_is_st:
                    hard_failed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-ST-REQUIRED",
                        field="social_category",
                        operator="==",
                        required_value="ST",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value=profile.social_category,
                        result=RuleEvaluationResult.FAIL,
                        reason=f"Scheme mandates Scheduled Tribe (ST) category; applicant category is '{profile.social_category or 'NON-ST'}'."
                    ))
                else:
                    hard_passed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-ST-REQUIRED",
                        field="social_category",
                        operator="==",
                        required_value="ST",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value="ST",
                        result=RuleEvaluationResult.PASS,
                        reason="Applicant satisfies mandatory Scheduled Tribe (ST) category requirement."
                    ))

        # D3. Mandatory OBC (Other Backward Classes) Requirement
        is_obc_mandatory = bool(
            (scheme.target_groups and scheme.target_groups.strip().upper() in ("OBC", "OBC, WOMEN"))
            or (scheme.scheme_name and "NBCFDC" in scheme.scheme_name.upper() and not (scheme.social_category and "ALL" in scheme.social_category.upper()))
            or (
                scheme.social_category
                and bool(re.search(r"\bOBC\b|(?:OTHER[_\s]+)?BACKWARD[_\s]+CLASS(?:ES)?", scheme.social_category, re.IGNORECASE))
                and not bool(re.search(r"\bSC\b|\bST\b|SCHEDULED|\bALL\b|\bGENERAL\b", scheme.social_category, re.IGNORECASE))
            )
        )
        if is_obc_mandatory:
            caste_unknown = False
            if profile.social_category is None or str(profile.social_category).strip().upper() in ("UNKNOWN", "NONE", "NULL", "", "NOT_SPECIFIED"):
                caste_unknown = True

            if caste_unknown:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-OBC-REQUIRED",
                    field="social_category",
                    operator="==",
                    required_value="OBC",
                    value_type="STRING",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=None,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason="Scheme strictly mandates Other Backward Classes (OBC) category; category was not specified on profile."
                ))
            else:
                user_is_obc = bool(profile.social_category and bool(re.search(r"\bOBC\b|(?:OTHER[_\s]+)?BACKWARD[_\s]+CLASS(?:ES)?", profile.social_category, re.IGNORECASE)))
                if not user_is_obc:
                    hard_failed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-OBC-REQUIRED",
                        field="social_category",
                        operator="==",
                        required_value="OBC",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value=profile.social_category,
                        result=RuleEvaluationResult.FAIL,
                        reason=f"Scheme mandates Other Backward Classes (OBC) category; applicant category is '{profile.social_category or 'NON-OBC'}'."
                    ))
                else:
                    hard_passed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-OBC-REQUIRED",
                        field="social_category",
                        operator="==",
                        required_value="OBC",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value="OBC",
                        result=RuleEvaluationResult.PASS,
                        reason="Applicant satisfies mandatory Other Backward Classes (OBC) category requirement."
                    ))

        # E. Gender Exclusivity (Women Only Schemes)
        g_cond = (scheme.gender_condition or scheme.gender_requirement or "").strip().upper()
        if any(w in g_cond for w in ["FEMALE_ONLY", "WOMEN_ONLY", "WOMEN EXCLUSIVE", "FEMALE EXCLUSIVE"]):
            gender_unknown = (profile.gender is None or str(profile.gender).strip().upper() in ("UNKNOWN", "NONE", "NULL", "", "NOT_SPECIFIED"))
            if gender_unknown:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-GENDER",
                    field="gender",
                    operator="==",
                    required_value="FEMALE",
                    value_type="STRING",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=None,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason="Scheme is exclusively for women applicants; gender was not specified on profile."
                ))
            else:
                user_gender = str(profile.gender).strip().upper()
                if user_gender not in ("FEMALE", "WOMAN", "WOMEN"):
                    hard_failed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-GENDER",
                        field="gender",
                        operator="==",
                        required_value="FEMALE",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value=profile.gender,
                        result=RuleEvaluationResult.FAIL,
                        reason=f"Scheme is exclusively for women applicants; applicant gender is {profile.gender}."
                    ))
                else:
                    hard_passed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-GENDER",
                        field="gender",
                        operator="==",
                        required_value="FEMALE",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value=profile.gender,
                        result=RuleEvaluationResult.PASS,
                        reason="Applicant satisfies scheme women-only gender requirement."
                    ))
        elif any(w in g_cond for w in ["MALE_ONLY", "MEN_ONLY"]):
            gender_unknown = (profile.gender is None or str(profile.gender).strip().upper() in ("UNKNOWN", "NONE", "NULL", "", "NOT_SPECIFIED"))
            if gender_unknown:
                unknown_eligibility.append(RuleEvaluationDetail(
                    rule_id=f"MASTER-{scheme.scheme_id}-GENDER",
                    field="gender",
                    operator="==",
                    required_value="MALE",
                    value_type="STRING",
                    rule_type="ELIGIBILITY",
                    priority="HIGH",
                    condition_group="BASE",
                    actual_value=None,
                    result=RuleEvaluationResult.UNKNOWN,
                    reason="Scheme is exclusively for male applicants; gender was not specified on profile."
                ))
            else:
                user_gender = str(profile.gender).strip().upper()
                if user_gender not in ("MALE", "MAN", "MEN"):
                    hard_failed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-GENDER",
                        field="gender",
                        operator="==",
                        required_value="MALE",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value=profile.gender,
                        result=RuleEvaluationResult.FAIL,
                        reason=f"Scheme is exclusively for male applicants; applicant gender is {profile.gender}."
                    ))
                else:
                    hard_passed.append(RuleEvaluationDetail(
                        rule_id=f"MASTER-{scheme.scheme_id}-GENDER",
                        field="gender",
                        operator="==",
                        required_value="MALE",
                        value_type="STRING",
                        rule_type="ELIGIBILITY",
                        priority="HIGH",
                        condition_group="BASE",
                        actual_value=profile.gender,
                        result=RuleEvaluationResult.PASS,
                        reason="Applicant satisfies scheme male-only gender requirement."
                    ))

        # -------------------------------------------------------------
        # 2. Database SchemeRule Evaluation
        # -------------------------------------------------------------
        conditional_eligibility: List[RuleEvaluationDetail] = []
        for rule in rules_to_eval:
            if not rule.active:
                continue

            act_val = cls.resolve_field_value(rule.field, profile, rule.value)
            res_type, reason = evaluate_operator(rule.operator, rule.value, rule.value_type, act_val)

            detail = RuleEvaluationDetail(
                rule_id=rule.rule_id,
                field=rule.field,
                operator=rule.operator,
                required_value=rule.value,
                value_type=rule.value_type,
                rule_type=rule.rule_type,
                priority=rule.priority,
                condition_group=rule.condition_group,
                actual_value=act_val,
                result=res_type,
                reason=reason
            )

            rtype = rule.rule_type.upper()

            if rtype in ("ELIGIBILITY", "HARD", "STATUTORY"):
                if res_type == RuleEvaluationResult.PASS:
                    hard_passed.append(detail)
                elif res_type == RuleEvaluationResult.FAIL:
                    hard_failed.append(detail)
                elif res_type == RuleEvaluationResult.UNKNOWN:
                    unknown_eligibility.append(detail)
                elif res_type == RuleEvaluationResult.CONDITIONAL:
                    conditional_eligibility.append(detail)
            elif rtype == "FINANCIAL":
                financial_evals.append(detail)
            elif rtype == "APPLICATION":
                application_evals.append(detail)

        # -------------------------------------------------------------
        # 3. Question A: Hard Eligibility Status Determination
        # Explicit Precedence: NOT_APPLICABLE > INELIGIBLE > INSUFFICIENT_INFORMATION > CONDITIONAL > ELIGIBLE
        # -------------------------------------------------------------
        passed_reasons = [r.reason for r in hard_passed]
        failed_reasons = [r.reason for r in hard_failed]
        unknown_reasons = [r.reason for r in unknown_eligibility]
        conditional_reasons = [r.reason for r in conditional_eligibility]

        # Check scheme status
        if scheme.scheme_status and scheme.scheme_status.strip().upper() in ("INACTIVE", "OBSOLETE", "DISCONTINUED", "CLOSED"):
            overall_status = SchemeEligibilityStatus.NOT_APPLICABLE
            explanations.append(f"Not Applicable: Scheme is currently {scheme.scheme_status}.")
        elif len(hard_failed) > 0:
            overall_status = SchemeEligibilityStatus.INELIGIBLE
            explanations.append(f"Ineligible: Failed {len(hard_failed)} mandatory hard eligibility rule(s).")
            for f_rule in hard_failed:
                explanations.append(f"• {f_rule.field}: {f_rule.reason}")
        elif len(unknown_eligibility) > 0:
            overall_status = SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
            explanations.append(f"Insufficient Information: Cannot verify {len(unknown_eligibility)} mandatory eligibility field(s).")
            for u_rule in unknown_eligibility:
                explanations.append(f"• {u_rule.field}: {u_rule.reason}")
        elif len(conditional_eligibility) > 0:
            overall_status = SchemeEligibilityStatus.CONDITIONAL
            explanations.append(f"Conditional: Meets baseline requirements subject to {len(conditional_eligibility)} statutory condition(s).")
            for c_rule in conditional_eligibility:
                explanations.append(f"• {c_rule.field}: {c_rule.reason}")
        else:
            overall_status = SchemeEligibilityStatus.ELIGIBLE
            explanations.append(f"Eligible: All {len(hard_passed)} mandatory eligibility rules satisfied.")

        verif_status = "VERIFIED"
        if getattr(scheme, "verification_status", None):
            verif_status = scheme.verification_status
        elif getattr(scheme, "verifications", None) and len(scheme.verifications) > 0:
            verif_status = scheme.verifications[0].verification_status

        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.scheme_name,
            verification_status=verif_status,
            status=overall_status,
            matched_rules=passed_reasons,
            failed_rules=failed_reasons,
            missing_information=unknown_reasons,
            hard_rules_passed=hard_passed,
            hard_rules_failed=hard_failed,
            unknown_eligibility_rules=unknown_eligibility,
            financial_rules=financial_evals,
            application_rules=application_evals,
            explanations=explanations
        )

    @classmethod
    def evaluate_all_schemes(
        cls,
        db: Session,
        profile: BeneficiaryProfileInput
    ) -> BatchEligibilityResponse:
        """
        Evaluates all 56 verified schemes in the database against beneficiary profile.
        Returns a batch evaluation response.
        """
        schemes = db.query(Scheme).all()
        results: List[SchemeEligibilityResult] = []

        eligible_cnt = 0
        ineligible_cnt = 0
        insufficient_cnt = 0

        for scheme in schemes:
            res = cls.evaluate_scheme(scheme, profile)
            results.append(res)

            if res.status == SchemeEligibilityStatus.ELIGIBLE:
                eligible_cnt += 1
            elif res.status == SchemeEligibilityStatus.INELIGIBLE:
                ineligible_cnt += 1
            elif res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION:
                insufficient_cnt += 1

        return BatchEligibilityResponse(
            total_evaluated=len(schemes),
            eligible_count=eligible_cnt,
            ineligible_count=ineligible_cnt,
            insufficient_info_count=insufficient_cnt,
            results=results
        )
