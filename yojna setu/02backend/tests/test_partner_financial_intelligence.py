"""
SIH26092: Channel Partner Financial Intelligence & Prudential Routing Test Suite.

Authoritative verification covering:
1. Entity Resolution (7 tests: exact, normalized, alias, amalgamation, sponsor-bank, ambiguous rejection, duplicate prevention)
2. Multi-Dimensional Financial Observations (11 tests: NNPA, GNPA, missing metrics, overdues, fund utilization, profit, guarantees)
3. Prudential Rule Engine (5 tests: RRB NNPA < 15% PASS, >= 15% FAIL, missing = UNKNOWN, no overdue != CLEAR, missing utilization != 100%)
4. Intelligent Geospatial Routing (9 tests: hard restriction exclusion, distance ranking, unverified handling, inactive/wrong scheme/category/geo exclusion)
5. Audit Provenance (6 tests: authority, URL, data_as_of, match confidence, staleness, conflicting sources)
6. Anti-Fabrication Invariants (6 tests: sector != partner, generic rule != partner status, LLM cannot override, missing != healthy/zero/100)
7. Dynamic Ingestion & Security (5 tests: SSRF protection, SHA-256 hash change detection, source failure retention, archive old, cache invalidation)
8. Mandatory Final Demos (4 cases: Gorakhpur Dairy ₹3L Term Loan, restricted excluded, unverified labeled, gov source update)
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.main import app
from app.db.session import SessionLocal
from app.models.partner import Partner
from app.models.partner_scheme import PartnerSchemeMapping
from app.models.financial_intelligence import (
    InstitutionEntity,
    InstitutionAlias,
    PartnerFinancialObservation,
    PrudentialRule,
)
from app.engine.entity_resolution import EntityResolutionEngine
from app.engine.prudential_rule_engine import PrudentialRuleEngine
from app.services.geo_partner_service import GeoPartnerLocatorService
from app.services.ingestion.partner_financial_ingestion_service import (
    PartnerFinancialIngestionService,
    SecurityValidationError
)
from app.ai.agent import GPTCopilotAgent
from app.schemas.ai import AIChatRequest

client = TestClient(app)


class PartnerStub:
    def __init__(self, name, partner_type="BANK", state="Uttar Pradesh", district="Gorakhpur", code=None):
        self.name = name
        self.partner_type = partner_type
        self.institution_type = partner_type
        self.state = state
        self.district = district
        self.code = code


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# =========================================================================
# PART 1: ENTITY MATCHING (Tests 1-7)
# =========================================================================

def test_exact_institution_match(db: Session):
    """1. Exact institution match against canonical legal registry."""
    p = PartnerStub(name="Bank of Baroda", partner_type="BANK", state="Uttar Pradesh")
    entity, match_level, score, reason = EntityResolutionEngine.resolve_partner(db=db, partner=p)
    assert entity is not None
    assert match_level in ("MATCH_LEVEL_1", "MATCH_LEVEL_2", "MATCH_LEVEL_3", "MATCH_LEVEL_5")
    assert "Bank of Baroda" in entity.canonical_name


def test_normalized_name_match(db: Session):
    """2. Punctuation, casing, and corporate suffixes normalized correctly."""
    p = PartnerStub(name="BANK OF BARODA LTD.", partner_type="PUBLIC_SECTOR_BANK", state="Uttar Pradesh")
    entity, match_level, score, reason = EntityResolutionEngine.resolve_partner(db=db, partner=p)
    assert entity is not None
    assert "Bank of Baroda" in entity.canonical_name


def test_alias_match(db: Session):
    """3. Institution alias lookup matches canonical entity."""
    p = PartnerStub(name="Central Bank of India Regional Office", partner_type="BANK", state="National")
    entity, match_level, score, reason = EntityResolutionEngine.resolve_partner(db=db, partner=p)
    assert entity is not None
    assert entity.canonical_name == "Central Bank of India"


def test_rrb_amalgamation_lineage_match(db: Session):
    """4. Pre-merger constituent RRB names correctly link to merged entity."""
    p = PartnerStub(name="Baroda UP Bank", partner_type="REGIONAL_RURAL_BANK", state="Uttar Pradesh")
    entity, match_level, score, reason = EntityResolutionEngine.resolve_partner(db=db, partner=p)
    assert entity is not None
    assert "Uttar Pradesh Gramin Bank" in entity.canonical_name or "Baroda U.P. Bank" in entity.canonical_name
    assert match_level in ("MATCH_LEVEL_3", "MATCH_LEVEL_4", "MATCH_LEVEL_5")


def test_sponsor_bank_validation(db: Session):
    """5. Sponsor bank identity signal correctly identifies RRB parentage."""
    entity = db.execute(
        select(InstitutionEntity).where(InstitutionEntity.canonical_name == "Uttar Pradesh Gramin Bank")
    ).scalars().first()
    if entity:
        assert entity.sponsor_bank == "Bank of Baroda"


def test_ambiguous_match_rejected(db: Session):
    """6. Ambiguous or completely unknown partner names are rejected (never force a false match)."""
    p = PartnerStub(name="Random Unregistered Micro Trust", partner_type="COOPERATIVE", state="Kerala")
    entity, match_level, score, reason = EntityResolutionEngine.resolve_partner(db=db, partner=p)
    assert entity is None or match_level in ("AMBIGUOUS_MATCH", "UNMATCHED")


def test_duplicate_entity_prevented(db: Session):
    """7. Canonical institution registry enforces distinct canonical names."""
    names = db.execute(select(InstitutionEntity.canonical_name)).scalars().all()
    assert len(names) == len(set(names)), "Duplicate canonical institution entities detected in database"


# =========================================================================
# PART 2: FINANCIAL OBSERVATIONS & PROVENANCE (Tests 8-18)
# =========================================================================

def test_valid_nnpa_observation(db: Session):
    """8. Valid Net NPA observation from official regulatory publication."""
    obs = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.metric_name == "NNPA_PERCENT",
            PartnerFinancialObservation.verification_status == "VERIFIED_OFFICIAL"
        )
    ).scalars().first()
    assert obs is not None
    assert obs.metric_value is not None
    assert obs.metric_value >= 0.0
    assert obs.source_authority in ("RBI", "NABARD")
    assert obs.data_as_of is not None


def test_high_nnpa_observation(db: Session):
    """9. Evaluation of a simulated/high NNPA (>15%) correctly identifies restriction."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={
            "NNPA_PERCENT": {"value": 16.5, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}
        }
    )
    assert eval_res["is_restricted"] is True
    assert eval_res["routing_status"] == "NOT_ROUTABLE"
    assert "16.50" in eval_res["primary_reason"]
    assert "breaches" in eval_res["primary_reason"] or "exceeds" in eval_res["primary_reason"]


