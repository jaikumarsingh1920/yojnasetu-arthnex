import re
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Set

logger = logging.getLogger("yojnasetu.ingestion.change_detector")

CRITICAL_FIELDS: Set[str] = {
    # Scheme Identity & Authority
    "scheme_name",
    "scheme_status",
    "ministry",
    "source_organization",
    "implementing_agency",
    # Eligibility Criteria
    "age_min",
    "age_max",
    "income_limit",
    "caste_criteria",
    "gender_criteria",
    "gender_condition",
    "gender_requirement",
    "sc_required",
    "social_category",
    "target_beneficiary",
    "applicant_types",
    "target_groups",
    "marginalized_group",
    "entrepreneur_type",
    "business_stage",
    "new_unit_required",
    "education_applicable",
    # Geography
    "state_restriction",
    "state_coverage",
    "district_restriction",
    "district_coverage",
    # Financial Terms & Subsidies
    "loan_available",
    "min_project_cost",
    "max_project_cost",
    "min_loan_amount",
    "max_loan_amount",
    "minimum_loan_amount",
    "maximum_loan_amount",
    "interest_rate",
    "interest_rate_min",
    "interest_rate_max",
    "interest_subvention",
    "subsidy_available",
    "subsidy_percentage",
    "subsidy_details",
    "grant_available",
    "grant_amount",
    "moratorium_min_months",
    "moratorium_max_months",
    "repayment_period_min_months",
    "repayment_period_max_months",
    "collateral_required",
    # Benefits & Supports
    "support_type",
    "benefit_description",
    "training_available",
    "equipment_support",
    "working_capital_support",
    "market_support",
    # Process & URLs
    "application_mode",
    "application_url",
    "official_portal",
    "official_source_url",
    "required_documents",
    "effective_from",
    "effective_to",
    "application_route",
}


class ChangeClassification:
    """
    Standardized classification of scheme monitoring ingestion results:
    1. UNCHANGED: Content hash and scheme data are completely identical.
    2. MODIFIED: Canonical scheme exists, but authoritative source contains verified parameter updates.
    3. NEW_SCHEME: Authoritative source contains a newly published official scheme.
    4. POSSIBLY_WITHDRAWN: Authoritative source explicitly indicates scheme is closed, discontinued, or withdrawn.
    5. SOURCE_CHANGED_ONLY: Source page/PDF hash changed, but extracted scheme parameters are identical to canonical data.
    """
    UNCHANGED = "UNCHANGED"
    MODIFIED = "MODIFIED"
    NEW_SCHEME = "NEW_SCHEME"
    POSSIBLY_WITHDRAWN = "POSSIBLY_WITHDRAWN"
    SOURCE_CHANGED_ONLY = "SOURCE_CHANGED_ONLY"


@dataclass
class FieldDiff:
    field: str
    change_type: str  # "ADDED", "MODIFIED", "REMOVED"
    old_value: Any
    new_value: Any
    is_critical: bool
    diff_text: str
    source_url: Optional[str] = None
    detected_at: Optional[str] = None
    confidence: float = 1.0
    validation_status: str = "VALID"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "change_type": self.change_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "is_critical": self.is_critical,
            "diff_text": self.diff_text,
            "source_url": self.source_url,
            "detected_at": self.detected_at,
            "confidence": self.confidence,
            "validation_status": self.validation_status,
        }


@dataclass
class ChangeDetectionResult:
    has_changed: bool
    status: str  # NO_CHANGE or CHANGE_DETECTED
    content_hash: str
    previous_hash: Optional[str] = None
    field_diffs: List[Dict[str, Any]] = field(default_factory=list)
    governance_category: str = "NEEDS_REVIEW"  # AUTO_SAFE, NEEDS_REVIEW, REJECTED
    classification: str = ChangeClassification.UNCHANGED


