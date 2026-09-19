import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.scheme import Scheme


@dataclass
class DeduplicationResult:
    is_duplicate: bool
    duplicate_stage: Optional[str]
    matched_scheme_id: Optional[str]
    matched_scheme_name: Optional[str]
    similarity_score: float
    action_recommended: str  # UNIQUE, DUPLICATE_CANDIDATE, MERGE_VARIATION
    notes: str


class SchemeDeduplicator:
    """
    7-Stage Layered Deduplication Engine.
    Prevents duplicate scheme creation across myScheme, central portals, state portals,
    and implementing agency registries.
    Never automatically overwrites canonical schemes based on fuzzy similarity.
    """

    KNOWN_ALIASES: Dict[str, str] = {
        "pmegp": "prime minister's employment generation programme",
        "mudra": "pradhan mantri mudra yojana",
        "pm svanidhi": "pm street vendor's atmanirbhar nidhi",
        "stand up india": "stand-up india scheme for sc/st and women",
        "pm vishwakarma": "pm vishwakarma scheme",
        "cgtmse": "credit guarantee fund trust for micro and small enterprises",
        "pm-janman": "pradhan mantri janjati adivasi nyaya maha abhiyan",
        "ahidf": "animal husbandry infrastructure development fund",
        "sclcss": "special credit linked capital subsidy scheme for sc/st",
        "day-nulm": "deen dayal antyodaya yojana - national urban livelihoods mission",
    }

    @classmethod
    def clean_name(cls, name: str) -> str:
        """Normalizes scheme name: strips punctuation, extra spaces, and common stop words."""
        if not name:
            return ""
        s = name.lower()
        # Strip parenthesized acronyms like (PMEGP)
        s = re.sub(r"\(.*?\)", " ", s)
        # Strip possessives like 's
        s = re.sub(r"['’]s\b", " ", s)
        # Remove common filler prefixes
        s = re.sub(r"^(operational\s+guidelines\s+for|guidelines\s+of|scheme\s+for|the)\s+", "", s)
        # Remove punctuation
        s = re.sub(r"[^\w\s]", " ", s)
        tokens = [t for t in s.split() if t not in ["yojana", "scheme", "mission", "programme", "program", "for", "and", "the", "of", "in", "pm"]]
        return " ".join(tokens)

    @classmethod
    def token_jaccard(cls, s1: str, s2: str) -> float:
        set1 = set(cls.clean_name(s1).split())
        set2 = set(cls.clean_name(s2).split())
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    @classmethod
    def check_duplicate(
        cls,
        candidate_name: str,
        candidate_code: Optional[str] = None,
        candidate_source_url: Optional[str] = None,
        candidate_app_url: Optional[str] = None,
        candidate_ministry: Optional[str] = None,
        db: Optional[Session] = None,
        existing_schemes: Optional[List[Scheme]] = None
    ) -> DeduplicationResult:
        if not candidate_name:
            return DeduplicationResult(
                is_duplicate=False,
                duplicate_stage=None,
                matched_scheme_id=None,
                matched_scheme_name=None,
                similarity_score=0.0,
                action_recommended="UNIQUE",
                notes="Candidate name empty."
            )

        schemes = existing_schemes or []
        if db and not schemes:
            schemes = db.query(Scheme).all()

        c_name_norm = cls.clean_name(candidate_name)
        c_code_clean = (candidate_code or "").strip().upper()
        c_source_clean = (candidate_source_url or "").strip().rstrip("/")
        c_app_clean = (candidate_app_url or "").strip().rstrip("/")
        c_min_clean = (candidate_ministry or "").strip().lower()

        # Check known alias resolution
        c_alias = None
        for alias_key, alias_val in cls.KNOWN_ALIASES.items():
            if alias_key in candidate_name.lower():
                c_alias = alias_val
                break

        for s in schemes:
            s_name = s.scheme_name or ""
            s_name_norm = cls.clean_name(s_name)
            s_code = (s.scheme_code or "").strip().upper()
            s_source = (s.official_source_url or "").strip().rstrip("/")
            s_app = (s.application_url or s.official_portal or "").strip().rstrip("/")
            s_min = (s.ministry or "").strip().lower()

            # STAGE 1: Exact Scheme Code Match
            if c_code_clean and c_code_clean != "UNKNOWN" and s_code and s_code != "UNKNOWN":
                if c_code_clean == s_code:
                    return DeduplicationResult(
                        is_duplicate=True,
                        duplicate_stage="STAGE_1_EXACT_CODE",
                        matched_scheme_id=s.scheme_id,
                        matched_scheme_name=s_name,
                        similarity_score=1.0,
                        action_recommended="DUPLICATE_CANDIDATE",
                        notes=f"Matches canonical scheme code '{s_code}'."
                    )

            # STAGE 2: Normalized Official Name Match
            if c_name_norm and s_name_norm and c_name_norm == s_name_norm:
                return DeduplicationResult(
                    is_duplicate=True,
                    duplicate_stage="STAGE_2_NORMALIZED_NAME",
                    matched_scheme_id=s.scheme_id,
                    matched_scheme_name=s_name,
                    similarity_score=1.0,
                    action_recommended="DUPLICATE_CANDIDATE",
                    notes=f"Normalized title identical to existing scheme '{s_name}'."
                )

            # STAGE 3: Scheme Name + Ministry / Implementing Agency Pair
            if c_min_clean and s_min and (c_min_clean in s_min or s_min in c_min_clean):
                if cls.token_jaccard(candidate_name, s_name) >= 0.70:
                    return DeduplicationResult(
                        is_duplicate=True,
                        duplicate_stage="STAGE_3_NAME_AND_MINISTRY",
                        matched_scheme_id=s.scheme_id,
                        matched_scheme_name=s_name,
                        similarity_score=0.90,
                        action_recommended="DUPLICATE_CANDIDATE",
                        notes=f"Matches ministry and high title similarity with '{s_name}'."
                    )

            # STAGE 4: Official Source URL Match
            if c_source_clean and s_source and c_source_clean == s_source:
                return DeduplicationResult(
                    is_duplicate=True,
                    duplicate_stage="STAGE_4_SOURCE_URL",
                    matched_scheme_id=s.scheme_id,
                    matched_scheme_name=s_name,
                    similarity_score=1.0,
                    action_recommended="DUPLICATE_CANDIDATE",
                    notes=f"Identical official source URL '{s_source}' already registered."
                )

            # STAGE 5: Application Portal URL Match
            if c_app_clean and s_app and c_app_clean == s_app and not s_app.endswith(".gov.in"):
                return DeduplicationResult(
                    is_duplicate=True,
                    duplicate_stage="STAGE_5_APPLICATION_URL",
                    matched_scheme_id=s.scheme_id,
                    matched_scheme_name=s_name,
                    similarity_score=0.95,
                    action_recommended="DUPLICATE_CANDIDATE",
                    notes=f"Shares specialized application portal '{s_app}' with '{s_name}'."
                )

            # STAGE 6: Known Alias Match
            if c_alias and cls.token_jaccard(c_alias, s_name) >= 0.65:
                return DeduplicationResult(
                    is_duplicate=True,
                    duplicate_stage="STAGE_6_ALIAS_MATCH",
                    matched_scheme_id=s.scheme_id,
                    matched_scheme_name=s_name,
                    similarity_score=0.90,
                    action_recommended="DUPLICATE_CANDIDATE",
                    notes=f"Candidate alias matched known official scheme '{s_name}'."
                )

            # STAGE 7: High Token Jaccard Similarity (> 0.85)
            j_score = cls.token_jaccard(candidate_name, s_name)
            if j_score >= 0.85:
                return DeduplicationResult(
                    is_duplicate=True,
                    duplicate_stage="STAGE_7_TOKEN_SIMILARITY",
                    matched_scheme_id=s.scheme_id,
                    matched_scheme_name=s_name,
                    similarity_score=j_score,
                    action_recommended="DUPLICATE_CANDIDATE",
                    notes=f"High lexical similarity ({j_score:.2f}) with '{s_name}'."
                )

        return DeduplicationResult(
            is_duplicate=False,
            duplicate_stage=None,
            matched_scheme_id=None,
            matched_scheme_name=None,
            similarity_score=0.0,
            action_recommended="UNIQUE",
            notes="No existing duplicate detected across 7 deduplication stages."
        )
