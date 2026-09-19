import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class RelevanceClassification:
    status: str  # HIGH_PRIORITY, RELEVANT, LOW_PRIORITY, IRRELEVANT, NEEDS_REVIEW
    priority_level: Optional[str]
    score: float
    reason: str
    matched_keywords: List[str]


class SchemeRelevanceClassifier:
    """
    Explainable Relevance Classification Engine for YojnaSetu.
    Aligns discovered government schemes with YojnaSetu's problem statement
    and 7 core priorities. Rejects non-livelihood and purely physical infrastructure grants.
    """

    IRRELEVANT_PATTERNS = [
        (r"\b(?:flyover|highway|expressway|road\s+construction|bridge|metro\s+rail)\b", "Physical transport infrastructure programme; not a citizen welfare scheme"),
        (r"\b(?:toilet\s+construction|swachh\s+bharat\s+odf|solid\s+waste\s+management)\b", "Sanitation infrastructure subsidy; not an enterprise/livelihood credit/subsidy scheme"),
        (r"\b(?:defense\s+procurement|defence\s+equipment|military|ordinance)\b", "Defense and military procurement; not individual citizen/enterprise scheme"),
        (r"\b(?:dissolved|discontinued|subsumed\s+and\s+closed|archived\s+portal)\b", "Archived or discontinued historical programme"),
    ]

    LOW_PRIORITY_PATTERNS = [
        (r"\b(?:primary\s+school|pre-matric\s+books|uniform\s+allowance)\b", "General school allowance; not vocational/enterprise training or business financing"),
        (r"\b(?:general\s+crop\s+insurance|pmfby\s+general)\b", "Broad commercial crop indemnity; separate from enterprise/credit subsidy"),
    ]

    PRIORITIES = [
        ("PRIORITY_1_MSME_CREDIT", [
            "msme", "micro enterprise", "small enterprise", "business loan", "term loan",
            "working capital", "credit guarantee", "interest subsidy", "capital subsidy",
            "startup", "self employment", "entrepreneurship", "pmegp", "mudra", "cgtmse"
        ], "Direct enterprise financing, credit subsidy, or MSME business support"),

        ("PRIORITY_2_MARGINALIZED_ENTREPRENEURSHIP", [
            "scheduled caste", "scheduled tribe", "sc/st", "sc entrepreneur", "st entrepreneur",
            "obc entrepreneur", "minority artisan", "women entrepreneur", "mahila", "stand-up india",
            "divyang", "pwd", "differently abled", "backward classes", "safai karamchari"
        ], "Targeted financial empowerment for marginalized, minority, and women entrepreneurs"),

        ("PRIORITY_3_LIVELIHOOD_ARTISANS", [
            "artisan", "craftsperson", "craftsman", "handloom", "handicraft", "weaver",
            "potter", "blacksmith", "carpenter", "street vendor", "urban vendor", "svanidhi",
            "vishwakarma", "shg", "self help group", "rural livelihood", "traditional trade", "coir"
        ], "Direct support for traditional trades, craftsmen, artisans, and street vendors"),

        ("PRIORITY_4_AGRICULTURE_ALLIED", [
            "dairy", "fisheries", "poultry", "animal husbandry", "food processing",
            "agri-business", "cold storage", "ahidf", "pmksy", "pmmsy", "farm mechanization"
        ], "Commercial agriculture-allied, livestock, food processing, or fisheries enterprise"),

        ("PRIORITY_5_EMPLOYMENT_SKILLS", [
            "skill development", "vocational training", "capacity building", "entrepreneurship training",
            "samarth", "apprentice", "technical training", "tool kit"
        ], "Vocational skill training, entrepreneurship development, and tool kit assistance"),

        ("PRIORITY_6_FINANCIAL_INCLUSION", [
            "microfinance", "concessional credit", "interest subvention", "financial inclusion",
            "direct benefit transfer", "collateral free loan", "soft loan"
        ], "Concessional credit, micro-credit lines, and banking inclusion"),

        ("PRIORITY_7_STATE_SCHEMES", [
            "state scheme", "mukhyamantri", "shasan", "karnataka", "maharashtra", "uttar pradesh",
            "tamil nadu", "gujarat", "rajasthan", "madhya pradesh", "odisha", "bihar", "kerala"
        ], "State-specific enterprise, artisan, or self-employment scheme")
    ]

    @classmethod
    def classify(cls, scheme_name: str, description: str = "", category: str = "") -> RelevanceClassification:
        combined = f"{scheme_name} {description} {category}".lower()

        # 1. Check Irrelevant Patterns
        for pat, reason in cls.IRRELEVANT_PATTERNS:
            if re.search(pat, combined):
                return RelevanceClassification(
                    status="IRRELEVANT",
                    priority_level=None,
                    score=0.0,
                    reason=reason,
                    matched_keywords=[pat]
                )

        # 2. Check Low Priority Patterns
        for pat, reason in cls.LOW_PRIORITY_PATTERNS:
            if re.search(pat, combined):
                return RelevanceClassification(
                    status="LOW_PRIORITY",
                    priority_level="LOW_PRIORITY",
                    score=25.0,
                    reason=reason,
                    matched_keywords=[pat]
                )

        # 3. Check Priorities (1 through 7)
        matched_priorities = []
        matched_kws = []

        for p_code, keywords, p_desc in cls.PRIORITIES:
            hits = [kw for kw in keywords if kw in combined]
            if hits:
                matched_priorities.append((p_code, p_desc, len(hits)))
                matched_kws.extend(hits)

        if matched_priorities:
            # Sort by number of keyword hits
            matched_priorities.sort(key=lambda x: x[2], reverse=True)
            top_p, top_desc, count = matched_priorities[0]

            score = min(100.0, 50.0 + (count * 10.0))
            status = "HIGH_PRIORITY" if score >= 70.0 else "RELEVANT"

            return RelevanceClassification(
                status=status,
                priority_level=top_p,
                score=score,
                reason=f"Matched {top_p}: {top_desc} (found indicators: {matched_kws[:4]})",
                matched_keywords=matched_kws
            )

        # Default fallback for unclassified government entries
        return RelevanceClassification(
            status="NEEDS_REVIEW",
            priority_level=None,
            score=40.0,
            reason="Scheme does not strongly match core MSME/livelihood keywords nor explicit exclusions; requires manual triage.",
            matched_keywords=[]
        )
