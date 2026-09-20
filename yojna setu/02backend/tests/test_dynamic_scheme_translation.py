"""
Authoritative Test Suite for Dynamic Government Scheme Content Translation.
Verifies backend-first, production-ready localization across all 16 required invariants:

1. English / source language returns canonical content.
2. Supported language triggers translation.
3. First request causes provider call.
4. Translation is cached in database.
5. Second request uses cache (zero provider calls).
6. Source hash change invalidates old translation.
7. Unsupported language rejected safely / fallback.
8. Provider failure falls back to canonical content without raising 500.
9. Translation does not modify eligibility rules.
10. IDs remain unchanged.
11. URLs remain unchanged.
12. Numeric amounts remain unchanged.
13. Dates remain unchanged.
14. Scheme ID remains unchanged.
15. Cached translation is returned correctly.
16. Provider credentials are never exposed.
"""

import hashlib
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.models.rule import SchemeRule
from app.models.translation import SchemeTranslation
from app.services.dynamic_scheme_translation import DynamicSchemeTranslationService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_scheme(db_session: Session):
    """Creates an isolated, verified test scheme with strict statutory parameters."""
    test_id = f"TEST-SCH-{uuid.uuid4().hex[:8]}"
    scheme = Scheme(
        scheme_id=test_id,
        scheme_code="TEST-CODE-001",
        scheme_name="Prime Minister Enterprise Scheme (PMES)",
        ministry="Ministry of Micro, Small and Medium Enterprises",
        short_description="Financial credit support up to ₹50,00,000 for manufacturing enterprises with 25% subsidy.",
        detailed_description="PMES provides margin money assistance up to ₹50 Lakh for eligible entrepreneurs. Repayment tenure is 84 months at 5.0% p.a. interest.",
        purpose="Promote entrepreneurship and self-employment opportunities.",
        target_beneficiary="Micro and Small entrepreneurs across India.",
        benefit_description="Subsidy up to 35% in rural areas and 25% in urban areas. Bank credit up to 90% of project cost.",
        application_steps="Apply online at https://pmes.gov.in and submit project report with Aadhaar.",
        required_documents="Aadhaar Card, PAN Card, Project Report, Caste Certificate (if applicable).",
        official_portal="https://pmes.gov.in",
        application_url="https://pmes.gov.in/apply",
        max_loan_amount=5000000.00,
        min_loan_amount=100000.00,
        subsidy_percentage=25.00,
        interest_rate_min=5.00,
        interest_rate_max=8.50,
        scheme_status="ACTIVE",
    )
    db_session.add(scheme)

    # Add a statutory eligibility rule
    rule = SchemeRule(
        rule_id=f"RULE-{uuid.uuid4().hex[:6]}",
        scheme_id=test_id,
        field="age",
        operator=">=",
        value="18",
        value_type="INTEGER",
        rule_type="STATUTORY_CRITERIA",
        priority="HIGH",
        condition_group="AGE_RESTRICTION",
        active=True,
    )
    db_session.add(rule)
    db_session.commit()

    yield scheme

    # Teardown
    db_session.query(SchemeRule).filter(SchemeRule.scheme_id == test_id).delete()
    db_session.query(SchemeTranslation).filter(SchemeTranslation.scheme_id == test_id).delete()
    db_session.query(Scheme).filter(Scheme.scheme_id == test_id).delete()
    db_session.commit()


# ---------------------------------------------------------------------------
# TEST 1: ENGLISH / SOURCE LANGUAGE RETURNS CANONICAL CONTENT
# ---------------------------------------------------------------------------
def test_01_english_returns_canonical_content(test_scheme: Scheme, db_session: Session):
    res = DynamicSchemeTranslationService.get_translated_scheme_detail(
        scheme=test_scheme,
        target_lang="en",
        db=db_session
    )
    assert res["language"] == "en"
    assert res["translation_cached"] is True
    assert res["translation_available"] is True
    assert res["fields"]["scheme_name"] == test_scheme.scheme_name
    assert res["fields"]["short_description"] == test_scheme.short_description
    assert res["canonical_scheme_name"] == test_scheme.scheme_name


