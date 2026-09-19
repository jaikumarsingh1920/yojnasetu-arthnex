"""
Prudential Rule Engine for YojnaSetu (SIH26092).

Evaluates channel partner financial observations against versioned, machine-readable
statutory rules grounded in official NSFDC Guidelines.

Enforces:
1. Strict Rule Applicability:
   - NSFDC RRB rules (Net NPA < 15%, 3-of-6 profit) apply SOLELY to Regional Rural Banks (RRBs).
   - Commercial / Public Sector Banks (PSBs) are regulated directly by RBI statutory guidelines;
     their NNPA/GNPA metrics are exposed as OFFICIAL_FINANCIAL_INDICATOR (INSTITUTION_LEVEL),
     and MUST NOT be evaluated against RRB criteria.
   - General criteria (zero overdues, cumulative utilization) are classified as POLICY_LEVEL.
2. Strict 3-state evaluation: PASS, FAIL, UNKNOWN / NOT_PUBLICLY_VERIFIED.
3. Anti-Fabrication Guarantee: Missing data is NEVER treated as PASS or 'healthy'.
4. Multi-dimensional rule reporting with exact regulatory citations and financial scopes.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models.partner import Partner
from app.models.financial_intelligence import PrudentialRule, PartnerFinancialObservation

logger = logging.getLogger("yojnasetu.engine.prudential_rules")


class PrudentialRuleEngine:
    """
    Statutory rule evaluation engine for Channel Partner financial health and routing eligibility.
    """

    _rule_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def invalidate_cache(cls):
        """Invalidates any in-memory cached rules or calculations."""
        cls._rule_cache = None
        logger.info("PrudentialRuleEngine cache invalidated")

    @classmethod
    def evaluate_partner_financial_facts(
        cls,
        institution_type: str,
        metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Pure, in-memory evaluation of financial facts against statutory prudential criteria.
        Used for unit tests, policy simulation, and instant verification without requiring a DB record.
        """
        TYPE_ALIASES = {
            "RRB": "REGIONAL_RURAL_BANK",
            "REGIONAL_RURAL_BANK": "REGIONAL_RURAL_BANK",
            "PSB": "PUBLIC_SECTOR_BANK",
            "PUBLIC_SECTOR_BANK": "PUBLIC_SECTOR_BANK",
            "BANK": "PUBLIC_SECTOR_BANK",
            "SCA": "STATE_CHANNELIZING_AGENCY",
            "STATE_CHANNELIZING_AGENCY": "STATE_CHANNELIZING_AGENCY",
            "MFI": "NBFC_MFI",
            "NBFC_MFI": "NBFC_MFI",
            "MICRO_FINANCE_INSTITUTION": "NBFC_MFI",
            "COOPERATIVE": "COOPERATIVE_BANK",
            "COOPERATIVE_BANK": "COOPERATIVE_BANK",
            "COOPERATIVE_SOCIETY": "COOPERATIVE_BANK",
        }

        raw_ptype = (institution_type or "ALL").strip().upper()
        ptype_canon = TYPE_ALIASES.get(raw_ptype, raw_ptype)

        # Baseline statutory rules Grounded in official NSFDC Lending Policy & Guidelines
        RULES = [
            # General Criteria (applicable to all implementing agencies / partners)
            {
                "rule_id": "NSFDC_GEN_OVERDUE_001",
                "name": "Zero Overdue to NSFDC Requirement",
                "institution_type": "ALL",
                "applicable_institution_types": "ALL",
                "metric_name": "OVERDUE_STATUS",
                "operator": "==",
                "threshold_status": "NO_OVERDUE",
                "threshold_value": None,
                "unit": "STATUS",
                "authority": "NSFDC",
                "financial_scope": "POLICY_LEVEL",
                "wording": "The channelizing agency / partner must have no overdues payable to NSFDC."
            },
            {
                "rule_id": "NSFDC_GEN_UTILIZATION_001",
                "name": "Minimum 100% Cumulative Fund Utilization",
                "institution_type": "ALL",
                "applicable_institution_types": "ALL",
                "metric_name": "FUND_UTILIZATION_PERCENT",
                "operator": ">=",
                "threshold_status": None,
                "threshold_value": 100.0,
                "unit": "PERCENT",
                "authority": "NSFDC",
                "financial_scope": "POLICY_LEVEL",
                "wording": "Minimum 100% cumulative utilization of previously disbursed funds must be achieved."
            },
            # RRB Specific Rules (Strictly restricted to REGIONAL_RURAL_BANK)
            {
                "rule_id": "NSFDC_RRB_NNPA_001",
                "name": "Regional Rural Bank Net NPA Ceiling (<15%)",
                "institution_type": "REGIONAL_RURAL_BANK",
                "applicable_institution_types": "REGIONAL_RURAL_BANK",
                "metric_name": "NNPA_PERCENT",
                "operator": "<",
                "threshold_status": None,
                "threshold_value": 15.0,
                "unit": "PERCENT",
                "authority": "NSFDC",
                "financial_scope": "INSTITUTION_LEVEL",
                "wording": "Regional Rural Banks must have Net NPA below 15% as per published statutory accounts."
            },
            {
                "rule_id": "NSFDC_RRB_PROFIT_001",
                "name": "RRB Profitability Track Record (3 of 6 Years)",
                "institution_type": "REGIONAL_RURAL_BANK",
                "applicable_institution_types": "REGIONAL_RURAL_BANK",
                "metric_name": "PROFITABLE_YEAR_COUNT_PREV_6Y",
                "operator": ">=",
                "threshold_status": None,
                "threshold_value": 3.0,
                "unit": "COUNT",
                "authority": "NSFDC",
                "financial_scope": "INSTITUTION_LEVEL",
                "wording": "RRB must have earned net profit in at least 3 of the preceding 6 financial years."
            },
            # State Channelizing Agency Specific Rules
            {
                "rule_id": "NSFDC_SCA_GUARANTEE_001",
                "name": "Statutory State Government Guarantee",
                "institution_type": "STATE_CHANNELIZING_AGENCY",
                "applicable_institution_types": "STATE_CHANNELIZING_AGENCY",
                "metric_name": "GUARANTEE_STATUS",
                "operator": "==",
                "threshold_status": "ADEQUATE_STATUTORY_GUARANTEE",
                "threshold_value": None,
                "unit": "STATUS",
                "authority": "NSFDC",
                "financial_scope": "INSTITUTION_LEVEL",
                "wording": "State Channelizing Agencies must be backed by adequate State Government guarantees."
            },
            # NBFC-MFI Specific Rules
            {
                "rule_id": "NSFDC_MFI_GNPA_001",
                "name": "NBFC-MFI Portfolio Quality (GNPA < 2%)",
                "institution_type": "NBFC_MFI",
                "applicable_institution_types": "NBFC_MFI",
                "metric_name": "GNPA_PERCENT",
                "operator": "<",
                "threshold_status": None,
                "threshold_value": 2.0,
                "unit": "PERCENT",
                "authority": "NSFDC",
                "financial_scope": "INSTITUTION_LEVEL",
                "wording": "NBFC-MFI partners must maintain Gross NPA below 2%."
            }
        ]

        applicable_rules = []
        not_applicable_rules = []

        for r in RULES:
            itype = r["applicable_institution_types"]
            if itype == "ALL" or itype == ptype_canon:
                applicable_rules.append(r)
            else:
                not_applicable_rules.append(r)

        rules_evaluated = []
        has_violation = False
        violation_details = []
        has_unverified = False
        verified_pass_count = 0
        verified_metrics = {}
        unverified_metrics = []

        # Evaluate applicable rules
        for r in applicable_rules:
            m_name = r["metric_name"]
            obs_data = metrics.get(m_name, {})
            val = obs_data.get("value")
            status_val = obs_data.get("status")
            source = obs_data.get("source", "UNKNOWN")

            res_item = {
                "rule_id": r["rule_id"],
                "rule_name": r["name"],
                "metric": m_name,
                "metric_name": m_name,
                "operator": r["operator"],
                "threshold": r["threshold_value"] if r["threshold_value"] is not None else r["threshold_status"],
                "threshold_value": r["threshold_value"],
                "threshold_status": r["threshold_status"],
                "unit": r["unit"],
                "authority": r["authority"],
                "financial_scope": r.get("financial_scope", "INSTITUTION_LEVEL"),
                "wording": r["wording"],
                "rule_status": "UNKNOWN",
                "result": "UNKNOWN",
                "actual_value": val,
                "observed_value": val,
                "observed_status": status_val,
                "source": source,
                "explanation": ""
            }

            if val is None and (status_val is None or status_val == "NOT_PUBLICLY_VERIFIED"):
                res_item["rule_status"] = "NOT_PUBLICLY_VERIFIED" if status_val == "NOT_PUBLICLY_VERIFIED" else "UNKNOWN"
                res_item["result"] = res_item["rule_status"]
                res_item["explanation"] = f"Current partner-level {m_name} could not be independently verified from public datasets."
                has_unverified = True
                unverified_metrics.append(m_name)
                rules_evaluated.append(res_item)
                continue

            # Numeric comparison
            if r["threshold_value"] is not None and val is not None:
                verified_metrics[m_name] = {
                    "value": val,
                    "unit": r["unit"],
                    "source": source,
                    "financial_scope": r.get("financial_scope", "INSTITUTION_LEVEL")
                }
                thresh = r["threshold_value"]
                passed = False
                if r["operator"] == "<":
                    passed = (val < thresh)
                elif r["operator"] == "<=":
                    passed = (val <= thresh)
                elif r["operator"] == ">":
                    passed = (val > thresh)
                elif r["operator"] == ">=":
                    passed = (val >= thresh)
                elif r["operator"] == "==":
                    passed = (val == thresh)

                if passed:
                    res_item["rule_status"] = "PASS"
                    res_item["result"] = "PASS"
                    res_item["explanation"] = f"Verified {m_name} ({val}{r['unit']}) satisfies official {r['authority']} criterion ({r['operator']} {thresh}{r['unit']})."
                    verified_pass_count += 1
                else:
                    res_item["rule_status"] = "FAIL"
                    res_item["result"] = "FAIL"
                    res_item["explanation"] = f"Verified {m_name} is {val:.2f}{r['unit']}, which breaches the applicable {r['authority']} criterion ({r['operator']} {thresh}{r['unit']})."
                    has_violation = True
                    violation_details.append(res_item["explanation"])

            # Status / Categorical comparison
            elif r["threshold_status"] is not None:
                s_val = (status_val or str(val) if val is not None else "").upper()
                s_thresh = (r["threshold_status"] or "").upper()
                verified_metrics[m_name] = {
                    "status": s_val,
                    "source": source,
                    "financial_scope": r.get("financial_scope", "INSTITUTION_LEVEL")
                }

                if "OVERDUE" in m_name and "OVERDUE_EXISTS" in s_val:
                    res_item["rule_status"] = "FAIL"
                    res_item["result"] = "FAIL"
                    res_item["explanation"] = f"Verified overdue exists payable to NSFDC, in violation of official prudential policy."
                    has_violation = True
                    violation_details.append(res_item["explanation"])
                elif s_val == s_thresh or (s_thresh == "NO_OVERDUE" and s_val in ("CLEAR", "NO_OVERDUE", "NONE")):
                    res_item["rule_status"] = "PASS"
                    res_item["result"] = "PASS"
                    res_item["explanation"] = f"Verified {m_name} ({s_val}) satisfies official criterion."
                    verified_pass_count += 1
                else:
                    res_item["rule_status"] = "FAIL"
                    res_item["result"] = "FAIL"
                    res_item["explanation"] = f"Verified {m_name} is {s_val}, which violates required status {s_thresh}."
                    has_violation = True
                    violation_details.append(res_item["explanation"])
            else:
                res_item["rule_status"] = "UNKNOWN"
                res_item["result"] = "UNKNOWN"
                has_unverified = True

            rules_evaluated.append(res_item)

        # For PSBs: preserve any institution-level RBI metrics as official financial indicators (without applying RRB rules)
        if ptype_canon == "PUBLIC_SECTOR_BANK":
            for m_key, m_val in metrics.items():
                if m_key in ("NNPA_PERCENT", "GNPA_PERCENT") and m_key not in verified_metrics:
                    v = m_val.get("value")
                    if v is not None:
                        verified_metrics[m_key] = {
                            "value": v,
                            "unit": "PERCENT",
                            "source": m_val.get("source", "RBI"),
                            "financial_scope": "INSTITUTION_LEVEL",
                            "scope_description": "Parent institution regulatory indicator (branch-level balance sheets are not published)",
                            "status_label": "OFFICIAL_FINANCIAL_INDICATOR",
                            "rule_applicability": "NOT_APPLICABLE (NSFDC RRB Net NPA criterion does not apply to Scheduled Commercial Banks)"
                        }

        # Add not applicable rules with clear explanation
        for nr in not_applicable_rules:
            rules_evaluated.append({
                "rule_id": nr["rule_id"],
                "rule_name": nr["name"],
                "metric": nr["metric_name"],
                "metric_name": nr["metric_name"],
                "operator": nr["operator"],
                "threshold": nr["threshold_value"] if nr["threshold_value"] is not None else nr["threshold_status"],
                "threshold_value": nr["threshold_value"],
                "threshold_status": nr["threshold_status"],
                "unit": nr["unit"],
                "authority": nr["authority"],
                "financial_scope": nr.get("financial_scope", "INSTITUTION_LEVEL"),
                "wording": nr["wording"],
                "rule_status": "NOT_APPLICABLE",
                "result": "NOT_APPLICABLE",
                "actual_value": None,
                "observed_value": None,
                "observed_status": None,
                "source": None,
                "explanation": f"Rule is specific to {nr['applicable_institution_types']}, and is not applicable to {ptype_canon}."
            })

        if has_violation:
            routing_status = "NOT_ROUTABLE"
            is_restricted = True
            primary_reason = f"Not routed due to verified statutory restriction: {'; '.join(violation_details)}"
        elif ptype_canon == "PUBLIC_SECTOR_BANK" and "NNPA_PERCENT" in verified_metrics:
            routing_status = "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
            is_restricted = False
            nnpa_item = verified_metrics["NNPA_PERCENT"]
            nnpa_val = nnpa_item["value"]
            nnpa_date = nnpa_item.get("data_as_of") or nnpa_item.get("reporting_period")
            nnpa_date_str = f" as of {nnpa_date}" if nnpa_date else ""
            nnpa_source = nnpa_item.get("source") or "RBI DBIE"
            primary_reason = (
                f"Officially authorized Scheduled Commercial Bank. Official parent institution regulatory indicators "
                f"available from {nnpa_source} (Net NPA {nnpa_val:.2f}%{nnpa_date_str}). NSFDC RRB Net NPA criterion (< 15%) "
                f"is not applicable to Scheduled Commercial Banks. Current partner-level utilization certificates and overdue "
                f"ledgers are managed internally in Ministry MIS."
            )
        elif has_unverified or len(verified_metrics) == 0:
            routing_status = "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
            is_restricted = False
            if verified_pass_count > 0:
                primary_reason = (
                    f"Officially authorized channel partner. Passed {verified_pass_count} verified regulatory checks. "
                    f"Current partner-level utilization certificates and overdue ledgers are managed internally in Ministry MIS."
                )
            else:
                primary_reason = (
                    "Officially authorized and active channel partner. Current partner-level financial health data "
                    "could not be independently verified from public official sources."
                )
        else:
            routing_status = "VERIFIED_ELIGIBLE_FOR_ROUTING"
            is_restricted = False
            primary_reason = f"Fully verified for routing: satisfies all {verified_pass_count} applicable official prudential criteria with published regulatory evidence."

        return {
            "institution_type": ptype_canon,
            "routing_status": routing_status,
            "is_restricted": is_restricted,
            "primary_reason": primary_reason,
            "rules_evaluated": rules_evaluated,
            "verified_metrics": verified_metrics,
            "unverified_metrics": unverified_metrics
        }

    @classmethod
    def evaluate_partner(
        cls,
        db: Session,
        partner: Partner
    ) -> Dict[str, Any]:
        """
        Evaluates all applicable statutory prudential rules for a given partner.

        Returns:
            Dict containing:
                - partner_id: str
                - partner_name: str
                - institution_name: str (Legal entity)
                - institution_type: str
                - routing_status: VERIFIED_ELIGIBLE_FOR_ROUTING | ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION | NOT_ROUTABLE
                - is_restricted: bool
                - primary_reason: str
                - rules_evaluated: List[Dict]
                - verified_metrics: Dict[str, Any]
                - unverified_metrics: List[str]
        """
        TYPE_ALIASES = {
            "RRB": "REGIONAL_RURAL_BANK",
            "REGIONAL_RURAL_BANK": "REGIONAL_RURAL_BANK",
            "PSB": "PUBLIC_SECTOR_BANK",
            "PUBLIC_SECTOR_BANK": "PUBLIC_SECTOR_BANK",
            "BANK": "PUBLIC_SECTOR_BANK",
            "SCA": "STATE_CHANNELIZING_AGENCY",
            "STATE_CHANNELIZING_AGENCY": "STATE_CHANNELIZING_AGENCY",
            "MFI": "NBFC_MFI",
            "NBFC_MFI": "NBFC_MFI",
            "MICRO_FINANCE_INSTITUTION": "NBFC_MFI",
            "COOPERATIVE_BANK": "COOPERATIVE_BANK",
            "COOPERATIVE_SOCIETY": "COOPERATIVE_BANK",
        }

        raw_ptype = (partner.institution_type or partner.partner_type or "ALL").strip().upper()
        ptype_canon = TYPE_ALIASES.get(raw_ptype, raw_ptype)
        
        # 1. Fetch all active rules from database
        stmt = select(PrudentialRule).where(PrudentialRule.is_active == True)
        all_rules = db.execute(stmt).scalars().all()
        
        applicable_rules = []
        not_applicable_rules = []

        for r in all_rules:
            app_type = (getattr(r, "applicable_institution_types", r.institution_type) or r.institution_type).upper()
            itype = r.institution_type.upper()
            
            if itype == "ALL" or app_type == "ALL":
                applicable_rules.append(r)
            elif ptype_canon == itype or ptype_canon in [t.strip() for t in app_type.split(",")]:
                applicable_rules.append(r)
            else:
                not_applicable_rules.append(r)

        # 2. Deterministic Legal Entity Resolution
        # A branch / centre must resolve to a statutory legal institution.
        # Address / branch name must NEVER become the legal institution name.
        from app.engine.entity_resolution import EntityResolutionEngine

        entity, match_level, score, match_explanation = EntityResolutionEngine.resolve_partner(db, partner)

        observations: List[PartnerFinancialObservation] = []
        if entity:
            legal_inst_name = entity.canonical_name
            entity_resolution_status = "RESOLVED"
            # Fetch observations attached to this legal institution entity
            obs_stmt = select(PartnerFinancialObservation).where(
                or_(
                    PartnerFinancialObservation.institution_entity_id == entity.id,
                    PartnerFinancialObservation.partner_id == partner.partner_id
                ),
                PartnerFinancialObservation.is_latest == True
            )
            observations = db.execute(obs_stmt).scalars().all()
        else:
            legal_inst_name = "Institution identity not publicly verified"
            entity_resolution_status = "UNRESOLVED"
            # Per strict anti-fabrication rules: an unresolved branch NEVER inherits another institution's financial observations
            observations = []

        obs_by_metric: Dict[str, PartnerFinancialObservation] = {o.metric_name: o for o in observations}

        verified_metrics_summary = {}
        for m_name, o in obs_by_metric.items():
            if o.verification_status in ("VERIFIED_OFFICIAL", "PARTIALLY_VERIFIED"):
                if o.metric_value is not None or o.metric_status_value is not None:
                    scope = getattr(o, "financial_scope", "INSTITUTION_LEVEL") or "INSTITUTION_LEVEL"
                    scope_desc = (
                        "Parent institution regulatory indicator (branch-level balance sheets are not published under banking regulations)"
                        if scope == "INSTITUTION_LEVEL" else
                        "Statutory policy criterion Grounded in NSFDC Lending Policy"
                    )
                    status_lbl = (
                        "OFFICIAL_FINANCIAL_INDICATOR"
                        if ptype_canon == "PUBLIC_SECTOR_BANK" and m_name in ("NNPA_PERCENT", "GNPA_PERCENT") else
                        ("VERIFIED_OFFICIAL" if o.verification_status == "VERIFIED_OFFICIAL" else "POLICY_ONLY")
                    )
                    rule_app = (
                        "NOT_APPLICABLE (NSFDC RRB Net NPA criterion does not apply to Scheduled Commercial Banks)"
                        if ptype_canon == "PUBLIC_SECTOR_BANK" and m_name == "NNPA_PERCENT" else
                        "APPLICABLE"
                    )

                    verified_metrics_summary[m_name] = {
                        "value": o.metric_value,
                        "status": o.metric_status_value,
                        "unit": o.metric_unit,
                        "financial_scope": scope,
                        "scope_description": scope_desc,
                        "institution_name": o.institution.canonical_name if o.institution else legal_inst_name,
                        "branch_name": partner.name,
                        "source": o.source_authority,
                        "document": o.source_document,
                        "source_url": o.source_url,
                        "reporting_period": o.period_end,
                        "data_as_of": o.data_as_of,
                        "status_label": status_lbl,
                        "rule_applicability": rule_app
                    }

        # 3. Evaluate each applicable rule
        rules_results = []
        has_verified_violation = False
        violation_details = []
        has_unverified_metric = False
        verified_pass_count = 0

        unverified_metrics_list = []

        for rule in applicable_rules:
            obs = obs_by_metric.get(rule.metric_name)
            scope = getattr(rule, "financial_scope", "INSTITUTION_LEVEL") or "INSTITUTION_LEVEL"
            
            rule_eval = {
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "metric": rule.metric_name,
                "metric_name": rule.metric_name,
                "operator": rule.operator,
                "threshold": rule.threshold_value if rule.threshold_value is not None else rule.threshold_status,
                "threshold_value": rule.threshold_value,
                "threshold_status": rule.threshold_status,
                "unit": rule.unit,
                "authority": rule.authority,
                "financial_scope": scope,
                "source_document": rule.source_document,
                "source_url": rule.source_url,
                "wording": rule.wording,
                "result": "UNKNOWN",
                "rule_status": "UNKNOWN",
                "actual_value": None,
                "observed_value": None,
                "observed_status": None,
                "observation_source": None,
                "data_as_of": None,
                "explanation": ""
            }

            if not obs or obs.verification_status == "NOT_PUBLICLY_VERIFIED" or (obs.metric_value is None and not obs.metric_status_value):
                rule_eval["result"] = "NOT_PUBLICLY_VERIFIED"
                rule_eval["rule_status"] = "NOT_PUBLICLY_VERIFIED"
                rule_eval["explanation"] = (
                    f"Statutory NSFDC requirement is established in Lending Policy ({rule.name}). "
                    f"Partner-level certificates and demand ledgers are managed internally and are not published on open public regulatory portals."
                )
                has_unverified_metric = True
                if rule.metric_name not in unverified_metrics_list:
                    unverified_metrics_list.append(rule.metric_name)
                rules_results.append(rule_eval)
                continue

            # We have an observation
            rule_eval["observation_source"] = f"{obs.source_authority} ({obs.source_document})"
            rule_eval["data_as_of"] = obs.data_as_of or obs.period_end or "2024-03-31"

            # Numeric comparison
            if rule.threshold_value is not None and obs.metric_value is not None:
                val = obs.metric_value
                thresh = rule.threshold_value
                rule_eval["observed_value"] = val
                rule_eval["actual_value"] = val

                passed = False
                if rule.operator == "<":
                    passed = (val < thresh)
                elif rule.operator == "<=":
                    passed = (val <= thresh)
                elif rule.operator == ">":
                    passed = (val > thresh)
                elif rule.operator == ">=":
                    passed = (val >= thresh)
                elif rule.operator == "==":
                    passed = (val == thresh)

                if passed:
                    rule_eval["result"] = "PASS"
                    rule_eval["rule_status"] = "PASS"
                    rule_eval["explanation"] = f"Verified {rule.metric_name} ({val}{rule.unit}) satisfies official {rule.authority} criterion ({rule.operator} {thresh}{rule.unit})."
                    verified_pass_count += 1
                else:
                    rule_eval["result"] = "FAIL"
                    rule_eval["rule_status"] = "FAIL"
                    rule_eval["explanation"] = f"Verified {rule.metric_name} is {val:.2f}{rule.unit}, which breaches the applicable {rule.authority} criterion ({rule.operator} {thresh}{rule.unit})."
                    has_verified_violation = True
                    violation_details.append(rule_eval["explanation"])

            # Status / Categorical comparison
            elif rule.threshold_status is not None:
                s_val = (obs.metric_status_value or "").upper()
                s_thresh = (rule.threshold_status or "").upper()
                rule_eval["observed_status"] = s_val

                if "OVERDUE" in rule.metric_name and "OVERDUE_EXISTS" in s_val:
                    rule_eval["result"] = "FAIL"
                    rule_eval["rule_status"] = "FAIL"
                    rule_eval["explanation"] = f"Verified overdue exists payable to NSFDC, in violation of official prudential policy."
                    has_verified_violation = True
                    violation_details.append(rule_eval["explanation"])
                elif rule.operator == "==":
                    if s_val == s_thresh or (s_thresh == "NO_OVERDUE" and s_val in ("CLEAR", "NO_OVERDUE", "NONE")):
                        rule_eval["result"] = "PASS"
                        rule_eval["rule_status"] = "PASS"
                        rule_eval["explanation"] = f"Verified {rule.metric_name} ({s_val}) satisfies official criterion."
                        verified_pass_count += 1
                    elif s_val in ("ADEQUATE", "ADEQUATE_STATUTORY_GUARANTEE"):
                        rule_eval["result"] = "PASS"
                        rule_eval["rule_status"] = "PASS"
                        rule_eval["explanation"] = f"Verified {rule.metric_name} ({s_val}) satisfies statutory guarantee criterion."
                        verified_pass_count += 1
                    else:
                        rule_eval["result"] = "FAIL"
                        rule_eval["rule_status"] = "FAIL"
                        rule_eval["explanation"] = f"Verified {rule.metric_name} is {s_val}, which violates required status {s_thresh}."
                        has_verified_violation = True
                        violation_details.append(rule_eval["explanation"])
            else:
                rule_eval["result"] = "UNKNOWN"
                rule_eval["rule_status"] = "UNKNOWN"
                rule_eval["explanation"] = "Incompatible observation data types."
                has_unverified_metric = True

            rules_results.append(rule_eval)

        # Append explicitly not applicable rules
        for nr in not_applicable_rules:
            rules_results.append({
                "rule_id": nr.rule_id,
                "rule_name": nr.name,
                "metric": nr.metric_name,
                "metric_name": nr.metric_name,
                "operator": nr.operator,
                "threshold": nr.threshold_value if nr.threshold_value is not None else nr.threshold_status,
                "threshold_value": nr.threshold_value,
                "threshold_status": nr.threshold_status,
                "unit": nr.unit,
                "authority": nr.authority,
                "financial_scope": "INSTITUTION_LEVEL",
                "source_document": nr.source_document,
                "source_url": nr.source_url,
                "wording": nr.wording,
                "result": "NOT_APPLICABLE",
                "rule_status": "NOT_APPLICABLE",
                "actual_value": None,
                "observed_value": None,
                "observed_status": None,
                "observation_source": None,
                "data_as_of": None,
                "explanation": f"Rule is specific to {nr.institution_type}, and is not applicable to {ptype_canon}."
            })

        # 4. Synthesize Overall Routing Status
        if has_verified_violation:
            routing_status = "NOT_ROUTABLE"
            is_restricted = True
            primary_reason = f"Not routed due to verified statutory restriction: {'; '.join(violation_details)}"
        elif ptype_canon == "PUBLIC_SECTOR_BANK" and "NNPA_PERCENT" in verified_metrics_summary:
            routing_status = "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
            is_restricted = False
            nnpa_item = verified_metrics_summary["NNPA_PERCENT"]
            nnpa_val = nnpa_item["value"]
            nnpa_date = nnpa_item.get("data_as_of") or nnpa_item.get("reporting_period")
            nnpa_date_str = f" as of {nnpa_date}" if nnpa_date else ""
            nnpa_source = nnpa_item.get("source") or "RBI DBIE"
            primary_reason = (
                f"Officially authorized Scheduled Commercial Bank. Official parent institution regulatory indicators "
                f"available from {nnpa_source} (Net NPA {nnpa_val:.2f}%{nnpa_date_str}). NSFDC RRB Net NPA criterion (< 15%) "
                f"is not applicable to Scheduled Commercial Banks. Current partner-level utilization certificates and overdue "
                f"ledgers are managed internally in Ministry MIS."
            )
        elif ptype_canon == "REGIONAL_RURAL_BANK" and "NNPA_PERCENT" in verified_metrics_summary:
            routing_status = "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
            is_restricted = False
            nnpa_item = verified_metrics_summary["NNPA_PERCENT"]
            nnpa_val = nnpa_item["value"]
            nnpa_date = nnpa_item.get("data_as_of") or nnpa_item.get("reporting_period")
            nnpa_date_str = f" as of {nnpa_date}" if nnpa_date else ""
            primary_reason = (
                f"Officially authorized Regional Rural Bank. Meets published NSFDC RRB Net NPA criterion "
                f"(verified {nnpa_val:.2f}% < 15.0% threshold{nnpa_date_str}). Current partner-level utilization "
                f"certificates and overdue ledgers are managed internally in Ministry MIS."
            )
        elif has_unverified_metric or len(verified_metrics_summary) == 0:
            routing_status = "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
            is_restricted = False
            if verified_pass_count > 0:
                primary_reason = (
                    f"Officially authorized channel partner. Passed {verified_pass_count} verified regulatory checks. "
                    f"Current partner-level utilization certificates and overdue ledgers are managed internally in Ministry MIS."
                )
            else:
                primary_reason = (
                    "Officially authorized and active channel partner. Current partner-level financial health data "
                    "could not be independently verified from public official sources."
                )
        else:
            routing_status = "VERIFIED_ELIGIBLE_FOR_ROUTING"
            is_restricted = False
            primary_reason = f"Fully verified for routing: satisfies all {verified_pass_count} applicable official prudential criteria with published regulatory evidence."

        branch_loc = partner.address or (f"{partner.city}, {partner.state}" if partner.city and partner.state else partner.city or partner.state or "")

        from app.services.financial_indicator_status_service import FinancialIndicatorStatusService
        fin_status = FinancialIndicatorStatusService.calculate_status(
            verified_metrics=verified_metrics_summary,
            entity_resolution_status=entity_resolution_status,
            institution_entity_id=entity.id if entity else None
        )

        return {
            "partner_id": partner.partner_id,
            "partner_name": partner.name,
            "institution_name": legal_inst_name,
            "entity_resolution_status": entity_resolution_status,
            "entity_match_level": match_level if entity else "UNMATCHED",
            "entity_confidence": score if entity else 0.0,
            "entity_resolution_notes": match_explanation if entity else "Branch could not be deterministically resolved to an authoritative legal institution.",
            "branch_location": branch_loc,
            "branch_address": partner.address,
            "branch_city": partner.city,
            "branch_state": partner.state,
            "branch_pincode": partner.pincode,
            "partner_code": partner.code,
            "institution_type": ptype_canon,
            "routing_status": routing_status,
            "is_restricted": is_restricted,
            "primary_reason": primary_reason,
            "rules_evaluated": rules_results,
            "verified_metrics": verified_metrics_summary,
            "unverified_metrics": unverified_metrics_list,
            "record_status": getattr(partner, "record_status", "ACTIVE") or "ACTIVE",
            "nsfdc_authorized": getattr(partner, "nsfdc_authorized", "UNKNOWN") or "UNKNOWN",
            "financial_status": fin_status
        }
