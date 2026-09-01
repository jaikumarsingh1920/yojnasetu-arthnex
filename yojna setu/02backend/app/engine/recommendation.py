"""
Deterministic Scheme Recommendation Engine for YojnaSetu (TASK-007).

Pipeline:
1. Beneficiary Profile Input
2. Evaluate all 56 VERIFIED schemes via DeterministicEligibilityEngine (TASK-003)
3. Hard Eligibility Gate (keep ELIGIBLE candidates; exclude INELIGIBLE)
4. Soft-Fit Scoring (0-100 score across 7 transparent dimensions)
5. Deterministic Ranking (score DESC, scheme_id ASC)
6. Top-K Selection (slice top_k recommendations)
7. Explainable Recommendation Reasons & Match Breakdown

Zero LLM/AI, zero random numbers, zero hardcoded scoring shortcuts.
"""

from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.scheme import Scheme
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.eligibility import (
    SchemeEligibilityStatus,
    SchemeEligibilityResult,
)
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
    ScoreDimensionBreakdown,
    ScoreDimensionResult,
)
from app.engine.eligibility import DeterministicEligibilityEngine
from app.engine.taxonomy import TaxonomyMatcher
from app.engine.normalization import SchemeNormalizedProfileBuilder

# Centralized, transparent scoring weights model (Sum = 100.0)
SCORING_WEIGHTS = {
    "sector_match": 20.0,
    "applicant_type_match": 15.0,
    "target_group_match": 15.0,
    "business_stage_match": 15.0,
    "activity_match": 10.0,
    "geography_match": 10.0,
    "financial_fit": 15.0,
}

SENTINEL_STRINGS = {"UNKNOWN", "NOT_APPLICABLE", "CONDITIONAL", "NONE", ""}


def _is_sentinel(val: Optional[str]) -> bool:
    if val is None:
        return True
    return str(val).strip().upper() in SENTINEL_STRINGS


