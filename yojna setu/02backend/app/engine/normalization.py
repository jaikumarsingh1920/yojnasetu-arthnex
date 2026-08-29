"""
YojnaSetu Scheme Normalized Profile Builder.
Generates rich normalized matching metadata for all 56 schemes without altering
authoritative official policy facts or inventing government legal/financial data.
"""

from typing import List, Dict, Set, Optional, Any
from pydantic import BaseModel, Field
from app.models.scheme import Scheme
from app.engine.taxonomy import (
    SECTORS,
    ACTIVITY_ALIASES,
    OCCUPATION_MAP,
    APPLICANT_TYPE_MAP,
    TARGET_GROUP_MAP,
    GEOGRAPHY_MAP,
    BUSINESS_STAGE_MAP,
    SUPPORT_TYPE_MAP,
    TaxonomyMatcher,
)


class SchemeNormalizedProfile(BaseModel):
    scheme_id: str
    scheme_name: str
    normalized_sectors: List[str] = Field(default_factory=list)
    normalized_activities: List[str] = Field(default_factory=list)
    normalized_activity_aliases: List[str] = Field(default_factory=list)
    normalized_applicant_types: List[str] = Field(default_factory=list)
    normalized_target_groups: List[str] = Field(default_factory=list)
    normalized_business_stages: List[str] = Field(default_factory=list)
    normalized_geographies: List[str] = Field(default_factory=list)
    normalized_support_types: List[str] = Field(default_factory=list)
    normalized_keywords: List[str] = Field(default_factory=list)
    semantic_tags: List[str] = Field(default_factory=list)
    related_industries: List[str] = Field(default_factory=list)
    related_occupations: List[str] = Field(default_factory=list)
    related_business_types: List[str] = Field(default_factory=list)
    related_use_cases: List[str] = Field(default_factory=list)
    financial_requirement_category: Optional[str] = None


