"""
Financial Indicator Status Service for YojnaSetu (SIH26092).

Authoritative backend service providing deterministic, citizen-friendly interpretation
of verified publicly reported financial indicators according to methodology YS-FIS-V1.

IMPORTANT SEMANTIC BOUNDARY:
- These categories are a YojnaSetu presentation aid based on verified publicly reported financial indicators.
- They are NOT an official RBI rating, bank safety score, risk rating, or loan approval prediction.
- Does not alter deterministic eligibility, prudential rules, or entity resolution.
"""

from enum import Enum
import math
from typing import Optional, Dict, Any, List, Union


class FinancialIndicatorStatusCode(str, Enum):
    STRONGER = "STRONGER"
    MIXED = "MIXED"
    HIGHER_STRESS = "HIGHER_STRESS"
    LIMITED_DATA = "LIMITED_DATA"


STATUS_LABELS: Dict[FinancialIndicatorStatusCode, str] = {
    FinancialIndicatorStatusCode.STRONGER: "Financial position looks stronger",
    FinancialIndicatorStatusCode.MIXED: "Financial position is mixed",
    FinancialIndicatorStatusCode.HIGHER_STRESS: "Financial position needs attention",
    FinancialIndicatorStatusCode.LIMITED_DATA: "Not enough information",
}

STATUS_DESCRIPTIONS: Dict[FinancialIndicatorStatusCode, str] = {
    FinancialIndicatorStatusCode.STRONGER: "Reported loan problems are lower and capital is in a stronger range.",
    FinancialIndicatorStatusCode.MIXED: "Some reported financial numbers need attention.",
    FinancialIndicatorStatusCode.HIGHER_STRESS: "One or more reported financial numbers need attention.",
    FinancialIndicatorStatusCode.LIMITED_DATA: "Not enough verified financial information is available.",
}

STATUS_WHY_EXPLANATIONS: Dict[FinancialIndicatorStatusCode, str] = {
    FinancialIndicatorStatusCode.STRONGER: "This status is shown because the available verified financial indicators fall within YojnaSetu's stronger presentation ranges.",
    FinancialIndicatorStatusCode.MIXED: "This status is shown because some available verified indicators are in the middle range.",
    FinancialIndicatorStatusCode.HIGHER_STRESS: "This status is shown because one or more available verified indicators are in a higher range of concern.",
    FinancialIndicatorStatusCode.LIMITED_DATA: "We do not have enough verified financial information to calculate a meaningful summary.",
}

PRIMARY_EXPLANATION = (
    "This is a simple summary of publicly reported financial information. "
    "It does not guarantee loan approval, service quality, or financial safety."
)

METHODOLOGY_VERSION = "YS-FIS-V1"


