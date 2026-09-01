import re
import uuid
import logging
from typing import List, Optional, Dict, Any, Generator
from sqlalchemy.orm import Session

from app.models.scheme import Scheme
from app.schemas.ai import AIChatRequest, AIChatResponse, SourceCitation, AICopilotAction, RichCard
from app.schemas.recommendation import BeneficiaryProfileInput
from app.ai.copilot_router import AICopilotQueryRouter
from app.ai.hybrid_rag import HybridSchemeRAG
from app.ai.tools import CopilotTools
from app.ai.security import AISecurityGuard
from app.ai.provider import get_ai_provider

logger = logging.getLogger("yojnasetu.ai.agent")

# Multi-turn conversation memory store
SESSION_MEMORY_STORE: Dict[str, Dict[str, Any]] = {}

CASUAL_INTENTS = {
    "CASUAL_GREETING",
    "CASUAL_CONVERSATION",
    "IDENTITY_QUERY",
    "GENERAL_HELP",
    "EMOTIONAL_HELP",
    "LANGUAGE_CHANGE",
}


def sanitize_user_facing_text(text: str) -> str:
    """
    Sanitizes user-facing text before sending to frontend.
    Removes internal rule IDs (RULE-0002), field names, SQL operators, and raw metadata headers.
    """
    if not text:
        return ""
    
    sanitized = str(text)
    # 1. Remove internal rule codes (e.g. RULE-0001, RULE-0002, rule_123, Rule Code: RULE-0015)
    sanitized = re.sub(r"Rule\s+Code:\s*\w+[-_]?\d*", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bRULE[-_]?\d+\b", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\brule[-_]?\d+\b", "", sanitized, flags=re.IGNORECASE)

    # 2. Remove internal database field & operator patterns
    sanitized = re.sub(r"Field:\s*[\w_]+(?:\s*(?:IN|==|!=|>|<|>=|<=)\s*[^;\.\n]+)?[;\.]?", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"Requirement\s+Field:\s*\w+", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"Requirement\s+Value:\s*[^;\.\n]+", "", sanitized, flags=re.IGNORECASE)
    
    # 3. Clean raw internal enum constants & identifiers
    sanitized = re.sub(r"\b(?:PM_SURAJ|AUTHORISED_SCA|AUTHORISED_CA)\b", "Authorized Partner Portal", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bTRADITIONAL_TRADE_\d+\b", "Traditional Artisanship & Trade", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bactivity_type\b", "business activity", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bsocial_category\b", "social category", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bannual_income\b", "annual income", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bSMALL_MICRO_BUSINESS\b", "Small & Micro Enterprise", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bAPPLICATION_ROUTE\b", "Application Route", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bapplication_route\b", "application route", sanitized, flags=re.IGNORECASE)

    # 4. Strip internal raw headers if present
    for header in [
        "Rule Code:", "Requirement Field:", "Requirement Value:",
        "Verification Status:", "Scheme Code:", "Field:", "Description:"
    ]:
        sanitized = re.sub(re.escape(header), "", sanitized, flags=re.IGNORECASE)

    # 5. Clean up multiple spaces and trailing whitespace
    sanitized = re.sub(r"[ \t]{2,}", " ", sanitized)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)

    return sanitized.strip()


