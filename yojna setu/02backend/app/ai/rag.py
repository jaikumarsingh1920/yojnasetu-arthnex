import logging
import json
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Scheme, SchemeRule, SchemeDocument
from app.models.knowledge import SchemeFAQ, SchemeKnowledgeProfile
from app.schemas.ai import SourceCitation
from app.ai.observability import RAGObservabilityTracker

logger = logging.getLogger("yojnasetu.ai.rag")

HINDI_STOPWORDS: Set[str] = {
    "के", "का", "की", "को", "में", "से", "पर", "और", "या", "लिए", "है", "हैं", "था",
    "थे", "थी", "होगा", "होगी", "कर", "करना", "चाहिए", "यह", "वह", "एक", "तो", "भी",
    "ने", "पे", "तक", "क्या", "कैसे", "कहाँ", "किसे", "मुझे", "हमें", "आपको", "अपने",
    "अपनी", "अपना", "वाले", "वाली", "वाला", "हेतु", "दौरान", "तहत", "अनुसार", "द्वारा"
}

RAG_STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "over", "after", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "it", "its", "tell", "me",
    "my", "i", "we", "you", "your", "he", "she", "they", "them", "how", "can", "could",
    "should", "would", "please", "kya", "hai", "hain", "ka", "ki", "ke", "ko", "se", "me",
    "mein", "par", "bhi", "aur", "ya", "toh", "ye", "yeh", "woh", "unka", "meri", "mera",
    "give", "get", "want", "need", "show"
} | HINDI_STOPWORDS

# Authoritative bilingual concept map for government scheme domain retrieval
HINDI_BILINGUAL_MAP: Dict[str, List[str]] = {
    # Caste, Tribal & Social Classes
    "अनुसूचित जाति": ["scheduled", "caste", "sc", "nsfdc"],
    "अनुसूचित जनजाति": ["scheduled", "tribe", "st", "nstfdc"],
    "अनुसूचित": ["scheduled", "sc", "st"],
    "जाति": ["caste"],
    "जनजाति": ["tribe"],
    "अन्य पिछड़ा वर्ग": ["obc", "backward", "nbcfdc"],
    "पिछड़ा वर्ग": ["backward", "obc"],
    "सफाई कर्मचारी": ["safai", "karamchari", "sanitation", "nskfdc"],
    "दिव्यांग": ["pwd", "disability", "disabled", "divyang"],
    "विकलांग": ["disability", "disabled"],
    "अल्पसंख्यक": ["minority", "minorities"],

    # Credit & Financial Assistance
    "ऋण": ["loan", "credit", "finance", "borrowing"],
    "कर्ज": ["loan", "credit"],
    "उधार": ["loan", "credit"],
    "सब्सिडी": ["subsidy", "grant"],
    "अनुदान": ["grant", "subsidy", "assistance"],
    "ब्याज": ["interest"],
    "छूट": ["concession", "subsidy", "rebate"],
    "वित्तीय सहायता": ["financial", "assistance", "subsidy"],
    "वित्तीय": ["financial", "finance"],
    "सहायता": ["assistance", "support"],

    # Business, MSME & Livelihood
    "व्यवसाय": ["business", "enterprise", "trade"],
    "उद्योग": ["industry", "enterprise", "msme", "business"],
    "रोजगार": ["employment", "livelihood"],
    "स्वरोजगार": ["self", "employment", "entrepreneur", "business"],
    "उद्यमी": ["entrepreneur", "enterprise", "business"],
    "उद्यमिता": ["entrepreneurship", "enterprise"],
    "दुकान": ["shop", "store", "retail"],
    "व्यापार": ["business", "trade"],
    "सूक्ष्म": ["micro", "msme"],
    "लघु": ["small", "msme"],
    "मध्यम": ["medium", "msme"],

    # Target Demographics
    "महिला उद्यमी": ["women", "woman", "entrepreneur", "female"],
    "महिला": ["woman", "women", "female", "mahila"],
    "महिलाएं": ["women", "females"],
    "युवा": ["youth"],
    "कारीगर": ["artisan", "craftsperson", "craft", "vishwakarma"],
    "शिल्पकार": ["artisan", "craftsperson"],
    "बुनकर": ["weaver", "handloom"],
    "किसान": ["farmer", "kisan", "agriculture"],
    "कृषि": ["agriculture", "farming"],

    # Education & Training
    "शिक्षा": ["education", "student", "study"],
    "छात्र": ["student", "scholarship"],
    "छात्रवृत्ति": ["scholarship", "stipend"],

    # Statutory Documentation & Procedures
    "दस्तावेज": ["document", "documents", "certificate", "paper"],
    "कागजात": ["document", "documents", "paper"],
    "प्रमाण पत्र": ["certificate", "proof", "document"],
    "प्रमाण": ["proof", "certificate"],
    "पत्र": ["document", "certificate"],
    "पात्रता": ["eligibility", "eligible"],
    "शर्तें": ["terms", "conditions", "eligibility"],
    "आवेदन": ["application", "apply", "portal"],
    "प्रक्रिया": ["process", "guidance", "how"],
    "योजना": ["scheme", "yojna"],
    "मुद्रा": ["mudra"],
    "पीएमईजीपी": ["pmegp"],
    "विश्वकर्मा": ["vishwakarma", "artisan"],
    "स्टैंडअप": ["standup", "stand-up"],
    "स्टार्टअप": ["startup", "start-up"],
    "लाभ": ["benefit", "benefits", "advantage"],
    "फायदा": ["benefit", "benefits", "advantage"],
    "गारंटी": ["guarantee", "collateral", "security"],
    "जमानत": ["collateral", "guarantee", "security"],
    "अवधि": ["tenure", "period", "months"],
    "उम्र": ["age", "eligibility"],
    "आयु": ["age", "eligibility"],
    "आय": ["income", "eligibility"],
    "सवाल": ["faq", "question", "query"],
    "प्रश्न": ["faq", "question", "query"],
}