class SchemeNormalizedProfileBuilder:
    """
    Analyzes existing authoritative scheme attributes, rules, documents, and text fields
    to derive a rich, semantically normalized matching profile for soft-fit recommendation scoring.
    """

    @classmethod
    def build_profile(cls, scheme: Scheme) -> SchemeNormalizedProfile:
        text_corpus = " ".join(filter(None, [
            scheme.scheme_name,
            scheme.purpose,
            scheme.short_description,
            scheme.detailed_description,
            scheme.target_beneficiary,
            scheme.target_groups,
            scheme.sector,
            scheme.activity_type,
            scheme.ministry,
            scheme.implementing_agency,
            scheme.support_type,
            scheme.benefit_description,
        ])).lower()

        # 1. Normalized Sectors
        sectors: Set[str] = set()
        if scheme.sector and scheme.sector.strip().upper() not in ["UNKNOWN", "NONE", "NULL", ""]:
            sectors.add(TaxonomyMatcher.normalize_string(scheme.sector))
        
        # Derive sectors from text
        if "micro finance" in text_corpus or "mfs" in text_corpus or "small loan" in text_corpus:
            sectors.update(["MICRO_FINANCE", "MICRO_ENTERPRISE", "MSME", "SMALL_BUSINESS", "SELF_EMPLOYMENT"])
        if "term loan" in text_corpus or "equipment loan" in text_corpus or "capital loan" in text_corpus:
            sectors.update(["TERM_LOAN", "MSME", "MANUFACTURING", "SERVICES", "TRADING"])
        if "education" in text_corpus or "els" in text_corpus or "study" in text_corpus or "college" in text_corpus:
            sectors.update(["EDUCATION", "SKILL_DEVELOPMENT", "HIGHER_EDUCATION"])
        if "udyam nidhi" in text_corpus or "uny" in text_corpus or "entrepreneur" in text_corpus:
            sectors.update(["ENTREPRENEURSHIP", "MSME", "MICRO_ENTERPRISE", "SELF_EMPLOYMENT"])
        if "pmegp" in text_corpus or "prime minister" in text_corpus:
            sectors.update(["MANUFACTURING", "SERVICES", "MICRO_ENTERPRISE", "MSME", "SELF_EMPLOYMENT"])
        if "tailor" in text_corpus or "stitching" in text_corpus or "sewing" in text_corpus or "garment" in text_corpus:
            sectors.update(["TEXTILES", "TAILORING", "GARMENTS", "HANDICRAFTS", "SELF_EMPLOYMENT"])
        if "dairy" in text_corpus or "milk" in text_corpus or "cattle" in text_corpus:
            sectors.update(["DAIRY", "ANIMAL_HUSBANDRY", "AGRICULTURE", "ALLIED_AGRICULTURE"])
        if "fish" in text_corpus or "aqua" in text_corpus:
            sectors.update(["FISHERIES", "AQUACULTURE", "ALLIED_AGRICULTURE"])
        if "artisan" in text_corpus or "craft" in text_corpus or "vishwakarma" in text_corpus:
            sectors.update(["ARTISAN_ACTIVITY", "HANDICRAFTS", "TRADITIONAL_TRADE", "MICRO_ENTERPRISE"])

        if not sectors:
            sectors.add("MICRO_ENTERPRISE")

        # 2. Normalized Activities & Aliases
        activities: Set[str] = set()
        aliases: Set[str] = set()

        if scheme.activity_type and scheme.activity_type.strip().upper() not in ["UNKNOWN", "NONE", "NULL", ""]:
            activities.add(TaxonomyMatcher.normalize_string(scheme.activity_type))

        for sec in sectors:
            if sec in ACTIVITY_ALIASES:
                aliases.update(ACTIVITY_ALIASES[sec])
            if sec in SECTORS:
                activities.update(SECTORS[sec])

        # Add explicit keyword aliases
        if "TAILORING" in sectors or "TEXTILES" in sectors:
            activities.update(["STITCHING", "SEWING", "GARMENT_MAKING", "BOUTIQUE"])
            aliases.update(ACTIVITY_ALIASES["TAILORING"])
        if "DAIRY" in sectors:
            activities.update(["MILK_PRODUCTION", "CATTLE_REARING", "MILK_PROCESSING"])
            aliases.update(ACTIVITY_ALIASES["DAIRY"])
        if "ARTISAN_ACTIVITY" in sectors:
            activities.update(["HANDICRAFT", "TRADITIONAL_CRAFT", "POTTERY", "CARPENTRY", "BLACKSMITHY"])
            aliases.update(ACTIVITY_ALIASES["ARTISAN"])

        # 3. Normalized Applicant Types
        applicant_types: Set[str] = set()
        if scheme.applicant_types and scheme.applicant_types.strip().upper() not in ["UNKNOWN", "NONE", "NULL", ""]:
            applicant_types.add(TaxonomyMatcher.normalize_string(scheme.applicant_types))
        
        applicant_types.update(["INDIVIDUAL", "ENTREPRENEUR", "SELF_EMPLOYED", "MICRO_ENTERPRISE"])
        if "artisan" in text_corpus or "craft" in text_corpus:
            applicant_types.add("ARTISAN")
        if "farmer" in text_corpus or "agriculture" in text_corpus:
            applicant_types.add("FARMER")
        if "student" in text_corpus or "education" in text_corpus:
            applicant_types.add("STUDENT")
        if "shg" in text_corpus or "self help" in text_corpus:
            applicant_types.add("SHG")

        # 4. Normalized Target Groups
        target_groups: Set[str] = set()
        if scheme.target_groups and scheme.target_groups.strip().upper() not in ["UNKNOWN", "NONE", "NULL", ""]:
            target_groups.add(TaxonomyMatcher.normalize_string(scheme.target_groups))
        if scheme.target_beneficiary and scheme.target_beneficiary.strip().upper() not in ["UNKNOWN", "NONE", "NULL", ""]:
            target_groups.add(TaxonomyMatcher.normalize_string(scheme.target_beneficiary))

        if "sc" in text_corpus or "scheduled caste" in text_corpus or scheme.sc_required == "TRUE":
            target_groups.update(["SC", "SCHEDULED_CASTE"])
        if "st" in text_corpus or "scheduled tribe" in text_corpus:
            target_groups.update(["ST", "SCHEDULED_TRIBE"])
        if "obc" in text_corpus or "backward class" in text_corpus:
            target_groups.update(["OBC", "BACKWARD_CLASS"])
        if "women" in text_corpus or "female" in text_corpus:
            target_groups.update(["WOMEN", "FEMALE_BENEFICIARY"])
        if "minority" in text_corpus:
            target_groups.add("MINORITY")

        if not target_groups:
            target_groups.add("GENERAL_BENEFICIARY")

        # 5. Business Stages
        stages: Set[str] = set()
        if scheme.business_stage and scheme.business_stage.strip().upper() not in ["UNKNOWN", "NONE", "NULL", ""]:
            stages.add(TaxonomyMatcher.normalize_string(scheme.business_stage))
        
        if "new" in text_corpus or "greenfield" in text_corpus or "setting up" in text_corpus:
            stages.update(["NEW", "STARTUP", "NEW_UNIT", "SELF_EMPLOYMENT"])
        if "existing" in text_corpus or "expansion" in text_corpus or "modernization" in text_corpus:
            stages.update(["EXISTING", "EXPANSION", "MODERNIZATION"])
        
        if not stages:
            stages.update(["NEW", "EXISTING", "ANY_STAGE"])

        # 6. Geographies
        geographies: Set[str] = set()
        if scheme.state_coverage:
            geographies.add(TaxonomyMatcher.normalize_geography(scheme.state_coverage))
        if scheme.state_restriction:
            geographies.add(TaxonomyMatcher.normalize_geography(scheme.state_restriction))
        
        if not geographies or "UNKNOWN_GEOGRAPHY" in geographies:
            geographies.clear()
            geographies.add("ALL_INDIA")

        # 7. Support Types
        support_types: Set[str] = set()
        if scheme.support_type and scheme.support_type.strip().upper() not in ["UNKNOWN", "NONE", "NULL", ""]:
            support_types.add(TaxonomyMatcher.normalize_string(scheme.support_type))
        
        if "loan" in text_corpus or "credit" in text_corpus:
            support_types.update(["CREDIT", "TERM_LOAN", "MICROFINANCE"])
        if "subsidy" in text_corpus or "margin money" in text_corpus:
            support_types.update(["SUBSIDY", "MARGIN_MONEY"])
        if "education" in text_corpus or "els" in text_corpus:
            support_types.add("EDUCATIONAL_LOAN")

        # 8. Keywords & Tags
        keywords: Set[str] = set()
        tags: Set[str] = set()
        for sec in sectors:
            keywords.add(sec.lower().replace('_', ' '))
            tags.add(sec.lower().replace('_', '-'))
        for act in activities:
            keywords.add(act.lower().replace('_', ' '))
            tags.add(act.lower().replace('_', '-'))
        for tg in target_groups:
            keywords.add(tg.lower().replace('_', ' '))
            tags.add(tg.lower().replace('_', '-'))

        # Add core general tags
        tags.update(["government-scheme", "welfare", "financial-assistance", "empowerment"])

        # 9. Related Occupations & Industries
        related_occupations: Set[str] = set()
        related_industries: Set[str] = set()
        related_business_types: Set[str] = set()
        related_use_cases: Set[str] = set()

        if "TEXTILES" in sectors or "TAILORING" in sectors:
            related_occupations.update(["TAILOR", "SEWING_WORKER", "BOUTIQUE_OWNER"])
            related_industries.update(["TEXTILE_INDUSTRY", "GARMENT_INDUSTRY", "FASHION"])
            related_business_types.update(["tailoring shop", "garment stitching unit", "boutique", "apparel manufacturing"])
            related_use_cases.update(["purchase of sewing machines", "cloth inventory", "shop setup", "working capital"])

        if "DAIRY" in sectors or "ANIMAL_HUSBANDRY" in sectors:
            related_occupations.update(["DAIRY_FARMER", "LIVESTOCK_KEEPER", "MILK_VENDOR"])
            related_industries.update(["DAIRY_INDUSTRY", "ANIMAL_HUSBANDRY", "AGRICULTURE"])
            related_business_types.update(["dairy farm", "milk collection center", "cattle breeding unit"])
            related_use_cases.update(["purchase of milch cattle", "shed construction", "chaff cutter", "feed purchase"])

        if "MICRO_ENTERPRISE" in sectors or "MICRO_FINANCE" in sectors:
            related_occupations.update(["SMALL_SHOPKEEPER", "STREET_VENDOR", "MICRO_ENTREPRENEUR", "SELF_EMPLOYED"])
            related_industries.update(["RETAIL", "SERVICES", "MICRO_BUSINESS"])
            related_business_types.update(["kirana store", "repair shop", "tea stall", "micro trading unit"])
            related_use_cases.update(["working capital loan", "tools purchase", "small business expansion"])

        # 10. Non-Numeric Financial Requirement Category
        fin_cat: Optional[str] = None
        max_loan = scheme.max_loan_amount or scheme.maximum_loan_amount if hasattr(scheme, 'maximum_loan_amount') else scheme.max_loan_amount
        if max_loan:
            if max_loan <= 100000:
                fin_cat = "LOW_LOAN_REQUIREMENT"
            elif max_loan <= 1000000:
                fin_cat = "MEDIUM_LOAN_REQUIREMENT"
            else:
                fin_cat = "HIGH_LOAN_REQUIREMENT"

        return SchemeNormalizedProfile(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.scheme_name,
            normalized_sectors=sorted(list(sectors)),
            normalized_activities=sorted(list(activities)),
            normalized_activity_aliases=sorted(list(aliases)),
            normalized_applicant_types=sorted(list(applicant_types)),
            normalized_target_groups=sorted(list(target_groups)),
            normalized_business_stages=sorted(list(stages)),
            normalized_geographies=sorted(list(geographies)),
            normalized_support_types=sorted(list(support_types)),
            normalized_keywords=sorted(list(keywords)),
            semantic_tags=sorted(list(tags)),
            related_industries=sorted(list(related_industries)),
            related_occupations=sorted(list(related_occupations)),
            related_business_types=sorted(list(related_business_types)),
            related_use_cases=sorted(list(related_use_cases)),
            financial_requirement_category=fin_cat,
        )
