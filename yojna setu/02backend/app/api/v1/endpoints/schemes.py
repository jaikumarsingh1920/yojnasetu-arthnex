import json
import math
import re
from typing import Optional, List, Dict, Any, Set
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, and_, asc, desc, func
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, get_optional_current_user
from app.models.user import User
from app.models.scheme import Scheme
from app.models.verification import SchemeVerification
from app.schemas.profile import BeneficiaryProfileInput
from app.engine.eligibility import DeterministicEligibilityEngine
from app.schemas.scheme import (
    SchemeListItemResponse,
    PaginatedSchemeListResponse,
    SchemeDetailResponse,
    FilterOptionsResponse,
    FilterOptionItem,
    SchemeComparisonResponse,
    SchemeComparisonItem,
    SchemePersonalizedEligibility,
)

router = APIRouter()

# Multilingual and domain synonym mapping for Hindi and English search
MULTILINGUAL_SYNONYMS: Dict[str, List[str]] = {
    "ऋण": ["loan", "credit", "mudra", "svanidhi", "term loan"],
    "कर्ज": ["loan", "credit", "mudra"],
    "लोन": ["loan", "credit", "mudra"],
    "मुद्रा": ["mudra", "micro finance", "shishu", "kishore", "tarun"],
    "अनुदान": ["subsidy", "grant", "assistance", "capital subsidy"],
    "सब्सिडी": ["subsidy", "grant"],
    "सहायता": ["assistance", "support", "benefit"],
    "छात्रवृत्ति": ["scholarship", "fellowship", "education", "stipend", "shreyas"],
    "वजीफा": ["scholarship", "stipend"],
    "प्रशिक्षण": ["training", "skill", "capacity building", "samarth"],
    "कौशल": ["skill", "training", "vocational"],
    "महिला": ["women", "mahila", "female", "lakhpati", "stand-up"],
    "स्त्री": ["women", "mahila", "female"],
    "नारी": ["women", "mahila", "female"],
    "कृषि": ["agriculture", "agri", "farming", "kisan", "crop", "krishi"],
    "किसान": ["kisan", "farmer", "agriculture"],
    "खेती": ["agriculture", "farming", "kisan"],
    "कारीगर": ["artisan", "craftsman", "vishwakarma", "handicraft", "handloom", "shilp"],
    "शिल्पकार": ["artisan", "craftsman", "vishwakarma", "shilp"],
    "दस्तकार": ["artisan", "craftsman"],
    "बुनकर": ["weaver", "handloom", "textile"],
    "पेंशन": ["pension", "atal pension", "social security"],
    "बीमा": ["insurance", "bima", "suraksha", "jeevan jyoti", "pmjay"],
    "स्वास्थ्य": ["health", "ayushman", "pmjay", "medical"],
    "दवा": ["health", "medical"],
    "शिक्षा": ["education", "scholarship", "study", "fellowship", "school"],
    "विश्वकर्मा": ["vishwakarma", "artisan", "toolkit", "craftsman"],
    "स्वनिधि": ["svanidhi", "street vendor", "vendor", "rehri"],
    "ठेला": ["street vendor", "vendor", "svanidhi"],
    "रोजगार": ["employment", "pmegp", "livelihood", "enterprise"],
    "उद्यम": ["msme", "enterprise", "business", "udyam"],
    "उद्योग": ["industry", "msme", "business"],
    "व्यापार": ["trade", "business", "commercial"],
    "गारंटी": ["guarantee", "cgtmse", "credit guarantee"],
    "दिव्यांग": ["pwd", "disabled", "disabilities", "divyangjan", "adip", "ddrs"],
    "विकलांग": ["pwd", "disabled", "disabilities"],
    "अल्पसंख्यक": ["minority", "nmdfc", "virasat"],
    "अनुसूचित": ["sc", "st", "scheduled caste", "scheduled tribe", "nsfdc", "nstfdc"],
    "सफाई": ["sanitation", "safai", "nskfdc", "sanitary"],
}

# Allowed sort fields to prevent SQL injection / invalid column sorting
ALLOWED_SORT_FIELDS = {
    "scheme_id": Scheme.scheme_id,
    "scheme_name": Scheme.scheme_name,
    "created_at": Scheme.created_at,
    "ministry": Scheme.ministry,
    "max_loan_amount": Scheme.max_loan_amount,
    "interest_rate_min": Scheme.interest_rate_min,
    "interest_rate_max": Scheme.interest_rate_max,
}


