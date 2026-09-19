import pytest
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.partner import Partner
from app.engine.entity_resolution import EntityResolutionEngine


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_corrupted_address_fragments_never_resolve(db: Session):
    """
    Forensic anti-fabrication check:
    Address fragments and PDF artifacts must NEVER resolve to an InstitutionEntity.
    """
    fragments = [
        "Mumbai 400 021",
        "Ranchi-834001",
        "Complex",
        "Tikiapara",
        "Plot No.-47",
        "9th & 10th Floor, Jeevan Deep Building",
        "834001",
        "B-912",
    ]
    for frag in fragments:
        fake_partner = Partner(
            partner_id=f"TEST-{hash(frag)}",
            name=frag,
            partner_type="PUBLIC_SECTOR_BANK",
            state="Maharashtra",
            is_active=True,
            record_status="ACTIVE",
        )
        entity, match_level, score, exp = EntityResolutionEngine.resolve_partner(db, fake_partner)
        assert entity is None, f"Corrupted fragment '{frag}' must NOT resolve to an institution, got: {entity}"
        assert match_level in ("CORRUPTED_FRAGMENT", "UNMATCHED")


def test_quarantined_partner_never_resolves(db: Session):
    """Quarantined partner records must never resolve to an institution entity."""
    quarantined = Partner(
        partner_id="TEST-QUARANTINED-001",
        name="State Bank of India Quarantined Branch",
        partner_type="PUBLIC_SECTOR_BANK",
        record_status="QUARANTINED",
        quarantine_reason="Corrupted extraction record",
        is_active=False,
    )
    entity, match_level, score, exp = EntityResolutionEngine.resolve_partner(db, quarantined)
    assert entity is None
    assert match_level == "QUARANTINED"


def test_exact_canonical_name_matches(db: Session):
    """Exact canonical name matches at high confidence."""
    p = Partner(
        partner_id="TEST-SBI-001",
        name="State Bank of India",
        partner_type="PUBLIC_SECTOR_BANK",
        state="Maharashtra",
        is_active=True,
        record_status="ACTIVE",
    )
    entity, match_level, score, exp = EntityResolutionEngine.resolve_partner(db, p)
    assert entity is not None
    assert entity.canonical_name == "State Bank of India"
    assert match_level in ("MATCH_LEVEL_2", "MATCH_LEVEL_3", "MATCH_LEVEL_5")
    assert score >= 0.75


def test_generic_single_word_bank_does_not_overmatch(db: Session):
    """Generic words like 'Bank' or 'India' must never overmatch to a random bank."""
    p = Partner(
        partner_id="TEST-GENERIC-001",
        name="Bank",
        partner_type="PUBLIC_SECTOR_BANK",
        state="Maharashtra",
        is_active=True,
        record_status="ACTIVE",
    )
    entity, match_level, score, exp = EntityResolutionEngine.resolve_partner(db, p)
    assert entity is None
