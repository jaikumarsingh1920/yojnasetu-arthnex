import os
import sys
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.partner import Partner
from app.models.scheme import Scheme
from app.models.user import User, UserRole
from app.models.financial_intelligence import InstitutionEntity, PartnerFinancialObservation
from app.services.ingestion.promotion_service import CandidatePromotionService
from app.services.admin_service import AdminService
from app.engine.prudential_rule_engine import PrudentialRuleEngine

DB_PATH = os.path.join(BACKEND_DIR, "app", "yojnasetu.db")


@pytest.fixture(scope="module")
def real_db_session():
    """Provides a read-only session to the real SQLite DB for verification."""
    if not os.path.exists(DB_PATH):
        pytest.skip("yojnasetu.db not found")
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_scheme_sequence_generation_beyond_859(real_db_session):
    """Verify that scheme ID sequence correctly continues to SIH26092-860 after 859 canonical schemes."""
    next_id = CandidatePromotionService.generate_next_scheme_id(real_db_session)
    assert next_id == "SIH26092-860", f"Expected SIH26092-860, but got {next_id}"


def test_punjab_and_sind_bank_entity_resolution(real_db_session):
    """Verify that partner 6b8dc71e-28b2-47a6-8b9e-02a4c3bc94d7 is resolved to Punjab & Sind Bank."""
    partner_id = "6b8dc71e-28b2-47a6-8b9e-02a4c3bc94d7"
    partner = real_db_session.execute(
        select(Partner).where(Partner.partner_id == partner_id)
    ).scalar_one_or_none()

    assert partner is not None, "Partner not found in database"
    assert partner.name == "Punjab & Sind Bank", f"Expected 'Punjab & Sind Bank', got '{partner.name}'"
    assert "21 Rajendra Place" in (partner.address or ""), f"Expected Rajendra Place in address, got '{partner.address}'"
    assert partner.city == "New Delhi", f"Expected city 'New Delhi', got '{partner.city}'"
    assert partner.state == "Delhi", f"Expected state 'Delhi', got '{partner.state}'"
    assert partner.pincode == "110008", f"Expected pincode '110008', got '{partner.pincode}'"

    # Verify canonical institution exists for Punjab & Sind Bank
    inst = real_db_session.execute(
        select(InstitutionEntity).where(InstitutionEntity.canonical_name == "Punjab & Sind Bank")
    ).scalars().first()
    assert inst is not None, "InstitutionEntity Punjab & Sind Bank must exist"

    # Verify financial observations exist and have INSTITUTION scope
    obs_list = real_db_session.execute(
        select(PartnerFinancialObservation).where(PartnerFinancialObservation.partner_id == partner_id)
    ).scalars().all()
    assert len(obs_list) > 0, "Punjab & Sind Bank partner must have verified financial observations"
    for obs in obs_list:
        assert obs.financial_scope in ("INSTITUTION_LEVEL", "POLICY_LEVEL"), f"Scope must be INSTITUTION_LEVEL or POLICY_LEVEL, got {obs.financial_scope}"
        assert obs.financial_scope != "PARTNER_LEVEL", "Partner-level financial metrics must never be fabricated"


def test_admin_system_health_separated(real_db_session):
    """Verify system health separates AI Provider (truthful fallback) and RAG Engine (19,863 chunks)."""
    health = AdminService.get_system_health(real_db_session)
    assert health is not None
    assert len(health.components) > 0

    comp_map = {c.name: c for c in health.components}
    assert "YojnaSetu AI Provider" in comp_map
    assert "YojnaSetu RAG Engine" in comp_map

    ai_provider = comp_map["YojnaSetu AI Provider"]
    rag_engine = comp_map["YojnaSetu RAG Engine"]

    assert ai_provider.status == "DEGRADED"
    assert rag_engine.status == "ONLINE"
    assert rag_engine.details.get("indexed_schemes") == 859
    assert rag_engine.details.get("total_chunks") == 19863

    # Ensure no API secret is leaked in details
    for comp in health.components:
        for k, v in comp.details.items():
            val_str = str(v)
            assert "AIza" not in val_str, "API secrets must never be leaked in health details"


def test_admin_dashboard_summary_partner_metrics(real_db_session):
    """Verify admin dashboard summary metrics reflect accurate canonical institutions and geocoded partner locations."""
    mock_admin = User(user_id="test_admin_id", role=UserRole.SYSTEM_ADMIN.value)
    summary = AdminService.get_dashboard_summary(db=real_db_session, current_user=mock_admin)
    # Canonical institutions verified from database (81 canonical institution entities)
    assert summary.total_partner_institutions == 81
    assert summary.known_partner_locations == 170
    assert summary.geocoded_locations == 165
    assert summary.ungeocoded_locations == 5


def test_rrb_vs_psb_prudential_rule_isolation():
    """Verify that RRB NNPA rule applies strictly to RRBs and never to PSBs."""
    # PSB with NNPA 16.2% must NOT be restricted by the RRB NNPA rule
    psb_result = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="PUBLIC_SECTOR_BANK",
        metrics={"NNPA_PERCENT": {"value": 16.2, "status": "VERIFIED_OFFICIAL", "source": "RBI"}}
    )
    rrb_rule_evals = [r for r in psb_result["rules_evaluated"] if r.get("metric") == "NNPA_PERCENT" and "RRB" in r.get("rule_id", "")]
    assert len(rrb_rule_evals) > 0, "RRB rule evaluation record should be present"
    assert rrb_rule_evals[0]["rule_status"] == "NOT_APPLICABLE", "RRB NNPA rule must be marked NOT_APPLICABLE for Public Sector Bank"
    assert psb_result["is_restricted"] is False

    # RRB with NNPA 16.2% MUST fail and be restricted
    rrb_result = PrudentialRuleEngine.evaluate_partner_financial_facts(
        institution_type="RRB",
        metrics={"NNPA_PERCENT": {"value": 16.2, "status": "VERIFIED_OFFICIAL", "source": "NABARD"}}
    )
    rrb_rule_evals_for_rrb = [r for r in rrb_result["rules_evaluated"] if r.get("metric") == "NNPA_PERCENT"]
    assert len(rrb_rule_evals_for_rrb) > 0, "RRB rule must be evaluated for RRB"
    assert rrb_rule_evals_for_rrb[0]["rule_status"] == "FAIL"
    assert rrb_result["is_restricted"] is True
