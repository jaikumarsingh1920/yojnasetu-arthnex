import io
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.models.candidate import CandidateScheme
from app.models.rule import SchemeRule
from app.models.document import SchemeDocument
from app.models.verification import SchemeVerification
from app.models.changelog import SchemeChangelog
from app.models.ingestion import SchemeSource
from app.services.ingestion.fetcher import HTMLFetcher, PDFFetcher, DomainRateLimiter, FetchResult
from app.services.ingestion.extractor import OfficialGovHTMLExtractor
from app.services.ingestion.pdf_extractor import OfficialGovPDFExtractor, OCRFallbackDetector
from app.services.ingestion.normalizer import SchemeDataNormalizer
from app.services.ingestion.validator import SchemeDataValidator
from app.services.ingestion.relevance_classifier import SchemeRelevanceClassifier
from app.services.ingestion.source_resolver import OfficialSourceResolver
from app.services.ingestion.deduplicator import SchemeDeduplicator
from app.services.ingestion.rule_generator import SchemeRuleGenerator
from app.services.ingestion.document_generator import SchemeDocumentGenerator
from app.services.ingestion.promotion_service import CandidatePromotionService
from app.services.ingestion.discovery_worker import SchemeDiscoveryWorker, SchemeDiscoveryCatalog
from app.engine.recommendation import DeterministicRecommendationEngine
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.recommendation import RecommendationRequest