class DeterministicRecommendationEngine:
    """
    Core Deterministic Recommendation Engine.
    Combines hard eligibility gating with soft-fit multidimensional scoring.
    """

    @classmethod
    def evaluate_soft_fit(
        cls,
        scheme: Scheme,
        profile: BeneficiaryProfileInput,
        eligibility: SchemeEligibilityResult
    ) -> Tuple[float, List[str], List[str], List[str], List[str], List[ScoreDimensionBreakdown]]:
        """
        Evaluates soft-fit score for an eligible scheme candidate.
        Returns: (normalized_score, matched_factors, unmatched_factors, not_evaluated_factors, recommendation_reasons, score_breakdown)
        """
        breakdown: List[ScoreDimensionBreakdown] = []
        matched_factors: List[str] = []
        unmatched_factors: List[str] = []
        not_evaluated_factors: List[str] = []
        recommendation_reasons: List[str] = []

        # Generate Rich Normalized Matching Profile
        norm_profile = SchemeNormalizedProfileBuilder.build_profile(scheme)

        # ── 1. Sector Match (Max 20.0) ──
        w_sector = SCORING_WEIGHTS["sector_match"]
        if profile.sector is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="sector_match", max_weight=w_sector, score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Beneficiary sector not specified on profile."
            ))
            not_evaluated_factors.append("sector_match")
        else:
            status, score_factor, explanation = TaxonomyMatcher.match_sector_or_activity(
                user_input=profile.sector,
                scheme_sectors=norm_profile.normalized_sectors,
                scheme_activities=norm_profile.normalized_activities,
                scheme_aliases=norm_profile.normalized_activity_aliases
            )
            score = round(w_sector * score_factor, 1)

            if status == "MATCH":
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="sector_match", max_weight=w_sector, score=score,
                    result=ScoreDimensionResult.MATCH,
                    reason=explanation
                ))
                matched_factors.append("sector_match")
                recommendation_reasons.append(explanation)
            elif status == "PARTIAL_MATCH":
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="sector_match", max_weight=w_sector, score=score,
                    result=ScoreDimensionResult.PARTIAL_MATCH,
                    reason=explanation
                ))
                matched_factors.append("sector_match (PARTIAL)")
                recommendation_reasons.append(explanation)
            else:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="sector_match", max_weight=w_sector, score=0.0,
                    result=ScoreDimensionResult.NO_MATCH,
                    reason=explanation
                ))
                unmatched_factors.append("sector_match")

        # ── 2. Applicant Type Match (Max 15.0) ──
        w_app = SCORING_WEIGHTS["applicant_type_match"]
        if profile.applicant_type is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="applicant_type_match", max_weight=w_app, score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Applicant type not specified on beneficiary profile."
            ))
            not_evaluated_factors.append("applicant_type_match")
        else:
            prof_app = TaxonomyMatcher.normalize_string(profile.applicant_type)
            norm_apps = [TaxonomyMatcher.normalize_string(a) for a in norm_profile.normalized_applicant_types]

            if prof_app in norm_apps or any(prof_app in a for a in norm_apps) or "INDIVIDUAL" in norm_apps:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="applicant_type_match", max_weight=w_app, score=w_app,
                    result=ScoreDimensionResult.MATCH,
                    reason=f"Applicant type '{profile.applicant_type}' matches scheme candidate criteria ({', '.join(norm_profile.normalized_applicant_types[:3])})."
                ))
                matched_factors.append("applicant_type_match")
                recommendation_reasons.append(f"Tailored for '{profile.applicant_type}' applicants.")
            else:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="applicant_type_match", max_weight=w_app, score=0.0,
                    result=ScoreDimensionResult.NO_MATCH,
                    reason=f"Applicant type '{profile.applicant_type}' not in scheme allowed list."
                ))
                unmatched_factors.append("applicant_type_match")

        # ── 3. Target Group / Marginalized Group Match (Max 15.0) ──
        w_target = SCORING_WEIGHTS["target_group_match"]
        is_sc = profile.is_sc or (profile.social_category and profile.social_category.strip().upper() == "SC")
        
        status_tg, factor_tg, expl_tg = TaxonomyMatcher.match_target_group(
            user_category=profile.social_category,
            user_is_sc=is_sc,
            scheme_target_groups=norm_profile.normalized_target_groups
        )
        score_tg = round(w_target * factor_tg, 1)

        if status_tg == "MATCH":
            breakdown.append(ScoreDimensionBreakdown(
                dimension="target_group_match", max_weight=w_target, score=score_tg,
                result=ScoreDimensionResult.MATCH,
                reason=expl_tg
            ))
            matched_factors.append("target_group_match")
            recommendation_reasons.append(expl_tg)
        elif status_tg == "PARTIAL_MATCH":
            breakdown.append(ScoreDimensionBreakdown(
                dimension="target_group_match", max_weight=w_target, score=score_tg,
                result=ScoreDimensionResult.PARTIAL_MATCH,
                reason=expl_tg
            ))
            matched_factors.append("target_group_match (PARTIAL)")
            recommendation_reasons.append(expl_tg)
        elif not is_sc and profile.social_category is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="target_group_match", max_weight=w_target, score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Social category / target group attributes not specified on beneficiary profile."
            ))
            not_evaluated_factors.append("target_group_match")
        else:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="target_group_match", max_weight=w_target, score=0.0,
                result=ScoreDimensionResult.NO_MATCH,
                reason=expl_tg
            ))
            unmatched_factors.append("target_group_match")

        # ── 4. Business Stage & Unit Match (Max 15.0) ──
        w_stage = SCORING_WEIGHTS["business_stage_match"]
        if profile.business_stage is None and profile.is_new_unit is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="business_stage_match", max_weight=w_stage, score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Business stage and unit type not specified on beneficiary profile."
            ))
            not_evaluated_factors.append("business_stage_match")
        else:
            stage_match = False
            norm_stages = norm_profile.normalized_business_stages
            if profile.is_new_unit is True and ("NEW" in norm_stages or "NEW_UNIT" in norm_stages or "ANY_STAGE" in norm_stages):
                stage_match = True
            elif profile.is_new_unit is False and ("EXISTING" in norm_stages or "EXPANSION" in norm_stages or "ANY_STAGE" in norm_stages):
                stage_match = True
            elif profile.business_stage:
                prof_stg = TaxonomyMatcher.normalize_string(profile.business_stage)
                if prof_stg in norm_stages or "ANY_STAGE" in norm_stages:
                    stage_match = True

            if stage_match:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="business_stage_match", max_weight=w_stage, score=w_stage,
                    result=ScoreDimensionResult.MATCH,
                    reason="Beneficiary business stage / unit status matches scheme criteria."
                ))
                matched_factors.append("business_stage_match")
                recommendation_reasons.append("Fully supports your business stage and unit type.")
            else:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="business_stage_match", max_weight=w_stage, score=0.0,
                    result=ScoreDimensionResult.NO_MATCH,
                    reason="Beneficiary business stage does not match scheme allowed criteria."
                ))
                unmatched_factors.append("business_stage_match")

        # ── 5. Activity Match (Max 10.0) ──
        w_act = SCORING_WEIGHTS["activity_match"]
        if profile.activity_type is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="activity_match", max_weight=w_act, score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Activity type not specified on beneficiary profile."
            ))
            not_evaluated_factors.append("activity_match")
        else:
            status_act, factor_act, expl_act = TaxonomyMatcher.match_sector_or_activity(
                user_input=profile.activity_type,
                scheme_sectors=norm_profile.normalized_sectors,
                scheme_activities=norm_profile.normalized_activities,
                scheme_aliases=norm_profile.normalized_activity_aliases
            )
            score_act = round(w_act * factor_act, 1)

            if status_act in ("MATCH", "PARTIAL_MATCH"):
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="activity_match", max_weight=w_act, score=score_act,
                    result=ScoreDimensionResult.MATCH if status_act == "MATCH" else ScoreDimensionResult.PARTIAL_MATCH,
                    reason=expl_act
                ))
                matched_factors.append("activity_match")
                recommendation_reasons.append(expl_act)
            else:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="activity_match", max_weight=w_act, score=0.0,
                    result=ScoreDimensionResult.NO_MATCH,
                    reason=expl_act
                ))
                unmatched_factors.append("activity_match")

        # ── 6. Geography Match (Max 10.0) ──
        w_geo = SCORING_WEIGHTS["geography_match"]
        status_geo, factor_geo, expl_geo = TaxonomyMatcher.match_geography(
            user_state=profile.state,
            scheme_geographies=norm_profile.normalized_geographies
        )
        score_geo = round(w_geo * factor_geo, 1)

        if status_geo == "MATCH":
            breakdown.append(ScoreDimensionBreakdown(
                dimension="geography_match", max_weight=w_geo, score=score_geo,
                result=ScoreDimensionResult.MATCH,
                reason=expl_geo
            ))
            matched_factors.append("geography_match")
            recommendation_reasons.append(expl_geo)
        elif status_geo == "NOT_EVALUATED":
            breakdown.append(ScoreDimensionBreakdown(
                dimension="geography_match", max_weight=w_geo, score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason=expl_geo
            ))
            not_evaluated_factors.append("geography_match")
        else:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="geography_match", max_weight=w_geo, score=0.0,
                result=ScoreDimensionResult.NO_MATCH,
                reason=expl_geo
            ))
            unmatched_factors.append("geography_match")

        # ── 7. Financial Fit (Max 15.0) ──
        w_fin = SCORING_WEIGHTS["financial_fit"]
        if profile.requested_loan_amount is None and profile.project_cost is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="financial_fit", max_weight=w_fin, score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Project cost and requested loan amount not specified on profile."
            ))
            not_evaluated_factors.append("financial_fit")
        elif scheme.max_loan_amount is None and scheme.max_project_cost is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="financial_fit", max_weight=w_fin, score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Scheme maximum loan amount and project cost are UNKNOWN / require verification."
            ))
            not_evaluated_factors.append("financial_fit")
        else:
            fin_fits = True
            reasons_fin = []
            if profile.requested_loan_amount is not None and scheme.max_loan_amount is not None:
                if profile.requested_loan_amount <= scheme.max_loan_amount:
                    reasons_fin.append(f"Requested loan ₹{profile.requested_loan_amount:,.2f} is within maximum loan limit ₹{scheme.max_loan_amount:,.2f}.")
                else:
                    fin_fits = False

            if profile.project_cost is not None and scheme.max_project_cost is not None:
                if profile.project_cost <= scheme.max_project_cost:
                    reasons_fin.append(f"Project cost ₹{profile.project_cost:,.2f} is within maximum project cost limit ₹{scheme.max_project_cost:,.2f}.")
                else:
                    fin_fits = False

            if fin_fits and reasons_fin:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="financial_fit", max_weight=w_fin, score=w_fin,
                    result=ScoreDimensionResult.MATCH,
                    reason=" ".join(reasons_fin)
                ))
                matched_factors.append("financial_fit")
                recommendation_reasons.append("Financial terms match your requested financing scenario.")
            elif not fin_fits:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="financial_fit", max_weight=w_fin, score=0.0,
                    result=ScoreDimensionResult.NO_MATCH,
                    reason="Requested financial terms exceed scheme maximum limits."
                ))
                unmatched_factors.append("financial_fit")
            else:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="financial_fit", max_weight=w_fin, score=0.0,
                    result=ScoreDimensionResult.NOT_EVALUATED,
                    reason="Insufficient scheme financial parameters for fit evaluation."
                ))
                not_evaluated_factors.append("financial_fit")

        # ── 8. Calculate Normalized Score (0.0 - 100.0) ──
        evaluated_max_weight = sum(
            b.max_weight for b in breakdown if b.result in (ScoreDimensionResult.MATCH, ScoreDimensionResult.PARTIAL_MATCH, ScoreDimensionResult.NO_MATCH)
        )
        total_earned_score = sum(b.score for b in breakdown)

        if evaluated_max_weight > 0:
            normalized_score = round((total_earned_score / evaluated_max_weight) * 100.0, 1)
        else:
            normalized_score = 50.0

        return (
            normalized_score,
            matched_factors,
            unmatched_factors,
            not_evaluated_factors,
            recommendation_reasons,
            breakdown,
        )

    @classmethod
    def get_recommendations(
        cls,
        db: Session,
        req: RecommendationRequest
    ) -> RecommendationResponse:
        """
        Orchestrates full recommendation pipeline:
        1. Retrieve all 56 schemes
        2. Hard eligibility gating (via TASK-003 engine)
        3. Soft-fit scoring of eligible candidates
        4. Deterministic ranking (score DESC, scheme_id ASC)
        5. Top-K selection
        """
        profile = req.profile

        # Identify missing profile fields
        missing_fields: List[str] = []
        for field_name in profile.model_fields.keys():
            if getattr(profile, field_name) is None:
                missing_fields.append(field_name)

        # Retrieve schemes with pre-loaded relations (Only ACTIVE schemes)
        schemes = db.query(Scheme).options(
            selectinload(Scheme.verifications),
            selectinload(Scheme.rules),
            selectinload(Scheme.documents),
        ).filter(
            or_(Scheme.scheme_status == "ACTIVE", Scheme.scheme_status == None, Scheme.scheme_status == "")
        ).all()

        evaluated_count = len(schemes)
        eligible_candidates: List[Tuple[Scheme, SchemeEligibilityResult]] = []
        ineligible_candidates: List[Tuple[Scheme, SchemeEligibilityResult]] = []
        insufficient_candidates: List[Tuple[Scheme, SchemeEligibilityResult]] = []
        ineligible_cnt = 0
        insufficient_cnt = 0

        # Hard Eligibility Gate
        for scheme in schemes:
            elig_res = DeterministicEligibilityEngine.evaluate_scheme(scheme, profile)
            if elig_res.status == SchemeEligibilityStatus.ELIGIBLE:
                eligible_candidates.append((scheme, elig_res))
            elif elig_res.status == SchemeEligibilityStatus.INELIGIBLE:
                ineligible_candidates.append((scheme, elig_res))
                ineligible_cnt += 1
            elif elig_res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION:
                insufficient_candidates.append((scheme, elig_res))
                insufficient_cnt += 1

        eligible_count = len(eligible_candidates)

        # Soft-Fit Scoring for all eligible candidates
        scored_items: List[Tuple[float, str, RecommendationItem]] = []

        for scheme, elig_res in eligible_candidates:
            (
                score,
                matched,
                unmatched,
                not_eval,
                rec_reasons,
                breakdown,
            ) = cls.evaluate_soft_fit(scheme, profile, elig_res)

            passed_reasons = [rule.reason for rule in elig_res.hard_rules_passed] or ["Passed hard eligibility gate requirements."]

            rec_item = RecommendationItem(
                rank=0,  # Populated after ranking
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                eligibility_status=elig_res.status.value,
                score=score,
                eligible=True,
                matched_rules=passed_reasons,
                failed_rules=[],
                missing_information=[],
                matched_factors=matched,
                unmatched_factors=unmatched,
                not_evaluated_factors=not_eval,
                eligibility_reasons=passed_reasons,
                recommendation_reasons=rec_reasons,
                score_breakdown=breakdown,
                ministry=scheme.ministry,
                source_organization=scheme.source_organization,
                official_portal=scheme.official_portal,
                application_url=scheme.application_url,
                official_source_url=scheme.official_source_url,
                source_document=scheme.source_document,
                is_direct_portal_scheme=(scheme.application_route == "DIRECT_PORTAL"),
                financial_category=scheme.financial_category,
                is_credit_scheme=scheme.is_credit_scheme,
                calculator_applicable=scheme.calculator_applicable,
                financial_assistance_summary=scheme.financial_assistance_summary,
                max_loan_amount=float(scheme.max_loan_amount) if scheme.max_loan_amount is not None else None,
                interest_rate=scheme.interest_rate,
                repayment_period_max_months=scheme.repayment_period_max_months,
                subsidy_percentage=float(scheme.subsidy_percentage) if scheme.subsidy_percentage is not None else None,
                grant_amount=float(scheme.grant_amount) if scheme.grant_amount is not None else None,
            )
            # Tuple for sorting: (-score, scheme_id) for score DESC, scheme_id ASC
            scored_items.append((-score, scheme.scheme_id, rec_item))

        # Deterministic Ranking: score DESC, tie-breaker scheme_id ASC
        scored_items.sort(key=lambda x: (x[0], x[1]))

        # Assign ranks and select Top-K
        top_recommendations: List[RecommendationItem] = []
        for idx, (_, _, item) in enumerate(scored_items[:req.top_k], start=1):
            item.rank = idx
            top_recommendations.append(item)

        # Build Ineligible Schemes List with exact failed reasons
        ineligible_items: List[RecommendationItem] = []
        for idx, (scheme, elig_res) in enumerate(ineligible_candidates, start=1):
            (
                score,
                matched,
                unmatched,
                not_eval,
                rec_reasons,
                breakdown,
            ) = cls.evaluate_soft_fit(scheme, profile, elig_res)

            passed_reasons = [rule.reason for rule in elig_res.hard_rules_passed]
            failed_reasons = [rule.reason for rule in elig_res.hard_rules_failed]
            unknown_reasons = [rule.reason for rule in elig_res.unknown_eligibility_rules]

            ineligible_items.append(RecommendationItem(
                rank=idx,
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                eligibility_status=elig_res.status.value,
                score=score,
                eligible=False,
                matched_rules=passed_reasons,
                failed_rules=failed_reasons,
                missing_information=unknown_reasons,
                matched_factors=matched,
                unmatched_factors=unmatched,
                not_evaluated_factors=not_eval,
                eligibility_reasons=failed_reasons,
                recommendation_reasons=rec_reasons,
                score_breakdown=breakdown,
                ministry=scheme.ministry,
                source_organization=scheme.source_organization,
                official_portal=scheme.official_portal,
                application_url=scheme.application_url,
                official_source_url=scheme.official_source_url,
                source_document=scheme.source_document,
                is_direct_portal_scheme=(scheme.application_route == "DIRECT_PORTAL"),
                financial_category=scheme.financial_category,
                is_credit_scheme=scheme.is_credit_scheme,
                calculator_applicable=scheme.calculator_applicable,
                financial_assistance_summary=scheme.financial_assistance_summary,
                max_loan_amount=float(scheme.max_loan_amount) if scheme.max_loan_amount is not None else None,
                interest_rate=scheme.interest_rate,
                repayment_period_max_months=scheme.repayment_period_max_months,
                subsidy_percentage=float(scheme.subsidy_percentage) if scheme.subsidy_percentage is not None else None,
                grant_amount=float(scheme.grant_amount) if scheme.grant_amount is not None else None,
            ))

        # Build Insufficient Information Schemes List
        insufficient_items: List[RecommendationItem] = []
        for idx, (scheme, elig_res) in enumerate(insufficient_candidates, start=1):
            (
                score,
                matched,
                unmatched,
                not_eval,
                rec_reasons,
                breakdown,
            ) = cls.evaluate_soft_fit(scheme, profile, elig_res)

            passed_reasons = [rule.reason for rule in elig_res.hard_rules_passed]
            unknown_reasons = [rule.reason for rule in elig_res.unknown_eligibility_rules]

            insufficient_items.append(RecommendationItem(
                rank=idx,
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                eligibility_status=elig_res.status.value,
                score=score,
                eligible=False,
                matched_rules=passed_reasons,
                failed_rules=[],
                missing_information=unknown_reasons,
                matched_factors=matched,
                unmatched_factors=unmatched,
                not_evaluated_factors=not_eval,
                eligibility_reasons=unknown_reasons,
                recommendation_reasons=rec_reasons,
                score_breakdown=breakdown,
                ministry=scheme.ministry,
                source_organization=scheme.source_organization,
                official_portal=scheme.official_portal,
                application_url=scheme.application_url,
                official_source_url=scheme.official_source_url,
                source_document=scheme.source_document,
                is_direct_portal_scheme=(scheme.application_route == "DIRECT_PORTAL"),
                financial_category=scheme.financial_category,
                is_credit_scheme=scheme.is_credit_scheme,
                calculator_applicable=scheme.calculator_applicable,
                financial_assistance_summary=scheme.financial_assistance_summary,
                max_loan_amount=float(scheme.max_loan_amount) if scheme.max_loan_amount is not None else None,
                interest_rate=scheme.interest_rate,
                repayment_period_max_months=scheme.repayment_period_max_months,
                subsidy_percentage=float(scheme.subsidy_percentage) if scheme.subsidy_percentage is not None else None,
                grant_amount=float(scheme.grant_amount) if scheme.grant_amount is not None else None,
            ))

        # Profile Summary
        profile_summary = {
            k: v for k, v in profile.model_dump().items() if v is not None
        }

        return RecommendationResponse(
            profile_summary=profile_summary,
            evaluated_scheme_count=evaluated_count,
            eligible_scheme_count=eligible_count,
            excluded_scheme_count=ineligible_cnt,
            insufficient_info_scheme_count=insufficient_cnt,
            recommendations=top_recommendations,
            ineligible_schemes=ineligible_items,
            insufficient_info_schemes=insufficient_items,
            missing_profile_fields=missing_fields,
        )