class GPTCopilotAgent:
    """
    Deep Conversational Agent for YojnaSetu:
    - Normalizes Indian regional speech, Hinglish, Roman Hindi, and voice transcription shorthand.
    - Handles pronoun references ("isme", "iske", "ye") across multi-turn context.
    - Supports profile corrections ("actually 26 age", "nahi OBC hu").
    - Progressive 1-2 question profiling flow.
    - Grounded scheme facts + Deterministic tool execution for recommendations, eligibility & EMIs.
    """

    @classmethod
    def get_session_memory(cls, session_id: str) -> Dict[str, Any]:
        if session_id not in SESSION_MEMORY_STORE:
            SESSION_MEMORY_STORE[session_id] = {
                "extracted_facts": {},
                "history": [],
                "active_scheme_id": None,
                "current_scheme_id": None,
                "last_recommendation": None,
                "preferred_language": "en"
            }
        return SESSION_MEMORY_STORE[session_id]

    @classmethod
    def update_session_facts(cls, session_id: str, message: str) -> Dict[str, Any]:
        """Extracts and updates conversational profile facts with voice tolerance and correction handling."""
        memory = cls.get_session_memory(session_id)
        facts = memory["extracted_facts"]

        raw_msg = re.sub(r"</?untrusted_content>", "", message).strip()
        msg_lower = raw_msg.lower()

        # Handle explicit corrections
        if any(term in msg_lower for term in ["actually", "nahi", "change", "correct", "update"]):
            if "age" in msg_lower or "saal" in msg_lower or "years" in msg_lower:
                m = re.search(r"\b(\d{1,2})\b", msg_lower)
                if m:
                    facts["age"] = int(m.group(1))
            if "obc" in msg_lower:
                facts["social_category"] = "OBC"
                facts["is_obc"] = True
                facts.pop("is_sc", None)
                facts.pop("is_st", None)
            elif "sc" in msg_lower or "scheduled caste" in msg_lower:
                facts["social_category"] = "SC"
                facts["is_sc"] = True
                facts.pop("is_obc", None)
                facts.pop("is_st", None)
            elif "st" in msg_lower or "scheduled tribe" in msg_lower:
                facts["social_category"] = "ST"
                facts["is_st"] = True
                facts.pop("is_sc", None)
                facts.pop("is_obc", None)
            elif "general" in msg_lower or "gen" in msg_lower:
                facts["social_category"] = "GENERAL"
                facts.pop("is_sc", None)
                facts.pop("is_obc", None)
                facts.pop("is_st", None)

        # Age extraction with voice tolerance ("24 saal", "age 28", "28 years old", "meri umar 25 hai")
        age_match = re.search(r"\b(?:i\s+am|age|mer?i\s+umar|umar)\s*[:=]?\s*(\d{1,2})\b", msg_lower)
        if not age_match:
            age_match = re.search(r"\b(\d{1,2})\s*(?:saal|years|year|yrs|yr)\b", msg_lower)
        if age_match:
            facts["age"] = int(age_match.group(1))
        elif re.match(r"^\d{2}$", msg_lower.strip()):
            facts["age"] = int(msg_lower.strip())

        # State extraction with voice tolerance ("up", "u p", "uttar pradesh", "mp", "m p")
        if any(term in msg_lower for term in ["up", "u p", "uttar pradesh"]):
            facts["state"] = "UTTAR PRADESH"
        elif "bihar" in msg_lower:
            facts["state"] = "BIHAR"
        elif "maharashtra" in msg_lower:
            facts["state"] = "MAHARASHTRA"
        elif "delhi" in msg_lower:
            facts["state"] = "DELHI"
        elif any(term in msg_lower for term in ["mp", "m p", "madhya pradesh"]):
            facts["state"] = "MADHYA PRADESH"
        elif "rajasthan" in msg_lower:
            facts["state"] = "RAJASTHAN"
        elif "gujarat" in msg_lower:
            facts["state"] = "GUJARAT"
        elif "tamil nadu" in msg_lower:
            facts["state"] = "TAMIL NADU"
        elif "karnataka" in msg_lower:
            facts["state"] = "KARNATAKA"
        elif "west bengal" in msg_lower:
            facts["state"] = "WEST BENGAL"

        # Social Category extraction
        if "sc" in msg_lower or "scheduled caste" in msg_lower:
            facts["social_category"] = "SC"
            facts["is_sc"] = True
        elif "st" in msg_lower or "scheduled tribe" in msg_lower:
            facts["social_category"] = "ST"
            facts["is_st"] = True
        elif "obc" in msg_lower:
            facts["social_category"] = "OBC"
            facts["is_obc"] = True
        elif "general" in msg_lower or "gen" in msg_lower:
            facts["social_category"] = "GENERAL"

        # Gender extraction
        if any(term in msg_lower for term in ["woman", "female", "mahila", "ladki"]):
            facts["gender"] = "FEMALE"
        elif any(term in msg_lower for term in ["man", "male", "purush", "ladka"]):
            facts["gender"] = "MALE"

        # Income extraction ("1.8 lakh", "2 lakh", "2 lac", "2L", "50k", "180000")
        if any(term in msg_lower for term in ["1.8 lakh", "1.8l", "180000"]):
            facts["annual_income"] = 180000.0
        elif any(term in msg_lower for term in ["2 lakh", "2 lac", "2l", "200000"]):
            facts["annual_income"] = 200000.0
        elif any(term in msg_lower for term in ["1 lakh", "1 lac", "1l", "100000"]):
            facts["annual_income"] = 100000.0
        elif any(term in msg_lower for term in ["3 lakh", "3 lac", "3l", "300000"]):
            facts["annual_income"] = 300000.0
        elif any(term in msg_lower for term in ["5 lakh", "5 lac", "5l", "500000"]):
            facts["annual_income"] = 500000.0

        # Activity / Business Purpose extraction
        if any(term in msg_lower for term in ["tailoring", "stitching", "kapde", "silai"]):
            facts["sector"] = "MICRO_FINANCE"
            facts["activity_type"] = "SMALL_MICRO_BUSINESS"
            facts["business_description"] = "tailoring"
        elif any(term in msg_lower for term in ["dairy", "milk", "doodh", "pashupalan"]):
            facts["sector"] = "AGRICULTURE"
            facts["activity_type"] = "FARMING_ALLIED"
            facts["business_description"] = "dairy farming"
        elif any(term in msg_lower for term in ["shop", "retail", "kirana", "dukaan", "dukan"]):
            facts["sector"] = "MICRO_FINANCE"
            facts["activity_type"] = "SMALL_MICRO_BUSINESS"
            facts["business_description"] = "retail shop"
        elif any(term in msg_lower for term in ["factory", "manufacturing", "production"]):
            facts["sector"] = "MICRO_FINANCE"
            facts["activity_type"] = "SMALL_MICRO_BUSINESS"
            facts["business_description"] = "manufacturing"
        elif any(term in msg_lower for term in ["business", "kaam", "trade", "work", "entrepreneur", "shop"]):
            facts["sector"] = "MICRO_FINANCE"
            facts["activity_type"] = "SMALL_MICRO_BUSINESS"
            facts["business_description"] = "new business unit"

        # Funding Needed / Loan Amount ("2 lakh", "₹2 lakh", "2 lac", "2L", "50k")
        loan_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|l|lakhs)", msg_lower)
        if loan_match:
            val = float(loan_match.group(1)) * 100000
            facts["requested_loan_amount"] = val
        elif "50k" in msg_lower or "50 thousand" in msg_lower:
            facts["requested_loan_amount"] = 50000.0

        # Interest rate & tenure extraction
        rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", msg_lower)
        if rate_match:
            facts["custom_interest_rate"] = float(rate_match.group(1))

        tenure_match = re.search(r"(\d+)\s*(?:years?|yrs?|yr|saal)", msg_lower)
        if tenure_match:
            facts["custom_tenure_months"] = int(tenure_match.group(1)) * 12

        memory["extracted_facts"] = facts
        return facts

    @classmethod
    def build_profile_from_memory(cls, session_id: str, req_profile: Optional[BeneficiaryProfileInput]) -> BeneficiaryProfileInput:
        """Combines session memory facts with request profile."""
        memory = cls.get_session_memory(session_id)
        facts = memory["extracted_facts"]

        base_data = req_profile.model_dump() if req_profile else {}
        for k, v in facts.items():
            if k in base_data and base_data[k] is None:
                base_data[k] = v
            elif k not in base_data:
                base_data[k] = v

        if "annual_income" not in base_data or base_data["annual_income"] is None:
            base_data["annual_income"] = facts.get("annual_income", 180000.0)

        if "age" not in base_data or base_data["age"] is None:
            base_data["age"] = facts.get("age", 28)

        if "social_category" not in base_data or base_data["social_category"] is None:
            base_data["social_category"] = facts.get("social_category", "GENERAL")

        if "state" not in base_data or base_data["state"] is None:
            base_data["state"] = facts.get("state", "ALL_INDIA")

        return BeneficiaryProfileInput(**base_data)

    @classmethod
    def process_query(
        cls,
        db: Session,
        req: AIChatRequest,
        current_user_id: Optional[str] = None
    ) -> AIChatResponse:
        """Main agent query processing pipeline."""
        session_id = req.session_id or f"copilot-sess-{uuid.uuid4().hex[:10]}"
        sanitized_msg = AISecurityGuard.sanitize_user_input(req.message)
        raw_msg = re.sub(r"</?untrusted_content>", "", sanitized_msg).strip()

        memory = cls.get_session_memory(session_id)
        extracted_facts = cls.update_session_facts(session_id, raw_msg)

        page_ctx = req.page_context or {}
        msg_lower = raw_msg.lower()
        norm_msg = AICopilotQueryRouter.normalize_query(raw_msg)

        intent = AICopilotQueryRouter.classify_intent(raw_msg, page_ctx)

        # Determine active conversation language:
        # Priority 1: Session memory language (if explicitly chosen by user)
        # Priority 2: Detected language from current user input (if Indian script or Hinglish)
        # Priority 3: Frontend requested language
        session_lang = memory.get("preferred_language")
        detected_lang = AICopilotQueryRouter.detect_language(raw_msg)
        req_lang = (req.preferred_language or "").lower().split("-")[0]

        if session_lang in ["hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or", "as"]:
            target_lang = session_lang
        elif detected_lang != "en":
            target_lang = detected_lang
        elif req_lang in ["hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or", "as"]:
            target_lang = req_lang
        else:
            target_lang = "en"

        # -------------------------------------------------------------
        # 1. ABSOLUTE EARLY EXIT FOR LANGUAGE_CHANGE (0 RAG, 0 Cards)
        # -------------------------------------------------------------
        if intent == "LANGUAGE_CHANGE":
            logger.info("AI Copilot Intent -> RAW: %r | NORMALIZED: %r | INTENT: LANGUAGE_CHANGE | HANDLER: EarlyExit | RAG: FALSE", raw_msg, norm_msg)
            
            # Check for negative English expressions first ("mujhe english nahi aati") -> Switch to Hindi
            if any(w in norm_msg for w in ["english", "angrezi", "eng"]) and any(neg in norm_msg for neg in ["nahi", "nhi", "nahin", "na", "no", "not"]):
                target_lang = "hi"
            elif any(w in raw_msg or w in norm_msg for w in ["hindi", "हिंदी", "hin"]):
                target_lang = "hi"
            elif any(w in raw_msg or w in norm_msg for w in ["english", "angrezi", "eng"]):
                target_lang = "en"
            elif any(w in raw_msg or w in norm_msg for w in ["bengali", "বাংলা"]):
                target_lang = "bn"
            elif any(w in raw_msg or w in norm_msg for w in ["tamil", "தமிழ்"]):
                target_lang = "ta"
            elif any(w in raw_msg or w in norm_msg for w in ["telugu", "తెలుగు"]):
                target_lang = "te"
            elif any(w in raw_msg or w in norm_msg for w in ["marathi", "मराठी"]):
                target_lang = "mr"
            elif any(w in raw_msg or w in norm_msg for w in ["gujarati", "ગુજરાતી"]):
                target_lang = "gu"
            elif any(w in raw_msg or w in norm_msg for w in ["kannada", "ಕನ್ನಡ"]):
                target_lang = "kn"
            elif any(w in raw_msg or w in norm_msg for w in ["malayalam", "മലയാളം"]):
                target_lang = "ml"
            elif any(w in raw_msg or w in norm_msg for w in ["punjabi", "ਪੰਜਾਬੀ"]):
                target_lang = "pa"
            elif any(w in raw_msg or w in norm_msg for w in ["odia", "ଓଡ଼ିଆ"]):
                target_lang = "or"
            elif any(w in raw_msg or w in norm_msg for w in ["assamese", "অসমীয়া"]):
                target_lang = "as"
            else:
                target_lang = "hi"

            memory["preferred_language"] = target_lang
            # Clear active scheme context so new language session is clean
            memory.pop("active_scheme_id", None)
            SESSION_MEMORY_STORE[session_id] = memory

            if target_lang == "hi":
                confirmation_text = "बिलकुल 😊 अब मैं आपसे हिंदी में बात करूँगा। मैं आपकी किस सरकारी योजना, लोन या दस्तावेज़ में मदद कर सकता हूँ?"
                suggested_questions = ["💡 मुझे नया बिज़नेस शुरू करना है", "PMEGP लोन के लिए क्या चाहिए?", "मेरी पात्रता चेक करें"]
            elif target_lang == "bn":
                confirmation_text = "অবশ্যই 😊 এখন থেকে আমরা বাংলায় কথা বলব। আমি আপনাকে সরকারি প্রকল্প বা ঋণের তথ্যে কীভাবে সাহায্য করতে পারি?"
                suggested_questions = ["💡 আমি ব্যবসা শুরু করতে চাই", "ঋণের সুদের হার কত?", "আবেদন কিভাবে করব?"]
            elif target_lang == "ta":
                confirmation_text = "நிச்சயமாக 😊 இனிமேல் நாம் தமிழில் பேசுவோம். அரசு திட்டங்கள் குறித்து உங்களுக்கு எப்படி உதவட்டும்?"
                suggested_questions = ["💡 நான் தொழில் தொடங்க வேண்டும்", "கடன் வட்டி விகிதம் என்ன?", "விண்ணப்பிப்பது எப்படி?"]
            elif target_lang == "te":
                confirmation_text = "ఖచ్చితంగా 😊 ఇప్పటి నుండి మనం తెలుగులో మాట్లాడుకుందాం. మీకు ఏ ప్రభుత్వ పథకం సహాయం కావాలి?"
                suggested_questions = ["💡 నేను వ్యాపారం ప్రారంభించాలనుకుంటున్నాను", "రుణ వడ్డీ రేటు ఎంత?", "అప్లై ఎలా చేయాలి?"]
            elif target_lang == "mr":
                confirmation_text = "नक्कीच 😊 आता आपण मराठीत बोलू. मी तुम्हाला कोणत्या सरकारी योजनेत मदत करू शकतो?"
                suggested_questions = ["💡 मला व्यवसाय सुरू करायचा आहे", "कर्जाचा व्याजदर किती आहे?", "अर्ज कसा करावा?"]
            else:
                confirmation_text = "Sure 😊 I will speak to you in English from now on. How can I assist you with government schemes, loan calculations, or required documents today?"
                suggested_questions = ["💡 I want to start a business", "🔎 Which schemes am I eligible for?", "💰 Calculate EMI for ₹2 Lakh loan"]

            return AIChatResponse(
                answer=confirmation_text,
                intent="LANGUAGE_CHANGE",
                response_mode="CASUAL",
                citations=[],
                actions=[],
                rich_cards=[],
                suggested_questions=suggested_questions,
                session_id=session_id,
                deterministic_used=False,
                financial_calculation=None,
                is_fallback=False,
                provider_name="system"
            )

        # -------------------------------------------------------------
        # Scheme Context Resolution (Strict Context Isolation)
        # -------------------------------------------------------------
        explicit_scheme_in_msg = None
        if "pmegp" in msg_lower or "pmegp" in norm_msg:
            explicit_scheme_in_msg = "SIH26092-001"
        elif "mudra" in msg_lower or "mudra" in norm_msg:
            explicit_scheme_in_msg = "SIH26092-002"
        elif "stand-up" in msg_lower or "stand up" in msg_lower or "standup" in norm_msg:
            explicit_scheme_in_msg = "SIH26092-003"
        elif "vishwakarma" in msg_lower or "vishwakarma" in norm_msg:
            explicit_scheme_in_msg = "SIH26092-005"
        elif "nsfdc" in msg_lower or "nsfdc" in norm_msg:
            explicit_scheme_in_msg = "SIH26092-004"

        if req.scheme_id:
            active_sid = req.scheme_id
            memory["active_scheme_id"] = active_sid
        elif page_ctx.get("scheme_id"):
            active_sid = page_ctx.get("scheme_id")
            memory["active_scheme_id"] = active_sid
        elif explicit_scheme_in_msg:
            active_sid = explicit_scheme_in_msg
            memory["active_scheme_id"] = active_sid
        else:
            # Contextual follow-up only if message explicitly references previous scheme
            has_pronoun_ref = bool(re.search(r"\b(?:isme|iske|iska|iski|usme|uska|uski|ye|yeh|this)\b", norm_msg or msg_lower))
            is_scheme_followup = intent in ("DOCUMENT_QUERY", "FINANCIAL_QUERY", "ELIGIBILITY_QUERY", "APPLICATION_QUERY")
            if (has_pronoun_ref or is_scheme_followup) and memory.get("active_scheme_id"):
                active_sid = memory.get("active_scheme_id")
            else:
                active_sid = None

        if intent in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY", "CASUAL_GREETING", "CASUAL_CONVERSATION", "IDENTITY_QUERY", "GENERAL_HELP", "EMOTIONAL_HELP"):
            memory.pop("active_scheme_id", None)
            active_sid = None

        actions: List[AICopilotAction] = []
        rich_cards: List[RichCard] = []
        citations: List[SourceCitation] = []
        suggested_questions: List[str] = []
        answer_parts: List[str] = []
        deterministic_used = False
        fin_calc_res: Optional[Dict[str, Any]] = None
        response_mode = "GROUNDED"

        # Structured debug log for intent decision
        rag_active = (intent not in CASUAL_INTENTS and intent not in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY", "SAVE_SCHEME", "SAVED_SCHEMES_LIST", "WHY_MATCH_QUERY"))
        logger.info(
            "AI Copilot Intent Decision -> RAW: %r | NORMALIZED: %r | INTENT: %s | HANDLER: %s | RAG: %s",
            raw_msg, norm_msg, intent, intent, str(rag_active).upper()
        )

        # -------------------------------------------------------------
        # 2. HARD ROUTING GATE FOR CASUAL, SMALL TALK & EMOTIONAL INTENTS
        # (0 RAG Calls, 0 Citations)
        # -------------------------------------------------------------
        if intent == "CASUAL_GREETING":
            response_mode = "CASUAL"
            if target_lang == "hi":
                answer_parts.append("नमस्ते! 🙏 मैं आपका योजनासेतु सहायक हूँ। आज मैं सरकारी योजनाएं, पात्रता और ऋण कैलकुलेटर खोजने में आपकी क्या मदद कर सकता हूँ?")
                suggested_questions = ["💡 मुझे नया बिज़नेस शुरू करना है", "🔎 मैं किस योजना के लिए पात्र हूँ?", "💰 ₹2 लाख का लोन चाहिए"]
            elif target_lang == "bn":
                answer_parts.append("নমস্কার! 👋 আমি আপনার যোজনাসেতু সহায়ক। আজ আপনাকে সরকারি কল্যাণমূলক প্রকল্প ও ঋণ সংক্রান্ত তথ্যে কীভাবে সাহায্য করতে পারি?")
                suggested_questions = ["💡 আমি ব্যবসা শুরু করতে চাই", "🔎 কোন প্রকল্পের জন্য আমি যোগ্য?", "💰 ঋণ দরকার"]
            elif target_lang == "ta":
                answer_parts.append("வணக்கம்! 👋 நான் உங்கள் யோஜனாசேது உதவியாளர். அரசு நலத்திட்டங்கள் மற்றும் கடன் உதவிகளைக் கண்டறிய உங்களுக்கு எவ்வாறு உதவட்டும்?")
                suggested_questions = ["💡 நான் தொழில் தொடங்க வேண்டும்", "🔎 எனக்கு என்ன திட்டம் பொருந்தும்?", "💰 கடன் உதவி தேவை"]
            elif target_lang == "te":
                answer_parts.append("నమస్కారం! 👋 నేను మీ యోజనాసేతు సహాయకుడిని. ప్రభుత్వ సంక్షేమ పథకాలను కనుగొనడంలో మీకు ఎలా సహాయపడగలను?")
                suggested_questions = ["💡 నేను వ్యాపారం ప్రారంభించాలనుకుంటున్నాను", "🔎 నాకు ఏ పథకం వర్తిస్తుంది?", "💰 రుణం కావాలి"]
            elif target_lang == "mr":
                answer_parts.append("नमस्कार! 👋 मी तुमचा योजनासेतू सहाय्यक आहे. सरकारी योजना आणि कर्ज माहिती शोधण्यात मी तुम्हाला कशी मदत करू शकतो?")
                suggested_questions = ["💡 मला व्यवसाय सुरू करायचा आहे", "🔎 मी कोणत्या योजनेसाठी पात्र आहे?", "💰 कर्जाची गरज आहे"]
            else:
                answer_parts.append("Namaste! 👋 I am your YojnaSetu Assistant. How can I help you discover government schemes, eligibility rules, and loan options today?")
                suggested_questions = ["💡 I want to start a small business", "🔎 Which schemes am I eligible for?", "💰 I need a ₹2 lakh loan"]

        elif intent == "IDENTITY_QUERY":
            response_mode = "CASUAL"
            if target_lang == "hi":
                answer_parts.append("मैं योजनासेतु का एआई नागरिक सहायक हूँ। मेरा उद्देश्य भारतीय नागरिकों को आधिकारिक सरकारी योजनाओं, सब्सिडी, पात्रता और ऋण कैलकुलेटर से जोड़ना है।")
            elif target_lang == "bn":
                answer_parts.append("আমি যোজনাসেতুর AI নাগরিক সহায়ক। ভারতীয় নাগরিকদের সরকারি প্রকল্প, ভরতুকি ও ঋণের তথ্যের সাথে যুক্ত করাই আমার উদ্দেশ্য।")
            else:
                answer_parts.append("I am the YojnaSetu AI Citizen Assistant. My purpose is to help Indian citizens discover official government schemes, verify eligibility guidelines, calculate loan EMIs, and access official application portals.")
            suggested_questions = [
                "💡 I want to start a small business",
                "🔎 Show schemes for women entrepreneurs",
                "💰 How to apply for PMEGP loan?"
            ]

        elif intent == "LANGUAGE_CHANGE":
            response_mode = "CASUAL"
            detected_target = "hi"
            msg_str = (norm_msg or "") + " " + (msg_lower or "") + " " + (raw_msg or "")
            if re.search(r"\b(?:english|eng|angrezi|अंग्रेज़ी)\b", msg_str, re.IGNORECASE):
                detected_target = "en"
            elif re.search(r"\b(?:bengali|bangla|বাংলা)\b", msg_str, re.IGNORECASE):
                detected_target = "bn"
            elif re.search(r"\b(?:tamil|தமிழ்)\b", msg_str, re.IGNORECASE):
                detected_target = "ta"
            elif re.search(r"\b(?:telugu|తెలుగు)\b", msg_str, re.IGNORECASE):
                detected_target = "te"
            elif re.search(r"\b(?:marathi|मराठी)\b", msg_str, re.IGNORECASE):
                detected_target = "mr"
            elif re.search(r"\b(?:gujarati|ગુજરાતી)\b", msg_str, re.IGNORECASE):
                detected_target = "gu"
            elif re.search(r"\b(?:kannada|ಕನ್ನಡ)\b", msg_str, re.IGNORECASE):
                detected_target = "kn"
            elif re.search(r"\b(?:malayalam|മലയാളം)\b", msg_str, re.IGNORECASE):
                detected_target = "ml"
            elif re.search(r"\b(?:punjabi|ਪੰਜਾਬੀ)\b", msg_str, re.IGNORECASE):
                detected_target = "pa"
            elif re.search(r"\b(?:odia|ଓଡ଼ିଆ)\b", msg_str, re.IGNORECASE):
                detected_target = "or"
            elif re.search(r"\b(?:assamese|অসমীয়া)\b", msg_str, re.IGNORECASE):
                detected_target = "as"
            else:
                detected_target = "hi"

            # Persist language preference in session memory
            memory["preferred_language"] = detected_target
            SESSION_MEMORY_STORE[session_id] = memory
            target_lang = detected_target

            # 0 RAG, 0 Citations, 0 Scheme Cards, clean friendly localized response
            if detected_target == "hi":
                answer_parts.append("जी बिल्कुल! 😊 अब से हम हिंदी में बात करेंगे। आप सरकारी योजनाओं, पात्रता, आवश्यक दस्तावेज़ या ऋण के बारे में पूछ सकते हैं।")
                suggested_questions = [
                    "💡 मुझे नया बिज़नेस शुरू करना है",
                    "🔎 मैं किस योजना के लिए पात्र हूँ?",
                    "📄 क्या दस्तावेज़ लगेंगे?",
                    "💰 ₹2 लाख का लोन चाहिए"
                ]
            elif detected_target == "en":
                answer_parts.append("Sure! 😊 I will speak with you in English from now on. You can ask about government schemes, eligibility rules, required documents, or loan EMIs.")
                suggested_questions = [
                    "💡 I want to start a small business",
                    "🔎 Which schemes might I qualify for?",
                    "📄 What documents do I need?",
                    "💰 I need a ₹2 lakh loan"
                ]
            elif detected_target == "bn":
                answer_parts.append("অবশ্যই! 😊 এখন থেকে আমরা বাংলায় কথা বলব। আপনি সরকারি প্রকল্প, যোগ্যতা, প্রয়োজনীয় কাগজপত্র বা ঋণ সম্পর্কে জিজ্ঞাসা করতে পারেন।")
                suggested_questions = ["💡 আমি ব্যবসা শুরু করতে চাই", "🔎 কোন প্রকল্পের জন্য যোগ্য?", "📄 কী কী কাগজপত্র লাগবে?"]
            elif detected_target == "ta":
                answer_parts.append("நிச்சயமாக! 😊 இனி நாம் தமிழில் பேசுவோம். அரசு திட்டங்கள், தகுதி, தேவையான ஆவணங்கள் அல்லது கடன் பற்றி நீங்கள் கேட்கலாம்.")
                suggested_questions = ["💡 நான் தொழில் தொடங்க வேண்டும்", "🔎 என்ன திட்டம் பொருந்தும்?", "📄 என்ன ஆவணங்கள் தேவை?"]
            elif detected_target == "te":
                answer_parts.append("తప్పకుండా! 😊 ఇకపై మనం తెలుగులో మాట్లాడదాం. మీరు ప్రభుత్వ పథకాలు, అర్హతలు, అవసరమైన పత్రాలు లేదా రుణాల గురించి అడగవచ్చు.")
                suggested_questions = ["💡 వ్యాపారం ప్రారంభించాలనుకుంటున్నాను", "🔎 ఏ పథకం వర్తిస్తుంది?", "📄 ఏ పత్రాలు కావాలి?"]
            elif detected_target == "mr":
                answer_parts.append("नक्कीच! 😊 आतापासून आपण मराठीत बोलू. तुम्ही सरकारी योजना, पात्रता, आवश्यक कागदपत्रे किंवा कर्जाबद्दल विचारू शकता.")
                suggested_questions = ["💡 मला व्यवसाय सुरू करायचा आहे", "🔎 कोणती योजना योग्य आहे?", "📄 कोणती कागदपत्रे लागतील?"]
            elif detected_target == "gu":
                answer_parts.append("ચોક્કસ! 😊 હવેથી આપણે ગુજરાતીમાં વાત કરીશું. તમે સરકારી યોજનાઓ, પાત્રતા, જરૂરી દસ્તાવેજો અથવા લોન વિશે પૂછી શકો છો.")
                suggested_questions = ["💡 મારે વ્યવસાય શરૂ કરવો છે", "🔎 કઈ યોજના મળશે?", "📄 કયા દસ્તાવેજો જોઈએ?"]
            else:
                answer_parts.append("जी बिल्कुल! 😊 अब से हम आपकी चुनी हुई भाषा में बात करेंगे। आप सरकारी योजनाओं या ऋण के बारे में पूछ सकते हैं।")
                suggested_questions = ["💡 मुझे नया बिज़नेस शुरू करना है", "🔎 कौन सी योजना मिलेगी?", "💰 लोन कैसे मिलेगा?"]

        elif intent == "EMOTIONAL_HELP":
            response_mode = "CASUAL"
            if target_lang == "hi":
                answer_parts.append(
                    "कोई दिक्कत नहीं 😊 मैं स्टेप-बाय-स्टेप आपकी मदद करता हूँ।\n\n"
                    "आपको नई योजना खोजनी है, किसी बिज़नेस के लिए लोन चाहिए, या आवश्यक दस्तावेज़ों की सूची देखनी है?"
                )
                suggested_questions = [
                    "💡 मुझे नया बिज़नेस शुरू करना है",
                    "PMEGP योजना के बारे में बताओ",
                    "लोन के लिए क्या दस्तावेज़ लगेंगे?"
                ]
            else:
                answer_parts.append(
                    "Koi dikkat nahi 😊 Main step-by-step help karta hoon.\n\n"
                    "Aapko nayi scheme chahiye, kisi business ke liye loan chahiye, ya document checklist ke baare mein jaanna hai?"
                )
                suggested_questions = [
                    "💡 I want to start a business",
                    "PMEGP scheme ke baare mein batao",
                    "Loan ke liye kya documents lagenge?"
                ]

        elif intent == "CASUAL_CONVERSATION":
            response_mode = "CASUAL"
            # Casual frustration / feedback ("nhi chal rha h bhaiii", "nahi chal raha", "not working")
            if any(term in msg_lower or term in norm_msg for term in ["nahi chal raha", "nhi chal rha", "not working", "chal nahi raha", "kaam nahi kar raha", "kuch nahi chal raha"]):
                if target_lang == "hi":
                    answer_parts.append("अरे 😅 समझ गया! मैं स्टेप-बाय-स्टेप आपकी मदद करता हूँ। बताइए आपको किस चीज़ में मदद चाहिए — नया बिज़नेस लोन, योजनाएं खोजना, या आवश्यक दस्तावेज़?")
                    suggested_questions = [
                        "💡 मुझे नया बिज़नेस शुरू करना है",
                        "PMEGP योजना के बारे में बताओ",
                        "लोन के लिए क्या दस्तावेज़ लगेंगे?"
                    ]
                else:
                    answer_parts.append("Arre 😅 samajh gaya! Main step-by-step help karta hoon. Batao, kis cheez mein help chahiye — business loans, government schemes, ya document checklist?")
                    suggested_questions = [
                        "💡 I want to start a business",
                        "Tell me about PMEGP scheme",
                        "What documents are needed for loan?"
                    ]
            elif any(term in msg_lower for term in ["fool", "stupid", "dumb", "gadhe", "gadha", "ullu", "pagal"]):
                if target_lang == "hi":
                    answer_parts.append("अरे नहीं 😄! मैं आपकी पूरी मदद करने की कोशिश करूँगा। बताइए आपको क्या जानकारी चाहिए — बिज़नेस लोन, योजनाएं या डॉक्यूमेंट्स?")
                else:
                    answer_parts.append("Haha, I'll try my best! 😄 Tell me what you need help with — business loans, scheme discovery, or document checklists.")
            elif "love" in msg_lower:
                answer_parts.append("Thank you! 😊 I'm always here to help you navigate government schemes and loan guidance.")
            elif "kaise ho" in msg_lower or "how are you" in msg_lower or "how r u" in msg_lower:
                answer_parts.append("I'm doing great! 😊 What are you looking for today — a business scheme, loan, scholarship, subsidy, or something else?")
            elif any(term in msg_lower for term in ["thanks", "thank you", "shukriya"]):
                answer_parts.append("You're very welcome! 🙏 Feel free to ask if you need help checking eligibility or loan EMIs.")
            elif any(term in msg_lower for term in ["bye", "goodbye"]):
                answer_parts.append("Goodbye! 👋 Have a great day ahead. Best of luck with your scheme applications!")
            else:
                if target_lang == "hi":
                    answer_parts.append("नमस्ते! 👋 बताइए मैं आपकी क्या मदद करूँ — सरकारी योजनाएं खोजना, बिज़नेस लोन, पात्रता या दस्तावेज़?")
                else:
                    answer_parts.append("Namaste! 👋 Tell me what you are looking for — government schemes, business loans, eligibility guidelines, or document checklists.")

            if not suggested_questions:
                suggested_questions = [
                    "💡 I want to start a business",
                    "🔎 Find schemes for SC entrepreneurs",
                    "💰 Calculate EMI for ₹1 Lakh loan"
                ]

        elif intent == "GENERAL_HELP":
            response_mode = "CASUAL"
            if target_lang == "hi":
                answer_parts.append(
                    "मैं आपकी इन तरीकों से मदद कर सकता हूँ:\n\n"
                    "1. **सरकारी योजनाएं खोजें**: अपना राज्य, श्रेणी और व्यापार विवरण दर्ज करें।\n"
                    "2. **पात्रता जाँचें**: देखें कि क्या आप उम्र, आय और श्रेणी मानदंडों को पूरा करते हैं।\n"
                    "3. **ऋण और ईएमआई कैलकुलेटर**: अपनी मासिक किस्तों का अनुमान लगाएं।\n"
                    "4. **दस्तावेज़ मार्गदर्शन**: आवश्यक दस्तावेज़ों की सूची देखें।\n"
                    "5. **आधिकारिक पोर्टल आवेदन**: सुरक्षित और सत्यापित सरकारी पोर्टल लिंक प्राप्त करें।"
                )
            else:
                answer_parts.append(
                    "Here is how I can guide you:\n\n"
                    "1. **Find Government Schemes**: Enter your state, category, and business need to get personalized recommendations.\n"
                    "2. **Check Eligibility**: Verify if you appear to meet age, income, and category criteria.\n"
                    "3. **Calculate Loan & EMI**: Estimate monthly installments using our financial engine.\n"
                    "4. **Document Guidance**: Review required document checklists.\n"
                    "5. **Official Application Portal**: Get safe, verified links to apply on official government portals."
                )
            suggested_questions = [
                "💡 I want to start a business",
                "🔎 Am I eligible for PMEGP?",
                "💰 Calculate EMI for ₹2 Lakh loan"
            ]

        elif intent == "SAVE_SCHEME":
            if not current_user_id:
                response_mode = "CLARIFICATION"
                answer_parts.append("Sure — login once to your YojnaSetu account and I'll save it for you! 👍")
                actions.append(AICopilotAction(label="Sign In", action_type="VIEW_SCHEME", target_url="/login"))
            else:
                target_sid = active_sid or "SIH26092-001"
                from app.models.saved_scheme import SavedScheme
                scheme_obj = db.query(Scheme).filter(Scheme.scheme_id == target_sid).first()
                scheme_name = scheme_obj.scheme_name if scheme_obj else target_sid
                existing = db.query(SavedScheme).filter(SavedScheme.user_id == current_user_id, SavedScheme.scheme_id == target_sid).first()
                if not existing:
                    db.add(SavedScheme(user_id=current_user_id, scheme_id=target_sid))
                    db.commit()
                response_mode = "TOOL_RESULT"
                deterministic_used = True
                answer_parts.append(f"Done 👍 I've saved **{scheme_name}** to your Saved Schemes.")
                actions.append(AICopilotAction(label="View Saved Schemes", action_type="VIEW_SCHEME", target_url="/saved-schemes"))

        elif intent == "SAVED_SCHEMES_LIST":
            if not current_user_id:
                response_mode = "CLARIFICATION"
                answer_parts.append("Please sign in to view your saved schemes.")
                actions.append(AICopilotAction(label="Sign In", action_type="VIEW_SCHEME", target_url="/login"))
            else:
                from app.models.saved_scheme import SavedScheme
                saved_items = db.query(SavedScheme).filter(SavedScheme.user_id == current_user_id).order_by(SavedScheme.created_at.desc()).all()
                response_mode = "TOOL_RESULT"
                deterministic_used = True
                if not saved_items:
                    answer_parts.append("You don't have any saved schemes yet. Browse schemes and click **♡ Save Scheme** to save them for later! 👍")
                else:
                    answer_parts.append(f"Sure! You have **{len(saved_items)}** saved scheme(s) in your YojnaSetu account:\n")
                    for s in saved_items:
                        s_name = s.scheme.scheme_name if s.scheme else s.scheme_id
                        answer_parts.append(f"• **{s_name}** ({s.scheme.ministry if s.scheme else 'Government of India'})")
                    actions.append(AICopilotAction(label="Open Saved Schemes Page", action_type="VIEW_SCHEME", target_url="/saved-schemes"))

        elif intent == "WHY_MATCH_QUERY":
            response_mode = "CASUAL"
            st = extracted_facts.get("state", "India")
            cat = extracted_facts.get("social_category", "listed category")
            act = extracted_facts.get("business_description", "business project")
            answer_parts.append(
                f"Isse aapko isliye suggest kiya gaya kyunki aapka profile (Location: {st}, Category: {cat}, Activity: {act}) "
                f"scheme ke official beneficiary criteria aur funding range se closely match karta hai. 👍"
            )

        # -------------------------------------------------------------
        # 3. CONVERSATIONAL SCHEME DISCOVERY & PROGRESSIVE PROFILING
        # -------------------------------------------------------------

        elif intent in ("SCHEME_DISCOVERY", "BUSINESS_PROFILE_INIT", "PROFILE_CORRECTION", "RECOMMENDATION_QUERY"):
            state_val = extracted_facts.get("state") or (req.profile.state if req.profile and req.profile.state != "ALL_INDIA" else None)
            cat_val = extracted_facts.get("social_category") or (req.profile.social_category if req.profile else None)
            inc_val = extracted_facts.get("annual_income") or (req.profile.annual_income if req.profile and req.profile.annual_income > 0 else None)
            act_val = extracted_facts.get("business_description") or extracted_facts.get("activity_type") or (getattr(req.profile, "activity_type", None) or getattr(req.profile, "occupation", None) or getattr(req.profile, "applicant_type", None) if req.profile else None)

            if not state_val:
                response_mode = "CLARIFICATION"
                if target_lang == "hi":
                    answer_parts.append(
                        "बिलकुल! 👍 मैं आपके प्रोफाइल के हिसाब से suitable government schemes ढूँढता हूँ।\n\n"
                        "बस 1-2 डिटेल्स बता दीजिए:\n"
                        "1. आप किस State से हैं?"
                    )
                    suggested_questions = ["Uttar Pradesh", "Bihar", "Maharashtra", "Delhi"]
                else:
                    answer_parts.append(
                        "Bilkul! 👍 Main aapke profile ke hisaab se suitable government schemes find karta hoon.\n\n"
                        "Bas 1-2 details bata dijiye:\n"
                        "1. Aap kis State se hain?"
                    )
                    suggested_questions = ["Uttar Pradesh", "Bihar", "Maharashtra", "Delhi"]

            elif not cat_val:
                response_mode = "CLARIFICATION"
                if target_lang == "hi":
                    answer_parts.append(
                        f"बहुत बढ़िया! ({state_val}) 👍\n\n"
                        "2. आपकी Social Category क्या है — General, OBC, SC, या ST?"
                    )
                    suggested_questions = ["SC", "ST", "OBC", "General"]
                else:
                    answer_parts.append(
                        f"Got it! ({state_val}) 👍\n\n"
                        "2. Which social category do you belong to — General, OBC, SC, or ST?"
                    )
                    suggested_questions = ["SC", "ST", "OBC", "General"]

            elif not inc_val:
                response_mode = "CLARIFICATION"
                if target_lang == "hi":
                    answer_parts.append(
                        "3. आपकी approximate annual family income कितनी है?"
                    )
                    suggested_questions = ["Below ₹1 Lakh", "₹1 - 2 Lakhs", "₹2 - 5 Lakhs", "Above ₹5 Lakhs"]
                else:
                    answer_parts.append(
                        "3. What is your approximate annual family income?"
                    )
                    suggested_questions = ["Below ₹1 Lakh", "₹1 - 2 Lakhs", "₹2 - 5 Lakhs", "Above ₹5 Lakhs"]

            elif not act_val:
                response_mode = "CLARIFICATION"
                if target_lang == "hi":
                    answer_parts.append(
                        "4. आप किस प्रकार का बिज़नेस शुरू या बढ़ाना चाहते हैं? (जैसे tailoring, retail shop, dairy farming, manufacturing, etc.)"
                    )
                    suggested_questions = ["Tailoring / Stitching", "Dairy Farming", "Retail Shop", "Manufacturing"]
                else:
                    answer_parts.append(
                        "4. What type of business would you like to start or expand? (e.g. tailoring, retail shop, dairy farming, manufacturing, etc.)"
                    )
                    suggested_questions = ["Tailoring / Stitching", "Dairy Farming", "Retail Shop", "Manufacturing"]

            else:
                response_mode = "TOOL_RESULT"
                profile = cls.build_profile_from_memory(session_id, req.profile)
                rec_out = CopilotTools.get_recommendations(db, profile, top_k=3)
                deterministic_used = True
                recs = rec_out.get("recommendations", [])

                if target_lang == "hi":
                    answer_parts.append(
                        f"आपकी जानकारी के आधार पर (State: {state_val}, Category: {cat_val}), ये official government schemes आपके लिए सबसे suitable हैं:"
                    )
                else:
                    answer_parts.append(
                        f"Based on the details you shared (State: {state_val}, Category: {cat_val}), here are the official government schemes that match your profile:"
                    )

                for idx, item in enumerate(recs, 1):
                    score_val = item.get("score", item.get("soft_score", 90))
                    match_pct = int(score_val)
                    answer_parts.append(
                        f"**{idx}. {item['scheme_name']}** — *{match_pct}% Profile Match*\n"
                        f"• **Ministry**: {item.get('ministry', 'Government of India')}\n"
                        f"• **Facility**: {item.get('financial_category', 'Assistance')}\n"
                        f"• **Key Benefit**: {item.get('purpose', item.get('short_description', 'Financial support'))[:120]}..."
                    )
                    actions.append(AICopilotAction(
                        label=f"Apply on Official Portal",
                        action_type="VIEW_SCHEME",
                        target_url=f"/schemes/{item['scheme_id']}"
                    ))
                    rich_cards.append(RichCard(
                        card_type="SCHEME_CARD",
                        title=item["scheme_name"],
                        subtitle=f"Match: {match_pct}% | Meets Listed Criteria",
                        data=item
                    ))

                suggested_questions = [
                    "What documents are required?",
                    "Calculate EMI for ₹2 Lakh loan",
                    "How to apply for this scheme?"
                ]

        # -------------------------------------------------------------
        # 4. GROUNDED TOOL & RAG ROUTING
        # -------------------------------------------------------------
        else:
            profile = cls.build_profile_from_memory(session_id, req.profile)
            hybrid_rag = HybridSchemeRAG(db)

            target_sid = active_sid
            target_scheme = db.query(Scheme).filter(Scheme.scheme_id == target_sid).first() if target_sid else None
            is_credit_target = target_scheme.is_credit_scheme if (target_scheme and target_scheme.is_credit_scheme is not None) else True

            if intent == "FINANCIAL_QUERY":
                response_mode = "TOOL_RESULT"
                req_loan = extracted_facts.get("requested_loan_amount", 200000.0)
                interest_rate = extracted_facts.get("custom_interest_rate", 7.0)
                tenure_months = extracted_facts.get("custom_tenure_months", 60)

                # Standard EMI formula calculation
                r_monthly = (interest_rate / 100.0) / 12.0
                if r_monthly > 0:
                    emi_val = (req_loan * r_monthly * ((1.0 + r_monthly) ** tenure_months)) / (((1.0 + r_monthly) ** tenure_months) - 1.0)
                else:
                    emi_val = req_loan / tenure_months

                if target_sid and target_scheme:
                    if not is_credit_target:
                        answer_parts.append(
                            f"**Loan Facility Not Applicable for '{target_scheme.scheme_name}'**:\n\n"
                            f"This scheme does not provide a loan or credit facility. Financial support is provided directly as a **grant, subsidy, scholarship, or statutory welfare entitlement**.\n"
                            f"• Benefit Description: {target_scheme.benefit_description or 'Direct Financial Assistance'}"
                        )
                    else:
                        calc_out = CopilotTools.calculate_financials(db, target_sid, project_cost=req_loan*1.25, requested_loan_amount=req_loan)
                        fin_calc_res = calc_out
                        deterministic_used = True

                        actual_loan = calc_out.get("eligible_loan_amount")
                        actual_rate = calc_out.get("interest_rate") or target_scheme.interest_rate
                        actual_emi = calc_out.get("periodic_installment")
                        actual_tenure = calc_out.get("repayment_period_months") or target_scheme.repayment_period_max_months

                        if actual_rate is not None:
                            rate_desc = f"{actual_rate}% p.a." if actual_rate > 0 else "0% (Interest-Free)"
                        else:
                            rate_desc = "As determined by financing institution / not specified in available official guidelines"

                        if actual_loan is not None:
                            loan_desc = f"₹{actual_loan:,.0f}"
                        else:
                            loan_desc = f"₹{req_loan:,.0f} (subject to project appraisal)"

                        if actual_emi is not None and actual_tenure:
                            emi_desc = f"Estimated Monthly EMI: ₹{actual_emi:,.0f} over {actual_tenure} months ({actual_tenure//12} years)"
                        elif actual_tenure:
                            emi_desc = f"Repayment tenure: up to {actual_tenure} months ({actual_tenure//12} years)"
                        else:
                            emi_desc = "Repayment tenure: Not specified in available official guidelines"

                        sub_desc = f"\n• Subsidy: {target_scheme.subsidy_percentage}% on eligible project cost" if target_scheme.subsidy_percentage else ""

                        answer_parts.append(
                            f"Official Financial Estimation for '{target_scheme.scheme_name}':\n\n"
                            f"• Loan Amount: {loan_desc}\n"
                            f"• Interest Rate: {rate_desc}\n"
                            f"• {emi_desc}{sub_desc}"
                        )
                        actions.append(AICopilotAction(
                            label=f"Open EMI Calculator",
                            action_type="CALCULATE_EMI",
                            target_url=f"/calculator?scheme={target_sid}"
                        ))
                        rich_cards.append(RichCard(
                            card_type="FINANCIAL_CARD",
                            title=f"Loan Calculation — {target_scheme.scheme_name}",
                            data=calc_out
                        ))
                else:
                    deterministic_used = True
                    fin_calc_res = {
                        "scheme_name": "General Financial Estimation",
                        "eligible_loan_amount": req_loan,
                        "interest_rate": interest_rate,
                        "periodic_installment": emi_val,
                        "repayment_period_months": tenure_months,
                        "total_repayment": emi_val * tenure_months,
                    }
                    answer_parts.append(
                        f"Financial Estimation for ₹{req_loan:,.0f} Loan at {interest_rate}% for {tenure_months//12} years ({tenure_months} months):\n\n"
                        f"• Loan Amount: ₹{req_loan:,.0f}\n"
                        f"• Interest Rate: {interest_rate}% p.a.\n"
                        f"• Estimated Monthly EMI: ₹{emi_val:,.0f}\n"
                        f"• Total Repayment: ₹{(emi_val * tenure_months):,.0f}\n\n"
                        f"* Specify a government scheme (e.g. PMEGP, MUDRA, Stand-Up India) to evaluate capital subsidies and interest subvention."
                    )
                    actions.append(AICopilotAction(
                        label="Open Financial Calculator",
                        action_type="CALCULATE_EMI",
                        target_url="/calculator"
                    ))

            elif intent == "ELIGIBILITY_QUERY":
                response_mode = "TOOL_RESULT"
                if target_sid and target_scheme:
                    elig_out = CopilotTools.check_eligibility(db, target_sid, profile)
                    deterministic_used = True

                    status_str = "You appear to meet the listed criteria" if elig_out["is_eligible"] else "Requirements to verify"
                    answer_parts.append(
                        f"Eligibility Guidance (Deterministic Eligibility Evaluation) for '{elig_out['scheme_name']}':\n"
                        f"• Status: Based on the information provided, {status_str.lower()}.\n"
                        f"• Details: {'; '.join(elig_out.get('explanations', []))}\n\n"
                        f"Note: Final eligibility is determined exclusively by the concerned government department."
                    )
                    rich_cards.append(RichCard(
                        card_type="ELIGIBILITY_CARD",
                        title=f"Eligibility Guidance — {elig_out['scheme_name']}",
                        subtitle=status_str,
                        data=elig_out
                    ))
                else:
                    response_mode = "CLARIFICATION"
                    answer_parts.append(
                        "Which scheme's eligibility would you like to check? You can ask about schemes like **PMEGP**, **PM MUDRA**, **PM Vishwakarma**, or **Stand-Up India**."
                    )
                    suggested_questions = [
                        "Am I eligible for PMEGP?",
                        "Am I eligible for MUDRA Loan?",
                        "Am I eligible for PM Vishwakarma?"
                    ]

            elif intent == "DOCUMENT_QUERY":
                if not target_sid or not target_scheme:
                    response_mode = "CLARIFICATION"
                    if target_lang == "hi":
                        answer_parts.append(
                            "जी बिल्कुल! 👍 आप किस योजना की दस्तावेज़ सूची (Document Checklist) जानना चाहते हैं?\n\n"
                            "अगर आप मुझे योजना का नाम बता दें (जैसे **PMEGP**, **PM MUDRA**, या **PM Vishwakarma**), तो मैं उसकी verified document checklist दिखा दूंगा।"
                        )
                        suggested_questions = [
                            "PMEGP के लिए क्या-क्या दस्तावेज़ चाहिए?",
                            "MUDRA लोन के दस्तावेज़ बताओ",
                            "PM Vishwakarma दस्तावेज़ सूची"
                        ]
                    else:
                        answer_parts.append(
                            "Sure! 👍 Which scheme's required document checklist would you like to view?\n\n"
                            "Please specify the scheme name (e.g. **PMEGP**, **PM MUDRA**, or **PM Vishwakarma**), and I will show you its verified document checklist."
                        )
                        suggested_questions = [
                            "What documents are needed for PMEGP?",
                            "What documents are needed for PM MUDRA?",
                            "Documents for PM Vishwakarma"
                        ]
                else:
                    response_mode = "GROUNDED"
                    details = CopilotTools.get_scheme_details(db, target_sid)
                    if details:
                        doc_list = [f"• ✓ {d['document_name']} ({d['requirement_type']})" for d in details.get("documents", [])]
                        answer_parts.append(
                            f"Official Document Requirement Guidance for '{details['scheme_name']}':\n\n" + "\n".join(doc_list) +
                            "\n\n* Final document requirements may vary by issuing office. Please verify on the official government portal."
                        )
                        actions.append(AICopilotAction(
                            label=f"View Official Scheme Portal",
                            action_type="VIEW_DOCUMENTS",
                            target_url=f"/schemes/{target_sid}"
                        ))
                        rich_cards.append(RichCard(
                            card_type="DOCUMENT_CHECKLIST",
                            title=f"Document Guidance — {details['scheme_name']}",
                            data={"documents": details.get("documents", [])}
                        ))

            elif intent == "APPLICATION_QUERY":
                response_mode = "GROUNDED"
                scheme_name_str = target_scheme.scheme_name if target_scheme else "government schemes"
                target_url_str = f"/schemes/{target_sid}" if target_sid else "/schemes"
                answer_parts.append(
                    f"Application Guidance & Official Routing for '{scheme_name_str}':\n\n"
                    "1. **Review Eligibility**: Verify that you meet the age, income, and category criteria.\n"
                    "2. **Prepare Document Checklist**: Gather required documents (Aadhaar, income proof, caste certificate, project report).\n"
                    "3. **Open Official Portal**: Click 'Apply on Official Portal' to navigate to the official government portal.\n"
                    "4. **Visit Channel Partner**: Visit an authorized bank branch or DIC office for physical application submission."
                )
                actions.append(AICopilotAction(
                    label=f"Apply on Official Portal",
                    action_type="VIEW_SCHEME",
                    target_url=target_url_str
                ))

            elif intent == "PARTNER_DISCOVERY":
                response_mode = "TOOL_RESULT"
                scheme_name_str = target_scheme.scheme_name if target_scheme else "government schemes"
                target_url_str = f"/locator?scheme={target_sid}" if target_sid else "/locator"
                deterministic_used = True
                answer_parts.append(
                    f"Authorized Channel Partners for '{scheme_name_str}':\n\n"
                    "• **Nodal Agency**: District Industries Centre (DIC) / KVIC Regional Office\n"
                    "• **Sanctioning Partners**: Public Sector Banks & Regional Rural Banks (RRBs)\n"
                    "• **Digital Assistance Outlets**: Common Service Centres (CSC)\n\n"
                    "You can locate authorized bank branches and channel partner offices near your location."
                )
                actions.append(AICopilotAction(
                    label=f"Locate Nearby Partner",
                    action_type="LOCATE_PARTNER",
                    target_url=target_url_str
                ))

            elif intent == "SCHEME_COMPARISON":
                response_mode = "GROUNDED"
                answer_parts.append(
                    "Key Comparison of Business Assistance Schemes:\n\n"
                    "• **PMEGP**: Credit-linked capital subsidy (15%-35%) for new micro-enterprises. Manufacturing up to ₹50L, Service up to ₹20L.\n"
                    "• **PM MUDRA Yojana**: Collateral-free loan up to ₹10L for micro-enterprises without capital subsidy (Shishu, Kishore, Tarun).\n"
                    "• **PM Vishwakarma**: Financial & skill support up to ₹3L at 5% interest rate for traditional artisans."
                )
                actions.append(AICopilotAction(
                    label=f"Compare Schemes",
                    action_type="VIEW_SCHEME",
                    target_url="/compare"
                ))

            else:
                # Grounded Scheme Search with RAG
                citations = hybrid_rag.hybrid_search(
                    query=raw_msg,
                    scheme_id=target_sid,
                    state=extracted_facts.get("state"),
                    category=extracted_facts.get("social_category"),
                    top_k=3
                )
                if citations:
                    response_mode = "GROUNDED"
                    grounded_ctx = hybrid_rag.build_grounded_context(citations)
                    top_cite = citations[0]

                    system_instructions = (
                        "You are YojnaSetu AI Assistant, an authoritative Indian government scheme helper. "
                        "You must answer the user's question using ONLY the provided official scheme documents. "
                        "Do NOT invent any benefits, eligibility rules, interest rates, or document requirements not present in the context. "
                        "If the answer is not present in the context, state: 'I couldn't verify this information from the available official scheme data.'\n\n"
                        f"GROUNDED CONTEXT:\n{grounded_ctx}"
                    )
                    
                    try:
                        provider = get_ai_provider()
                        synthesized_answer = provider.generate(
                            prompt=f"User Question: {raw_msg}\n\nLanguage: {target_lang}\nAnswer concisely, warmly, and factually based ONLY on the grounded context.",
                            system_prompt=system_instructions
                        )
                    except Exception as err:
                        logger.warning("AI provider generation error: %s. Falling back to grounded context synthesis.", err)
                        synthesized_answer = None

                    if synthesized_answer and "error" not in synthesized_answer.lower() and "notice:" not in synthesized_answer.lower():
                        answer_parts.append(synthesized_answer)
                    else:
                        clean_snippet = top_cite.snippet
                        for header in [
                            "Scheme Name:", "Scheme Code:", "Rule Code:", "Requirement Field:",
                            "Scheme:", "Field:", "Ministry/Department:", "Purpose/Objective:",
                            "Target Beneficiaries:", "Social Category:", "Gender Condition:",
                            "State Coverage:", "Financial Category:", "Maximum Loan Facility:",
                            "Interest Rate:", "Capital Subsidy:", "Repayment Tenure:",
                            "Application Mode:", "Official Government Portal:", "Verification Status:"
                        ]:
                            clean_snippet = clean_snippet.replace(header, "")
                        clean_snippet = re.sub(r"\s+", " ", clean_snippet).strip()
                        answer_parts.append(f"Official verified information for **{top_cite.scheme_name}**:\n\n{clean_snippet}")

                    if target_sid:
                        actions.append(AICopilotAction(
                            label=f"View Scheme Details",
                            action_type="VIEW_SCHEME",
                            target_url=f"/schemes/{target_sid}"
                        ))
                else:
                    # Proper Fallback Category for UNKNOWN (0 RAG, 0 Citations)
                    response_mode = "CLARIFICATION"
                    if target_lang == "hi":
                        answer_parts.append(
                            "मैं आपकी बात समझ नहीं पाया 🤔\n\n"
                            "आप इनमें से क्या जानकारी जानना चाहते हैं?\n"
                            "1. नया बिज़नेस शुरू करने के लिए योजनाएं खोजना\n"
                            "2. किसी विशेष योजना की पात्रता या दस्तावेज़ जानना (जैसे PMEGP, MUDRA)\n"
                            "3. लोन और EMI कैलकुलेट करना\n\n"
                            "कृपया अपना सवाल थोड़ा स्पष्ट लिखकर बताएं!"
                        )
                    else:
                        answer_parts.append(
                            "I'm not quite sure I understood that 🤔\n\n"
                            "How can I assist you today?\n"
                            "1. Discover schemes to start or expand a business\n"
                            "2. Check eligibility or documents for a specific scheme (e.g. PMEGP, MUDRA)\n"
                            "3. Calculate loan EMI and subsidies\n\n"
                            "Please feel free to ask a specific question!"
                        )

            # Dynamic suggested questions
            if target_scheme:
                if is_credit_target:
                    if target_lang == "hi":
                        suggested_questions = ["ब्याज दर कितनी है?", "कितना लोन मिल सकता है?", "क्या दस्तावेज चाहिए?", "आवेदन कैसे करें?"]
                    else:
                        suggested_questions = ["What's the interest rate?", "How much loan can I get?", "What documents are required?", "How do I apply?"]
                else:
                    if target_lang == "hi":
                        suggested_questions = ["कौन पात्र है?", "क्या लाभ मिलते हैं?", "क्या दस्तावेज चाहिए?", "आवेदन कैसे करें?"]
                    else:
                        suggested_questions = ["Who is eligible?", "What benefits are provided?", "What documents are required?", "How do I apply?"]
            elif not suggested_questions:
                if target_lang == "hi":
                    suggested_questions = [
                        "💡 मुझे नया बिज़नेस शुरू करना है",
                        "🔎 मैं किस योजना के लिए पात्र हूँ?",
                        "💰 ₹2 लाख का लोन चाहिए"
                    ]
                else:
                    suggested_questions = [
                        "💡 I want to start a business",
                        "🔎 Which schemes am I eligible for?",
                        "💰 Calculate EMI for ₹2 Lakh loan"
                    ]

        # -------------------------------------------------------------
        # 5. FINAL SANITIZATION & RESPONSE PACKAGING
        # -------------------------------------------------------------

        final_answer = sanitize_user_facing_text("\n\n".join(answer_parts))
        provider = get_ai_provider()

        # HARD CONTRACT: If intent is casual or response_mode is not GROUNDED, citations MUST be empty list
        raw_citations = citations if (response_mode == "GROUNDED" and intent not in CASUAL_INTENTS) else []
        final_citations = []
        for c in raw_citations:
            c.snippet = sanitize_user_facing_text(c.snippet)
            if c.source_document:
                c.source_document = sanitize_user_facing_text(c.source_document)
            final_citations.append(c)

        final_cards = []
        for card in rich_cards:
            card.title = sanitize_user_facing_text(card.title)
            if card.subtitle:
                card.subtitle = sanitize_user_facing_text(card.subtitle)
            if card.data and isinstance(card.data, dict):
                clean_data = {}
                for k, v in card.data.items():
                    if isinstance(v, str):
                        clean_data[k] = sanitize_user_facing_text(v)
                    elif isinstance(v, list):
                        clean_data[k] = [sanitize_user_facing_text(item) if isinstance(item, str) else item for item in v]
                    else:
                        clean_data[k] = v
                card.data = clean_data
            final_cards.append(card)

        final_actions = []
        for act in actions:
            act.label = sanitize_user_facing_text(act.label)
            final_actions.append(act)

        return AIChatResponse(
            answer=final_answer,
            intent=intent,
            response_mode=response_mode,
            citations=final_citations,
            actions=final_actions,
            rich_cards=final_cards,
            suggested_questions=suggested_questions,
            session_id=session_id,
            deterministic_used=deterministic_used,
            financial_calculation=fin_calc_res,
            is_fallback=provider.is_fallback,
            provider_name=provider.name
        )

    @classmethod
    def generate_stream_chunks(cls, db: Session, req: AIChatRequest, current_user_id: Optional[str] = None) -> Generator[str, None, None]:
        """Yields incremental text chunks for SSE streaming response."""
        res = cls.process_query(db, req, current_user_id)
        words = res.answer.split(" ")

        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
