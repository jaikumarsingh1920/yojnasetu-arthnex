"""
Unit and Integration Test Suite for YojnaSetu Financial Health Citizen Interpretation Layer.
Validates methodology YS-FIS-V1:

1. STRONGER classification (NNPA=0.5, GNPA=2.0, CRAR=14.0)
2. MIXED classification (NNPA=2.0, GNPA=4.0, CRAR=11.0)
3. HIGHER_STRESS by NNPA (> 3.0%)
4. HIGHER_STRESS by GNPA (> 7.0%)
5. HIGHER_STRESS by CRAR (< 9.0%)
6. Minimum evidence rule (1 metric -> LIMITED_DATA; 0 metrics -> LIMITED_DATA)
7. Two-metric state (exactly 2 metrics -> valid classification with evidence_count = 2)
8. Conflict resolution (Higher-stress overrides Mixed and Stronger)
9. Exact boundary tests:
   - NNPA: 1.00 (STRONGER), 1.01 (MIXED), 3.00 (MIXED), 3.01 (HIGHER_STRESS)
   - GNPA: 3.00 (STRONGER), 3.01 (MIXED), 7.00 (MIXED), 7.01 (HIGHER_STRESS)
   - CRAR: 12.00 (STRONGER), 11.99 (MIXED), 9.00 (MIXED), 8.99 (HIGHER_STRESS)
10. Unrounded raw float comparison (3.004% > 3.0% -> HIGHER_STRESS)
11. Null safety & invalid data (None, NaN, inf, negative numbers, corrupt types)
12. Unresolved institution entity isolation (unresolved partner -> LIMITED_DATA)
13. Scope & provenance validation (policy-level or unverified metrics excluded)
14. End-to-end API integration test on /api/v1/partners/financial-health/{id}
"""

import math
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.partner import Partner
from app.services.financial_indicator_status_service import (
    FinancialIndicatorStatusService,
    FinancialIndicatorStatusCode,
)

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_01_stronger_scenario():
    """
    Test 1: All available metrics in the stronger range:
    NNPA = 0.5%, GNPA = 2.0%, CRAR = 14.0% -> STRONGER
    """
    metrics = {
        "NNPA_PERCENT": {"value": 0.5, "source": "RBI DBIE", "verification_status": "VERIFIED_OFFICIAL"},
        "GNPA_PERCENT": {"value": 2.0, "source": "RBI DBIE", "verification_status": "VERIFIED_OFFICIAL"},
        "CRAR_PERCENT": {"value": 14.0, "source": "RBI DBIE", "verification_status": "VERIFIED_OFFICIAL"},
    }
    result = FinancialIndicatorStatusService.calculate_status(metrics)
    assert result["code"] == FinancialIndicatorStatusCode.STRONGER.value
    assert result["label"] == "Financial position looks stronger"
    assert result["evidence_count"] == 3
    assert result["calculated_from"] == ["CRAR_PERCENT", "GNPA_PERCENT", "NNPA_PERCENT"]
    assert result["methodology_version"] == "YS-FIS-V1"


def test_02_mixed_scenario():
    """
    Test 2: One or more metrics in the middle band, none higher-stress:
    NNPA = 2.0%, GNPA = 4.0%, CRAR = 11.0% -> MIXED
    """
    metrics = {
        "NNPA_PERCENT": 2.0,
        "GNPA_PERCENT": 4.0,
        "CRAR_PERCENT": 11.0,
    }
    result = FinancialIndicatorStatusService.calculate_status(metrics)
    assert result["code"] == FinancialIndicatorStatusCode.MIXED.value
    assert result["label"] == "Financial position is mixed"
    assert result["evidence_count"] == 3


def test_03_higher_stress_nnpa():
    """
    Test 3: NNPA > 3.0% triggers HIGHER_STRESS even if other metrics are stronger.
    NNPA = 3.5%, GNPA = 2.0%, CRAR = 14.0% -> HIGHER_STRESS
    """
    metrics = {
        "NNPA_PERCENT": 3.5,
        "GNPA_PERCENT": 2.0,
        "CRAR_PERCENT": 14.0,
    }
    result = FinancialIndicatorStatusService.calculate_status(metrics)
    assert result["code"] == FinancialIndicatorStatusCode.HIGHER_STRESS.value
    assert result["label"] == "Financial position needs attention"


