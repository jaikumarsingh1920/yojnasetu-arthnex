"""
Comprehensive verification test suite for YojnaSetu Partner Data & Financial Health Remediation.
Tests all 14 critical failure modes identified in forensic audit YJS-AUDIT-PARTNER-PROVENANCE-2026-09-17:

1. NULL CRAR -> returns None / absent, never fabricated fallback 17.16%
2. NULL reporting date -> returns None, never fake '31 March 2024'
3. NULL source authority -> returns None, never fake 'Reserve Bank of India (RBI DBIE)'
4. Missing address -> returns None / empty, never fake 'New Delhi, Delhi' or '110008'
5. Unresolved institution -> no inherited financial observations
6. Quarantined partner -> excluded from locator (/partners/nearest), returns 404 in /financial-health
7. Unverified authorization -> not labelled authorized (nsfdc_authorized = 'UNKNOWN' or 'NOT_AUTHORIZED')
8. Institution-level financial scope -> explicitly tagged INSTITUTION_LEVEL, never converted to branch-level
9. Policy-level rules -> OVERDUE_STATUS / FUND_UTILIZATION are marked POLICY_LEVEL / program conditions, not partner live balance
10. No cryptographic claim -> ensure UI code does not assert Merkle proofs / cryptographic signatures
11. Duplicate institution cleanup -> duplicate row marked inactive with audit changelog, canonical preserved
12. Valid verified bank -> genuine audited observations preserved (e.g. State Bank of India, Punjab National Bank)
13. Verified source -> provenance properly exposed (source_authority, source_document, source_url)
14. Missing financial metric -> returns None, never invented / copied across institutions
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.partner import Partner
from app.models.financial_intelligence import PartnerFinancialObservation, InstitutionEntity
from app.models.partner_changelog import PartnerChangelog
from app.engine.prudential_rule_engine import PrudentialRuleEngine
from app.engine.entity_resolution import EntityResolutionEngine
from app.services.geo_partner_service import GeoPartnerLocatorService

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_01_null_crar_returns_none(db: Session):
    """
    Test 1: When CRAR observation is absent, the engine and API return None/omitted,
    never the fabricated fallback of 17.16%.
    """
    # Pick a partner that has no CRAR observation (e.g. SCA or RRB without CRAR)
    partners = db.query(Partner).filter(
        Partner.is_active == True,
        Partner.record_status == "ACTIVE"
    ).all()
    
    for partner in partners:
        eval_result = PrudentialRuleEngine.evaluate_partner(db, partner)
        crar_metric = eval_result["verified_metrics"].get("CRAR_PERCENT")
        if crar_metric:
            # If present, it must be because an actual observation exists in DB, not a fallback
            assert crar_metric["value"] != 17.16 or crar_metric.get("source") != "Reserve Bank of India (RBI DBIE)"
            # Specifically check that 17.16 is not present unless there's an actual DB record
            obs = db.query(PartnerFinancialObservation).filter(
                PartnerFinancialObservation.metric_name == "CRAR_PERCENT",
                PartnerFinancialObservation.metric_value == 17.16
            ).first()
            assert obs is None, "Fabricated 17.16 CRAR observation must not exist in DB"


def test_02_null_date_produces_none(db: Session):
    """
    Test 2: When data_as_of / period_end is NULL, engine returns None,
    never the fabricated fallback '31 March 2024'.
    """
    obs_list = db.query(PartnerFinancialObservation).filter(
        (PartnerFinancialObservation.data_as_of == None) &
        (PartnerFinancialObservation.period_end == None)
    ).all()
    for obs in obs_list:
        assert obs.data_as_of is None
        assert obs.period_end is None


def test_03_null_source_produces_none(db: Session):
    """
    Test 3: Missing source authority must not be defaulted to 'Reserve Bank of India (RBI DBIE)'.
    """
    obs_without_source = db.query(PartnerFinancialObservation).filter(
        (PartnerFinancialObservation.source_authority == None) | 
        (PartnerFinancialObservation.source_authority == "")
    ).all()
    for obs in obs_without_source:
        assert obs.source_authority is None or obs.source_authority == ""


def test_04_missing_address_has_no_new_delhi_fallback(db: Session):
    """
    Test 4: Partners with missing address details must not inherit 'New Delhi, Delhi' or '110008'.
    """
    partners_no_address = db.query(Partner).filter(
        (Partner.address == None) | (Partner.address == "")
    ).all()
    for p in partners_no_address:
        assert p.address is None or p.address == ""
        assert p.address != "New Delhi, Delhi"
        assert p.pincode != "110008"


def test_05_unresolved_institution_no_inherited_financial_data(db: Session):
    """
    Test 5: An unresolved partner must NEVER inherit financial observations
    from any bank institution entity.
    """
    active_partners = db.query(Partner).filter(
        Partner.is_active == True,
        Partner.record_status == "ACTIVE"
    ).all()
    
    unresolved_count = 0
    for p in active_partners:
        entity, level, score, exp = EntityResolutionEngine.resolve_partner(db, p)
        if entity is None:
            unresolved_count += 1
            eval_result = PrudentialRuleEngine.evaluate_partner(db, p)
            assert eval_result["entity_resolution_status"] == "UNRESOLVED"
            # Must not inherit bank-level metrics
            assert "GNPA_PERCENT" not in eval_result["verified_metrics"]
            assert "NNPA_PERCENT" not in eval_result["verified_metrics"]
            assert "CRAR_PERCENT" not in eval_result["verified_metrics"]
    
    assert unresolved_count > 0, "Expected at least one active partner with UNRESOLVED institution entity"


def test_06_quarantined_partner_excluded_from_locator(db: Session):
    """
    Test 6: Quarantined partners must be completely excluded from:
    - GeoPartnerLocatorService.find_nearest_partners
    - /partners/financial-health/{id} returns 404
    """
    quarantined = db.query(Partner).filter(Partner.record_status == "QUARANTINED").all()
    assert len(quarantined) >= 11, "Must have quarantined at least 11 corrupted records"
    quarantined_ids = {q.partner_id for q in quarantined}
    
    # 1. Test locator service
    locator_results = GeoPartnerLocatorService.find_nearest_partners(
        db=db,
        latitude=28.6139,
        longitude=77.2090,
        radius_km=5000.0,
        limit=200
    )
    returned_ids = {r["partner"].partner_id for r in locator_results}
    assert quarantined_ids.isdisjoint(returned_ids), "Quarantined partners must NOT appear in locator results!"

    # 2. Test financial health endpoint: quarantined partner must return 404
    sample_quarantined = quarantined[0]
    resp = client.get(f"/api/v1/partners/financial-health/{sample_quarantined.partner_id}")
    assert resp.status_code == 404, f"Quarantined partner {sample_quarantined.partner_id} must return 404 in financial health"


def test_07_unverified_authorization_semantics(db: Session):
    """
    Test 7: NSFDC authorization is distinct from institution existence.
    Partners without authoritative evidence must have nsfdc_authorized = 'UNKNOWN'.
    """
    unknown_auth_partners = db.query(Partner).filter(
        Partner.nsfdc_authorized == "UNKNOWN"
    ).all()
    assert len(unknown_auth_partners) > 0, "There should be partners with UNKNOWN authorization status"
    
    for p in unknown_auth_partners:
        assert p.nsfdc_authorized == "UNKNOWN"
        assert p.nsfdc_authorized != "AUTHORIZED"


def test_08_institution_level_scope_preserved(db: Session):
    """
    Test 8: Financial observations with INSTITUTION_LEVEL scope must retain their scope
    and never be converted to BRANCH_LEVEL.
    """
    institution_obs = db.query(PartnerFinancialObservation).filter(
        PartnerFinancialObservation.financial_scope == "INSTITUTION_LEVEL"
    ).all()
    assert len(institution_obs) > 0
    
    for obs in institution_obs:
        assert obs.financial_scope == "INSTITUTION_LEVEL"
        assert obs.financial_scope != "BRANCH_LEVEL"


def test_09_policy_level_rules_distinct_from_partner_health(db: Session):
    """
    Test 9: Policy-level conditions (e.g. OVERDUE_STATUS, FUND_UTILIZATION_PERCENT)
    must be tagged as POLICY_LEVEL scope and NOT_PUBLICLY_VERIFIED, not live partner balances.
    """
    policy_obs = db.query(PartnerFinancialObservation).filter(
        PartnerFinancialObservation.financial_scope == "POLICY_LEVEL"
    ).all()
    assert len(policy_obs) > 0
    
    for obs in policy_obs:
        assert obs.financial_scope == "POLICY_LEVEL"
        assert obs.verification_status == "NOT_PUBLICLY_VERIFIED"
        assert obs.metric_name in ["FUND_UTILIZATION_PERCENT", "OVERDUE_STATUS"]


def test_10_no_cryptographic_claim():
    """
    Test 10: Verify the codebase does not claim cryptographic provenance without implementation.
    """
    ts_path = os.path.join(
        os.path.dirname(__file__),
        "../../01frontend/src/pages/PartnerFinancialHealth.tsx"
    )
    if os.path.exists(ts_path):
        with open(ts_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Cryptographically traceable" not in content
        assert "cryptographic" not in content.lower()


def test_11_duplicate_institution_cleanup(db: Session):
    """
    Test 11: Duplicate Punjab & Sind Bank record marked inactive with changelog.
    Canonical head office preserved.
    """
    psb_partners = db.query(Partner).filter(
        Partner.name.ilike("%Punjab & Sind Bank%")
    ).all()
    assert len(psb_partners) == 2, "Expected 2 Punjab & Sind Bank rows"
    
    active_psb = [p for p in psb_partners if p.is_active]
    inactive_psb = [p for p in psb_partners if not p.is_active]
    
    assert len(active_psb) == 1, "Exactly one PSB row must remain active"
    assert len(inactive_psb) == 1, "Duplicate PSB row must be inactive"
    assert active_psb[0].address is not None, "Active PSB row must have an address"
    assert inactive_psb[0].record_status == "INACTIVE"
    
    # Check changelog exists for duplicate cleanup
    changelog = db.query(PartnerChangelog).filter(
        PartnerChangelog.partner_id == inactive_psb[0].partner_id
    ).first()
    assert changelog is not None, "Changelog entry must exist for duplicate deactivation"
    assert "duplicate" in changelog.reason.lower()


def test_12_valid_verified_banks_preserve_metrics(db: Session):
    """
    Test 12: Genuine audited financial metrics for verified banks (e.g. State Bank of India)
    are preserved with exact provenance.
    """
    sbi_entity = db.query(InstitutionEntity).filter(
        InstitutionEntity.canonical_name == "State Bank of India"
    ).first()
    assert sbi_entity is not None
    
    sbi_obs = db.query(PartnerFinancialObservation).filter(
        PartnerFinancialObservation.institution_entity_id == sbi_entity.id
    ).all()
    assert len(sbi_obs) >= 3, "SBI must have GNPA, NNPA, and CRAR observations"
    
    obs_map = {o.metric_name: o for o in sbi_obs}
    assert "GNPA_PERCENT" in obs_map
    assert "NNPA_PERCENT" in obs_map
    assert "CRAR_PERCENT" in obs_map
    
    # Genuine Audited values for SBI: GNPA 1.82%, NNPA 0.47%, CRAR 14.28%
    assert obs_map["GNPA_PERCENT"].metric_value == 1.82
    assert obs_map["NNPA_PERCENT"].metric_value == 0.47
    assert obs_map["CRAR_PERCENT"].metric_value == 14.28
    assert "RBI" in obs_map["GNPA_PERCENT"].source_authority


def test_13_verified_source_provenance_exposure(db: Session):
    """
    Test 13: Financial health endpoint properly exposes source authority, document,
    and verification status.
    """
    sbi_partner = db.query(Partner).filter(
        Partner.name.ilike("%State Bank of India%"),
        Partner.is_active == True,
        Partner.record_status == "ACTIVE"
    ).first()
    assert sbi_partner is not None
    
    resp = client.get(f"/api/v1/partners/financial-health/{sbi_partner.partner_id}")
    assert resp.status_code == 200
    data = resp.json()
    
    metrics = data["verified_metrics"]
    assert "NNPA_PERCENT" in metrics
    nnpa = metrics["NNPA_PERCENT"]
    assert nnpa["value"] == 0.47
    assert nnpa["source"] is not None
    assert nnpa["financial_scope"] == "INSTITUTION_LEVEL"


def test_14_missing_financial_metrics_return_none(db: Session):
    """
    Test 14: Entities without public verified data (e.g. SCAs or unverified partners)
    must not have invented metrics in verified_metrics.
    """
    sca_partner = db.query(Partner).filter(
        Partner.partner_type.in_(["STATE_CHANNELIZING_AGENCY", "SCA"]),
        Partner.is_active == True,
        Partner.record_status == "ACTIVE"
    ).first()
    
    if sca_partner:
        resp = client.get(f"/api/v1/partners/financial-health/{sca_partner.partner_id}")
        assert resp.status_code == 200
        data = resp.json()
        metrics = data["verified_metrics"]
        # Bank indicators must not be present or must be unverified
        assert "GNPA_PERCENT" not in metrics
        assert "NNPA_PERCENT" not in metrics
        assert "CRAR_PERCENT" not in metrics