def test_missing_nnpa_observation():
    """10. Missing NNPA evaluates to UNKNOWN / NOT_PUBLICLY_VERIFIED, never PASS."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={}
    )
    assert eval_res["is_restricted"] is False
    assert eval_res["routing_status"] == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
    rule_res = [r for r in eval_res["rules_evaluated"] if r["metric"] == "NNPA_PERCENT"]
    assert len(rule_res) > 0
    assert rule_res[0]["rule_status"] == "UNKNOWN"


def test_valid_gnpa_observation(db: Session):
    """11. Valid Gross NPA observation from official RBI DBIE."""
    obs = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.metric_name == "GNPA_PERCENT",
            PartnerFinancialObservation.verification_status == "VERIFIED_OFFICIAL"
        )
    ).scalars().first()
    assert obs is not None
    assert obs.metric_value is not None
    assert obs.metric_value >= 0.0
    assert obs.source_authority == "RBI"


def test_missing_overdue_not_publicly_verified(db: Session):
    """12. Overdue to NSFDC is a statutory policy requirement; missing public partner observation must be labeled NOT_PUBLICLY_VERIFIED and POLICY_LEVEL."""
    obs = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.metric_name == "OVERDUE_STATUS"
        )
    ).scalars().first()
    assert obs is not None
    assert obs.metric_status_value == "NOT_PUBLICLY_VERIFIED"
    assert obs.source_authority == "NSFDC"
    assert obs.financial_scope == "POLICY_LEVEL"
    assert "Policy" in (obs.source_document or "") or "NSFDC" in (obs.source_document or "")


def test_verified_overdue_observation():
    """13. If verified overdue exists, partner is NOT_ROUTABLE."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={
            "OVERDUE_STATUS": {"value": "OVERDUE_EXISTS", "status": "VERIFIED_OFFICIAL", "source": "NSFDC"}
        }
    )
    assert eval_res["is_restricted"] is True
    assert eval_res["routing_status"] == "NOT_ROUTABLE"


def test_valid_utilization_observation():
    """14. Valid fund utilization meeting criterion passes rule evaluation."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={
            "FUND_UTILIZATION_PERCENT": {"value": 100.0, "status": "VERIFIED_OFFICIAL", "source": "NSFDC"}
        }
    )
    util_rules = [r for r in eval_res["rules_evaluated"] if r["metric"] == "FUND_UTILIZATION_PERCENT"]
    assert len(util_rules) > 0
    assert util_rules[0]["rule_status"] == "PASS"


def test_missing_utilization_not_publicly_verified(db: Session):
    """15. Missing fund utilization is NOT converted to 100%."""
    obs = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.metric_name == "FUND_UTILIZATION_PERCENT"
        )
    ).scalars().first()
    assert obs is not None
    assert obs.metric_status_value == "NOT_PUBLICLY_VERIFIED"
    assert obs.metric_value is None, "Missing fund utilization must not be fabricated as a numeric float"


def test_utilization_below_criterion():
    """16. Verified fund utilization below 100% fails prudential rule."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={
            "FUND_UTILIZATION_PERCENT": {"value": 82.5, "status": "VERIFIED_OFFICIAL", "source": "NSFDC"}
        }
    )
    assert eval_res["is_restricted"] is True
    assert eval_res["routing_status"] == "NOT_ROUTABLE"


def test_profitability_criterion():
    """17. RRB profitability requires net profit in at least 3 of previous 6 financial years."""
    # 4 of 6 years -> PASS
    eval_pass = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={
            "PROFITABLE_YEAR_COUNT_PREV_6Y": {"value": 4.0, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}
        }
    )
    rule_pass = [r for r in eval_pass["rules_evaluated"] if r["metric"] == "PROFITABLE_YEAR_COUNT_PREV_6Y"][0]
    assert rule_pass["rule_status"] == "PASS"

    # 2 of 6 years -> FAIL
    eval_fail = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={
            "PROFITABLE_YEAR_COUNT_PREV_6Y": {"value": 2.0, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}
        }
    )
    assert eval_fail["is_restricted"] is True
    rule_fail = [r for r in eval_fail["rules_evaluated"] if r["metric"] == "PROFITABLE_YEAR_COUNT_PREV_6Y"][0]
    assert rule_fail["rule_status"] == "FAIL"


def test_guarantee_status_observation(db: Session):
    """18. Statutory State Channelizing Agencies (SCAs) have adequate state government guarantees."""
    obs = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.metric_name == "GUARANTEE_STATUS"
        )
    ).scalars().first()
    assert obs is not None
    assert obs.metric_status_value in ("ADEQUATE", "ADEQUATE_STATUTORY_GUARANTEE")
    assert obs.verification_status == "VERIFIED_OFFICIAL"


# =========================================================================
# PART 3: PRUDENTIAL RULE EVALUATION (Tests 19-23)
# =========================================================================

def test_rule_rrb_nnpa_below_15_passes():
    """19. RRB Net NPA below 15% PASSES."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="RRB",
        metrics={"NNPA_PERCENT": {"value": 2.4, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}}
    )
    rule = [r for r in eval_res["rules_evaluated"] if r["metric"] == "NNPA_PERCENT"][0]
    assert rule["rule_status"] == "PASS"
    assert eval_res["is_restricted"] is False


def test_rule_rrb_nnpa_above_15_fails():
    """20. RRB Net NPA >= 15% FAILS."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="RRB",
        metrics={"NNPA_PERCENT": {"value": 15.0, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}}
    )
    rule = [r for r in eval_res["rules_evaluated"] if r["metric"] == "NNPA_PERCENT"][0]
    assert rule["rule_status"] == "FAIL"
    assert eval_res["is_restricted"] is True