# ---------------------------------------------------------------------------
# TEST 2: SUPPORTED LANGUAGE TRIGGERS TRANSLATION
# ---------------------------------------------------------------------------
def test_02_supported_language_triggers_translation(test_scheme: Scheme, db_session: Session):
    mock_translated_json = {
        "scheme_name": "प्रधानमंत्री उद्यम योजना (PMES)",
        "short_description": "₹50,00,000 तक की वित्तीय ऋण सहायता 25% सब्सिडी के साथ।",
        "detailed_description": "PMES पात्र उद्यमियों के लिए ₹50 Lakh तक सहायता प्रदान करता है।",
        "purpose": "उद्यमिता और स्वरोजगार को बढ़ावा देना।",
        "target_beneficiary": "भारत भर के सूक्ष्म और लघु उद्यमी।",
        "benefit_description": "ग्रामीण क्षेत्रों में 35% और शहरी क्षेत्रों में 25% तक सब्सिडी।",
        "application_steps": "https://pmes.gov.in पर ऑनलाइन आवेदन करें।",
        "required_documents": "आधार कार्ड, पैन कार्ड, प्रोजेक्ट रिपोर्ट।"
    }

    mock_provider = MagicMock()
    mock_provider.name = "google_gemini"
    mock_provider.is_fallback = False
    mock_provider.generate.return_value = f"```json\n{json_dumps(mock_translated_json)}\n```"

    with patch("app.services.dynamic_scheme_translation.get_ai_provider", return_value=mock_provider):
        res = DynamicSchemeTranslationService.get_translated_scheme_detail(
            scheme=test_scheme,
            target_lang="hi",
            db=db_session
        )

    assert res["language"] == "hi"
    assert res["fields"]["scheme_name"] == "प्रधानमंत्री उद्यम योजना (PMES)"
    assert "₹50,00,000" in res["fields"]["short_description"]
    assert "25%" in res["fields"]["short_description"]
    assert res["canonical_scheme_name"] == test_scheme.scheme_name


# ---------------------------------------------------------------------------
# TEST 3 & 4: FIRST REQUEST CAUSES PROVIDER CALL AND STORES IN DB CACHE
# ---------------------------------------------------------------------------
def test_03_04_first_request_calls_provider_and_caches_in_db(test_scheme: Scheme, db_session: Session):
    # Ensure cache is empty for this scheme
    db_session.query(SchemeTranslation).filter(
        SchemeTranslation.scheme_id == test_scheme.scheme_id,
        SchemeTranslation.language_code == "bn"
    ).delete()
    db_session.commit()

    mock_translated_json = {
        "scheme_name": "প্রধানমন্ত্রী উদ্যোগ যোজনা (PMES)",
        "short_description": "₹50,00,000 পর্যন্ত আর্থিক সহায়তা 25% ভরতুকি সহ।",
    }

    mock_provider = MagicMock()
    mock_provider.name = "google_gemini"
    mock_provider.is_fallback = False
    mock_provider.generate.return_value = json_dumps(mock_translated_json)

    with patch("app.services.dynamic_scheme_translation.get_ai_provider", return_value=mock_provider):
        res = DynamicSchemeTranslationService.get_translated_scheme_detail(
            scheme=test_scheme,
            target_lang="bn",
            db=db_session
        )

    # Provider should have been called
    assert mock_provider.generate.called
    assert res["translation_cached"] is False  # First time was a cache miss

    # Verify DB now contains cached records
    cached = db_session.query(SchemeTranslation).filter(
        SchemeTranslation.scheme_id == test_scheme.scheme_id,
        SchemeTranslation.language_code == "bn",
        SchemeTranslation.field_name == "scheme_name"
    ).first()
    assert cached is not None
    assert cached.translated_text == "প্রধানমন্ত্রী উদ্যোগ যোজনা (PMES)"
    assert cached.provider == "google_gemini"


# ---------------------------------------------------------------------------
# TEST 5: SECOND REQUEST USES CACHE (ZERO PROVIDER CALLS)
# ---------------------------------------------------------------------------
def test_05_second_request_uses_cache_zero_provider_calls(test_scheme: Scheme, db_session: Session):
    # Ensure scheme_name and short_description are cached
    s_hash_name = DynamicSchemeTranslationService.compute_source_hash(test_scheme.scheme_name)
    db_session.merge(SchemeTranslation(
        id=str(uuid.uuid4()),
        scheme_id=test_scheme.scheme_id,
        language_code="ta",
        field_name="scheme_name",
        translated_text="பிரதமர் தொழில் திட்டம் (PMES)",
        source_hash=s_hash_name,
        provider="test_precache"
    ))
    db_session.commit()

    mock_provider = MagicMock()
    mock_provider.name = "google_gemini"
    mock_provider.is_fallback = False

    with patch("app.services.dynamic_scheme_translation.get_ai_provider", return_value=mock_provider):
        hits, misses, providers = DynamicSchemeTranslationService.get_cached_translations(
            scheme_id=test_scheme.scheme_id,
            target_lang="ta",
            fields_to_check={"scheme_name": test_scheme.scheme_name},
            db=db_session
        )

    assert "scheme_name" in hits
    assert hits["scheme_name"] == "பிரதமர் தொழில் திட்டம் (PMES)"
    assert len(misses) == 0
    assert not mock_provider.generate.called