@router.get(
    "/filter-options",
    response_model=FilterOptionsResponse,
    summary="Get dynamically aggregated filter options with counts from database",
    description="Returns distinct ministries, sectors, financial categories, beneficiary categories, states, and application routes directly from database."
)
def get_filter_options(db: Session = Depends(get_db)):
    """
    Returns dynamically computed filter options with accurate scheme counts.
    Never hardcoded or stale.
    """
    schemes = db.query(Scheme).filter(
        or_(Scheme.scheme_status == "ACTIVE", Scheme.scheme_status == None, Scheme.scheme_status == "")
    ).all()
    total_schemes = len(schemes)

    # 1. Ministries aggregation
    ministry_counts: Dict[str, int] = {}
    for s in schemes:
        if s.ministry and s.ministry.strip() and s.ministry != "UNKNOWN":
            m = s.ministry.strip()
            ministry_counts[m] = ministry_counts.get(m, 0) + 1

    ministry_items = [
        FilterOptionItem(label=m, value=m, count=cnt)
        for m, cnt in sorted(ministry_counts.items(), key=lambda x: (-x[1], x[0]))
    ]

    # 2. Sectors aggregation
    sector_counts: Dict[str, int] = {}
    for s in schemes:
        if s.sector and s.sector.strip() and s.sector != "UNKNOWN":
            # Sectors can be semicolon-separated
            sec_parts = [p.strip() for p in s.sector.split(";") if p.strip()]
            for sec in sec_parts:
                sec_clean = sec.replace("_", " ")
                sector_counts[sec_clean] = sector_counts.get(sec_clean, 0) + 1

    sector_items = [
        FilterOptionItem(label=sec.title(), value=sec, count=cnt)
        for sec, cnt in sorted(sector_counts.items(), key=lambda x: (-x[1], x[0]))
    ]

    # 3. Financial Types aggregation
    fin_counts: Dict[str, int] = {}
    for s in schemes:
        cat = s.financial_category
        fin_counts[cat] = fin_counts.get(cat, 0) + 1

    fin_labels = {
        "LOAN_CREDIT": "Loan / Credit Schemes",
        "GRANT_SUBSIDY": "Capital Subsidy & Grants",
        "SCHOLARSHIP": "Scholarships & Education",
        "TRAINING_SKILL": "Skill Training & Toolkits",
        "GUARANTEE_CREDIT_SUPPORT": "Credit Guarantees",
        "DIRECT_BENEFIT": "Direct Benefit / Insurance / DBT",
        "NON_FINANCIAL": "Non-Financial & Advisory",
    }

    financial_type_items = [
        FilterOptionItem(label=fin_labels.get(cat, cat.replace("_", " ").title()), value=cat, count=cnt)
        for cat, cnt in sorted(fin_counts.items(), key=lambda x: (-x[1], x[0]))
    ]

    # 4. Beneficiary Categories aggregation
    beneficiary_counts: Dict[str, int] = {
        "ALL_CITIZENS": 0,
        "SC": 0,
        "ST": 0,
        "OBC": 0,
        "WOMEN": 0,
        "MINORITY": 0,
        "PWD": 0,
        "ARTISAN": 0,
        "FARMER": 0,
        "STREET_VENDOR": 0,
        "YOUTH": 0,
    }

    for s in schemes:
        txt = f"{s.scheme_name} {s.target_beneficiary or ''} {s.target_groups or ''} {s.marginalized_group or ''} {s.social_category or ''} {s.gender_condition or ''}".upper()
        if "SC" in txt or "SCHEDULED CASTE" in txt or "NSFDC" in txt:
            beneficiary_counts["SC"] += 1
        if "ST" in txt or "SCHEDULED TRIBE" in txt or "NSTFDC" in txt:
            beneficiary_counts["ST"] += 1
        if "OBC" in txt or "BACKWARD" in txt or "NBCFDC" in txt:
            beneficiary_counts["OBC"] += 1
        if "WOMEN" in txt or "FEMALE" in txt or "MAHILA" in txt or "LAKHPATI" in txt or "MATRU" in txt:
            beneficiary_counts["WOMEN"] += 1
        if "MINORITY" in txt or "NMDFC" in txt:
            beneficiary_counts["MINORITY"] += 1
        if "PWD" in txt or "DIVYANG" in txt or "DISABLED" in txt or "DISABILITIES" in txt or "ADIP" in txt or "DDRS" in txt:
            beneficiary_counts["PWD"] += 1
        if "ARTISAN" in txt or "CRAFTSMAN" in txt or "WEAVER" in txt or "VISHWAKARMA" in txt or "HANDICRAFT" in txt:
            beneficiary_counts["ARTISAN"] += 1
        if "FARMER" in txt or "KISAN" in txt or "AGRICULTURE" in txt:
            beneficiary_counts["FARMER"] += 1
        if "STREET VENDOR" in txt or "VENDOR" in txt or "SVANIDHI" in txt:
            beneficiary_counts["STREET_VENDOR"] += 1
        if "YOUTH" in txt or "STUDENT" in txt or "EDUCATION" in txt or "FELLOWSHIP" in txt:
            beneficiary_counts["YOUTH"] += 1
        if not s.marginalized_group or s.marginalized_group == "ALL" or s.marginalized_group == "UNKNOWN":
            beneficiary_counts["ALL_CITIZENS"] += 1

    beneficiary_labels = {
        "ALL_CITIZENS": "All Eligible Citizens",
        "SC": "Scheduled Caste (SC)",
        "ST": "Scheduled Tribe (ST)",
        "OBC": "Other Backward Class (OBC)",
        "WOMEN": "Women Entrepreneurs / Beneficiaries",
        "MINORITY": "Minority Communities",
        "PWD": "Persons with Disabilities (PwD)",
        "ARTISAN": "Artisans & Traditional Craftsmen",
        "FARMER": "Farmers & Rural Producers",
        "STREET_VENDOR": "Street Vendors & Micro Retailers",
        "YOUTH": "Students & Youth",
    }

    beneficiary_items = [
        FilterOptionItem(label=beneficiary_labels[cat], value=cat, count=cnt)
        for cat, cnt in beneficiary_counts.items()
        if cnt > 0
    ]

    # 5. States / Applicability aggregation
    state_counts: Dict[str, int] = {}
    for s in schemes:
        st = s.state_restriction or "ALL_INDIA"
        st_clean = st.replace("_", " ").title()
        state_counts[st_clean] = state_counts.get(st_clean, 0) + 1

    state_items = [
        FilterOptionItem(label=st, value=st.upper().replace(" ", "_"), count=cnt)
        for st, cnt in sorted(state_counts.items(), key=lambda x: (-x[1], x[0]))
    ]

    # 6. Application Routes aggregation
    route_counts: Dict[str, int] = {}
    for s in schemes:
        rt = s.application_route or "OFFICIAL_ROUTE_UNVERIFIED"
        route_counts[rt] = route_counts.get(rt, 0) + 1

    route_labels = {
        "DIRECT_PORTAL": "Apply Online via Official Portal",
        "PARTNER_ASSISTED": "Apply via Authorized Channel Partner / Bank",
        "PHYSICAL_OFFICE": "Apply at District / Department Office",
        "OFFICIAL_ROUTE_UNVERIFIED": "Official Government Guidelines",
    }

    route_items = [
        FilterOptionItem(label=route_labels.get(rt, rt.replace("_", " ").title()), value=rt, count=cnt)
        for rt, cnt in sorted(route_counts.items(), key=lambda x: (-x[1], x[0]))
    ]

    return FilterOptionsResponse(
        ministries=ministry_items,
        sectors=sector_items,
        financial_types=financial_type_items,
        beneficiary_categories=beneficiary_items,
        states=state_items,
        application_routes=route_items,
        total_schemes=total_schemes,
    )