def expand_query_multilingual(query: str) -> Tuple[Set[str], bool]:
    """
    Expands input queries (English, Hinglish, Devanagari Hindi) into normalized concept tokens.
    Uses Unicode-aware tokenization to preserve Devanagari combining marks and conjuncts.
    """
    q_norm = query.strip()
    is_hindi = bool(re.search(r"[\u0900-\u097F]", q_norm))

    # Unicode-aware word tokenization (preserves Latin alphanumeric and Devanagari glyphs)
    raw_tokens = set(re.findall(r"[a-zA-Z0-9_\u0900-\u097F]+", q_norm))
    informative = {t.lower() for t in raw_tokens} - RAG_STOPWORDS

    expanded = set(informative)
    if is_hindi:
        # Check multi-word phrase mappings first
        for phrase, eng_tokens in HINDI_BILINGUAL_MAP.items():
            if " " in phrase and phrase in q_norm:
                expanded.update(eng_tokens)

        # Check individual Hindi tokens
        for t in raw_tokens:
            if t in HINDI_BILINGUAL_MAP:
                expanded.update(HINDI_BILINGUAL_MAP[t])

    return expanded, is_hindi


class SchemeVectorStore:
    """
    Retrieval-Augmented Generation (RAG) vector store for verified scheme data & documents.
    Uses TF-IDF + metadata relevance ranking over authoritative scheme database records.
    Returns traceable SourceCitation objects with version metadata and observability tracking.
    """

    def __init__(self, db: Session):
        self.db = db
        self._chunks: List[Dict[str, Any]] = []
        self._build_index()

    def reindex(self, db: Optional[Session] = None) -> int:
        """Re-indexes active scheme chunks to guarantee version freshness upon updates."""
        if db:
            self.db = db
        self._build_index()
        return len(self._chunks)

    def _generate_chunks_for_scheme(self, sch: Scheme) -> List[Dict[str, Any]]:
        """Generates all context chunks (metadata, financials, rules, documents, application, eligibility, benefits, faqs) for a single scheme."""
        sch_version = getattr(sch, 'version', 1) or 1
        sch_status = sch.scheme_status or "VERIFIED"
        last_updated = sch.updated_at.isoformat() if getattr(sch, 'updated_at', None) else None
        source_url = sch.official_source_url or getattr(sch, 'official_portal', None) or "Official Government Portal"

        # Check knowledge profile
        profile = self.db.query(SchemeKnowledgeProfile).filter(SchemeKnowledgeProfile.scheme_id == sch.scheme_id).first()
        quality_score = float(getattr(profile, 'quality_score', 85.0) or 85.0)
        confidence = 0.95

        chunks: List[Dict[str, Any]] = []

        # 1. Scheme General Metadata Chunk
        aliases_str = ""
        if profile and profile.aliases:
            try:
                alias_list = json.loads(profile.aliases)
                if alias_list:
                    aliases_str = f" Known aliases: {', '.join(alias_list)}."
            except Exception:
                pass
        geo_str = f" Geographic scope: {profile.geographic_level}." if (profile and profile.geographic_level) else ""
        outcome_str = f" Intended outcome: {profile.intended_outcome}" if (profile and profile.intended_outcome) else ""

        meta_text = (
            f"{sch.scheme_name} (ID: {sch.scheme_id}, Version: v{sch_version}) is implemented by "
            f"{sch.ministry or sch.implementing_agency or 'the Government of India'}.{aliases_str} "
            f"Objective: {sch.purpose or sch.short_description or sch.scheme_name}.{outcome_str} "
            f"Target Beneficiaries: {sch.target_beneficiary or sch.target_groups or 'All eligible citizens'}. "
            f"State Coverage: {sch.state_coverage or sch.state_restriction or 'All India'}.{geo_str}"
        )
        chunks.append({
            "scheme_id": sch.scheme_id,
            "scheme_code": sch.scheme_id,
            "scheme_name": sch.scheme_name,
            "version": sch_version,
            "scheme_status": sch_status,
            "last_updated": last_updated,
            "source_type": "SCHEME_METADATA",
            "source_document": getattr(sch, 'source_document', None) or 'Official Scheme Guidelines',
            "official_source_url": source_url,
            "rule_id": None,
            "text": meta_text,
            "quality_score": quality_score,
            "confidence": confidence,
        })

        # 2. Scheme Financial Assistance Chunk (Strict fact separation)
        is_credit = getattr(sch, 'is_credit_scheme', True)
        if is_credit:
            fin_type = "Credit / Loan Facility"
            max_loan = f"₹{sch.max_loan_amount:,.0f}" if getattr(sch, 'max_loan_amount', None) else "As per project appraisal / not specified in available official guidelines"
            rate_val = getattr(sch, 'interest_rate', None) or getattr(sch, 'interest_rate_max', None)
            rate = f"{rate_val}% p.a." if rate_val is not None else "As determined by financing institution / not specified in available official guidelines"
        else:
            fin_type = f"Grant / Subsidy / Welfare Assistance (No Loan) — {getattr(sch, 'financial_category', 'DIRECT_BENEFIT')}"
            max_loan = "Loan facility not applicable"
            rate = "Loan interest not applicable"

        subsidy = f"{sch.subsidy_percentage}%" if getattr(sch, 'subsidy_percentage', None) else "Refer to official scheme guidelines"
        tenure_val = getattr(sch, 'repayment_period_max_months', None) or getattr(sch, 'repayment_period_min_months', None)
        tenure_str = f"up to {tenure_val} months" if tenure_val else "Not specified in available official guidelines"

        fin_summary_text = f" Breakdown: {profile.financial_summary}" if (profile and profile.financial_summary) else ""

        fin_text = (
            f"Financial details for {sch.scheme_name} (v{sch_version}): Facility type is {fin_type}. "
            f"Maximum support available is {max_loan} with interest rate at {rate} and capital subsidy up to {subsidy}. "
            f"Repayment period is {tenure_str}. "
            f"{getattr(sch, 'benefit_description', None) or getattr(sch, 'financial_assistance_summary', None) or 'Official Financial Support'}"
            f"{fin_summary_text}"
        )
        chunks.append({
            "scheme_id": sch.scheme_id,
            "scheme_code": sch.scheme_id,
            "scheme_name": sch.scheme_name,
            "version": sch_version,
            "scheme_status": sch_status,
            "last_updated": last_updated,
            "source_type": "SCHEME_FINANCIALS",
            "source_document": getattr(sch, 'source_document', None) or 'Official Financial Guidelines',
            "official_source_url": source_url,
            "rule_id": None,
            "text": fin_text,
            "quality_score": quality_score,
            "confidence": confidence,
        })

        # 3. Scheme Rules Chunks
        rules = self.db.query(SchemeRule).filter(SchemeRule.scheme_id == sch.scheme_id).all()
        for r in rules:
            raw_desc = r.error_message or f"Requirement condition for {r.field} must be satisfied."
            clean_desc = re.sub(r"Rule\s+Code:\s*\w+[-_]?\d*", "", raw_desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r"\bRULE[-_]?\d+\b", "", clean_desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r"Field:\s*[\w_]+\s*(?:IN|==|!=|>|<|>=|<=)?\s*[^;\.\n]+(?:;|\.|\n|$)", "", clean_desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r"Requirement\s+Field:\s*\w+", "", clean_desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r"Requirement\s+Value:\s*[^;\.\n]+", "", clean_desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r"\b(?:PM_SURAJ|AUTHORISED_SCA|AUTHORISED_CA)\b", "Authorized Partner Portal", clean_desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r"\bDescription:\s*", "", clean_desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r"[ \t]{2,}", " ", clean_desc).strip()

            rule_text = (
                f"Official eligibility guideline for {sch.scheme_name} (v{sch_version}): "
                f"{clean_desc or f'Eligibility requirement for {sch.scheme_name}.'}"
            )
            chunks.append({
                "scheme_id": sch.scheme_id,
                "scheme_code": sch.scheme_id,
                "scheme_name": sch.scheme_name,
                "version": sch_version,
                "scheme_status": sch_status,
                "last_updated": last_updated,
                "source_type": "SCHEME_RULE",
                "source_document": r.source_document or 'Official Statutory Rules',
                "official_source_url": source_url,
                "rule_id": str(r.rule_id),
                "text": rule_text,
                "quality_score": quality_score,
                "confidence": confidence,
            })

        # 4. Scheme Granular Eligibility Chunk
        exclusions_text = profile.exclusions if (profile and profile.exclusions) else "Defaulters, existing central capital subsidy recipients, and ineligible entity types as per guidelines."
        elig_summary = (
            getattr(profile, 'applicant_category_summary', None)
            or getattr(sch, 'target_beneficiary', None)
            or getattr(sch, 'target_groups', None)
            or "Refer to official scheme guidelines"
        )
        elig_text = (
            f"Official eligibility criteria for {sch.scheme_name} (v{sch_version}): "
            f"Target Beneficiaries: {sch.target_beneficiary or sch.target_groups or 'All eligible citizens'}. "
            f"Requirements: {elig_summary}. "
            f"Exclusions: {exclusions_text}"
        )
        chunks.append({
            "scheme_id": sch.scheme_id,
            "scheme_code": sch.scheme_id,
            "scheme_name": sch.scheme_name,
            "version": sch_version,
            "scheme_status": sch_status,
            "last_updated": last_updated,
            "source_type": "SCHEME_ELIGIBILITY",
            "source_document": getattr(sch, 'source_document', None) or 'Official Eligibility Guidelines',
            "official_source_url": source_url,
            "rule_id": None,
            "text": elig_text,
            "quality_score": quality_score,
            "confidence": confidence,
        })

        # 5. Scheme Benefits Chunk
        ben_desc = getattr(sch, 'benefit_description', None) or getattr(sch, 'financial_assistance_summary', None) or sch.purpose or 'Official Financial and Technical Support'
        ben_text = (
            f"Official benefits and entitlements for {sch.scheme_name} (v{sch_version}): "
            f"{ben_desc}. Category: {getattr(sch, 'financial_category', 'Assistance')}. "
            f"Concessions: Provided as per official operational guidelines."
        )
        chunks.append({
            "scheme_id": sch.scheme_id,
            "scheme_code": sch.scheme_id,
            "scheme_name": sch.scheme_name,
            "version": sch_version,
            "scheme_status": sch_status,
            "last_updated": last_updated,
            "source_type": "SCHEME_BENEFITS",
            "source_document": getattr(sch, 'source_document', None) or 'Official Benefit Guidelines',
            "official_source_url": source_url,
            "rule_id": None,
            "text": ben_text,
            "quality_score": quality_score,
            "confidence": confidence,
        })

        # 6. Scheme Documents Chunks
        docs = self.db.query(SchemeDocument).filter(SchemeDocument.scheme_id == sch.scheme_id).all()
        for doc in docs:
            doc_text = (
                f"Document guidance for {sch.scheme_name} (v{sch_version}): "
                f"Required paper: {doc.document_name} ({doc.requirement_type}). "
                f"{doc.condition or 'Must be submitted during application verification.'}"
            )
            chunks.append({
                "scheme_id": sch.scheme_id,
                "scheme_code": sch.scheme_id,
                "scheme_name": sch.scheme_name,
                "version": sch_version,
                "scheme_status": sch_status,
                "last_updated": last_updated,
                "source_type": "SCHEME_DOCUMENT",
                "source_document": doc.document_name,
                "official_source_url": source_url,
                "rule_id": None,
                "text": doc_text,
                "quality_score": quality_score,
                "confidence": confidence,
            })

        # 7. Application Guidance & Provenance Chunk
        app_stages = ""
        if profile and profile.approval_stages:
            try:
                st_list = json.loads(profile.approval_stages)
                if st_list:
                    app_stages = f" Key stages: {' -> '.join(st_list)}."
            except Exception:
                pass
        app_text = (
            f"Official application process for {sch.scheme_name} (v{sch_version}): "
            f"Submissions are handled via {sch.application_mode or 'ONLINE'} mode through official portal ({sch.official_portal or 'Official Ministry Portal'}). "
            f"{app_stages} "
            f"Official URL: {source_url}. Verification Status: Verified Government Scheme."
        )
        chunks.append({
            "scheme_id": sch.scheme_id,
            "scheme_code": sch.scheme_id,
            "scheme_name": sch.scheme_name,
            "version": sch_version,
            "scheme_status": sch_status,
            "last_updated": last_updated,
            "source_type": "APPLICATION_GUIDANCE",
            "source_document": sch.official_source_url or 'Official Gazette Portal',
            "official_source_url": source_url,
            "rule_id": None,
            "text": app_text,
            "quality_score": quality_score,
            "confidence": confidence,
        })

        # 8. Grounded Scheme FAQs Chunks
        faqs = self.db.query(SchemeFAQ).filter(SchemeFAQ.scheme_id == sch.scheme_id).all()
        for faq in faqs:
            faq_text = (
                f"Frequently Asked Question for {sch.scheme_name} ({faq.category}): "
                f"Question: {faq.question} Answer: {faq.answer}"
            )
            chunks.append({
                "scheme_id": sch.scheme_id,
                "scheme_code": sch.scheme_id,
                "scheme_name": sch.scheme_name,
                "version": sch_version,
                "scheme_status": sch_status,
                "last_updated": last_updated,
                "source_type": "SCHEME_FAQ",
                "source_document": faq.source_document or getattr(sch, 'source_document', None) or 'Official FAQs',
                "official_source_url": faq.source_url or source_url,
                "rule_id": None,
                "text": faq_text,
                "quality_score": quality_score,
                "confidence": faq.confidence or 0.95,
            })

        return chunks


    def _build_index(self):
        """Indexes all verified Schemes, SchemeRules, and SchemeDocuments into searchable context chunks."""
        schemes = self.db.query(Scheme).filter(
            or_(
                Scheme.scheme_status == "ACTIVE",
                Scheme.scheme_status == "VERIFIED",
                Scheme.scheme_status.is_(None),
                Scheme.scheme_status == ""
            )
        ).all()
        active_schemes = [
            s for s in schemes
            if str(getattr(s, "scheme_status", "") or "").upper() not in ("INACTIVE", "DISCONTINUED", "ARCHIVED")
        ]

        chunks: List[Dict[str, Any]] = []
        for sch in active_schemes:
            chunks.extend(self._generate_chunks_for_scheme(sch))

        self._chunks = chunks
        logger.info("RAG Vector Store indexed %d scheme context chunks across %d active schemes.", len(chunks), len(active_schemes))

    def update_scheme_chunks(self, scheme_or_id: Any) -> int:
        """
        Incrementally updates RAG vector chunks for a single scheme without rebuilding
        the entire catalog index.
        """
        if isinstance(scheme_or_id, Scheme):
            scheme = scheme_or_id
            sid = scheme.scheme_id
        else:
            sid = str(scheme_or_id)
            scheme = self.db.query(Scheme).filter(Scheme.scheme_id == sid).first()

        # Remove old chunks for this scheme
        self._chunks = [c for c in self._chunks if c.get("scheme_id") != sid]

        # If scheme is active, generate new chunks and append
        if scheme and str(getattr(scheme, "scheme_status", "") or "").upper() not in ("INACTIVE", "DISCONTINUED", "ARCHIVED"):
            new_chunks = self._generate_chunks_for_scheme(scheme)
            self._chunks.extend(new_chunks)
            logger.info("Incrementally synchronized %d RAG chunks for scheme '%s'. Total chunks: %d", len(new_chunks), sid, len(self._chunks))
            return len(new_chunks)

        logger.info("Removed RAG chunks for inactive/deleted scheme '%s'. Total chunks: %d", sid, len(self._chunks))
        return 0


    def search(
        self,
        query: str,
        scheme_id: Optional[str] = None,
        top_k: int = 4
    ) -> List[SourceCitation]:
        """Searches indexed scheme chunks for top relevant context citations with bilingual Hindi support."""
        if not self._chunks:
            RAGObservabilityTracker.record_retrieval(0)
            return []

        # Filter by scheme_id if explicitly specified
        target_chunks = self._chunks
        if scheme_id:
            scheme_scoped = [c for c in self._chunks if c["scheme_id"] == str(scheme_id)]
            if scheme_scoped:
                target_chunks = scheme_scoped

        eval_terms, is_hindi = expand_query_multilingual(query)

        # If query has zero informative terms and no scheme_id filter, avoid false positive retrieval
        if not eval_terms and not scheme_id:
            RAGObservabilityTracker.record_retrieval(0)
            return []

        scored_chunks = []
        q_lower = query.lower()

        for chunk in target_chunks:
            text_terms = set(re.findall(r"[a-zA-Z0-9_\u0900-\u097F]+", chunk["text"].lower()))
            overlap = eval_terms.intersection(text_terms)
            score = len(overlap) / (len(eval_terms) + 1.0)

            # Boost exact scheme code, scheme name, or acronym match
            chunk_code = chunk["scheme_code"].lower()
            chunk_name = chunk["scheme_name"].lower()

            acronym_match = re.search(r"\(([^)]+)\)", chunk_name)
            acronym = acronym_match.group(1).lower() if acronym_match else None

            is_scheme_match = (
                chunk_code in q_lower
                or chunk_name in q_lower
                or (acronym and re.search(rf"\b{re.escape(acronym)}\b", q_lower))
                or (acronym and acronym in eval_terms)
                or (chunk_code in eval_terms)
            )
            if is_scheme_match:
                score += 0.50

            # Intent boost ONLY if there is substantive overlap or direct scheme match
            # (Prevents out-of-domain queries like 'how to cook...' from receiving +0.3 application boost)
            if is_scheme_match or len(overlap) >= 1:
                if any(term in q_lower for term in ["document", "documents", "paper", "papers", "certificate", "praman", "दस्तावेज", "प्रमाण"]):
                    if chunk["source_type"] == "SCHEME_DOCUMENT":
                        score += 0.3
                elif any(term in q_lower for term in ["emi", "interest", "loan", "subsidy", "money", "paise", "byaj", "cost", "ऋण", "कर्ज", "ब्याज"]):
                    if chunk["source_type"] == "SCHEME_FINANCIALS":
                        score += 0.3
                elif any(term in q_lower for term in ["apply", "portal", "how to", "form", "kaise kare", "website", "आवेदन", "प्रक्रिया"]):
                    if chunk["source_type"] == "APPLICATION_GUIDANCE":
                        score += 0.3
                elif any(term in q_lower for term in ["eligible", "eligibility", "patrata", "पात्रता", "शर्तें", "criteria", "caste", "age", "income", "who can apply", "उम्र", "आय"]):
                    if chunk["source_type"] in ("SCHEME_ELIGIBILITY", "SCHEME_RULE"):
                        score += 0.3
                elif any(term in q_lower for term in ["benefit", "benefits", "advantage", "entitlement", "fayda", "लाभ", "फायदा"]):
                    if chunk["source_type"] == "SCHEME_BENEFITS":
                        score += 0.3
                elif any(term in q_lower for term in ["faq", "question", "kya", "kaise", "kab", "kitna", "who", "where", "can"]):
                    if chunk["source_type"] == "SCHEME_FAQ":
                        score += 0.25

            # False-positive rejection:
            # 1. Reject if no overlap and no scheme match
            if len(overlap) == 0 and not is_scheme_match and not (scheme_id and chunk["scheme_id"] == scheme_id):
                continue

            # 2. For queries with >= 3 terms, require at least 2 matching terms OR direct scheme match
            # to avoid false positive retrieval on coincidental single words (e.g. 'football match' -> 'match')
            if len(eval_terms) >= 3 and not is_scheme_match and len(overlap) < 2 and not (scheme_id and chunk["scheme_id"] == scheme_id):
                continue

            # 3. Calibrated relevance threshold
            min_thresh = 0.22 if len(eval_terms) >= 3 else 0.12
            if score >= min_thresh or is_scheme_match or (scheme_id and chunk["scheme_id"] == scheme_id):
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        citations: List[SourceCitation] = []
        for score, chunk in scored_chunks[:top_k]:
            norm_score = min(1.0, score)
            citations.append(SourceCitation(
                scheme_id=chunk["scheme_id"],
                scheme_name=chunk["scheme_name"],
                source_type=chunk["source_type"],
                source_document=chunk["source_document"],
                rule_id=chunk["rule_id"],
                snippet=chunk["text"][:400],
                relevance_score=round(norm_score, 2),
                official_source_url=chunk.get("official_source_url"),
                quality_score=chunk.get("quality_score")
            ))

        RAGObservabilityTracker.record_retrieval(len(citations))
        RAGObservabilityTracker.record_citations(len(citations))
        return citations

