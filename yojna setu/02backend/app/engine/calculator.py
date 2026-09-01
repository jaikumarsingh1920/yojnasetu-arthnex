"""
Deterministic Financial Calculation Engine for YojnaSetu.

Answers: "Given this scheme and financing scenario, what financial terms/calculations apply?"

All scheme-authoritative financial parameters come from the database.
No values are invented, estimated, inferred, or assumed.
Uses Decimal arithmetic for monetary safety.
"""

from typing import List, Optional, Dict, Tuple
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from sqlalchemy.orm import Session

from app.models.scheme import Scheme
from app.models.rule import SchemeRule
from app.schemas.financial import (
    FinancialCalculationInput,
    FinancialCalculationResult,
    FinancialCalculationStatus,
    ResolvedFinancialParameter,
    ParameterResolutionStatus,
    ValidationError,
    AmortizationEntry,
    RepaymentFrequency,
)

# Precision constants
TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")
TWELVE = Decimal("12")
FOUR = Decimal("4")
TWO = Decimal("2")
HUNDRED = Decimal("100")

# Sentinel raw values that indicate missing/conditional data
SENTINEL_RAW_VALUES = {"UNKNOWN", "CONDITIONAL", "NOT_APPLICABLE", "NONE", ""}


def _decimal_or_none(val) -> Optional[Decimal]:
    """Safely convert a value to Decimal, returning None for sentinels/None."""
    if val is None:
        return None
    try:
        d = Decimal(str(val))
        if d.is_nan() or d.is_infinite():
            return None
        return d
    except (InvalidOperation, ValueError, TypeError):
        return None


def _raw_is_sentinel(raw_val: Optional[str]) -> bool:
    """Check if a raw string value is a sentinel (UNKNOWN, CONDITIONAL, etc.)."""
    if raw_val is None:
        return True
    return raw_val.strip().upper() in SENTINEL_RAW_VALUES


def _periods_per_year(frequency: str) -> Optional[int]:
    """Return the number of payment periods per year for a frequency."""
    freq = frequency.strip().upper()
    if freq == "MONTHLY":
        return 12
    elif freq == "QUARTERLY":
        return 4
    elif freq == "HALF_YEARLY":
        return 2
    elif freq == "YEARLY":
        return 1
    return None