def _clean_str(val: Any) -> Optional[str]:
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


@router.get(
    "",
    response_model=PaginatedSchemeListResponse,
    summary="List schemes with multi-field search, multilingual synonyms, advanced filtering, and sorting",
    description="Public REST endpoint for scheme discovery. Deterministically searches and filters on the 90-scheme database."
)
def list_schemes(
    search: Optional[str] = Query(default=None, description="Case-insensitive multi-word keyword search with Hindi/English synonym expansion."),
    scheme_type: Optional[str] = Query(default=None, description="Filter by legacy scheme type"),
    financial_type: Optional[str] = Query(default=None, description="Filter by financial category: LOAN_CREDIT, GRANT_SUBSIDY, SCHOLARSHIP, TRAINING_SKILL, GUARANTEE_CREDIT_SUPPORT, DIRECT_BENEFIT, NON_FINANCIAL"),
    ministry: Optional[str] = Query(default=None, description="Filter by governing ministry"),
    implementing_agency: Optional[str] = Query(default=None, description="Filter by implementing agency"),
    sector: Optional[str] = Query(default=None, description="Filter by economic sector / vocation"),
    beneficiary_category: Optional[str] = Query(default=None, description="Filter by target group: SC, ST, OBC, WOMEN, MINORITY, PWD, ARTISAN, FARMER, STREET_VENDOR, YOUTH, ALL_CITIZENS"),
    marginalized_group: Optional[str] = Query(default=None, description="Filter by marginalized group code"),
    business_stage: Optional[str] = Query(default=None, description="Filter by business stage (e.g. NEW_BUSINESS, EXPANSION)"),
    state_restriction: Optional[str] = Query(default=None, description="Filter by state coverage (e.g. ALL_INDIA, state name)"),
    loan_available: Optional[str] = Query(default=None, description="Filter by loan availability (YES / NO)"),
    subsidy_available: Optional[str] = Query(default=None, description="Filter by subsidy availability (YES / NO)"),
    grant_available: Optional[str] = Query(default=None, description="Filter by grant availability (YES / NO)"),
    application_route: Optional[str] = Query(default=None, description="Filter by application route: DIRECT_PORTAL, PARTNER_ASSISTED"),
    scheme_status: Optional[str] = Query(default=None, description="Filter by scheme status (e.g. ACTIVE)"),
    verification_status: Optional[str] = Query(default=None, description="Filter by verification status (e.g. VERIFIED)"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: str = Query(default="scheme_id", description="Sort field: relevance, scheme_name, created_at, ministry, max_loan_amount, interest_rate_min"),
    sort_order: str = Query(default="asc", description="Sort direction: asc or desc"),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of schemes with deterministic database-level filtering,
    multilingual tokenized search, dynamic category filtering, and stable sorting.
    """
    search_clean = _clean_str(search)
    scheme_type_clean = _clean_str(scheme_type)
    financial_type_clean = _clean_str(financial_type)
    ministry_clean = _clean_str(ministry)
    implementing_agency_clean = _clean_str(implementing_agency)
    sector_clean = _clean_str(sector)
    beneficiary_category_clean = _clean_str(beneficiary_category)
    marginalized_group_clean = _clean_str(marginalized_group)
    business_stage_clean = _clean_str(business_stage)
    state_restriction_clean = _clean_str(state_restriction)
    loan_available_clean = _clean_str(loan_available)
    subsidy_available_clean = _clean_str(subsidy_available)
    grant_available_clean = _clean_str(grant_available)
    application_route_clean = _clean_str(application_route)
    scheme_status_clean = _clean_str(scheme_status)
    verification_status_clean = _clean_str(verification_status)
    
    page_num = page if isinstance(page, int) and page >= 1 else 1
    page_sz = page_size if isinstance(page_size, int) and 1 <= page_size <= 100 else 20
    sort_key = sort_by.lower() if isinstance(sort_by, str) else "scheme_id"
    sort_ord = sort_order.lower() if isinstance(sort_order, str) else "asc"

    query = db.query(Scheme).options(selectinload(Scheme.verifications))

    # Scheme status filter (Default: only ACTIVE schemes for public directory)
    if scheme_status_clean:
        st_clean = scheme_status_clean.upper()
        if st_clean == "ACTIVE":
            query = query.filter(or_(Scheme.scheme_status == "ACTIVE", Scheme.scheme_status == None, Scheme.scheme_status == ""))
        elif st_clean == "INACTIVE":
            query = query.filter(Scheme.scheme_status == "INACTIVE")
        elif st_clean != "ALL":
            query = query.filter(Scheme.scheme_status.ilike(f"%{scheme_status_clean}%"))
    else:
        query = query.filter(or_(Scheme.scheme_status == "ACTIVE", Scheme.scheme_status == None, Scheme.scheme_status == ""))

    # 1. Verification status filter
    if verification_status_clean:
        query = query.join(Scheme.verifications).filter(
            SchemeVerification.verification_status.ilike(f"%{verification_status_clean}%")
        )

    # 2. Advanced Multi-Field Tokenized Search with Multilingual Synonyms
    if search_clean:
        raw_search = search_clean.lower()
        
        # Whole phrase match clause
        phrase_like = f"%{raw_search}%"
        whole_phrase_clause = or_(
            Scheme.scheme_id.ilike(phrase_like),
            Scheme.scheme_code.ilike(phrase_like),
            Scheme.scheme_name.ilike(phrase_like),
            Scheme.short_description.ilike(phrase_like),
            Scheme.detailed_description.ilike(phrase_like),
            Scheme.purpose.ilike(phrase_like),
            Scheme.ministry.ilike(phrase_like),
            Scheme.implementing_agency.ilike(phrase_like),
            Scheme.source_organization.ilike(phrase_like),
            Scheme.sector.ilike(phrase_like),
            Scheme.activity_type.ilike(phrase_like),
            Scheme.target_beneficiary.ilike(phrase_like),
            Scheme.target_groups.ilike(phrase_like),
            Scheme.marginalized_group.ilike(phrase_like),
            Scheme.social_category.ilike(phrase_like),
            Scheme.state_restriction.ilike(phrase_like),
            Scheme.searchable_tags.ilike(phrase_like),
            Scheme.support_type.ilike(phrase_like),
            Scheme.benefit_description.ilike(phrase_like),
            Scheme.source_document.ilike(phrase_like),
            Scheme.source_title.ilike(phrase_like),
        )

        # Split search into whitespace/comma separated tokens
        tokens = [t for t in re.split(r"[\s,;]+", raw_search) if t]
        
        token_clauses = []
        for token in tokens:
            search_terms = {token}
            if token in MULTILINGUAL_SYNONYMS:
                search_terms.update(MULTILINGUAL_SYNONYMS[token])

            term_clauses = []
            for term in search_terms:
                like_expr = f"%{term}%"
                term_clauses.append(
                    or_(
                        Scheme.scheme_id.ilike(like_expr),
                        Scheme.scheme_code.ilike(like_expr),
                        Scheme.scheme_name.ilike(like_expr),
                        Scheme.short_description.ilike(like_expr),
                        Scheme.detailed_description.ilike(like_expr),
                        Scheme.purpose.ilike(like_expr),
                        Scheme.ministry.ilike(like_expr),
                        Scheme.implementing_agency.ilike(like_expr),
                        Scheme.source_organization.ilike(like_expr),
                        Scheme.sector.ilike(like_expr),
                        Scheme.activity_type.ilike(like_expr),
                        Scheme.target_beneficiary.ilike(like_expr),
                        Scheme.target_groups.ilike(like_expr),
                        Scheme.marginalized_group.ilike(like_expr),
                        Scheme.social_category.ilike(like_expr),
                        Scheme.state_restriction.ilike(like_expr),
                        Scheme.searchable_tags.ilike(like_expr),
                        Scheme.support_type.ilike(like_expr),
                        Scheme.benefit_description.ilike(like_expr),
                        Scheme.source_document.ilike(like_expr),
                        Scheme.source_title.ilike(like_expr),
                    )
                )
            token_clauses.append(or_(*term_clauses))

        # Query matches if whole phrase matches OR all individual tokens match
        if token_clauses:
            query = query.filter(or_(whole_phrase_clause, and_(*token_clauses)))
        else:
            query = query.filter(whole_phrase_clause)

    # 3. Ministry filter
    if ministry_clean:
        query = query.filter(Scheme.ministry.ilike(f"%{ministry_clean}%"))

    # 4. Implementing agency filter
    if implementing_agency_clean:
        query = query.filter(Scheme.implementing_agency.ilike(f"%{implementing_agency_clean}%"))

    # 5. Sector filter
    if sector_clean:
        sec_clean = sector_clean.replace(" ", "_")
        query = query.filter(
            or_(
                Scheme.sector.ilike(f"%{sector_clean}%"),
                Scheme.sector.ilike(f"%{sec_clean}%"),
                Scheme.activity_type.ilike(f"%{sector_clean}%"),
                Scheme.searchable_tags.ilike(f"%{sector_clean}%"),
            )
        )

    # 6. Legacy scheme_type filter
    if scheme_type_clean:
        st_clean = scheme_type_clean.replace("_", " ")
        st_tokens = [t.strip() for t in scheme_type_clean.split("_") if t.strip()]
        token_conds = [Scheme.scheme_type.ilike(f"%{t}%") for t in st_tokens]
        if token_conds:
            query = query.filter(
                or_(
                    Scheme.scheme_type.ilike(f"%{scheme_type_clean}%"),
                    Scheme.scheme_type.ilike(f"%{st_clean}%"),
                    and_(*token_conds),
                )
            )
        else:
            query = query.filter(Scheme.scheme_type.ilike(f"%{scheme_type_clean}%"))

    # 7. Beneficiary category filter
    if beneficiary_category_clean:
        b_cat = beneficiary_category_clean.upper()
        if b_cat == "SC":
            query = query.filter(
                or_(
                    Scheme.marginalized_group.ilike("%SC%"),
                    Scheme.target_groups.ilike("%SC%"),
                    Scheme.target_beneficiary.ilike("%SCHEDULED CASTE%"),
                    Scheme.scheme_name.ilike("%NSFDC%"),
                    Scheme.scheme_name.ilike("%SC%"),
                )
            )
        elif b_cat == "ST":
            query = query.filter(
                or_(
                    Scheme.marginalized_group.ilike("%ST%"),
                    Scheme.target_groups.ilike("%ST%"),
                    Scheme.target_beneficiary.ilike("%SCHEDULED TRIBE%"),
                    Scheme.scheme_name.ilike("%NSTFDC%"),
                    Scheme.scheme_name.ilike("%VAN DHAN%"),
                    Scheme.scheme_name.ilike("%ADIVASI%"),
                )
            )
        elif b_cat == "OBC":
            query = query.filter(
                or_(
                    Scheme.marginalized_group.ilike("%OBC%"),
                    Scheme.target_groups.ilike("%OBC%"),
                    Scheme.target_beneficiary.ilike("%BACKWARD%"),
                    Scheme.scheme_name.ilike("%NBCFDC%"),
                )
            )
        elif b_cat == "WOMEN":
            query = query.filter(
                or_(
                    Scheme.gender_condition.ilike("%FEMALE%"),
                    Scheme.gender_condition.ilike("%WOMEN%"),
                    Scheme.target_beneficiary.ilike("%WOMEN%"),
                    Scheme.target_beneficiary.ilike("%MAHILA%"),
                    Scheme.scheme_name.ilike("%MAHILA%"),
                    Scheme.scheme_name.ilike("%LAKHPATI%"),
                    Scheme.scheme_name.ilike("%MATRU%"),
                    Scheme.scheme_name.ilike("%STAND-UP%"),
                    Scheme.scheme_name.ilike("%SUKANYA%"),
                )
            )
        elif b_cat == "MINORITY":
            query = query.filter(
                or_(
                    Scheme.marginalized_group.ilike("%MINORITY%"),
                    Scheme.target_beneficiary.ilike("%MINORITY%"),
                    Scheme.scheme_name.ilike("%NMDFC%"),
                    Scheme.scheme_name.ilike("%VIRASAT%"),
                )
            )
        elif b_cat == "PWD":
            query = query.filter(
                or_(
                    Scheme.marginalized_group.ilike("%PWD%"),
                    Scheme.marginalized_group.ilike("%DIVYANG%"),
                    Scheme.target_beneficiary.ilike("%DISABLED%"),
                    Scheme.target_beneficiary.ilike("%DISABILITIES%"),
                    Scheme.scheme_name.ilike("%ADIP%"),
                    Scheme.scheme_name.ilike("%DDRS%"),
                    Scheme.scheme_name.ilike("%SIPDA%"),
                    Scheme.scheme_name.ilike("%NHFDC%"),
                )
            )
        elif b_cat == "ARTISAN":
            query = query.filter(
                or_(
                    Scheme.target_beneficiary.ilike("%ARTISAN%"),
                    Scheme.target_beneficiary.ilike("%CRAFTSMAN%"),
                    Scheme.target_beneficiary.ilike("%WEAVER%"),
                    Scheme.scheme_name.ilike("%VISHWAKARMA%"),
                    Scheme.scheme_name.ilike("%SHILP%"),
                    Scheme.scheme_name.ilike("%HANDICRAFT%"),
                    Scheme.scheme_name.ilike("%HANDLOOM%"),
                    Scheme.scheme_name.ilike("%COIR%"),
                )
            )
        elif b_cat == "FARMER":
            query = query.filter(
                or_(
                    Scheme.target_beneficiary.ilike("%FARMER%"),
                    Scheme.target_beneficiary.ilike("%KISAN%"),
                    Scheme.sector.ilike("%AGRICULTURE%"),
                    Scheme.scheme_name.ilike("%KISAN%"),
                    Scheme.scheme_name.ilike("%KRISHI%"),
                )
            )
        elif b_cat == "STREET_VENDOR":
            query = query.filter(
                or_(
                    Scheme.target_beneficiary.ilike("%VENDOR%"),
                    Scheme.target_beneficiary.ilike("%STREET VENDOR%"),
                    Scheme.scheme_name.ilike("%SVANIDHI%"),
                )
            )
        elif b_cat == "YOUTH":
            query = query.filter(
                or_(
                    Scheme.target_beneficiary.ilike("%STUDENT%"),
                    Scheme.target_beneficiary.ilike("%YOUTH%"),
                    Scheme.sector.ilike("%EDUCATION%"),
                    Scheme.scheme_name.ilike("%SCHOLARSHIP%"),
                    Scheme.scheme_name.ilike("%FELLOWSHIP%"),
                    Scheme.scheme_name.ilike("%CSIS%"),
                )
            )

    # 8. Marginalized group filter
    if marginalized_group_clean:
        query = query.filter(Scheme.marginalized_group.ilike(f"%{marginalized_group_clean}%"))

    # 9. Business stage filter
    if business_stage_clean:
        query = query.filter(Scheme.business_stage.ilike(f"%{business_stage_clean}%"))

    # 10. State restriction filter
    if state_restriction_clean:
        clean_state = state_restriction_clean.upper()
        if clean_state == "ALL_INDIA":
            query = query.filter(
                or_(
                    Scheme.state_restriction.ilike("%ALL_INDIA%"),
                    Scheme.state_restriction.is_(None),
                    Scheme.state_restriction == "",
                )
            )
        else:
            query = query.filter(
                or_(
                    Scheme.state_restriction.ilike(f"%{clean_state}%"),
                    Scheme.state_restriction.ilike("%ALL_INDIA%"),
                    Scheme.state_coverage.ilike(f"%{clean_state}%"),
                )
            )

    # 11. Application route filter
    if application_route_clean:
        query = query.filter(Scheme.application_route == application_route_clean)

    # 12. Scheme status filter
    if scheme_status_clean:
        query = query.filter(Scheme.scheme_status.ilike(f"%{scheme_status_clean}%"))

    # 13. Loan Available filter
    if loan_available_clean:
        la = loan_available_clean.upper()
        if la in ["YES", "TRUE", "1"]:
            query = query.filter(
                or_(
                    Scheme.loan_available.in_(["TRUE", "YES", "1"]),
                    Scheme.max_loan_amount.isnot(None),
                    Scheme.interest_rate_max.isnot(None),
                )
            )
        elif la in ["NO", "FALSE", "0"]:
            query = query.filter(
                and_(
                    or_(
                        Scheme.loan_available.in_(["FALSE", "NO", "0"]),
                        Scheme.loan_available.is_(None),
                    ),
                    Scheme.max_loan_amount.is_(None),
                )
            )

    # 14. Subsidy Available filter
    if subsidy_available_clean:
        sa = subsidy_available_clean.upper()
        if sa in ["YES", "TRUE", "1"]:
            query = query.filter(
                or_(
                    Scheme.subsidy_available.in_(["TRUE", "YES", "1"]),
                    Scheme.subsidy_percentage.isnot(None),
                    Scheme.subsidy_details.isnot(None),
                )
            )
        elif sa in ["NO", "FALSE", "0"]:
            query = query.filter(
                or_(
                    Scheme.subsidy_available.in_(["FALSE", "NO", "0"]),
                    Scheme.subsidy_available.is_(None),
                ),
                Scheme.subsidy_percentage.is_(None),
            )

    # 15. Grant Available filter
    if grant_available_clean:
        ga = grant_available_clean.upper()
        if ga in ["YES", "TRUE", "1"]:
            query = query.filter(
                or_(
                    Scheme.grant_available.in_(["TRUE", "YES", "1"]),
                    Scheme.grant_amount.isnot(None),
                )
            )

    # Fetch intermediate list for python-level financial_type filtering if specified
    all_matched = query.all()

    if financial_type_clean:
        target_fin = financial_type_clean.upper()
        filtered_items = [s for s in all_matched if s.financial_category == target_fin]
    else:
        filtered_items = all_matched

    total = len(filtered_items)

    # 16. Sorting
    is_desc = sort_ord == "desc"

    if sort_key == "relevance" and search_clean:
        # Relevance score: exact name match > name contains > description contains
        s_term = search_clean.lower()
        def relevance_key(s: Scheme) -> tuple:
            name_lower = (s.scheme_name or "").lower()
            if name_lower == s_term:
                rank = 0
            elif name_lower.startswith(s_term):
                rank = 1
            elif s_term in name_lower:
                rank = 2
            elif s_term in (s.searchable_tags or "").lower():
                rank = 3
            else:
                rank = 4
            return (rank, s.scheme_id)

        filtered_items.sort(key=relevance_key, reverse=is_desc)
    elif sort_key == "scheme_name":
        filtered_items.sort(key=lambda s: (s.scheme_name or "").lower(), reverse=is_desc)
    elif sort_key == "created_at":
        filtered_items.sort(key=lambda s: s.created_at, reverse=is_desc)
    elif sort_key == "ministry":
        filtered_items.sort(key=lambda s: (s.ministry or "").lower(), reverse=is_desc)
    elif sort_key == "max_loan_amount":
        filtered_items.sort(key=lambda s: float(s.max_loan_amount or 0), reverse=is_desc)
    elif sort_key in ["interest_rate", "interest_rate_min", "interest_rate_max"]:
        filtered_items.sort(key=lambda s: float(s.interest_rate or 999.0), reverse=is_desc)
    else:
        # Default stable sort by scheme_id
        filtered_items.sort(key=lambda s: s.scheme_id, reverse=is_desc)

    # 17. Pagination
    pages = math.ceil(total / page_sz) if total > 0 else 0
    offset = (page_num - 1) * page_sz
    paged_items = filtered_items[offset : offset + page_sz]

    return PaginatedSchemeListResponse(
        items=paged_items,
        total=total,
        page=page_num,
        page_size=page_sz,
        pages=pages,
    )


@router.get(
    "/compare",
    response_model=SchemeComparisonResponse,
    summary="Compare 2 to 4 schemes side-by-side with optional personalized eligibility",
    description="Fetches full scheme details for up to 4 schemes in a single query. Computes personalized eligibility if beneficiary is authenticated."
)
def compare_schemes(
    ids: str = Query(..., description="Comma-separated scheme IDs (between 2 and 4 schemes, e.g. 'SIH26092-001,SIH26092-053')"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Side-by-side comparison endpoint for 2 to 4 schemes.
    Deduplicates requested IDs while preserving requested order.
    Rejects requests with > 4 scheme IDs.
    Calculates deterministic personalized eligibility for logged-in citizens.
    """
    if not ids or not ids.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least 1 scheme ID to compare."
        )

    # Parse and deduplicate requested IDs while preserving order
    raw_parts = [p.strip() for p in ids.split(",") if p.strip()]
    dedup_ids: List[str] = []
    for pid in raw_parts:
        if pid not in dedup_ids:
            dedup_ids.append(pid)

    if len(dedup_ids) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can compare a maximum of 4 schemes at a time."
        )

    if len(dedup_ids) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide valid scheme IDs to compare."
        )

    # Single eager-loaded DB query to prevent N+1 query overhead
    schemes_db = db.query(Scheme).options(
        selectinload(Scheme.verifications),
        selectinload(Scheme.rules),
        selectinload(Scheme.documents),
        selectinload(Scheme.partner_mappings),
    ).filter(
        Scheme.scheme_id.in_(dedup_ids)
    ).all()

    scheme_map = {s.scheme_id: s for s in schemes_db}
    invalid_ids = [sid for sid in dedup_ids if sid not in scheme_map]

    # Load citizen profile if user is logged in and has profile_data
    user_profile: Optional[BeneficiaryProfileInput] = None
    if current_user and current_user.profile_data:
        try:
            data = json.loads(current_user.profile_data)
            user_profile = BeneficiaryProfileInput(**data)
        except Exception:
            user_profile = None

    compared_items: List[SchemeComparisonItem] = []
    for sid in dedup_ids:
        if sid in scheme_map:
            sch = scheme_map[sid]
            detail_res = SchemeDetailResponse.model_validate(sch)

            elig_res: Optional[SchemePersonalizedEligibility] = None
            if user_profile:
                eval_res = DeterministicEligibilityEngine.evaluate_scheme(sch, user_profile)
                if eval_res.status.value == "ELIGIBLE":
                    reasons = eval_res.matched_rules if eval_res.matched_rules else eval_res.explanations
                    elig_res = SchemePersonalizedEligibility(
                        status="ELIGIBLE",
                        reasons=reasons,
                        missing_fields=[]
                    )
                elif eval_res.status.value == "INSUFFICIENT_INFORMATION":
                    reasons = eval_res.missing_information if eval_res.missing_information else eval_res.explanations
                    elig_res = SchemePersonalizedEligibility(
                        status="INSUFFICIENT_INFORMATION",
                        reasons=reasons,
                        missing_fields=eval_res.missing_information
                    )
                else:
                    reasons = eval_res.failed_rules if eval_res.failed_rules else eval_res.explanations
                    elig_res = SchemePersonalizedEligibility(
                        status="INELIGIBLE",
                        reasons=reasons,
                        missing_fields=[]
                    )

            compared_items.append(SchemeComparisonItem(
                scheme=detail_res,
                personalized_eligibility=elig_res
            ))

    return SchemeComparisonResponse(
        compared_schemes=compared_items,
        invalid_ids=invalid_ids
    )


@router.get(
    "/{scheme_id}",
    response_model=SchemeDetailResponse,
    summary="Get complete scheme detail by scheme_id",
    description="Returns full detailed representation of a scheme including applicable rules, documents, and verification metadata."
)
def get_scheme_detail(
    scheme_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns complete scheme details for a valid scheme_id.
    Eagerly loads related rules, documents, and verifications to prevent N+1 queries.
    Raises HTTP 404 if the scheme_id does not exist.
    """
    scheme = db.query(Scheme).options(
        selectinload(Scheme.verifications),
        selectinload(Scheme.rules),
        selectinload(Scheme.documents),
        selectinload(Scheme.partner_mappings),
    ).filter(
        Scheme.scheme_id == scheme_id
    ).first()

    if not scheme or scheme.scheme_status == "INACTIVE":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with ID '{scheme_id}' was not found or is currently inactive.",
        )

    return scheme