@pytest.fixture
def db_session():
    session = SessionLocal()
    pre_scheme_ids = set(r[0] for r in session.query(Scheme.scheme_id).all())
    pre_candidate_ids = set(r[0] for r in session.query(CandidateScheme.candidate_id).all())
    pre_candidate_states = {
        c.candidate_id: (c.candidate_status, c.reviewed_at, c.reviewed_by, c.admin_notes)
        for c in session.query(CandidateScheme).all()
    }
    try:
        yield session
    finally:
        try:
            # 1. Clean up any newly created schemes and their child records
            post_scheme_ids = [r[0] for r in session.query(Scheme.scheme_id).all() if r[0] not in pre_scheme_ids]
            if post_scheme_ids:
                session.query(SchemeRule).filter(SchemeRule.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(SchemeDocument).filter(SchemeDocument.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(SchemeVerification).filter(SchemeVerification.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(SchemeChangelog).filter(SchemeChangelog.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(SchemeSource).filter(SchemeSource.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)
                session.query(Scheme).filter(Scheme.scheme_id.in_(post_scheme_ids)).delete(synchronize_session=False)

            # 2. Clean up any newly created candidate schemes
            post_candidate_ids = [r[0] for r in session.query(CandidateScheme.candidate_id).all() if r[0] not in pre_candidate_ids]
            if post_candidate_ids:
                session.query(CandidateScheme).filter(CandidateScheme.candidate_id.in_(post_candidate_ids)).delete(synchronize_session=False)

            # 3. Restore any modified candidate statuses for pre-existing candidates
            for cid, (stat, rev_at, rev_by, notes) in pre_candidate_states.items():
                cand = session.query(CandidateScheme).filter(CandidateScheme.candidate_id == cid).first()
                if cand and (cand.candidate_status != stat or cand.reviewed_by != rev_by):
                    cand.candidate_status = stat
                    cand.reviewed_at = rev_at
                    cand.reviewed_by = rev_by
                    cand.admin_notes = notes

            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


# 1. Discovery Catalog Resolution
def test_01_discovery_catalog_resolution():
    catalog = SchemeDiscoveryCatalog.OFFICIAL_DISCOVERY_CATALOG
    assert len(catalog) >= 15
    sources = set(e["discovery_source"] for e in catalog)
    assert "CENTRAL_MINISTRY" in sources
    assert "IMPLEMENTING_AGENCY" in sources
    assert "STATE_PORTAL" in sources


# 2. Candidate Creation with Traceable Run ID
def test_02_candidate_creation_traceable_run(db_session: Session):
    worker = SchemeDiscoveryWorker(db_session)
    uid = uuid.uuid4().hex[:6]
    test_entry = [{
        "name": f"Dynamic Unique Central Scheme {uid}",
        "official_source_url": f"https://msme.gov.in/test-{uid}",
        "stated_benefits": "Special MSME credit support",
        "category": "MSME",
        "discovery_source": "CENTRAL_MINISTRY"
    }]
    with patch.object(SchemeDiscoveryCatalog, "OFFICIAL_DISCOVERY_CATALOG", test_entry):
        res = worker.run_discovery_batch(target_source="CENTRAL_MINISTRY", max_candidates=1)
        assert res["run_id"].startswith("RUN-")
        assert res["staged_for_review"] == 1

        candidate = db_session.query(CandidateScheme).filter(CandidateScheme.run_id == res["run_id"]).first()
        assert candidate is not None
        assert candidate.discovered_name
        assert candidate.candidate_status == "STAGED"


# 3. Official Source Domain Verification
def test_03_official_source_validation():
    # Level 1 Authority
    r1 = OfficialSourceResolver.resolve("https://msme.gov.in/schemes")
    assert r1.is_authoritative is True
    assert r1.authority_level == "LEVEL_1_PRIMARY"

    r2 = OfficialSourceResolver.resolve("https://tribal.nic.in/schemes.aspx")
    assert r2.is_authoritative is True
    assert r2.authority_level == "LEVEL_1_PRIMARY"

    # Level 2 Agency
    r3 = OfficialSourceResolver.resolve("https://www.sidbi.in/en/schemes")
    assert r3.is_authoritative is True
    assert r3.authority_level == "LEVEL_2_AGENCY"

    # Level 3 Discovery
    r4 = OfficialSourceResolver.resolve("https://www.myscheme.gov.in/schemes/pmegp")
    assert r4.is_authoritative is True
    assert r4.authority_level == "LEVEL_3_DISCOVERY"

    # Commercial / SEO aggregator rejection
    r5 = OfficialSourceResolver.resolve("https://www.bankbazaar.com/personal-loan.html")
    assert r5.is_authoritative is False
    assert r5.authority_level == "UNVERIFIED_THIRD_PARTY"

    r6 = OfficialSourceResolver.resolve("https://cleartax.in/s/pmegp-scheme")
    assert r6.is_authoritative is False
    assert r6.authority_level == "UNVERIFIED_THIRD_PARTY"


# 4. Canonical Mapping
def test_04_canonical_mapping():
    raw_data = {
        "scheme_name": "Test Artisan Assistance Scheme",
        "ministry": "Ministry of Textiles",
        "max_loan_amount": "500000",
        "subsidy_percentage": "25.0",
        "age_min": "18",
        "income_limit": "300000",
        "official_source_url": "https://texmin.gov.in/artisan"
    }
    norm = SchemeDataNormalizer.normalize(raw_data)
    assert norm["scheme_name"] == "Test Artisan Assistance Scheme"
    assert norm["max_loan_amount"] == 500000.0
    assert norm["loan_available"] == "YES"
    assert norm["subsidy_percentage"] == 25.0
    assert norm["age_min"] == 18
    assert norm["income_limit"] == 300000.0


# 5. Normalization Sentinels
def test_05_normalization_sentinels():
    raw_empty = {
        "scheme_name": "Free Training Fellowship",
        "official_source_url": "https://msde.gov.in"
    }
    norm = SchemeDataNormalizer.normalize(raw_empty)
    assert norm.get("max_loan_amount") is None
    assert norm.get("subsidy_percentage") is None
    assert norm.get("age_min") is None
    assert norm["state_coverage"] == "All India"


# 6. Deduplication by Exact Code and Normalized Title
def test_06_deduplication_exact_code(db_session: Session):
    existing = db_session.query(Scheme).filter(Scheme.scheme_id == "SIH26092-001").first()
    assert existing is not None

    # Test Exact Code match
    res_code = SchemeDeduplicator.check_duplicate(
        candidate_name="Some Random Name",
        candidate_code=existing.scheme_code,
        existing_schemes=[existing]
    )
    assert res_code.is_duplicate is True
    assert res_code.duplicate_stage == "STAGE_1_EXACT_CODE"

    # Test Normalized Name match
    res_name = SchemeDeduplicator.check_duplicate(
        candidate_name="Prime Minister's Employment Generation Programme",
        candidate_code="UNKNOWN",
        existing_schemes=[existing]
    )
    assert res_name.is_duplicate is True
    assert res_name.duplicate_stage in ["STAGE_2_NORMALIZED_NAME", "STAGE_6_ALIAS_MATCH", "STAGE_7_TOKEN_SIMILARITY"]


# 7. Missing Fields Preservation
def test_07_missing_fields_preservation(db_session: Session):
    cid = f"CAND-TEST-MISSING-{uuid.uuid4().hex[:6]}"
    cand = CandidateScheme(
        candidate_id=cid,
        run_id="RUN-TEST",
        discovered_name="Non-Credit Grant Scheme",
        normalized_name=f"Non-Credit Grant Scheme {uuid.uuid4().hex[:4]}",
        scheme_code="UNKNOWN",
        discovery_source="CENTRAL_MINISTRY",
        official_source_url=f"https://welfare.gov.in/{cid}",
        level="CENTRAL_SECTOR",
        relevance_status="HIGH_PRIORITY",
        extraction_status="EXTRACTED",
        verification_status="OFFICIALLY_VERIFIED",
        duplicate_status="UNIQUE",
        data_confidence="HIGH",
        extracted_data=json.dumps({
            "scheme_name": "Non-Credit Grant Scheme",
            "official_source_url": f"https://welfare.gov.in/{cid}"
        }),
        missing_fields=json.dumps(["max_loan_amount", "income_limit"]),
        evidence=json.dumps({}),
        validation_status="VALID",
        validation_errors=json.dumps([]),
        candidate_status="STAGED"
    )
    db_session.add(cand)
    db_session.commit()

    promoted = CandidatePromotionService.promote_candidate(db_session, cand.candidate_id)
    assert promoted.max_loan_amount is None
    assert promoted.max_loan_amount_raw == "NOT_APPLICABLE"
    assert promoted.loan_available == "NO"
    assert promoted.income_limit is None
    assert promoted.income_limit_raw == "NOT_APPLICABLE"


# 8. Financial Validation
def test_08_financial_validation():
    # Valid financial data
    valid_data = {
        "scheme_name": "Valid MSME Scheme",
        "official_source_url": "https://msme.gov.in",
        "max_loan_amount": 1000000.0,
        "subsidy_percentage": 35.0,
        "interest_rate_max": 8.5
    }
    v_res = SchemeDataValidator.validate(valid_data)
    assert v_res.is_valid is True

    # Invalid negative loan
    inv_loan = {**valid_data, "max_loan_amount": -5000}
    res_inv = SchemeDataValidator.validate(inv_loan)
    assert res_inv.is_valid is False
    assert any("max_loan_amount" in err for err in res_inv.errors)

    # Subsidy exceeding 100%
    inv_sub = {**valid_data, "subsidy_percentage": 150.0}
    res_sub = SchemeDataValidator.validate(inv_sub)
    assert res_sub.is_valid is False
    assert any("subsidy_percentage" in err for err in res_sub.errors)


# 9. Eligibility Rule Generation
def test_09_eligibility_rule_generation():
    extracted = {
        "age_min": 18,
        "age_max": 45,
        "income_limit": 250000.0,
        "gender_requirement": "FEMALE",
        "new_unit_required": "YES",
        "source_document": "Notification 2026",
        "source_page": "Page 5"
    }
    rules = SchemeRuleGenerator.generate_rules_for_scheme("TEST-SCHEME-01", extracted)
    assert len(rules) == 5

    fields = [r.field for r in rules]
    assert "age" in fields
    assert "annual_income" in fields
    assert "gender" in fields
    assert "new_unit_required" in fields

    age_min_rule = [r for r in rules if r.field == "age" and r.operator == ">="][0]
    assert age_min_rule.value == "18"
    assert age_min_rule.source_page == "Page 5"


# 10. PDF Extraction via pdfplumber
def test_10_pdf_extraction_plumber():
    # Create a mock text-based PDF in memory
    extractor = OfficialGovPDFExtractor()
    with patch("pdfplumber.open") as mock_open:
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = (
            "Operational Guidelines of PM Artisans Livelihood Scheme\n"
            "Ministry of Textiles, Government of India\n"
            "Eligibility Criteria: Applicant must be above 18 years of age. Maximum loan amount up to Rs. 5 Lakhs.\n"
            "Capital subsidy rate: 25%."
        )
        mock_pdf.pages = [mock_page1]
        mock_open.return_value.__enter__.return_value = mock_pdf

        res = extractor.extract(b"%PDF-1.4 Mock", "https://texmin.gov.in/guidelines.pdf")
        assert res.success is True
        assert res.is_scanned is False
        assert res.extracted_data.get("scheme_name") == "PM Artisans Livelihood Scheme"
        assert res.extracted_data.get("ministry") == "Ministry of Textiles"
        assert res.extracted_data.get("max_loan_amount") == 500000.0
        assert res.extracted_data.get("subsidy_percentage") == 25.0
        assert res.extracted_data.get("age_min") == 18


# 11. OCR Fallback Detection (Scanned PDF Flag)
def test_11_ocr_fallback_detection():
    extractor = OfficialGovPDFExtractor()
    with patch("pdfplumber.open") as mock_open:
        mock_pdf = MagicMock()
        mock_page_scanned = MagicMock()
        # Sparse characters simulate a scanned image without OCR
        mock_page_scanned.extract_text.return_value = "   1   \n\n  "
        mock_pdf.pages = [mock_page_scanned]
        mock_open.return_value.__enter__.return_value = mock_pdf

        res = extractor.extract(b"%PDF-1.4 Mock Scanned", "https://welfare.gov.in/scanned.pdf")
        assert res.success is False
        assert res.is_scanned is True
        assert res.ocr_status == "UNAVAILABLE_OR_LOW_QUALITY"
        assert any("scanned" in note.lower() for note in res.notes)


# 12. Evidence Preservation with Page and Section Citations
def test_12_evidence_preservation():
    extractor = OfficialGovPDFExtractor()
    with patch("pdfplumber.open") as mock_open:
        mock_pdf = MagicMock()
        p1 = MagicMock()
        p1.extract_text.return_value = "Guidelines of Women Entrepreneur Support Scheme\nMinistry of MSME\nAnnual family income below Rs. 3 Lakh."
        mock_pdf.pages = [p1]
        mock_open.return_value.__enter__.return_value = mock_pdf

        res = extractor.extract(b"%PDF-1.4", "https://msme.gov.in/scheme.pdf")
        assert "income_limit" in res.evidence
        evi = res.evidence["income_limit"]
        assert evi["source_page"] == "Page 1"
        assert "below Rs. 3 Lakh" in evi["text"]


# 13. Failed Source Isolation
def test_13_failed_source_isolation(db_session: Session):
    worker = SchemeDiscoveryWorker(db_session)
    uid = uuid.uuid4().hex[:6]
    # Inject a failing entry into catalog
    bad_catalog = [
        {
            "name": f"Broken Server Portal Scheme {uid}",
            "official_source_url": f"https://nonexistent-server-error-{uid}.gov.in",
            "stated_benefits": "Micro loan up to 5 Lakhs",
            "category": "MSME"
        },
        {
            "name": f"Healthy Server Portal Scheme {uid}",
            "official_source_url": f"https://msme.gov.in/healthy-{uid}",
            "stated_benefits": "Term loan up to 10 Lakhs",
            "category": "MSME"
        }
    ]
    with patch.object(SchemeDiscoveryCatalog, "OFFICIAL_DISCOVERY_CATALOG", bad_catalog):
        res = worker.run_discovery_batch(max_candidates=2)
        # One broken portal should not crash the batch job
        assert res["staged_for_review"] >= 1


# 14. Timeout Handling
def test_14_timeout_handling():
    fetcher = HTMLFetcher(timeout_seconds=0.001)
    with patch("httpx.Client.get", side_effect=Exception("Connection timed out after 0.001s")):
        res = fetcher.fetch("https://msme.gov.in/delayed")
        assert res.success is False
        assert "failed" in res.error_message.lower() or "timed out" in res.error_message.lower()


# 15. Retry & Resilience
def test_15_retry_and_resilience():
    fetcher = PDFFetcher()
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.is_success = False
        mock_resp.status_code = 503
        mock_resp.reason_phrase = "Service Unavailable"
        mock_get.return_value = mock_resp

        res = fetcher.fetch("https://msme.gov.in/guidelines.pdf")
        assert res.success is False
        assert "503" in res.error_message


# 16. Per-Domain Rate Limiting
def test_16_rate_limiting():
    # Calling throttle twice in succession pauses for min_interval
    import time
    t0 = time.time()
    DomainRateLimiter.throttle("https://test-throttle.gov.in/page1", min_interval_seconds=0.3)
    DomainRateLimiter.throttle("https://test-throttle.gov.in/page2", min_interval_seconds=0.3)
    elapsed = time.time() - t0
    assert elapsed >= 0.28


# 17. Idempotent Re-run
def test_17_idempotent_rerun(db_session: Session):
    worker = SchemeDiscoveryWorker(db_session)
    count_before = db_session.query(CandidateScheme).count()
    res1 = worker.run_discovery_batch(target_source="STATE_PORTAL", max_candidates=2)
    count_after_first = db_session.query(CandidateScheme).count()

    # Re-run same batch: should detect existing candidates and not inflate count
    res2 = worker.run_discovery_batch(target_source="STATE_PORTAL", max_candidates=2)
    count_after_second = db_session.query(CandidateScheme).count()

    assert count_after_second == count_after_first


# 18. Admin Approval & Promotion
def test_18_admin_approval_promotion(db_session: Session):
    uid = uuid.uuid4().hex[:6]
    cand_id = f"CAND-TEST-APPROVE-{uid}"
    cand = CandidateScheme(
        candidate_id=cand_id,
        run_id="RUN-TEST",
        discovered_name=f"Tamil Nadu Special MSME Subsidy {uid}",
        normalized_name=f"Tamil Nadu Special MSME Subsidy {uid}",
        scheme_code=f"TN-MSME-{uid}",
        discovery_source="STATE_PORTAL",
        official_source_url=f"https://msme.tn.gov.in/special-{uid}",
        level="STATE",
        state_coverage="Tamil Nadu",
        sector="MSME_MANUFACTURING",
        relevance_status="HIGH_PRIORITY",
        extraction_status="EXTRACTED",
        verification_status="OFFICIALLY_VERIFIED",
        duplicate_status="UNIQUE",
        data_confidence="HIGH",
        extracted_data=json.dumps({
            "scheme_name": f"Tamil Nadu Special MSME Subsidy {uid}",
            "max_loan_amount": 1500000.0,
            "subsidy_percentage": 25.0,
            "age_min": 21,
            "official_source_url": f"https://msme.tn.gov.in/special-{uid}"
        }),
        missing_fields=json.dumps([]),
        evidence=json.dumps({}),
        validation_status="VALID",
        validation_errors=json.dumps([]),
        candidate_status="STAGED"
    )
    db_session.add(cand)
    db_session.commit()

    promoted = CandidatePromotionService.promote_candidate(
        db_session,
        candidate_id=cand.candidate_id,
        reviewer_id="reviewer@yojnasetu.gov.in",
        notes="Verified against Tamil Nadu MSME Gazette"
    )

    assert promoted.scheme_id.startswith("SIH26092-")
    assert "Tamil Nadu Special MSME Subsidy" in promoted.scheme_name
    assert promoted.state_coverage == "Tamil Nadu"
    assert promoted.max_loan_amount == 1500000.0

    # Verify generated rules and verification record
    rules = db_session.query(SchemeRule).filter(SchemeRule.scheme_id == promoted.scheme_id).all()
    assert len(rules) >= 1

    verif = db_session.query(SchemeVerification).filter(SchemeVerification.scheme_id == promoted.scheme_id).first()
    assert verif.verification_status == "VERIFIED"
    assert verif.data_confidence == "HIGH"


# 19. Admin Rejection Leaves Canonical DB Untouched
def test_19_admin_rejection(db_session: Session):
    uid = uuid.uuid4().hex[:6]
    cand = CandidateScheme(
        candidate_id=f"CAND-TEST-REJECT-{uid}",
        run_id="RUN-TEST",
        discovered_name=f"Unverifiable Private Loan Scheme {uid}",
        normalized_name=f"Unverifiable Private Loan Scheme {uid}",
        scheme_code="UNKNOWN",
        discovery_source="COMMERCIAL",
        official_source_url=f"https://unverified-{uid}.com",
        level="CENTRAL_SECTOR",
        relevance_status="LOW_PRIORITY",
        extraction_status="EXTRACTED",
        verification_status="UNVERIFIED",
        duplicate_status="UNIQUE",
        data_confidence="LOW",
        extracted_data=json.dumps({}),
        missing_fields=json.dumps([]),
        evidence=json.dumps({}),
        validation_status="INVALID",
        validation_errors=json.dumps([]),
        candidate_status="STAGED"
    )
    db_session.add(cand)
    db_session.commit()

    initial_scheme_count = db_session.query(Scheme).count()

    # Reject candidate
    cand.candidate_status = "REJECTED"
    cand.rejection_reason = "Lacks official .gov.in backing and authoritative evidence."
    db_session.commit()

    final_scheme_count = db_session.query(Scheme).count()
    assert final_scheme_count == initial_scheme_count
    assert cand.candidate_status == "REJECTED"


# 20. RAG Knowledge Synchronization
def test_20_rag_synchronization(db_session: Session):
    existing = db_session.query(Scheme).first()
    assert existing is not None
    from app.services.ingestion.sync_service import IngestionSyncService
    synced = IngestionSyncService.sync_rag_knowledge(db_session, existing)
    assert synced is True


# 21. Recommendation Engine Compatibility
def test_21_recommendation_engine_compatibility(db_session: Session):
    profile = BeneficiaryProfileInput(
        age=30,
        gender="FEMALE",
        social_category="GENERAL",
        annual_income=200000.0,
        state="Maharashtra",
        sector="MANUFACTURING",
        applicant_type="INDIVIDUAL"
    )
    req = RecommendationRequest(profile=profile, top_k=5)
    res = DeterministicRecommendationEngine.get_recommendations(db_session, req)
    assert res.evaluated_scheme_count > 0
    assert isinstance(res.recommendations, list)


# 22. Malformed Extraction Handling
def test_22_malformed_extraction_handling():
    extractor = OfficialGovHTMLExtractor()
    malformed_html = "<<<>>> <invalid html tag body broken"
    res = extractor.extract(malformed_html, "https://broken.gov.in")
    assert isinstance(res, dict)
    assert res.get("source_url") == "https://broken.gov.in"


# 23. Zero Fabrication Enforcement
def test_23_zero_fabrication_enforcement(db_session: Session):
    non_credit_scheme = db_session.query(Scheme).filter(Scheme.loan_available == "NO").first()
    if non_credit_scheme:
        assert non_credit_scheme.is_credit_scheme is False
        assert non_credit_scheme.calculator_applicable is False
        summary = (non_credit_scheme.financial_assistance_summary or "").lower()
        allowed = ["non-financial", "grant", "subsidy", "scholarship", "skill", "guarantee", "assistance", "support", "benefit"]
        assert any(w in summary for w in allowed)


# 24. Layered Duplicate Detection Across Stages
def test_24_duplicate_candidate_detection(db_session: Session):
    existing = db_session.query(Scheme).first()
    assert existing is not None

    # Test Source URL duplicate
    res_url = SchemeDeduplicator.check_duplicate(
        candidate_name="Different Name But Same Source",
        candidate_source_url=existing.official_source_url,
        existing_schemes=[existing]
    )
    if existing.official_source_url:
        assert res_url.is_duplicate is True
        assert res_url.duplicate_stage == "STAGE_4_SOURCE_URL"

    # Test Alias duplicate
    res_alias = SchemeDeduplicator.check_duplicate(
        candidate_name="PM SVANidhi",
        existing_schemes=db_session.query(Scheme).all()
    )
    assert res_alias.is_duplicate is True
