import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Scheme, SchemeRule, SchemeVerification
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.eligibility import (
    RuleEvaluationResult,
    SchemeEligibilityStatus,
    SchemeEligibilityResult
)
from app.schemas.recommendation import RecommendationRequest
from app.engine.eligibility import DeterministicEligibilityEngine
from app.engine.recommendation import DeterministicRecommendationEngine
from app.engine.operators import evaluate_operator
from app.engine.taxonomy import TaxonomyMatcher


@pytest.fixture(scope="module")
def audit_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    # Seed representative schemes for audit testing
    schemes = [
        # 1. National Central Scheme (PMEGP-style)
        Scheme(
            scheme_id="AUDIT-NATIONAL-001",
            scheme_name="National Enterprise Support Scheme",
            ministry="Ministry of Micro, Small and Medium Enterprises",
            scheme_type="CENTRAL_SECTOR",
            state_coverage="ALL INDIA",
            sc_required=False,
            gender_condition="ALL",
            age_min=18,
            age_max=60,
            income_limit=None,
            scheme_status="ACTIVE",
            max_loan_amount=2500000.0,
        ),
        # 2. State-Specific Scheme (Gujarat only)
        Scheme(
            scheme_id="AUDIT-STATE-GJ",
            scheme_name="Gujarat Khadi & Village Industries Scheme",
            ministry="Government of Gujarat",
            scheme_type="STATE",
            state_coverage="Gujarat",
            state_restriction="YES",
            sc_required=False,
            gender_condition="ALL",
            age_min=21,
            age_max=55,
            income_limit=300000.0,
            scheme_status="ACTIVE",
            max_loan_amount=500000.0,
        ),
        # 3. Multi-State Scheme (Karnataka & Maharashtra)
        Scheme(
            scheme_id="AUDIT-MULTI-STATE",
            scheme_name="Western Corridor Agro Cluster Scheme",
            ministry="Ministry of Agriculture",
            scheme_type="CENTRAL_SECTOR",
            state_coverage="Karnataka, Maharashtra",
            state_restriction="YES",
            sc_required=False,
            gender_condition="ALL",
            age_min=18,
            age_max=65,
            income_limit=500000.0,
            scheme_status="ACTIVE",
            max_loan_amount=1000000.0,
        ),
        # 4. Regional Scheme (North Eastern Region / NER)
        Scheme(
            scheme_id="AUDIT-REGIONAL-NER",
            scheme_name="North Eastern Region Micro Finance Scheme",
            ministry="Ministry of Development of North Eastern Region",
            scheme_type="CENTRAL_SECTOR",
            state_coverage="North Eastern Region",
            state_restriction="YES",
            sc_required=False,
            gender_condition="ALL",
            age_min=18,
            age_max=60,
            income_limit=400000.0,
            scheme_status="ACTIVE",
            max_loan_amount=300000.0,
        ),
        # 5. Malformed / Ambiguous Geography Scheme
        Scheme(
            scheme_id="AUDIT-MALFORMED-GEO",
            scheme_name="Special Economic Zone Development Scheme",
            ministry="Statutory Board",
            scheme_type="STATE",
            state_coverage="Special Autonomous Zone Delta-9",
            state_restriction="YES",
            sc_required=False,
            gender_condition="ALL",
            age_min=18,
            age_max=60,
            income_limit=500000.0,
            scheme_status="ACTIVE",
            max_loan_amount=500000.0,
        ),
        # 6. SC-Required Mandatory Scheme (NSFDC Mahila Samriddhi style)
        Scheme(
            scheme_id="AUDIT-SC-MANDATORY",
            scheme_name="National Scheduled Caste Special Assistance Scheme",
            ministry="Ministry of Social Justice and Empowerment",
            scheme_type="CENTRAL_SECTOR",
            state_coverage="ALL INDIA",
            sc_required=True,
            social_category="SC",
            gender_condition="ALL",
            age_min=18,
            age_max=50,
            income_limit=300000.0,
            scheme_status="ACTIVE",
            max_loan_amount=200000.0,
        ),
        # 7. Female-Only Mandatory Scheme (Women Exclusive)
        Scheme(
            scheme_id="AUDIT-FEMALE-ONLY",
            scheme_name="National Women Entrepreneur Empowerment Scheme",
            ministry="Ministry of Women and Child Development",
            scheme_type="CENTRAL_SECTOR",
            state_coverage="ALL INDIA",
            sc_required=False,
            gender_condition="FEMALE_ONLY",
            gender_requirement="WOMEN_ONLY",
            age_min=18,
            age_max=55,
            income_limit=400000.0,
            scheme_status="ACTIVE",
            max_loan_amount=500000.0,
        ),
        # 8. SC-Women Combined Exclusive Scheme (Mahila Samriddhi)
        Scheme(
            scheme_id="AUDIT-SC-WOMAN-EXCL",
            scheme_name="Scheduled Caste Women Special Micro Unit Scheme",
            ministry="Ministry of Social Justice and Empowerment",
            scheme_type="CENTRAL_SECTOR",
            state_coverage="ALL INDIA",
            sc_required=True,
            social_category="SC",
            gender_condition="FEMALE_ONLY",
            age_min=18,
            age_max=50,
            income_limit=300000.0,
            scheme_status="ACTIVE",
            max_loan_amount=140000.0,
        ),
        # 9. Discontinued / Inactive Scheme
        Scheme(
            scheme_id="AUDIT-DISCONTINUED",
            scheme_name="Legacy Artisans Grant 2018",
            ministry="Ministry of Textiles",
            scheme_type="CENTRAL_SECTOR",
            state_coverage="ALL INDIA",
            sc_required=False,
            gender_condition="ALL",
            scheme_status="DISCONTINUED",
        ),
    ]

    for s in schemes:
        session.add(s)
    session.commit()

    # Add explicit rule-table rules for AUDIT-STATE-GJ
    rule_gj = SchemeRule(
        rule_id="RULE-GJ-GEO",
        scheme_id="AUDIT-STATE-GJ",
        field="state",
        operator="IN",
        value="GUJARAT",
        value_type="ENUM",
        rule_type="ELIGIBILITY",
        priority="CRITICAL",
        condition_group="BASE",
        active=True
    )
    session.add(rule_gj)
    session.commit()

    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# 1. GEOGRAPHY STATUTORY AUDIT TESTS