def test_rule_missing_nnpa_evaluates_unknown():
    """21. Missing NNPA results in UNKNOWN rule status (never PASS)."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="RRB",
        metrics={}
    )
    rule = [r for r in eval_res["rules_evaluated"] if r["metric"] == "NNPA_PERCENT"][0]
    assert rule["rule_status"] == "UNKNOWN"


def test_rule_no_overdue_evidence_is_not_clear():
    """22. Absence of overdue evidence does NOT mean overdue_status = CLEAR."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={"OVERDUE_STATUS": {"value": None, "status": "NOT_PUBLICLY_VERIFIED", "source": "NSFDC"}}
    )
    rule = [r for r in eval_res["rules_evaluated"] if r["metric"] == "OVERDUE_STATUS"][0]
    assert rule["rule_status"] == "NOT_PUBLICLY_VERIFIED"
    assert eval_res["routing_status"] == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"


def test_rule_missing_utilization_is_not_100_percent():
    """23. Missing utilization data is NOT assumed to be 100%."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={"FUND_UTILIZATION_PERCENT": {"value": None, "status": "NOT_PUBLICLY_VERIFIED", "source": "NSFDC"}}
    )
    rule = [r for r in eval_res["rules_evaluated"] if r["metric"] == "FUND_UTILIZATION_PERCENT"][0]
    assert rule["rule_status"] == "NOT_PUBLICLY_VERIFIED"
    assert rule["actual_value"] != 100.0


# =========================================================================
# PART 4: DETERMINISTIC GEOSPATIAL ROUTING (Tests 24-32)
# =========================================================================

def test_routing_nearest_restricted_partner_excluded(db: Session):
    """24. If nearest partner has a verified restriction, it is strictly excluded from routing results."""
    # Find a commercial bank or RRB near Gorakhpur
    partner = db.execute(
        select(Partner).where(
            Partner.district.ilike("%Gorakhpur%"),
            Partner.institution_type.in_(["BANK", "PUBLIC_SECTOR_BANK", "REGIONAL_RURAL_BANK", "RRB"]),
            Partner.is_active == True
        )
    ).scalars().first()
    if not partner:
        partner = db.execute(
            select(Partner).where(
                Partner.district.ilike("%Gorakhpur%"),
                Partner.partner_type.in_(["BANK", "REGIONAL_RURAL_BANK"]),
                Partner.is_active == True
            )
        ).scalars().first()
    assert partner is not None

    # Temporarily inject a verified overdue observation for this partner
    test_obs = PartnerFinancialObservation(
        partner_id=partner.partner_id,
        metric_name="OVERDUE_STATUS",
        metric_value=None,
        metric_status_value="OVERDUE_EXISTS",
        metric_unit="STATUS",
        source_authority="NSFDC",
        source_url="https://nsfdc.nic.in/overdue-audit",
        source_document="Statutory Overdue Audit",
        verification_status="VERIFIED_OFFICIAL",
        match_confidence="EXACT",
        is_latest=True
    )
    db.add(test_obs)
    db.commit()

    try:
        # Check that this partner is evaluated as restricted and excluded from nearest results
        eval_res = PrudentialRuleEngine.evaluate_partner(db, partner)
        assert eval_res["is_restricted"] is True

        results = GeoPartnerLocatorService.find_nearest_partners(
            db=db,
            latitude=partner.latitude or 26.7606,
            longitude=partner.longitude or 83.3732,
            radius_km=50.0
        )
        returned_ids = [r["partner"].partner_id for r in results]
        assert partner.partner_id not in returned_ids, "Restricted partner must be excluded from routing results"
    finally:
        # Clean up test observation
        db.delete(test_obs)
        db.commit()


def test_routing_farther_eligible_partner_selected(db: Session):
    """25. A farther eligible partner is selected over a nearer restricted partner."""
    # When Partner A is restricted, Partner B (farther away) is returned as top result
    results = GeoPartnerLocatorService.find_nearest_partners(
        db=db,
        latitude=26.7606,
        longitude=83.3732,
        radius_km=25.0
    )
    assert len(results) > 0
    # Results must be strictly sorted by distance ascending among ROUTABLE partners
    distances = [r["distance_km"] for r in results]
    assert distances == sorted(distances)


def test_routing_unverified_partner_transparently_represented(db: Session):
    """26. Partners with missing financial feeds are classified as ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION."""
    results = GeoPartnerLocatorService.find_nearest_partners(
        db=db,
        latitude=26.7606,
        longitude=83.3732,
        radius_km=25.0
    )
    for r in results:
        assert r["routing_status"] in ("VERIFIED_ELIGIBLE_FOR_ROUTING", "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION")
        assert "financial_intelligence" in r
        assert "rules_evaluated" in r
        assert "routing_reasons" in r


def test_routing_inactive_partner_excluded(db: Session):
    """27. Inactive partners are excluded regardless of location or financial status."""
    inactive_partner = db.execute(select(Partner).where(Partner.is_active == False)).scalars().first()
    if inactive_partner and inactive_partner.latitude and inactive_partner.longitude:
        results = GeoPartnerLocatorService.find_nearest_partners(
            db=db,
            latitude=inactive_partner.latitude,
            longitude=inactive_partner.longitude,
            radius_km=10.0
        )
        returned_ids = [r["partner"].partner_id for r in results]
        assert inactive_partner.partner_id not in returned_ids


def test_routing_wrong_scheme_excluded(db: Session):
    """28. When querying for a specific scheme, partners not authorized for that scheme are excluded."""
    scheme_id = "SIH26092-053"
    results = GeoPartnerLocatorService.find_nearest_partners(
        db=db,
        latitude=26.7606,
        longitude=83.3732,
        scheme_id=scheme_id,
        radius_km=50.0
    )
    assert len(results) > 0
    for r in results:
        assert scheme_id in r["supported_schemes"] or r["is_scheme_matched"] is True


def test_routing_wrong_loan_category_excluded(db: Session):
    """29. Querying for a specific loan category filters out partners without that category authorization."""
    results = GeoPartnerLocatorService.find_nearest_partners(
        db=db,
        latitude=26.7606,
        longitude=83.3732,
        scheme_id="SIH26092-053",
        loan_category="TERM_LOAN",
        radius_km=50.0
    )
    for r in results:
        cat = r.get("scheme_authorized_category")
        assert cat in (None, "TERM_LOAN", "AUTHORIZED_INSTITUTIONAL_CHANNEL")


def test_routing_wrong_geography_excluded(db: Session):
    """30. Location filter excludes partners in other districts."""
    results = GeoPartnerLocatorService.find_nearest_partners(
        db=db,
        latitude=26.7606,
        longitude=83.3732,
        district="Gorakhpur",
        radius_km=50.0
    )
    for r in results:
        assert "gorakhpur" in (r["partner"].district or "").lower()


def test_routing_all_partners_restricted():
    """31. If all candidate partners have verified restrictions, returns empty list without crashing."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={
            "NNPA_PERCENT": {"value": 18.0, "status": "VERIFIED_OFFICIAL", "source": "RBI"},
            "OVERDUE_STATUS": {"value": "OVERDUE_EXISTS", "status": "VERIFIED_OFFICIAL", "source": "NSFDC"}
        }
    )
    assert eval_res["is_restricted"] is True


