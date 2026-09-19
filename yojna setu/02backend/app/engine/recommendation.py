"""
Deterministic Scheme Recommendation Engine for YojnaSetu (Scale-Up Architecture).
Evaluates schemes deterministically across 3 layers:
  Layer 1: Hard Statutory Eligibility Gates (Zero LLM, Strict Invariant Filtering)
  Layer 2: Hard Financial Compatibility Gates (Zero LLM, Exact Decimal Math)
  Layer 3: Multi-Dimensional Fit Scoring (Versioned Scoring Policy v2.1.0, Fixed 100.0 Denominator)
  Deterministic Tie-Breaking & Traceable Explainability
"""

import re
import uuid
from typing import List, Dict, Any, Tuple, Optional
from decimal import Decimal
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.scheme import Scheme
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.eligibility import (
    SchemeEligibilityStatus,
    SchemeEligibilityResult,
    RuleEvaluationResult,
    RuleEvaluationDetail,
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
from app.engine.scoring_policy import ScoringPolicy, DEFAULT_SCORING_POLICY
from app.engine.relevance_policy import SIH26092RecommendationRelevancePolicy

# Backwards-compatible weights reference
SCORING_WEIGHTS = DEFAULT_SCORING_POLICY.weights

SENTINEL_STRINGS = {"UNKNOWN", "NOT_APPLICABLE", "CONDITIONAL", "NONE", ""}


def _is_sentinel(val: Optional[str]) -> bool:
    if val is None:
        return True
    return str(val).strip().upper() in SENTINEL_STRINGS


def compute_scheme_quality_score(scheme: Scheme) -> float:
    """Calculates objective scheme data completeness score (0.0 to 100.0)."""
    elig_pts = 0
    if scheme.target_beneficiary: elig_pts += 5
    if scheme.state_coverage or scheme.state_restriction: elig_pts += 5
    if scheme.sector: elig_pts += 5
    if scheme.applicant_types: elig_pts += 5
    if scheme.age_min is not None or scheme.age_max is not None: elig_pts += 5
    if scheme.income_limit is not None: elig_pts += 5

    fin_pts = 0
    if scheme.benefit_description or scheme.financial_assistance_summary: fin_pts += 5
    if scheme.is_credit_scheme is not None: fin_pts += 5
    if scheme.max_loan_amount is not None: fin_pts += 5
    if scheme.subsidy_percentage is not None or scheme.subsidy_details: fin_pts += 5
    if scheme.interest_rate_max is not None or scheme.interest_rate is not None: fin_pts += 5

    src_pts = 0
    if scheme.official_source_url: src_pts += 10
    if scheme.application_url: src_pts += 5
    if scheme.ministry: src_pts += 5
    if scheme.source_document: src_pts += 5

    doc_pts = 0
    if scheme.required_documents: doc_pts += 10
    if scheme.application_mode: doc_pts += 5
    if scheme.application_steps: doc_pts += 5

    return float(min(100, elig_pts + fin_pts + src_pts + doc_pts))


class DeterministicRecommendationEngine:
    """
    Core Deterministic Recommendation Engine.
    Combines SQL shortlist pre-filtering, hard statutory eligibility gating,
    hard financial compatibility, and soft-fit multi-dimensional scoring.
    """

    @classmethod
    def evaluate_soft_fit(
        cls,
        scheme: Scheme,
        profile: BeneficiaryProfileInput,
        eligibility: SchemeEligibilityResult,
        policy: Optional[ScoringPolicy] = None,
        semantic_query: Optional[str] = None,
    ) -> Tuple[float, List[str], List[str], List[str], List[str], List[ScoreDimensionBreakdown]]:
        """
        Evaluates soft-fit score for an eligible scheme candidate.
        Returns: (normalized_score, matched_factors, unmatched_factors, not_evaluated_factors, recommendation_reasons, score_breakdown)
        """
        if policy is None:
            policy = DEFAULT_SCORING_POLICY

        breakdown: List[ScoreDimensionBreakdown] = []
        matched_factors: List[str] = []
        unmatched_factors: List[str] = []
        not_evaluated_factors: List[str] = []
        recommendation_reasons: List[str] = []

        # Generate Rich Normalized Matching Profile
        norm_profile = SchemeNormalizedProfileBuilder.build_profile(scheme)

        # ── 1. Sector Match (Max 20.0) ──
        w_sector = policy.weights.get("sector_match", 20.0)
        if profile.sector is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="sector_match", max_weight=w_sector,
                score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Beneficiary sector not specified on profile; neutral baseline weight applied."
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
                # Check if scheme is generic / open to all sectors
                if not norm_profile.normalized_sectors or "ALL" in norm_profile.normalized_sectors or "ANY" in norm_profile.normalized_sectors:
                    gen_score = round(w_sector * policy.general_scheme_ratio, 1)
                    breakdown.append(ScoreDimensionBreakdown(
                        dimension="sector_match", max_weight=w_sector, score=gen_score,
                        result=ScoreDimensionResult.PARTIAL_MATCH,
                        reason="Scheme supports all enterprise and commercial sectors (universal scope)."
                    ))
                    matched_factors.append("sector_match (UNIVERSAL)")
                    recommendation_reasons.append("Supports all commercial sectors.")
                else:
                    breakdown.append(ScoreDimensionBreakdown(
                        dimension="sector_match", max_weight=w_sector, score=0.0,
                        result=ScoreDimensionResult.NO_MATCH,
                        reason=explanation
                    ))
                    unmatched_factors.append("sector_match")

        # ── 2. Applicant Type Match (Max 15.0) ──
        w_app = policy.weights.get("applicant_type_match", 15.0)
        if profile.applicant_type is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="applicant_type_match", max_weight=w_app,
                score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Applicant type not specified on beneficiary profile; neutral baseline weight applied."
            ))
            not_evaluated_factors.append("applicant_type_match")
        else:
            prof_app = TaxonomyMatcher.normalize_string(profile.applicant_type)
            norm_apps = [TaxonomyMatcher.normalize_string(a) for a in norm_profile.normalized_applicant_types]

            if prof_app in norm_apps or any(prof_app in a for a in norm_apps) or "INDIVIDUAL" in norm_apps:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="applicant_type_match", max_weight=w_app, score=w_app,
                    result=ScoreDimensionResult.MATCH,
                    reason=f"Applicant type '{profile.applicant_type}' matches scheme criteria ({', '.join(norm_profile.normalized_applicant_types[:3]) or 'Individual'})."
                ))
                matched_factors.append("applicant_type_match")
                recommendation_reasons.append(f"Tailored for '{profile.applicant_type}' applicants.")
            elif not norm_apps:
                gen_app_score = round(w_app * policy.general_scheme_ratio, 1)
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="applicant_type_match", max_weight=w_app, score=gen_app_score,
                    result=ScoreDimensionResult.MATCH,
                    reason="Scheme has universal applicant type eligibility."
                ))
                matched_factors.append("applicant_type_match (UNIVERSAL)")
            else:
                breakdown.append(ScoreDimensionBreakdown(
                    dimension="applicant_type_match", max_weight=w_app, score=0.0,
                    result=ScoreDimensionResult.NO_MATCH,
                    reason=f"Applicant type '{profile.applicant_type}' not in scheme allowed list."
                ))
                unmatched_factors.append("applicant_type_match")

        # ── 3. Target Group / Marginalized Group Match (Max 15.0) ──
        w_target = policy.weights.get("target_group_match", 15.0)
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
                dimension="target_group_match", max_weight=w_target,
                score=0.0,
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
        w_stage = policy.weights.get("business_stage_match", 15.0)
        if profile.business_stage is None and profile.is_new_unit is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="business_stage_match", max_weight=w_stage,
                score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Business stage and unit type not specified on beneficiary profile."
            ))
            not_evaluated_factors.append("business_stage_match")
        else:
            stage_match = False
            norm_stages = norm_profile.normalized_business_stages
            if profile.is_new_unit is True and ("NEW" in norm_stages or "NEW_UNIT" in norm_stages or "ANY_STAGE" in norm_stages or not norm_stages):
                stage_match = True
            elif profile.is_new_unit is False and ("EXISTING" in norm_stages or "EXPANSION" in norm_stages or "ANY_STAGE" in norm_stages or not norm_stages):
                stage_match = True
            elif profile.business_stage:
                prof_stg = TaxonomyMatcher.normalize_string(profile.business_stage)
                if prof_stg in norm_stages or "ANY_STAGE" in norm_stages or not norm_stages:
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
        w_act = policy.weights.get("activity_match", 10.0)
        if profile.activity_type is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="activity_match", max_weight=w_act,
                score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Activity type not specified on beneficiary profile; neutral baseline weight applied."
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
        w_geo = policy.weights.get("geography_match", 10.0)
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
                dimension="geography_match", max_weight=w_geo,
                score=0.0,
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
        w_fin = policy.weights.get("financial_fit", 15.0)
        if profile.requested_loan_amount is None and profile.project_cost is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="financial_fit", max_weight=w_fin,
                score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Project cost and requested loan amount not specified on profile; neutral baseline applied."
            ))
            not_evaluated_factors.append("financial_fit")
        elif scheme.max_loan_amount is None and scheme.max_project_cost is None:
            breakdown.append(ScoreDimensionBreakdown(
                dimension="financial_fit", max_weight=w_fin,
                score=0.0,
                result=ScoreDimensionResult.NOT_EVALUATED,
                reason="Scheme maximum loan amount and project cost are UNKNOWN / not specified."
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
                    dimension="financial_fit", max_weight=w_fin,
                    score=0.0,
                    result=ScoreDimensionResult.NOT_EVALUATED,
                    reason="Scheme financial parameters not specified for exact fit evaluation."
                ))
                not_evaluated_factors.append("financial_fit")

        # ── 8. Calculate Normalized Score with Credibility Shrinkage & Fixed Denominator ──
        evaluated_max_weight = sum(
            b.max_weight for b in breakdown if b.result in (ScoreDimensionResult.MATCH, ScoreDimensionResult.PARTIAL_MATCH, ScoreDimensionResult.NO_MATCH)
        )
        total_earned_score = sum(b.score for b in breakdown)

        # Bayesian shrinkage: Unevaluated optional dimensions earn neutral baseline credit,
        # preventing denominator inflation while penalizing unverified schemes
        unevaluated_weight = max(0.0, 100.0 - evaluated_max_weight)
        neutral_credit = unevaluated_weight * policy.neutral_weight_ratio

        raw_base_score = total_earned_score + neutral_credit

        # Affirmative Action Bonuses
        bonuses_total = 0.0
        if is_sc and profile.gender and profile.gender.strip().upper() in ("FEMALE", "WOMAN"):
            if any(w in (scheme.target_groups or scheme.target_beneficiary or "").lower() for w in ["women", "woman", "sc", "female"]) or scheme.sc_required:
                bonus_scw = policy.bonuses.get("sc_woman_priority_bonus", 3.0)
                bonuses_total += bonus_scw
                recommendation_reasons.append(f"Affirmative action priority for SC Woman Entrepreneur (+{bonus_scw} pts).")

        is_artisan = profile.is_artisan or (profile.applicant_type and "ARTISAN" in profile.applicant_type.upper())
        if is_artisan:
            if any(w in (scheme.target_beneficiary or scheme.sector or "").lower() for w in ["artisan", "craft", "handloom", "weaver", "vishwakarma"]):
                bonus_art = policy.bonuses.get("rural_artisan_priority_bonus", 2.0)
                bonuses_total += bonus_art
                recommendation_reasons.append(f"Special artisan & craft sector priority (+{bonus_art} pts).")

        if semantic_query:
            q_clean = semantic_query.lower()
            q_words = [w for w in re.findall(r"\w+", q_clean) if len(w) > 2]
            text_corpus = f"{scheme.scheme_name} {scheme.short_description or ''} {scheme.sector or ''}".lower()
            overlap_hits = sum(1 for w in q_words if w in text_corpus)
            if overlap_hits >= 2:
                bonus_sem = min(policy.bonuses.get("semantic_resonance_max_bonus", 5.0), float(overlap_hits))
                bonuses_total += bonus_sem
                recommendation_reasons.append(f"Semantic query resonance (+{bonus_sem} pts).")

        # Data Quality Calibration Multiplier
        quality_score = compute_scheme_quality_score(scheme)
        quality_multiplier = 0.85 + 0.15 * (quality_score / 100.0)

        # Final normalized score bounded to [0.0, 100.0]
        normalized_score = min(100.0, max(0.0, round((raw_base_score + bonuses_total) * quality_multiplier, 1)))

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
        req: RecommendationRequest,
        policy: Optional[ScoringPolicy] = None
    ) -> RecommendationResponse:
        """
        Orchestrates full recommendation pipeline:
        1. Retrieve active schemes
        2. Layer 1: Hard statutory eligibility gating (caste, gender, state, age, income)
        3. Layer 2: Hard financial feasibility gating (requested loan vs maximum limits)
        4. Layer 3: Soft-fit scoring with versioned ScoringPolicy v2.1.0 & fixed 100.0 denominator
        5. Deterministic tie-breaking (-score, -quality_score, scheme_id ASC)
        6. Explainable comparative ranking reasons
        """
        if policy is None:
            policy = DEFAULT_SCORING_POLICY

        profile = req.profile
        trace_id = f"rec-trace-{uuid.uuid4().hex[:8]}"

        # Identify missing profile fields
        missing_fields: List[str] = []
        for field_name in profile.model_fields.keys():
            if getattr(profile, field_name) is None:
                missing_fields.append(field_name)

        # Retrieve schemes with pre-loaded relations (Only ACTIVE schemes)
        schemes = db.query(Scheme).options(
            selectinload(Scheme.rules),
            selectinload(Scheme.verifications),
            selectinload(Scheme.partner_mappings),
            selectinload(Scheme.documents),
        ).filter(
            or_(Scheme.scheme_status == "ACTIVE", Scheme.scheme_status == None, Scheme.scheme_status == "")
        ).all()

        # Gate candidate universe using SIH26092 recommendation relevance policy
        # Excludes out-of-scope records (e.g., pilgrimage tours, sports medals) while preserving them in database
        universe_schemes = []
        for s in schemes:
            is_rel, _, _ = SIH26092RecommendationRelevancePolicy.is_recommendation_universe_eligible(s)
            if is_rel:
                universe_schemes.append(s)

        evaluated_count = len(universe_schemes)
        eligible_candidates: List[Tuple[Scheme, SchemeEligibilityResult]] = []
        ineligible_candidates: List[Tuple[Scheme, SchemeEligibilityResult]] = []
        insufficient_candidates: List[Tuple[Scheme, SchemeEligibilityResult]] = []
        conditional_candidates: List[Tuple[Scheme, SchemeEligibilityResult]] = []
        not_applicable_candidates: List[Tuple[Scheme, SchemeEligibilityResult]] = []

        ineligible_cnt = 0
        insufficient_cnt = 0
        conditional_cnt = 0
        not_applicable_cnt = 0

        # ── Layer 1 & Layer 2: Hard Statutory & Financial Feasibility Gates ──
        for scheme in universe_schemes:
            elig_res = DeterministicEligibilityEngine.evaluate_scheme(scheme, profile)

            # Layer 2 Hard Financial Compatibility Gate
            if elig_res.status == SchemeEligibilityStatus.ELIGIBLE and profile.requested_loan_amount is not None:
                max_loan = scheme.max_loan_amount
                if max_loan is not None and max_loan > 0:
                    exceed_ratio = policy.thresholds.get("loan_exceed_ratio_hard_fail", 1.5)
                    if Decimal(str(profile.requested_loan_amount)) > Decimal(str(max_loan)) * Decimal(str(exceed_ratio)):
                        elig_res.status = SchemeEligibilityStatus.INELIGIBLE
                        fail_reason = f"Requested loan ₹{profile.requested_loan_amount:,.2f} substantially exceeds scheme maximum assistance limit of ₹{max_loan:,.2f}."
                        elig_res.failed_rules.append(fail_reason)
                        elig_res.hard_rules_failed.append(RuleEvaluationDetail(
                            rule_id=f"FIN-{scheme.scheme_id}-MAX-LOAN",
                            field="requested_loan_amount",
                            operator="<=",
                            required_value=float(max_loan),
                            value_type="INR",
                            rule_type="HARD_FINANCIAL",
                            priority="HIGH",
                            condition_group="FINANCIAL",
                            actual_value=float(profile.requested_loan_amount),
                            result=RuleEvaluationResult.FAIL,
                            reason=fail_reason
                        ))

            if elig_res.status == SchemeEligibilityStatus.ELIGIBLE:
                eligible_candidates.append((scheme, elig_res))
            elif elig_res.status == SchemeEligibilityStatus.INELIGIBLE:
                ineligible_candidates.append((scheme, elig_res))
                ineligible_cnt += 1
            elif elig_res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION:
                insufficient_candidates.append((scheme, elig_res))
                insufficient_cnt += 1
            elif elig_res.status == SchemeEligibilityStatus.CONDITIONAL:
                conditional_candidates.append((scheme, elig_res))
                conditional_cnt += 1
            elif elig_res.status == SchemeEligibilityStatus.NOT_APPLICABLE:
                not_applicable_candidates.append((scheme, elig_res))
                not_applicable_cnt += 1

        # Evaluate Financial Health Context (Advisory only)
        fin_health_status = None
        fin_health_advisory = None
        try:
            from app.schemas.financial_health import FinancialHealthInput
            from app.engine.financial_health import DeterministicFinancialHealthEngine

            if profile.annual_income is not None or profile.requested_loan_amount is not None or getattr(profile, "monthly_obligations", None) is not None:
                f_res = DeterministicFinancialHealthEngine.evaluate(FinancialHealthInput(profile=profile), db=db)
                fin_health_status = f_res.status.value
                fin_health_advisory = f_res.summary_headline
        except Exception:
            fin_health_status = None
            fin_health_advisory = None

        eligible_count = len(eligible_candidates)

        def _get_scheme_fin_details(s: Scheme) -> Dict[str, Any]:
            fin_suit = None
            fin_reason = None
            emi_val = None
            sub_val = None
            own_val = None
            try:
                from app.engine.financial_health import DeterministicFinancialHealthEngine
                eval_res = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
                    scheme=s,
                    profile=profile,
                    db=db
                )
                fin_suit = eval_res.suitability.value
                fin_reason = eval_res.suitability_reason
                emi_val = float(eval_res.estimated_emi) if eval_res.estimated_emi is not None else None
                sub_val = float(eval_res.available_subsidy) if eval_res.available_subsidy is not None else None
                own_val = float(eval_res.required_margin_money) if eval_res.required_margin_money is not None else None
            except Exception:
                pass
            return {
                "financial_suitability": fin_suit,
                "financial_suitability_reason": fin_reason,
                "estimated_monthly_installment": emi_val,
                "available_subsidy_amount": sub_val,
                "required_own_contribution": own_val,
                "min_project_cost": float(s.min_project_cost) if s.min_project_cost is not None else None,
                "max_project_cost": float(s.max_project_cost) if s.max_project_cost is not None else None,
                "min_loan_amount": float(s.min_loan_amount) if s.min_loan_amount is not None else None,
                "collateral_requirement": s.collateral_required if s.collateral_required and s.collateral_required not in ("", "UNKNOWN", "NOT_APPLICABLE") else "NOT_PUBLICLY_AVAILABLE",
                "guarantee_requirement": getattr(s, "guarantee_requirement", None) or "NOT_PUBLICLY_AVAILABLE",
                "processing_fee": getattr(s, "processing_fee", None) or "NOT_PUBLICLY_AVAILABLE",
            }

        # ── Layer 3: Soft-Fit Scoring for all eligible candidates ──
        scored_items: List[Tuple[float, float, str, RecommendationItem]] = []

        for scheme, elig_res in eligible_candidates:
            (
                score,
                matched,
                unmatched,
                not_eval,
                rec_reasons,
                breakdown,
            ) = cls.evaluate_soft_fit(
                scheme=scheme,
                profile=profile,
                eligibility=elig_res,
                policy=policy,
                semantic_query=req.semantic_query
            )

            passed_reasons = [rule.reason for rule in elig_res.hard_rules_passed] or ["Passed hard eligibility gate requirements."]
            quality_score = compute_scheme_quality_score(scheme)

            # Bonuses identification
            bonuses = [r for r in rec_reasons if "(+" in r]
            fin_details = _get_scheme_fin_details(scheme)

            # Determine match tier - a financially unsuitable scheme must not be presented as "BEST_MATCH"
            fin_suit = fin_details.get("financial_suitability")
            if score >= 75.0:
                tier = "ELIGIBLE" if fin_suit == "FINANCIALLY_UNSUITABLE" else "BEST_MATCH"
            elif score >= 50.0:
                tier = "ELIGIBLE"
            else:
                tier = "POTENTIALLY_RELEVANT"

            # Extract documents
            doc_names = []
            if getattr(scheme, "documents", None):
                doc_names = [d.document_name for d in scheme.documents if getattr(d, "active", True)]
            elif scheme.required_documents:
                doc_names = [d.strip() for d in scheme.required_documents.split(";") if d.strip()]

            # Determine partner availability
            if getattr(scheme, "partner_mappings", None) and len(scheme.partner_mappings) > 0:
                partner_avail = f"Verified Physical Partner Available ({len(scheme.partner_mappings)} authorized institutions)"
            elif scheme.application_route == "DIRECT_PORTAL":
                partner_avail = "Direct Online Portal Route (Physical bank visit not required)"
            else:
                partner_avail = "Official Government Application Channel"

            # Key conditions
            key_conds = [r.reason for r in elig_res.hard_rules_passed[:3]] or [
                r.error_message for r in (getattr(scheme, "rules", []) or [])[:3] if getattr(r, "error_message", None)
            ]

            missing_info = [f"Missing '{dim}' on applicant profile" for dim in not_eval]
            dim_penalties = [f"Unevaluated dimension penalty applied for '{dim}'" for dim in not_eval]

            rec_item = RecommendationItem(
                rank=0,  # Populated after ranking
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                eligibility_status=elig_res.status.value,
                score=score,
                eligible=True,
                match_tier=tier,
                scoring_policy_version=policy.policy_version,
                data_quality_score=quality_score,
                bonuses=bonuses,
                penalties=dim_penalties,
                financial_health_status=fin_health_status,
                financial_health_advisory=fin_health_advisory,
                matched_rules=passed_reasons,
                failed_rules=[],
                missing_information=missing_info,
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
                is_direct_portal_scheme=(scheme.application_route == "DIRECT_PORTAL" or not bool(getattr(scheme, "partner_mappings", None))),
                has_verified_partner_mapping=bool(getattr(scheme, "partner_mappings", None)),
                application_channel="CHANNEL_PARTNER_LOCATOR" if bool(getattr(scheme, "partner_mappings", None)) else "OFFICIAL_DIRECT_PORTAL",
                partner_availability=partner_avail,
                required_documents=doc_names,
                key_conditions=key_conds,
                financial_category=scheme.financial_category,
                is_credit_scheme=scheme.is_credit_scheme,
                calculator_applicable=scheme.calculator_applicable,
                financial_assistance_summary=scheme.financial_assistance_summary,
                short_description=scheme.short_description or scheme.purpose,
                purpose=scheme.purpose or scheme.short_description,
                max_loan_amount=float(scheme.max_loan_amount) if scheme.max_loan_amount is not None else None,
                interest_rate=scheme.interest_rate,
                repayment_period_max_months=scheme.repayment_period_max_months,
                subsidy_percentage=float(scheme.subsidy_percentage) if scheme.subsidy_percentage is not None else None,
                grant_amount=float(scheme.grant_amount) if scheme.grant_amount is not None else None,
                **fin_details
            )
            # Tuple for deterministic tie-breaking:
            # 1. Statutory eligibility (all in this loop are eligible)
            # 2. Scheme relevance (-score)
            # 3. Financial compatibility (0: viable, 1: high repayment burden)
            # 4. Scheme quality (-quality_score)
            # 5. Stable scheme_id ASC
            scored_items.append((-score, scheme.scheme_id, rec_item))

        # Deterministic Ranking: score DESC, scheme_id ASC
        scored_items.sort(key=lambda x: (x[0], x[1]))

        # Assign ranks and generate comparative ranking reasons
        top_recommendations: List[RecommendationItem] = []
        for idx, (_, _, item) in enumerate(scored_items[:req.top_k], start=1):
            item.rank = idx
            if idx == 1:
                fin_note = " (Note: High repayment burden detected)" if item.financial_suitability == "FINANCIALLY_UNSUITABLE" else ""
                item.comparative_ranking_reason = f"Ranked #1 (Score: {item.score}) with top multi-dimensional fit ({', '.join(item.matched_factors[:3]) or 'eligible'}).{fin_note}"
            else:
                prev_item = top_recommendations[idx - 2]
                if prev_item.financial_suitability in ("STRONG_FIT", "POSSIBLE_FIT") and item.financial_suitability == "FINANCIALLY_UNSUITABLE":
                    item.comparative_ranking_reason = (
                        f"Ranked #{idx} (Score: {item.score}) below #{idx - 1} "
                        f"({prev_item.scheme_name[:25]}) due to higher repayment burden despite statutory eligibility."
                    )
                else:
                    item.comparative_ranking_reason = (
                        f"Ranked #{idx} (Score: {item.score}) below #{idx - 1} "
                        f"({prev_item.scheme_name[:25]}, Score: {prev_item.score}) due to difference in multi-dimensional fit."
                    )
            top_recommendations.append(item)

        # Build Ineligible Schemes List with exact failed reasons
        ineligible_items: List[RecommendationItem] = []
        for idx, (scheme, elig_res) in enumerate(ineligible_candidates[:50], start=1):
            (
                score,
                matched,
                unmatched,
                not_eval,
                rec_reasons,
                breakdown,
            ) = cls.evaluate_soft_fit(scheme, profile, elig_res, policy=policy)

            passed_reasons = [rule.reason for rule in elig_res.hard_rules_passed]
            failed_reasons = [rule.reason for rule in elig_res.hard_rules_failed] or elig_res.failed_rules
            unknown_reasons = [rule.reason for rule in elig_res.unknown_eligibility_rules]

            ineligible_items.append(RecommendationItem(
                rank=idx,
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                eligibility_status=elig_res.status.value,
                score=0.0,  # Invariant: Ineligible scheme must NEVER receive an affirmative fit score
                eligible=False,
                match_tier="INELIGIBLE",
                scoring_policy_version=policy.policy_version,
                data_quality_score=compute_scheme_quality_score(scheme),
                financial_health_status=fin_health_status,
                financial_health_advisory=fin_health_advisory,
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
                is_direct_portal_scheme=(scheme.application_route == "DIRECT_PORTAL" or not bool(getattr(scheme, "partner_mappings", None))),
                has_verified_partner_mapping=bool(getattr(scheme, "partner_mappings", None)),
                application_channel="CHANNEL_PARTNER_LOCATOR" if bool(getattr(scheme, "partner_mappings", None)) else "OFFICIAL_DIRECT_PORTAL",
                financial_category=scheme.financial_category,
                is_credit_scheme=scheme.is_credit_scheme,
                calculator_applicable=scheme.calculator_applicable,
                financial_assistance_summary=scheme.financial_assistance_summary,
                short_description=scheme.short_description or scheme.purpose,
                purpose=scheme.purpose or scheme.short_description,
                max_loan_amount=float(scheme.max_loan_amount) if scheme.max_loan_amount is not None else None,
                interest_rate=scheme.interest_rate,
                repayment_period_max_months=scheme.repayment_period_max_months,
                subsidy_percentage=float(scheme.subsidy_percentage) if scheme.subsidy_percentage is not None else None,
                grant_amount=float(scheme.grant_amount) if scheme.grant_amount is not None else None,
                **_get_scheme_fin_details(scheme)
            ))

        # Build Insufficient Information Schemes List
        insufficient_items: List[RecommendationItem] = []
        for idx, (scheme, elig_res) in enumerate(insufficient_candidates[:50], start=1):
            (
                score,
                matched,
                unmatched,
                not_eval,
                rec_reasons,
                breakdown,
            ) = cls.evaluate_soft_fit(scheme, profile, elig_res, policy=policy)

            passed_reasons = [rule.reason for rule in elig_res.hard_rules_passed]
            unknown_reasons = [rule.reason for rule in elig_res.unknown_eligibility_rules] or elig_res.missing_information

            insufficient_items.append(RecommendationItem(
                rank=idx,
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                eligibility_status=elig_res.status.value,
                score=score,
                eligible=False,
                match_tier="INSUFFICIENT_INFORMATION",
                scoring_policy_version=policy.policy_version,
                data_quality_score=compute_scheme_quality_score(scheme),
                financial_health_status=fin_health_status,
                financial_health_advisory=fin_health_advisory,
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
                is_direct_portal_scheme=(scheme.application_route == "DIRECT_PORTAL" or not bool(getattr(scheme, "partner_mappings", None))),
                has_verified_partner_mapping=bool(getattr(scheme, "partner_mappings", None)),
                application_channel="CHANNEL_PARTNER_LOCATOR" if bool(getattr(scheme, "partner_mappings", None)) else "OFFICIAL_DIRECT_PORTAL",
                financial_category=scheme.financial_category,
                is_credit_scheme=scheme.is_credit_scheme,
                calculator_applicable=scheme.calculator_applicable,
                financial_assistance_summary=scheme.financial_assistance_summary,
                short_description=scheme.short_description or scheme.purpose,
                purpose=scheme.purpose or scheme.short_description,
                max_loan_amount=float(scheme.max_loan_amount) if scheme.max_loan_amount is not None else None,
                interest_rate=scheme.interest_rate,
                repayment_period_max_months=scheme.repayment_period_max_months,
                subsidy_percentage=float(scheme.subsidy_percentage) if scheme.subsidy_percentage is not None else None,
                grant_amount=float(scheme.grant_amount) if scheme.grant_amount is not None else None,
                **_get_scheme_fin_details(scheme)
            ))

        # Build Conditional Schemes List
        conditional_items: List[RecommendationItem] = []
        for idx, (scheme, elig_res) in enumerate(conditional_candidates[:50], start=1):
            (
                score,
                matched,
                unmatched,
                not_eval,
                rec_reasons,
                breakdown,
            ) = cls.evaluate_soft_fit(scheme, profile, elig_res, policy=policy)

            passed_reasons = [rule.reason for rule in elig_res.hard_rules_passed]
            conditional_reasons = elig_res.explanations or [rule.reason for rule in elig_res.hard_rules_passed]

            conditional_items.append(RecommendationItem(
                rank=idx,
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                eligibility_status=elig_res.status.value,
                score=score,
                eligible=False,
                match_tier="CONDITIONAL",
                scoring_policy_version=policy.policy_version,
                data_quality_score=compute_scheme_quality_score(scheme),
                financial_health_status=fin_health_status,
                financial_health_advisory=fin_health_advisory,
                matched_rules=passed_reasons,
                failed_rules=[],
                missing_information=[],
                matched_factors=matched,
                unmatched_factors=unmatched,
                not_evaluated_factors=not_eval,
                eligibility_reasons=conditional_reasons,
                recommendation_reasons=rec_reasons,
                score_breakdown=breakdown,
                ministry=scheme.ministry,
                source_organization=scheme.source_organization,
                official_portal=scheme.official_portal,
                application_url=scheme.application_url,
                official_source_url=scheme.official_source_url,
                source_document=scheme.source_document,
                is_direct_portal_scheme=(scheme.application_route == "DIRECT_PORTAL" or not bool(getattr(scheme, "partner_mappings", None))),
                has_verified_partner_mapping=bool(getattr(scheme, "partner_mappings", None)),
                application_channel="CHANNEL_PARTNER_LOCATOR" if bool(getattr(scheme, "partner_mappings", None)) else "OFFICIAL_DIRECT_PORTAL",
                financial_category=scheme.financial_category,
                is_credit_scheme=scheme.is_credit_scheme,
                calculator_applicable=scheme.calculator_applicable,
                financial_assistance_summary=scheme.financial_assistance_summary,
                short_description=scheme.short_description or scheme.purpose,
                purpose=scheme.purpose or scheme.short_description,
                max_loan_amount=float(scheme.max_loan_amount) if scheme.max_loan_amount is not None else None,
                interest_rate=scheme.interest_rate,
                repayment_period_max_months=scheme.repayment_period_max_months,
                subsidy_percentage=float(scheme.subsidy_percentage) if scheme.subsidy_percentage is not None else None,
                grant_amount=float(scheme.grant_amount) if scheme.grant_amount is not None else None,
                key_conditions=conditional_reasons,
                **_get_scheme_fin_details(scheme)
            ))

        # Profile Summary
        profile_summary = {
            k: v for k, v in profile.model_dump().items() if v is not None
        }

        return RecommendationResponse(
            profile_summary=profile_summary,
            scoring_policy_version=policy.policy_version,
            recommendation_trace_id=trace_id,
            candidate_shortlist_count=evaluated_count,
            evaluated_scheme_count=evaluated_count,
            eligible_scheme_count=eligible_count,
            excluded_scheme_count=ineligible_cnt,
            insufficient_info_scheme_count=insufficient_cnt,
            conditional_scheme_count=conditional_cnt,
            not_applicable_scheme_count=not_applicable_cnt,
            recommendations=top_recommendations,
            ineligible_schemes=ineligible_items,
            insufficient_info_schemes=insufficient_items,
            conditional_schemes=conditional_items,
            not_applicable_schemes=[],
            missing_profile_fields=missing_fields,
        )