def test_04_higher_stress_gnpa():
    """
    Test 4: GNPA > 7.0% triggers HIGHER_STRESS.
    NNPA = 0.5%, GNPA = 8.0%, CRAR = 14.0% -> HIGHER_STRESS
    """
    metrics = {
        "NNPA_PERCENT": 0.5,
        "GNPA_PERCENT": 8.0,
        "CRAR_PERCENT": 14.0,
    }
    result = FinancialIndicatorStatusService.calculate_status(metrics)
    assert result["code"] == FinancialIndicatorStatusCode.HIGHER_STRESS.value


def test_05_higher_stress_crar():
    """
    Test 5: CRAR < 9.0% triggers HIGHER_STRESS.
    NNPA = 0.5%, GNPA = 2.0%, CRAR = 8.5% -> HIGHER_STRESS
    """
    metrics = {
        "NNPA_PERCENT": 0.5,
        "GNPA_PERCENT": 2.0,
        "CRAR_PERCENT": 8.5,
    }
    result = FinancialIndicatorStatusService.calculate_status(metrics)
    assert result["code"] == FinancialIndicatorStatusCode.HIGHER_STRESS.value


def test_06_minimum_evidence_rule_single_metric():
    """
    Test 6: Exactly one verified metric is NOT enough for classification.
    Returns LIMITED_DATA.
    """
    metrics = {
        "GNPA_PERCENT": 2.0,
        "NNPA_PERCENT": None,
        "CRAR_PERCENT": None,
    }
    result = FinancialIndicatorStatusService.calculate_status(metrics)
    assert result["code"] == FinancialIndicatorStatusCode.LIMITED_DATA.value
    assert result["evidence_count"] == 1
    assert "limited" in result["short_description"].lower()


def test_07_minimum_evidence_rule_zero_metrics():
    """
    Test 7: Zero metrics return LIMITED_DATA.
    """
    result = FinancialIndicatorStatusService.calculate_status({})
    assert result["code"] == FinancialIndicatorStatusCode.LIMITED_DATA.value
    assert result["evidence_count"] == 0


def test_08_two_metric_state():
    """
    Test 8: Exactly two verified metrics allow classification.
    NNPA = 0.5%, GNPA = 2.0%, CRAR = None -> STRONGER, evidence_count = 2
    """
    metrics = {
        "NNPA_PERCENT": 0.5,
        "GNPA_PERCENT": 2.0,
        "CRAR_PERCENT": None,
    }
    result = FinancialIndicatorStatusService.calculate_status(metrics)
    assert result["code"] == FinancialIndicatorStatusCode.STRONGER.value
    assert result["evidence_count"] == 2
    assert result["calculated_from"] == ["GNPA_PERCENT", "NNPA_PERCENT"]