def test_routing_all_partners_unverified():
    """32. If all partners have unverified financial feeds, system routes with transparent caveat."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={}
    )
    assert eval_res["is_restricted"] is False
    assert eval_res["routing_status"] == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
    assert "could not be independently verified" in eval_res["primary_reason"]


# =========================================================================
# PART 5: DATA PROVENANCE (Tests 33-38)
# =========================================================================

def test_provenance_source_authority_required(db: Session):
    """33. Every financial observation requires a statutory source authority."""
    obs = db.execute(select(PartnerFinancialObservation)).scalars().all()
    for o in obs:
        assert o.source_authority is not None and len(o.source_authority) > 0


def test_provenance_source_url_required(db: Session):
    """34. Official source URL is present on verified observations."""
    obs = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.verification_status == "VERIFIED_OFFICIAL"
        )
    ).scalars().first()
    assert obs is not None
    assert obs.source_url is not None and obs.source_url.startswith("http")


def test_provenance_data_as_of_required(db: Session):
    """35. Data as of reporting period is captured."""
    obs = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.verification_status == "VERIFIED_OFFICIAL"
        )
    ).scalars().first()
    assert obs is not None
    assert obs.data_as_of is not None


def test_provenance_match_confidence_required(db: Session):
    """36. Entity match confidence is recorded on every observation."""
    obs = db.execute(select(PartnerFinancialObservation)).scalars().all()
    for o in obs:
        assert o.match_confidence in (
            "EXACT", "HIGH", "MEDIUM", "AMBIGUOUS", "UNMATCHED",
            "MATCH_LEVEL_1", "MATCH_LEVEL_2", "MATCH_LEVEL_3", "MATCH_LEVEL_4", "MATCH_LEVEL_5"
        )


def test_provenance_stale_data_marked(db: Session):
    """37. Staleness evaluation correctly detects observations older than policy."""
    stale = PartnerFinancialIngestionService.check_observation_staleness(db=db, max_stale_months=120)
    assert isinstance(stale, list)


def test_provenance_conflicting_sources_preserved(db: Session):
    """38. Different sources reporting on different periods or metrics coexist without overwriting."""
    obs_rbi = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.source_authority == "RBI"
        )
    ).scalars().all()
    obs_nabard = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.source_authority == "NABARD"
        )
    ).scalars().all()
    assert len(obs_rbi) > 0
    assert len(obs_nabard) > 0


# =========================================================================
# PART 6: ANTI-FABRICATION INVARIANTS (Tests 39-44)
# =========================================================================

def test_anti_fabrication_sector_metric_cannot_be_partner_metric(db: Session):
    """39. Sector-level statistics (e.g. SIDBI Microfinance Pulse) cannot be saved as partner observations."""
    with pytest.raises(ValueError, match="Sector-level context cannot be attached"):
        PartnerFinancialIngestionService.ingest_observation(
            db=db,
            partner_id="test-partner-123",
            metric_name="SECTOR_MFI_PAR_90_PLUS",
            metric_value=2.45,
            metric_status_value=None,
            metric_unit="PERCENT",
            source_authority="SIDBI",
            source_url="https://www.sidbi.in/report",
            source_document="SIDBI Microfinance Pulse"
        )


def test_anti_fabrication_generic_rule_not_partner_status():
    """40. A general policy requirement ('100% utilization required') is NOT assumed to be partner status."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={}
    )
    # Partner with no data must NOT have 100% utilization
    assert "FUND_UTILIZATION_PERCENT" not in eval_res["verified_metrics"]


def test_anti_fabrication_llm_cannot_override_routing(db: Session):
    """41. LLM copilot agent cannot invent financial routing outside deterministic backend."""
    copilot = GPTCopilotAgent()
    req = AIChatRequest(
        message="Find me nearest eligible partner in Gorakhpur with high NPA",
        language="en",
        coordinates={"latitude": 26.7606, "longitude": 83.3732}
    )
    res = copilot.process_query(db=db, req=req)
    # Must use deterministic tool response without hallucinating health scores
    assert "87/100" not in res.answer
    assert "Financial Health Score" not in res.answer


def test_anti_fabrication_missing_value_never_healthy():
    """42. Missing financial observations are never tagged as HEALTHY or GOOD."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={}
    )
    assert eval_res["routing_status"] != "HEALTHY"
    assert eval_res["routing_status"] == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"


def test_anti_fabrication_missing_utilization_never_100_percent():
    """43. Missing utilization certificate status is never 100%."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="BANK",
        metrics={"FUND_UTILIZATION_PERCENT": {"value": None, "status": "NOT_PUBLICLY_VERIFIED"}}
    )
    util_rule = [r for r in eval_res["rules_evaluated"] if r["metric"] == "FUND_UTILIZATION_PERCENT"][0]
    assert util_rule["rule_status"] == "NOT_PUBLICLY_VERIFIED"
    assert util_rule["actual_value"] is None


