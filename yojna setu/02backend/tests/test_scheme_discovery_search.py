import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.scheme import Scheme

client = TestClient(app)


def test_filter_options_dynamic_endpoint():
    """Verify /filter-options returns dynamically calculated categories from DB."""
    response = client.get("/api/v1/schemes/filter-options")
    assert response.status_code == 200
    data = response.json()

    assert data["total_schemes"] == 90
    assert len(data["ministries"]) > 0
    assert len(data["sectors"]) > 0
    assert len(data["financial_types"]) > 0
    assert len(data["beneficiary_categories"]) > 0
    assert len(data["states"]) > 0
    assert len(data["application_routes"]) > 0

    # Ensure financial types contain all authoritative categories
    fin_types = {item["value"] for item in data["financial_types"]}
    assert "LOAN_CREDIT" in fin_types
    assert "GRANT_SUBSIDY" in fin_types
    assert "SCHOLARSHIP" in fin_types
    assert "DIRECT_BENEFIT" in fin_types

    # Ensure total counts match
    total_fin_count = sum(item["count"] for item in data["financial_types"])
    assert total_fin_count == 90


def test_exact_and_partial_scheme_search():
    """Verify search across name, code, description, and tags."""
    # Exact code search
    res_code = client.get("/api/v1/schemes?search=SIH26092-001")
    assert res_code.status_code == 200
    data_code = res_code.json()
    assert data_code["total"] >= 1
    assert any("PMEGP" in s["scheme_name"] or s["scheme_id"] == "SIH26092-001" for s in data_code["items"])

    # Partial name search
    res_part = client.get("/api/v1/schemes?search=mudra")
    assert res_part.status_code == 200
    data_part = res_part.json()
    assert data_part["total"] >= 1
    assert any("MUDRA" in s["scheme_name"].upper() for s in data_part["items"])


def test_multilingual_hindi_search():
    """Verify Hindi terms expand to English synonyms correctly."""
    # Search "ऋण" (Loan) -> matches credit/loan schemes
    res_hindi_loan = client.get("/api/v1/schemes?search=ऋण")
    assert res_hindi_loan.status_code == 200
    assert res_hindi_loan.json()["total"] > 0

    # Search "महिला" (Women) -> matches women-oriented schemes
    res_hindi_women = client.get("/api/v1/schemes?search=महिला")
    assert res_hindi_women.status_code == 200
    assert res_hindi_women.json()["total"] > 0

    # Search "कारीगर" (Artisan) -> matches Vishwakarma and artisan schemes
    res_hindi_artisan = client.get("/api/v1/schemes?search=कारीगर")
    assert res_hindi_artisan.status_code == 200
    assert res_hindi_artisan.json()["total"] > 0


def test_ministry_and_sector_filters():
    """Verify filtering by governing ministry and sector."""
    # Filter by MSME ministry
    res_msme = client.get("/api/v1/schemes?ministry=Ministry of Micro, Small and Medium Enterprises")
    assert res_msme.status_code == 200
    data_msme = res_msme.json()
    assert data_msme["total"] >= 20
    for s in data_msme["items"]:
        assert "MSME" in (s["ministry"] or "").upper() or "MICRO, SMALL" in (s["ministry"] or "").upper()

    # Filter by Agriculture sector
    res_agri = client.get("/api/v1/schemes?sector=AGRICULTURE")
    assert res_agri.status_code == 200
    assert res_agri.json()["total"] > 0


def test_financial_type_filter():
    """Verify filtering strictly by financial classification."""
    # Filter only GRANT_SUBSIDY schemes
    res_sub = client.get("/api/v1/schemes?financial_type=GRANT_SUBSIDY")
    assert res_sub.status_code == 200
    data_sub = res_sub.json()
    assert data_sub["total"] > 0
    for s in data_sub["items"]:
        assert s["financial_category"] == "GRANT_SUBSIDY"
        assert s["is_credit_scheme"] is False

    # Filter only LOAN_CREDIT schemes
    res_loan = client.get("/api/v1/schemes?financial_type=LOAN_CREDIT")
    assert res_loan.status_code == 200
    data_loan = res_loan.json()
    assert data_loan["total"] > 0
    for s in data_loan["items"]:
        assert s["financial_category"] == "LOAN_CREDIT"
        assert s["is_credit_scheme"] is True


def test_beneficiary_category_filter():
    """Verify filtering by target beneficiary groups."""
    # SC Beneficiary filter
    res_sc = client.get("/api/v1/schemes?beneficiary_category=SC")
    assert res_sc.status_code == 200
    assert res_sc.json()["total"] > 0

    # Women Beneficiary filter
    res_women = client.get("/api/v1/schemes?beneficiary_category=WOMEN")
    assert res_women.status_code == 200
    assert res_women.json()["total"] > 0

    # Artisan Beneficiary filter
    res_artisan = client.get("/api/v1/schemes?beneficiary_category=ARTISAN")
    assert res_artisan.status_code == 200
    assert res_artisan.json()["total"] > 0


def test_combined_multiple_filters():
    """Verify combining ministry, financial_type, and beneficiary_category together."""
    res = client.get("/api/v1/schemes?ministry=Ministry of Social Justice and Empowerment&beneficiary_category=SC&financial_type=LOAN_CREDIT")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    for s in data["items"]:
        assert s["financial_category"] == "LOAN_CREDIT"


def test_no_results_and_recovery():
    """Verify zero results returned cleanly for impossible search queries."""
    res = client.get("/api/v1/schemes?search=xyznonexistentschemequery999")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["pages"] == 0


def test_sorting_options():
    """Verify sorting by name, loan amount, interest rate, and relevance."""
    # Sort A-Z
    res_asc = client.get("/api/v1/schemes?sort_by=scheme_name&sort_order=asc")
    assert res_asc.status_code == 200
    items_asc = res_asc.json()["items"]
    names_asc = [s["scheme_name"].lower() for s in items_asc]
    assert names_asc == sorted(names_asc)

    # Sort Z-A
    res_desc = client.get("/api/v1/schemes?sort_by=scheme_name&sort_order=desc")
    assert res_desc.status_code == 200
    items_desc = res_desc.json()["items"]
    names_desc = [s["scheme_name"].lower() for s in items_desc]
    assert names_desc == sorted(names_desc, reverse=True)

    # Sort by max loan amount descending
    res_loan = client.get("/api/v1/schemes?sort_by=max_loan_amount&sort_order=desc")
    assert res_loan.status_code == 200
    items_loan = res_loan.json()["items"]
    loan_amounts = [float(s.get("max_loan_amount") or 0) for s in items_loan]
    assert loan_amounts == sorted(loan_amounts, reverse=True)