def test_09_exact_boundary_values():
    """
    Test 9: Exact boundaries according to YS-FIS-V1:
    NNPA: 1.00 -> STRONGER, 1.01 -> MIXED, 3.00 -> MIXED, 3.01 -> HIGHER_STRESS
    GNPA: 3.00 -> STRONGER, 3.01 -> MIXED, 7.00 -> MIXED, 7.01 -> HIGHER_STRESS
    CRAR: 12.00 -> STRONGER, 11.99 -> MIXED, 9.00 -> MIXED, 8.99 -> HIGHER_STRESS
    """
    # NNPA 1.00 vs 1.01 (baseline GNPA 2.0, CRAR 14.0)
    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 1.00, "GNPA_PERCENT": 2.0, "CRAR_PERCENT": 14.0
    })["code"] == FinancialIndicatorStatusCode.STRONGER.value

    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 1.01, "GNPA_PERCENT": 2.0, "CRAR_PERCENT": 14.0
    })["code"] == FinancialIndicatorStatusCode.MIXED.value

    # NNPA 3.00 vs 3.01
    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 3.00, "GNPA_PERCENT": 2.0, "CRAR_PERCENT": 14.0
    })["code"] == FinancialIndicatorStatusCode.MIXED.value

    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 3.01, "GNPA_PERCENT": 2.0, "CRAR_PERCENT": 14.0
    })["code"] == FinancialIndicatorStatusCode.HIGHER_STRESS.value

    # GNPA 3.00 vs 3.01 (baseline NNPA 0.5, CRAR 14.0)
    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 0.5, "GNPA_PERCENT": 3.00, "CRAR_PERCENT": 14.0
    })["code"] == FinancialIndicatorStatusCode.STRONGER.value

    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 0.5, "GNPA_PERCENT": 3.01, "CRAR_PERCENT": 14.0
    })["code"] == FinancialIndicatorStatusCode.MIXED.value

    # GNPA 7.00 vs 7.01
    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 0.5, "GNPA_PERCENT": 7.00, "CRAR_PERCENT": 14.0
    })["code"] == FinancialIndicatorStatusCode.MIXED.value

    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 0.5, "GNPA_PERCENT": 7.01, "CRAR_PERCENT": 14.0
    })["code"] == FinancialIndicatorStatusCode.HIGHER_STRESS.value

    # CRAR 12.00 vs 11.99 (baseline NNPA 0.5, GNPA 2.0)
    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 0.5, "GNPA_PERCENT": 2.0, "CRAR_PERCENT": 12.00
    })["code"] == FinancialIndicatorStatusCode.STRONGER.value

    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 0.5, "GNPA_PERCENT": 2.0, "CRAR_PERCENT": 11.99
    })["code"] == FinancialIndicatorStatusCode.MIXED.value

    # CRAR 9.00 vs 8.99
    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 0.5, "GNPA_PERCENT": 2.0, "CRAR_PERCENT": 9.00
    })["code"] == FinancialIndicatorStatusCode.MIXED.value

    assert FinancialIndicatorStatusService.calculate_status({
        "NNPA_PERCENT": 0.5, "GNPA_PERCENT": 2.0, "CRAR_PERCENT": 8.99
    })["code"] == FinancialIndicatorStatusCode.HIGHER_STRESS.value


def test_10_unrounded_raw_float_comparison():
    """
    Test 10: Classification uses raw unrounded numbers:
    NNPA = 3.004% must be HIGHER_STRESS, not rounded to 3.00% (MIXED).
    """
    metrics = {
        "NNPA_PERCENT": 3.004,
        "GNPA_PERCENT": 2.0,
        "CRAR_PERCENT": 14.0,
    }
    result = FinancialIndicatorStatusService.calculate_status(metrics)
    assert result["code"] == FinancialIndicatorStatusCode.HIGHER_STRESS.value


def test_11_null_safety_and_invalid_data():
    """
    Test 11: Missing data, negative numbers, NaN, inf, or bad types never crash and never classify as favorable.
    """
    # Negative NPA (corrupt) -> excluded from evidence
    metrics_neg = {
        "NNPA_PERCENT": -1.5,
        "GNPA_PERCENT": 2.0,
        "CRAR_PERCENT": 14.0,
    }
    res_neg = FinancialIndicatorStatusService.calculate_status(metrics_neg)
    # NNPA is dropped, only 2 valid remain
    assert res_neg["evidence_count"] == 2
    assert "NNPA_PERCENT" not in res_neg["calculated_from"]

    # NaN / Inf -> safely excluded
    metrics_nan = {
        "NNPA_PERCENT": float("nan"),
        "GNPA_PERCENT": float("inf"),
        "CRAR_PERCENT": 14.0,
    }
    res_nan = FinancialIndicatorStatusService.calculate_status(metrics_nan)
    # Only 1 valid metric -> LIMITED_DATA
    assert res_nan["code"] == FinancialIndicatorStatusCode.LIMITED_DATA.value
    assert res_nan["evidence_count"] == 1


def test_12_unresolved_entity_isolation():
    """
    Test 12: An unresolved partner entity MUST return LIMITED_DATA and zero evidence,
    even if dictionary contains metrics.
    """
    metrics = {
        "NNPA_PERCENT": 0.5,
        "GNPA_PERCENT": 2.0,
        "CRAR_PERCENT": 14.0,
    }
    result = FinancialIndicatorStatusService.calculate_status(
        verified_metrics=metrics,
        entity_resolution_status="UNRESOLVED"
    )
    assert result["code"] == FinancialIndicatorStatusCode.LIMITED_DATA.value
    assert result["evidence_count"] == 0
    assert result["calculated_from"] == []