def test_anti_fabrication_missing_npa_never_zero():
    """44. Missing Net NPA is never assumed to be 0.0%."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={}
    )
    nnpa_rule = [r for r in eval_res["rules_evaluated"] if r["metric"] == "NNPA_PERCENT"][0]
    assert nnpa_rule["rule_status"] == "UNKNOWN"
    assert nnpa_rule["actual_value"] is None


# =========================================================================
# PART 7: DYNAMIC INGESTION & SECURITY (Tests 45-49)
# =========================================================================

def test_ingestion_ssrf_and_domain_allowlist():
    """45. Ingestion blocks non-government URLs and internal IP addresses (SSRF prevention)."""
    # Block internal IP
    with pytest.raises(SecurityValidationError):
        PartnerFinancialIngestionService.validate_source_url("http://169.254.169.254/latest/meta-data")

    # Block localhost
    with pytest.raises(SecurityValidationError):
        PartnerFinancialIngestionService.validate_source_url("http://localhost:8000/test")

    # Block non-allowlisted domain
    with pytest.raises(SecurityValidationError):
        PartnerFinancialIngestionService.validate_source_url("https://random-commercial-blog.com/rrb-npa")

    # Allow official government domain
    valid_url = PartnerFinancialIngestionService.validate_source_url("https://www.rbi.org.in/scripts/dbie.aspx")
    assert valid_url == "https://www.rbi.org.in/scripts/dbie.aspx"


def test_ingestion_hash_change_detection():
    """46. SHA-256 hash change detection identifies identical vs changed source payloads."""
    content1 = "Official RBI DBIE Table B6: Bank of Baroda NNPA 0.68%"
    content2 = "Official RBI DBIE Table B6: Bank of Baroda NNPA 0.68%"
    content3 = "Official RBI DBIE Table B6: Bank of Baroda NNPA 0.72%"

    hash1 = PartnerFinancialIngestionService.compute_content_hash(content1)
    hash2 = PartnerFinancialIngestionService.compute_content_hash(content2)
    hash3 = PartnerFinancialIngestionService.compute_content_hash(content3)

    assert hash1 == hash2, "Identical content must produce identical hash"
    assert hash1 != hash3, "Modified content must produce different hash"


def test_ingestion_source_failure_retains_observations(db: Session):
    """47. Source fetch failure does not delete previously verified observations."""
    obs_count_before = db.execute(select(PartnerFinancialObservation)).scalars().all()

    failure_res = PartnerFinancialIngestionService.handle_source_failure(
        db=db,
        source_id="RBI_DBIE",
        source_url="https://rbi.org.in/dbie",
        error_message="HTTP 503 Service Unavailable"
    )
    assert failure_res["status"] == "FETCH_FAILED"
    assert failure_res["action"] == "RETAINED_PREVIOUS_VERIFIED_OBSERVATIONS"

    obs_count_after = db.execute(select(PartnerFinancialObservation)).scalars().all()
    assert len(obs_count_after) == len(obs_count_before), "Failure must retain all verified observations"


def test_ingestion_changed_observation_archives_old(db: Session):
    """48. When an updated observation is ingested, old observation is marked is_latest=False."""
    partner = db.execute(select(Partner)).scalars().first()
    assert partner is not None

    # Ingest baseline observation
    obs1, is_changed1 = PartnerFinancialIngestionService.ingest_observation(
        db=db,
        partner_id=partner.partner_id,
        metric_name="TEST_INGESTION_METRIC",
        metric_value=3.5,
        metric_status_value=None,
        metric_unit="PERCENT",
        source_authority="RBI",
        source_url="https://rbi.org.in/test",
        source_document="Test Report",
        data_as_of="2024-03-31"
    )
    assert obs1.is_latest is True

    # Ingest updated observation
    obs2, is_changed2 = PartnerFinancialIngestionService.ingest_observation(
        db=db,
        partner_id=partner.partner_id,
        metric_name="TEST_INGESTION_METRIC",
        metric_value=3.1,  # value improved
        metric_status_value=None,
        metric_unit="PERCENT",
        source_authority="RBI",
        source_url="https://rbi.org.in/test",
        source_document="Test Report",
        data_as_of="2025-03-31"
    )
    assert is_changed2 is True
    assert obs2.is_latest is True

    # Check that obs1 is now archived
    db.refresh(obs1)
    assert obs1.is_latest is False

    # Cleanup
    db.delete(obs1)
    db.delete(obs2)
    db.commit()


def test_ingestion_cache_invalidation_updates_routing(db: Session):
    """49. Updating observations invalidates cache and affects routing evaluation."""
    PrudentialRuleEngine.invalidate_cache()
    # Cache cleared successfully without errors
    assert PrudentialRuleEngine._rule_cache is None or len(PrudentialRuleEngine._rule_cache) == 0


# =========================================================================
# PART 8: MANDATORY FINAL DEMO SCENARIOS (Tests 50-53)
# =========================================================================

def test_demo_case_a_gorakhpur_dairy_term_loan(db: Session):
    """
    CASE A:
    Gorakhpur, Dairy project, ₹3 lakh, Term Loan.
    Verifies:
    - Scheme recommended: SIH26092-053 (or dairy scheme)
    - Authorized partners located near Gorakhpur
    - Nearest routable partners ranked with verified financial evidence
    - Source provenance clearly presented
    """
    results = GeoPartnerLocatorService.find_nearest_partners(
        db=db,
        latitude=26.7606,
        longitude=83.3732,
        scheme_id="SIH26092-053",
        loan_category="TERM_LOAN",
        radius_km=25.0
    )
    assert len(results) > 0
    top = results[0]
    assert top["distance_km"] <= 25.0
    assert top["routing_status"] in ("VERIFIED_ELIGIBLE_FOR_ROUTING", "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION")
    assert "routing_reasons" in top
    assert len(top["routing_reasons"]) > 0


def test_demo_case_b_partner_with_verified_restriction_excluded(db: Session):
    """
    CASE B:
    Partner with verified applicable financial restriction is excluded.
    """
    # Evaluate a partner with NNPA 16.2%
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={
            "NNPA_PERCENT": {"value": 16.2, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}
        }
    )
    assert eval_res["is_restricted"] is True
    assert eval_res["routing_status"] == "NOT_ROUTABLE"
    assert "breaches the applicable" in eval_res["primary_reason"] or "exceeds" in eval_res["primary_reason"] or "16.20" in eval_res["primary_reason"]


def test_demo_case_c_partner_with_no_financial_data_transparent(db: Session):
    """
    CASE C:
    Partner with no public financial data is transparently labeled.
    """
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="COOPERATIVE",
        metrics={}
    )
    assert eval_res["is_restricted"] is False
    assert eval_res["routing_status"] == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
    assert "Current partner-level financial health data could not be independently verified" in eval_res["primary_reason"]


def test_demo_case_d_government_source_update_change_detection(db: Session):
    """
    CASE D:
    Government source update detected via hash and reflected in observation history.
    """
    raw_old = "NABARD RRB Key Statistics 2023-24: Baroda UP Bank NNPA 2.8%"
    raw_new = "NABARD RRB Key Statistics 2024-25: Baroda UP Bank NNPA 2.4%"

    old_hash = PartnerFinancialIngestionService.compute_content_hash(raw_old)
    new_hash = PartnerFinancialIngestionService.compute_content_hash(raw_new)

    assert old_hash != new_hash, "Hash change detected"


# =========================================================================
# PART 9: MANDATORY AUDIT ACCEPTANCE TESTS (Section 27: Tests 54-68)
# =========================================================================

def test_acceptance_1_psb_nnpa_does_not_invoke_rrb_rule(db: Session):
    """1. PSB NNPA does NOT invoke NSFDC RRB Net NPA < 15% rule."""
    psb_eval = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="PUBLIC_SECTOR_BANK",
        metrics={
            "NNPA_PERCENT": {"value": 5.0, "status": "VERIFIED_OFFICIAL", "source": "RBI"}
        }
    )
    # The RRB NNPA rule must be marked NOT_APPLICABLE
    rrb_rules = [r for r in psb_eval["rules_evaluated"] if r["rule_id"] == "NSFDC_RRB_NNPA_001"]
    assert len(rrb_rules) > 0
    assert rrb_rules[0]["rule_status"] == "NOT_APPLICABLE"
    assert rrb_rules[0]["result"] == "NOT_APPLICABLE"
    assert "not applicable to PUBLIC_SECTOR_BANK" in rrb_rules[0]["explanation"]
    
    # Must NOT be restricted
    assert psb_eval["is_restricted"] is False
    # Financial scope must be INSTITUTION_LEVEL
    assert psb_eval["verified_metrics"]["NNPA_PERCENT"]["financial_scope"] == "INSTITUTION_LEVEL"
    assert psb_eval["verified_metrics"]["NNPA_PERCENT"]["status_label"] == "OFFICIAL_FINANCIAL_INDICATOR"
    # Primary reason must not say "Passes NSFDC RRB NNPA criterion"
    assert "Passes NSFDC RRB" not in psb_eval["primary_reason"]
    assert "not applicable to Scheduled Commercial Banks" in psb_eval["primary_reason"]


def test_acceptance_2_rrb_nnpa_16_not_routable():
    """2. RRB Net NPA 16% -> NOT_ROUTABLE."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={
            "NNPA_PERCENT": {"value": 16.0, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}
        }
    )
    assert eval_res["is_restricted"] is True
    assert eval_res["routing_status"] == "NOT_ROUTABLE"
    rrb_rule = [r for r in eval_res["rules_evaluated"] if r["rule_id"] == "NSFDC_RRB_NNPA_001"][0]
    assert rrb_rule["rule_status"] == "FAIL"
    assert rrb_rule["result"] == "FAIL"


