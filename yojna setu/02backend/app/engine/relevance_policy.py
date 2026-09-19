"""
SIH26092 Recommendation Universe Relevance Policy.
Defines explicit lifecycle and relevance classifications to prevent non-livelihood /
out-of-scope schemes (e.g., pilgrimage tours, sports medals, photo contests)
from polluting the citizen entrepreneur recommendation experience while preserving
full provenance in the global discovery catalog.
"""

import re
from enum import Enum
from typing import Tuple, Optional
from app.models.scheme import Scheme


class SIH26092RecommendationStatus(str, Enum):
    DIRECTLY_RELEVANT = "DIRECTLY_RELEVANT"
    SUPPORTING = "SUPPORTING"
    LOW_RELEVANCE = "LOW_RELEVANCE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class SIH26092RecommendationRelevancePolicy:
    """
    Authoritative policy defining which schemes in the global catalog belong to the
    SIH26092 recommendation universe for marginalized and micro-entrepreneurs.
    """

    # 1. Patterns that are strictly OUT_OF_SCOPE for entrepreneurship/livelihood recommendations
    OUT_OF_SCOPE_PATTERNS = [
        # Religious pilgrimage, yatras, temple tours
        (
            r"\b(?:tirth|tirtha|teerth|yatra|darshan|pilgrim|pilgrimage|temple\s+tour|mansarovar|kailash|sindhu\s+darshan|sita\s+temple|hinglaj)\b",
            "Religious pilgrimage or temple tour scheme; outside SIH26092 entrepreneurship & livelihood scope"
        ),
        # Competitive sports awards, sports hostels, sports pensions
        (
            r"\b(?:sports\s+excellence|cash\s+award\s+to\s+players|sportsperson\s+pension|sports\s+hostel|sports\s+medal|dronacharya\s+award|olympiad)\b",
            "Competitive sports incentive, player cash award, or sports pension; outside enterprise/livelihood scope"
        ),
        # Creative contests, photo competitions
        (
            r"\b(?:photo\s+contest|photography\s+competition|photo\s+exhibition|acting\s+in\s+tiatr|film\s+making\s+competition)\b",
            "Cultural or photography contest/exhibition; not an enterprise support or livelihood credit scheme"
        ),
        # Pure civil/mega transport infrastructure
        (
            r"\b(?:flyover|expressway|metro\s+rail|solid\s+waste\s+treatment\s+plant|ropeway\s+infrastructure|seaplane\s+terminal)\b",
            "Large-scale municipal/civil infrastructure project; not an individual or micro-enterprise scheme"
        ),
    ]

    # 2. Patterns that are LOW_RELEVANCE (non-enterprise school kits, general crop indemnity)
    LOW_RELEVANCE_PATTERNS = [
        (
            r"\b(?:pre-matric\s+books|primary\s+school\s+uniform|free\s+school\s+cycle|school\s+bus\s+pass)\b",
            "General school supply or minor student allowance; not vocational/enterprise training or business financing"
        ),
    ]

    # 3. DIRECTLY_RELEVANT priority patterns
    DIRECTLY_RELEVANT_PATTERNS = [
        r"\b(?:loan|credit|subsidy|margin\s+money|interest\s+subsidy|grant|working\s+capital|term\s+loan)\b",
        r"\b(?:msme|micro\s+enterprise|small\s+enterprise|business|startup|self\s+employment|entrepreneur|udyam)\b",
        r"\b(?:artisan|craftsperson|craftsman|handloom|handicraft|weaver|potter|blacksmith|carpenter|vishwakarma)\b",
        r"\b(?:dairy|fisheries|poultry|livestock|animal\s+husbandry|food\s+processing|agro\s+processing)\b",
        r"\b(?:sc|st|scheduled\s+caste|scheduled\s+tribe|obc|minority|women\s+entrepreneur|mahila|divyang|pwd)\b",
        r"\b(?:stand-up\s+india|pmegp|mudra|cgtmse|svanidhi|street\s+vendor|nsfdc|nstfdc|nbcfdc|nskfdc)\b",
        r"\b(?:skill\s+development|vocational\s+training|capacity\s+building|tool\s+kit|equipment\s+subsidy)\b",
    ]

    _relevance_cache: dict = {}

    @classmethod
    def clear_cache(cls) -> None:
        cls._relevance_cache.clear()

    @classmethod
    def evaluate_scheme(cls, scheme: Scheme) -> Tuple[SIH26092RecommendationStatus, str]:
        """
        Evaluates a canonical scheme against the SIH26092 recommendation universe policy.
        Returns: (status, reason)
        """
        cache_key = (scheme.scheme_id, str(getattr(scheme, "updated_at", None))) if getattr(scheme, "scheme_id", None) else None
        if cache_key and cache_key in cls._relevance_cache:
            return cls._relevance_cache[cache_key]

        corpus = " ".join(filter(None, [
            scheme.scheme_name,
            scheme.purpose,
            scheme.short_description,
            scheme.sector,
            scheme.activity_type,
            scheme.target_beneficiary,
            scheme.benefit_description,
        ])).lower()

        # Check OUT_OF_SCOPE patterns
        for pattern, reason in cls.OUT_OF_SCOPE_PATTERNS:
            if re.search(pattern, corpus):
                res = (SIH26092RecommendationStatus.OUT_OF_SCOPE, reason)
                if cache_key:
                    cls._relevance_cache[cache_key] = res
                return res

        # Check LOW_RELEVANCE patterns
        for pattern, reason in cls.LOW_RELEVANCE_PATTERNS:
            if re.search(pattern, corpus):
                res = (SIH26092RecommendationStatus.LOW_RELEVANCE, reason)
                if cache_key:
                    cls._relevance_cache[cache_key] = res
                return res

        # Check DIRECTLY_RELEVANT patterns
        for pattern in cls.DIRECTLY_RELEVANT_PATTERNS:
            if re.search(pattern, corpus):
                res = (
                    SIH26092RecommendationStatus.DIRECTLY_RELEVANT,
                    "Core enterprise credit, MSME assistance, marginalized livelihood, or vocational empowerment scheme"
                )
                if cache_key:
                    cls._relevance_cache[cache_key] = res
                return res

        # Default to SUPPORTING if no negative patterns triggered
        res = (
            SIH26092RecommendationStatus.SUPPORTING,
            "Supporting welfare or livelihood enablement programme"
        )
        if cache_key:
            cls._relevance_cache[cache_key] = res
        return res

    @classmethod
    def is_recommendation_universe_eligible(cls, scheme: Scheme) -> Tuple[bool, SIH26092RecommendationStatus, str]:
        """
        Determines whether a scheme should be evaluated within the SIH26092 recommendation universe.
        Returns: (is_eligible, status, reason)
        """
        status, reason = cls.evaluate_scheme(scheme)
        is_eligible = status in (
            SIH26092RecommendationStatus.DIRECTLY_RELEVANT,
            SIH26092RecommendationStatus.SUPPORTING,
        )
        return is_eligible, status, reason