def test_13_scope_and_provenance_validation():
    """
    Test 13: Policy-level metrics (e.g. OVERDUE_STATUS, FUND_UTILIZATION) or unverified items
    must NOT participate in financial indicator classification.
    """
    metrics = {
        "OVERDUE_STATUS": {"value": 0, "financial_scope": "POLICY_LEVEL"},
        "FUND_UTILIZATION_PERCENT": {"value": 100.0, "financial_scope": "POLICY_LEVEL"},
        "NNPA_PERCENT": {"value": 0.5, "verification_status": "NOT_PUBLICLY_VERIFIED"},
        "GNPA_PERCENT": {"value": 2.0, "verification_status": "VERIFIED_OFFICIAL"},
    }
    result = FinancialIndicatorStatusService.calculate_status(metrics)
    # Only GNPA_PERCENT is valid -> evidence_count is 1 -> LIMITED_DATA
    assert result["code"] == FinancialIndicatorStatusCode.LIMITED_DATA.value
    assert result["evidence_count"] == 1


def test_14_api_integration_financial_health_endpoint(db: Session):
    """
    Test 14: Verify live endpoint /api/v1/partners/financial-health/{id} returns
    financial_status with code, label, evidence_count, calculated_from, and methodology_version.
    """
    # Pick active SBI partner
    sbi_partner = db.query(Partner).filter(
        Partner.name.ilike("%State Bank of India%"),
        Partner.is_active == True,
        Partner.record_status == "ACTIVE"
    ).first()
    assert sbi_partner is not None

    resp = client.get(f"/api/v1/partners/financial-health/{sbi_partner.partner_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert "financial_status" in data
    fin_status = data["financial_status"]
    assert fin_status is not None
    # State Bank of India has NNPA 0.47%, GNPA 1.82%, CRAR 14.28% -> STRONGER
    assert fin_status["code"] == FinancialIndicatorStatusCode.STRONGER.value
    assert fin_status["label"] == "Financial position looks stronger"
    assert fin_status["evidence_count"] == 3
    assert fin_status["methodology_version"] == "YS-FIS-V1"
    assert "scope_disclaimer" in fin_status


def test_15_financial_health_schemes_hub_endpoint():
    """
    Test 15: Verify GET /api/v1/partners/financial-health/schemes returns schemes
    with audited counts of channel partners, verified indicators, and limited data.
    """
    resp = client.get("/api/v1/partners/financial-health/schemes?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first_scheme = data[0]
    assert "scheme_id" in first_scheme
    assert "scheme_name" in first_scheme
    assert "channel_partners_count" in first_scheme
    assert "with_verified_financial_info_count" in first_scheme
    assert "limited_information_count" in first_scheme
    assert first_scheme["channel_partners_count"] >= 1
    assert first_scheme["channel_partners_count"] == (
        first_scheme["with_verified_financial_info_count"] + first_scheme["limited_information_count"]
    )


def test_16_scheme_financial_health_detail_endpoint():
    """
    Test 16: Verify GET /api/v1/partners/financial-health/schemes/{scheme_id}
    returns scheme financial detail and neutrally sorted partner cards.
    """
    resp = client.get("/api/v1/partners/financial-health/schemes/SIH26092-001")
    assert resp.status_code == 200
    data = resp.json()

    assert data["scheme_id"] == "SIH26092-001"
    assert "total_channel_partners" in data
    assert "partners_with_verified_financial_info" in data
    assert "partners_with_limited_information" in data
    assert "partners" in data
    assert len(data["partners"]) > 0

    first_p = data["partners"][0]
    assert "partner_id" in first_p
    assert "partner_name" in first_p
    assert "financial_status" in first_p
    assert first_p["financial_status"]["code"] in ("STRONGER", "MIXED", "HIGHER_STRESS", "LIMITED_DATA")