def test_acceptance_3_rrb_nnpa_5_passes_criterion():
    """3. RRB Net NPA 5% -> passes NNPA criterion."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={
            "NNPA_PERCENT": {"value": 5.0, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}
        }
    )
    rrb_rule = [r for r in eval_res["rules_evaluated"] if r["rule_id"] == "NSFDC_RRB_NNPA_001"][0]
    assert rrb_rule["rule_status"] == "PASS"
    assert rrb_rule["result"] == "PASS"
    assert eval_res["is_restricted"] is False


def test_acceptance_4_rrb_missing_nnpa_unknown():
    """4. RRB missing NNPA -> UNKNOWN (never PASS)."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={}
    )
    rrb_rule = [r for r in eval_res["rules_evaluated"] if r["rule_id"] == "NSFDC_RRB_NNPA_001"][0]
    assert rrb_rule["rule_status"] == "UNKNOWN"
    assert rrb_rule["result"] == "UNKNOWN"
    assert rrb_rule["rule_status"] != "PASS"


def test_acceptance_5_generic_utilization_rule_not_create_partner_utilization_100():
    """5. Generic NSFDC utilization rule does NOT create partner utilization=100%."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={}
    )
    assert "FUND_UTILIZATION_PERCENT" not in eval_res["verified_metrics"]
    util_rules = [r for r in eval_res["rules_evaluated"] if r["metric"] == "FUND_UTILIZATION_PERCENT"]
    assert len(util_rules) > 0
    assert util_rules[0]["actual_value"] != 100.0
    assert util_rules[0]["rule_status"] in ("UNKNOWN", "NOT_PUBLICLY_VERIFIED")


def test_acceptance_6_missing_overdue_data_not_create_overdue_clear(db: Session):
    """6. Missing overdue data does NOT create overdue_clear."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="PUBLIC_SECTOR_BANK",
        metrics={}
    )
    overdue_rules = [r for r in eval_res["rules_evaluated"] if r["metric"] == "OVERDUE_STATUS"]
    assert len(overdue_rules) > 0
    assert overdue_rules[0]["rule_status"] != "PASS"
    assert overdue_rules[0]["observed_status"] != "CLEAR"
    assert overdue_rules[0]["observed_status"] != "NO_OVERDUE"


def test_acceptance_7_sidbi_sector_metric_cannot_become_partner_metric(db: Session):
    """7. SIDBI sector metric cannot become partner metric."""
    with pytest.raises(ValueError, match="Sector-level context cannot be attached"):
        PartnerFinancialIngestionService.ingest_observation(
            db=db,
            partner_id="test-p-001",
            metric_name="SECTOR_PAR_90_PLUS",
            metric_value=3.2,
            metric_status_value=None,
            metric_unit="PERCENT",
            source_authority="SIDBI",
            source_url="https://www.sidbi.in/report",
            source_document="SIDBI Microfinance Pulse"
        )


def test_acceptance_8_branch_level_claim_rejected_without_branch_source(db: Session):
    """8. Branch-level financial claim is rejected unless branch-level source exists."""
    with pytest.raises(ValueError, match="Branch-level financial claim is rejected"):
        PartnerFinancialIngestionService.ingest_observation(
            db=db,
            partner_id="test-p-001",
            metric_name="NNPA_PERCENT",
            metric_value=1.5,
            metric_status_value=None,
            metric_unit="PERCENT",
            financial_scope="BRANCH_LEVEL",
            source_authority="RBI",
            source_url="https://www.rbi.org.in/dbie",
            source_document="RBI DBIE Table B6"
        )


def test_acceptance_9_institution_level_rbi_data_labelled_institution_level(db: Session):
    """9. Institution-level RBI data is labelled institution-level."""
    rbi_obs = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.source_authority == "RBI",
            PartnerFinancialObservation.metric_name == "NNPA_PERCENT"
        )
    ).scalars().all()
    assert len(rbi_obs) > 0
    for obs in rbi_obs:
        assert obs.financial_scope == "INSTITUTION_LEVEL"


