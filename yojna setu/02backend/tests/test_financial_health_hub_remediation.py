"""
Test suite for Financial Health Hub Data & UI Remediation (SIH26092).

Verifies:
1. Scheme count is not artificially capped (returns all canonical schemes).
2. Scheme aggregation returns all intended schemes with truthful partner counts (total = verified + limited).
3. HTML entity normalization (&quot; -> ", &amp; -> &, &amp;amp; -> &, &lt; -> <, etc.).
4. Raw HTML tag removal and spacing normalization (<br>, <p>, etc.).
5. Markdown artifact normalization (**bold**, __italic__).
6. Long description splitting into concise overview and full details.
7. Quarantine exclusion from all scheme-level and partner-level aggregates.
8. Unresolved entity isolation without financial data inheritance.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.models.partner import Partner
from app.models.partner_scheme import PartnerSchemeMapping
from app.services.channel_partner_enrichment_service import ChannelPartnerEnrichmentService
from app.utils.text_sanitizer import (
    normalize_gov_text,
    clean_gov_title,
    clean_gov_description,
    split_overview_and_details,
)

client = TestClient(app)


def test_01_scheme_count_not_artificially_capped():
    """Verify GET /api/v1/partners/financial-health/schemes is not capped at 100 or 150."""
    resp = client.get("/api/v1/partners/financial-health/schemes?limit=1000")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Must return all 859 canonical schemes
    assert len(data) == 859, f"Expected 859 schemes, got {len(data)}"


def test_02_scheme_aggregation_all_intended_schemes_and_truthful_math():
    """Verify every scheme satisfies total_channel_partners = verified + limited."""
    resp = client.get("/api/v1/partners/financial-health/schemes?limit=1000")
    assert resp.status_code == 200
    data = resp.json()

    mapped_count = 0
    direct_count = 0
    for s in data:
        total = s["channel_partners_count"]
        ver = s["with_verified_financial_info_count"]
        lim = s["limited_information_count"]
        # Truthful invariant
        assert total == ver + lim, f"Scheme {s['scheme_id']}: {total} != {ver} + {lim}"
        if total > 0:
            mapped_count += 1
            assert s["delivery_mode"] == "FINANCIAL_INTERMEDIARY"
        else:
            direct_count += 1
            assert s["delivery_mode"] == "DIRECT_DEPARTMENTAL_OR_ONLINE"

    assert mapped_count == 425, f"Expected 425 credit/partner schemes, got {mapped_count}"
    assert direct_count == 434, f"Expected 434 direct departmental schemes, got {direct_count}"


def test_03_html_entity_normalization():
    """Verify recursive HTML entity decoding (&quot;, &amp;, &amp;amp;, etc.)."""
    raw1 = 'The &quot;Credit Linked Capital Subsidy&quot; Scheme'
    assert clean_gov_title(raw1) == 'The "Credit Linked Capital Subsidy" Scheme'

    # Double encoded
    raw2 = 'Delhi Khadi &amp;amp; Village Industries Board'
    assert clean_gov_title(raw2) == 'Delhi Khadi & Village Industries Board'

    raw3 = 'Loans &lt;= Rs. 50,000 &amp; Interest &gt; 5%'
    assert normalize_gov_text(raw3) == 'Loans <= Rs. 50,000 & Interest > 5%'

    # Outer quotes removal
    raw4 = '"National SC/ST Hub Scheme"'
    assert clean_gov_title(raw4) == 'National SC/ST Hub Scheme'


def test_04_raw_html_tag_removal_and_normalization():
    """Verify <br>, <br />, <p>, etc. are safely converted or removed."""
    raw = 'Line one.<br><br >Line two.<p>Paragraph three.</p>'
    cleaned = normalize_gov_text(raw)
    assert '<br' not in cleaned
    assert '<p' not in cleaned
    assert '</p>' not in cleaned
    assert 'Line one. Line two.' in cleaned
    assert 'Paragraph three.' in cleaned


def test_05_markdown_artifact_normalization():
    """Verify markdown bold/italic stars and hashtags are stripped cleanly."""
    raw = '### Scheme Purpose\n**Eligible Entities:** All SC/ST units with __valid__ registration.'
    cleaned = normalize_gov_text(raw)
    assert '**' not in cleaned
    assert '__' not in cleaned
    assert '###' not in cleaned
    assert 'Scheme Purpose' in cleaned
    assert 'Eligible Entities: All SC/ST units with valid registration.' in cleaned


def test_06_long_description_handling_overview_split():
    """Verify long descriptions are split into concise overview and full details."""
    long_desc = (
        'Prime Minister Employment Generation Programme (PMEGP) is a major credit-linked subsidy programme '
        'aimed at generating self-employment opportunities through establishment of micro-enterprises in non-farm sector. '
        'The scheme is implemented by Khadi and Village Industries Commission (KVIC) functioning as the nodal agency at the national level. '
        'At the state level, the scheme is implemented through State KVIC Directorates, State Khadi and Village Industries Boards (KVIBs), '
        'District Industries Centres (DICs) and banks.'
    )
    overview, full_details = split_overview_and_details(long_desc, target_words=25)
    assert len(overview) > 0
    assert len(overview) < len(full_details)
    assert full_details == normalize_gov_text(long_desc)
    assert overview.startswith('Prime Minister Employment Generation Programme')


def test_07_quarantine_exclusion():
    """Verify quarantined partner records are never counted or displayed in scheme views."""
    db: Session = SessionLocal()
    try:
        quar_partners = db.query(Partner).filter(Partner.record_status == 'QUARANTINED').all()
        quar_ids = set(p.partner_id for p in quar_partners)
        assert len(quar_ids) > 0, "Expected quarantined test fixtures in database"

        # Fetch detail for a scheme
        resp = client.get("/api/v1/partners/financial-health/schemes/SIH26092-001")
        assert resp.status_code == 200
        detail = resp.json()
        returned_pids = set(p["partner_id"] for p in detail["partners"])

        # Quarantine isolation check
        overlap = quar_ids.intersection(returned_pids)
        assert len(overlap) == 0, f"Quarantined partners leaked into scheme view: {overlap}"
    finally:
        db.close()


def test_08_unresolved_entity_isolation():
    """Verify unresolved partners receive LIMITED_DATA without inheriting financial observations."""
    db: Session = SessionLocal()
    try:
        # Check APSCCFC or any unresolved SCA
        res = ChannelPartnerEnrichmentService.get_scheme_financial_health(db, "SIH26092-001")
        assert res is not None
        for p in res["partners"]:
            if "APSCCFC" in p["partner_name"] or "Cooperative Finance" in p["partner_name"]:
                # Must be limited data unless independently resolved
                if not p["verified_metrics"]:
                    assert p["financial_status"]["code"] == "LIMITED_DATA"
    finally:
        db.close()