class FinancialIndicatorStatusService:
    """
    Pure, deterministic, side-effect free service for calculating citizen financial indicator status.
    """

    @classmethod
    def calculate_status(
        cls,
        verified_metrics: Optional[Dict[str, Any]] = None,
        entity_resolution_status: Optional[str] = "RESOLVED",
        institution_entity_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates the canonical YojnaSetu financial indicator status (YS-FIS-V1).

        Args:
            verified_metrics: Dict mapping metric_name (e.g. NNPA_PERCENT, GNPA_PERCENT, CRAR_PERCENT)
                              to either a float or an observation dict containing 'value', 'source',
                              'financial_scope', 'verification_status', etc.
            entity_resolution_status: 'RESOLVED' or 'UNRESOLVED'.
            institution_entity_id: Canonical institution ID if resolved.

        Returns:
            Dict containing:
                - code: STRONGER | MIXED | HIGHER_STRESS | LIMITED_DATA
                - label: str
                - short_description: str
                - explanation: str
                - evidence_count: int
                - calculated_from: List[str]
                - methodology_version: str ("YS-FIS-V1")
                - scope_disclaimer: str
        """
        # 1. Unresolved Entity Rule:
        # A partner with unverified or unresolved institution identity must NEVER
        # receive an interpreted financial status or inherited financial indicators.
        if (entity_resolution_status or "").upper() == "UNRESOLVED":
            return cls._build_response(
                code=FinancialIndicatorStatusCode.LIMITED_DATA,
                evidence_count=0,
                calculated_from=[],
                short_description=STATUS_DESCRIPTIONS[FinancialIndicatorStatusCode.LIMITED_DATA],
            )

        if not verified_metrics or not isinstance(verified_metrics, dict):
            return cls._build_response(
                code=FinancialIndicatorStatusCode.LIMITED_DATA,
                evidence_count=0,
                calculated_from=[],
                short_description=STATUS_DESCRIPTIONS[FinancialIndicatorStatusCode.LIMITED_DATA],
            )

        # 2. Extract and strictly validate participating metrics
        # Supported indicators under YS-FIS-V1: NNPA_PERCENT, GNPA_PERCENT, CRAR_PERCENT
        valid_values: Dict[str, float] = {}

        for m_name in ("NNPA_PERCENT", "GNPA_PERCENT", "CRAR_PERCENT"):
            if m_name not in verified_metrics:
                continue

            raw_item = verified_metrics[m_name]
            val = None

            if isinstance(raw_item, (int, float)):
                val = float(raw_item)
            elif isinstance(raw_item, dict):
                # Validate verification status and scope if metadata present
                v_stat = (raw_item.get("verification_status") or "").upper()
                scope = (raw_item.get("financial_scope") or "INSTITUTION_LEVEL").upper()

                # Disallow policy-level observations from participating in bank indicators
                if scope == "POLICY_LEVEL":
                    continue

                # Must not be explicitly unverified
                if v_stat and v_stat not in ("VERIFIED_OFFICIAL", "VERIFIED", "PUBLICLY_VERIFIED"):
                    continue

                raw_val = raw_item.get("value")
                if raw_val is not None:
                    try:
                        val = float(raw_val)
                    except (ValueError, TypeError):
                        val = None

            # Numeric validity check: must be a finite non-NaN number
            if val is not None and not math.isnan(val) and not math.isinf(val):
                # Disallow negative NPA or negative CRAR as corrupt data
                if val >= 0.0:
                    valid_values[m_name] = val

        evidence_count = len(valid_values)
        calculated_from = sorted(list(valid_values.keys()))

        # 3. Minimum Evidence Rule:
        # Requires AT LEAST TWO verified indicators before assigning STRONGER, MIXED, or HIGHER_STRESS.
        # If fewer than 2 indicators exist, return LIMITED_DATA.
        if evidence_count < 2:
            short_desc = (
                "Only limited verified financial information is available."
                if evidence_count == 1
                else STATUS_DESCRIPTIONS[FinancialIndicatorStatusCode.LIMITED_DATA]
            )
            return cls._build_response(
                code=FinancialIndicatorStatusCode.LIMITED_DATA,
                evidence_count=evidence_count,
                calculated_from=calculated_from,
                short_description=short_desc,
            )

        nnpa = valid_values.get("NNPA_PERCENT")
        gnpa = valid_values.get("GNPA_PERCENT")
        crar = valid_values.get("CRAR_PERCENT")

        # 4. Presentation Bands (YS-FIS-V1):
        # High Stress condition:
        # NNPA > 3.0% OR GNPA > 7.0% OR CRAR < 9.0%
        is_higher_stress = (
            (nnpa is not None and nnpa > 3.0)
            or (gnpa is not None and gnpa > 7.0)
            or (crar is not None and crar < 9.0)
        )

        if is_higher_stress:
            return cls._build_response(
                code=FinancialIndicatorStatusCode.HIGHER_STRESS,
                evidence_count=evidence_count,
                calculated_from=calculated_from,
                short_description=STATUS_DESCRIPTIONS[FinancialIndicatorStatusCode.HIGHER_STRESS],
            )

        # Mixed condition:
        # 1.0% < NNPA <= 3.0% OR 3.0% < GNPA <= 7.0% OR 9.0% <= CRAR < 12.0%
        is_mixed = (
            (nnpa is not None and 1.0 < nnpa <= 3.0)
            or (gnpa is not None and 3.0 < gnpa <= 7.0)
            or (crar is not None and 9.0 <= crar < 12.0)
        )

        if is_mixed:
            return cls._build_response(
                code=FinancialIndicatorStatusCode.MIXED,
                evidence_count=evidence_count,
                calculated_from=calculated_from,
                short_description=STATUS_DESCRIPTIONS[FinancialIndicatorStatusCode.MIXED],
            )

        # Stronger condition:
        # All available indicators fall into the stronger range:
        # NNPA <= 1.0% AND GNPA <= 3.0% AND CRAR >= 12.0%
        is_stronger = (
            (nnpa is None or nnpa <= 1.0)
            and (gnpa is None or gnpa <= 3.0)
            and (crar is None or crar >= 12.0)
        )

        if is_stronger:
            return cls._build_response(
                code=FinancialIndicatorStatusCode.STRONGER,
                evidence_count=evidence_count,
                calculated_from=calculated_from,
                short_description=STATUS_DESCRIPTIONS[FinancialIndicatorStatusCode.STRONGER],
            )

        # Fallback safeguard
        return cls._build_response(
            code=FinancialIndicatorStatusCode.LIMITED_DATA,
            evidence_count=evidence_count,
            calculated_from=calculated_from,
            short_description=STATUS_DESCRIPTIONS[FinancialIndicatorStatusCode.LIMITED_DATA],
        )

    @classmethod
    def _build_response(
        cls,
        code: FinancialIndicatorStatusCode,
        evidence_count: int,
        calculated_from: List[str],
        short_description: str,
    ) -> Dict[str, Any]:
        """
        Constructs the canonical status response structure.
        """
        return {
            "code": code.value,
            "label": STATUS_LABELS[code],
            "short_description": short_description,
            "explanation": PRIMARY_EXPLANATION,
            "why_this_status": STATUS_WHY_EXPLANATIONS.get(code, ""),
            "evidence_count": evidence_count,
            "calculated_from": calculated_from,
            "methodology_version": METHODOLOGY_VERSION,
            "scope_disclaimer": (
                "This information describes the institution as a whole. "
                "It does not describe the financial position of this individual branch."
            ),
        }