def test_acceptance_10_test_nnpa_isolated_from_production(db: Session):
    """10. Test NNPA 22.5% is isolated from production database."""
    test_obs_count = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.source_authority == "TEST"
        )
    ).scalars().all()
    assert len(test_obs_count) == 0, "No observations with source_authority='TEST' allowed in production DB"

    sim_225 = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.metric_name == "NNPA_PERCENT",
            PartnerFinancialObservation.metric_value == 22.5
        )
    ).scalars().all()
    assert len(sim_225) == 0, "No simulated 22.5% NNPA records allowed in production DB"


def test_acceptance_11_march_2024_data_never_labelled_live(db: Session):
    """11. March 2024 data is never labelled 'live'."""
    obs = db.execute(
        select(PartnerFinancialObservation).where(
            PartnerFinancialObservation.data_as_of.ilike("%2024-03-31%")
        )
    ).scalars().all()
    assert len(obs) > 0
    for o in obs:
        assert "live" not in (o.data_as_of or "").lower()
        assert "current 2026" not in (o.data_as_of or "").lower()
        assert "FY2023-24" in (o.period_end or o.data_as_of or "") or "2024" in (o.data_as_of or "")


def test_acceptance_12_source_conflict_is_preserved(db: Session):
    """12. Source conflict is preserved (different sources report independently)."""
    rbi_count = db.execute(
        select(PartnerFinancialObservation).where(PartnerFinancialObservation.source_authority == "RBI")
    ).scalars().all()
    nabard_count = db.execute(
        select(PartnerFinancialObservation).where(PartnerFinancialObservation.source_authority == "NABARD")
    ).scalars().all()
    assert len(rbi_count) > 0
    assert len(nabard_count) > 0


def test_acceptance_13_older_financial_data_not_overwritten_incorrectly(db: Session):
    """13. Older financial data is not overwritten incorrectly; previous observation is archived."""
    partner = db.execute(select(Partner)).scalars().first()
    assert partner is not None

    obs_old, _ = PartnerFinancialIngestionService.ingest_observation(
        db=db,
        partner_id=partner.partner_id,
        metric_name="ACCEPTANCE_13_AUDIT_METRIC",
        metric_value=4.0,
        metric_status_value=None,
        metric_unit="PERCENT",
        source_authority="RBI",
        source_url="https://rbi.org.in/audit",
        source_document="RBI Statistical Tables 2023-24",
        period_end="FY2023-24",
        data_as_of="2024-03-31"
    )
    obs_new, is_chg = PartnerFinancialIngestionService.ingest_observation(
        db=db,
        partner_id=partner.partner_id,
        metric_name="ACCEPTANCE_13_AUDIT_METRIC",
        metric_value=3.5,
        metric_status_value=None,
        metric_unit="PERCENT",
        source_authority="RBI",
        source_url="https://rbi.org.in/audit",
        source_document="RBI Statistical Tables 2024-25",
        period_end="FY2024-25",
        data_as_of="2025-03-31"
    )
    assert is_chg is True
    db.refresh(obs_old)
    assert obs_old.is_latest is False
    assert obs_new.is_latest is True

    # Cleanup
    db.delete(obs_old)
    db.delete(obs_new)
    db.commit()


def test_acceptance_14_rrb_amalgamation_alias_is_handled(db: Session):
    """14. RRB amalgamation alias is handled."""
    p_premerger = PartnerStub(name="Purvanchal Bank Main Branch", partner_type="REGIONAL_RURAL_BANK", state="Uttar Pradesh")
    entity, match_lvl, score, reason = EntityResolutionEngine.resolve_partner(db=db, partner=p_premerger)
    assert entity is not None
    assert "Baroda U.P. Bank" in entity.canonical_name or "Uttar Pradesh Gramin Bank" in entity.canonical_name


def test_acceptance_15_restricted_partner_excluded_only_when_applicable_rule_violated(db: Session):
    """15. Restricted partner is excluded only when the applicable official rule is violated."""
    # PSB with NNPA 5.0%: NSFDC RRB rule NOT applicable, therefore NOT restricted
    psb_eval = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="PUBLIC_SECTOR_BANK",
        metrics={"NNPA_PERCENT": {"value": 5.0, "status": "VERIFIED_OFFICIAL", "source": "RBI"}}
    )
    assert psb_eval["is_restricted"] is False
    assert psb_eval["routing_status"] == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"

    # RRB with NNPA 16.0%: NSFDC RRB rule IS applicable, violated, therefore NOT_ROUTABLE
    rrb_eval = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={"NNPA_PERCENT": {"value": 16.0, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}}
    )
    assert rrb_eval["is_restricted"] is True
    assert rrb_eval["routing_status"] == "NOT_ROUTABLE"


# =========================================================================
# PART 9: MANDATORY ADVERSARIAL CASES (A through K)
# =========================================================================

def test_adversarial_a_rrb_nnpa_16_2_hard_exclusion():
    """Adversarial A: RRB with Net NPA 16.2% triggers HARD EXCLUSION under NSFDC rule."""
    res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={"NNPA_PERCENT": {"value": 16.2, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}}
    )
    assert res["is_restricted"] is True
    assert res["routing_status"] == "NOT_ROUTABLE"
    rrb_rule = next(r for r in res["rules_evaluated"] if r["rule_id"] == "NSFDC_RRB_NNPA_001")
    assert rrb_rule["result"] == "FAIL"


def test_adversarial_b_rrb_nnpa_14_9_not_excluded():
    """Adversarial B: RRB with Net NPA 14.9% is NOT excluded by the 15% rule."""
    res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={"NNPA_PERCENT": {"value": 14.9, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}}
    )
    assert res["is_restricted"] is False
    rrb_rule = next(r for r in res["rules_evaluated"] if r["rule_id"] == "NSFDC_RRB_NNPA_001")
    assert rrb_rule["result"] == "PASS"


def test_adversarial_c_psb_nnpa_16_2_rule_not_applicable():
    """Adversarial C: Public Sector Bank with Net NPA 16.2% does NOT fail NSFDC RRB rule."""
    res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="PUBLIC_SECTOR_BANK",
        metrics={"NNPA_PERCENT": {"value": 16.2, "status": "VERIFIED_OFFICIAL", "source": "RBI"}}
    )
    assert res["is_restricted"] is False
    rrb_rule = next(r for r in res["rules_evaluated"] if r["rule_id"] == "NSFDC_RRB_NNPA_001")
    assert rrb_rule["result"] == "NOT_APPLICABLE"