# ==============================================================================

def test_geography_all_india_passes_all_states(audit_db):
    """ALL INDIA / national scheme + any valid Indian state => eligible"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-NATIONAL-001").first()
    assert sch is not None

    for state in ["Maharashtra", "Rajasthan", "Bihar", "Tamil Nadu", "Assam", "Delhi", "Ladakh"]:
        profile = BeneficiaryProfileInput(state=state, age=30, gender="MALE", social_category="GENERAL")
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.ELIGIBLE
        assert any(r.field == "state" and r.result == RuleEvaluationResult.PASS for r in res.hard_rules_passed)


def test_geography_state_specific_matching_state(audit_db):
    """state-specific scheme + matching state => eligible"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-STATE-GJ").first()
    profile = BeneficiaryProfileInput(state="Gujarat", age=30, gender="MALE", annual_income=200000.0)
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
    assert res.status == SchemeEligibilityStatus.ELIGIBLE
    assert any(r.field == "state" and r.result == RuleEvaluationResult.PASS for r in res.hard_rules_passed)


def test_geography_state_specific_different_state(audit_db):
    """state-specific scheme + different state => INELIGIBLE"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-STATE-GJ").first()
    for wrong_state in ["Maharashtra", "Rajasthan", "Uttar Pradesh", "Bihar"]:
        profile = BeneficiaryProfileInput(state=wrong_state, age=30, gender="MALE", annual_income=200000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.INELIGIBLE
        assert any(r.field == "state" and r.result == RuleEvaluationResult.FAIL for r in res.hard_rules_failed)


def test_geography_multi_state_coverage_included(audit_db):
    """multi-state coverage including user's state => eligible"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-MULTI-STATE").first()
    for st in ["Karnataka", "Maharashtra", "MH", "KA"]:
        profile = BeneficiaryProfileInput(state=st, age=30, gender="MALE", annual_income=300000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.ELIGIBLE
        assert any(r.field == "state" and r.result == RuleEvaluationResult.PASS for r in res.hard_rules_passed)


def test_geography_multi_state_coverage_excluded(audit_db):
    """multi-state coverage excluding user's state => INELIGIBLE"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-MULTI-STATE").first()
    for wrong_state in ["Rajasthan", "Gujarat", "Kerala", "Punjab"]:
        profile = BeneficiaryProfileInput(state=wrong_state, age=30, gender="MALE", annual_income=300000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.INELIGIBLE
        assert any(r.field == "state" and r.result == RuleEvaluationResult.FAIL for r in res.hard_rules_failed)


def test_geography_missing_user_state_yields_insufficient_info(audit_db):
    """missing/unknown user state when geography is mandatory => INSUFFICIENT_INFORMATION, NOT INELIGIBLE"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-STATE-GJ").first()
    for sentinel in [None, "UNKNOWN", "NONE", ""]:
        profile = BeneficiaryProfileInput(state=sentinel, age=30, gender="MALE", annual_income=200000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION, f"Expected INSUFFICIENT_INFO for {sentinel}, got {res.status}"
        assert any(r.field == "state" and r.result == RuleEvaluationResult.UNKNOWN for r in res.unknown_eligibility_rules)


def test_geography_malformed_ambiguous_coverage_not_all_india(audit_db):
    """malformed/ambiguous coverage must not silently become ALL INDIA"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-MALFORMED-GEO").first()
    profile = BeneficiaryProfileInput(state="Maharashtra", age=30, gender="MALE", annual_income=200000.0)
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
    # Must NOT be ELIGIBLE (malformed coverage should yield INSUFFICIENT_INFORMATION)
    assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
    assert any(r.field == "state" and r.result == RuleEvaluationResult.UNKNOWN for r in res.unknown_eligibility_rules)


def test_geography_regional_north_east_expansion(audit_db):
    """regional coverage (North Eastern Region) encompasses all 8 NE states, rejects others"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-REGIONAL-NER").first()
    
    # All 8 NE States must be eligible
    for ne_state in ["Assam", "Arunachal Pradesh", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Sikkim", "Tripura"]:
        profile = BeneficiaryProfileInput(state=ne_state, age=30, gender="MALE", annual_income=200000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.ELIGIBLE, f"Failed for NE state: {ne_state}"

    # Non-NE States must be strictly INELIGIBLE
    for non_ne in ["Maharashtra", "Gujarat", "Kerala", "Bihar", "Delhi"]:
        profile = BeneficiaryProfileInput(state=non_ne, age=30, gender="MALE", annual_income=200000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.INELIGIBLE, f"Expected INELIGIBLE for non-NE: {non_ne}"


def test_geography_cases_a_through_g_explicit(audit_db):
    """
    Explicitly tests cases A through G as defined in statutory requirement 3:
    A. ALL INDIA scheme + Rajasthan user => ELIGIBLE
    B. Rajasthan-only scheme + Rajasthan user => ELIGIBLE
    C. Rajasthan-only scheme + Gujarat user => INELIGIBLE
    D. Rajasthan + Gujarat scheme + Gujarat user => ELIGIBLE
    E. Rajasthan + Gujarat scheme + Tamil Nadu user => INELIGIBLE
    F. unknown user state => INSUFFICIENT_INFORMATION
    G. malformed/ambiguous state coverage => INSUFFICIENT_INFORMATION
    """
    # Scheme definitions
    sch_all_india = Scheme(
        scheme_id="AUDIT-GEO-CASE-A",
        scheme_name="National Scheme A",
        state_coverage="ALL INDIA",
        scheme_type="CENTRAL_SECTOR",
        age_min=18, age_max=65
    )
    sch_rj_only = Scheme(
        scheme_id="AUDIT-GEO-CASE-B",
        scheme_name="Rajasthan State Scheme B",
        state_coverage="Rajasthan",
        state_restriction="YES",
        scheme_type="STATE",
        age_min=18, age_max=65
    )
    sch_rj_gj = Scheme(
        scheme_id="AUDIT-GEO-CASE-D",
        scheme_name="Western Corridor Scheme D",
        state_coverage="Rajasthan, Gujarat",
        state_restriction="YES",
        scheme_type="CENTRAL_SECTOR",
        age_min=18, age_max=65
    )
    sch_malformed = Scheme(
        scheme_id="AUDIT-GEO-CASE-G",
        scheme_name="Malformed Geo Scheme G",
        state_coverage="Zone 9 / District Cluster Omega",
        state_restriction="YES",
        scheme_type="STATE",
        age_min=18, age_max=65
    )

    # A. ALL INDIA scheme + Rajasthan user => ELIGIBLE
    prof_rj = BeneficiaryProfileInput(state="Rajasthan", age=30, gender="MALE")
    res_a = DeterministicEligibilityEngine.evaluate_scheme(sch_all_india, prof_rj)
    assert res_a.status == SchemeEligibilityStatus.ELIGIBLE

    # B. Rajasthan-only scheme + Rajasthan user => ELIGIBLE
    res_b = DeterministicEligibilityEngine.evaluate_scheme(sch_rj_only, prof_rj)
    assert res_b.status == SchemeEligibilityStatus.ELIGIBLE

    # C. Rajasthan-only scheme + Gujarat user => INELIGIBLE
    prof_gj = BeneficiaryProfileInput(state="Gujarat", age=30, gender="MALE")
    res_c = DeterministicEligibilityEngine.evaluate_scheme(sch_rj_only, prof_gj)
    assert res_c.status == SchemeEligibilityStatus.INELIGIBLE
    assert any(r.field == "state" and r.result == RuleEvaluationResult.FAIL for r in res_c.hard_rules_failed)

    # D. Rajasthan + Gujarat scheme + Gujarat user => ELIGIBLE
    res_d = DeterministicEligibilityEngine.evaluate_scheme(sch_rj_gj, prof_gj)
    assert res_d.status == SchemeEligibilityStatus.ELIGIBLE

    # E. Rajasthan + Gujarat scheme + Tamil Nadu user => INELIGIBLE
    prof_tn = BeneficiaryProfileInput(state="Tamil Nadu", age=30, gender="MALE")
    res_e = DeterministicEligibilityEngine.evaluate_scheme(sch_rj_gj, prof_tn)
    assert res_e.status == SchemeEligibilityStatus.INELIGIBLE
    assert any(r.field == "state" and r.result == RuleEvaluationResult.FAIL for r in res_e.hard_rules_failed)

    # F. unknown user state => INSUFFICIENT_INFORMATION
    prof_unknown = BeneficiaryProfileInput(state=None, age=30, gender="MALE")
    res_f = DeterministicEligibilityEngine.evaluate_scheme(sch_rj_only, prof_unknown)
    assert res_f.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
    assert any(r.field == "state" and r.result == RuleEvaluationResult.UNKNOWN for r in res_f.unknown_eligibility_rules)

    # G. malformed/ambiguous state coverage => INSUFFICIENT_INFORMATION
    res_g = DeterministicEligibilityEngine.evaluate_scheme(sch_malformed, prof_rj)
    assert res_g.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
    assert any(r.field == "state" and r.result == RuleEvaluationResult.UNKNOWN for r in res_g.unknown_eligibility_rules)


# ==============================================================================
# 2. SC / CASTE STATUTORY AUDIT TESTS
# ==============================================================================

def test_sc_caste_required_with_sc_applicant(audit_db):
    """SC-required scheme + SC applicant => eligible"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-SC-MANDATORY").first()
    
    # Via is_sc flag
    p1 = BeneficiaryProfileInput(is_sc=True, state="Maharashtra", age=30, gender="MALE", annual_income=200000.0)
    assert DeterministicEligibilityEngine.evaluate_scheme(sch, p1).status == SchemeEligibilityStatus.ELIGIBLE

    # Via social_category string
    p2 = BeneficiaryProfileInput(social_category="SC", state="Maharashtra", age=30, gender="MALE", annual_income=200000.0)
    assert DeterministicEligibilityEngine.evaluate_scheme(sch, p2).status == SchemeEligibilityStatus.ELIGIBLE

    # Via Scheduled Caste text
    p3 = BeneficiaryProfileInput(social_category="Scheduled Caste", state="Maharashtra", age=30, gender="MALE", annual_income=200000.0)
    assert DeterministicEligibilityEngine.evaluate_scheme(sch, p3).status == SchemeEligibilityStatus.ELIGIBLE


def test_sc_caste_required_with_non_sc_applicant(audit_db):
    """SC-required scheme + non-SC applicant => INELIGIBLE"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-SC-MANDATORY").first()
    for cat in ["GENERAL", "OBC", "ST", "MINORITY"]:
        profile = BeneficiaryProfileInput(social_category=cat, is_sc=False, state="Maharashtra", age=30, gender="MALE", annual_income=200000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.INELIGIBLE
        assert any(r.field == "social_category" and r.result == RuleEvaluationResult.FAIL for r in res.hard_rules_failed)


def test_sc_caste_required_with_unknown_caste(audit_db):
    """SC-required scheme + unknown caste => INSUFFICIENT_INFORMATION"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-SC-MANDATORY").first()
    for sentinel in [None, "UNKNOWN", "NONE", ""]:
        profile = BeneficiaryProfileInput(social_category=sentinel, is_sc=None, state="Maharashtra", age=30, gender="MALE", annual_income=200000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION, f"Expected INSUFFICIENT_INFO for {sentinel}"
        assert any(r.field == "social_category" and r.result == RuleEvaluationResult.UNKNOWN for r in res.unknown_eligibility_rules)


def test_non_sc_scheme_allows_sc_applicants(audit_db):
    """non-SC-specific scheme must not incorrectly reject SC applicants unless statutory rule requires exclusion"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-NATIONAL-001").first()
    p_sc = BeneficiaryProfileInput(is_sc=True, social_category="SC", state="Maharashtra", age=30, gender="MALE")
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, p_sc)
    assert res.status == SchemeEligibilityStatus.ELIGIBLE


# ==============================================================================
# 3. GENDER STATUTORY AUDIT TESTS
# ==============================================================================

def test_gender_female_only_with_female_applicant(audit_db):
    """female-only scheme + FEMALE => eligible"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-FEMALE-ONLY").first()
    for f_term in ["FEMALE", "WOMAN", "Female"]:
        profile = BeneficiaryProfileInput(gender=f_term, state="Maharashtra", age=30, annual_income=200000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.ELIGIBLE
        assert any(r.field == "gender" and r.result == RuleEvaluationResult.PASS for r in res.hard_rules_passed)


def test_gender_female_only_with_male_applicant(audit_db):
    """female-only scheme + MALE => INELIGIBLE"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-FEMALE-ONLY").first()
    for m_term in ["MALE", "MAN", "Male"]:
        profile = BeneficiaryProfileInput(gender=m_term, state="Maharashtra", age=30, annual_income=200000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.INELIGIBLE
        assert any(r.field == "gender" and r.result == RuleEvaluationResult.FAIL for r in res.hard_rules_failed)


def test_gender_female_only_with_unknown_gender(audit_db):
    """female-only scheme + UNKNOWN gender => INSUFFICIENT_INFORMATION"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-FEMALE-ONLY").first()
    for sentinel in [None, "UNKNOWN", "NONE", ""]:
        profile = BeneficiaryProfileInput(gender=sentinel, state="Maharashtra", age=30, annual_income=200000.0)
        res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
        assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION, f"Expected INSUFFICIENT_INFO for {sentinel}"
        assert any(r.field == "gender" and r.result == RuleEvaluationResult.UNKNOWN for r in res.unknown_eligibility_rules)


def test_gender_neutral_scheme_allows_all(audit_db):
    """gender-neutral scheme => both male and female can remain eligible"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-NATIONAL-001").first()
    p_male = BeneficiaryProfileInput(gender="MALE", state="Maharashtra", age=30)
    p_female = BeneficiaryProfileInput(gender="FEMALE", state="Maharashtra", age=30)
    assert DeterministicEligibilityEngine.evaluate_scheme(sch, p_male).status == SchemeEligibilityStatus.ELIGIBLE
    assert DeterministicEligibilityEngine.evaluate_scheme(sch, p_female).status == SchemeEligibilityStatus.ELIGIBLE