class DeterministicFinancialEngine:
    """
    Core Financial Calculation Engine.
    Strictly separated from the eligibility engine.
    Does NOT modify eligibility status.
    """

    # ─────────────────────────────────────────────────────────
    # 1. RESOLVE FINANCIAL PARAMETERS
    # ─────────────────────────────────────────────────────────

    @classmethod
    def resolve_financial_rules(
        cls,
        scheme: Scheme,
        db_rules: List[SchemeRule],
        calc_input: FinancialCalculationInput,
    ) -> List[ResolvedFinancialParameter]:
        """
        Resolves all scheme-authoritative financial parameters from:
        1. FINANCIAL rules in scheme_rules table
        2. Master scheme attributes (fallback)

        Returns a list of ResolvedFinancialParameter with full traceability.
        Never invents missing values.
        """
        resolved: List[ResolvedFinancialParameter] = []
        financial_rules = [r for r in db_rules if r.rule_type.upper() == "FINANCIAL" and r.active]

        # ── Max Project Cost ──
        resolved.append(cls._resolve_limit_parameter(
            scheme, financial_rules, calc_input,
            field="max_project_cost",
            master_numeric=scheme.max_project_cost,
            master_raw=scheme.max_project_cost_raw,
            master_source_doc=scheme.source_document,
            master_source_page=scheme.source_page,
        ))

        # ── Min Project Cost ──
        resolved.append(cls._resolve_limit_parameter(
            scheme, financial_rules, calc_input,
            field="min_project_cost",
            master_numeric=scheme.min_project_cost,
            master_raw=scheme.min_project_cost_raw,
            master_source_doc=scheme.source_document,
            master_source_page=scheme.source_page,
        ))

        # ── Max Loan Amount ──
        resolved.append(cls._resolve_limit_parameter(
            scheme, financial_rules, calc_input,
            field="max_loan_amount",
            master_numeric=scheme.max_loan_amount,
            master_raw=scheme.max_loan_amount_raw,
            master_source_doc=scheme.source_document,
            master_source_page=scheme.source_page,
        ))

        # ── Min Loan Amount ──
        resolved.append(cls._resolve_limit_parameter(
            scheme, financial_rules, calc_input,
            field="min_loan_amount",
            master_numeric=scheme.min_loan_amount,
            master_raw=scheme.min_loan_amount_raw,
            master_source_doc=scheme.source_document,
            master_source_page=scheme.source_page,
        ))

        # ── Financing Percentage ──
        resolved.append(cls._resolve_limit_parameter(
            scheme, financial_rules, calc_input,
            field="financing_percentage",
            master_numeric=scheme.financing_percentage,
            master_raw=scheme.financing_percentage_raw,
            master_source_doc=scheme.source_document,
            master_source_page=scheme.source_page,
        ))

        # ── Beneficiary Contribution Percentage ──
        resolved.append(cls._resolve_limit_parameter(
            scheme, financial_rules, calc_input,
            field="beneficiary_contribution_percentage",
            master_numeric=scheme.beneficiary_contribution_percentage,
            master_raw=scheme.beneficiary_contribution_percentage_raw,
            master_source_doc=scheme.source_document,
            master_source_page=scheme.source_page,
        ))

        # ── Interest Rate (may be slab-dependent) ──
        resolved.append(cls._resolve_interest_rate(scheme, financial_rules, calc_input))

        # ── Repayment Period ──
        resolved.append(cls._resolve_repayment_period(scheme, financial_rules, calc_input))

        # ── Repayment Frequency ──
        resolved.append(cls._resolve_repayment_frequency(scheme, calc_input))

        # ── Moratorium ──
        resolved.extend(cls._resolve_moratorium(scheme, financial_rules))

        # ── Subsidy ──
        resolved.append(cls._resolve_subsidy(scheme))

        # ── Grant ──
        resolved.append(cls._resolve_grant(scheme))

        # ── Collateral ──
        coll_rule = next((r for r in financial_rules if r.field == "collateral_required"), None)
        if coll_rule:
            resolved.append(ResolvedFinancialParameter(
                field="collateral_required",
                value=coll_rule.value,
                status=ParameterResolutionStatus.RESOLVED,
                source_rule_id=coll_rule.rule_id,
                source_document=coll_rule.source_document,
                source_page=coll_rule.source_page,
                reason=f"Collateral requirement from rule: {coll_rule.value}",
            ))
        elif scheme.collateral_required and scheme.collateral_required.upper() not in SENTINEL_RAW_VALUES:
            resolved.append(ResolvedFinancialParameter(
                field="collateral_required",
                value=scheme.collateral_required,
                status=ParameterResolutionStatus.RESOLVED,
                source_rule_id=f"MASTER-{scheme.scheme_id}",
                source_document=scheme.source_document,
                source_page=scheme.source_page,
                reason=f"Collateral requirement from master scheme attribute: {scheme.collateral_required}",
            ))
        else:
            resolved.append(ResolvedFinancialParameter(
                field="collateral_required",
                value=None,
                status=ParameterResolutionStatus.UNKNOWN,
                source_rule_id=f"MASTER-{scheme.scheme_id}",
                reason="Collateral requirement is UNKNOWN in scheme data.",
            ))

        return resolved

    @classmethod
    def _resolve_limit_parameter(
        cls,
        scheme: Scheme,
        financial_rules: List[SchemeRule],
        calc_input: FinancialCalculationInput,
        field: str,
        master_numeric,
        master_raw: Optional[str],
        master_source_doc: Optional[str],
        master_source_page: Optional[str],
    ) -> ResolvedFinancialParameter:
        """Resolve a numeric limit parameter from rules or master attributes."""
        # First check for a matching financial rule
        matching_rules = [r for r in financial_rules if r.field == field]

        # If there are matching rules in BASE condition group, use them
        base_rule = next((r for r in matching_rules if r.condition_group == "BASE"), None)
        if base_rule:
            val = _decimal_or_none(base_rule.value)
            if val is not None:
                return ResolvedFinancialParameter(
                    field=field, value=val,
                    status=ParameterResolutionStatus.RESOLVED,
                    source_rule_id=base_rule.rule_id,
                    source_document=base_rule.source_document,
                    source_page=base_rule.source_page,
                    reason=f"Resolved from financial rule {base_rule.rule_id}: {field} {base_rule.operator} {base_rule.value}",
                )

        # Check non-BASE condition group rules (these are conditional/slab-dependent)
        non_base_rules = [r for r in matching_rules if r.condition_group != "BASE"]
        if non_base_rules and not base_rule:
            # Try to find the applicable slab rule
            applicable = cls._find_applicable_slab_rule(non_base_rules, calc_input)
            if applicable:
                val = _decimal_or_none(applicable.value)
                if val is not None:
                    return ResolvedFinancialParameter(
                        field=field, value=val,
                        status=ParameterResolutionStatus.RESOLVED,
                        source_rule_id=applicable.rule_id,
                        source_document=applicable.source_document,
                        source_page=applicable.source_page,
                        reason=f"Resolved from conditional rule {applicable.rule_id} [{applicable.condition_group}]: {field} {applicable.operator} {applicable.value}",
                    )
            else:
                # Cannot determine which slab applies
                return ResolvedFinancialParameter(
                    field=field, value=None,
                    status=ParameterResolutionStatus.CONDITIONAL,
                    source_rule_id=non_base_rules[0].rule_id,
                    reason=f"Parameter depends on condition group; cannot resolve without additional context. Groups: {[r.condition_group for r in non_base_rules]}",
                )

        # Fallback to master scheme attribute
        if master_numeric is not None and not _raw_is_sentinel(master_raw):
            val = _decimal_or_none(master_numeric)
            if val is not None:
                return ResolvedFinancialParameter(
                    field=field, value=val,
                    status=ParameterResolutionStatus.RESOLVED,
                    source_rule_id=f"MASTER-{scheme.scheme_id}",
                    source_document=master_source_doc,
                    source_page=master_source_page,
                    reason=f"Resolved from master scheme attribute: {field} = {master_numeric}",
                )

        # Truly UNKNOWN
        raw_status = ParameterResolutionStatus.UNKNOWN
        raw_reason = f"Parameter '{field}' is UNKNOWN in scheme data."
        if master_raw and master_raw.strip().upper() == "CONDITIONAL":
            raw_status = ParameterResolutionStatus.CONDITIONAL
            raw_reason = f"Parameter '{field}' is CONDITIONAL in scheme data."
        elif master_raw and master_raw.strip().upper() == "NOT_APPLICABLE":
            raw_status = ParameterResolutionStatus.NOT_APPLICABLE
            raw_reason = f"Parameter '{field}' is NOT_APPLICABLE for this scheme."

        return ResolvedFinancialParameter(
            field=field, value=None,
            status=raw_status,
            source_rule_id=f"MASTER-{scheme.scheme_id}",
            reason=raw_reason,
        )

    @classmethod
    def _find_applicable_slab_rule(
        cls,
        slab_rules: List[SchemeRule],
        calc_input: FinancialCalculationInput,
    ) -> Optional[SchemeRule]:
        """
        For slab-dependent rules, find the applicable rule based on input context.
        Returns None if the slab cannot be determined.
        """
        if not slab_rules:
            return None

        groups = {r.condition_group for r in slab_rules}

        # ── Loan slab resolution: LOAN_LTE_{boundary} vs LOAN_GT_{boundary} ──
        lte_groups = [g for g in groups if g.startswith("LOAN_LTE_")]
        gt_groups = [g for g in groups if g.startswith("LOAN_GT_")]
        if lte_groups and gt_groups:
            if calc_input.requested_loan_amount is None:
                return None
            # Extract boundary from condition group name (e.g. LOAN_LTE_125000 → 125000)
            try:
                boundary = Decimal(lte_groups[0].replace("LOAN_LTE_", ""))
            except Exception:
                return None
            if calc_input.requested_loan_amount <= boundary:
                return next((r for r in slab_rules if r.condition_group == lte_groups[0]), None)
            else:
                return next((r for r in slab_rules if r.condition_group == gt_groups[0]), None)

        # ── UNY rate slab: UNY_COOP_RATE vs UNY_SFB_RATE (channel-dependent) ──
        if "UNY_COOP_RATE" in groups or "UNY_SFB_RATE" in groups:
            # Cannot resolve without channel type information — return None
            return None

        # ── ELS repayment slab: ELS_REPAY_STARTED vs ELS_REPAY_NOT_STARTED ──
        if "ELS_REPAY_STARTED" in groups or "ELS_REPAY_NOT_STARTED" in groups:
            # Cannot determine repayment start status — return None
            return None

        # Single non-BASE slab — take it directly if only one
        if len(slab_rules) == 1:
            return slab_rules[0]

        return None

    @classmethod
    def _resolve_interest_rate(
        cls,
        scheme: Scheme,
        financial_rules: List[SchemeRule],
        calc_input: FinancialCalculationInput,
    ) -> ResolvedFinancialParameter:
        """Resolve interest rate, handling slab-based rates."""
        rate_rules = [r for r in financial_rules if r.field == "interest_rate_max"]

        if rate_rules:
            base_rate = next((r for r in rate_rules if r.condition_group == "BASE"), None)
            if base_rate:
                val = _decimal_or_none(base_rate.value)
                if val is not None:
                    return ResolvedFinancialParameter(
                        field="interest_rate",
                        value=val,
                        status=ParameterResolutionStatus.RESOLVED,
                        source_rule_id=base_rate.rule_id,
                        source_document=base_rate.source_document,
                        source_page=base_rate.source_page,
                        reason=f"Interest rate from rule {base_rate.rule_id}: {base_rate.value}% p.a.",
                    )

            # Non-BASE slab rules
            non_base = [r for r in rate_rules if r.condition_group != "BASE"]
            if non_base:
                applicable = cls._find_applicable_slab_rule(non_base, calc_input)
                if applicable:
                    val = _decimal_or_none(applicable.value)
                    if val is not None:
                        return ResolvedFinancialParameter(
                            field="interest_rate",
                            value=val,
                            status=ParameterResolutionStatus.RESOLVED,
                            source_rule_id=applicable.rule_id,
                            source_document=applicable.source_document,
                            source_page=applicable.source_page,
                            reason=f"Interest rate from slab rule {applicable.rule_id} [{applicable.condition_group}]: {applicable.value}% p.a.",
                        )
                else:
                    return ResolvedFinancialParameter(
                        field="interest_rate",
                        value=None,
                        status=ParameterResolutionStatus.CONDITIONAL,
                        source_rule_id=non_base[0].rule_id,
                        reason=f"Interest rate depends on slab/channel selection. Groups: {[r.condition_group for r in non_base]}",
                    )

        # Fallback to master scheme attributes
        if scheme.interest_rate_max is not None and not _raw_is_sentinel(scheme.interest_rate_max_raw):
            val = _decimal_or_none(scheme.interest_rate_max)
            if val is not None:
                return ResolvedFinancialParameter(
                    field="interest_rate",
                    value=val,
                    status=ParameterResolutionStatus.RESOLVED,
                    source_rule_id=f"MASTER-{scheme.scheme_id}",
                    source_document=scheme.source_document,
                    source_page=scheme.source_page,
                    reason=f"Interest rate from master scheme attribute: {scheme.interest_rate_max}% p.a.",
                )

        return ResolvedFinancialParameter(
            field="interest_rate", value=None,
            status=ParameterResolutionStatus.UNKNOWN,
            source_rule_id=f"MASTER-{scheme.scheme_id}",
            reason="Interest rate is UNKNOWN in scheme data.",
        )

    @classmethod
    def _resolve_repayment_period(
        cls,
        scheme: Scheme,
        financial_rules: List[SchemeRule],
        calc_input: FinancialCalculationInput,
    ) -> ResolvedFinancialParameter:
        """Resolve repayment period in months."""
        repay_rules = [r for r in financial_rules if r.field == "repayment_period_max_months"]

        if repay_rules:
            base_rule = next((r for r in repay_rules if r.condition_group == "BASE"), None)
            if base_rule:
                val = _decimal_or_none(base_rule.value)
                if val is not None:
                    return ResolvedFinancialParameter(
                        field="repayment_period_max_months",
                        value=int(val),
                        status=ParameterResolutionStatus.RESOLVED,
                        source_rule_id=base_rule.rule_id,
                        source_document=base_rule.source_document,
                        source_page=base_rule.source_page,
                        reason=f"Max repayment period from rule {base_rule.rule_id}: {int(val)} months.",
                    )

            non_base = [r for r in repay_rules if r.condition_group != "BASE"]
            if non_base:
                applicable = cls._find_applicable_slab_rule(non_base, calc_input)
                if applicable:
                    val = _decimal_or_none(applicable.value)
                    if val is not None:
                        return ResolvedFinancialParameter(
                            field="repayment_period_max_months",
                            value=int(val),
                            status=ParameterResolutionStatus.RESOLVED,
                            source_rule_id=applicable.rule_id,
                            source_document=applicable.source_document,
                            source_page=applicable.source_page,
                            reason=f"Max repayment period from slab rule {applicable.rule_id} [{applicable.condition_group}]: {int(val)} months.",
                        )
                else:
                    return ResolvedFinancialParameter(
                        field="repayment_period_max_months",
                        value=None,
                        status=ParameterResolutionStatus.CONDITIONAL,
                        source_rule_id=non_base[0].rule_id,
                        reason=f"Repayment period depends on slab selection. Groups: {[r.condition_group for r in non_base]}",
                    )

        # Master attribute fallback
        if scheme.repayment_period_max_months is not None and not _raw_is_sentinel(scheme.repayment_period_max_months_raw):
            return ResolvedFinancialParameter(
                field="repayment_period_max_months",
                value=scheme.repayment_period_max_months,
                status=ParameterResolutionStatus.RESOLVED,
                source_rule_id=f"MASTER-{scheme.scheme_id}",
                source_document=scheme.source_document,
                source_page=scheme.source_page,
                reason=f"Max repayment period from master attribute: {scheme.repayment_period_max_months} months.",
            )

        return ResolvedFinancialParameter(
            field="repayment_period_max_months",
            value=None,
            status=ParameterResolutionStatus.UNKNOWN,
            source_rule_id=f"MASTER-{scheme.scheme_id}",
            reason="Repayment period is UNKNOWN in scheme data.",
        )

    @classmethod
    def _resolve_repayment_frequency(
        cls,
        scheme: Scheme,
        calc_input: FinancialCalculationInput,
    ) -> ResolvedFinancialParameter:
        """Resolve repayment frequency."""
        freq = scheme.repayment_frequency
        if freq and freq.strip().upper() not in SENTINEL_RAW_VALUES:
            clean = freq.strip().upper()
            # If the scheme specifies a single deterministic frequency
            if clean in ("MONTHLY", "QUARTERLY", "HALF_YEARLY", "YEARLY"):
                return ResolvedFinancialParameter(
                    field="repayment_frequency",
                    value=clean,
                    status=ParameterResolutionStatus.RESOLVED,
                    source_rule_id=f"MASTER-{scheme.scheme_id}",
                    source_document=scheme.source_document,
                    source_page=scheme.source_page,
                    reason=f"Repayment frequency from master attribute: {clean}.",
                )
            # Multiple options (e.g. "QUARTERLY; HALF_YEARLY")
            if ";" in clean or "," in clean:
                options = [o.strip() for o in clean.replace(";", ",").split(",") if o.strip()]
                # If caller specified a preference and it's in the allowed set
                if calc_input.repayment_frequency and calc_input.repayment_frequency.value in options:
                    return ResolvedFinancialParameter(
                        field="repayment_frequency",
                        value=calc_input.repayment_frequency.value,
                        status=ParameterResolutionStatus.RESOLVED,
                        source_rule_id=f"MASTER-{scheme.scheme_id}",
                        source_document=scheme.source_document,
                        source_page=scheme.source_page,
                        reason=f"Repayment frequency selected by caller from allowed options: {options}.",
                    )
                # Default to first available option
                return ResolvedFinancialParameter(
                    field="repayment_frequency",
                    value=options[0],
                    status=ParameterResolutionStatus.CONDITIONAL,
                    source_rule_id=f"MASTER-{scheme.scheme_id}",
                    reason=f"Multiple repayment frequencies allowed: {options}. Using first option; caller may specify preference.",
                )

        return ResolvedFinancialParameter(
            field="repayment_frequency",
            value=None,
            status=ParameterResolutionStatus.UNKNOWN,
            source_rule_id=f"MASTER-{scheme.scheme_id}",
            reason="Repayment frequency is UNKNOWN in scheme data.",
        )

    @classmethod
    def _resolve_moratorium(
        cls,
        scheme: Scheme,
        financial_rules: List[SchemeRule],
    ) -> List[ResolvedFinancialParameter]:
        """Resolve moratorium months and interest treatment."""
        results = []

        # Check for TEXT moratorium rule (e.g. ELS scheme RULE-0057)
        text_mor_rules = [r for r in financial_rules if r.field == "moratorium" and r.value_type == "TEXT"]
        if text_mor_rules:
            rule = text_mor_rules[0]
            results.append(ResolvedFinancialParameter(
                field="moratorium_months",
                value=None,
                status=ParameterResolutionStatus.CONDITIONAL,
                source_rule_id=rule.rule_id,
                source_document=rule.source_document,
                source_page=rule.source_page,
                reason=f"Moratorium is conditional: {rule.value}",
            ))
        else:
            # Numeric moratorium from rules or master attributes
            mor_min_rules = [r for r in financial_rules if r.field == "moratorium_min_months"]
            mor_max_rules = [r for r in financial_rules if r.field == "moratorium_max_months"]

            mor_val = None
            mor_source = f"MASTER-{scheme.scheme_id}"
            mor_status = ParameterResolutionStatus.UNKNOWN
            mor_reason = "Moratorium is UNKNOWN in scheme data."

            if mor_max_rules:
                rule = mor_max_rules[0]
                val = _decimal_or_none(rule.value)
                if val is not None:
                    mor_val = int(val)
                    mor_source = rule.rule_id
                    mor_status = ParameterResolutionStatus.RESOLVED
                    mor_reason = f"Moratorium max from rule {rule.rule_id}: {mor_val} months."
            elif scheme.moratorium_max_months is not None and not _raw_is_sentinel(scheme.moratorium_max_months_raw):
                mor_val = scheme.moratorium_max_months
                mor_status = ParameterResolutionStatus.RESOLVED
                mor_reason = f"Moratorium max from master attribute: {mor_val} months."
            elif scheme.moratorium_max_months_raw and scheme.moratorium_max_months_raw.strip().upper() == "CONDITIONAL":
                mor_status = ParameterResolutionStatus.CONDITIONAL
                mor_reason = "Moratorium is CONDITIONAL in scheme data."

            results.append(ResolvedFinancialParameter(
                field="moratorium_months",
                value=mor_val,
                status=mor_status,
                source_rule_id=mor_source,
                source_document=scheme.source_document,
                source_page=scheme.source_page,
                reason=mor_reason,
            ))

        # Moratorium interest mode — UNKNOWN for all current schemes
        mode_val = scheme.moratorium_interest_mode
        if mode_val and mode_val.strip().upper() not in SENTINEL_RAW_VALUES:
            results.append(ResolvedFinancialParameter(
                field="moratorium_interest_mode",
                value=mode_val,
                status=ParameterResolutionStatus.RESOLVED,
                source_rule_id=f"MASTER-{scheme.scheme_id}",
                source_document=scheme.source_document,
                source_page=scheme.source_page,
                reason=f"Moratorium interest mode from master attribute: {mode_val}.",
            ))
        else:
            results.append(ResolvedFinancialParameter(
                field="moratorium_interest_mode",
                value=None,
                status=ParameterResolutionStatus.UNKNOWN,
                source_rule_id=f"MASTER-{scheme.scheme_id}",
                reason="Moratorium interest mode is UNKNOWN in scheme data. Cannot determine interest treatment during moratorium.",
            ))

        return results

    @classmethod
    def _resolve_subsidy(cls, scheme: Scheme) -> ResolvedFinancialParameter:
        """Resolve subsidy information."""
        if scheme.subsidy_available and scheme.subsidy_available.strip().upper() == "TRUE":
            val = _decimal_or_none(scheme.subsidy_percentage)
            return ResolvedFinancialParameter(
                field="subsidy_percentage",
                value=val,
                status=ParameterResolutionStatus.RESOLVED if val is not None else ParameterResolutionStatus.UNKNOWN,
                source_rule_id=f"MASTER-{scheme.scheme_id}",
                source_document=scheme.source_document,
                source_page=scheme.source_page,
                reason=f"Subsidy: {val}%" if val else "Subsidy available but percentage UNKNOWN.",
            )
        elif scheme.subsidy_available and scheme.subsidy_available.strip().upper() == "FALSE":
            return ResolvedFinancialParameter(
                field="subsidy_percentage",
                value=None,
                status=ParameterResolutionStatus.NOT_APPLICABLE,
                source_rule_id=f"MASTER-{scheme.scheme_id}",
                reason="Subsidy is NOT_APPLICABLE for this scheme.",
            )
        return ResolvedFinancialParameter(
            field="subsidy_percentage",
            value=None,
            status=ParameterResolutionStatus.UNKNOWN,
            source_rule_id=f"MASTER-{scheme.scheme_id}",
            reason="Subsidy availability is UNKNOWN.",
        )

    @classmethod
    def _resolve_grant(cls, scheme: Scheme) -> ResolvedFinancialParameter:
        """Resolve grant information."""
        if scheme.grant_available and scheme.grant_available.strip().upper() == "TRUE":
            val = _decimal_or_none(scheme.grant_amount)
            return ResolvedFinancialParameter(
                field="grant_amount",
                value=val,
                status=ParameterResolutionStatus.RESOLVED if val is not None else ParameterResolutionStatus.UNKNOWN,
                source_rule_id=f"MASTER-{scheme.scheme_id}",
                source_document=scheme.source_document,
                source_page=scheme.source_page,
                reason=f"Grant amount: ₹{val}" if val else "Grant available but amount UNKNOWN.",
            )
        elif scheme.grant_available and scheme.grant_available.strip().upper() == "FALSE":
            return ResolvedFinancialParameter(
                field="grant_amount",
                value=None,
                status=ParameterResolutionStatus.NOT_APPLICABLE,
                source_rule_id=f"MASTER-{scheme.scheme_id}",
                reason="Grant is NOT_APPLICABLE for this scheme.",
            )
        return ResolvedFinancialParameter(
            field="grant_amount",
            value=None,
            status=ParameterResolutionStatus.UNKNOWN,
            source_rule_id=f"MASTER-{scheme.scheme_id}",
            reason="Grant availability is UNKNOWN.",
        )

    # ─────────────────────────────────────────────────────────
    # 2. VALIDATE LOAN REQUEST
    # ─────────────────────────────────────────────────────────

    @classmethod
    def validate_loan_request(
        cls,
        calc_input: FinancialCalculationInput,
        resolved: List[ResolvedFinancialParameter],
    ) -> List[ValidationError]:
        """
        Validate requested amounts against authoritative limits.
        Returns structured validation errors — never silently adjusts values.
        """
        errors: List[ValidationError] = []
        param_map = {p.field: p for p in resolved}

        # ── Project cost validation ──
        if calc_input.project_cost is not None:
            max_proj = param_map.get("max_project_cost")
            if max_proj and max_proj.status == ParameterResolutionStatus.RESOLVED and max_proj.value is not None:
                if calc_input.project_cost > max_proj.value:
                    errors.append(ValidationError(
                        field="project_cost",
                        message=f"Project cost ₹{calc_input.project_cost:,.2f} exceeds scheme maximum of ₹{max_proj.value:,.2f}.",
                        requested_value=calc_input.project_cost,
                        authoritative_limit=max_proj.value,
                    ))

            min_proj = param_map.get("min_project_cost")
            if min_proj and min_proj.status == ParameterResolutionStatus.RESOLVED and min_proj.value is not None:
                if calc_input.project_cost < min_proj.value:
                    errors.append(ValidationError(
                        field="project_cost",
                        message=f"Project cost ₹{calc_input.project_cost:,.2f} is below scheme minimum of ₹{min_proj.value:,.2f}.",
                        requested_value=calc_input.project_cost,
                        authoritative_limit=min_proj.value,
                    ))

        # ── Loan amount validation ──
        if calc_input.requested_loan_amount is not None:
            max_loan = param_map.get("max_loan_amount")
            if max_loan and max_loan.status == ParameterResolutionStatus.RESOLVED and max_loan.value is not None:
                if calc_input.requested_loan_amount > max_loan.value:
                    errors.append(ValidationError(
                        field="requested_loan_amount",
                        message=f"Requested loan ₹{calc_input.requested_loan_amount:,.2f} exceeds scheme maximum of ₹{max_loan.value:,.2f}.",
                        requested_value=calc_input.requested_loan_amount,
                        authoritative_limit=max_loan.value,
                    ))

            min_loan = param_map.get("min_loan_amount")
            if min_loan and min_loan.status == ParameterResolutionStatus.RESOLVED and min_loan.value is not None:
                if calc_input.requested_loan_amount < min_loan.value:
                    errors.append(ValidationError(
                        field="requested_loan_amount",
                        message=f"Requested loan ₹{calc_input.requested_loan_amount:,.2f} is below scheme minimum of ₹{min_loan.value:,.2f}.",
                        requested_value=calc_input.requested_loan_amount,
                        authoritative_limit=min_loan.value,
                    ))

            # Validate against financing percentage if project cost is known
            fin_pct = param_map.get("financing_percentage")
            if (calc_input.project_cost is not None
                    and fin_pct and fin_pct.status == ParameterResolutionStatus.RESOLVED
                    and fin_pct.value is not None):
                max_financed = (calc_input.project_cost * fin_pct.value / HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                if calc_input.requested_loan_amount > max_financed:
                    errors.append(ValidationError(
                        field="requested_loan_amount",
                        message=f"Requested loan ₹{calc_input.requested_loan_amount:,.2f} exceeds {fin_pct.value}% financing limit of ₹{max_financed:,.2f} on project cost ₹{calc_input.project_cost:,.2f}.",
                        requested_value=calc_input.requested_loan_amount,
                        authoritative_limit=max_financed,
                    ))

        # ── Repayment period validation ──
        if calc_input.repayment_period_months is not None:
            max_repay = param_map.get("repayment_period_max_months")
            if max_repay and max_repay.status == ParameterResolutionStatus.RESOLVED and max_repay.value is not None:
                if calc_input.repayment_period_months > int(max_repay.value):
                    errors.append(ValidationError(
                        field="repayment_period_months",
                        message=f"Requested tenure {calc_input.repayment_period_months} months exceeds scheme maximum of {max_repay.value} months.",
                        requested_value=calc_input.repayment_period_months,
                        authoritative_limit=max_repay.value,
                    ))

        return errors

    # ─────────────────────────────────────────────────────────
    # 3. FINANCING CALCULATION
    # ─────────────────────────────────────────────────────────

    @classmethod
    def calculate_financing(
        cls,
        calc_input: FinancialCalculationInput,
        param_map: Dict[str, ResolvedFinancialParameter],
    ) -> Dict:
        """
        Calculate eligible loan amount, beneficiary contribution, etc.
        Returns dict of computed amounts. Uses Decimal throughout.
        """
        result = {
            "eligible_loan_amount": None,
            "beneficiary_contribution_amount": None,
        }

        if calc_input.project_cost is None or calc_input.requested_loan_amount is None:
            return result

        project_cost = calc_input.project_cost
        requested = calc_input.requested_loan_amount

        fin_pct = param_map.get("financing_percentage")
        if fin_pct and fin_pct.status == ParameterResolutionStatus.RESOLVED and fin_pct.value is not None:
            max_financed = (project_cost * fin_pct.value / HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            eligible = min(requested, max_financed)

            # Also cap at max loan amount if known
            max_loan = param_map.get("max_loan_amount")
            if max_loan and max_loan.status == ParameterResolutionStatus.RESOLVED and max_loan.value is not None:
                eligible = min(eligible, max_loan.value)

            result["eligible_loan_amount"] = eligible.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            result["beneficiary_contribution_amount"] = (project_cost - eligible).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        else:
            # Cannot determine financing without percentage
            result["eligible_loan_amount"] = requested
            max_loan = param_map.get("max_loan_amount")
            if max_loan and max_loan.status == ParameterResolutionStatus.RESOLVED and max_loan.value is not None:
                result["eligible_loan_amount"] = min(requested, max_loan.value)

            result["beneficiary_contribution_amount"] = (project_cost - result["eligible_loan_amount"]).quantize(TWO_PLACES, rounding=ROUND_HALF_UP) if result["eligible_loan_amount"] else None

        return result

    # ─────────────────────────────────────────────────────────
    # 4. INSTALLMENT CALCULATION
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def calculate_installment(
        principal: Decimal,
        annual_rate_percent: Decimal,
        total_periods: int,
        periods_per_year: int,
    ) -> Optional[Decimal]:
        """
        Standard reducing-balance installment formula.
        EMI = P × r(1+r)^n / ((1+r)^n - 1)
        where r = periodic rate, n = total periods.

        Handles zero-interest case separately.
        Returns None for invalid inputs (principal <= 0 or total_periods <= 0).
        """
        if principal <= ZERO or total_periods <= 0:
            return None

        if annual_rate_percent == ZERO:
            # Zero interest: simple division
            return (principal / Decimal(total_periods)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # Periodic interest rate
        r = annual_rate_percent / HUNDRED / Decimal(periods_per_year)
        n = total_periods

        # (1 + r)^n
        one_plus_r_n = (ONE + r) ** n

        # EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        emi = principal * r * one_plus_r_n / (one_plus_r_n - ONE)
        return emi.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    # ─────────────────────────────────────────────────────────
    # 5. AMORTIZATION SCHEDULE
    # ─────────────────────────────────────────────────────────

    @classmethod
    def generate_amortization_schedule(
        cls,
        principal: Decimal,
        annual_rate_percent: Decimal,
        total_periods: int,
        periods_per_year: int,
        moratorium_months: Optional[int] = None,
        moratorium_interest_mode: Optional[str] = None,
    ) -> Tuple[List[AmortizationEntry], List[str]]:
        """
        Generate full amortization schedule with Decimal precision.
        Returns (schedule, warnings).

        Moratorium: since moratorium_interest_mode is UNKNOWN for all current
        schemes, moratorium periods are reported as a warning but the schedule
        begins after the moratorium. No interest treatment is assumed.
        """
        schedule: List[AmortizationEntry] = []
        warnings: List[str] = []

        if principal <= ZERO or total_periods <= 0:
            return schedule, ["Cannot generate schedule: invalid principal or tenure."]

        # Moratorium warning
        if moratorium_months and moratorium_months > 0:
            if moratorium_interest_mode is None or str(moratorium_interest_mode).strip().upper() in SENTINEL_RAW_VALUES:
                warnings.append(
                    f"Moratorium of {moratorium_months} months applies before repayment begins. "
                    f"Interest treatment during moratorium is UNKNOWN — schedule excludes moratorium period."
                )
            else:
                warnings.append(
                    f"Moratorium of {moratorium_months} months applies with interest mode: {moratorium_interest_mode}."
                )

        installment = cls.calculate_installment(principal, annual_rate_percent, total_periods, periods_per_year)
        if installment is None:
            return schedule, ["Cannot compute installment."]

        r = annual_rate_percent / HUNDRED / Decimal(periods_per_year) if annual_rate_percent > ZERO else ZERO
        balance = principal

        for i in range(1, total_periods + 1):
            interest = (balance * r).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

            if i == total_periods:
                # Last installment: clear the remaining balance exactly
                principal_component = balance
                actual_installment = (principal_component + interest).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            else:
                principal_component = (installment - interest).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                actual_installment = installment

            new_balance = (balance - principal_component).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

            schedule.append(AmortizationEntry(
                installment_number=i,
                period_label=f"Period {i}",
                opening_principal=balance,
                installment_amount=actual_installment,
                interest_component=interest,
                principal_component=principal_component,
                closing_principal=new_balance,
            ))
            balance = new_balance

        # Verify final balance is zero within tolerance
        if abs(balance) > TWO_PLACES:
            warnings.append(f"Rounding residual: final balance is ₹{balance}, expected ₹0.00.")

        return schedule, warnings

    # ─────────────────────────────────────────────────────────
    # 6. TOP-LEVEL CALCULATE
    # ─────────────────────────────────────────────────────────

    @classmethod
    def calculate(
        cls,
        db: Session,
        calc_input: FinancialCalculationInput,
    ) -> FinancialCalculationResult:
        """
        Top-level entry point. Orchestrates: resolve → validate → calculate → amortize.
        Returns a fully traceable FinancialCalculationResult.
        """
        # Load scheme
        scheme = db.query(Scheme).filter(Scheme.scheme_id == calc_input.scheme_id).first()
        if not scheme:
            return FinancialCalculationResult(
                status=FinancialCalculationStatus.VALIDATION_FAILED,
                scheme_id=calc_input.scheme_id,
                scheme_name="UNKNOWN",
                validation_errors=[ValidationError(
                    field="scheme_id",
                    message=f"Scheme '{calc_input.scheme_id}' not found in database.",
                )],
            )

        # Load rules
        db_rules = db.query(SchemeRule).filter(
            SchemeRule.scheme_id == calc_input.scheme_id,
            SchemeRule.active == True,
        ).all()

        # 1. Resolve parameters
        resolved = cls.resolve_financial_rules(scheme, db_rules, calc_input)
        param_map = {p.field: p for p in resolved}

        # Check if scheme is a non-credit scheme
        if not scheme.is_credit_scheme or not scheme.calculator_applicable:
            return FinancialCalculationResult(
                status=FinancialCalculationStatus.NOT_APPLICABLE,
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                is_credit_scheme=False,
                calculator_applicable=False,
                financial_category=scheme.financial_category,
                financial_assistance_summary=scheme.financial_assistance_summary,
                resolved_parameters=resolved,
                message="Loan / EMI calculation is not applicable for this scheme. Assistance is provided as a subsidy/grant/benefit rather than a repayable loan.",
                warnings=["Loan / EMI calculation is not applicable for this scheme."],
            )

        # 2. Check for missing critical inputs
        missing: List[str] = []
        all_warnings: List[str] = []

        if calc_input.requested_loan_amount is None:
            missing.append("requested_loan_amount")
        if calc_input.project_cost is None:
            missing.append("project_cost")

        # Check critical resolved parameters
        interest_param = param_map.get("interest_rate")
        repay_param = param_map.get("repayment_period_max_months")
        freq_param = param_map.get("repayment_frequency")

        effective_interest_rate = calc_input.interest_rate
        if effective_interest_rate is None and interest_param and interest_param.value is not None:
            effective_interest_rate = _decimal_or_none(interest_param.value)

        if effective_interest_rate is None:
            if interest_param and interest_param.status == ParameterResolutionStatus.UNKNOWN:
                missing.append("interest_rate")
            elif interest_param and interest_param.status == ParameterResolutionStatus.CONDITIONAL:
                all_warnings.append(f"Interest rate is CONDITIONAL: {interest_param.reason}")
                missing.append("interest_rate (CONDITIONAL)")
            else:
                missing.append("interest_rate")

        if calc_input.repayment_period_months is None and repay_param and repay_param.status == ParameterResolutionStatus.UNKNOWN:
            missing.append("repayment_period_max_months")
        # Note: repayment_frequency UNKNOWN is NOT a hard blocker.
        # The engine defaults to MONTHLY with a warning when frequency is UNKNOWN,
        # since the core calculation (interest rate, tenure, principal) can still proceed.

        # Conditional parameters as warnings, not blockers
        if repay_param and repay_param.status == ParameterResolutionStatus.CONDITIONAL:
            all_warnings.append(f"Repayment period is CONDITIONAL: {repay_param.reason}")

        # 3. Validate loan request
        validation_errors = cls.validate_loan_request(calc_input, resolved)

        if validation_errors:
            return FinancialCalculationResult(
                status=FinancialCalculationStatus.VALIDATION_FAILED,
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                resolved_parameters=resolved,
                project_cost=calc_input.project_cost,
                requested_loan_amount=calc_input.requested_loan_amount,
                validation_errors=validation_errors,
                missing_parameters=missing,
                warnings=all_warnings,
            )

        if missing:
            return FinancialCalculationResult(
                status=FinancialCalculationStatus.INSUFFICIENT_INFORMATION,
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                resolved_parameters=resolved,
                project_cost=calc_input.project_cost,
                requested_loan_amount=calc_input.requested_loan_amount,
                missing_parameters=missing,
                warnings=all_warnings,
            )

        # 4. Calculate financing
        financing = cls.calculate_financing(calc_input, param_map)
        eligible_loan = financing["eligible_loan_amount"]
        beneficiary_contribution = financing["beneficiary_contribution_amount"]

        # 5. Determine calculation parameters
        interest_rate = effective_interest_rate

        # Determine tenure
        tenure = calc_input.repayment_period_months
        if tenure is None:
            if repay_param and repay_param.status == ParameterResolutionStatus.RESOLVED and repay_param.value is not None:
                tenure = int(repay_param.value)
            else:
                return FinancialCalculationResult(
                    status=FinancialCalculationStatus.INSUFFICIENT_INFORMATION,
                    scheme_id=scheme.scheme_id,
                    scheme_name=scheme.scheme_name,
                    resolved_parameters=resolved,
                    project_cost=calc_input.project_cost,
                    requested_loan_amount=calc_input.requested_loan_amount,
                    eligible_loan_amount=eligible_loan,
                    beneficiary_contribution_amount=beneficiary_contribution,
                    interest_rate=interest_rate,
                    missing_parameters=["repayment_period_months"],
                    warnings=all_warnings,
                )

        # Determine frequency
        freq_str = None
        if calc_input.repayment_frequency:
            freq_str = calc_input.repayment_frequency.value if hasattr(calc_input.repayment_frequency, 'value') else str(calc_input.repayment_frequency)
        elif freq_param and freq_param.value:
            freq_str = str(freq_param.value)

        if not freq_str:
            freq_str = "MONTHLY"
            all_warnings.append("Repayment frequency not determined; defaulting to MONTHLY for calculation.")

        ppy = _periods_per_year(freq_str)
        if ppy is None:
            freq_str = "MONTHLY"
            ppy = 12
            all_warnings.append(f"Unsupported repayment frequency; defaulting to MONTHLY.")

        # Convert tenure from months to periods
        months_per_period = 12 // ppy
        total_periods = tenure // months_per_period if months_per_period > 0 else tenure

        if total_periods <= 0:
            return FinancialCalculationResult(
                status=FinancialCalculationStatus.VALIDATION_FAILED,
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.scheme_name,
                resolved_parameters=resolved,
                validation_errors=[ValidationError(
                    field="repayment_period_months",
                    message=f"Tenure of {tenure} months results in 0 payment periods for {freq_str} frequency.",
                )],
                warnings=all_warnings,
            )

        # 6. Calculate installment
        installment = cls.calculate_installment(eligible_loan, interest_rate, total_periods, ppy)

        # 7. Moratorium
        mor_param = param_map.get("moratorium_months")
        mor_mode_param = param_map.get("moratorium_interest_mode")
        moratorium_months = None
        moratorium_mode = None
        if mor_param and mor_param.status == ParameterResolutionStatus.RESOLVED and mor_param.value is not None:
            moratorium_months = int(mor_param.value)
        if mor_mode_param and mor_mode_param.value:
            moratorium_mode = str(mor_mode_param.value)

        # 8. Generate amortization schedule
        schedule, schedule_warnings = cls.generate_amortization_schedule(
            principal=eligible_loan,
            annual_rate_percent=interest_rate,
            total_periods=total_periods,
            periods_per_year=ppy,
            moratorium_months=moratorium_months,
            moratorium_interest_mode=moratorium_mode,
        )
        all_warnings.extend(schedule_warnings)

        # 9. Compute totals
        total_interest = sum(e.interest_component for e in schedule)
        total_repayment = sum(e.installment_amount for e in schedule)

        # Subsidy / Grant
        sub_param = param_map.get("subsidy_percentage")
        subsidy_amount = None
        if sub_param and sub_param.status == ParameterResolutionStatus.RESOLVED and sub_param.value is not None:
            subsidy_amount = (calc_input.project_cost * _decimal_or_none(sub_param.value) / HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        grant_param = param_map.get("grant_amount")
        grant_val = None
        if grant_param and grant_param.status == ParameterResolutionStatus.RESOLVED and grant_param.value is not None:
            grant_val = _decimal_or_none(grant_param.value)

        return FinancialCalculationResult(
            status=FinancialCalculationStatus.CALCULATED,
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.scheme_name,
            resolved_parameters=resolved,
            project_cost=calc_input.project_cost,
            requested_loan_amount=calc_input.requested_loan_amount,
            eligible_loan_amount=eligible_loan,
            beneficiary_contribution_amount=beneficiary_contribution,
            subsidy_amount=subsidy_amount,
            grant_amount=grant_val,
            interest_rate=interest_rate,
            repayment_period_months=tenure,
            repayment_frequency=freq_str,
            moratorium_months=moratorium_months,
            moratorium_interest_mode=moratorium_mode,
            periodic_installment=installment,
            total_interest=total_interest.quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
            total_repayment=total_repayment.quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
            amortization_schedule=schedule,
            validation_errors=[],
            missing_parameters=[],
            warnings=all_warnings,
        )