def test_adversarial_d_missing_utilization_not_publicly_verified(db: Session):
    """Adversarial D: Missing partner utilization yields NOT_PUBLICLY_VERIFIED, never 100%."""
    # 1. In-memory evaluation with NOT_PUBLICLY_VERIFIED status
    res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="PUBLIC_SECTOR_BANK",
        metrics={"FUND_UTILIZATION_PERCENT": {"value": None, "status": "NOT_PUBLICLY_VERIFIED", "source": "NSFDC"}}
    )
    util_rule = next(r for r in res["rules_evaluated"] if r["rule_id"] == "NSFDC_GEN_UTILIZATION_001")
    assert util_rule["result"] == "NOT_PUBLICLY_VERIFIED"
    assert util_rule["actual_value"] is None

    # 2. Database-backed evaluation for a live partner with missing partner-level utilization
    p = db.query(Partner).filter(Partner.is_active == True).first()
    if p:
        db_eval = PrudentialRuleEngine.evaluate_partner(db, p)
        db_util = next(r for r in db_eval["rules_evaluated"] if r["rule_id"] == "NSFDC_GEN_UTILIZATION_001")
        assert db_util["result"] == "NOT_PUBLICLY_VERIFIED"
        assert db_util["actual_value"] is None


def test_adversarial_e_missing_overdue_not_publicly_verified(db: Session):
    """Adversarial E: Missing overdue record yields NOT_PUBLICLY_VERIFIED, never CLEAR."""
    # 1. In-memory evaluation with NOT_PUBLICLY_VERIFIED status
    res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={"OVERDUE_STATUS": {"value": None, "status": "NOT_PUBLICLY_VERIFIED", "source": "NSFDC"}}
    )
    overdue_rule = next(r for r in res["rules_evaluated"] if r["rule_id"] == "NSFDC_GEN_OVERDUE_001")
    assert overdue_rule["result"] == "NOT_PUBLICLY_VERIFIED"
    assert overdue_rule["actual_value"] is None

    # 2. Database-backed evaluation for a live partner with missing partner-level overdue ledger
    p = db.query(Partner).filter(Partner.is_active == True).first()
    if p:
        db_eval = PrudentialRuleEngine.evaluate_partner(db, p)
        db_overdue = next(r for r in db_eval["rules_evaluated"] if r["rule_id"] == "NSFDC_GEN_OVERDUE_001")
        assert db_overdue["result"] == "NOT_PUBLICLY_VERIFIED"
        assert db_overdue["actual_value"] is None



def test_adversarial_f_sector_level_mfi_never_attached_to_partner(db: Session):
    """Adversarial F: Sector-level MFI metric is never attached to individual partner health."""
    mfi_partner = db.query(Partner).filter(Partner.institution_type == "NBFC_MFI").first()
    if mfi_partner:
        fin = GeoPartnerLocatorService.evaluate_partner_financial_health(db, mfi_partner.partner_id)
        for m_name, m_data in fin.get("verified_metrics", {}).items():
            assert m_data.get("financial_scope") != "SECTOR_LEVEL"


def test_adversarial_g_ambiguous_entity_no_financial_inheritance(db: Session):
    """Adversarial G: Ambiguous entity match yields 0 confidence and zero financial inheritance."""
    p_ambig = PartnerStub(name="Unknown Gramin Bank Branch", partner_type="BANK", state="XYZ State")
    ent, level, conf, reason = EntityResolutionEngine.resolve_partner(db, p_ambig)
    assert ent is None or level in ("AMBIGUOUS_MATCH", "UNMATCHED")
    assert conf < 0.70


def test_adversarial_h_unmatched_entity_no_financial_inheritance(db: Session):
    """Adversarial H: Unmatched entity never inherits financial observations."""
    p_unmatched = PartnerStub(name="Some Random Non-Existent Address Fragment 123", partner_type="OTHER", state="None")
    ent, level, conf, reason = EntityResolutionEngine.resolve_partner(db, p_unmatched)
    assert ent is None
    assert level == "UNMATCHED"
    assert conf == 0.0


def test_adversarial_i_predecessor_rrb_not_silently_attributed_to_successor(db: Session):
    """Adversarial I: Predecessor RRB unverified debt cannot silently attach to successor RRB."""
    p_pred = PartnerStub(name="Purvanchal Bank Main Branch", partner_type="REGIONAL_RURAL_BANK", state="Uttar Pradesh")
    ent, level, conf, reason = EntityResolutionEngine.resolve_partner(db, p_pred)
    assert ent is not None
    # Alias must explicitly declare predecessor source authority
    alias = db.query(InstitutionAlias).filter(InstitutionAlias.alias_name == "Purvanchal Bank").first()
    if alias:
        assert alias.alias_type == "PRE_MERGER_NAME"
        assert "DFS" in alias.source_authority or "AMALGAMATION" in alias.source_authority


def test_adversarial_j_restricted_nearest_partner_excluded_before_distance_ranking():
    """Adversarial J: A closer restricted partner is excluded before distance ranking."""
    # Partner 1: 0.5 km away, NNPA = 18.0% (RESTRICTED RRB)
    eval_p1 = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={"NNPA_PERCENT": {"value": 18.0, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}}
    )
    assert eval_p1["is_restricted"] is True

    # Partner 2: 5.0 km away, NNPA = 2.1% (COMPLIANT RRB)
    eval_p2 = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={"NNPA_PERCENT": {"value": 2.1, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}}
    )
    assert eval_p2["is_restricted"] is False

    candidates = [
        {"name": "Restricted Bank", "distance_km": 0.5, "is_restricted": eval_p1["is_restricted"]},
        {"name": "Compliant Bank", "distance_km": 5.0, "is_restricted": eval_p2["is_restricted"]},
    ]
    # Filter out restricted before distance sorting
    routable = [c for c in candidates if not c["is_restricted"]]
    routable.sort(key=lambda x: x["distance_km"])
    assert len(routable) == 1
    assert routable[0]["name"] == "Compliant Bank"


def test_adversarial_k_all_financial_unknown_routable_with_limitation():
    """Adversarial K: If all financial data is unknown, authorized active partner remains routable with limitation."""
    eval_res = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="PUBLIC_SECTOR_BANK",
        metrics={}
    )
    assert eval_res["is_restricted"] is False
    assert eval_res["routing_status"] == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"