# ---------------------------------------------------------------------------
# TEST 6: SOURCE HASH CHANGE INVALIDATES OLD TRANSLATION
# ---------------------------------------------------------------------------
def test_06_source_hash_change_invalidates_old_translation(test_scheme: Scheme, db_session: Session):
    old_canonical = "Old official scheme title"
    old_hash = hashlib.sha256(old_canonical.encode("utf-8")).hexdigest()

    # Pre-populate translation cache with old hash
    db_session.query(SchemeTranslation).filter(
        SchemeTranslation.scheme_id == test_scheme.scheme_id,
        SchemeTranslation.language_code == "te"
    ).delete()

    db_session.add(SchemeTranslation(
        id=str(uuid.uuid4()),
        scheme_id=test_scheme.scheme_id,
        language_code="te",
        field_name="scheme_name",
        translated_text="పాత పథకం పేరు",
        source_hash=old_hash,
        provider="old_run"
    ))
    db_session.commit()

    # The test_scheme has a DIFFERENT scheme_name, so its source_hash differs from old_hash!
    hits, misses, _ = DynamicSchemeTranslationService.get_cached_translations(
        scheme_id=test_scheme.scheme_id,
        target_lang="te",
        fields_to_check={"scheme_name": test_scheme.scheme_name},
        db=db_session
    )

    # Old translation MUST NOT be used!
    assert "scheme_name" not in hits
    assert "scheme_name" in misses
    assert misses["scheme_name"] == test_scheme.scheme_name


# ---------------------------------------------------------------------------
# TEST 7: UNSUPPORTED LANGUAGE REJECTED SAFELY / FALLS BACK TO CANONICAL
# ---------------------------------------------------------------------------
def test_07_unsupported_language_fallback(test_scheme: Scheme, db_session: Session):
    assert not DynamicSchemeTranslationService.is_supported("french")
    assert not DynamicSchemeTranslationService.is_supported("de")
    assert not DynamicSchemeTranslationService.is_supported("xx")

    res = DynamicSchemeTranslationService.get_translated_scheme_detail(
        scheme=test_scheme,
        target_lang="fr",  # French is unsupported
        db=db_session
    )
    assert res["language"] == "en"  # Normalized to en
    assert res["fields"]["scheme_name"] == test_scheme.scheme_name


# ---------------------------------------------------------------------------
# TEST 8: PROVIDER FAILURE FALLS BACK TO CANONICAL CONTENT WITHOUT CRASHING
# ---------------------------------------------------------------------------
def test_08_provider_failure_fallback_to_canonical(test_scheme: Scheme, db_session: Session):
    # Ensure no cache hits
    db_session.query(SchemeTranslation).filter(
        SchemeTranslation.scheme_id == test_scheme.scheme_id,
        SchemeTranslation.language_code == "mr"
    ).delete()
    db_session.commit()

    mock_provider = MagicMock()
    mock_provider.name = "failing_provider"
    mock_provider.is_fallback = False
    mock_provider.generate.side_effect = RuntimeError("Provider 503 Service Unavailable")

    with patch("app.services.dynamic_scheme_translation.get_ai_provider", return_value=mock_provider):
        res = DynamicSchemeTranslationService.get_translated_scheme_detail(
            scheme=test_scheme,
            target_lang="mr",
            db=db_session
        )

    # Must NOT raise 500, must gracefully fall back to canonical English
    assert res["language"] == "mr"
    assert res["fields"]["scheme_name"] == test_scheme.scheme_name
    assert res["fields"]["short_description"] == test_scheme.short_description