# ==============================================================================
# 4. AGE STATUTORY AUDIT TESTS
# ==============================================================================

def test_age_boundaries_exact(audit_db):
    """Verify exact age boundaries: age == min, age == max => eligible; age < min, age > max => INELIGIBLE"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-STATE-GJ").first() # min=21, max=55
    assert sch.age_min == 21 and sch.age_max == 55

    # 1. Exactly at min boundary: 21 => eligible
    p_min = BeneficiaryProfileInput(state="Gujarat", age=21, gender="MALE", annual_income=200000.0)
    assert DeterministicEligibilityEngine.evaluate_scheme(sch, p_min).status == SchemeEligibilityStatus.ELIGIBLE

    # 2. Exactly at max boundary: 55 => eligible
    p_max = BeneficiaryProfileInput(state="Gujarat", age=55, gender="MALE", annual_income=200000.0)
    assert DeterministicEligibilityEngine.evaluate_scheme(sch, p_max).status == SchemeEligibilityStatus.ELIGIBLE

    # 3. Below min boundary: 20 => INELIGIBLE
    p_under = BeneficiaryProfileInput(state="Gujarat", age=20, gender="MALE", annual_income=200000.0)
    res_under = DeterministicEligibilityEngine.evaluate_scheme(sch, p_under)
    assert res_under.status == SchemeEligibilityStatus.INELIGIBLE
    assert any(r.field == "age" and r.result == RuleEvaluationResult.FAIL for r in res_under.hard_rules_failed)

    # 4. Above max boundary: 56 => INELIGIBLE
    p_over = BeneficiaryProfileInput(state="Gujarat", age=56, gender="MALE", annual_income=200000.0)
    res_over = DeterministicEligibilityEngine.evaluate_scheme(sch, p_over)
    assert res_over.status == SchemeEligibilityStatus.INELIGIBLE
    assert any(r.field == "age" and r.result == RuleEvaluationResult.FAIL for r in res_over.hard_rules_failed)

    # 5. Missing age when mandatory => INSUFFICIENT_INFORMATION
    p_missing = BeneficiaryProfileInput(state="Gujarat", age=None, gender="MALE", annual_income=200000.0)
    res_miss = DeterministicEligibilityEngine.evaluate_scheme(sch, p_missing)
    assert res_miss.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
    assert any(r.field == "age" and r.result == RuleEvaluationResult.UNKNOWN for r in res_miss.unknown_eligibility_rules)


# ==============================================================================
# 5. INCOME STATUTORY AUDIT TESTS
# ==============================================================================

def test_income_boundaries_exact(audit_db):
    """income == threshold => eligible; income > threshold => INELIGIBLE; missing income => INSUFFICIENT_INFORMATION"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-STATE-GJ").first() # limit = ₹300,000
    assert sch.income_limit == 300000.0

    # 1. Exactly at threshold: ₹300,000 => eligible
    p_exact = BeneficiaryProfileInput(state="Gujarat", age=30, gender="MALE", annual_income=300000.0)
    assert DeterministicEligibilityEngine.evaluate_scheme(sch, p_exact).status == SchemeEligibilityStatus.ELIGIBLE

    # 2. Below threshold: ₹299,999 => eligible
    p_below = BeneficiaryProfileInput(state="Gujarat", age=30, gender="MALE", annual_income=299999.0)
    assert DeterministicEligibilityEngine.evaluate_scheme(sch, p_below).status == SchemeEligibilityStatus.ELIGIBLE

    # 3. Beyond threshold: ₹300,001 => INELIGIBLE
    p_above = BeneficiaryProfileInput(state="Gujarat", age=30, gender="MALE", annual_income=300001.0)
    res_above = DeterministicEligibilityEngine.evaluate_scheme(sch, p_above)
    assert res_above.status == SchemeEligibilityStatus.INELIGIBLE
    assert any(r.field == "annual_income" and r.result == RuleEvaluationResult.FAIL for r in res_above.hard_rules_failed)

    # 4. Missing income when mandatory => INSUFFICIENT_INFORMATION
    p_missing = BeneficiaryProfileInput(state="Gujarat", age=30, gender="MALE", annual_income=None)
    res_miss = DeterministicEligibilityEngine.evaluate_scheme(sch, p_missing)
    assert res_miss.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION
    assert any(r.field == "annual_income" and r.result == RuleEvaluationResult.UNKNOWN for r in res_miss.unknown_eligibility_rules)


