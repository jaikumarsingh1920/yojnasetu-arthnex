"""
Entity Resolution Engine for YojnaSetu (SIH26092).

Provides high-precision institutional matching between partner branch records and
statutory government entities (RBI, NABARD, NSFDC, DFS).

Adheres strictly to Anti-Fabrication Rule:
Ambiguous or low-confidence matches are NEVER attached to sensitive financial observations.
"""

import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models.financial_intelligence import InstitutionEntity, InstitutionAlias
from app.models.partner import Partner

logger = logging.getLogger("yojnasetu.engine.entity_resolution")


class EntityResolutionEngine:
    """
    Multi-tier institution matching and alias resolution engine.
    """

    @classmethod
    def normalize_name(cls, name: Optional[str]) -> str:
        """
        Cleans and normalizes institution names into a canonical token string.
        Handles punctuation, corporate suffixes, banking synonyms, and abbreviations.
        """
        if not name:
            return ""
        
        # 1. Uppercase
        s = name.upper().strip()
        
        # 2. Replace ampersands
        s = re.sub(r"\s*&\s*", " AND ", s)
        
        # 3. Strip punctuation
        s = re.sub(r"[\(\)\[\]\{\}\.,\-_/\\'\"]", " ", s)
        
        # 4. Normalize corporate and cooperative forms
        s = re.sub(r"\bLIMITED\b|\bLTD\b", " ", s)
        s = re.sub(r"\bPRIVATE\b|\bPVT\b", " ", s)
        s = re.sub(r"\bCORPORATION\b|\bCORP\b", " CORPORATION ", s)
        s = re.sub(r"\bCOOPERATIVE\b|\bCO OP\b|\bCOOP\b|\bSAHAKARI\b", " COOPERATIVE ", s)
        s = re.sub(r"\bDEVELOPMENT\b|\bVIKAS\b", " DEVELOPMENT ", s)
        s = re.sub(r"\bFINANCE\b|\bVITTA\b", " FINANCE ", s)
        s = re.sub(r"\bNIGAM\b", " CORPORATION ", s)
        s = re.sub(r"\bHEAD OFFICE\b|\bHO\b|\bCIRCLE OFFICE\b|\bREGIONAL OFFICE\b|\bRO\b|\bBRANCH\b|\bMAIN BRANCH\b|\bMSME BRANCH\b", " ", s)
        
        # 5. Remove city/district tokens if attached at tail (e.g. 'GORAKHPUR', 'LUCKNOW')
        # We preserve them during multi-field matching, but strip from core legal stem
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @classmethod
    def resolve_partner(
        cls,
        db: Session,
        partner: Partner
    ) -> Tuple[Optional[InstitutionEntity], str, float, str]:
        """
        Resolves a Partner record to an authoritative InstitutionEntity.
        
        Returns:
            Tuple[Optional[InstitutionEntity], match_level, confidence_score, explanation]
            
        Match levels:
            MATCH_LEVEL_1 (1.00): Exact Authoritative Identifier (e.g. RBI / NABARD code)
            MATCH_LEVEL_2 (0.98): Exact Canonical Legal Name Match
            MATCH_LEVEL_3 (0.92): Normalized Name + Institution Type + State Match
            MATCH_LEVEL_4 (0.88): Registered Alias + Institution Type + State Match
            MATCH_LEVEL_5 (0.70): Conservative Multi-Field Evidence
            AMBIGUOUS_MATCH (0.0): Conflict or below safety threshold
            UNMATCHED (0.0): No authoritative government entity record found
        """
        norm_partner = cls.normalize_name(partner.name)
        partner_state = (partner.state or "").strip().upper()
        partner_dist = (partner.district or "").strip().upper()
        raw_inst_type = (partner.institution_type or partner.partner_type or "").strip().upper()

        TYPE_ALIASES = {
            "RRB": "REGIONAL_RURAL_BANK",
            "REGIONAL_RURAL_BANK": "REGIONAL_RURAL_BANK",
            "PSB": "PUBLIC_SECTOR_BANK",
            "PUBLIC_SECTOR_BANK": "PUBLIC_SECTOR_BANK",
            "BANK": "PUBLIC_SECTOR_BANK",
            "SCA": "STATE_CHANNELIZING_AGENCY",
            "STATE_CHANNELIZING_AGENCY": "STATE_CHANNELIZING_AGENCY",
            "CHANNELIZING_AGENCY": "STATE_CHANNELIZING_AGENCY",
            "MFI": "NBFC_MFI",
            "NBFC_MFI": "NBFC_MFI",
            "MICRO_FINANCE_INSTITUTION": "NBFC_MFI",
            "COOPERATIVE_BANK": "COOPERATIVE_BANK",
            "COOPERATIVE_SOCIETY": "COOPERATIVE_BANK",
            "DISTRICT_INDUSTRIES_CENTRE": "DISTRICT_INDUSTRIES_CENTRE",
            "DIC": "DISTRICT_INDUSTRIES_CENTRE",
            "COMMISSION_OFFICE": "STATUTORY_COMMISSION",
            "STATUTORY_COMMISSION": "STATUTORY_COMMISSION",
            "CSC": "COMMON_SERVICES_CENTRE",
            "COMMON_SERVICES_CENTRE": "COMMON_SERVICES_CENTRE",
            "STATUTORY_FINANCIAL_CORPORATION": "STATUTORY_FINANCIAL_CORPORATION",
            "SMALL_FINANCE_BANK": "SMALL_FINANCE_BANK",
            "SFB": "SMALL_FINANCE_BANK",
            "FINANCIAL_INSTITUTION": "FINANCIAL_INSTITUTION",
            "OTHER_AGENCY": "OTHER_AGENCY",
        }
        partner_inst_type = TYPE_ALIASES.get(raw_inst_type, raw_inst_type)

        # -------------------------------------------------------------
        # Level 0: Strict Quarantine & Corrupted Fragment Gate
        # -------------------------------------------------------------
        # Quarantined records must NEVER resolve to an institution
        if (getattr(partner, "record_status", None) == "QUARANTINED" 
                or getattr(partner, "quarantine_reason", None) 
                or getattr(partner, "validation_status", None) == "QUARANTINED"):
            return (None, "QUARANTINED", 0.0, f"Partner is quarantined ({getattr(partner, 'quarantine_reason', 'quarantined')}) and cannot be resolved to an institution entity.")

        # Address fragments, building names, postal codes, and corrupted PDF extraction fragments
        FRAGMENT_PATTERNS = [
            r"^\d+$",                                            # pure digits
            r"^\d{6}$",                                          # pincode
            r"^[A-Z0-9\-\.\s,]{1,3}$",                          # 1-3 characters
            r"\b(PLOT\s*NO|FLOOR|SECTOR|ROAD|MARG|TIKIAPARA|COMPLEX|PREMISES|BUILDING)\b",
            r"\b(RANCHI\s*[-–]?\s*\d{6}|MUMBAI\s*[-–]?\s*\d{3}\s*\d{3})\b",
            r"^\s*(PLOT|FLAT|SHOP|ROOM|DOOR|KHASRA|WARD|LANE|STREET)\b",
        ]
        raw_name_upper = (partner.name or "").upper().strip()
        is_fragment = any(re.search(pat, raw_name_upper) for pat in FRAGMENT_PATTERNS)
        
        INSTITUTIONAL_KEYWORDS = {
            "BANK", "GRAMIN", "GRAMA", "GRAMEENA", "CORPORATION", "COMMISSION", "NIGAM",
            "COOPERATIVE", "VIKAS", "SOCIETY", "KENDRA", "DIRECTORATE", "DEPARTMENT",
            "SIDBI", "NABARD", "NSFDC", "DIC", "KVIC", "SFB", "MFI", "FINANCE", "VITTA",
            "AUTHORITY", "MINISTRY", "AGENCY", "BOARD", "TRUST", "FOUNDATION", "CENTRE",
            "ENTERPRISE", "SAHAKARI"
        }
        tokens = set(norm_partner.split())
        has_institutional_keyword = bool(tokens & INSTITUTIONAL_KEYWORDS)

        if is_fragment and not has_institutional_keyword:
            return (None, "CORRUPTED_FRAGMENT", 0.0, f"Record '{partner.name}' is an address fragment or corrupted extraction text, not a financial institution.")

        # -------------------------------------------------------------
        # Level 1: Match by Explicit Regulatory Identifier (if present)
        # -------------------------------------------------------------
        if hasattr(partner, "code") and partner.code:
            code_clean = partner.code.strip()
            stmt = select(InstitutionEntity).where(
                or_(
                    InstitutionEntity.rbi_code == code_clean,
                    InstitutionEntity.nabard_code == code_clean
                ),
                InstitutionEntity.is_active == True
            )
            entity = db.execute(stmt).scalars().first()
            if entity:
                return (entity, "MATCH_LEVEL_1", 1.00, f"Exact authoritative regulatory identifier match: {code_clean}")

        # -------------------------------------------------------------
        # Level 2: Exact Canonical Normalized Name Match
        # -------------------------------------------------------------
        stmt = select(InstitutionEntity).where(
            InstitutionEntity.normalized_name == norm_partner,
            InstitutionEntity.is_active == True
        )
        entity = db.execute(stmt).scalars().first()
        if entity:
            return (entity, "MATCH_LEVEL_2", 0.98, f"Exact canonical name match: {entity.canonical_name}")

        # -------------------------------------------------------------
        # Level 3: Normalized Name + Institution Type + State
        # -------------------------------------------------------------
        # Query all active entities
        entities = db.execute(select(InstitutionEntity).where(InstitutionEntity.is_active == True)).scalars().all()
        
        best_match = None
        best_score = 0.0
        best_level = "UNMATCHED"
        best_reason = "No matching institution found"

        for ent in entities:
            ent_norm = ent.normalized_name
            ent_type = TYPE_ALIASES.get(ent.institution_type, ent.institution_type)
            type_matches = (
                (ent_type == partner_inst_type)
                or (partner_inst_type in ("FINANCIAL_INSTITUTION", "OTHER_AGENCY"))
                or (partner_inst_type in ent_type)
                or (ent_type in partner_inst_type)
                or ("BANK" in partner_inst_type and "BANK" in ent_type)
            )
            national_types = {
                "PUBLIC_SECTOR_BANK", "STATUTORY_FINANCIAL_CORPORATION",
                "STATUTORY_COMMISSION", "COMMON_SERVICES_CENTRE",
                "SMALL_FINANCE_BANK", "NBFC_MFI"
            }
            state_matches = (
                ent.institution_type in national_types
                or not ent.headquarters_state
                or not partner_state
                or (ent.headquarters_state.upper() == partner_state)
            )

            # Direct stem containment: partner branch name must contain authoritative entity name
            if ent_norm in norm_partner and type_matches and state_matches:
                score = 0.92
                if score > best_score:
                    best_score = score
                    best_match = ent
                    best_level = "MATCH_LEVEL_3"
                    best_reason = f"Normalized name match with {ent.canonical_name} (Type: {ent.institution_type}, State: {partner.state})"

        if best_match and best_score >= 0.90:
            return (best_match, best_level, best_score, best_reason)

        # -------------------------------------------------------------
        # Level 4: Registered Alias Match (Amalgamation & Lineage)
        # -------------------------------------------------------------
        aliases = db.execute(select(InstitutionAlias)).scalars().all()
        for al in aliases:
            al_norm = al.normalized_alias
            al_ent = al.institution
            if not al_ent or not al_ent.is_active:
                continue

            al_type = TYPE_ALIASES.get(al_ent.institution_type, al_ent.institution_type)
            type_matches = (
                (al_type == partner_inst_type)
                or (partner_inst_type in ("FINANCIAL_INSTITUTION", "OTHER_AGENCY"))
                or (partner_inst_type in al_type)
                or (al_type in partner_inst_type)
                or ("BANK" in partner_inst_type and "BANK" in al_type)
            )
            national_types = {
                "PUBLIC_SECTOR_BANK", "STATUTORY_FINANCIAL_CORPORATION",
                "STATUTORY_COMMISSION", "COMMON_SERVICES_CENTRE",
                "SMALL_FINANCE_BANK", "NBFC_MFI"
            }
            state_matches = (
                al_ent.institution_type in national_types
                or not al_ent.headquarters_state
                or not partner_state
                or (al_ent.headquarters_state.upper() == partner_state)
            )

            alias_in_partner = (al_norm in norm_partner) if len(al_norm) > 4 else bool(re.search(rf"\b{re.escape(al_norm)}\b", norm_partner))
            if alias_in_partner and type_matches and state_matches:
                score = 0.88
                if score > best_score:
                    best_score = score
                    best_match = al_ent
                    best_level = "MATCH_LEVEL_4"
                    best_reason = f"Official alias match '{al.alias_name}' -> {al_ent.canonical_name} (Source: {al.source_authority})"

        if best_match and best_score >= 0.85:
            return (best_match, best_level, best_score, best_reason)

        # -------------------------------------------------------------
        # Level 5: Conservative Multi-Field Matching (Key Recognized Brands)
        # -------------------------------------------------------------
        BRAND_STEMS = {
            "BANK OF BARODA": "Bank of Baroda",
            "PUNJAB NATIONAL BANK": "Punjab National Bank",
            "CENTRAL BANK OF INDIA": "Central Bank of India",
            "INDIAN BANK": "Indian Bank",
            "UNION BANK OF INDIA": "Union Bank of India",
            "CANARA BANK": "Canara Bank",
            "STATE BANK OF INDIA": "State Bank of India",
            "BANK OF INDIA": "Bank of India",
            "UCO BANK": "UCO Bank",
            "BANK OF MAHARASHTRA": "Bank of Maharashtra",
            "INDIAN OVERSEAS BANK": "Indian Overseas Bank",
            "PUNJAB AND SIND BANK": "Punjab & Sind Bank",
            "PUNJAB & SIND BANK": "Punjab & Sind Bank",
            "BARODA U P BANK": "Baroda U.P. Bank",
            "BARODA UP BANK": "Baroda U.P. Bank",
            "ARYAVART BANK": "Aryavart Bank",
            "GRAMIN BANK OF ARYAVART": "Aryavart Bank",
            "PRATHAMA UP GRAMIN BANK": "Prathama U.P. Gramin Bank",
            "PRATHAMA BANK": "Prathama U.P. Gramin Bank",
            "MAHARASHTRA GRAMIN BANK": "Maharashtra Gramin Bank",
            "SAURASHTRA GRAMIN BANK": "Saurashtra Gramin Bank",
            "BARODA GUJARAT GRAMIN BANK": "Baroda Gujarat Gramin Bank",
            "KERALA GRAMIN BANK": "Kerala Gramin Bank",
            "KARNATAKA VIKAS GRAMEENA BANK": "Karnataka Vikas Grameena Bank",
            "TAMIL NADU GRAMA BANK": "Tamil Nadu Grama Bank",
            "PASCHIM BANGA GRAMIN BANK": "Paschim Banga Gramin Bank",
            "UTTAR PRADESH SCHEDULED CASTE FINANCE": "Uttar Pradesh Scheduled Caste Finance and Development Corporation (UPSCFDC)",
            "DISTRICT INDUSTRIES AND ENTERPRISE PROMOTION": "Directorate of Industries & Enterprise Promotion",
            "DISTRICT INDUSTRIES CENTRE": "Directorate of Industries & Enterprise Promotion",
            "KHADI AND VILLAGE INDUSTRIES COMMISSION": "Khadi and Village Industries Commission (KVIC)",
            "SMALL INDUSTRIES DEVELOPMENT BANK OF INDIA": "Small Industries Development Bank of India (SIDBI)",
            "COMMON SEVA KENDRA": "CSC e-Governance Services India Limited",
            "CSC KENDRA": "CSC e-Governance Services India Limited",
        }

        for stem, canonical_target in BRAND_STEMS.items():
            if stem in norm_partner:
                for ent in entities:
                    if ent.canonical_name == canonical_target or ent.normalized_name == cls.normalize_name(canonical_target):
                        return (ent, "MATCH_LEVEL_5", 0.75, f"Conservative brand identifier match for '{stem}' -> {ent.canonical_name}")

        return (None, "UNMATCHED", 0.0, f"No verified statutory entity could be matched with confidence >= 0.70 for '{partner.name}'")
