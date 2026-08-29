"""
YojnaSetu Normalized Taxonomy & Multi-Level Semantic Matcher.
Provides reusable taxonomies, synonyms, occupations, applicant types, target groups,
geographies, business stages, support types, and 5-level matching hierarchy.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
import re


# ── 1. SECTOR TAXONOMY & PARENT-CHILD RELATIONSHIPS ──
SECTORS: Dict[str, List[str]] = {
    "AGRICULTURE": ["FARMING", "CROPS", "AGRO_BUSINESS", "ORGANIC_FARMING", "HORTICULTURE"],
    "ALLIED_AGRICULTURE": ["ANIMAL_HUSBANDRY", "DAIRY", "FISHERIES", "POULTRY", "BEE_KEEPING", "SERICULTURE"],
    "ANIMAL_HUSBANDRY": ["DAIRY", "POULTRY", "LIVESTOCK", "GOATRY", "SHEEP_FARMING", "PIGGERY"],
    "DAIRY": ["MILK_PRODUCTION", "DAIRY_FARMING", "MILK_PROCESSING", "DAIRY_PRODUCTS"],
    "FISHERIES": ["AQUACULTURE", "FISH_FARMING", "INLAND_FISHERIES", "MARINE_FISHERIES"],
    "FORESTRY": ["AGRO_FORESTRY", "NON_TIMBER_FOREST_PRODUCE", "SOCIAL_FORESTRY"],
    "FOOD_PROCESSING": ["AGRO_PROCESSING", "FOOD_MANUFACTURING", "PACKAGED_FOOD", "FRUIT_PROCESSING"],
    "MANUFACTURING": ["MICRO_MANUFACTURING", "SMALL_MANUFACTURING", "TEXTILE_MANUFACTURING", "WOOD_MANUFACTURING", "METAL_FABRICATION"],
    "MSME": ["MICRO_ENTERPRISE", "SMALL_ENTERPRISE", "MEDIUM_ENTERPRISE", "SMALL_BUSINESS"],
    "MICRO_ENTERPRISE": ["SELF_EMPLOYMENT_BUSINESS", "TINY_UNIT", "VILLAGE_INDUSTRY", "COTTAGE_INDUSTRY"],
    "SMALL_BUSINESS": ["RETAIL_SHOP", "SERVICE_CENTER", "LOCAL_STORE", "MICRO_ENTERPRISE"],
    "SERVICES": ["PROFESSIONAL_SERVICES", "REPAIR_SERVICES", "PERSONAL_SERVICES", "DIGITAL_SERVICES", "IT_SERVICES"],
    "TRADING": ["RETAIL_TRADING", "WHOLESALE_TRADING", "SHOPKEEPING", "COMMERCIAL_TRADE"],
    "RETAIL": ["RETAIL_SHOP", "STREET_VENDING", "GROCERY", "CLOTH_STORE"],
    "TRANSPORT": ["PASSENGER_TRANSPORT", "GOODS_TRANSPORT", "LOGISTICS", "AUTO_RICKSHAW", "COMMERCIAL_VEHICLE"],
    "LOGISTICS": ["WAREHOUSING", "COLD_STORAGE", "SUPPLY_CHAIN", "FREIGHT"],
    "TEXTILES": ["TAILORING", "GARMENTS", "APPAREL", "WEAVING", "SPINNING", "FABRIC"],
    "TAILORING": ["STITCHING", "SEWING", "GARMENT_STITCHING", "DRESS_MAKING", "CLOTHING"],
    "GARMENTS": ["READYMADE_GARMENTS", "CLOTHING_MANUFACTURING", "APPAREL_MAKING"],
    "HANDLOOMS": ["WEAVING", "HANDLOOM_WEAVING", "TRADITIONAL_TEXTILES"],
    "HANDICRAFTS": ["ARTISAN_ACTIVITY", "CRAFT_WORK", "HANDMADE_PRODUCTS", "WOOD_CRAFT", "POTTERY"],
    "ARTISAN_ACTIVITY": ["TRADITIONAL_TRADE", "HANDICRAFT", "BLACKSMITHY", "CARPENTRY", "GOLDSMITHY", "COBBLER"],
    "TRADITIONAL_TRADE": ["ARTISAN", "VILLAGE_CRAFT", "HEREDITARY_TRADE"],
    "EDUCATION": ["HIGHER_EDUCATION", "TECHNICAL_EDUCATION", "PROFESSIONAL_EDUCATION", "SKILL_TRAINING"],
    "SKILL_DEVELOPMENT": ["VOCATIONAL_TRAINING", "SKILL_UPGRADATION", "CAPACITY_BUILDING"],
    "HOUSING": ["RURAL_HOUSING", "URBAN_HOUSING", "HOUSE_CONSTRUCTION"],
    "SELF_EMPLOYMENT": ["MICRO_ENTERPRISE", "OWN_BUSINESS", "ENTREPRENEURSHIP", "INDEPENDENT_WORK"],
    "ENTREPRENEURSHIP": ["STARTUP", "BUSINESS_INCUBATION", "NEW_ENTERPRISE"],
    "DIGITAL_SERVICES": ["COMMON_SERVICE_CENTER", "IT_ENABLEMENT", "DIGITAL_KIOSK"],
    "PROFESSIONAL_SERVICES": ["CONSULTANCY", "REPAIR", "BEAUTY_PARLOR", "SALON"],
}


# ── 2. ACTIVITY SYNONYMS & ALIASES ──
ACTIVITY_ALIASES: Dict[str, Set[str]] = {
    "TAILORING": {
        "tailoring", "stitching", "sewing", "dress making", "garment stitching",
        "apparel making", "clothing work", "textile stitching", "boutique", "fashion designing"
    },
    "DAIRY": {
        "dairy", "dairy farming", "milk production", "milk business", "milk processing",
        "cattle dairy", "livestock dairy", "cow farming", "buffalo farming", "milch cattle"
    },
    "POULTRY": {
        "poultry", "poultry farming", "chicken farming", "egg production",
        "broiler farming", "layer farming", "hatchery", "poultry unit"
    },
    "FISHERIES": {
        "fishery", "fisheries", "fish farming", "aquaculture", "fish cultivation",
        "inland fisheries", "marine fisheries", "prawn farming", "fish hatcheries"
    },
    "FOOD_PROCESSING": {
        "food processing", "food manufacturing", "agro processing", "food preparation",
        "packaged food", "food products", "flour mill", "rice mill", "oil extraction", "bakery"
    },
    "HANDICRAFT": {
        "handicraft", "handicrafts", "craft work", "traditional craft", "artisan craft",
        "handmade products", "pottery", "embroidery", "carpet weaving", "bamboo craft"
    },
    "CARPENTRY": {
        "carpentry", "wood work", "woodworking", "furniture making", "wood craft",
        "timber work", "wooden articles"
    },
    "MICRO_ENTERPRISE": {
        "micro enterprise", "micro business", "small business", "small unit",
        "small enterprise", "self employment business", "tiny unit", "micro unit"
    },
    "ARTISAN": {
        "artisan", "craftsperson", "craft worker", "traditional artisan",
        "skilled craft worker", "vishwakarma", "artisan worker"
    },
    "TRANSPORT": {
        "transport", "transport business", "auto rickshaw", "e-rickshaw",
        "goods vehicle", "commercial vehicle", "taxi business", "driver self employment"
    },
    "RETAIL": {
        "retail", "retail shop", "grocery store", "kirana shop", "general store",
        "vendor", "street vending", "cloth shop"
    },
    "EDUCATION": {
        "education", "higher education", "college education", "technical education",
        "engineering education", "medical education", "professional course", "studies"
    },
    "AGRICULTURE": {
        "agriculture", "farming", "crop cultivation", "farmer activity",
        "agricultural production", "horticulture", "organic farming"
    },
    "ANIMAL_HUSBANDRY": {
        "animal husbandry", "livestock rearing", "cattle rearing", "goat farming",
        "sheep farming", "piggery", "animal breeding"
    },
}


# ── 3. OCCUPATION SEMANTIC MAP ──
OCCUPATION_MAP: Dict[str, List[str]] = {
    "TAILOR": ["TAILORING", "TEXTILES", "GARMENTS", "APPAREL", "SELF_EMPLOYMENT"],
    "SEWING_WORKER": ["TAILORING", "TEXTILES", "GARMENTS", "SELF_EMPLOYMENT"],
    "DAIRY_FARMER": ["DAIRY", "ANIMAL_HUSBANDRY", "LIVESTOCK", "AGRICULTURE", "ALLIED_AGRICULTURE"],
    "MILK_MAN": ["DAIRY", "ANIMAL_HUSBANDRY", "RETAIL"],
    "FISH_FARMER": ["FISHERIES", "AQUACULTURE", "ALLIED_AGRICULTURE"],
    "FISHERMAN": ["FISHERIES", "AQUACULTURE", "ALLIED_AGRICULTURE"],
    "CARPENTER": ["CARPENTRY", "WOODWORK", "FURNITURE", "HANDICRAFT", "ARTISAN_ACTIVITY"],
    "ARTISAN": ["ARTISAN_ACTIVITY", "TRADITIONAL_TRADE", "HANDICRAFT", "MICRO_ENTERPRISE"],
    "BLACKSMITH": ["ARTISAN_ACTIVITY", "TRADITIONAL_TRADE", "METAL_FABRICATION"],
    "POTTER": ["ARTISAN_ACTIVITY", "HANDICRAFT", "TRADITIONAL_TRADE"],
    "WEAVER": ["HANDLOOMS", "TEXTILES", "ARTISAN_ACTIVITY", "TRADITIONAL_TRADE"],
    "FARMER": ["AGRICULTURE", "ALLIED_AGRICULTURE", "SELF_EMPLOYMENT"],
    "STREET_VENDOR": ["RETAIL", "STREET_VENDING", "MICRO_ENTERPRISE", "SELF_EMPLOYMENT"],
    "SHOPKEEPER": ["RETAIL", "TRADING", "SMALL_BUSINESS", "MICRO_ENTERPRISE"],
    "STUDENT": ["EDUCATION", "SKILL_DEVELOPMENT", "HIGHER_EDUCATION"],
    "DRIVER": ["TRANSPORT", "LOGISTICS", "SELF_EMPLOYMENT"],
    "MECHANIC": ["SERVICES", "REPAIR_SERVICES", "MICRO_ENTERPRISE"],
    "BEAUTICIAN": ["SERVICES", "PROFESSIONAL_SERVICES", "MICRO_ENTERPRISE", "SELF_EMPLOYMENT"],
}


# ── 4. APPLICANT TYPE NORMALIZATION ──
APPLICANT_TYPE_MAP: Dict[str, Set[str]] = {
    "INDIVIDUAL": {"INDIVIDUAL", "SINGLE_PERSON", "PERSON", "CITIZEN", "BENEFICIARY"},
    "ENTREPRENEUR": {"ENTREPRENEUR", "FIRST_GENERATION_ENTREPRENEUR", "PROPRIETOR", "BUSINESS_OWNER"},
    "SELF_EMPLOYED": {"SELF_EMPLOYED", "SELF_EMPLOYMENT", "OWN_ACCOUNT_WORKER"},
    "MICRO_ENTERPRISE": {"MICRO_ENTERPRISE", "MICRO_BUSINESS", "TINY_UNIT", "SMALL_BUSINESS"},
    "ARTISAN": {"ARTISAN", "CRAFTSPERSON", "TRADITIONAL_WORKER"},
    "FARMER": {"FARMER", "AGRICULTURIST", "CULTIVATOR"},
    "STUDENT": {"STUDENT", "SCHOLAR", "TRAINEE"},
    "SHG": {"SHG", "SELF_HELP_GROUP", "WOMEN_SHG"},
    "COOPERATIVE": {"COOPERATIVE", "COOPERATIVE_SOCIETY", "FPO", "FARMER_PRODUCER_ORGANIZATION"},
    "ORGANIZATION": {"ORGANIZATION", "SOCIETY", "TRUST", "NGO", "FIRM", "COMPANY"},
    "STARTUP": {"STARTUP", "NEW_ENTERPRISE", "INNOVATIVE_BUSINESS"},
    "BUSINESS_OWNER": {"BUSINESS_OWNER", "PROPRIETOR", "PROMOTER"},
}


# ── 5. TARGET GROUP NORMALIZATION ──
TARGET_GROUP_MAP: Dict[str, Set[str]] = {
    "SC": {"SC", "SCHEDULED_CASTE", "SCHEDULED_CASTES", "DALIT"},
    "ST": {"ST", "SCHEDULED_TRIBE", "SCHEDULED_TRIBES", "ADIVASI", "TRIBAL"},
    "OBC": {"OBC", "OTHER_BACKWARD_CLASS", "OTHER_BACKWARD_CLASSES", "BACKWARD_CLASS"},
    "WOMEN": {"WOMEN", "WOMAN", "FEMALE", "FEMALE_BENEFICIARY", "GIRL"},
    "MINORITY": {"MINORITY", "MINORITIES", "MUSLIM", "CHRISTIAN", "SIKH", "BUDDHIST", "JAIN", "PARSI"},
    "PWD": {"PWD", "DIVYANG", "PERSONS_WITH_DISABILITIES", "HANDICAPPED"},
    "STUDENT": {"STUDENT", "YOUTH", "SCHOLAR"},
    "YOUTH": {"YOUTH", "YOUNG_PERSON", "YOUNG_ENTREPRENEUR"},
    "ARTISAN": {"ARTISAN", "VISHWAKARMA", "CRAFTSPERSON"},
    "FARMER": {"FARMER", "AGRICULTURIST", "SMALL_MARGINAL_FARMER"},
    "SELF_EMPLOYED": {"SELF_EMPLOYED", "MICRO_ENTREPRENEUR", "STREET_VENDOR"},
    "GENERAL_BENEFICIARY": {"GENERAL_BENEFICIARY", "ALL_ELIGIBLE", "ANY_CITIZEN", "OPEN_CATEGORY", "GENERAL"},
}


# ── 6. GEOGRAPHY NORMALIZATION ──
GEOGRAPHY_MAP: Dict[str, str] = {
    "UP": "UTTAR_PRADESH",
    "U.P.": "UTTAR_PRADESH",
    "UTTAR PRADESH": "UTTAR_PRADESH",
    "UTTARPRADESH": "UTTAR_PRADESH",
    "DELHI": "DELHI",
    "NCT DELHI": "DELHI",
    "NCT OF DELHI": "DELHI",
    "NATIONAL CAPITAL TERRITORY OF DELHI": "DELHI",
    "MH": "MAHARASHTRA",
    "MAHARASHTRA": "MAHARASHTRA",
    "MP": "MADHYA_PRADESH",
    "MADHYA PRADESH": "MADHYA_PRADESH",
    "TN": "TAMIL_NADU",
    "TAMIL NADU": "TAMIL_NADU",
    "KA": "KARNATAKA",
    "KARNATAKA": "KARNATAKA",
    "RJ": "RAJASTHAN",
    "RAJASTHAN": "RAJASTHAN",
    "GJ": "GUJARAT",
    "GUJARAT": "GUJARAT",
    "WB": "WEST_BENGAL",
    "WEST BENGAL": "WEST_BENGAL",
    "AP": "ANDHRA_PRADESH",
    "ANDHRA PRADESH": "ANDHRA_PRADESH",
    "TS": "TELANGANA",
    "TELANGANA": "TELANGANA",
    "KL": "KERALA",
    "KERALA": "KERALA",
    "PB": "PUNJAB",
    "PUNJAB": "PUNJAB",
    "HR": "HARYANA",
    "HARYANA": "HARYANA",
    "BR": "BIHAR",
    "BIHAR": "BIHAR",
    "OD": "ODISHA",
    "ODISHA": "ODISHA",
    "ORISSA": "ODISHA",
    "ALL INDIA": "ALL_INDIA",
    "PAN INDIA": "ALL_INDIA",
    "NATIONAL": "ALL_INDIA",
    "CENTRAL": "ALL_INDIA",
}


# ── 7. BUSINESS STAGE NORMALIZATION ──
BUSINESS_STAGE_MAP: Dict[str, Set[str]] = {
    "NEW": {"NEW", "NEW_UNIT", "GREENFIELD", "STARTUP", "FRESH_PROJECT", "NEW_BUSINESS"},
    "EXISTING": {"EXISTING", "EXISTING_UNIT", "EXPANSION", "MODERNIZATION", "DIVERSIFICATION", "BROWNFIELD"},
    "SELF_EMPLOYMENT": {"SELF_EMPLOYMENT", "STARTING_OWN_BUSINESS", "NEW_SELF_EMPLOYMENT"},
    "ANY_STAGE": {"ANY_STAGE", "NEW_OR_EXISTING", "ALL_STAGES", "ANY"},
}


# ── 8. SUPPORT TYPE NORMALIZATION ──
SUPPORT_TYPE_MAP: Dict[str, Set[str]] = {
    "TERM_LOAN": {"TERM_LOAN", "PROJECT_LOAN", "CAPITAL_LOAN", "CREDIT_FACILITY"},
    "MICROFINANCE": {"MICROFINANCE", "MICRO_LOAN", "SMALL_LOAN", "TINY_CREDIT"},
    "CREDIT": {"CREDIT", "LOAN", "FINANCIAL_ASSISTANCE", "BANK_FINANCE"},
    "SUBSIDY": {"SUBSIDY", "MARGIN_MONEY", "BACK_ENDED_SUBSIDY", "CAPITAL_SUBSIDY", "INTEREST_SUBSIDY"},
    "MARGIN_MONEY": {"MARGIN_MONEY", "BENEFICIARY_CONTRIBUTION_SUPPORT", "SUBSIDY"},
    "INTEREST_SUPPORT": {"INTEREST_SUBVENTION", "INTEREST_SUBSIDY", "CONCESSIONAL_INTEREST"},
    "EDUCATIONAL_LOAN": {"EDUCATIONAL_LOAN", "STUDENT_LOAN", "EDUCATION_FINANCE"},
    "SKILL_SUPPORT": {"SKILL_TRAINING", "CAPACITY_BUILDING", "TRAINING_ASSISTANCE"},
    "TRAINING": {"TRAINING", "SKILL_UPGRADATION", "ENTREPRENEURSHIP_DEVELOPMENT"},
    "TOOL_SUPPORT": {"TOOL_KIT", "EQUIPMENT_SUPPORT", "MACHINERY_GRANT"},
    "MARKET_LINKAGE": {"MARKET_LINKAGE", "EXHIBITION_SUPPORT", "MARKETING_ASSISTANCE"},
    "ENTREPRENEURSHIP_SUPPORT": {"EDP_TRAINING", "INCUBATION", "MENTORSHIP"},
    "FINANCIAL_ASSISTANCE": {"FINANCIAL_ASSISTANCE", "DIRECT_BENEFIT", "GRANT"},
}


class TaxonomyMatcher:
    """
    Multi-Level Taxonomy & Semantic Matching Engine.
    Implements Level 1 to Level 5 hierarchy:
      - LEVEL 1: Exact Normalized Match -> MATCH (1.0)
      - LEVEL 2: Synonym / Alias Match -> MATCH (0.9)
      - LEVEL 3: Parent-Child Semantic Category Match -> MATCH/PARTIAL_MATCH (0.8)
      - LEVEL 4: Related Industry / Activity Match -> PARTIAL_MATCH (0.6)
      - LEVEL 5: Broad Compatible Category -> PARTIAL_MATCH (0.4)
      - MISMATCH -> MISMATCH (0.0)
      - UNKNOWN / Insufficient Info -> NOT_EVALUATED (0.0)
    """

    @classmethod
    def normalize_string(cls, val: Optional[str]) -> str:
        if not val:
            return ""
        return re.sub(r'[^A-Z0-9_]', '', str(val).strip().upper().replace(' ', '_'))

    @classmethod
    def normalize_geography(cls, geo_str: Optional[str]) -> str:
        if not geo_str or str(geo_str).strip().upper() in ["UNKNOWN", "NONE", "NULL", ""]:
            return "UNKNOWN_GEOGRAPHY"
        clean = str(geo_str).strip().upper()
        if clean in GEOGRAPHY_MAP:
            return GEOGRAPHY_MAP[clean]
        for k, v in GEOGRAPHY_MAP.items():
            if k in clean:
                return v
        if "PAN INDIA" in clean or "ALL INDIA" in clean or "NATIONAL" in clean or "CENTRAL" in clean:
            return "ALL_INDIA"
        return cls.normalize_string(clean)

    @classmethod
    def match_sector_or_activity(
        cls,
        user_input: Optional[str],
        scheme_sectors: List[str],
        scheme_activities: List[str],
        scheme_aliases: List[str]
    ) -> Tuple[str, float, str]:
        """
        Evaluates sector/activity match across 5-level hierarchy.
        Returns: (match_status, normalized_score_factor, transparent_explanation)
        """
        if not user_input or str(user_input).strip().upper() in ["UNKNOWN", "NONE", "NULL", ""]:
            return ("NOT_EVALUATED", 0.0, "Beneficiary sector/activity not specified.")

        clean_input = str(user_input).strip().lower()
        norm_input = cls.normalize_string(clean_input)

        # ── LEVEL 1: Exact Normalized Match ──
        for s in scheme_sectors:
            if cls.normalize_string(s) == norm_input:
                return ("MATCH", 1.0, f"Exact sector match: '{user_input.upper()}' matches scheme sector '{s}'.")
        for a in scheme_activities:
            if cls.normalize_string(a) == norm_input:
                return ("MATCH", 1.0, f"Exact activity match: '{user_input}' matches scheme activity '{a}'.")

        # ── LEVEL 2: Synonym / Alias Match ──
        # Check alias dictionary
        all_scheme_aliases = set(scheme_aliases)
        for act in scheme_activities:
            norm_act = cls.normalize_string(act)
            if norm_act in ACTIVITY_ALIASES:
                all_scheme_aliases.update(ACTIVITY_ALIASES[norm_act])
        for sec in scheme_sectors:
            norm_sec = cls.normalize_string(sec)
            if norm_sec in ACTIVITY_ALIASES:
                all_scheme_aliases.update(ACTIVITY_ALIASES[norm_sec])

        for alias in all_scheme_aliases:
            if alias.lower() in clean_input or clean_input in alias.lower():
                return ("MATCH", 0.9, f"Strong synonym match: '{user_input}' matches scheme activity alias '{alias}'.")

        # Check occupation mappings
        for occ, mapped_cats in OCCUPATION_MAP.items():
            if occ.lower() in clean_input or clean_input in occ.lower():
                for cat in mapped_cats:
                    if cat in scheme_sectors or cat in scheme_activities:
                        return ("MATCH", 0.9, f"Occupation match: '{occ}' maps to scheme category '{cat}'.")

        # ── LEVEL 3: Parent-Child Semantic Category Match ──
        for s in scheme_sectors:
            norm_s = cls.normalize_string(s)
            if norm_s in SECTORS:
                children = SECTORS[norm_s]
                for child in children:
                    if child.lower() in clean_input or norm_input == child:
                        return ("MATCH", 0.8, f"Parent-child category match: Scheme sector '{s}' encompasses '{child}'.")
        for norm_sec_key, children in SECTORS.items():
            if norm_input == norm_sec_key or norm_sec_key.lower() in clean_input:
                for sch_sec in scheme_sectors:
                    if cls.normalize_string(sch_sec) in children:
                        return ("MATCH", 0.8, f"Sub-sector category match: '{user_input}' encompasses scheme sector '{sch_sec}'.")

        # ── LEVEL 4: Related Industry / Activity Match ──
        broad_keywords = ["MICRO_ENTERPRISE", "SMALL_BUSINESS", "MSME", "SELF_EMPLOYMENT", "SERVICE", "TRADING", "MANUFACTURING"]
        for sch_sec in scheme_sectors:
            norm_sch_sec = cls.normalize_string(sch_sec)
            if norm_sch_sec in broad_keywords and any(bk in norm_input for bk in broad_keywords):
                return ("PARTIAL_MATCH", 0.6, f"Related industry match: '{user_input.upper()}' shares broad domain with scheme sector '{sch_sec}'.")

        # ── LEVEL 5: Broad Compatible Category Match ──
        if "ANY" in scheme_sectors or "MICRO_ENTERPRISE" in scheme_sectors or "ALL" in scheme_sectors:
            return ("PARTIAL_MATCH", 0.4, f"Broad category match: Scheme supports general micro-enterprises and self-employment.")

        # ── MISMATCH ──
        return ("MISMATCH", 0.0, f"Sector/activity '{user_input}' does not align with scheme sectors ({', '.join(scheme_sectors) or 'N/A'}).")

    @classmethod
    def match_target_group(
        cls,
        user_category: Optional[str],
        user_is_sc: Optional[bool],
        scheme_target_groups: List[str]
    ) -> Tuple[str, float, str]:
        """
        Evaluates target group match.
        """
        norm_targets = [cls.normalize_string(t) for t in scheme_target_groups]

        if "GENERAL_BENEFICIARY" in norm_targets or "ALL_ELIGIBLE" in norm_targets or "OPEN_CATEGORY" in norm_targets or not norm_targets:
            return ("MATCH", 1.0, "Scheme is broadly open to all eligible beneficiaries.")

        if user_is_sc is True or (user_category and str(user_category).strip().upper() in ["SC", "SCHEDULED_CASTE"]):
            if "SC" in norm_targets or "SCHEDULED_CASTE" in norm_targets:
                return ("MATCH", 1.0, "Exact target group match: Scheduled Caste (SC) beneficiary requirement satisfied.")
            if "SC_ST" in norm_targets or "MARGINALIZED_GROUPS" in norm_targets:
                return ("MATCH", 0.9, "Target group match: SC beneficiary covered under marginalized group criteria.")

        if user_category:
            norm_cat = cls.normalize_string(user_category)
            if norm_cat in norm_targets:
                return ("MATCH", 1.0, f"Exact target group match: '{user_category}' satisfies scheme criteria.")
            # Check synonyms
            for target in norm_targets:
                if target in TARGET_GROUP_MAP and norm_cat in TARGET_GROUP_MAP[target]:
                    return ("MATCH", 0.9, f"Target group synonym match: '{user_category}' aligns with '{target}'.")

        return ("MISMATCH", 0.0, f"Target group criteria ({', '.join(scheme_target_groups)}) does not match provided beneficiary category.")

    @classmethod
    def match_geography(
        cls,
        user_state: Optional[str],
        scheme_geographies: List[str]
    ) -> Tuple[str, float, str]:
        """
        Evaluates geography match.
        """
        if not user_state or str(user_state).strip().upper() in ["UNKNOWN", "NONE", "NULL", ""]:
            return ("NOT_EVALUATED", 0.0, "Beneficiary state not specified.")

        user_geo = cls.normalize_geography(user_state)
        norm_scheme_geos = [cls.normalize_geography(g) for g in scheme_geographies]

        if "ALL_INDIA" in norm_scheme_geos or "PAN_INDIA" in norm_scheme_geos or "NATIONAL" in norm_scheme_geos or not norm_scheme_geos:
            return ("MATCH", 1.0, "Scheme is applicable nationwide across all States and UTs.")

        if "NO_SPECIFIC_STATE_RESTRICTION" in norm_scheme_geos:
            return ("MATCH", 1.0, "Scheme has no restrictive state boundary requirements.")

        if user_geo in norm_scheme_geos:
            return ("MATCH", 1.0, f"Exact geographic match: Beneficiary state '{user_state.upper()}' is eligible.")

        return ("MISMATCH", 0.0, f"Beneficiary state '{user_state.upper()}' is outside scheme coverage area ({', '.join(scheme_geographies)}).")