# ==============================================================================
# 6. RULE TABLE PRECEDENCE & INTERACTION AUDIT TESTS
# ==============================================================================

def test_precedence_ineligible_over_insufficient_info(audit_db):
    """INELIGIBLE statutory condition takes precedence over missing data"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-STATE-GJ").first()
    # Wrong state (fails state gate) AND missing age (would be insufficient info)
    p_conflict = BeneficiaryProfileInput(state="Bihar", age=None, annual_income=None, gender="MALE")
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, p_conflict)
    # INELIGIBLE must dominate
    assert res.status == SchemeEligibilityStatus.INELIGIBLE
    assert len(res.hard_rules_failed) > 0


def test_discontinued_scheme_not_applicable(audit_db):
    """Discontinued/inactive scheme must return NOT_APPLICABLE"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-DISCONTINUED").first()
    p_valid = BeneficiaryProfileInput(state="Maharashtra", age=30, gender="MALE")
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, p_valid)
    assert res.status == SchemeEligibilityStatus.NOT_APPLICABLE


def test_master_field_cannot_bypass_rule_table_restriction(audit_db):
    """A rule-table restriction must never be accidentally bypassed by a master-field value"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-STATE-GJ").first()
    # Master scheme says state_coverage = Gujarat, rule table says state IN GUJARAT
    # An applicant with state="Rajasthan" must fail both master and rule table
    profile = BeneficiaryProfileInput(state="Rajasthan", age=30, gender="MALE", annual_income=200000.0)
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, profile)
    assert res.status == SchemeEligibilityStatus.INELIGIBLE


# ==============================================================================
# 7. COMBINATION TESTS (REQUIREMENT 8)
# ==============================================================================

def test_combination_sc_female_correct_state(audit_db):
    """SC + female + correct state on SC-Woman exclusive scheme => eligible"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-SC-WOMAN-EXCL").first()
    p = BeneficiaryProfileInput(social_category="SC", is_sc=True, gender="FEMALE", state="Maharashtra", age=28, annual_income=150000.0)
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, p)
    assert res.status == SchemeEligibilityStatus.ELIGIBLE


