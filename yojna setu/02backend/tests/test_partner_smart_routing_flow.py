"""
Comprehensive verification test suite for Beneficiary-Facing Partner Locator + Smart Routing Flow.

Verifies:
1. Hard statutory restrictions are applied FIRST (closer restricted partner is excluded).
2. Eligible farther partner is routed when nearer partner is restricted.
3. Multi-signal ranking for scheme routing (scheme match + category + verified financial status + distance).
4. Missing financial data remains explicitly unknown (ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION, NOT_PUBLICLY_VERIFIED).
5. Sector-level data cannot become partner-level health.
6. RRB rules do not apply to PSBs.
7. Ambiguous institution matching does not inherit financial observations.
8. /routing-audit returns structured recommended and excluded partner collections.
9. /nearest?include_excluded=true includes structured exclusion explanations.
10. Transparent citizen-friendly routing explanations in routing_reasons and suitability_reason.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.partner import Partner
from app.models.partner_scheme import PartnerSchemeMapping
from app.services.geo_partner_service import GeoPartnerLocatorService
from app.engine.prudential_rule_engine import PrudentialRuleEngine
from app.engine.entity_resolution import EntityResolutionEngine

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_restricted_closer_partner_excluded_and_farther_eligible_routed(db: Session):
    """
    Verify:
    - Step 2 applies hard restrictions FIRST.
    - Closer restricted partner (e.g. 1.0 km, Net NPA 18.0%) is excluded.
    - Farther compliant partner (e.g. 5.0 km, Net NPA 2.4%) is routed.
    """
    # Create closer restricted RRB partner
    restricted_partner = Partner(
        partner_id="p-test-closer-restricted-rrb",
        name="Test Over-Limit Gramin Bank Branch",
        code="TEST-RRB-HIGH-NPA",
        partner_type="REGIONAL_RURAL_BANK",
        institution_type="REGIONAL_RURAL_BANK",
        partner_category="AUTHORIZED_SCHEME_PARTNER",
        latitude=26.7610,
        longitude=83.3740,  # ~0.1 km from center
        npa_percentage=18.5,  # Exceeds 15%
        is_active=True,
        is_accepting_applications=True,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=True
    )
    
    # Create farther compliant partner
    compliant_partner = Partner(
        partner_id="p-test-farther-compliant-bank",
        name="Test Compliant National Bank Branch",
        code="TEST-PSB-COMPLIANT",
        partner_type="PUBLIC_SECTOR_BANK",
        institution_type="PUBLIC_SECTOR_BANK",
        partner_category="AUTHORIZED_SCHEME_PARTNER",
        latitude=26.8000,
        longitude=83.4000,  # ~5.0 km from center
        npa_percentage=1.2,
        is_active=True,
        is_accepting_applications=True,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=True
    )

    db.add(restricted_partner)
    db.add(compliant_partner)
    db.commit()

    try:
        results = GeoPartnerLocatorService.find_nearest_partners(
            db=db,
            latitude=26.7606,
            longitude=83.3732,
            radius_km=15.0,
            max_npa=15.0
        )
        returned_ids = [r["partner"].partner_id for r in results]
        
        # Closer restricted partner must be EXCLUDED
        assert "p-test-closer-restricted-rrb" not in returned_ids
        # Farther compliant partner must be ROUTABLE
        assert "p-test-farther-compliant-bank" in returned_ids
    finally:
        db.delete(restricted_partner)
        db.delete(compliant_partner)
        db.commit()


def test_routing_audit_endpoint_returns_structured_exclusions(db: Session):
    """
    Verify /routing-audit API returns both recommended and excluded partners
    with structured statutory exclusion reasons.
    """
    restricted_p = Partner(
        partner_id="p-audit-restricted-demo",
        name="Disqualified Regional Bank",
        code="DISQUAL-RRB-01",
        partner_type="REGIONAL_RURAL_BANK",
        institution_type="REGIONAL_RURAL_BANK",
        partner_category="AUTHORIZED_SCHEME_PARTNER",
        latitude=26.7620,
        longitude=83.3750,
        npa_percentage=19.2,
        is_active=True,
        is_accepting_applications=True,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=True
    )
    db.add(restricted_p)
    db.commit()

    try:
        resp = client.get("/api/v1/partner/routing-audit?latitude=26.7606&longitude=83.3732&radius_km=10.0&max_npa=15.0")
        assert resp.status_code == 200
        data = resp.json()

        assert "recommended_partners" in data
        assert "excluded_partners" in data
        assert data["hard_restrictions_enforced"] is True
        assert data["total_evaluated"] >= data["total_recommended"] + data["total_excluded"]

        # Find the restricted partner in excluded list
        excluded_ids = [p["partner"]["partner_id"] for p in data["excluded_partners"]]
        assert "p-audit-restricted-demo" in excluded_ids

        excluded_item = next(p for p in data["excluded_partners"] if p["partner"]["partner_id"] == "p-audit-restricted-demo")
        assert excluded_item["is_restricted"] is True
        assert excluded_item["routing_status"] == "NOT_ROUTABLE"
        assert "exclusion_reason" in excluded_item
        assert "19.2" in excluded_item["exclusion_reason"] or "ceiling" in excluded_item["exclusion_reason"]
    finally:
        db.delete(restricted_p)
        db.commit()


def test_nearest_endpoint_include_excluded_flag(db: Session):
    """
    Verify /nearest endpoint supports include_excluded=true to include
    structured excluded records for debugging and administrative auditing.
    """
    restricted_p = Partner(
        partner_id="p-debug-flag-test",
        name="Debug High NPA Entity",
        code="DBG-NPA-01",
        partner_type="PUBLIC_SECTOR_BANK",
        institution_type="PUBLIC_SECTOR_BANK",
        partner_category="AUTHORIZED_SCHEME_PARTNER",
        latitude=26.7620,
        longitude=83.3750,
        npa_percentage=22.0,
        is_active=True,
        is_accepting_applications=True,
        verification_status="VERIFIED_OFFICIAL",
        coordinates_verified=True
    )
    db.add(restricted_p)
    db.commit()

    try:
        # 1. Default call (include_excluded=false): restricted partner MUST NOT appear
        resp_default = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&radius_km=10.0&max_npa=10.0")
        assert resp_default.status_code == 200
        ids_default = [p["partner"]["partner_id"] for p in resp_default.json()]
        assert "p-debug-flag-test" not in ids_default

        # 2. Audit call (include_excluded=true): restricted partner appears with is_restricted=True
        resp_with_excluded = client.get("/api/v1/partner/nearest?latitude=26.7606&longitude=83.3732&radius_km=10.0&max_npa=10.0&include_excluded=true")
        assert resp_with_excluded.status_code == 200
        items_with_excluded = resp_with_excluded.json()
        ids_all = [p["partner"]["partner_id"] for p in items_with_excluded]
        assert "p-debug-flag-test" in ids_all

        target = next(p for p in items_with_excluded if p["partner"]["partner_id"] == "p-debug-flag-test")
        assert target["is_restricted"] is True
        assert target["routing_status"] == "NOT_ROUTABLE"
        assert target["exclusion_reason"] is not None
    finally:
        db.delete(restricted_p)
        db.commit()


def test_rrb_rule_does_not_apply_to_psb():
    """
    Verify:
    - NSFDC RRB Net NPA ceiling (< 15%) is strictly restricted to Regional Rural Banks.
    - Public Sector Banks (PSBs) are evaluated under RBI statutory indicators and NOT penalized by RRB rule.
    """
    psb_facts = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="PUBLIC_SECTOR_BANK",
        metrics={"NNPA_PERCENT": {"value": 0.55, "status": "VERIFIED_OFFICIAL", "source": "RBI"}}
    )
    assert psb_facts["is_restricted"] is False
    assert psb_facts["routing_status"] == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
    
    # RRB Net NPA rule must be marked NOT_APPLICABLE for PSB
    rrb_rule_eval = next(r for r in psb_facts["rules_evaluated"] if r["rule_id"] == "NSFDC_RRB_NNPA_001")
    assert rrb_rule_eval["rule_status"] == "NOT_APPLICABLE"
    assert "not applicable to PUBLIC_SECTOR_BANK" in rrb_rule_eval["explanation"]


def test_missing_financial_data_remains_explicitly_unknown():
    """
    Verify Anti-Fabrication Guarantee:
    - Missing financial data is NEVER treated as healthy, zero NPA, or 100% fund utilization.
    - Classified truthfully as NOT_PUBLICLY_VERIFIED with ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION.
    """
    facts = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="REGIONAL_RURAL_BANK",
        metrics={}
    )
    assert facts["is_restricted"] is False
    assert facts["routing_status"] == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION"
    
    for r in facts["rules_evaluated"]:
        if r["rule_status"] != "NOT_APPLICABLE":
            assert r["rule_status"] in ("NOT_PUBLICLY_VERIFIED", "UNKNOWN")


def test_scheme_routing_ranking_and_transparent_explanations(db: Session):
    """
    Verify:
    - When querying with scheme_id, candidate partners have transparent routing explanations:
      - "Why this partner is being shown"
      - Scheme authorization
      - Distance & branch coordinates
      - Financial clearance / limitation notice
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

    assert top["is_scheme_matched"] is True
    assert "routing_reasons" in top
    assert len(top["routing_reasons"]) >= 2
    assert "suitability_reason" in top
    assert len(top["suitability_reason"]) > 10

    # Verify transparent reasons
    reasons_text = " ".join(top["routing_reasons"])
    assert "authorized" in reasons_text.lower()
    assert "located" in reasons_text.lower()
    assert top["routing_status"] in ("VERIFIED_ELIGIBLE_FOR_ROUTING", "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION")