class DeterministicChangeDetector:
    """
    Deterministic Change Detection & Machine-Readable Field Diffing Engine.
    1. Normalizes webpage content to strip volatile, non-semantic artifacts (scripts,
       styles, session tokens, dynamic timestamps, CSRF tokens) before generating a stable
       cryptographic SHA-256 fingerprint.
    2. Compares extracted candidate attributes against canonical scheme attributes.
    3. Produces auditable, machine-readable field-level diffs categorizing changes into
       ADDED, MODIFIED, or REMOVED, and CRITICAL vs NON_CRITICAL.
    4. Categorizes into AUTO_SAFE vs NEEDS_REVIEW governance boundaries.
    Zero LLM involvement, 100% deterministic and auditable.
    """

    @classmethod
    def detect_deactivation_evidence(
        cls,
        raw_content: Optional[str],
        extracted_data: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Inspects content and extracted data for authoritative deactivation/withdrawal notices.
        Returns (is_deactivated_candidate, reason_or_evidence).
        Temporary HTTP errors, timeouts, or missing pages NEVER count as deactivation.
        """
        data = extracted_data or {}
        status_val = str(data.get("scheme_status", "")).upper()
        if status_val in ("INACTIVE", "CLOSED", "WITHDRAWN", "DEACTIVATED", "DISCONTINUED"):
            return True, f"Official source status explicitly marked as {status_val}"

        patterns = [
            r"(?:this\s+)?scheme\s+(?:has\s+been|is)\s+(?:withdrawn|discontinued|closed|deactivated|terminated)",
            r"(?:applications|admissions)\s+(?:are\s+closed|have\s+been\s+closed|suspended|discontinued)",
            r"no\s+longer\s+accepting\s+(?:new\s+)?applications",
            r"scheme\s+(?:closed|discontinued)\s+w\.?e\.?f\.?",
            r"official\s+closure\s+notice",
        ]
        c_clean = raw_content or ""
        for pat in patterns:
            match = re.search(pat, c_clean, re.IGNORECASE)
            if match:
                return True, f"Authoritative deactivation notice detected: '{match.group(0)}'"

        return False, None

    @classmethod
    def normalize_content(cls, raw_html: str) -> str:
        """
        Normalizes HTML content into a stable canonical text representation
        free of volatile elements like analytics tags, csrf tokens, dynamic timestamps,
        and layout whitespace.
        """
        if not raw_html:
            return ""

        text = raw_html

        # 1. Remove HTML comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # 2. Remove script, style, noscript, svg, iframe tags and contents
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<noscript[^>]*>.*?</noscript>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<svg[^>]*>.*?</svg>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<iframe[^>]*>.*?</iframe>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # 3. Strip volatile inputs (CSRF tokens, viewstates, session tokens, nonces, timestamps)
        text = re.sub(
            r'<input[^>]*(?:csrf|token|session|viewstate|timestamp|nonce|cache|_ts)[^>]*>',
            "",
            text,
            flags=re.IGNORECASE
        )

        # 4. Remove transient metadata tags (date, cache, expires, last-modified)
        text = re.sub(r'<meta[^>]*>', "", text, flags=re.IGNORECASE)

        # 5. Remove dynamic render/server timestamps in tags
        text = re.sub(
            r'<[^>]*>[^<]*(?:page\s+generated|rendered\s+at|server\s+time|current\s+time|last\s+updated)[^<]*</[^>]*>',
            "",
            text,
            flags=re.IGNORECASE
        )

        # 6. Remove dynamic cache-busting query strings in URLs
        text = re.sub(r'\?[_a-zA-Z0-9]+=\d{8,}', "", text)

        # 7. Normalize inter-tag whitespace
        text = re.sub(r'>\s+<', '><', text)

        # 8. Normalize text whitespace
        text = re.sub(r'[ \t\r\n]+', ' ', text)

        return text.strip()

    @classmethod
    def compute_hash(cls, normalized_content: str) -> str:
        """Computes deterministic SHA-256 hex digest of normalized content."""
        return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()

    @classmethod
    def detect_change(
        cls,
        current_raw_content: str,
        previous_snapshot_hash: Optional[str]
    ) -> ChangeDetectionResult:
        """
        Evaluates whether newly fetched content represents a real change
        compared to the previous successful snapshot.
        """
        normalized = cls.normalize_content(current_raw_content)
        current_hash = cls.compute_hash(normalized)

        if not previous_snapshot_hash:
            # First fetch for this source: baseline snapshot establishes baseline
            return ChangeDetectionResult(
                has_changed=True,
                status="CHANGE_DETECTED",
                content_hash=current_hash,
                previous_hash=None,
                governance_category="NEEDS_REVIEW"
            )

        if current_hash == previous_snapshot_hash:
            return ChangeDetectionResult(
                has_changed=False,
                status="NO_CHANGE",
                content_hash=current_hash,
                previous_hash=previous_snapshot_hash,
                governance_category="AUTO_SAFE"
            )

        return ChangeDetectionResult(
            has_changed=True,
            status="CHANGE_DETECTED",
            content_hash=current_hash,
            previous_hash=previous_snapshot_hash,
            governance_category="NEEDS_REVIEW"
        )

    @classmethod
    def format_value_for_display(cls, field_name: str, val: Any) -> str:
        """Formats currency, percentages, and text cleanly for audit diff display."""
        if val is None:
            return "None"
        if "amount" in field_name or "income" in field_name or "assistance" in field_name or "cost" in field_name:
            try:
                num = float(val)
                if num >= 10000000:
                    return f"₹{num / 10000000:.2f} Crore (₹{num:,.0f})"
                elif num >= 100000:
                    return f"₹{num / 100000:.2f} Lakh (₹{num:,.0f})"
                else:
                    return f"₹{num:,.0f}"
            except (ValueError, TypeError):
                return str(val).strip()
        if "rate" in field_name or "percentage" in field_name or "subsidy" in field_name:
            try:
                return f"{float(val):.2f}%"
            except (ValueError, TypeError):
                return str(val).strip()
        return str(val).strip()

    @classmethod
    def generate_field_diffs(
        cls,
        target_scheme: Optional[Any],
        candidate_data: Dict[str, Any],
        source_url: Optional[str] = None,
        validation_status: str = "VALID",
        confidence: float = 1.0,
        detected_at: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Compares candidate extracted data against canonical scheme attributes.
        Returns machine-readable field diffs (with field, change_type, old_value, new_value,
        is_critical, source_url, detected_at, confidence, validation_status)
        and a governance recommendation (AUTO_SAFE vs NEEDS_REVIEW).
        """
        diffs: List[Dict[str, Any]] = []
        has_critical_change = False
        timestamp = detected_at or datetime.utcnow().isoformat()

        if not target_scheme:
            # Entirely new scheme proposed
            for k, new_v in candidate_data.items():
                if new_v is not None and str(new_v).strip():
                    is_crit = k in CRITICAL_FIELDS
                    if is_crit:
                        has_critical_change = True
                    disp_new = cls.format_value_for_display(k, new_v)
                    diff_obj = FieldDiff(
                        field=k,
                        change_type="ADDED",
                        old_value=None,
                        new_value=new_v,
                        is_critical=is_crit,
                        diff_text=f"NEW: {k} = {disp_new} [{'CRITICAL' if is_crit else 'NON_CRITICAL'}]",
                        source_url=source_url,
                        detected_at=timestamp,
                        confidence=confidence,
                        validation_status=validation_status
                    )
                    diffs.append(diff_obj.to_dict())
            return diffs, "NEEDS_REVIEW"

        for k, new_v in candidate_data.items():
            if hasattr(target_scheme, k):
                old_v = getattr(target_scheme, k)
                old_str = str(old_v).strip() if old_v is not None else ""
                new_str = str(new_v).strip() if new_v is not None else ""

                is_diff = False
                try:
                    old_float = float(old_v) if old_v is not None else None
                    new_float = float(new_v) if new_v is not None else None
                    if old_float is not None and new_float is not None:
                        is_diff = abs(old_float - new_float) > 1e-5
                    elif "url" in k.lower():
                        is_diff = old_str.rstrip("/") != new_str.rstrip("/")
                    else:
                        is_diff = (old_str != new_str)
                except (ValueError, TypeError):
                    if "url" in k.lower():
                        is_diff = old_str.rstrip("/") != new_str.rstrip("/")
                    else:
                        is_diff = (old_str != new_str)

                if is_diff:
                    is_crit = k in CRITICAL_FIELDS
                    if is_crit:
                        has_critical_change = True

                    disp_old = cls.format_value_for_display(k, old_v)
                    disp_new = cls.format_value_for_display(k, new_v)

                    if not old_str and new_str:
                        change_type = "ADDED"
                        diff_text = f"ADDED: {k} = {disp_new} [{'CRITICAL' if is_crit else 'NON_CRITICAL'}]"
                    elif old_str and not new_str:
                        change_type = "REMOVED"
                        diff_text = f"REMOVED: {k} (was {disp_old}) [{'CRITICAL' if is_crit else 'NON_CRITICAL'}]"
                    else:
                        change_type = "MODIFIED"
                        diff_text = f"OLD: {k} = {disp_old} | NEW: {k} = {disp_new} [{'CRITICAL' if is_crit else 'NON_CRITICAL'}]"

                    diff_obj = FieldDiff(
                        field=k,
                        change_type=change_type,
                        old_value=old_v,
                        new_value=new_v,
                        is_critical=is_crit,
                        diff_text=diff_text,
                        source_url=source_url,
                        detected_at=timestamp,
                        confidence=confidence,
                        validation_status=validation_status
                    )
                    diffs.append(diff_obj.to_dict())

        if not diffs:
            return [], "AUTO_SAFE"

        governance = "NEEDS_REVIEW" if has_critical_change else "AUTO_SAFE"
        return diffs, governance

    @classmethod
    def build_structured_diff_summary(
        cls,
        diffs: List[Dict[str, Any]],
        source_url: Optional[str] = None,
        validation_status: str = "VALID"
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive machine-readable diff summary dictionary.
        """
        added = [d["field"] for d in diffs if d.get("change_type") == "ADDED"]
        changed = [d["field"] for d in diffs if d.get("change_type") == "MODIFIED"]
        removed = [d["field"] for d in diffs if d.get("change_type") == "REMOVED"]
        has_critical = any(d.get("is_critical", False) for d in diffs)

        return {
            "total_changes": len(diffs),
            "added_fields": added,
            "changed_fields": changed,
            "removed_fields": removed,
            "has_critical_changes": has_critical,
            "source_url": source_url,
            "detected_at": datetime.utcnow().isoformat(),
            "validation_status": validation_status,
            "diffs": diffs
        }