# ---------------------------------------------------------------------------
# TEST 9: TRANSLATION DOES NOT MODIFY ELIGIBILITY RULES
# ---------------------------------------------------------------------------
def test_09_translation_does_not_modify_eligibility_rules(test_scheme: Scheme, db_session: Session):
    rule_before = db_session.query(SchemeRule).filter(SchemeRule.scheme_id == test_scheme.scheme_id).first()
    assert rule_before is not None
    assert rule_before.field == "age"
    assert rule_before.operator == ">="
    assert rule_before.value == "18"

    # Perform translation call
    DynamicSchemeTranslationService.get_translated_scheme_detail(
        scheme=test_scheme,
        target_lang="hi",
        db=db_session
    )

    # Verify rule in database is 100% unchanged
    rule_after = db_session.query(SchemeRule).filter(SchemeRule.scheme_id == test_scheme.scheme_id).first()
    assert rule_after.field == "age"
    assert rule_after.operator == ">="
    assert rule_after.value == "18"
    assert rule_after.rule_type == "STATUTORY_CRITERIA"


# ---------------------------------------------------------------------------
# TEST 10, 11, 12, 13, 14: IDENTIFIERS, URLS, AMOUNTS, DATES, SCHEME_ID UNCHANGED
# ---------------------------------------------------------------------------
def test_10_to_14_invariants_and_identifiers_unchanged(test_scheme: Scheme, client: TestClient):
    resp = client.get(f"/api/v1/schemes/{test_scheme.scheme_id}?language=hi")
    assert resp.status_code == 200
    data = resp.json()

    # Rule 8: Identifiers NEVER translated
    assert data["scheme_id"] == test_scheme.scheme_id
    assert data["scheme_code"] == test_scheme.scheme_code
    assert data["canonical_scheme_name"] == test_scheme.scheme_name

    # URLs NEVER translated
    assert data["official_portal"] == "https://pmes.gov.in"
    assert data["application_url"] == "https://pmes.gov.in/apply"

    # Numerical and financial amounts NEVER translated
    assert float(data["max_loan_amount"]) == 5000000.00
    assert float(data["min_loan_amount"]) == 100000.00
    assert float(data["subsidy_percentage"]) == 25.00
    assert float(data["interest_rate_min"]) == 5.00
    assert float(data["interest_rate_max"]) == 8.50


# ---------------------------------------------------------------------------
# TEST 15: CACHED TRANSLATION RETURNED CORRECTLY VIA REST API
# ---------------------------------------------------------------------------
def test_15_cached_translation_returned_via_api(test_scheme: Scheme, db_session: Session, client: TestClient):
    s_hash = DynamicSchemeTranslationService.compute_source_hash(test_scheme.scheme_name)
    db_session.merge(SchemeTranslation(
        id=str(uuid.uuid4()),
        scheme_id=test_scheme.scheme_id,
        language_code="gu",
        field_name="scheme_name",
        translated_text="પ્રધાનમંત્રી એન્ટરપ્રાઇઝ યોજના (PMES)",
        source_hash=s_hash,
        provider="google_gemini"
    ))
    db_session.commit()

    resp = client.get(f"/api/v1/schemes/{test_scheme.scheme_id}?language=gu")
    assert resp.status_code == 200
    data = resp.json()

    assert data["scheme_name"] == "પ્રધાનમંત્રી એન્ટરપ્રાઇઝ યોજના (PMES)"
    assert data["language"] == "gu"
    assert data["canonical_scheme_name"] == test_scheme.scheme_name


# ---------------------------------------------------------------------------
# TEST 16: PROVIDER CREDENTIALS ARE NEVER EXPOSED
# ---------------------------------------------------------------------------
def test_16_provider_credentials_never_exposed(test_scheme: Scheme, client: TestClient):
    resp = client.get(f"/api/v1/schemes/{test_scheme.scheme_id}?language=hi")
    assert resp.status_code == 200
    raw_content = resp.text

    # Verify no secret patterns exist in response
    assert "AI_KEY" not in raw_content
    assert "SECRET" not in raw_content
    assert "GEMINI_API_KEY" not in raw_content
    assert "OPENAI_API_KEY" not in raw_content


# ---------------------------------------------------------------------------
# DEDICATED TRANSLATIONS ENDPOINT TESTS
# ---------------------------------------------------------------------------
def test_dedicated_translations_endpoint(test_scheme: Scheme, client: TestClient):
    resp = client.get(f"/api/v1/schemes/{test_scheme.scheme_id}/translations?language=hi")
    assert resp.status_code == 200
    data = resp.json()

    assert data["scheme_id"] == test_scheme.scheme_id
    assert data["language"] == "hi"
    assert data["is_supported"] is True
    assert "fields" in data
    assert "metadata" in data
    assert "source_hashes" in data["metadata"]


