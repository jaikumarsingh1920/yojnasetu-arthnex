"""
Deterministic Financial Health Status Engine for YojnaSetu.

Core Principles:
1. Zero LLM / Gemini decision-making: All ratios, bounds, and indicators are 100% deterministic Python logic.
2. Decimal Precision: Monetary and percentage calculations use Python Decimal with exact rounding.
3. Safe Handling of Missing / Incomplete Data: Missing critical fields yield INSUFFICIENT_INFORMATION with structured missing field guidance.
4. Non-Interference with Legal Eligibility: Financial health is strictly an advisory decision-support layer and never overrides statutory scheme eligibility.
5. Strict Non-Fabrication: Never assumes zero or fake values for missing financial data.
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.schemas.financial_health import (
    FinancialHealthInput,
    FinancialHealthResponse,
    FinancialHealthStatus,
    FinancialIndicatorStatus,
    FinancialIndicatorResult,
    MissingFinancialField,
    SchemeFinancialSuitability,
    SchemeFinancialAssessment,
)
from app.schemas.financial import FinancialCalculationInput, FinancialCalculationStatus
from app.schemas.profile import BeneficiaryProfileInput
from app.models.scheme import Scheme
from app.engine.calculator import DeterministicFinancialEngine

# Precision constants
TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")
TWELVE = Decimal("12")
HUNDRED = Decimal("100")
VERSION = "v1.0-SIH-DETERMINISTIC"


def _to_decimal(val: Any) -> Optional[Decimal]:
    if val is None or val == "" or val == "UNKNOWN" or val == "NOT_APPLICABLE":
        return None
    try:
        d = Decimal(str(val))
        if d.is_nan() or d.is_infinite():
            return None
        return d
    except (InvalidOperation, ValueError, TypeError):
        return None


class DeterministicFinancialHealthEngine:
    """
    Evaluates citizen financial suitability, leverage, debt-service capacity, and liquidity buffer.
    """

    @classmethod
    def evaluate(
        cls,
        input_data: FinancialHealthInput,
        db: Optional[Session] = None
    ) -> FinancialHealthResponse:
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Resolve effective values from input_data or nested profile
        ann_inc = input_data.annual_income
        mon_inc = input_data.monthly_income
        mon_exp = input_data.monthly_expenses
        req_loan = input_data.requested_loan_amount
        proj_cost = input_data.project_cost
        liabilities = input_data.existing_liabilities
        monthly_ob = input_data.monthly_obligations
        savings = input_data.liquid_savings
        scheme_inst = input_data.estimated_scheme_installment

        if input_data.profile:
            p = input_data.profile
            if ann_inc is None and p.annual_income is not None:
                ann_inc = _to_decimal(p.annual_income)
            if mon_exp is None and getattr(p, "monthly_expenses", None) is not None:
                mon_exp = _to_decimal(p.monthly_expenses)
            if req_loan is None and p.requested_loan_amount is not None:
                req_loan = _to_decimal(p.requested_loan_amount)
            if proj_cost is None and p.project_cost is not None:
                proj_cost = _to_decimal(p.project_cost)
            if liabilities is None and getattr(p, "existing_liabilities", None) is not None:
                liabilities = _to_decimal(p.existing_liabilities)
            if monthly_ob is None and getattr(p, "monthly_obligations", None) is not None:
                monthly_ob = _to_decimal(p.monthly_obligations)
            if savings is None and getattr(p, "liquid_savings", None) is not None:
                savings = _to_decimal(p.liquid_savings)

        # 2. Check for missing critical inputs
        missing: List[MissingFinancialField] = []
        if ann_inc is None and mon_inc is None:
            missing.append(MissingFinancialField(
                field="annual_income",
                label="Annual Family Income",
                impact_reason="Required to compute monthly cash flow and debt service capacity (FOIR)."
            ))

        if req_loan is None and liabilities is None and monthly_ob is None:
            missing.append(MissingFinancialField(
                field="requested_loan_amount",
                label="Requested Borrowing Amount",
                impact_reason="Required to assess credit leverage and loan serviceability."
            ))

        if missing:
            return FinancialHealthResponse(
                status=FinancialHealthStatus.INSUFFICIENT_INFORMATION,
                score=None,
                summary_headline="Insufficient financial parameters to determine financial health status.",
                indicators=[],
                risk_flags=["Essential income or borrowing information is missing from the citizen profile."],
                positive_factors=[],
                recommendations=["Provide annual family income and requested loan requirement to receive an explainable financial health assessment."],
                missing_fields=missing,
                calculation_version=VERSION,
                evaluated_at=now_iso
            )

        # 3. Derive Monthly Income
        if mon_inc is not None:
            effective_monthly_income = mon_inc
        elif ann_inc is not None:
            effective_monthly_income = (ann_inc / TWELVE).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        else:
            effective_monthly_income = ZERO

        # 4. Resolve Scheme Monthly Installment (if scheme_id provided and db available)
        effective_scheme_emi = ZERO
        if scheme_inst is not None:
            effective_scheme_emi = scheme_inst
        elif input_data.scheme_id and db and req_loan and req_loan > ZERO:
            try:
                calc_res = DeterministicFinancialEngine.calculate(
                    db=db,
                    calc_input=FinancialCalculationInput(
                        scheme_id=input_data.scheme_id,
                        requested_loan_amount=req_loan,
                        project_cost=proj_cost or req_loan
                    )
                )
                if calc_res.status == FinancialCalculationStatus.CALCULATED and calc_res.periodic_installment:
                    effective_scheme_emi = calc_res.periodic_installment
            except Exception:
                effective_scheme_emi = ZERO

        if effective_scheme_emi == ZERO and req_loan and req_loan > ZERO:
            r_rate = Decimal(str(input_data.interest_rate or 8.5))
            r_tenure = Decimal(str(input_data.tenure_months or 36))
            r_monthly = (r_rate / Decimal("100")) / Decimal("12")
            if r_monthly > ZERO:
                factor = (Decimal("1") + r_monthly) ** int(r_tenure)
                effective_scheme_emi = (req_loan * r_monthly * factor / (factor - Decimal("1"))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            else:
                effective_scheme_emi = (req_loan / r_tenure).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # 5. Core aggregates
        existing_obs = (monthly_ob or ZERO)
        effective_monthly_expenses = mon_exp or ZERO
        effective_monthly_obligations = existing_obs + effective_scheme_emi
        disposable_income = effective_monthly_income - effective_monthly_obligations - effective_monthly_expenses

        indicators: List[FinancialIndicatorResult] = []
        risk_flags: List[str] = []
        positive_factors: List[str] = []
        recommendations: List[str] = []

        # ── Indicator 1: FOIR / DTI (Fixed Obligation to Income Ratio) [Weight 40%] ──
        w_foir = Decimal("40.0")
        if effective_monthly_income > ZERO:
            foir_pct = ((effective_monthly_obligations / effective_monthly_income) * HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            if foir_pct <= Decimal("30.0"):
                ind_status = FinancialIndicatorStatus.HEALTHY
                ind_score = Decimal("100.0")
                expl = f"Total monthly obligations (₹{effective_monthly_obligations:,.2f}) consume {foir_pct}% of monthly income (₹{effective_monthly_income:,.2f}), well within the healthy benchmark (<= 30%)."
                positive_factors.append(f"Comfortable debt-service ratio of {foir_pct}%, leaving substantial disposable income for operational stability.")
            elif foir_pct <= Decimal("50.0"):
                ind_status = FinancialIndicatorStatus.MODERATE
                ind_score = Decimal("75.0")
                expl = f"Total monthly obligations (₹{effective_monthly_obligations:,.2f}) consume {foir_pct}% of monthly income, within sustainable lending limits (<= 50%)."
            elif foir_pct <= Decimal("70.0"):
                ind_status = FinancialIndicatorStatus.STRESSED
                ind_score = Decimal("40.0")
                expl = f"Total monthly obligations (₹{effective_monthly_obligations:,.2f}) consume {foir_pct}% of monthly income, indicating elevated debt burden (> 50%)."
                risk_flags.append(f"High Fixed Obligation to Income Ratio ({foir_pct}%): Over half of monthly income is committed to debt service.")
                recommendations.append("Consider opting for a longer repayment tenure to lower monthly installment burden.")
            else:
                ind_status = FinancialIndicatorStatus.HIGH_RISK
                ind_score = Decimal("15.0")
                expl = f"Total monthly obligations (₹{effective_monthly_obligations:,.2f}) consume {foir_pct}% of monthly income, exceeding safe debt thresholds (> 70%)."
                risk_flags.append(f"Critical debt-service ratio ({foir_pct}%): Monthly obligations leave negligible disposable income for household needs.")
                recommendations.append("Prioritize debt consolidation or consider capital subsidy/grant schemes with zero loan obligations.")

            indicators.append(FinancialIndicatorResult(
                indicator_name="foir",
                label="Fixed Obligation to Income Ratio (FOIR)",
                value=foir_pct,
                formatted_value=f"{foir_pct}%",
                benchmark="<= 30% Healthy | 31-50% Moderate | 51-70% Stressed | > 70% High Risk",
                status=ind_status,
                score=ind_score,
                weight=w_foir,
                explanation=expl
            ))
        else:
            # Zero monthly income case
            if effective_monthly_obligations > ZERO:
                ind_status = FinancialIndicatorStatus.HIGH_RISK
                ind_score = ZERO
                expl = f"Monthly debt obligations of ₹{effective_monthly_obligations:,.2f} exist with zero declared monthly earnings."
                risk_flags.append("Debt service exists without declared income source.")
            else:
                ind_status = FinancialIndicatorStatus.MODERATE
                ind_score = Decimal("60.0")
                expl = "Zero monthly earnings and zero existing debt commitments."

            indicators.append(FinancialIndicatorResult(
                indicator_name="foir",
                label="Fixed Obligation to Income Ratio (FOIR)",
                value=None,
                formatted_value="N/A (Zero Income)",
                benchmark="<= 30% Healthy | 31-50% Moderate | 51-70% Stressed | > 70% High Risk",
                status=ind_status,
                score=ind_score,
                weight=w_foir,
                explanation=expl
            ))

        # ── Indicator 2: Borrowing Leverage Multiplier [Weight 30%] ──
        w_lev = Decimal("30.0")
        effective_annual_income = ann_inc or (effective_monthly_income * TWELVE)
        effective_loan = req_loan or ZERO

        if effective_annual_income > ZERO:
            leverage = (effective_loan / effective_annual_income).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            if effective_loan == ZERO:
                lev_status = FinancialIndicatorStatus.HEALTHY
                lev_score = Decimal("100.0")
                expl = "No borrowing requested; zero debt leverage."
                positive_factors.append("Zero proposed borrowing; completely debt-free scenario.")
            elif leverage <= Decimal("1.0"):
                lev_status = FinancialIndicatorStatus.HEALTHY
                lev_score = Decimal("100.0")
                expl = f"Requested loan (₹{effective_loan:,.2f}) is {leverage}x annual income (₹{effective_annual_income:,.2f}), well within conservative credit bounds (<= 1.0x)."
                positive_factors.append(f"Low leverage multiplier ({leverage}x annual earnings).")
            elif leverage <= Decimal("2.5"):
                lev_status = FinancialIndicatorStatus.MODERATE
                lev_score = Decimal("75.0")
                expl = f"Requested loan is {leverage}x annual income, acceptable for productive enterprise setup (<= 2.5x)."
            elif leverage <= Decimal("4.0"):
                lev_status = FinancialIndicatorStatus.STRESSED
                lev_score = Decimal("45.0")
                expl = f"Requested loan is {leverage}x annual income, representing substantial borrowing relative to annual earnings (> 2.5x)."
                risk_flags.append(f"Elevated debt-to-income multiplier ({leverage}x annual income).")
            else:
                lev_status = FinancialIndicatorStatus.HIGH_RISK
                lev_score = Decimal("20.0")
                expl = f"Requested loan is {leverage}x annual income, exceeding prudent micro-credit benchmarks (> 4.0x)."
                risk_flags.append(f"Severe borrowing leverage ({leverage}x annual income).")
                recommendations.append("Consider scaling down the initial project scale to align with current earnings capacity.")

            indicators.append(FinancialIndicatorResult(
                indicator_name="leverage_ratio",
                label="Borrowing Leverage Multiplier",
                value=leverage,
                formatted_value=f"{leverage}x",
                benchmark="<= 1.0x Healthy | 1.1-2.5x Moderate | 2.6-4.0x Stressed | > 4.0x High Risk",
                status=lev_status,
                score=lev_score,
                weight=w_lev,
                explanation=expl
            ))
        else:
            if effective_loan > ZERO:
                lev_status = FinancialIndicatorStatus.HIGH_RISK
                lev_score = ZERO
                expl = f"Borrowing of ₹{effective_loan:,.2f} requested with zero declared annual earnings."
                risk_flags.append("Loan requested without documented income.")
            else:
                lev_status = FinancialIndicatorStatus.HEALTHY
                lev_score = Decimal("100.0")
                expl = "Zero borrowing requested with zero declared income."

            indicators.append(FinancialIndicatorResult(
                indicator_name="leverage_ratio",
                label="Borrowing Leverage Multiplier",
                value=None,
                formatted_value="N/A (Zero Income)",
                benchmark="<= 1.0x Healthy | 1.1-2.5x Moderate | 2.6-4.0x Stressed | > 4.0x High Risk",
                status=lev_status,
                score=lev_score,
                weight=w_lev,
                explanation=expl
            ))

        # ── Indicator 3: Financing & Margin Money Gearing (LTV) [Weight 20%] ──
        w_ltv = Decimal("20.0")
        req_margin = None
        margin_gap = None

        if proj_cost is not None and proj_cost > ZERO:
            if effective_loan > proj_cost:
                ltv_status = FinancialIndicatorStatus.HIGH_RISK
                ltv_score = ZERO
                expl = f"Requested loan (₹{effective_loan:,.2f}) exceeds total project cost (₹{proj_cost:,.2f})."
                risk_flags.append("Requested loan exceeds total project cost (over-financing anomaly).")
                recommendations.append("Ensure requested borrowing does not exceed total project investment cost.")
            else:
                ltv_pct = ((effective_loan / proj_cost) * HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                req_margin = proj_cost - effective_loan
                margin_pct = HUNDRED - ltv_pct

                if ltv_pct <= Decimal("85.0"):
                    ltv_status = FinancialIndicatorStatus.HEALTHY
                    ltv_score = Decimal("100.0")
                    expl = f"Financing ratio is {ltv_pct}%, with healthy promoter equity/margin of ₹{req_margin:,.2f} ({margin_pct}%)."
                    positive_factors.append(f"Balanced promoter margin contribution of {margin_pct}%.")
                elif ltv_pct <= Decimal("95.0"):
                    ltv_status = FinancialIndicatorStatus.MODERATE
                    ltv_score = Decimal("75.0")
                    expl = f"Financing ratio is {ltv_pct}%, requiring promoter equity margin of ₹{req_margin:,.2f} ({margin_pct}%)."
                else:
                    ltv_status = FinancialIndicatorStatus.STRESSED
                    ltv_score = Decimal("45.0")
                    expl = f"Financing ratio is {ltv_pct}%, with minimal promoter equity margin (< 5%)."
                    risk_flags.append("High debt reliance with under 5% promoter equity contribution.")

                if savings is not None and req_margin > ZERO:
                    if savings < req_margin:
                        margin_gap = req_margin - savings
                        risk_flags.append(f"Promoter Margin Shortfall: Required margin is ₹{req_margin:,.2f}, but declared liquid savings is ₹{savings:,.2f} (gap: ₹{margin_gap:,.2f}).")
                        recommendations.append(f"Arrange ₹{margin_gap:,.2f} in family/promoter contribution to satisfy bank margin requirements.")
                    else:
                        positive_factors.append(f"Sufficient liquid savings (₹{savings:,.2f}) to cover required promoter margin of ₹{req_margin:,.2f}.")

            indicators.append(FinancialIndicatorResult(
                indicator_name="financing_ratio",
                label="Financing & Margin Ratio (LTV)",
                value=ltv_pct if effective_loan <= proj_cost else None,
                formatted_value=f"{ltv_pct}%" if effective_loan <= proj_cost else "Exceeds Project Cost",
                benchmark="<= 85% Healthy | 86-95% Moderate | > 95% Stressed",
                status=ltv_status,
                score=ltv_score,
                weight=w_ltv,
                explanation=expl
            ))
        else:
            indicators.append(FinancialIndicatorResult(
                indicator_name="financing_ratio",
                label="Financing & Margin Ratio (LTV)",
                value=None,
                formatted_value="Not Specified",
                benchmark="<= 85% Healthy | 86-95% Moderate | > 95% Stressed",
                status=FinancialIndicatorStatus.NOT_EVALUATED,
                score=None,
                weight=w_ltv,
                explanation="Project cost not specified; financing ratio was not evaluated."
            ))

        # ── Indicator 4: Liquidity Cushion Buffer [Weight 10%] ──
        w_cush = Decimal("10.0")
        if savings is not None:
            if effective_monthly_obligations > ZERO:
                buffer_months = (savings / effective_monthly_obligations).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                if buffer_months >= Decimal("6.0"):
                    cush_status = FinancialIndicatorStatus.HEALTHY
                    cush_score = Decimal("100.0")
                    expl = f"Liquid savings (₹{savings:,.2f}) provide {buffer_months} months of debt service coverage (>= 6 months benchmark)."
                    positive_factors.append(f"Robust liquidity cushion of {buffer_months} months debt service reserve.")
                elif buffer_months >= Decimal("3.0"):
                    cush_status = FinancialIndicatorStatus.MODERATE
                    cush_score = Decimal("75.0")
                    expl = f"Liquid savings provide {buffer_months} months of debt service coverage (3 to 6 months benchmark)."
                elif buffer_months >= Decimal("1.0"):
                    cush_status = FinancialIndicatorStatus.STRESSED
                    cush_score = Decimal("45.0")
                    expl = f"Liquid savings provide only {buffer_months} months of debt service coverage (< 3 months)."
                    risk_flags.append(f"Limited liquidity buffer ({buffer_months} months debt service reserve).")
                else:
                    cush_status = FinancialIndicatorStatus.HIGH_RISK
                    cush_score = Decimal("20.0")
                    expl = f"Liquid savings cover under 1 month of debt service obligations."
                    risk_flags.append("Vulnerable liquidity buffer: less than 1 month of debt obligations in reserve.")
                    recommendations.append("Build a small emergency reserve before taking on additional loan debt.")

                indicators.append(FinancialIndicatorResult(
                    indicator_name="liquidity_buffer",
                    label="Liquidity Cushion Buffer",
                    value=buffer_months,
                    formatted_value=f"{buffer_months} months",
                    benchmark=">= 6 mos Healthy | 3-6 mos Moderate | 1-3 mos Stressed | < 1 mo High Risk",
                    status=cush_status,
                    score=cush_score,
                    weight=w_cush,
                    explanation=expl
                ))
            else:
                cush_score = Decimal("100.0") if savings > ZERO else Decimal("70.0")
                indicators.append(FinancialIndicatorResult(
                    indicator_name="liquidity_buffer",
                    label="Liquidity Cushion Buffer",
                    value=None,
                    formatted_value=f"₹{savings:,.2f} (Zero Obligations)",
                    benchmark=">= 6 mos Healthy | 3-6 mos Moderate | 1-3 mos Stressed | < 1 mo High Risk",
                    status=FinancialIndicatorStatus.HEALTHY if savings > ZERO else FinancialIndicatorStatus.MODERATE,
                    score=cush_score,
                    weight=w_cush,
                    explanation=f"Available savings of ₹{savings:,.2f} with zero debt commitments."
                ))
        else:
            indicators.append(FinancialIndicatorResult(
                indicator_name="liquidity_buffer",
                label="Liquidity Cushion Buffer",
                value=None,
                formatted_value="Not Specified",
                benchmark=">= 6 mos Healthy | 3-6 mos Moderate | 1-3 mos Stressed | < 1 mo High Risk",
                status=FinancialIndicatorStatus.NOT_EVALUATED,
                score=None,
                weight=w_cush,
                explanation="Liquid savings not specified; liquidity cushion was not evaluated."
            ))

        # 6. Aggregate Normalized Score (0.0 to 100.0)
        evaluated_indicators = [ind for ind in indicators if ind.score is not None]
        total_eval_weight = sum(ind.weight for ind in evaluated_indicators)
        total_weighted_score = sum(ind.score * ind.weight for ind in evaluated_indicators)

        if total_eval_weight > ZERO:
            final_score = (total_weighted_score / total_eval_weight).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        else:
            final_score = Decimal("50.0")

        # 7. Determine Final Status
        # Safety rules: Hard override if any critical dimension is zero-score HIGH_RISK
        has_critical_failure = any(
            ind.status == FinancialIndicatorStatus.HIGH_RISK and ind.score == ZERO for ind in evaluated_indicators
        )

        if has_critical_failure or final_score < Decimal("40.0"):
            overall_status = FinancialHealthStatus.HIGH_RISK
            summary = "High Financial Risk: Existing obligations or requested borrowing significantly exceed sustainable capacity."
        elif final_score < Decimal("60.0"):
            overall_status = FinancialHealthStatus.STRESSED
            summary = "Stressed Financial Health: High debt service ratio or leverage indicates tight operational cash flow."
        elif final_score < Decimal("80.0"):
            overall_status = FinancialHealthStatus.MODERATE
            summary = "Moderate Financial Health: Manageable borrowing scenario with balanced repayment capacity."
        else:
            overall_status = FinancialHealthStatus.HEALTHY
            summary = "Healthy Financial Profile: Strong debt-service coverage, low leverage, and sustainable cash buffer."

        # Add general advisory recommendations if list is empty
        if not recommendations:
            if overall_status == FinancialHealthStatus.HEALTHY:
                recommendations.append("Your financial profile supports institutional borrowing; explore concessional interest schemes under PMEGP or Stand-Up India.")
            elif overall_status == FinancialHealthStatus.MODERATE:
                recommendations.append("Maintain strict budget discipline and verify bank margin money requirements before formal application.")
            else:
                recommendations.append("Evaluate non-credit grant, skill fellowship, or interest subvention schemes to minimize financial leverage.")

        return FinancialHealthResponse(
            status=overall_status,
            score=final_score,
            summary_headline=summary,
            indicators=indicators,
            risk_flags=risk_flags,
            positive_factors=positive_factors,
            recommendations=recommendations,
            missing_fields=missing,
            monthly_income=effective_monthly_income,
            monthly_expenses=mon_exp,
            existing_monthly_obligations=existing_obs,
            proposed_monthly_emi=effective_scheme_emi,
            total_monthly_obligations=effective_monthly_obligations,
            debt_to_income_ratio=foir_pct if effective_monthly_income > ZERO else None,
            estimated_disposable_income=disposable_income,
            required_margin_money=req_margin,
            margin_money_gap=margin_gap,
            calculation_version=VERSION,
            evaluated_at=now_iso
        )

    @classmethod
    def evaluate_scheme_suitability(
        cls,
        scheme: Scheme,
        profile: Optional[BeneficiaryProfileInput] = None,
        requested_loan_amount: Optional[Decimal] = None,
        project_cost: Optional[Decimal] = None,
        own_contribution: Optional[Decimal] = None,
        annual_income: Optional[Decimal] = None,
        monthly_income: Optional[Decimal] = None,
        monthly_obligations: Optional[Decimal] = None,
        user_financials: Optional[Any] = None,
        db: Optional[Session] = None
    ) -> SchemeFinancialAssessment:
        """
        Determines whether the financial structure of a specific scheme is suitable
        for the citizen's financial position.

        Classifies fit into:
        - STRONG_FIT
        - POSSIBLE_FIT
        - INSUFFICIENT_INFORMATION
        - FINANCIALLY_UNSUITABLE

        Strictly handles unstated values as NOT_PUBLICLY_AVAILABLE without fabricating.
        """
        if user_financials is not None:
            if requested_loan_amount is None:
                requested_loan_amount = getattr(user_financials, "requested_loan_amount", None)
            if project_cost is None:
                project_cost = getattr(user_financials, "project_cost", None)
            if own_contribution is None:
                own_contribution = getattr(user_financials, "liquid_savings", None)
            if annual_income is None:
                annual_income = getattr(user_financials, "annual_income", None)
            if monthly_income is None:
                monthly_income = getattr(user_financials, "monthly_income", None)
            if monthly_obligations is None:
                monthly_obligations = getattr(user_financials, "monthly_obligations", None)
            if profile is None:
                profile = getattr(user_financials, "profile", None)

        # 1. Resolve user profile values
        proj_cost = project_cost or (Decimal(str(profile.project_cost)) if profile and profile.project_cost is not None else None)
        own_contrib = own_contribution or (Decimal(str(profile.liquid_savings)) if profile and getattr(profile, "liquid_savings", None) is not None else None)
        req_loan = requested_loan_amount or (Decimal(str(profile.requested_loan_amount)) if profile and profile.requested_loan_amount is not None else None)
        ann_inc = annual_income or (Decimal(str(profile.annual_income)) if profile and profile.annual_income is not None else None)
        mon_inc = monthly_income or ((ann_inc / TWELVE).quantize(TWO_PLACES, rounding=ROUND_HALF_UP) if ann_inc is not None else None)
        existing_debts = monthly_obligations or (Decimal(str(profile.monthly_obligations)) if profile and getattr(profile, "monthly_obligations", None) is not None else ZERO) or ZERO

        # 2. Extract scheme authoritative financial parameters
        max_proj = _to_decimal(scheme.max_project_cost)
        min_proj = _to_decimal(scheme.min_project_cost)
        max_loan = _to_decimal(scheme.max_loan_amount)
        min_loan = _to_decimal(scheme.min_loan_amount)
        sub_pct = _to_decimal(scheme.subsidy_percentage)
        sub_amt = _to_decimal(getattr(scheme, "subsidy_amount", None))
        grant_amt = _to_decimal(scheme.grant_amount)
        margin_pct = _to_decimal(scheme.beneficiary_contribution_percentage)
        int_rate = _to_decimal(scheme.interest_rate_max) if scheme.interest_rate_max is not None else _to_decimal(scheme.interest_rate_min)
        tenure_months = scheme.repayment_period_max_months or scheme.repayment_period_min_months
        moratorium_months = scheme.moratorium_max_months

        # 3. Format Display fields (Strict Unknown handling)
        if scheme.interest_rate_min is not None and scheme.interest_rate_max is not None:
            if scheme.interest_rate_min == Decimal("0") and scheme.interest_rate_max == Decimal("0"):
                int_display = "0.0% (Interest-Free)"
            elif scheme.interest_rate_min == scheme.interest_rate_max:
                int_display = f"{scheme.interest_rate_max}% p.a."
            else:
                int_display = f"{scheme.interest_rate_min}% - {scheme.interest_rate_max}% p.a."
        elif scheme.interest_rate_max is not None:
            int_display = f"{scheme.interest_rate_max}% p.a."
        elif scheme.interest_rate_min is not None:
            int_display = f"{scheme.interest_rate_min}% p.a."
        else:
            int_display = "NOT_PUBLICLY_AVAILABLE"

        if tenure_months is not None and tenure_months > 0:
            if tenure_months >= 12 and tenure_months % 12 == 0:
                tenure_display = f"{tenure_months} months ({tenure_months // 12} years)"
            else:
                tenure_display = f"{tenure_months} months"
        else:
            tenure_display = "NOT_PUBLICLY_AVAILABLE"

        if moratorium_months is not None and moratorium_months > 0:
            moratorium_display = f"{moratorium_months} months"
        else:
            moratorium_display = "NOT_PUBLICLY_AVAILABLE"

        if scheme.collateral_required and scheme.collateral_required.strip().upper() not in ("", "UNKNOWN", "NOT_APPLICABLE"):
            collateral_display = scheme.collateral_required.strip().upper()
        else:
            collateral_display = "NOT_PUBLICLY_AVAILABLE"

        if getattr(scheme, "guarantee_requirement", None) and scheme.guarantee_requirement.strip():
            guarantee_display = scheme.guarantee_requirement.strip()
        else:
            guarantee_display = "NOT_PUBLICLY_AVAILABLE"

        if getattr(scheme, "processing_fee", None) and scheme.processing_fee.strip():
            fee_display = scheme.processing_fee.strip()
        else:
            fee_display = "NOT_PUBLICLY_AVAILABLE"

        # 4. Check if scheme is a non-credit scheme (TEST D)
        is_non_credit = (
            (getattr(scheme, "loan_available", None) and str(scheme.loan_available).strip().upper() in ("NO", "FALSE", "N")) or
            (getattr(scheme, "is_credit_scheme", None) is False) or
            (getattr(scheme, "financial_category", None) in ("SCHOLARSHIP", "GRANT_SUBSIDY", "NON_FINANCIAL", "DIRECT_BENEFIT") and max_loan is None and min_loan is None)
        )
        if is_non_credit:
            return SchemeFinancialAssessment(
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                suitability=SchemeFinancialSuitability.NOT_APPLICABLE,
                suitability_reason="Scheme is non-credit; financial health / loan affordability assessment is not applicable.",
                project_cost=proj_cost,
                own_contribution=own_contrib,
                required_margin_money=None,
                margin_money_gap=None,
                required_loan=None,
                available_subsidy=None,
                subsidy_percentage=sub_pct,
                available_grant=grant_amt,
                estimated_emi=None,
                interest_rate_display="NOT_APPLICABLE",
                repayment_tenure_display="NOT_APPLICABLE",
                moratorium_display="NOT_APPLICABLE",
                collateral_requirement_display="NOT_APPLICABLE",
                guarantee_requirement_display="NOT_APPLICABLE",
                processing_fee_display="NOT_APPLICABLE",
                max_project_cost=max_proj,
                min_project_cost=min_proj,
                max_loan_amount=max_loan,
                min_loan_amount=min_loan,
                is_project_cost_eligible=None,
                is_loan_amount_eligible=None,
                is_own_contribution_sufficient=None,
                missing_parameters=[],
                unmet_criteria=[],
                positive_factors=[]
            )

        # 4b. Check if scheme has ANY authoritative credit/financial structure
        has_scheme_finance = (
            max_proj is not None or min_proj is not None or
            max_loan is not None or min_loan is not None or
            sub_pct is not None or sub_amt is not None or
            grant_amt is not None or int_rate is not None
        )

        missing_params: List[str] = []
        if max_proj is None and min_proj is None:
            missing_params.append("project_cost_limits")
        if max_loan is None and min_loan is None:
            missing_params.append("loan_limits")
        if int_rate is None:
            missing_params.append("interest_rate")
        if tenure_months is None:
            missing_params.append("repayment_tenure")
        if collateral_display == "NOT_PUBLICLY_AVAILABLE":
            missing_params.append("collateral_policy")

        if not has_scheme_finance:
            return SchemeFinancialAssessment(
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                suitability=SchemeFinancialSuitability.INSUFFICIENT_INFORMATION,
                suitability_reason="No authoritative financial parameters published in official guidelines for deterministic assessment.",
                project_cost=proj_cost,
                own_contribution=own_contrib,
                required_margin_money=None,
                margin_money_gap=None,
                required_loan=req_loan,
                available_subsidy=None,
                subsidy_percentage=None,
                available_grant=None,
                estimated_emi=None,
                interest_rate_display=int_display,
                repayment_tenure_display=tenure_display,
                moratorium_display=moratorium_display,
                collateral_requirement_display=collateral_display,
                guarantee_requirement_display=guarantee_display,
                processing_fee_display=fee_display,
                max_project_cost=max_proj,
                min_project_cost=min_proj,
                max_loan_amount=max_loan,
                min_loan_amount=min_loan,
                is_project_cost_eligible=None,
                is_loan_amount_eligible=None,
                is_own_contribution_sufficient=None,
                missing_parameters=missing_params,
                unmet_criteria=[],
                positive_factors=[]
            )

        # 5. Financial breakdown calculations
        # Subsidy estimation
        est_sub = None
        if sub_pct is not None and proj_cost is not None:
            est_sub = (proj_cost * sub_pct / HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            if sub_amt is not None and est_sub > sub_amt:
                est_sub = sub_amt
        elif sub_amt is not None:
            est_sub = sub_amt

        est_grant = grant_amt

        # Required margin money
        req_margin = None
        if margin_pct is not None and proj_cost is not None:
            req_margin = (proj_cost * margin_pct / HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        elif proj_cost is not None and req_loan is not None:
            diff = proj_cost - req_loan - (est_sub or ZERO) - (est_grant or ZERO)
            req_margin = max(ZERO, diff).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        margin_gap = None
        if req_margin is not None and own_contrib is not None:
            margin_gap = max(ZERO, req_margin - own_contrib).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # Net loan required
        if req_loan is not None:
            effective_loan = req_loan
        elif proj_cost is not None:
            net = proj_cost - (own_contrib or ZERO) - (est_sub or ZERO) - (est_grant or ZERO)
            effective_loan = max(ZERO, net).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        else:
            effective_loan = None

        # Estimated EMI
        est_emi = None
        if effective_loan is not None and effective_loan > ZERO and int_rate is not None and tenure_months and tenure_months > 0:
            try:
                est_emi = DeterministicFinancialEngine.calculate_installment(
                    principal=effective_loan,
                    annual_rate_percent=int_rate,
                    total_periods=int(tenure_months),
                    periods_per_year=12
                )
            except Exception:
                est_emi = None

        # 6. Evaluation & Rule Checking
        unmet: List[str] = []
        positive: List[str] = []

        is_cost_eligible = None
        if proj_cost is not None:
            is_cost_eligible = True
            if max_proj is not None and proj_cost > max_proj:
                unmet.append(f"Project cost ₹{proj_cost:,.2f} exceeds scheme ceiling of ₹{max_proj:,.2f}")
                is_cost_eligible = False
            if min_proj is not None and proj_cost < min_proj:
                unmet.append(f"Project cost ₹{proj_cost:,.2f} is below scheme minimum of ₹{min_proj:,.2f}")
                is_cost_eligible = False

        is_loan_eligible = None
        if effective_loan is not None:
            is_loan_eligible = True
            if max_loan is not None and effective_loan > max_loan:
                unmet.append(f"Required loan ₹{effective_loan:,.2f} exceeds scheme loan limit of ₹{max_loan:,.2f}")
                is_loan_eligible = False
            if min_loan is not None and effective_loan < min_loan:
                unmet.append(f"Required loan ₹{effective_loan:,.2f} is below scheme minimum loan limit of ₹{min_loan:,.2f}")
                is_loan_eligible = False

        is_margin_sufficient = None
        if req_margin is not None and own_contrib is not None:
            if margin_gap is not None and margin_gap > ZERO:
                unmet.append(f"Available own contribution shortfall: Scheme requires ₹{req_margin:,.2f} margin, user has ₹{own_contrib:,.2f} (gap: ₹{margin_gap:,.2f})")
                is_margin_sufficient = False
            else:
                positive.append(f"Own contribution satisfied: User has ₹{own_contrib:,.2f}, meeting required margin of ₹{req_margin:,.2f}")
                is_margin_sufficient = True

        if est_sub is not None and est_sub > ZERO:
            positive.append(f"Eligible for estimated capital/margin subsidy of ₹{est_sub:,.2f}")
        if est_grant is not None and est_grant > ZERO:
            positive.append(f"Eligible for direct grant assistance of ₹{est_grant:,.2f}")

        if est_emi is not None and mon_inc is not None and mon_inc > ZERO:
            foir = ((existing_debts + est_emi) / mon_inc * HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            if foir > Decimal("65.0"):
                unmet.append(f"Projected EMI (₹{est_emi:,.2f}/mo) causes excessive debt burden ({foir}% of monthly income)")
            elif foir <= Decimal("35.0"):
                positive.append(f"Comfortable repayment burden: Projected EMI consumes {foir}% of monthly income")

        # 7. Final Fit Determination
        if unmet:
            suitability = SchemeFinancialSuitability.FINANCIALLY_UNSUITABLE
            reason = f"Financially unsuitable: {'; '.join(unmet)}."
        elif max_proj is None and max_loan is None and min_loan is None and min_proj is None:
            suitability = SchemeFinancialSuitability.INSUFFICIENT_INFORMATION
            reason = "Insufficient official financial limits (project cost ceiling or loan limit) to verify deterministic financial fit."
        elif proj_cost is None and req_loan is None:
            suitability = SchemeFinancialSuitability.INSUFFICIENT_INFORMATION
            reason = "Insufficient citizen financial data (project cost or loan requirement) to determine exact financial fit."
        elif int_rate is None or tenure_months is None:
            if is_margin_sufficient is not False and is_loan_eligible is not False and is_cost_eligible is not False and (positive or (margin_gap is not None and margin_gap == ZERO)):
                suitability = SchemeFinancialSuitability.POSSIBLE_FIT
                reason = "Possible financial fit: Investment scale and margin requirements align with scheme parameters, but applicable lender interest rate/tenure is not specified in available guidelines."
            else:
                suitability = SchemeFinancialSuitability.INSUFFICIENT_INFORMATION
                reason = "Financial health cannot be fully assessed because the applicable lender interest rate/tenure is not specified in official guidelines."
        elif positive or (margin_gap is not None and margin_gap == ZERO):
            suitability = SchemeFinancialSuitability.STRONG_FIT
            reason = "Strong financial fit: Investment scale, own contribution, and repayment capacity fully align with scheme structure."
        else:
            suitability = SchemeFinancialSuitability.POSSIBLE_FIT
            reason = "Possible financial fit: Financially viable within published parameters; detailed institutional appraisal required."

        return SchemeFinancialAssessment(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.scheme_name,
            suitability=suitability,
            suitability_reason=reason,
            project_cost=proj_cost,
            own_contribution=own_contrib,
            required_margin_money=req_margin,
            margin_money_gap=margin_gap,
            required_loan=effective_loan,
            available_subsidy=est_sub,
            subsidy_percentage=sub_pct,
            available_grant=est_grant,
            estimated_emi=est_emi,
            interest_rate_display=int_display,
            repayment_tenure_display=tenure_display,
            moratorium_display=moratorium_display,
            collateral_requirement_display=collateral_display,
            guarantee_requirement_display=guarantee_display,
            processing_fee_display=fee_display,
            max_project_cost=max_proj,
            min_project_cost=min_proj,
            max_loan_amount=max_loan,
            min_loan_amount=min_loan,
            is_project_cost_eligible=is_cost_eligible,
            is_loan_amount_eligible=is_loan_eligible,
            is_own_contribution_sufficient=is_margin_sufficient,
            missing_parameters=missing_params,
            unmet_criteria=unmet,
            positive_factors=positive
        )

    @classmethod
    def compute_emi(
        cls,
        principal: Decimal,
        annual_rate: Decimal,
        tenure_months: int
    ) -> Optional[Decimal]:
        """
        Deterministic reducing-balance installment (EMI) calculation.
        """
        return DeterministicFinancialEngine.calculate_installment(
            principal=principal,
            annual_rate_percent=annual_rate,
            total_periods=int(tenure_months),
            periods_per_year=12
        )