def test_combination_sc_male_correct_state(audit_db):
    """SC + male + correct state on SC-Woman exclusive scheme => INELIGIBLE (fails gender)"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-SC-WOMAN-EXCL").first()
    p = BeneficiaryProfileInput(social_category="SC", is_sc=True, gender="MALE", state="Maharashtra", age=28, annual_income=150000.0)
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, p)
    assert res.status == SchemeEligibilityStatus.INELIGIBLE
    assert any(r.field == "gender" and r.result == RuleEvaluationResult.FAIL for r in res.hard_rules_failed)


def test_combination_non_sc_female_correct_state(audit_db):
    """non-SC + female + correct state on SC-Woman exclusive scheme => INELIGIBLE (fails caste)"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-SC-WOMAN-EXCL").first()
    p = BeneficiaryProfileInput(social_category="GENERAL", is_sc=False, gender="FEMALE", state="Maharashtra", age=28, annual_income=150000.0)
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, p)
    assert res.status == SchemeEligibilityStatus.INELIGIBLE
    assert any(r.field == "social_category" and r.result == RuleEvaluationResult.FAIL for r in res.hard_rules_failed)


def test_combination_sc_female_wrong_state(audit_db):
    """SC + female + wrong state on state-specific scheme => INELIGIBLE (fails state)"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-STATE-GJ").first() # Gujarat only
    p = BeneficiaryProfileInput(social_category="SC", is_sc=True, gender="FEMALE", state="Bihar", age=28, annual_income=150000.0)
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, p)
    assert res.status == SchemeEligibilityStatus.INELIGIBLE
    assert any(r.field == "state" and r.result == RuleEvaluationResult.FAIL for r in res.hard_rules_failed)


def test_combination_unknown_caste_female_correct_state(audit_db):
    """unknown caste + female + correct state on SC-Woman scheme => INSUFFICIENT_INFORMATION"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-SC-WOMAN-EXCL").first()
    p = BeneficiaryProfileInput(social_category="UNKNOWN", is_sc=None, gender="FEMALE", state="Maharashtra", age=28, annual_income=150000.0)
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, p)
    assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION


