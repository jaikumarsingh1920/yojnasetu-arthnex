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


class DeterministicEligibilityEngine:
    """
    Core Deterministic Eligibility Engine for YojnaSetu.
    Enforces strict separation between Hard Eligibility Rules (Question A: "Can beneficiary qualify?")
    and Financial/Application Rules (Question B: "What terms apply?").
    Zero LLM/AI dependencies.
    """

    @staticmethod
    def resolve_field_value(field_name: str, profile: BeneficiaryProfileInput) -> Optional[Any]:
        """
        Maps a rule field name to the corresponding field value on beneficiary profile.
        Returns None if field is missing/unknown on profile.
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
        elif fn == "entrepreneur_type":
            return profile.entrepreneur_type
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

        # -------------------------------------------------------------
        # 2. Database SchemeRule Evaluation
        # -------------------------------------------------------------
        for rule in rules_to_eval:
            if not rule.active:
                continue

            act_val = cls.resolve_field_value(rule.field, profile)
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

            if rtype in ("ELIGIBILITY", "HARD"):
                if res_type == RuleEvaluationResult.PASS:
                    hard_passed.append(detail)
                elif res_type == RuleEvaluationResult.FAIL:
                    hard_failed.append(detail)
                elif res_type == RuleEvaluationResult.UNKNOWN:
                    unknown_eligibility.append(detail)
            elif rtype == "FINANCIAL":
                financial_evals.append(detail)
            elif rtype == "APPLICATION":
                application_evals.append(detail)

        # -------------------------------------------------------------
        # 3. Question A: Hard Eligibility Status Determination
        # -------------------------------------------------------------
        passed_reasons = [r.reason for r in hard_passed]
        failed_reasons = [r.reason for r in hard_failed]
        unknown_reasons = [r.reason for r in unknown_eligibility]

        if len(hard_failed) > 0:
            overall_status = SchemeEligibilityStatus.INELIGIBLE
            explanations.append(f"Ineligible: Failed {len(hard_failed)} mandatory hard eligibility rule(s).")
            for f_rule in hard_failed:
                explanations.append(f"• {f_rule.field}: {f_rule.reason}")
        elif len(unknown_eligibility) > 0:
            overall_status = SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
            explanations.append(f"Insufficient Information: Cannot verify {len(unknown_eligibility)} mandatory eligibility field(s).")
            for u_rule in unknown_eligibility:
                explanations.append(f"• {u_rule.field}: {u_rule.reason}")
        else:
            overall_status = SchemeEligibilityStatus.ELIGIBLE
            explanations.append(f"Eligible: All {len(hard_passed)} mandatory eligibility rules satisfied.")

        return SchemeEligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.scheme_name,
            verification_status=scheme.verifications[0].verification_status if scheme.verifications else "VERIFIED",
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