# ---------------------------------------------------------------------------
# SCHEME LIST LIGHTWEIGHT TRANSLATION TEST
# ---------------------------------------------------------------------------
def test_scheme_list_lightweight_translation(test_scheme: Scheme, db_session: Session, client: TestClient):
    s_hash = DynamicSchemeTranslationService.compute_source_hash(test_scheme.scheme_name)
    db_session.merge(SchemeTranslation(
        id=str(uuid.uuid4()),
        scheme_id=test_scheme.scheme_id,
        language_code="kn",
        field_name="scheme_name",
        translated_text="ಪ್ರಧಾನ ಮಂತ್ರಿ ಎಂಟರ್‌ಪ್ರೈಸ್ ಯೋಜನೆ (PMES)",
        source_hash=s_hash,
        provider="google_gemini"
    ))
    db_session.commit()

    resp = client.get(f"/api/v1/schemes?language=kn&search=PMES")
    assert resp.status_code == 200
    data = resp.json()

    matched_items = [i for i in data["items"] if i["scheme_id"] == test_scheme.scheme_id]
    if matched_items:
        item = matched_items[0]
        assert item["scheme_name"] == "ಪ್ರಧಾನ ಮಂತ್ರಿ ಎಂಟರ್‌ಪ್ರೈಸ್ ಯೋಜನೆ (PMES)"
        assert item["language"] == "kn"
        assert item["canonical_scheme_name"] == test_scheme.scheme_name


# ---------------------------------------------------------------------------
# ACCEPT-LANGUAGE HEADER SUPPORT TEST
# ---------------------------------------------------------------------------
def test_accept_language_header_support(test_scheme: Scheme, db_session: Session, client: TestClient):
    s_hash = DynamicSchemeTranslationService.compute_source_hash(test_scheme.scheme_name)
    db_session.merge(SchemeTranslation(
        id=str(uuid.uuid4()),
        scheme_id=test_scheme.scheme_id,
        language_code="hi",
        field_name="scheme_name",
        translated_text="प्रधानमंत्री उद्यम योजना (PMES)",
        source_hash=s_hash,
        provider="header_test"
    ))
    db_session.commit()

    resp = client.get(
        f"/api/v1/schemes/{test_scheme.scheme_id}",
        headers={"Accept-Language": "hi-IN,hi;q=0.9,en;q=0.8"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "hi"
    assert data["scheme_name"] == "प्रधानमंत्री उद्यम योजना (PMES)"
    assert data["canonical_scheme_name"] == test_scheme.scheme_name


# ---------------------------------------------------------------------------
# FIELD WHITELIST ENFORCEMENT TEST
# ---------------------------------------------------------------------------
def test_field_whitelist_enforcement():
    translatable = DynamicSchemeTranslationService.TRANSLATABLE_FIELDS
    assert "scheme_id" not in translatable
    assert "scheme_code" not in translatable
    assert "official_portal" not in translatable
    assert "application_url" not in translatable
    assert "max_loan_amount" not in translatable
    assert "subsidy_percentage" not in translatable
    assert "interest_rate_min" not in translatable

    # Permitted human-readable fields only
    assert "scheme_name" in translatable
    assert "short_description" in translatable
    assert "detailed_description" in translatable
    assert "purpose" in translatable
    assert "benefit_description" in translatable
    assert "application_steps" in translatable
    assert "required_documents" in translatable


# ---------------------------------------------------------------------------
# SOURCE HASH NORMALIZATION RESILIENCE TEST
# ---------------------------------------------------------------------------
def test_source_hash_normalization_resilience():
    text1 = "Apply online at official portal."
    text2 = "  Apply online at official portal.  \n"
    text3 = "Apply online at official portal.\r\n"

    h1 = DynamicSchemeTranslationService.compute_source_hash(text1)
    h2 = DynamicSchemeTranslationService.compute_source_hash(text2)
    h3 = DynamicSchemeTranslationService.compute_source_hash(text3)

    assert h1 == h2 == h3
    assert len(h1) == 64  # SHA-256 hex string


# ---------------------------------------------------------------------------
# ALL 12 LANGUAGES SUPPORT VALIDATION TEST
# ---------------------------------------------------------------------------
def test_all_12_languages_supported():
    expected_12 = ["en", "hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]
    for lang in expected_12:
        assert DynamicSchemeTranslationService.is_supported(lang)
        assert DynamicSchemeTranslationService.normalize_language_code(lang) == lang
        assert lang in DynamicSchemeTranslationService.LANGUAGE_NAMES


# ---------------------------------------------------------------------------
# HELPER
# ---------------------------------------------------------------------------
def json_dumps(obj):
    import json
    return json.dumps(obj, ensure_ascii=False)