def test_combination_sc_unknown_gender_correct_state(audit_db):
    """SC + unknown gender + correct state on SC-Woman scheme => INSUFFICIENT_INFORMATION"""
    sch = audit_db.query(Scheme).filter(Scheme.scheme_id == "AUDIT-SC-WOMAN-EXCL").first()
    p = BeneficiaryProfileInput(social_category="SC", is_sc=True, gender=None, state="Maharashtra", age=28, annual_income=150000.0)
    res = DeterministicEligibilityEngine.evaluate_scheme(sch, p)
    assert res.status == SchemeEligibilityStatus.INSUFFICIENT_INFORMATION


# ==============================================================================
# 8. RECOMMENDATION INTEGRATION & ZERO LEAKAGE
# ==============================================================================

def test_recommendation_never_contains_ineligible_schemes(audit_db):
    """INELIGIBLE schemes can NEVER enter the final recommendation list"""
    # Profile from Bihar, General category, Male
    profile = BeneficiaryProfileInput(
        state="Bihar",
        gender="MALE",
        social_category="GENERAL",
        is_sc=False,
        age=30,
        annual_income=200000.0
    )
    req = RecommendationRequest(profile=profile, top_k=50)
    resp = DeterministicRecommendationEngine.get_recommendations(audit_db, req)

    rec_ids = [r.scheme_id for r in resp.recommendations]
    
    # Gujarat scheme must NOT be in top recommendations
    assert "AUDIT-STATE-GJ" not in rec_ids
    # SC mandatory scheme must NOT be in top recommendations
    assert "AUDIT-SC-MANDATORY" not in rec_ids
    # Female only scheme must NOT be in top recommendations
    assert "AUDIT-FEMALE-ONLY" not in rec_ids
    # SC woman scheme must NOT be in top recommendations
    assert "AUDIT-SC-WOMAN-EXCL" not in rec_ids
    # Discontinued scheme must NOT be in top recommendations
    assert "AUDIT-DISCONTINUED" not in rec_ids

    # All top recommendations must have eligible == True and status == ELIGIBLE
    for r in resp.recommendations:
        assert r.eligible is True
        assert r.eligibility_status == "ELIGIBLE"


def test_semantic_query_cannot_override_statutory_failure(audit_db):
    """Semantic resonance query cannot override a statutory failure"""
    profile = BeneficiaryProfileInput(
        state="Bihar",
        gender="MALE",
        social_category="GENERAL",
        is_sc=False,
        age=30,
        annual_income=200000.0
    )
    # Query mentions terms that match Gujarat or Women scheme exactly
    req = RecommendationRequest(
        profile=profile,
        top_k=50,
        semantic_query="Gujarat Khadi Village Industries and Women Entrepreneur Empowerment"
    )
    resp = DeterministicRecommendationEngine.get_recommendations(audit_db, req)
    rec_ids = [r.scheme_id for r in resp.recommendations]

    assert "AUDIT-STATE-GJ" not in rec_ids
    assert "AUDIT-FEMALE-ONLY" not in rec_ids
