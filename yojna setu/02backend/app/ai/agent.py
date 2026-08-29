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
}


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
                "current_scheme_id": None,
                "last_recommendation": None
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
            facts["sector"] = "MANUFACTURING"
            facts["activity_type"] = "SMALL_MICRO_BUSINESS"
            facts["business_description"] = "manufacturing unit"

        # Funding Needed / Loan Amount ("2 lakh", "2 lac", "2L", "50k")
        loan_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|l|lakhs)", msg_lower)
        if loan_match:
            val = float(loan_match.group(1)) * 100000
            facts["requested_loan_amount"] = val
        elif "50k" in msg_lower or "50 thousand" in msg_lower:
            facts["requested_loan_amount"] = 50000.0

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
        scheme_id = req.scheme_id or page_ctx.get("scheme_id") or memory.get("current_scheme_id")

        intent = AICopilotQueryRouter.classify_intent(raw_msg, page_ctx)

        actions: List[AICopilotAction] = []
        rich_cards: List[RichCard] = []
        citations: List[SourceCitation] = []
        suggested_questions: List[str] = []
        answer_parts: List[str] = []
        deterministic_used = False
        fin_calc_res: Optional[Dict[str, Any]] = None
        response_mode = "GROUNDED"

        msg_lower = raw_msg.lower()

        # Detect target language from request or message
        preferred_lang = (req.preferred_language or "en").lower().split("-")[0]
        detected_lang = AICopilotQueryRouter.detect_language(raw_msg)
        target_lang = preferred_lang if preferred_lang in ["hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or", "as"] else detected_lang

        # Check if user query matches scheme name directly (e.g. "PMEGP kya hai")
        if "pmegp" in msg_lower:
            memory["current_scheme_id"] = "SIH26092-001"
            scheme_id = "SIH26092-001"
        elif "mudra" in msg_lower:
            memory["current_scheme_id"] = "SIH26092-002"
            scheme_id = "SIH26092-002"
        elif "stand-up" in msg_lower or "stand up" in msg_lower:
            memory["current_scheme_id"] = "SIH26092-003"
            scheme_id = "SIH26092-003"
        elif "vishwakarma" in msg_lower:
            memory["current_scheme_id"] = "SIH26092-005"
            scheme_id = "SIH26092-005"

        # -------------------------------------------------------------
        # 1. HARD ROUTING GATE FOR CASUAL, SMALL TALK & EMOTIONAL INTENTS
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
            elif target_lang == "gu":
                answer_parts.append("નમસ્તે! 👋 હું તમારો યોજનાસેતુ સહાયક છું. આજે હું તમને સરકારી યોજનાઓ અને નાણાકીય સહાય શોધવામાં કેવી રીતે મદદ કરી શકું?")
            elif target_lang == "kn":
                answer_parts.append("ನಮಸ್ಕಾರ! 👋 ನಾನು ನಿಮ್ಮ ಯೋಜನಾಸೇತು ಸಹಾಯಕ. ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?")
            elif target_lang == "ml":
                answer_parts.append("നമസ്കാരം! 👋 ഞാൻ നിങ്ങളുടെ യോജനസേതു സഹായിയാണ്. സർക്കാർ പദ്ധതികൾ കണ്ടെത്താൻ ഞാൻ എങ്ങനെ സഹായിക്കണം?")
            elif target_lang == "pa":
                answer_parts.append("ਸਤਿ ਸ਼੍ਰੀ ਅਕਾਲ! 👋 ਮੈਂ ਤੁਹਾਡਾ ਯੋਜਨਾਸੇਤੂ ਸਹਾਇਕ ਹਾਂ। ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਲੱਭਣ ਵਿੱਚ ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?")
            elif target_lang == "or":
                answer_parts.append("ନମସ୍କାର! 👋 ମୁଁ ଆପଣଙ୍କ ଯୋଜନାସେତୁ ସହାୟକ। ଆଜି ସରକାରୀ ଯୋଜନା ଖୋଜିବାରେ ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?")
            elif target_lang == "as":
                answer_parts.append("নমস্কাৰ! 👋 মই আপোনাৰ যোজনাসেতু সহায়ক। চৰকাৰী আঁচনি বিচাৰি পোৱাত মই আপোনাক কেনেকৈ সহায় কৰিব পাৰোঁ?")
            else:
                answer_parts.append("Namaste! 👋 I am your YojnaSetu Assistant. How can I help you discover government schemes, eligibility rules, and loan options today?")
                suggested_questions = ["💡 I want to start a small business", "🔎 Which schemes am I eligible for?", "💰 I need a ₹2 lakh loan"]

        elif intent == "IDENTITY_QUERY":
            response_mode = "CASUAL"
            if target_lang == "hi":
                answer_parts.append("मैं योजनासेतु का एआई नागरिक सहायक हूँ। मेरा उद्देश्य भारतीय नागरिकों को 50+ आधिकारिक सरकारी योजनाओं, सब्सिडी, पात्रता और ऋण कैलकुलेटर से जोड़ना है।")
            elif target_lang == "bn":
                answer_parts.append("আমি যোজনাসেতুর AI নাগরিক সহায়ক। ভারতীয় নাগরিকদের সরকারি প্রকল্প, ভরতুকি ও ঋণের তথ্যের সাথে যুক্ত করাই আমার উদ্দেশ্য।")
            elif target_lang == "ta":
                answer_parts.append("நான் யோஜனாசேதுவின் AI குடிமக்கள் உதவியாளர். இந்தியக் குடிமக்களை அரசு நலத்திட்டங்கள் மற்றும் நிதி உதவிகளுடன் இணைப்பதே என் பணி.")
            elif target_lang == "te":
                answer_parts.append("నేను యోజనాసేతు AI పౌర సహాయకుడిని. భారతీయ పౌరులను ప్రభుత్వ పథకాలు మరియు ఆర్థిక ప్రయోజనాలతో అనుసంధానించడమే నా లక్ష్యం.")
            elif target_lang == "mr":
                answer_parts.append("मी योजनासेतूचा AI नागरिक सहाय्यक आहे. भारतीय नागरिकांना सरकारी योजना, सबसिडी आणि आर्थिक लाभांशी जोडणे हे माझे उद्दिष्ट आहे.")
            else:
                answer_parts.append("I am the YojnaSetu AI Citizen Assistant. My purpose is to help Indian citizens discover official government schemes, verify eligibility guidelines, calculate loan EMIs, and access official application portals.")
            suggested_questions = [
                "bhai mujhe business start karna hai",
                "Show schemes for women entrepreneurs",
                "How to apply for PMEGP loan?"
            ]

        elif intent == "EMOTIONAL_HELP":
            response_mode = "CASUAL"
            answer_parts.append(
                "Koi dikkat nahi 😊 Main step-by-step help karta hoon.\n\n"
                "Aapko nayi scheme chahiye, kisi business ke liye loan chahiye, ya document checklist ke baare mein jaanna hai?"
            )
            suggested_questions = [
                "bhai mujhe business start karna hai",
                "PMEGP scheme ke baare mein batao",
                "Loan ke liye kya documents lagenge?"
            ]

        elif intent == "CASUAL_CONVERSATION":
            response_mode = "CASUAL"
            if any(term in msg_lower for term in ["fool", "stupid", "dumb"]):
                answer_parts.append("Haha, hopefully not! 😄 Scheme se related koi bhi question poochiye, main help karunga.")
            elif "love" in msg_lower:
                answer_parts.append("Aww, thank you! 😊 Main yahan government schemes aur loan guidance ke liye always ready hoon.")
            elif "kaise ho" in msg_lower or "how are you" in msg_lower:
                answer_parts.append("Main badhiya hoon! 😊 Aaj aapki kya help kar sakta hoon?")
            elif any(term in msg_lower for term in ["match", "cricket", "weather"]):
                answer_parts.append("Main mainly government schemes, loan calculations, aur eligibility guidance mein help karta hoon. 😊 Scheme ke baare mein kya jaanna chahte hain?")
            else:
                answer_parts.append("Aapka swagat hai! 😊 Agar government scheme ya loan eligibility check karni hai, toh zaroor bataiye.")

            suggested_questions = [
                "bhai mujhe business start karna hai",
                "Find schemes for SC entrepreneurs",
                "Calculate EMI for ₹1 Lakh loan"
            ]

        elif intent == "GENERAL_HELP":
            response_mode = "CASUAL"
            answer_parts.append(
                "Here is how I can guide you:\n\n"
                "1. **Find Government Schemes**: Enter your state, category, and business need to get personalized recommendations.\n"
                "2. **Check Eligibility**: Verify if you appear to meet age, income, and category criteria.\n"
                "3. **Calculate Loan & EMI**: Estimate monthly installments using our financial engine.\n"
                "4. **Document Checklist**: Review optional document requirements.\n"
                "5. **Save Schemes**: Bookmark schemes to review later.\n"
                "6. **Official Application Portal**: Get safe, verified links to apply on official government portals."
            )
            suggested_questions = [
                "bhai mujhe business start karna hai",
                "Am I eligible for PMEGP?",
                "Calculate EMI for ₹2 Lakh loan"
            ]

        elif intent == "SAVE_SCHEME":
            if not current_user_id:
                response_mode = "CLARIFICATION"
                answer_parts.append("Sure — login once to your YojnaSetu account and I'll save it for you! 👍")
                actions.append(AICopilotAction(label="Sign In", action_type="VIEW_SCHEME", target_url="/login"))
            else:
                target_sid = scheme_id or memory.get("current_scheme_id") or "SIH26092-001"
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

        elif intent == "SAVED_SCHEME_CHECK":
            if not current_user_id:
                answer_parts.append("Please sign in to check your saved schemes.")
            else:
                target_sid = scheme_id or memory.get("current_scheme_id") or "SIH26092-001"
                from app.models.saved_scheme import SavedScheme
                saved_obj = db.query(SavedScheme).filter(SavedScheme.user_id == current_user_id, SavedScheme.scheme_id == target_sid).first()
                if saved_obj:
                    answer_parts.append("Yes 👍 This scheme is saved in your YojnaSetu account.")
                else:
                    answer_parts.append("No, this scheme is not saved in your account yet. Click **♡ Save Scheme** to save it!")

        elif intent == "REMOVE_SAVED_SCHEME":
            if not current_user_id:
                answer_parts.append("Please sign in to manage your saved schemes.")
            else:
                target_sid = scheme_id or memory.get("current_scheme_id") or "SIH26092-001"
                from app.models.saved_scheme import SavedScheme
                saved_obj = db.query(SavedScheme).filter(SavedScheme.user_id == current_user_id, SavedScheme.scheme_id == target_sid).first()
                if saved_obj:
                    db.delete(saved_obj)
                    db.commit()
                    answer_parts.append(f"Removed 👍 Scheme was removed from your Saved Schemes.")
                else:
                    answer_parts.append("This scheme was not in your saved list.")

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
        # 2. CONVERSATIONAL SCHEME DISCOVERY & PROGRESSIVE PROFILING
        # -------------------------------------------------------------

        elif intent == "BUSINESS_PROFILE_INIT" or intent == "PROFILE_CORRECTION":
            has_state = "state" in extracted_facts
            has_income = "annual_income" in extracted_facts
            has_category = "social_category" in extracted_facts
            has_activity = "business_description" in extracted_facts or "activity_type" in extracted_facts

            if not has_state:
                response_mode = "CLARIFICATION"
                answer_parts.append(
                    "Bilkul! 👍 Main aapke profile ke hisaab se suitable government schemes find karta hoon.\n\n"
                    "Bas 1-2 details bata dijiye:\n"
                    "1. Aap kis State se hain?"
                )
                suggested_questions = ["Uttar Pradesh", "Bihar", "Maharashtra", "Delhi"]

            elif not has_category:
                response_mode = "CLARIFICATION"
                answer_parts.append(
                    f"Got it! ({extracted_facts['state']}) 👍\n\n"
                    "Aap kis social category se belong karte hain — General, OBC, SC, ya ST?"
                )
                suggested_questions = ["SC", "ST", "OBC", "General"]

            elif not has_income:
                response_mode = "CLARIFICATION"
                answer_parts.append(
                    "Aapki approximate annual family income kitni hai?"
                )
                suggested_questions = ["Below ₹1 Lakh", "₹1 - 2 Lakhs", "₹2 - 5 Lakhs", "Above ₹5 Lakhs"]

            elif not has_activity:
                response_mode = "CLARIFICATION"
                answer_parts.append(
                    "Aap kis type ka business start ya expand karna chahte hain? (Jaise tailoring, retail shop, dairy farming, manufacturing, etc.)"
                )
                suggested_questions = ["Tailoring / Stitching", "Dairy Farming", "Retail Shop", "Manufacturing"]

            else:
                # All key profile slots gathered -> Run Deterministic Recommendation Engine
                response_mode = "TOOL_RESULT"
                profile = cls.build_profile_from_memory(session_id, req.profile)
                rec_out = CopilotTools.get_recommendations(db, profile, top_k=3)
                deterministic_used = True

                recs = rec_out.get("recommendations", [])
                st = extracted_facts.get('state', 'ALL_INDIA')
                cat = extracted_facts.get('social_category', 'SC')
                inc = extracted_facts.get('annual_income', 180000)

                answer_parts.append(
                    f"Samajh gaya 👍 Based on your profile (State: {st}, Category: {cat}, Income: ₹{inc:,.0f}), these verified schemes look like the best matches for you:"
                )

                for idx, item in enumerate(recs, 1):
                    score_val = item.get("score", item.get("soft_score", 90))
                    match_pct = int(score_val)
                    answer_parts.append(
                        f"**#{idx} {item['scheme_name']}** — Match: **{match_pct}%**\n"
                        f"• Eligibility: Based on the information provided, you appear to meet the listed criteria.\n"
                        f"• Objective: {item.get('objective', 'Verified Government Scheme')}"
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
                    "Iske required documents kya hain?",
                    "Calculate EMI for ₹2 Lakh loan",
                    "How to apply for this scheme?"
                ]

        elif intent == "RECOMMENDATION_QUERY":
            response_mode = "TOOL_RESULT"
            profile = cls.build_profile_from_memory(session_id, req.profile)
            rec_out = CopilotTools.get_recommendations(db, profile, top_k=3)
            deterministic_used = True

            recs = rec_out.get("recommendations", [])
            st = extracted_facts.get('state', 'ALL_INDIA')
            cat = extracted_facts.get('social_category', 'SC')
            inc = extracted_facts.get('annual_income', 180000)

            answer_parts.append(
                f"Based on what you've shared (State: {st}, Category: {cat}, Income: ₹{inc:,.0f}), these schemes appear to suit your needs best:"
            )

            for idx, item in enumerate(recs, 1):
                score_val = item.get("score", item.get("soft_score", 90))
                match_pct = int(score_val)
                answer_parts.append(f"**#{idx} {item['scheme_name']}** — Match: **{match_pct}%**")
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
                "Calculate EMI for loan",
                "How to apply?"
            ]

        # -------------------------------------------------------------
        # 3. GROUNDED TOOL & RAG ROUTING
        # -------------------------------------------------------------
        else:
            profile = cls.build_profile_from_memory(session_id, req.profile)
            hybrid_rag = HybridSchemeRAG(db)

            target_sid = scheme_id or "SIH26092-052"

            if intent == "FINANCIAL_QUERY":
                response_mode = "TOOL_RESULT"
                req_loan = extracted_facts.get("requested_loan_amount", 80000.0)
                calc_out = CopilotTools.calculate_financials(db, target_sid, project_cost=req_loan*1.25, requested_loan_amount=req_loan)
                fin_calc_res = calc_out
                deterministic_used = True

                answer_parts.append(
                    f"Official Financial Estimation for '{calc_out['scheme_name']}':\n"
                    f"• Estimated Loan Amount: ₹{(calc_out.get('eligible_loan_amount') or 0):,.0f}\n"
                    f"• Government Subsidy: ₹{(calc_out.get('subsidy_amount') or 0):,.0f}\n"
                    f"• Interest Rate: {calc_out.get('interest_rate') or 0}% p.a.\n"
                    f"• Estimated Monthly EMI: ₹{(calc_out.get('periodic_installment') or 0):,.0f} over {calc_out.get('repayment_period_months') or 0} months."
                )
                actions.append(AICopilotAction(
                    label=f"Open EMI Calculator",
                    action_type="CALCULATE_EMI",
                    target_url=f"/calculator?scheme={target_sid}"
                ))
                rich_cards.append(RichCard(
                    card_type="FINANCIAL_CARD",
                    title=f"Loan Calculation — {calc_out['scheme_name']}",
                    data=calc_out
                ))

            elif intent == "ELIGIBILITY_QUERY":
                response_mode = "TOOL_RESULT"
                elig_out = CopilotTools.check_eligibility(db, target_sid, profile)
                deterministic_used = True

                status_str = "You appear to meet the listed criteria" if elig_out["is_eligible"] else "Requirements to verify"
                answer_parts.append(
                    f"Eligibility Guidance (Deterministic Eligibility Evaluation) for '{elig_out['scheme_name']}':\n"
                    f"• Status: Based on the information provided, {status_str.lower()}.\n"
                    f"• Details: {'; '.join(elig_out.get('explanations', []))}\n\n"
                    f"Note: Final eligibility, document verification, and sanctioning are determined exclusively by the concerned government department or bank."
                )
                rich_cards.append(RichCard(
                    card_type="ELIGIBILITY_CARD",
                    title=f"Eligibility Guidance — {elig_out['scheme_name']}",
                    subtitle=status_str,
                    data=elig_out
                ))

            elif intent == "DOCUMENT_QUERY":
                response_mode = "GROUNDED"
                details = CopilotTools.get_scheme_details(db, target_sid)
                if details:
                    doc_list = [f"• ✓ {d['document_name']} ({d['requirement_type']})" for d in details.get("documents", [])]
                    answer_parts.append(
                        f"Optional Document Checklist for '{details['scheme_name']}':\n" + "\n".join(doc_list) +
                        "\n\n* Final document requirements may vary. Please verify them on the official application portal."
                    )
                    actions.append(AICopilotAction(
                        label=f"View Official Portal Link",
                        action_type="VIEW_DOCUMENTS",
                        target_url=f"/schemes/{target_sid}"
                    ))
                    rich_cards.append(RichCard(
                        card_type="DOCUMENT_CHECKLIST",
                        title=f"Document Checklist — {details['scheme_name']}",
                        data={"documents": details.get("documents", [])}
                    ))

            elif intent == "APPLICATION_QUERY":
                response_mode = "GROUNDED"
                details = CopilotTools.get_scheme_details(db, target_sid)
                scheme_name_str = details['scheme_name'] if details else "this scheme"
                answer_parts.append(
                    f"How to Apply for '{scheme_name_str}':\n\n"
                    "1. **Review Eligibility**: Verify that you meet the age, income, and category criteria.\n"
                    "2. **Prepare Document Checklist**: Gather Aadhaar, income certificate, caste certificate, and project proposal.\n"
                    "3. **Open Official Portal**: Click 'Apply on Official Portal' to navigate to the official government portal.\n"
                    "4. **Complete Application**: Fill in your details and submit directly on the government website.\n"
                    "5. **Track Progress**: Note down your official reference/acknowledgement number to track status on the official portal."
                )
                if details:
                    actions.append(AICopilotAction(
                        label=f"Apply on Official Portal",
                        action_type="VIEW_SCHEME",
                        target_url=f"/schemes/{target_sid}"
                    ))

            else:
                citations = hybrid_rag.hybrid_search(
                    query=raw_msg,
                    scheme_id=scheme_id,
                    state=extracted_facts.get("state"),
                    category=extracted_facts.get("social_category"),
                    top_k=3
                )
                if citations:
                    response_mode = "GROUNDED"
                    top_cite = citations[0]
                    answer_parts.append(f"Official scheme information for {top_cite.scheme_name}:\n\n{top_cite.snippet}")
                    if scheme_id:
                        actions.append(AICopilotAction(
                            label=f"View Details",
                            action_type="VIEW_SCHEME",
                            target_url=f"/schemes/{scheme_id}"
                        ))
                else:
                    response_mode = "CASUAL"
                    answer_parts.append("Official scheme information ke according, I can guide you through government schemes, eligibility guidelines, loan calculations, and official application portals.")

            if not suggested_questions:
                suggested_questions = [
                    "Which schemes am I eligible for?",
                    "Calculate EMI for loan",
                    "What documents are required for MSME schemes?"
                ]

        final_answer = "\n\n".join(answer_parts)
        provider = get_ai_provider()

        # HARD CONTRACT: If intent is casual, citations MUST be empty list
        final_citations = citations if (response_mode == "GROUNDED" and intent not in CASUAL_INTENTS) else []

        return AIChatResponse(
            answer=final_answer,
            intent=intent,
            response_mode=response_mode,
            citations=final_citations,
            actions=actions,
            rich_cards=rich_cards,
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
