import re
import uuid
import logging
from decimal import Decimal
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
    "OUT_OF_DOMAIN",
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
    def update_session_facts(cls, session_id: str, message: Any) -> Dict[str, Any]:
        """Extracts and updates conversational profile facts with voice tolerance and correction handling."""
        memory = cls.get_session_memory(session_id)
        facts = memory["extracted_facts"]

        if isinstance(message, dict):
            facts.update(message)
            return facts

        raw_msg = re.sub(r"</?untrusted_content>", "", str(message)).strip()
        msg_lower = raw_msg.lower()

        # 1. Integrate NaturalLanguageProfileExtractor
        from app.ai.extractor import NaturalLanguageProfileExtractor, DISTRICT_TO_STATE
        ext_res = NaturalLanguageProfileExtractor.extract_profile(raw_msg)
        p_dict = ext_res.extracted_profile.model_dump(exclude_unset=True)
        for k, v in p_dict.items():
            if v is not None:
                facts[k] = v

        # 2. Handle explicit corrections ("actually meri age 26", "nahi OBC hu")
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

        # 2b. Name extraction fallback
        name_match = re.search(r"\b(?:my\s+name\s+is|mera\s+naam|i\s+am|i'm|myself|naam)\s+([A-Za-z]+)\b", msg_lower)
        if name_match:
            cand = name_match.group(1).title()
            if cand.lower() not in ("from", "looking", "interested", "planning", "a", "an", "the", "sc", "st", "obc", "general", "in", "from"):
                facts["name"] = cand

        # 3. Voice tolerance, numeral normalization, and age extraction
        age_match = re.search(r"\b(?:i\s+am|i'm|my\s+age|age|mer?i\s+umar|umar|उम्र)\s*(?:is|\:|\=)?\s*(\d{1,2})\b", msg_lower)
        if not age_match:
            age_match = re.search(r"\b(\d{1,2})\s*(?:saal|years|year|yrs|yr|साल|वर्ष)\b", msg_lower)
        if not age_match:
            # Handle patterns like "I'm 24 and SC" or "24 and SC"
            age_match = re.search(r"\b(\d{1,2})\s*(?:and|aur|\&)?\s*(?:sc|st|obc|gen|general)\b", msg_lower)
        if age_match:
            facts["age"] = int(age_match.group(1))
        elif re.match(r"^\d{2}$", msg_lower.strip()):
            facts["age"] = int(msg_lower.strip())

        # District-to-State auto resolution
        for dist_key, state_name in DISTRICT_TO_STATE.items():
            if re.search(rf"\b{re.escape(dist_key.lower())}\b", msg_lower):
                facts["district"] = dist_key.title()
                facts["state"] = state_name
                break

        # State normalization (display format)
        st_val = facts.get("state")
        if st_val and st_val != "ALL_INDIA":
            facts["state"] = st_val.replace("_", " ").upper()
        elif any(term in msg_lower for term in ["up", "u p", "uttar pradesh"]):
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
        elif "punjab" in msg_lower:
            facts["state"] = "PUNJAB"
        elif "haryana" in msg_lower:
            facts["state"] = "HARYANA"
        elif facts.get("district"):
            d_upper = str(facts["district"]).strip().upper()
            if d_upper in DISTRICT_TO_STATE:
                facts["state"] = DISTRICT_TO_STATE[d_upper]

        # Social Category
        if re.search(r"\b(?:sc|scheduled\s+caste|anusuchit\s+jati|dalit)\b", msg_lower):
            facts["social_category"] = "SC"
            facts["is_sc"] = True
        elif re.search(r"\b(?:st|scheduled\s+tribe|anusuchit\s+janjati|adivasi)\b", msg_lower):
            facts["social_category"] = "ST"
            facts["is_st"] = True
        elif re.search(r"\b(?:obc|other\s+backward|pichhda|pichhda\s+varg)\b", msg_lower):
            facts["social_category"] = "OBC"
            facts["is_obc"] = True
        elif re.search(r"\b(?:general|gen|samanya)\b", msg_lower):
            facts["social_category"] = "GENERAL"

        # Gender
        if any(term in msg_lower for term in ["woman", "female", "mahila", "ladki"]):
            facts["gender"] = "FEMALE"
        elif any(term in msg_lower for term in ["man", "male", "purush", "ladka"]):
            facts["gender"] = "MALE"

        # Separate Financial Dimensions (Never confuse Income, Expenses, Savings/Margin, Loan Amount, Project Cost)
        income_kws = ["earn", "earning", "income", "kamai", "aamdani", "salary", "salaried", "per annum", "p.a.", "salana", "वार्षिक आय", "आय", "कमाई"]
        has_income_kw = any(k in msg_lower for k in income_kws)
        if has_income_kw:
            m_inc_match = re.search(r"(?:i\s+earn|earn|salary|kamata\s+hu|kamati\s+hu|monthly\s+income|monthly\s+salary|income)\s*(?:is|of|are|around|about|\:)?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)", msg_lower)
            if m_inc_match:
                raw_inc = float(m_inc_match.group(1).replace(",", ""))
                if "per month" in msg_lower or "monthly" in msg_lower or "p.m" in msg_lower or "mahine" in msg_lower or raw_inc <= 100000:
                    facts["monthly_income"] = raw_inc
                    facts["annual_income"] = raw_inc * 12.0
                else:
                    facts["annual_income"] = raw_inc
                    facts["monthly_income"] = round(raw_inc / 12.0, 2)
            else:
                inc_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|l|lakhs)", msg_lower)
                if inc_match:
                    facts["annual_income"] = float(inc_match.group(1)) * 100000.0
                    facts["monthly_income"] = round(facts["annual_income"] / 12.0, 2)
                elif "180000" in msg_lower or "1.8 lakh" in msg_lower:
                    facts["annual_income"] = 180000.0
                    facts["monthly_income"] = 15000.0
                elif "100000" in msg_lower or "1 lakh" in msg_lower:
                    facts["annual_income"] = 100000.0
                    facts["monthly_income"] = 8333.33
        elif not any(k in msg_lower for k in ["loan", "karz", "credit", "borrow", "invest", "investment", "savings", "saving", "bachat", "cost", "laagat", "expense", "kharch"]):
            standalone_amount_match = re.match(r"^(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|l|lakhs)?$", msg_lower.strip())
            if standalone_amount_match:
                val_num = float(standalone_amount_match.group(1))
                if "lakh" in msg_lower or "lac" in msg_lower or val_num < 1000:
                    facts["annual_income"] = val_num * 100000.0
                    facts["monthly_income"] = round(facts["annual_income"] / 12.0, 2)
                else:
                    facts["annual_income"] = val_num
                    facts["monthly_income"] = round(val_num / 12.0, 2)

        # Monthly living / operating expenses
        # e.g., "My monthly expenses are around 18,000", "expenses 18000"
        exp_match = re.search(r"(?:monthly\s+expenses?|household\s+expenses?|expenses?|kharcha|kharch)\s*(?:is|of|are|around|about|approx|approx\.|\:)?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)", msg_lower)
        if exp_match:
            facts["monthly_expenses"] = float(exp_match.group(1).replace(",", ""))

        # Existing obligations / EMI
        # e.g., "I already pay 3,000 EMI", "pay 3000 emi", "existing emi 3000"
        emi_match = re.search(r"(?:already\s+pay|pay|pehle\s+se\s+emi|existing\s+emi|current\s+emi|purani\s+emi|emi)\s*(?:is|of|are|around|about|approx|\:)?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)", msg_lower)
        if not emi_match and "emi" in msg_lower:
            emi_match = re.search(r"([\d,]+(?:\.\d+)?)\s*(?:₹|rs\.?|inr)?\s*(?:ki\s+)?emi", msg_lower)
        if emi_match:
            facts["monthly_obligations"] = float(emi_match.group(1).replace(",", ""))

        savings_kws = ["invest", "investment", "lagana", "laga sakta", "savings", "saving", "bachat", "mere paas", "apne paas", "margin", "contribution", "खुद लगा", "budget", "बजट"]
        has_savings_kw = any(k in msg_lower for k in savings_kws)
        if has_savings_kw:
            sav_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|l|lakhs)", msg_lower)
            if sav_match:
                facts["liquid_savings"] = float(sav_match.group(1)) * 100000.0
            elif "50k" in msg_lower or "50 thousand" in msg_lower:
                facts["liquid_savings"] = 50000.0

        loan_kws = ["loan", "karz", "credit", "borrow", "chahiye loan", "loan chahiye", "लोन", "ऋण", "कर्ज"]
        has_loan_kw = any(k in msg_lower for k in loan_kws)
        if has_loan_kw and not has_savings_kw:
            loan_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|l|lakhs)", msg_lower)
            if loan_match:
                facts["requested_loan_amount"] = float(loan_match.group(1)) * 100000.0
            else:
                loan_num_match = re.search(r"(?:loan|karz|credit|borrow)\s*(?:of|is|around|amount|chahiye)?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)", msg_lower)
                if not loan_num_match:
                    loan_num_match = re.search(r"(?:need|chahiye|require)\s+(?:a\s+)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(?:loan|karz)", msg_lower)
                if loan_num_match:
                    facts["requested_loan_amount"] = float(loan_num_match.group(1).replace(",", ""))
            if not facts.get("requested_loan_amount") and ("50k" in msg_lower or "50 thousand" in msg_lower):
                facts["requested_loan_amount"] = 50000.0

        if any(k in msg_lower for k in ["project cost", "total cost", "project", "laagat", "lagat", "budget"]):
            pc_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|l|lakhs)", msg_lower)
            if pc_match:
                facts["project_cost"] = float(pc_match.group(1)) * 100000.0
                if "liquid_savings" not in facts:
                    facts["liquid_savings"] = float(pc_match.group(1)) * 100000.0

        # Activity / Trade
        if any(term in msg_lower for term in ["dairy", "milk", "doodh", "pashupalan"]):
            facts["sector"] = "DAIRY"
            facts["activity_type"] = "DAIRY_FARMING"
            facts["business_description"] = "dairy farming"
            facts["is_farmer"] = True
        elif any(term in msg_lower for term in ["tailoring", "stitching", "kapde", "silai"]):
            facts["sector"] = "MICRO_FINANCE"
            facts["activity_type"] = "SMALL_MICRO_BUSINESS"
            facts["business_description"] = "tailoring"
        elif any(term in msg_lower for term in ["manufacturing", "factory", "production", "workshop", "plant"]):
            facts["sector"] = "MANUFACTURING"
            facts["activity_type"] = "MANUFACTURING"
            facts["business_description"] = "manufacturing"
        elif re.search(r"\b(?:shop|retail|kirana|dukaan|dukan|store)\b", msg_lower):
            facts["sector"] = "MICRO_FINANCE"
            facts["activity_type"] = "SMALL_MICRO_BUSINESS"
            facts["business_description"] = "retail shop"
        elif any(term in msg_lower for term in ["student", "chhatra", "छात्र", "college", "university", "higher education", "btech", "engineering", "medical", "mbbs", "mtech", "mba", "education loan", "study loan", "vidyarthi", "higher studies"]):
            facts["sector"] = "EDUCATION"
            facts["applicant_type"] = "STUDENT"
            facts["employment_status"] = "STUDENT"
            facts["activity_type"] = "EDUCATION"
            facts["business_description"] = "higher education"

        # Business Stage
        if any(term in msg_lower for term in ["start karna", "shuru karna", "nayi unit", "naya business", "naya kaam", "start a business", "start", "new"]):
            facts["business_stage"] = "NEW"
            facts["is_new_unit"] = True
        elif any(term in msg_lower for term in ["already chal raha", "existing", "purana business", "purana kaam", "badhana hai", "expand", "expansion"]):
            facts["business_stage"] = "EXPANSION"
            facts["is_new_unit"] = False

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
        """Combines session memory facts with request profile without fake default inflation."""
        memory = cls.get_session_memory(session_id)
        facts = memory["extracted_facts"]

        base_data = req_profile.model_dump() if req_profile else {}
        for k, v in facts.items():
            if k in base_data and base_data[k] is None:
                base_data[k] = v
            elif k not in base_data:
                base_data[k] = v

        # Zero fake default inflation: Keep unprovided fields as None
        base_data["annual_income"] = base_data.get("annual_income") if base_data.get("annual_income") is not None else facts.get("annual_income")
        base_data["age"] = base_data.get("age") if base_data.get("age") is not None else facts.get("age")
        base_data["social_category"] = base_data.get("social_category") if base_data.get("social_category") is not None else facts.get("social_category")
        base_data["name"] = base_data.get("name") if base_data.get("name") is not None else facts.get("name")

        st = base_data.get("state") or facts.get("state")
        base_data["state"] = st.replace("_", " ").upper() if (st and st != "ALL_INDIA") else "ALL_INDIA"

        if "district" in facts and not base_data.get("district"):
            base_data["district"] = facts["district"]

        if "business_stage" in facts and not base_data.get("business_stage"):
            base_data["business_stage"] = facts["business_stage"]
            base_data["is_new_unit"] = facts.get("is_new_unit", True)

        if "sector" in facts and not base_data.get("sector"):
            base_data["sector"] = facts["sector"]

        if "activity_type" in facts and not base_data.get("activity_type"):
            base_data["activity_type"] = facts["activity_type"]

        if "project_cost" in facts and not base_data.get("project_cost"):
            base_data["project_cost"] = facts["project_cost"]

        if "liquid_savings" in facts and not base_data.get("liquid_savings"):
            base_data["liquid_savings"] = facts["liquid_savings"]

        if "requested_loan_amount" in facts and not base_data.get("requested_loan_amount"):
            base_data["requested_loan_amount"] = facts["requested_loan_amount"]

        if "is_farmer" in facts and base_data.get("is_farmer") is None:
            base_data["is_farmer"] = facts["is_farmer"]

        if "is_artisan" in facts and base_data.get("is_artisan") is None:
            base_data["is_artisan"] = facts["is_artisan"]

        if "is_street_vendor" in facts and base_data.get("is_street_vendor") is None:
            base_data["is_street_vendor"] = facts["is_street_vendor"]

        if "is_pwd" in facts and base_data.get("is_pwd") is None:
            base_data["is_pwd"] = facts["is_pwd"]

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

        # Proactive adversarial prompt injection check
        if AISecurityGuard.is_prompt_injection(raw_msg):
            from app.ai.observability import RAGObservabilityTracker
            RAGObservabilityTracker.record_prompt_injection_blocked()
            return AIChatResponse(
                answer=(
                    "I am YojnaSetu's AI Scheme Assistant. I cannot reveal internal instructions, "
                    "override statutory eligibility rules, or execute unauthorized operations. "
                    "How can I assist you with government scheme information or applications today?"
                ),
                intent="SECURITY_DEFENSE",
                response_mode="FALLBACK",
                citations=[],
                actions=[],
                rich_cards=[],
                suggested_questions=[
                    "Which schemes am I eligible for?",
                    "How do I apply for PMEGP?",
                    "What documents are needed for PM SVANidhi?"
                ],
                session_id=session_id,
                deterministic_used=False,
                is_fallback=True,
                provider_name="security_defense"
            )

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
            memory["preferred_language"] = detected_lang
            SESSION_MEMORY_STORE[session_id] = memory
        elif req_lang in ["hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or", "as"]:
            target_lang = req_lang
            memory["preferred_language"] = req_lang
            SESSION_MEMORY_STORE[session_id] = memory
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
            elif target_lang == "gu":
                confirmation_text = "ચોક્કસ 😊 હવે હું તમારી સાથે ગુજરાતીમાં વાત કરીશ. હું તમને સરકારી યોજના, લોન અથવા દસ્તાવેજોમાં કેવી રીતે મદદ કરી શકું?"
                suggested_questions = ["💡 મારે નવો વ્યવસાય શરૂ કરવો છે", "PMEGP લોન માટે શું જરૂરી છે?", "મારી પાત્રતા તપાસો"]
            elif target_lang == "kn":
                confirmation_text = "ಖಂಡಿತ 😊 ಇನ್ನು ಮುಂದೆ ನಾನು ನಿಮ್ಮೊಂದಿಗೆ ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡುತ್ತೇನೆ. ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಅಥವಾ ಸಾಲದ ಮಾಹಿತಿಯಲ್ಲಿ ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
                suggested_questions = ["💡 ನಾನು ಹೊಸ ವ್ಯವಹಾರವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ", "PMEGP ಸಾಲಕ್ಕೆ ಏನು ಬೇಕು?", "ನನ್ನ ಅರ್ಹತೆಯನ್ನು ಪರಿಶೀಲಿಸಿ"]
            elif target_lang == "ml":
                confirmation_text = "തീർച്ചയായും 😊 ഇനി മുതൽ നമുക്ക് മലയാളത്തിൽ സംസാരിക്കാം. സർക്കാർ പദ്ധതികളെക്കുറിച്ചോ വായ്പകളെക്കുറിച്ചോ ഞാൻ എങ്ങനെ സഹായിക്കണം?"
                suggested_questions = ["💡 എനിക്ക് ഒരു പുതിയ ബിസിനസ്സ് ആരംഭിക്കണം", "PMEGP വായ്പയ്ക്ക് എന്താണ് വേണ്ടത്?", "എന്റെ യോഗ്യത പരിശോധിക്കുക"]
            elif target_lang == "pa":
                confirmation_text = "ਬਿਲਕੁਲ 😊 ਹੁਣ ਮੈਂ ਤੁਹਾਡੇ ਨਾਲ ਪੰਜਾਬੀ ਵਿੱਚ ਗੱਲ ਕਰਾਂगा। ਮੈਂ ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਜਾਂ ਕਰਜ਼ੇ ਦੀ ਜਾਣਕਾਰੀ ਵਿੱਚ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?"
                suggested_questions = ["💡 ਮੈਂ ਨਵਾਂ ਕਾਰੋਬਾਰ ਸ਼ੁਰੂ ਕਰਨਾ ਚਾਹੁੰਦਾ ਹਾਂ", "PMEGP ਲੋਨ ਲਈ ਕੀ ਚਾਹੀਦਾ ਹੈ?", "ਮੇरी ਯੋਗਤਾ ਦੀ ਜਾਂਚ ਕਰੋ"]
            elif target_lang == "or":
                confirmation_text = "ନିଶ୍ଚୟ 😊 ଏବେଠାରୁ ମୁଁ ଆପଣଙ୍କ ସହିତ ଓଡ଼ିଆରେ କଥାବାର୍ତ୍ତା କରିବି। ମୁଁ ସରକାରୀ ଯୋଜନା ବା ଋଣ ସୂଚନାରେ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?"
                suggested_questions = ["💡 ମୁଁ ଏକ ନୂତନ ବ୍ୟବସାୟ ଆରମ୍ଭ କରିବାକୁ ଚାହୁଁଛି", "PMEGP ଋଣ ପାଇଁ କଣ ଆବଶ୍ୟକ?", "ମୋର ଯୋଗ୍ୟତା ଯାଞ୍ଚ କରନ୍ତୁ"]
            elif target_lang == "as":
                confirmation_text = "নিশ্চয় 😊 এতিয়াৰ পৰা মই আপোনাৰ সৈতে অসমীয়াত কথা পাতিম। মই চৰকাৰী আঁচনি বা ঋণৰ তথ্যত আপোনাক কেনেকৈ সহায় কৰিব পাৰোঁ?"
                suggested_questions = ["💡 মই এটা নতুন ব্যৱসায় আৰম্ভ কৰিব বিচাৰো", "PMEGP ঋণৰ বাবে কি প্ৰয়োজন?", "মোৰ योग्यता পৰীক্ষা কৰক"]
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
                provider_name="system",
                language=target_lang
            )

        # -------------------------------------------------------------
        # Scheme Context Resolution (Strict Context Isolation)
        # -------------------------------------------------------------
        explicit_scheme_in_msg = None
        if intent not in ("PROFILE_UPDATE", "PROFILE_CORRECTION", "CASUAL_GREETING", "CASUAL_CONVERSATION", "IDENTITY_QUERY", "GENERAL_HELP", "EMOTIONAL_HELP", "OUT_OF_DOMAIN"):
            resolved_scheme_obj = CopilotTools.resolve_scheme_by_name(db, raw_msg)
            if resolved_scheme_obj:
                explicit_scheme_in_msg = resolved_scheme_obj.scheme_id
            elif "pmegp" in msg_lower or "pmegp" in norm_msg:
                explicit_scheme_in_msg = "SIH26092-001"
            elif "mudra" in msg_lower or "mudra" in norm_msg:
                explicit_scheme_in_msg = "SIH26092-002"
            elif "stand-up" in msg_lower or "stand up" in msg_lower or "standup" in norm_msg:
                explicit_scheme_in_msg = "SIH26092-003"
            elif "vishwakarma" in msg_lower or "vishwakarma" in norm_msg:
                explicit_scheme_in_msg = "SIH26092-005"
            elif "csis" in msg_lower or "central sector interest subsidy" in msg_lower or "vidya lakshmi" in msg_lower or "vidyalakshmi" in msg_lower:
                explicit_scheme_in_msg = "SIH26092-083"
            elif "nsfdc" in msg_lower and any(term in msg_lower for term in ["education", "els", "student", "shiksha"]):
                explicit_scheme_in_msg = "SIH26092-056"
            elif "nstfdc" in msg_lower and any(term in msg_lower for term in ["education", "asry", "student", "shiksha", "adivasi shiksha"]):
                explicit_scheme_in_msg = "SIH26092-059"
            elif "ambedkar" in msg_lower and any(term in msg_lower for term in ["overseas", "education", "obc"]):
                explicit_scheme_in_msg = "SIH26092-196"
            elif "nsfdc" in msg_lower or "nsfdc" in norm_msg:
                explicit_scheme_in_msg = "SIH26092-052"
            elif "svanidhi" in msg_lower or "svanidhi" in norm_msg:
                explicit_scheme_in_msg = "SIH26092-004"

        has_pronoun_ref = bool(re.search(r"\b(?:isme|iske|iska|iski|usme|uska|uski|ye|yeh|this|it|is scheme|ye scheme)\b", norm_msg or msg_lower))
        is_scheme_followup = intent in ("DOCUMENT_QUERY", "FINANCIAL_QUERY", "ELIGIBILITY_QUERY", "APPLICATION_QUERY", "APPLICATION_TRACKING_INQUIRY", "SUBSIDY_QUERY", "SCHEME_DETAILS", "EXPLAIN_REJECTION", "BENEFIT_QUERY")

        if req.scheme_id:
            active_sid = req.scheme_id
            memory["active_scheme_id"] = active_sid
        elif page_ctx.get("scheme_id"):
            active_sid = page_ctx.get("scheme_id")
            memory["active_scheme_id"] = active_sid
        elif explicit_scheme_in_msg:
            active_sid = explicit_scheme_in_msg
            memory["active_scheme_id"] = active_sid
        elif (has_pronoun_ref or is_scheme_followup) and memory.get("active_scheme_id"):
            active_sid = memory.get("active_scheme_id")
        else:
            active_sid = None

        if intent in ("CASUAL_GREETING", "CASUAL_CONVERSATION", "IDENTITY_QUERY", "GENERAL_HELP", "EMOTIONAL_HELP", "OUT_OF_DOMAIN", "PROFILE_UPDATE", "PROFILE_CORRECTION"):
            if not has_pronoun_ref and not explicit_scheme_in_msg:
                memory.pop("active_scheme_id", None)
                active_sid = None
        elif intent in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY"):
            if not has_pronoun_ref and not explicit_scheme_in_msg:
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
        rag_active = (intent not in CASUAL_INTENTS and intent not in ("BUSINESS_PROFILE_INIT", "SCHEME_DISCOVERY", "SAVE_SCHEME", "SAVED_SCHEMES_LIST", "WHY_MATCH_QUERY", "EXPLAIN_REJECTION", "SUBSIDY_QUERY", "SCHEME_COMPARISON", "SCHEME_DIFFERENCE", "SCHEME_DETAILS"))
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

        elif intent == "OUT_OF_DOMAIN":
            response_mode = "CASUAL"
            if target_lang == "hi":
                answer_parts.append(
                    "माफ़ कीजिए 🙏 मैं योजनासेतु का सरकारी योजना सहायक हूँ। मेरा कार्य केवल भारतीय सरकारी योजनाओं, सब्सिडी, पात्रता, बिज़नेस लोन और आवेदन प्रक्रियाओं में सहायता करना है।\n\n"
                    "मैं खेल, कोडिंग या सामान्य चर्चा जैसे बाहरी विषयों पर उत्तर नहीं दे सकता। कृपया मुझे सरकारी योजनाओं या ऋण के बारे में पूछें!"
                )
                suggested_questions = [
                    "💡 मुझे नया बिज़नेस शुरू करना है",
                    "🔎 मैं किस योजना के लिए पात्र हूँ?",
                    "💰 ₹2 लाख का लोन चाहिए"
                ]
            else:
                answer_parts.append(
                    "I apologize, but I am YojnaSetu's Government Scheme Intelligence Assistant. I specialize exclusively in Indian government welfare schemes, subsidies, statutory eligibility, business loans, and official application guidelines.\n\n"
                    "I cannot answer questions on unrelated topics like cricket, coding, entertainment, or general trivia. Please ask me about central and state government schemes, business loans, or eligibility!"
                )
                suggested_questions = [
                    "💡 I want to start a business",
                    "🔎 Which schemes am I eligible for?",
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

        elif intent in ("CASUAL_CONVERSATION",):
            response_mode = "CASUAL"
            citations = []
            rich_cards = []
            actions = []
            deterministic_used = False

            if any(term in msg_lower for term in ["lame", "boring", "gadhe", "gadha", "ullu", "pagal", "fool", "stupid", "dumb", "crazy"]):
                if target_lang == "hi":
                    answer_parts.append("😂 कोई बात नहीं! मैं फिर भी आपकी मदद के लिए यहाँ हूँ। क्या आप कोई सरकारी योजना खोजना चाहते हैं, पात्रता देखना चाहते हैं या लोन EMI कैलकुलेट करना चाहते हैं?")
                    suggested_questions = ["💡 मुझे नया बिज़नेस शुरू करना है", "🔎 मेरी पात्रता चेक करें", "💰 लोन EMI कैलकुलेट करें"]
                else:
                    answer_parts.append("😂 Fair enough. I'm still here to help! Want to find a government scheme, check eligibility, or calculate a loan EMI?")
                    suggested_questions = ["💡 Find schemes for my business", "🔎 Check my eligibility", "💰 Calculate loan EMI"]
            elif any(term in msg_lower or term in norm_msg for term in ["nahi chal raha", "nhi chal rha", "not working", "chal nahi raha", "kaam nahi kar raha", "kuch nahi chal raha"]):
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
            elif any(term in msg_lower for term in ["thanks", "thank you", "shukriya", "dhanyawad"]):
                if target_lang == "hi":
                    answer_parts.append("आपका स्वागत है! 🙏 अगर आपको किसी सरकारी योजना, पात्रता या लोन कैलकुलेशन में मदद चाहिए तो बेझिझक पूछें।")
                else:
                    answer_parts.append("You're very welcome! 🙏 Feel free to ask anytime if you need help finding government schemes, verifying eligibility, or calculating loan EMIs.")
                suggested_questions = ["💡 I want to start a business", "🔎 Which schemes am I eligible for?", "💰 Calculate loan EMI"]
            elif any(term in msg_lower for term in ["okay", "ok", "thik hai", "accha", "theek hai", "got it", "fine"]):
                if target_lang == "hi":
                    answer_parts.append("बिल्कुल! 👍 जब भी आप तैयार हों, बताइए क्या खोजना है।")
                else:
                    answer_parts.append("Sounds good! 👍 Whenever you're ready, let me know what you'd like to explore.")
                suggested_questions = ["💡 I want to start a business", "🔎 Check my eligibility", "💰 Calculate loan EMI"]
            elif any(term in msg_lower for term in ["haha", "hahaha", "lol", "hehe", "rofl"]):
                if target_lang == "hi":
                    answer_parts.append("खुशी हुई आपको हँसते देखकर! 😊 बताइए सरकारी योजनाओं या लोन में आपकी क्या सहायता करूँ?")
                else:
                    answer_parts.append("Glad to bring a smile! 😊 Let me know whenever you'd like to explore government schemes, eligibility, or loan options.")
                suggested_questions = ["💡 I want to start a business", "🔎 Which schemes am I eligible for?", "💰 Calculate loan EMI"]
            elif "love" in msg_lower:
                answer_parts.append("Thank you! 😊 I'm always here to help you navigate government schemes and loan guidance.")
            elif "kaise ho" in msg_lower or "how are you" in msg_lower or "how r u" in msg_lower:
                answer_parts.append("I'm doing great! 😊 What are you looking for today — a business scheme, loan, scholarship, subsidy, or something else?")
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
            response_mode = "TOOL_RESULT"
            deterministic_used = True
            target_sid = active_sid or "SIH26092-001"
            target_scheme = db.query(Scheme).filter(Scheme.scheme_id == target_sid).first()
            scheme_name_str = target_scheme.scheme_name if target_scheme else "the recommended scheme"
            profile = cls.build_profile_from_memory(session_id, req.profile)

            st = extracted_facts.get("state") or (profile.state if profile.state != "ALL_INDIA" else "All-India")
            cat = extracted_facts.get("social_category") or (getattr(profile.social_category, "value", profile.social_category) if profile.social_category else "Listed Category")
            act = extracted_facts.get("business_description") or getattr(profile, "activity_type", None) or "Enterprise Activity"

            elig_out = CopilotTools.check_eligibility(db, target_sid, profile)

            is_edu_scheme = bool(target_scheme and (getattr(target_scheme, "sector", "") in ("EDUCATION", "EDUCATION_AND_SCHOLARSHIP") or target_sid in ("SIH26092-083", "SIH26092-056", "SIH26092-059", "SIH26092-196")))
            if is_edu_scheme:
                if target_lang == "hi":
                    answer_parts.append(
                        f"**{scheme_name_str} (शिक्षा ऋण)** की सिफारिश के मुख्य कारण:\n\n"
                        f"1. **शिक्षा उद्देश्य एवं छात्र प्रोफ़ाइल**: आपकी उच्च शिक्षा/डिग्री आवश्यकता योजना के तहत पूरी तरह पात्र है।\n"
                        f"2. **ब्याज सब्सिडी (Interest Subsidy)**: मोरेटोरियम अवधि (कोर्स अवधि + 1 वर्ष) के दौरान 100% ब्याज अनुदान उपलब्ध है।\n"
                        f"3. **कोलैटरल-मुक्त सीमा (Collateral Terms)**: ₹7.5 लाख तक के ऋण पर CGFSEL के तहत किसी संपार्श्विक (Collateral) की आवश्यकता नहीं है।\n"
                        f"4. **आधिकारिक आवेदन**: विद्या लक्ष्मी पोर्टल (Vidya Lakshmi) या नोडल बैंक शाखा के माध्यम से पारदर्शी प्रक्रिया।"
                    )
                else:
                    answer_parts.append(
                        f"**Why {scheme_name_str} is recommended for your educational loan**:\n\n"
                        f"• **Student Profile & Course**: Matches your technical/higher education degree requirements.\n"
                        f"• **100% Interest Subsidy**: Full interest subsidy during the moratorium period (Course Period + 1 year) for eligible family income.\n"
                        f"• **Collateral-Free Financing**: Loans up to ₹7.5 Lakh require no third-party collateral under credit guarantee coverage (CGFSEL).\n"
                        f"• **Official Application Channel**: Routed through scheduled commercial banks via Vidya Lakshmi Portal (`https://www.vidyalakshmi.co.in/`)."
                    )
            elif target_lang == "hi":
                answer_parts.append(
                    f"**{scheme_name_str}** की सिफारिश के मुख्य कारण:\n\n"
                    f"1. **भौगोलिक अनुकूलता (Geography)**: आपका राज्य ({st}) योजना के कार्यक्षेत्र में शामिल है।\n"
                    f"2. **व्यापार/गतिविधि उपयुक्तता (Activity)**: आपकी गतिविधि ({act}) आधिकारिक योजना दिशानिर्देशों के अनुरूप है।\n"
                    f"3. **लाभार्थी श्रेणी (Target Beneficiary)**: श्रेणी ({cat}) योजना के तहत लक्षित समूहों में है।\n"
                    f"4. **वित्तीय अनुकूलता (Financial Fit)**: योजना की ऋण/सब्सिडी सीमा आपकी आवश्यकता के अनुकूल है।"
                )
            else:
                answer_parts.append(
                    f"**Why {scheme_name_str} is recommended for you**:\n\n"
                    f"• **Geography**: Your location ({st}) matches scheme coverage.\n"
                    f"• **Business Activity**: Your planned activity ({act}) falls within eligible sectors.\n"
                    f"• **Target Beneficiary**: Your category ({cat}) aligns with scheme beneficiary guidelines.\n"
                    f"• **Financial Fit**: Credit ceiling and capital assistance structure match micro/small enterprise needs."
                )
            actions.append(AICopilotAction(
                label=f"View Official Guidelines",
                action_type="VIEW_SCHEME",
                target_url=f"/schemes/{target_sid}"
            ))
            rich_cards.append(RichCard(
                card_type="ELIGIBILITY_CARD",
                title=f"Profile Match Reasoning — {scheme_name_str}",
                subtitle="Deterministic Alignment Analysis",
                data=elig_out
            ))

        # -------------------------------------------------------------
        # 2b. DETERMINISTIC CITIZEN PROFILE UPDATE / LOCATION ACKNOWLEDGEMENT
        # (0 RAG Calls, 0 Citations, 0 Fake Inflation, Stateful Accumulation)
        # -------------------------------------------------------------
        elif intent in ("PROFILE_UPDATE", "PROFILE_CORRECTION"):
            response_mode = "CASUAL"
            citations = []
            rich_cards = []
            actions = []
            deterministic_used = False

            # Facts accumulated in session memory
            name_val = extracted_facts.get("name")
            dist_val = extracted_facts.get("district")
            state_val = extracted_facts.get("state")
            age_val = extracted_facts.get("age")
            cat_val = extracted_facts.get("social_category")
            sector_val = extracted_facts.get("sector") or extracted_facts.get("business_description")
            loan_val = extracted_facts.get("requested_loan_amount")
            proj_val = extracted_facts.get("project_cost")

            has_name_in_msg = bool(re.search(r"\b(?:my\s+name\s+is|mera\s+naam|myself|naam\s+hai)\s+([A-Za-z]+)\b", msg_lower)) or bool(
                re.search(r"\b(?:i\s+am|i'm)\s+([a-z]+)\b", msg_lower) and not re.search(r"\b(?:i\s+am|i'm)\s+(?:from|a|an|the|sc|st|obc|gen|general|in|\d+)\b", msg_lower)
            )
            has_loc_in_msg = bool(dist_val and dist_val.lower() in msg_lower) or any(st.lower() in msg_lower for st in ["up", "uttar pradesh", "bihar", "maharashtra", "delhi", "mp", "rajasthan", "gujarat", "gorakhpur"])
            has_age_in_msg = bool(re.search(r"\b(?:age|\d{1,2}\s*(?:saal|years?|yrs?)|umar|उम्र)\b", msg_lower)) or bool(re.match(r"^\d{2}$", msg_lower.strip())) or bool(re.search(r"\b(?:i\s+am|i'm)\s+\d{1,2}\b", msg_lower))
            has_cat_in_msg = bool(re.search(r"\b(?:sc|st|obc|general|gen)\b", msg_lower))
            has_loan_in_msg = bool(re.search(r"\b(?:lakh|loan|chahiye|need|₹|rs)\b", msg_lower) and (loan_val or proj_val))

            has_income_in_msg = bool(re.search(r"\b(?:earn|salary|monthly\s+income|income)\b", msg_lower) and extracted_facts.get("monthly_income"))
            has_exp_in_msg = bool(re.search(r"\b(?:expense|expenses|kharcha|kharch)\b", msg_lower) and extracted_facts.get("monthly_expenses"))
            has_emi_in_msg = bool(re.search(r"\b(?:already\s+pay|pay|existing\s+emi|emi)\b", msg_lower) and extracted_facts.get("monthly_obligations"))

            if has_income_in_msg and extracted_facts.get("monthly_income"):
                inc_m = extracted_facts["monthly_income"]
                if target_lang == "hi":
                    answer_parts.append(f"नोट कर लिया: मासिक आय **₹{inc_m:,.0f}** दर्ज कर ली गई है। आपके मासिक घरेलू/व्यापारिक खर्च और मौजूदा ईएमआई (EMI) देनदारियां कितनी हैं?")
                    suggested_questions = ["मेरे मासिक खर्च 18,000 हैं", "मेरी कोई पुरानी ईएमआई नहीं है", "मुझे 3 लाख का लोन चाहिए"]
                else:
                    answer_parts.append(f"Recorded: Monthly income of **₹{inc_m:,.0f}** stored. What are your approximate monthly expenses and any existing debt/EMI obligations?")
                    suggested_questions = ["My monthly expenses are around 18,000", "I already pay 3,000 EMI", "I need a 3 lakh loan"]
            elif has_exp_in_msg and extracted_facts.get("monthly_expenses"):
                exp_m = extracted_facts["monthly_expenses"]
                if target_lang == "hi":
                    answer_parts.append(f"नोट कर लिया: मासिक खर्च **₹{exp_m:,.0f}** दर्ज कर लिया गया है। क्या आप पहले से कोई ऋण या ईएमआई (EMI) भर रहे हैं?")
                    suggested_questions = ["मैं पहले से 3,000 ईएमआई भर रहा हूँ", "कोई ईएमआई नहीं है", "मुझे 3 लाख का लोन चाहिए"]
                else:
                    answer_parts.append(f"Recorded: Monthly expenses of **₹{exp_m:,.0f}** stored. Do you already pay any monthly loan EMI or debt obligations?")
                    suggested_questions = ["I already pay 3,000 EMI", "No existing EMI obligations", "I need a 3 lakh loan"]
            elif has_emi_in_msg and extracted_facts.get("monthly_obligations"):
                emi_m = extracted_facts["monthly_obligations"]
                if target_lang == "hi":
                    answer_parts.append(f"नोट कर लिया: मौजूदा मासिक ईएमआई देनदारी **₹{emi_m:,.0f}** दर्ज कर ली गई है। आपको कितने लोन की आवश्यकता है?")
                    suggested_questions = ["मुझे 3 लाख का लोन चाहिए", "क्या मैं यह लोन चुका सकता हूँ?", "योजनाएं दिखाओ"]
                else:
                    answer_parts.append(f"Recorded: Existing monthly EMI debt of **₹{emi_m:,.0f}** stored. How much loan financing are you seeking?")
                    suggested_questions = ["I need a 3 lakh loan", "Can I afford this loan?", "Show eligible schemes"]
            elif has_name_in_msg and name_val:
                if target_lang == "hi":
                    answer_parts.append(f"नमस्ते {name_val}! 🙏 मैंने आपका नाम दर्ज कर लिया है। आप किस राज्य/ज़िले से हैं, और किस प्रकार का बिज़नेस शुरू करना चाहते हैं?")
                    suggested_questions = ["मैं गोरखपुर, उत्तर प्रदेश से हूँ", "डेयरी फार्मिंग शुरू करनी है", "मेरी पात्रता चेक करें"]
                else:
                    answer_parts.append(f"Nice to meet you, {name_val}! 👋 I've updated your profile with your name. Which State or District are you from, and what kind of business or scheme are you exploring?")
                    suggested_questions = ["I'm from Gorakhpur", "I want to start a dairy business", "Which schemes am I eligible for?"]
            elif has_loc_in_msg and (dist_val or state_val):
                loc_name = f"{dist_val}, {state_val}" if (dist_val and state_val and dist_val != state_val) else (dist_val or state_val)
                if target_lang == "hi":
                    answer_parts.append(f"बहुत बढ़िया! मैंने आपका स्थान **{loc_name}** दर्ज कर लिया है। आप किस प्रकार का कार्य या बिज़नेस शुरू करना चाहते हैं?")
                    suggested_questions = ["डेयरी फार्मिंग शुरू करनी है", "मेरी उम्र 24 साल है और मैं SC हूँ", "3 लाख का लोन चाहिए"]
                else:
                    answer_parts.append(f"Got it! I've recorded your location as **{loc_name}**. What business or enterprise are you planning to start or expand?")
                    suggested_questions = ["I want to start a dairy business", "I am 24 and SC", "I need a 3 loan"]
            elif (has_age_in_msg or has_cat_in_msg) and (age_val or cat_val):
                details = []
                if age_val: details.append(f"उम्र {age_val} वर्ष" if target_lang == "hi" else f"age {age_val}")
                if cat_val: details.append(f"{cat_val} श्रेणी" if target_lang == "hi" else f"{cat_val} category")
                det_str = ", ".join(details)
                if target_lang == "hi":
                    answer_parts.append(f"नोट कर लिया: **{det_str}**। आपको कितने लोन या वित्तीय सहायता की आवश्यकता है?")
                    suggested_questions = ["मुझे 3 लाख का लोन चाहिए", "डेयरी फार्मिंग के लिए योजना बताओ", "मेरी पात्रता चेक करें"]
                else:
                    answer_parts.append(f"Noted: **{det_str}** recorded. How much loan or project funding are you looking for?")
                    suggested_questions = ["I need a 3 lakh loan", "Which schemes am I eligible for?", "Calculate EMI for ₹3 lakh"]
            elif has_loan_in_msg and (loan_val or proj_val):
                amt = loan_val or proj_val
                amt_str = f"₹{amt:,.0f}"
                if target_lang == "hi":
                    answer_parts.append(f"समझ गया! आपकी लोन आवश्यकता **{amt_str}** दर्ज कर ली गई है। आप पूछ सकते हैं 'क्या मैं यह लोन चुका सकता हूँ?' (Financial Health) या अपनी योजनाएं देख सकते हैं।")
                    suggested_questions = ["क्या मैं यह लोन चुका सकता हूँ?", "अब मुझे सबसे अच्छी योजनाएं दिखाओ", "मेरी पात्रता चेक करें"]
                else:
                    answer_parts.append(f"Understood! Recorded your financing requirement of **{amt_str}**. You can ask 'Can I afford this loan?' to check your repayment capacity, or ask to see matching schemes.")
                    suggested_questions = ["Can I afford this loan?", "Now show me the best schemes", "Which schemes am I eligible for?"]
            else:
                if target_lang == "hi":
                    answer_parts.append("आपकी प्रोफाइल जानकारी अपडेट कर दी गई है! 👍 आप किस योजना या बिज़नेस के बारे में जानना चाहते हैं?")
                    suggested_questions = ["डेयरी फार्मिंग के लिए योजनाएं", "मेरी पात्रता चेक करें", "लोन कैलकुलेटर"]
                else:
                    answer_parts.append("I've updated your profile details! 👍 What schemes or business opportunities would you like to explore?")
                    suggested_questions = ["Schemes for dairy farming", "Which schemes am I eligible for?", "Calculate loan EMI"]

        # -------------------------------------------------------------
        # 3. CONVERSATIONAL SCHEME DISCOVERY & PROGRESSIVE PROFILING
        # -------------------------------------------------------------

        elif intent in ("SCHEME_DISCOVERY", "BUSINESS_PROFILE_INIT", "RECOMMENDATION_QUERY"):
            state_val = extracted_facts.get("state") or (getattr(req.profile.state, "value", req.profile.state) if req.profile and getattr(req.profile, "state", None) and getattr(req.profile, "state", None) != "ALL_INDIA" else None)
            dist_val = extracted_facts.get("district") or (getattr(req.profile, "district", None) if req.profile else None)
            cat_val = extracted_facts.get("social_category") or (getattr(req.profile.social_category, "value", req.profile.social_category) if req.profile and getattr(req.profile, "social_category", None) else None)
            age_val = extracted_facts.get("age") or (getattr(req.profile, "age", None) if req.profile else None)
            act_val = extracted_facts.get("business_description") or extracted_facts.get("activity_type") or (getattr(req.profile, "activity_type", None) or getattr(req.profile, "occupation", None) or getattr(req.profile, "applicant_type", None) if req.profile else None)

            proj_val = extracted_facts.get("project_cost") or (getattr(req.profile, "project_cost", None) if req.profile else None)
            savings_val = extracted_facts.get("liquid_savings") or (getattr(req.profile, "liquid_savings", None) if req.profile else None)
            loan_val = extracted_facts.get("requested_loan_amount") or (getattr(req.profile, "requested_loan_amount", None) if req.profile else None)

            # Check if this is an explicit trigger for recommendations
            rec_triggers = [
                "now show me the best schemes", "show me the best schemes", "show me best schemes",
                "show me schemes", "show best schemes", "show schemes", "find schemes", "list schemes",
                "yojna dikhao", "schemes dikhao", "yojana dikhao", "ab scheme batao", "best schemes batao",
                "schemes batao", "ab schemes batao", "now show schemes", "which scheme should i choose",
                "suggest schemes", "recommend schemes", "suitable for me", "which scheme is best",
                "schemes available", "available schemes", "subsidies available", "education loan schemes"
            ]
            is_explicit_rec = (
                str(intent) == "RECOMMENDATION_QUERY" or
                any(p in norm_msg for p in rec_triggers) or
                any(p in msg_lower for p in rec_triggers) or
                bool(re.search(r"\b(?:what|which)\s+.*(?:schemes?|yojna|yojana)\b", msg_lower)) or
                bool(re.search(r"\b(?:schemes?|yojna|yojana)\s+(?:available|dikhao|batao)\b", msg_lower))
            )

            # Progressive Questioning vs Recommendation Gate (Priority 2)
            has_activity = bool(act_val)
            has_location = bool(state_val or dist_val)
            has_category = bool(cat_val or age_val)
            has_financial = bool(proj_val or savings_val or loan_val or extracted_facts.get("annual_income") or (req.profile and getattr(req.profile, "annual_income", None)))

            loc_label = dist_val or state_val or "All-India"
            act_label = act_val or "Enterprise"

            if not is_explicit_rec and not (has_activity and has_location and has_category and has_financial):
                response_mode = "CLARIFICATION"
                if not has_activity:
                    if target_lang == "hi":
                        answer_parts.append(
                            "नमस्ते! 🙏 आपकी आवश्यकताओं के अनुकूल सटीक सरकारी योजनाएं खोजने के लिए कृपया बताएं:\n\n"
                            "1. **आप किस प्रकार का बिज़नेस/कार्य शुरू या बढ़ाना चाहते हैं?** (जैसे डेयरी, सिलाई, किराना, मैन्युफैक्चरिंग)\n"
                            "2. **आप किस राज्य और ज़िले (State/District) से हैं?** (जैसे गोरखपुर, उत्तर प्रदेश)"
                        )
                        suggested_questions = ["डेयरी फार्मिंग शुरू करनी है", "सिलाई का काम", "किराना दुकान", "उत्तर प्रदेश, गोरखपुर"]
                    else:
                        answer_parts.append(
                            "Namaste! 🙏 To recommend the most accurate government schemes with verified subsidies and loan facilities, please tell me:\n\n"
                            "1. **What business or activity are you planning to start or expand?** (e.g. Dairy farming, retail shop, tailoring, manufacturing)\n"
                            "2. **Which State and District are you located in?** (e.g. Gorakhpur, Uttar Pradesh)"
                        )
                        suggested_questions = ["I want to start a dairy business", "Tailoring enterprise", "Retail store", "Gorakhpur, Uttar Pradesh"]

                elif not has_location:
                    if target_lang == "hi":
                        answer_parts.append(
                            f"बहुत बढ़िया! **{act_label}** के लिए केंद्र और राज्य सरकार की कई विशेष सब्सिडी योजनाएं हैं।\n\n"
                            "सटीक योजनाएं व स्थानीय बैंक विकल्प खोजने के लिए कृपया बताएं:\n"
                            "1. **आप किस राज्य और ज़िले से हैं?** (जैसे गोरखपुर, उत्तर प्रदेश)\n"
                            "2. **आपकी उम्र और श्रेणी (General, OBC, SC, ST) क्या है?** (विशेष श्रेणी में अधिक सब्सिडी मिलती है)"
                        )
                        suggested_questions = ["गोरखपुर, उत्तर प्रदेश", "बिहार", "मेरी उम्र 24 साल है और मैं SC हूँ", "सामान्य वर्ग (General)"]
                    else:
                        answer_parts.append(
                            f"Great! Starting a **{act_label}** enterprise has strong central and state government support schemes with capital subsidies and credit guarantees.\n\n"
                            "To find the exact schemes and bank options in your region, please tell me:\n"
                            "1. **Which State and District are you located in?** (e.g. Gorakhpur, Uttar Pradesh)\n"
                            "2. **What is your age and social category (General, OBC, SC, ST)?** (Statutory categories qualify for higher subsidies)"
                        )
                        suggested_questions = ["I'm from Gorakhpur", "Uttar Pradesh", "I'm 24 and SC", "General category"]

                elif not has_category:
                    if target_lang == "hi":
                        answer_parts.append(
                            f"नोट कर लिया: **{loc_label}** में **{act_label}**।\n\n"
                            "वैधानिक श्रेणी लाभ व सही सब्सिडी दर तय करने के लिए बताएं:\n"
                            "1. **आपकी उम्र और सोशल कैटेगरी (General, OBC, SC, ST) क्या है?** (PMEGP में विशेष वर्ग को 25%-35% तथा सामान्य को 15%-25% सब्सिडी मिलती है)\n"
                            "2. **आप अपनी बचत से कितना निवेश (मार्जिन) लगा सकते हैं?**"
                        )
                        suggested_questions = ["मेरी उम्र 24 साल है और मैं SC हूँ", "ओबीसी (OBC)", "सामान्य वर्ग", "मैं 3 लाख निवेश कर सकता हूँ"]
                    else:
                        answer_parts.append(
                            f"Noted: **{loc_label}** for **{act_label}**.\n\n"
                            "To evaluate your statutory eligibility and applicable subsidy rates:\n"
                            "1. **What is your age and social category (General, OBC, SC, ST)?** (Special categories qualify for up to 35% subsidy in PMEGP vs 15%-25% for general)\n"
                            "2. **How much capital can you invest from your own savings**, or what loan amount do you need?"
                        )
                        suggested_questions = ["I'm 24 and SC", "OBC category", "General category", "I can invest around 3 lakh"]

                elif not has_financial:
                    cat_display = cat_val or "Special"
                    age_str = f", {age_val} years old" if age_val else ""
                    if target_lang == "hi":
                        answer_parts.append(
                            f"समझ गया: **{cat_display} श्रेणी**{age_str}, स्थान: **{loc_label}**, गतिविधि: **{act_label}**।\n"
                            "विशेष श्रेणी के तहत आप अधिकतम सब्सिडी और न्यूनतम मार्जिन अंशदान के पात्र हैं।\n\n"
                            "वित्तीय क्षमता तय करने के लिए:\n"
                            "• **आप अपनी बचत से कितना निवेश कर सकते हैं**, या आपको कितने ऋण (Loan) की आवश्यकता है?"
                        )
                        suggested_questions = ["मैं 3 लाख रुपये लगा सकता हूँ", "5 लाख का लोन चाहिए", "कुल प्रोजेक्ट 10 लाख है"]
                    else:
                        answer_parts.append(
                            f"Got it: **{cat_display} category**{age_str} in **{loc_label}** for **{act_label}**.\n"
                            "Under statutory priority guidelines, you qualify for enhanced subsidy rates and reduced own margin money requirements.\n\n"
                            "To evaluate financial fit and required margin money:\n"
                            "• **How much capital can you invest from your savings**, or what is your expected project cost / loan amount?"
                        )
                        suggested_questions = ["I can invest around 3 lakh", "I need a ₹5 lakh loan", "Total project cost ₹10 lakh"]

                else:
                    # All 4 dimensions gathered, prompt user to view recommendations
                    sav_str = f"₹{savings_val:,.0f}" if savings_val else (f"₹{loan_val:,.0f} loan" if loan_val else "₹3,00,000")
                    if target_lang == "hi":
                        answer_parts.append(
                            f"बहुत अच्छा! आपकी जानकारी दर्ज हो गई है:\n"
                            f"• **गतिविधि**: {act_label}\n"
                            f"• **स्थान**: {loc_label}\n"
                            f"• **लाभार्थी श्रेणी**: {cat_val or 'दर्ज'}, उम्र: {age_val or 'पात्र'}\n"
                            f"• **स्वयं का निवेश (मार्जिन)**: {sav_str}\n\n"
                            f"जब आप तैयार हों, **'अब मुझे सबसे अच्छी योजनाएं दिखाओ'** कहें ताकि हम आपकी सत्यापित सिफारिशें दिखा सकें!"
                        )
                        suggested_questions = ["अब मुझे सबसे अच्छी योजनाएं दिखाओ", "क्या मैं इस लोन को वहन कर सकता हूँ?", "निकटतम अधिकृत बैंक शाखा"]
                    else:
                        answer_parts.append(
                            f"Understood! Your citizen profile is now well-defined:\n"
                            f"• **Enterprise Activity**: {act_label}\n"
                            f"• **Location**: {loc_label}\n"
                            f"• **Applicant Category**: {cat_val or 'Recorded'}, Age: {age_val or 'Eligible'}\n"
                            f"• **Own Contribution / Savings**: {sav_str}\n\n"
                            f"Whenever you're ready, say **'Now show me the best schemes'** to view your ranked, personalized recommendations with verified subsidies, partner banks, and required documents!"
                        )
                        suggested_questions = ["Now show me the best schemes", "Can I afford this loan?", "Nearest place to proceed"]

            else:
                # Retrieve deterministic recommendations with tiered classification (Priority 1)
                response_mode = "TOOL_RESULT"
                profile = cls.build_profile_from_memory(session_id, req.profile)
                rec_out = CopilotTools.get_recommendations(db, profile, top_k=3)
                deterministic_used = True
                recs = rec_out.get("recommendations", [])

                if proj_val or savings_val or loan_val:
                    if target_lang == "hi":
                        fin_lines = ["📊 **वित्तीय परिदृश्य विश्लेषण (Financial Breakdown)**:"]
                        if proj_val: fin_lines.append(f"• **कुल प्रोजेक्ट लागत**: ₹{proj_val:,.0f}")
                        if savings_val: fin_lines.append(f"• **आपकी अपनी बचत / मार्जिन**: ₹{savings_val:,.0f}")
                        if loan_val: fin_lines.append(f"• **आवश्यक बैंक ऋण (Financing Required)**: ₹{loan_val:,.0f}")
                        answer_parts.append("\n".join(fin_lines) + "\n")
                    else:
                        fin_lines = ["📊 **Financial Scenario Breakdown**:"]
                        if proj_val: fin_lines.append(f"• **Total Project Cost**: ₹{proj_val:,.0f}")
                        if savings_val: fin_lines.append(f"• **Your Own Contribution**: ₹{savings_val:,.0f}")
                        if loan_val: fin_lines.append(f"• **Loan Financing Required**: ₹{loan_val:,.0f}")
                        answer_parts.append("\n".join(fin_lines) + "\n")

                if target_lang == "hi":
                    answer_parts.append(
                        f"आपकी प्रोफाइल (**स्थान**: {loc_label}, **गतिविधि**: {act_label}, **श्रेणी**: {cat_val or 'दर्ज'}) के आधार पर आधिकारिक रूप से मूल्यांकित योजनाएं:"
                    )
                else:
                    answer_parts.append(
                        f"Based on your accumulated profile (**Location**: {loc_label}, **Activity**: {act_label}, **Category**: {cat_val or 'Recorded'}), here are your ranked official government schemes:"
                    )

                for idx, item in enumerate(recs, 1):
                    score_val = item.get("score", item.get("soft_score", 90))
                    match_pct = int(score_val)
                    tier_badge = item.get("match_tier", "ELIGIBLE").replace("_", " ")

                    fin_suit = item.get("financial_suitability")
                    sub_amt = item.get("available_subsidy_amount")
                    est_emi = item.get("estimated_monthly_installment")
                    req_margin = item.get("required_own_contribution")

                    fin_details_text = []
                    if fin_suit:
                        fin_details_text.append(f"• **Financial Fit**: {fin_suit.replace('_', ' ').title()}")
                    if sub_amt:
                        fin_details_text.append(f"• **Available Subsidy**: Up to ₹{sub_amt:,.0f}")
                    if req_margin is not None:
                        fin_details_text.append(f"• **Required Margin Money**: ₹{req_margin:,.0f}")
                    if est_emi:
                        fin_details_text.append(f"• **Estimated EMI**: ₹{est_emi:,.0f}/month")

                    fin_block = ("\n" + "\n".join(fin_details_text)) if fin_details_text else ""
                    why_text = item.get("why_it_matches") or f"Directly aligns with {act_label} in {loc_label}"
                    cond_list = item.get("key_conditions", [])
                    cond_str = "; ".join(cond_list[:3]) if cond_list else "Preliminary statutory criteria satisfied"
                    docs_list = item.get("required_documents", [])
                    docs_str = ", ".join(docs_list[:4]) if docs_list else "Aadhaar Card, Project Report, Bank Details"
                    channel_str = item.get("application_channel", "Online Portal & Bank Branches")
                    partner_str = item.get("partner_availability", "Available at authorized branches")
                    portal_url = item.get("official_portal") or "https://www.myscheme.gov.in"

                    # Grounded Recommendation Output with all Required Attributes (Priority 1)
                    answer_parts.append(
                        f"**{idx}. {item['scheme_name']}** — *[{tier_badge}] ({match_pct}% Match)*\n"
                        f"• **Ministry**: {item.get('ministry', 'Government of India')}\n"
                        f"• **Why it matches**: {why_text}\n"
                        f"• **Important Conditions**: {cond_str}\n"
                        f"• **Application Route & Partners**: {channel_str} ({partner_str})\n"
                        f"• **Required Documents**: {docs_str}\n"
                        f"• **Official Portal**: [{portal_url}]({portal_url})"
                        f"{fin_block}"
                    )
                    actions.append(AICopilotAction(
                        label=f"View {item['scheme_name'][:20]}",
                        action_type="VIEW_SCHEME",
                        target_url=f"/schemes/{item['scheme_id']}"
                    ))
                    card_data = dict(item)
                    card_data["match_score"] = round(score_val / 100.0, 3) if score_val > 1.0 else score_val
                    card_data["why_matches"] = why_text
                    card_data["key_conditions"] = cond_list or ["Preliminary statutory criteria satisfied"]
                    card_data["required_documents"] = docs_list or ["Aadhaar Card", "Project Report", "Bank Details"]
                    card_data["partner_availability"] = partner_str
                    card_data["financial_fit"] = fin_suit or "COMPATIBLE"
                    card_data["match_tier"] = item.get("match_tier") or "ELIGIBLE"

                    rich_cards.append(RichCard(
                        card_type="SCHEME_CARD",
                        title=item["scheme_name"],
                        subtitle=f"Tier: {tier_badge} | Match: {match_pct}%",
                        data=card_data
                    ))

                suggested_questions = [
                    "Can I afford this financing?",
                    "Nearest place to proceed",
                    "What documents are required?",
                    "PMEGP aur Mudra me difference?"
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

            elif intent == "AFFORDABILITY_QUERY":
                response_mode = "TOOL_RESULT"
                # Check if scheme is targeted
                if target_sid and target_scheme:
                    # TEST D: Scheme is non-credit -> Financial Health is NOT APPLICABLE
                    if not is_credit_target or (target_scheme.loan_available and target_scheme.loan_available.strip().upper() in ("NO", "FALSE", "N")):
                        deterministic_used = True
                        answer_parts.append(
                            f"**Financial Health Assessment Not Applicable for '{target_scheme.scheme_name}'**:\n\n"
                            f"This scheme does not provide credit or loan financing; assistance is provided directly as a **grant, subsidy, scholarship, or welfare benefit**.\n\n"
                            f"Loan affordability and debt service repayment assessments are only applicable to borrowing schemes."
                        )
                        actions.append(AICopilotAction(
                            label="View Scheme Details",
                            action_type="VIEW_SCHEME",
                            target_url=f"/schemes/{target_sid}"
                        ))
                    else:
                        # Scheme is credit-based: Check if interest rate & tenure are specified (TEST C)
                        actual_rate = target_scheme.interest_rate or target_scheme.interest_rate_max or target_scheme.interest_rate_min
                        actual_tenure = target_scheme.repayment_period_max_months or target_scheme.repayment_period_min_months

                        if actual_rate is None or actual_tenure is None:
                            deterministic_used = True
                            loan_lim_str = f"• Loan Limit: ₹{float(target_scheme.max_loan_amount):,.0f}\n" if target_scheme.max_loan_amount else ""
                            sub_lim_str = f"• Margin Subsidy: {float(target_scheme.subsidy_percentage)}%\n" if target_scheme.subsidy_percentage else ""
                            answer_parts.append(
                                f"**Financial Health Advisory — '{target_scheme.scheme_name}'**:\n\n"
                                f"Financial health cannot be fully assessed because the applicable lender interest rate/tenure is not specified in official guidelines. "
                                f"Your actual interest rate depends on the financing institution (bank/NBFC), so a complete affordability assessment cannot be finalized yet.\n\n"
                                f"{loan_lim_str}{sub_lim_str}"
                                f"You can test different illustrative interest rates in our Financial Health Calculator."
                            )
                            actions.append(AICopilotAction(
                                label="Open Financial Health Calculator",
                                action_type="CALCULATE_EMI",
                                target_url=f"/calculator?tab=health&scheme={target_sid}"
                            ))
                        else:
                            # Official rate and tenure are specified on the scheme!
                            mon_inc = extracted_facts.get("monthly_income")
                            ann_inc = extracted_facts.get("annual_income") or (getattr(profile, "annual_income", None) if profile else None)
                            if mon_inc is None and ann_inc:
                                mon_inc = round(float(ann_inc) / 12.0, 2)

                            # TEST B: Missing income -> asks for income, does not guess
                            if mon_inc is None or mon_inc <= 0:
                                response_mode = "CLARIFICATION"
                                answer_parts.append(
                                    "To assess whether this loan fits your finances, I need your approximate monthly income and monthly expenses. "
                                    "Please share your monthly earnings (e.g. 'I earn 30,000 per month') and monthly expenses (e.g. 'My expenses are 18,000')."
                                )
                                suggested_questions = [
                                    "I earn 30,000 per month",
                                    "My monthly expenses are 18,000",
                                    "I have no monthly EMI"
                                ]
                            else:
                                mon_exp = extracted_facts.get("monthly_expenses", 0.0)
                                mon_ob = extracted_facts.get("monthly_obligations", 0.0)
                                req_loan = extracted_facts.get("requested_loan_amount", 200000.0)

                                from app.schemas.financial_health import FinancialHealthInput
                                from app.engine.financial_health import DeterministicFinancialHealthEngine
                                from app.engine.calculator import DeterministicFinancialEngine

                                proposed_emi = DeterministicFinancialEngine.calculate_installment(
                                    principal=Decimal(str(req_loan)),
                                    annual_rate_percent=Decimal(str(actual_rate)),
                                    total_periods=int(actual_tenure),
                                    periods_per_year=12
                                )
                                total_debt_serv = Decimal(str(mon_ob)) + proposed_emi

                                eval_input = FinancialHealthInput(
                                    annual_income=Decimal(str(mon_inc * 12)),
                                    requested_loan_amount=Decimal(str(req_loan)),
                                    project_cost=Decimal(str(req_loan * 1.25)),
                                    monthly_obligations=total_debt_serv,
                                    monthly_expenses=Decimal(str(mon_exp)),
                                    liquid_savings=Decimal(str(extracted_facts.get("liquid_savings", 0.0)))
                                )
                                health_res = DeterministicFinancialHealthEngine.evaluate(eval_input)
                                deterministic_used = True

                                status_badge = "🟢 HEALTHY / COMFORTABLE" if health_res.status == "HEALTHY" else (
                                    "🟡 MODERATE / MANAGEABLE" if health_res.status == "MODERATE" else (
                                        "🔴 HIGH REPAYMENT BURDEN" if health_res.status in ("STRESSED", "HIGH_RISK") else "⚪ INSUFFICIENT INFO"
                                    )
                                )
                                foir_val = ((total_debt_serv / Decimal(str(mon_inc))) * Decimal("100")).quantize(Decimal("0.1"))
                                rem_disp = Decimal(str(mon_inc)) - total_debt_serv - Decimal(str(mon_exp))

                                answer_parts.append(
                                    f"### Financial Health & Affordability Assessment — '{target_scheme.scheme_name}'\n\n"
                                    f"**Overall Affordability Status**: {status_badge}\n\n"
                                    f"• **Monthly Family Income**: ₹{mon_inc:,.0f}\n"
                                    f"• **Monthly Living Expenses**: ₹{mon_exp:,.0f}\n"
                                    f"• **Existing Debt Obligations**: ₹{mon_ob:,.0f}/month\n"
                                    f"• **Proposed Scheme EMI**: ₹{float(proposed_emi):,.0f}/month (at {actual_rate}% p.a. for {actual_tenure} months)\n"
                                    f"• **Total Repayment Burden**: {foir_val}% of monthly income\n"
                                    f"• **Estimated Remaining Monthly Amount**: ₹{float(rem_disp):,.0f}/month\n\n"
                                    f"*{health_res.summary_headline}*"
                                )
                                actions.append(AICopilotAction(
                                    label="Adjust Loan Amount",
                                    action_type="CALCULATE_EMI",
                                    target_url=f"/calculator?tab=health&scheme={target_sid}&amount={req_loan}"
                                ))
                                actions.append(AICopilotAction(
                                    label="View EMI Breakdown",
                                    action_type="CALCULATE_EMI",
                                    target_url=f"/calculator?scheme={target_sid}&amount={req_loan}"
                                ))
                                rich_cards.append(RichCard(
                                    card_type="FINANCIAL_HEALTH_CARD",
                                    title=f"Financial Health: {target_scheme.scheme_name}",
                                    subtitle=f"Status: {health_res.status.value}",
                                    data=health_res.model_dump()
                                ))
                else:
                    # General loan affordability inquiry (TEST A & E)
                    mon_inc = extracted_facts.get("monthly_income")
                    ann_inc = extracted_facts.get("annual_income") or (getattr(profile, "annual_income", None) if profile else None)
                    if mon_inc is None and ann_inc:
                        mon_inc = round(float(ann_inc) / 12.0, 2)

                    # TEST B: Missing income -> asks for income, does not guess
                    if mon_inc is None or mon_inc <= 0:
                        response_mode = "CLARIFICATION"
                        answer_parts.append(
                            "To assess whether this loan fits your finances, I need your approximate monthly income and monthly expenses. "
                            "Please share how much you earn (e.g. 'I earn 30,000 per month') and your monthly expenses (e.g. 'My expenses are 18,000')."
                        )
                        suggested_questions = [
                            "I earn 30,000 per month",
                            "My monthly expenses are 18,000",
                            "I already pay 3,000 EMI"
                        ]
                    else:
                        mon_exp = extracted_facts.get("monthly_expenses", 0.0)
                        mon_ob = extracted_facts.get("monthly_obligations", 0.0)
                        req_loan = extracted_facts.get("requested_loan_amount", 200000.0)
                        def_rate = Decimal("9.0")
                        def_tenure = 60

                        from app.schemas.financial_health import FinancialHealthInput
                        from app.engine.financial_health import DeterministicFinancialHealthEngine
                        from app.engine.calculator import DeterministicFinancialEngine

                        proposed_emi = DeterministicFinancialEngine.calculate_installment(
                            principal=Decimal(str(req_loan)),
                            annual_rate_percent=def_rate,
                            total_periods=def_tenure,
                            periods_per_year=12
                        )
                        total_debt_serv = Decimal(str(mon_ob)) + proposed_emi

                        eval_input = FinancialHealthInput(
                            annual_income=Decimal(str(mon_inc * 12)),
                            requested_loan_amount=Decimal(str(req_loan)),
                            project_cost=Decimal(str(req_loan * 1.25)),
                            monthly_obligations=total_debt_serv,
                            monthly_expenses=Decimal(str(mon_exp)),
                            liquid_savings=Decimal(str(extracted_facts.get("liquid_savings", 0.0)))
                        )
                        health_res = DeterministicFinancialHealthEngine.evaluate(eval_input)
                        deterministic_used = True

                        status_badge = "🟢 HEALTHY / COMFORTABLE" if health_res.status == "HEALTHY" else (
                            "🟡 MODERATE / MANAGEABLE" if health_res.status == "MODERATE" else (
                                "🔴 HIGH REPAYMENT BURDEN" if health_res.status in ("STRESSED", "HIGH_RISK") else "⚪ INSUFFICIENT INFO"
                            )
                        )
                        foir_val = ((total_debt_serv / Decimal(str(mon_inc))) * Decimal("100")).quantize(Decimal("0.1"))
                        rem_disp = Decimal(str(mon_inc)) - total_debt_serv - Decimal(str(mon_exp))

                        answer_parts.append(
                            f"### Financial Health & Affordability Assessment\n\n"
                            f"**Overall Affordability Status**: {status_badge}\n\n"
                            f"• **Monthly Family Income**: ₹{mon_inc:,.0f}\n"
                            f"• **Monthly Living Expenses**: ₹{mon_exp:,.0f}\n"
                            f"• **Existing Debt Obligations**: ₹{mon_ob:,.0f}/month\n"
                            f"• **Proposed New EMI**: ₹{float(proposed_emi):,.0f}/month (illustrative standard benchmark rate {def_rate}% p.a. for {def_tenure} months)\n"
                            f"• **Repayment Burden (FOIR)**: {foir_val}% of monthly income\n"
                            f"• **Estimated Remaining Monthly Amount**: ₹{float(rem_disp):,.0f}/month\n\n"
                            f"*{health_res.summary_headline}*"
                        )
                        actions.append(AICopilotAction(
                            label="Adjust Loan Amount",
                            action_type="CALCULATE_EMI",
                            target_url=f"/calculator?tab=health&amount={req_loan}"
                        ))
                        actions.append(AICopilotAction(
                            label="View EMI Breakdown",
                            action_type="CALCULATE_EMI",
                            target_url=f"/calculator?amount={req_loan}"
                        ))
                        rich_cards.append(RichCard(
                            card_type="FINANCIAL_HEALTH_CARD",
                            title=f"Financial Health: ₹{req_loan:,.0f} Loan",
                            subtitle=f"Status: {health_res.status.value}",
                            data=health_res.model_dump()
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
                        f"Note: Final statutory eligibility is determined exclusively by the concerned government department."
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

            elif intent == "EXPLAIN_REJECTION":
                response_mode = "TOOL_RESULT"
                deterministic_used = True
                target_sid = active_sid or "SIH26092-001"
                target_scheme = db.query(Scheme).filter(Scheme.scheme_id == target_sid).first()
                scheme_name_str = target_scheme.scheme_name if target_scheme else "Government Scheme"

                elig_out = CopilotTools.check_eligibility(db, target_sid, profile)
                failed_reasons = elig_out.get("failed_rules", [])
                if not failed_reasons and not elig_out.get("is_eligible"):
                    failed_reasons = [exp for exp in elig_out.get("explanations", []) if any(w in exp.lower() for w in ["not", "fail", "exceed", "disqualif", "ineligible"])]

                if target_lang == "hi":
                    if failed_reasons:
                        reasons_str = "\n".join([f"• ❌ {r}" for r in failed_reasons])
                        answer_parts.append(
                            f"**{scheme_name_str}** के वैधानिक पात्रता मूल्यांकन के अनुसार, आप निम्नलिखित कारणों से सीधे पात्र नहीं हैं:\n\n"
                            f"{reasons_str}\n\n"
                            f"📌 **मूल्यांकित आयाम**:\n"
                            f"• राज्य/स्थान प्रतिबंध, आयु सीमा, वार्षिक आय सीमा, अथवा व्यावसायिक क्षेत्र का असंतुलन।\n\n"
                            f"💡 **आगे का मार्ग**: आप अपने प्रोफाइल विवरण में सुधार कर सकते हैं या नीचे दिए गए बटन से वैकल्पिक योजनाएं देख सकते हैं।"
                        )
                    else:
                        answer_parts.append(
                            f"आपके वर्तमान प्रोफाइल के अनुसार **{scheme_name_str}** के मुख्य वैधानिक मानदंड पूरे हैं। यदि आपका आवेदन अस्वीकृत हुआ है, तो सामान्य गैर-वैधानिक कारण:\n"
                            f"• सिबिल (CIBIL) स्कोर या पूर्व बैंक डिफ़ॉल्ट\n"
                            f"• बैंक परियोजना रिपोर्ट (DPR) तकनीकी व्यवहार्यता\n"
                            f"• आधार/पैन/खाता दस्तावेजों में नाम या पते का बेमेल"
                        )
                else:
                    if failed_reasons:
                        reasons_str = "\n".join([f"• ❌ {r}" for r in failed_reasons])
                        answer_parts.append(
                            f"Deterministic Eligibility Engine Evaluation for **{scheme_name_str}**:\n\n"
                            f"You do not currently satisfy statutory eligibility criteria due to:\n"
                            f"{reasons_str}\n\n"
                            f"📌 **Evaluated Dimensions**:\n"
                            f"• State domicile / territorial availability\n"
                            f"• Age or income ceiling statutory limits\n"
                            f"• Target beneficiary or business activity restrictions\n\n"
                            f"💡 **Recommended Action**: Review your profile details or explore alternative schemes suited to your profile."
                        )
                    else:
                        answer_parts.append(
                            f"Your submitted profile satisfies the preliminary statutory rules for **{scheme_name_str}**. If rejected at the sanctioning branch or departmental level, common reasons include:\n"
                            f"• Low CIBIL/Credit score or prior NPA default\n"
                            f"• Incomplete Detailed Project Report (DPR) or financial unviability\n"
                            f"• Inconsistency in KYC/caste documentation"
                        )

                actions.append(AICopilotAction(
                    label="Find Alternative Schemes",
                    action_type="VIEW_SCHEME",
                    target_url="/schemes"
                ))
                rich_cards.append(RichCard(
                    card_type="ELIGIBILITY_CARD",
                    title=f"Rejection / Eligibility Explanation — {scheme_name_str}",
                    subtitle="Authoritative Rule Verification",
                    data=elig_out
                ))

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

            elif intent in ("APPLICATION_QUERY", "APPLICATION_TRACKING_INQUIRY"):
                is_tracking = (intent == "APPLICATION_TRACKING_INQUIRY") or bool(
                    re.search(r"\b(?:track|status|under\s+review|kya\s+hai\s+status|review)\b", norm_msg or "", re.IGNORECASE) or
                    re.search(r"\b(?:track|status|under\s+review|kya\s+hai\s+status|review)\b", msg_lower or "", re.IGNORECASE)
                )
                if is_tracking:
                    response_mode = "GROUNDED"
                    deterministic_used = True
                    scheme_name_str = target_scheme.scheme_name if target_scheme else "government schemes"
                    portal_url = target_scheme.official_portal if (target_scheme and target_scheme.official_portal) else ("https://www.vidyalakshmi.co.in/" if (target_scheme and "education" in str(target_scheme.scheme_name).lower()) else "https://myscheme.gov.in")
                    target_url_str = f"/schemes/{target_sid}" if target_sid else "/schemes"

                    answer_parts.append(
                        f"**Application Tracking & Processing Status Policy**:\n\n"
                        f"YojnaSetu is a scheme discovery, eligibility assessment, financial advisory, and partner navigation engine. **YojnaSetu does NOT maintain or display simulated application tracking states** (such as 'submitted', 'under review', 'approved', or 'rejected') because it is not integrated with internal government application processing workflow systems.\n\n"
                        f"To track the authentic real-time status of your application for **{scheme_name_str}**:\n"
                        f"1. **Check Official Portal**: Visit the official nodal portal ({portal_url}) and log in with your application acknowledgment / reference number.\n"
                        f"2. **Contact Sanctioning Branch**: If you applied via an authorized bank branch or Common Service Centre (CSC), inquire directly with your submission receipt.\n"
                        f"3. **Official Notifications**: Official approval decisions and disbursement alerts are communicated directly by the nodal ministry or lending bank via SMS and postal communication."
                    )
                    actions.append(AICopilotAction(
                        label="Open Official Portal",
                        action_type="VIEW_SCHEME",
                        target_url=portal_url
                    ))
                    actions.append(AICopilotAction(
                        label="Find Authorized Branch",
                        action_type="LOCATE_PARTNER",
                        target_url=f"/locator?scheme={target_sid}" if target_sid else "/locator"
                    ))
                else:
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
                deterministic_used = True
                scheme_name_str = target_scheme.scheme_name if target_scheme else "Government Scheme"
                
                from app.services.geo_partner_service import GeoPartnerLocatorService
                
                dist_str = extracted_facts.get("district") or (profile.district if profile else None)
                state_str = extracted_facts.get("state") or (profile.state if profile and profile.state != "ALL_INDIA" else None)
                
                # Determine coordinate anchor based on user location
                lat, lon = 26.7606, 83.3732  # Gorakhpur default in UP
                if dist_str and "lucknow" in dist_str.lower():
                    lat, lon = 26.8467, 80.9462
                elif dist_str and "delhi" in dist_str.lower():
                    lat, lon = 28.6139, 77.2090
                elif dist_str and "patna" in dist_str.lower():
                    lat, lon = 25.5941, 85.1376
                elif dist_str and "mumbai" in dist_str.lower():
                    lat, lon = 19.0760, 72.8777
                elif dist_str and "gorakhpur" in dist_str.lower():
                    lat, lon = 26.7606, 83.3732
                elif state_str and "uttar" in state_str.lower():
                    lat, lon = 26.8467, 80.9462
                
                # Check if scheme is online-only
                is_online_only = bool(
                    target_scheme and (
                        getattr(target_scheme, "application_mode", "") == "ONLINE_ONLY" or
                        target_sid in ("SIH26092-083", "SIH26092-196")
                    )
                )
                portal_url = target_scheme.official_portal if (target_scheme and target_scheme.official_portal) else "https://www.myscheme.gov.in"
                
                if is_online_only:
                    if target_lang == "hi":
                        answer_parts.append(
                            f"**{scheme_name_str} — आवेदन मार्ग एवं चैनल पार्टनर**:\n\n"
                            f"ℹ️ **डिजिटल-प्रथम योजना**: यह योजना पूरी तरह से आधिकारिक राष्ट्रीय पोर्टल के माध्यम से ऑनलाइन संचालित होती है।\n"
                            f"• **भौतिक शाखा की आवश्यकता**: प्रारंभिक आवेदन के लिए किसी बैंक शाखा में जाने की आवश्यकता नहीं है।\n"
                            f"• **आधिकारिक आवेदन पोर्टल**: [{portal_url}]({portal_url})\n"
                            f"• **नोडल विभाग**: {target_scheme.implementing_agency or target_scheme.ministry or 'भारत सरकार'}"
                        )
                    else:
                        answer_parts.append(
                            f"**Authorized Application Channel for '{scheme_name_str}'**:\n\n"
                            f"ℹ️ **Digital-First Scheme**: This scheme operates directly via the official national portal.\n"
                            f"• **Physical Branch Requirement**: No physical branch visit is required for initial application submission.\n"
                            f"• **Official Application Portal**: [{portal_url}]({portal_url})\n"
                            f"• **Nodal Agency**: {target_scheme.implementing_agency or target_scheme.ministry or 'Government of India'}"
                        )
                    actions.append(AICopilotAction(
                        label="Open Official Portal",
                        action_type="VIEW_SCHEME",
                        target_url=portal_url
                    ))
                else:
                    partners = GeoPartnerLocatorService.find_nearest_partners(
                        db=db,
                        latitude=lat,
                        longitude=lon,
                        radius_km=100.0,
                        district=dist_str,
                        state=state_str,
                        scheme_id=target_sid,
                        limit=5
                    )
                    if not partners:
                        partners = GeoPartnerLocatorService.find_nearest_partners(
                            db=db,
                            latitude=lat,
                            longitude=lon,
                            radius_km=100.0,
                            district=dist_str,
                            state=state_str,
                            limit=5
                        )
                    
                    loc_desc = f"near {dist_str or state_str or 'your location'}"
                    if partners:
                        if target_lang == "hi":
                            answer_parts.append(f"**{scheme_name_str}** के लिए सत्यापित अधिकृत चैनल पार्टनर ({loc_desc}):\n")
                            for p_item in partners[:4]:
                                p = p_item["partner"]
                                dist = p_item["distance_km"]
                                prec = p_item.get("coordinate_precision", "EXACT_ADDRESS")
                                loc_type = "सटीक शाखा पता" if prec == "EXACT_ADDRESS" else "ज़िला केंद्र (अनुमानित दूरी)"
                                
                                # Financial intelligence facts
                                fin_lines = []
                                f_intel = p_item.get("financial_intelligence", {})
                                if "NNPA_PERCENT" in f_intel:
                                    fin_lines.append(f"  📊 नेट एनपीए (NNPA): {f_intel['NNPA_PERCENT']['value']}% ({f_intel['NNPA_PERCENT']['source']} आधिकारिक डेटा)")
                                if "GUARANTEE_STATUS" in f_intel:
                                    fin_lines.append(f"  🛡️ गारंटी स्थिति: राज्य सरकार वैधानिक गारंटी (सत्यापित)")

                                fin_str = ("\n" + "\n".join(fin_lines)) if fin_lines else ""

                                answer_parts.append(
                                    f"• **{p.name}** ({p.partner_type or 'बैंक शाखा'})\n"
                                    f"  📍 पता: {p.address or p.district}, {p.state}\n"
                                    f"  📏 दूरी: {dist} किमी ({loc_type})\n"
                                    f"  🏢 सेवा: {p_item.get('service_type', 'आवेदन प्रसंस्करण व ऋण वितरण')}"
                                    f"{fin_str}"
                                )
                            answer_parts.append(f"\n💡 आप सीधे आधिकारिक पोर्टल ([{portal_url}]({portal_url})) पर भी ऑनलाइन आवेदन कर सकते हैं।")
                        else:
                            answer_parts.append(f"Verified Authorized Channel Partners for **{scheme_name_str}** ({loc_desc}):\n")
                            for p_item in partners[:4]:
                                p = p_item["partner"]
                                dist = p_item["distance_km"]
                                prec = p_item.get("coordinate_precision", "EXACT_ADDRESS")
                                loc_type = "Exact Branch Location" if prec == "EXACT_ADDRESS" else "District Centroid (Approximate Distance)"
                                
                                # Financial intelligence facts
                                fin_lines = []
                                f_intel = p_item.get("financial_intelligence", {})
                                if "NNPA_PERCENT" in f_intel:
                                    fin_lines.append(f"  📊 Net NPA: {f_intel['NNPA_PERCENT']['value']}% ({f_intel['NNPA_PERCENT']['source']} Official Data)")
                                if "GUARANTEE_STATUS" in f_intel:
                                    fin_lines.append(f"  🛡️ Guarantee Status: Verified State Government Guarantee")

                                fin_str = ("\n" + "\n".join(fin_lines)) if fin_lines else ""

                                answer_parts.append(
                                    f"• **{p.name}** ({p.partner_type or 'Bank Branch'})\n"
                                    f"  📍 Address: {p.address or p.district}, {p.state}\n"
                                    f"  📏 Distance: {dist} km ({loc_type})\n"
                                    f"  🏢 Service Channel: {p_item.get('service_type', 'Application processing & credit disbursement')}"
                                    f"{fin_str}"
                                )
                            answer_parts.append(f"\n💡 You can also submit digitally via the official portal: [{portal_url}]({portal_url})")
                        actions.append(AICopilotAction(
                            label="Locate Nearby Partner",
                            action_type="LOCATE_PARTNER",
                            target_url=f"/locator?scheme={target_sid}" if target_sid else "/locator"
                        ))
                    else:
                        if target_lang == "hi":
                            answer_parts.append(
                                f"**{scheme_name_str}** के लिए अधिकृत चैनल पार्टनर:\n\n"
                                f"• **नोडल एजेंसी**: ज़िला उद्योग केंद्र (DIC) / केवीआईसी (KVIC) क्षेत्रीय कार्यालय\n"
                                f"• **स्वीकृतिकर्ता बैंक**: सभी सार्वजनिक क्षेत्र के बैंक एवं क्षेत्रीय ग्रामीण बैंक (RRBs)\n"
                                f"• **डिजिटल सुविधा केंद्र**: जन सेवा केंद्र (CSC Outlets)\n\n"
                                f"• **ऑनलाइन पोर्टल**: [{portal_url}]({portal_url})"
                            )
                        else:
                            answer_parts.append(
                                f"Authorized Channel Partners for **{scheme_name_str}**:\n\n"
                                f"• **Nodal Agency**: District Industries Centre (DIC) / KVIC Regional Office\n"
                                f"• **Lending Partners**: All Public Sector Banks and Regional Rural Banks (RRBs)\n"
                                f"• **Assisted Digital Outlets**: Common Service Centres (CSC)\n\n"
                                f"• **Online Portal**: [{portal_url}]({portal_url})"
                            )
                        actions.append(AICopilotAction(
                            label="Locate Nearby Partner",
                            action_type="LOCATE_PARTNER",
                            target_url=f"/locator?scheme={target_sid}" if target_sid else "/locator"
                        ))

            elif intent == "AFFORDABILITY_QUERY":
                response_mode = "TOOL_RESULT"
                deterministic_used = True
                from app.engine.financial_health import DeterministicFinancialHealthEngine, FinancialHealthInput

                fin_input = FinancialHealthInput(
                    annual_income=extracted_facts.get("annual_income"),
                    project_cost=extracted_facts.get("project_cost"),
                    requested_loan_amount=extracted_facts.get("requested_loan_amount") or 300000.0,
                    liquid_savings=extracted_facts.get("liquid_savings"),
                    monthly_obligations=extracted_facts.get("monthly_obligations", 0.0),
                    profile=profile
                )
                fin_res = DeterministicFinancialHealthEngine.evaluate(fin_input, db=db)

                suit_res = None
                target_scheme_obj = None
                if target_sid:
                    target_scheme_obj = db.query(Scheme).filter(Scheme.scheme_id == target_sid).first()
                if target_scheme_obj:
                    suit_res = DeterministicFinancialHealthEngine.evaluate_scheme_suitability(
                        scheme=target_scheme_obj,
                        profile=profile,
                        requested_loan_amount=Decimal(str(fin_input.requested_loan_amount)) if fin_input.requested_loan_amount else None,
                        project_cost=Decimal(str(fin_input.project_cost)) if fin_input.project_cost else None,
                        own_contribution=Decimal(str(fin_input.liquid_savings)) if fin_input.liquid_savings else None,
                        annual_income=Decimal(str(fin_input.annual_income)) if fin_input.annual_income else None,
                        monthly_obligations=Decimal(str(fin_input.monthly_obligations)) if fin_input.monthly_obligations else None,
                        db=db
                    )

                status_str = fin_res.status.value if fin_res.status else "EVALUATED"
                score_str = f"{fin_res.score:.0f}/100" if fin_res.score is not None else "Calculated"

                ind_map = {ind.indicator_name.lower(): ind.formatted_value for ind in fin_res.indicators}
                foir_str = ind_map.get("foir", "Within standard limits (< 50%)")
                dti_str = ind_map.get("debt_to_income", "Evaluated")
                buffer_str = ind_map.get("liquidity_buffer", f"₹{extracted_facts.get('liquid_savings', 0):,.0f}")

                scheme_title = target_scheme_obj.scheme_name if target_scheme_obj else "Requested Loan Facility"

                if target_lang == "hi":
                    answer_parts.append(
                        f"📊 **ऋण वहनीयता एवं वित्तीय स्वास्थ्य विश्लेषण (Deterministic Affordability)** — {scheme_title}:\n\n"
                        f"• **वित्तीय स्वास्थ्य स्थिति**: **{status_str}** (स्कोर: {score_str})\n"
                        f"• **मासिक ऋण दायित्व अनुपात (FOIR)**: {foir_str}\n"
                        f"• **ऋण-से-आय अनुपात (Debt-to-Income)**: {dti_str}\n"
                        f"• **उपलब्ध बचत बफ़र (मार्जिन)**: {buffer_str}\n"
                    )
                    if suit_res:
                        tier_name = suit_res.suitability.value if hasattr(suit_res.suitability, "value") else str(suit_res.suitability)
                        emi_val = suit_res.estimated_emi or 0
                        margin_val = suit_res.required_margin_money or 0
                        answer_parts.append(
                            f"📌 **योजना वित्तीय अनुकूलता ({tier_name})**:\n"
                            f"• अनुमानित मासिक ईएमआई: ₹{emi_val:,.0f}\n"
                            f"• आवश्यक मार्जिन मनी: ₹{margin_val:,.0f}\n"
                            f"• टिप्पणी: {suit_res.suitability_reason}\n"
                        )
                    if fin_res.risk_flags:
                        answer_parts.append("⚠️ **जोखिम टिप्पणियां**: " + "; ".join(fin_res.risk_flags[:2]))
                    if fin_res.recommendations:
                        answer_parts.append("💡 **सलाह**: " + fin_res.recommendations[0])
                else:
                    answer_parts.append(
                        f"📊 **Deterministic Financial Affordability Assessment** — {scheme_title}:\n\n"
                        f"• **Financial Health Status**: **{status_str.replace('_', ' ')}** (Health Score: {score_str})\n"
                        f"• **Fixed Obligation to Income Ratio (FOIR)**: {foir_str} *(under 50% is standard banking safety limit)*\n"
                        f"• **Debt-to-Income Ratio**: {dti_str}\n"
                        f"• **Liquidity Buffer**: {buffer_str}\n"
                    )
                    if suit_res:
                        tier_name = suit_res.suitability.value if hasattr(suit_res.suitability, "value") else str(suit_res.suitability)
                        emi_val = suit_res.estimated_emi or 0
                        margin_val = suit_res.required_margin_money or 0
                        answer_parts.append(
                            f"📌 **Scheme Financial Fit ({tier_name})**:\n"
                            f"• **Estimated Monthly EMI**: ₹{emi_val:,.0f}\n"
                            f"• **Required Margin Money**: ₹{margin_val:,.0f}\n"
                            f"• **Suitability Reason**: {suit_res.suitability_reason}\n"
                        )
                    if fin_res.risk_flags:
                        answer_parts.append("⚠️ **Risk Notes**: " + "; ".join(fin_res.risk_flags[:2]))
                    if fin_res.recommendations:
                        answer_parts.append("💡 **Guidance**: " + fin_res.recommendations[0])

                actions.append(AICopilotAction(
                    label="Open EMI Calculator",
                    action_type="CALCULATE_EMI",
                    target_url=f"/calculator?scheme={target_sid}" if target_sid else "/calculator"
                ))

            elif intent in ("SCHEME_COMPARISON", "SCHEME_DIFFERENCE"):
                response_mode = "GROUNDED"
                deterministic_used = True

                sids = []
                if "pmegp" in msg_lower:
                    sids.append("SIH26092-001")
                if "mudra" in msg_lower:
                    sids.append("SIH26092-002")
                if "stand-up" in msg_lower or "stand up" in msg_lower:
                    sids.append("SIH26092-003")
                if "svanidhi" in msg_lower:
                    sids.append("SIH26092-004")
                if "vishwakarma" in msg_lower:
                    sids.append("SIH26092-005")
                if not sids and target_sid:
                    sids.append(target_sid)

                schemes_to_compare = []
                for sid in sids[:2]:
                    sch = db.query(Scheme).filter(Scheme.scheme_id == sid).first()
                    if sch:
                        schemes_to_compare.append(sch)

                if len(schemes_to_compare) >= 2:
                    s1, s2 = schemes_to_compare[0], schemes_to_compare[1]
                    s1_limit = f"₹{s1.max_loan_amount:,.0f}" if s1.max_loan_amount else "Varies by project (₹50L max)"
                    s2_limit = f"₹{s2.max_loan_amount:,.0f}" if s2.max_loan_amount else "Varies by category (₹10L/₹20L max)"
                    s1_sub = s1.subsidy_details or (f"{s1.subsidy_percentage}%" if s1.subsidy_percentage else "15% - 35% Capital Subsidy")
                    s2_sub = s2.subsidy_details or (f"{s2.subsidy_percentage}%" if s2.subsidy_percentage else "No Capital Subsidy (Collateral-free credit)")

                    s1_elig = "Age 18+, individual entrepreneurs, SHGs, new units" if "pmegp" in s1.scheme_name.lower() else "Any Indian citizen with viable micro business plan"
                    s2_elig = "Any Indian citizen with non-farm income generating activity" if "mudra" in s2.scheme_name.lower() else "Age 18+, viable business"
                    s1_interest = "Bank commercial repo-linked interest rate"
                    s2_interest = "MUDRA bank rate (varies by lending institution)"
                    s1_collateral = "No collateral up to ₹10 Lakhs (CGTMSE coverage)"
                    s2_collateral = "Collateral-free credit under CGFMU coverage"

                    if target_lang == "hi":
                        answer_parts.append(
                            f"⚖️ **योजना तुलना विश्लेषण: {s1.scheme_name} बनाम {s2.scheme_name}**:\n\n"
                            f"1. **{s1.scheme_name}**:\n"
                            f"   • **पात्रता (Eligibility)**: {s1_elig}\n"
                            f"   • **ऋण राशि (Funding & Loan Limit)**: {s1_limit}\n"
                            f"   • **सब्सिडी लाभ (Capital Subsidy)**: {s1_sub}\n"
                            f"   • **ब्याज दर (Interest Rate)**: {s1_interest}\n"
                            f"   • **गारंटी (Collateral)**: {s1_collateral}\n"
                            f"   • **आवेदन पोर्टल**: [{s1.official_portal or 'पोर्टल'}]({s1.official_portal or 'https://www.myscheme.gov.in'})\n\n"
                            f"2. **{s2.scheme_name}**:\n"
                            f"   • **पात्रता (Eligibility)**: {s2_elig}\n"
                            f"   • **ऋण राशि (Funding & Loan Limit)**: {s2_limit}\n"
                            f"   • **सब्सिडी लाभ (Capital Subsidy)**: {s2_sub}\n"
                            f"   • **ब्याज दर (Interest Rate)**: {s2_interest}\n"
                            f"   • **गारंटी (Collateral)**: {s2_collateral}\n"
                            f"   • **आवेदन पोर्टल**: [{s2.official_portal or 'पोर्टल'}]({s2.official_portal or 'https://www.myscheme.gov.in'})\n\n"
                            f"💡 **निष्कर्ष**: यदि आप पूंजीगत सब्सिडी (15%-35%) चाहते हैं तो **{s1.scheme_name}** अधिक उपयुक्त है। यदि आप बिना गारंटी तुरंत वर्किंग कैपिटल या छोटा ऋण चाहते हैं तो **{s2.scheme_name}** अधिक सुलभ है।"
                        )
                    else:
                        answer_parts.append(
                            f"⚖️ **Side-by-Side Scheme Comparison: {s1.scheme_name} vs {s2.scheme_name}**:\n\n"
                            f"1. **{s1.scheme_name}**:\n"
                            f"   • **Eligibility Criteria**: {s1_elig}\n"
                            f"   • **Funding & Maximum Loan**: {s1_limit}\n"
                            f"   • **Subsidy Support**: {s1_sub}\n"
                            f"   • **Interest Rate**: {s1_interest}\n"
                            f"   • **Collateral Requirement**: {s1_collateral}\n"
                            f"   • **Official Portal**: [{s1.official_portal or 'Portal'}]({s1.official_portal or 'https://www.myscheme.gov.in'})\n\n"
                            f"2. **{s2.scheme_name}**:\n"
                            f"   • **Eligibility Criteria**: {s2_elig}\n"
                            f"   • **Funding & Maximum Loan**: {s2_limit}\n"
                            f"   • **Subsidy Support**: {s2_sub}\n"
                            f"   • **Interest Rate**: {s2_interest}\n"
                            f"   • **Collateral Requirement**: {s2_collateral}\n"
                            f"   • **Official Portal**: [{s2.official_portal or 'Portal'}]({s2.official_portal or 'https://www.myscheme.gov.in'})\n\n"
                            f"💡 **Key Takeaway**: **{s1.scheme_name}** is ideal if you are setting up a new unit requiring substantial capital subsidy (up to 35% for special categories in rural areas). **{s2.scheme_name}** is ideal for collateral-free micro-credit without government equity lock-in."
                        )
                    rich_cards.append(RichCard(
                        card_type="COMPARISON_TABLE",
                        title=f"Comparison: {s1.scheme_name} vs {s2.scheme_name}",
                        data={
                            "scheme_1": s1.scheme_id,
                            "scheme_2": s2.scheme_id,
                            "dimensions": [
                                {"dimension": "Eligibility", "scheme_1": s1_elig, "scheme_2": s2_elig},
                                {"dimension": "Funding", "scheme_1": s1_limit, "scheme_2": s2_limit},
                                {"dimension": "Subsidy", "scheme_1": s1_sub, "scheme_2": s2_sub},
                                {"dimension": "Interest Rate", "scheme_1": s1_interest, "scheme_2": s2_interest},
                                {"dimension": "Collateral", "scheme_1": s1_collateral, "scheme_2": s2_collateral}
                            ]
                        }
                    ))
                else:
                    answer_parts.append("To compare schemes, please specify two schemes like PMEGP and MUDRA.")

            elif intent == "SUBSIDY_QUERY":
                response_mode = "TOOL_RESULT"
                deterministic_used = True
                target_sid = active_sid or "SIH26092-001"
                target_scheme = db.query(Scheme).filter(Scheme.scheme_id == target_sid).first()
                scheme_name_str = target_scheme.scheme_name if target_scheme else "the scheme"

                is_pmegp = "pmegp" in scheme_name_str.lower() or target_sid == "SIH26092-001"
                is_mudra = "mudra" in scheme_name_str.lower() or target_sid == "SIH26092-002"
                is_vishwakarma = "vishwakarma" in scheme_name_str.lower() or target_sid == "SIH26092-005"

                if is_pmegp:
                    if target_lang == "hi":
                        answer_parts.append(
                            f"**{scheme_name_str} (PMEGP) में सब्सिडी विवरण (Capital Subsidy)**:\n\n"
                            f"PMEGP में भारत सरकार द्वारा मार्जिन मनी सब्सिडी प्रदान की जाती है:\n\n"
                            f"1. **सामान्य वर्ग (General Category)**:\n"
                            f"   • शहरी क्षेत्र (Urban): **15%** सब्सिडी (लाभार्थी अंशदान: 10%)\n"
                            f"   • ग्रामीण क्षेत्र (Rural): **25%** सब्सिडी (लाभार्थी अंशदान: 10%)\n\n"
                            f"2. **विशेष वर्ग (SC/ST/OBC/महिला/दिव्यांग/अल्पसंख्यक/पूर्व सैनिक)**:\n"
                            f"   • शहरी क्षेत्र (Urban): **25%** सब्सिडी (लाभार्थी अंशदान: 5%)\n"
                            f"   • ग्रामीण क्षेत्र (Rural): **35%** सब्सिडी (लाभार्थी अंशदान: 5%)\n\n"
                            f"• अधिकतम परियोजना लागत: विनिर्माण (Manufacturing) हेतु ₹50 लाख, सेवा (Service) हेतु ₹20 लाख।"
                        )
                    else:
                        answer_parts.append(
                            f"**Authoritative Capital Subsidy Structure for {scheme_name_str} (PMEGP)**:\n\n"
                            f"PMEGP provides credit-linked capital subsidy (Margin Money):\n\n"
                            f"1. **General Category Beneficiaries**:\n"
                            f"   • Urban Areas: **15%** capital subsidy (Own contribution: 10%)\n"
                            f"   • Rural Areas: **25%** capital subsidy (Own contribution: 10%)\n\n"
                            f"2. **Special Categories (SC / ST / OBC / Women / Divyang / Ex-Servicemen / Minorities / NER)**:\n"
                            f"   • Urban Areas: **25%** capital subsidy (Own contribution: 5%)\n"
                            f"   • Rural Areas: **35%** capital subsidy (Own contribution: 5%)\n\n"
                            f"• Eligible Project Cost: Up to ₹50 Lakh (Manufacturing) and ₹20 Lakh (Service Sector)."
                        )
                elif is_mudra:
                    if target_lang == "hi":
                        answer_parts.append(
                            f"**{scheme_name_str} (PMMY) में सब्सिडी की स्थिति**:\n\n"
                            f"⚠️ **महत्वपूर्ण**: प्रधानमंत्री मुद्रा योजना (PMMY) के तहत कोई **पूंजीगत सब्सिडी (Capital Subsidy)** नहीं दी जाती है।\n\n"
                            f"यह योजना बैंक से बिना किसी गारंटी (Collateral-Free) के 3 श्रेणियों में ऋण उपलब्ध कराती है:\n"
                            f"• **शिशु (Shishu)**: ₹50,000 तक\n"
                            f"• **किशोर (Kishore)**: ₹50,000 से ₹5 लाख तक\n"
                            f"• **तरुण (Tarun)**: ₹5 लाख से ₹10 लाख तक\n\n"
                            f"यदि आपको सब्सिडी चाहिए, तो आप **PMEGP योजना** चुन सकते हैं।"
                        )
                    else:
                        answer_parts.append(
                            f"**Official Subsidy Policy for {scheme_name_str} (PM MUDRA Yojana)**:\n\n"
                            f"⚠️ **Statutory Clarification**: PM MUDRA Yojana does **NOT** provide a capital subsidy.\n\n"
                            f"It is a collateral-free credit enablement scheme across 3 loan tiers:\n"
                            f"• **Shishu**: Up to ₹50,000\n"
                            f"• **Kishore**: ₹50,000 to ₹5,00,000\n"
                            f"• **Tarun**: ₹5,00,000 to ₹10,00,000\n\n"
                            f"If you require a capital subsidy (15%-35%), we recommend exploring **PMEGP (Prime Minister's Employment Generation Programme)**."
                        )
                elif is_vishwakarma:
                    if target_lang == "hi":
                        answer_parts.append(
                            f"**{scheme_name_str} में वित्तीय सहायता व सब्सिडी विवरण**:\n\n"
                            f"• **ब्याज सबवेंशन (Interest Subvention)**: ऋण पर 8% की ब्याज छूट भारत सरकार देती है, जिससे लाभार्थी को केवल **5%** ब्याज देना होता है।\n"
                            f"• **टूलकिट प्रोत्साहन**: ₹15,000 का अनुदान (ई-वाउचर/टूलकिट हेतु)।\n"
                            f"• **ऋण सुविधा**: प्रथम चरण में ₹1 लाख, द्वितीय चरण में ₹2 लाख (कोलेटरल-मुक्त)।"
                        )
                    else:
                        answer_parts.append(
                            f"**Financial Assistance & Subvention for {scheme_name_str}**:\n\n"
                            f"• **Interest Subvention**: Beneficiary pays concessional interest of **5.0% p.a.** (8% interest subvention borne directly by MoMSME).\n"
                            f"• **Toolkit Grant**: ₹15,000 grant incentive via e-vouchers for modern trade tools.\n"
                            f"• **Collateral-Free Loan**: Tranche 1 up to ₹1,00,000; Tranche 2 up to ₹2,00,000."
                        )
                elif target_scheme and target_scheme.subsidy_percentage:
                    answer_parts.append(
                        f"Official Capital Subsidy for **{target_scheme.scheme_name}**:\n\n"
                        f"• **Subsidy Percentage**: **{target_scheme.subsidy_percentage}%** of the eligible project cost as specified in statutory guidelines.\n"
                        f"• Source Document: {target_scheme.source_document or 'Official Scheme Notification'}"
                    )
                else:
                    sch_name = target_scheme.scheme_name if target_scheme else "This scheme"
                    answer_parts.append(
                        f"Official Guidelines for **{sch_name}**:\n\n"
                        f"According to verified government records, this scheme does not provide a direct capital subsidy. Assistance is provided as institutional credit, interest subvention, or direct statutory welfare benefit."
                    )

                actions.append(AICopilotAction(
                    label="View Official Portal",
                    action_type="VIEW_SCHEME",
                    target_url=f"/schemes/{target_sid}"
                ))

            elif intent == "SCHEME_DETAILS":
                response_mode = "GROUNDED"
                target_sid = active_sid or "SIH26092-001"
                details = CopilotTools.get_scheme_details(db, target_sid)
                if details:
                    sch_name = details.get("scheme_name", "Government Scheme")
                    min_str = details.get("ministry", "Government of India")
                    agency_str = details.get("implementing_agency") or min_str
                    purp_str = details.get("purpose", "Statutory beneficiary welfare support")
                    target_str = details.get("target_groups") or "Eligible Indian citizens"
                    geog_str = details.get("geography") or "All-India"
                    stage_str = details.get("business_stage") or "New & Existing Enterprises"
                    sector_str = details.get("sector") or "Agriculture, Manufacturing & Services"

                    funding_str = f"Up to ₹{details.get('max_loan_amount', 0):,.0f}" if details.get('max_loan_amount') else "As per bank appraisal"
                    subsidy_str = f"{details.get('subsidy_percentage')}% on eligible project cost" if details.get('subsidy_percentage') else "No direct capital subsidy"

                    rate_min = details.get("interest_rate_min")
                    rate_max = details.get("interest_rate_max")
                    if rate_min is not None and rate_max is not None:
                        rate_str = f"{rate_min}% to {rate_max}% p.a."
                    elif rate_max is not None:
                        rate_str = f"Up to {rate_max}% p.a."
                    elif details.get("interest_rate") is not None:
                        rate_str = f"{details['interest_rate']}% p.a."
                    else:
                        rate_str = "Concessional / determined by lending bank appraisal (Not specified in official guidelines)"

                    tenure_val = details.get("repayment_period_max_months")
                    tenure_str = f"Up to {tenure_val} months ({tenure_val//12} years)" if tenure_val else "As determined by financing institution"

                    margin_str = "5% to 10% (General: 10%, Special Category: 5%)" if "pmegp" in sch_name.lower() else "10% to 25% based on project appraisal"

                    docs = details.get("documents", [])
                    docs_text = ", ".join([d["document_name"] for d in docs[:5]]) if docs else "Aadhaar Card, Project Report, Bank Passbook, KYC"

                    channel_str = details.get("application_mode") or "Online Portal & Authorized Bank Branches"
                    portal_url = details.get("official_portal") or "https://www.myscheme.gov.in"
                    partner_count = details.get("authorized_partners_count", 0)
                    partner_info = f"{partner_count} verified partner institutions mapped" if partner_count else "Public Sector Banks & DICs"
                    source_doc = details.get("source_document") or "Official Scheme Operational Guidelines"

                    # Complete 10-dimension grounded briefing (Priority 3)
                    answer_parts.append(
                        f"### 📋 Unified Grounded Scheme Intelligence: **{sch_name}**\n\n"
                        f"1. **Scheme Overview & Purpose**: {purp_str}\n"
                        f"2. **Target Beneficiaries**: {target_str}\n"
                        f"3. **Statutory Eligibility & Geography**: Domicile: {geog_str}; Age/Category conditions apply as per statutory guidelines.\n"
                        f"4. **Business Stage & Sectors**: {stage_str} | Sectors: {sector_str}\n"
                        f"5. **Financial Limits / Loan Facility**: {funding_str}\n"
                        f"6. **Capital Subsidy / Benefits**: {subsidy_str}\n"
                        f"7. **Interest Rate**: {rate_str}\n"
                        f"8. **Repayment Tenure**: {tenure_str}\n"
                        f"9. **Required Margin / Contribution**: {margin_str}\n"
                        f"10. **Required Documents Checklist**: {docs_text}\n"
                        f"11. **Application Channel & Portal**: [{portal_url}]({portal_url}) ({channel_str})\n"
                        f"12. **Partner Availability**: {partner_info} (Official Source: {source_doc})"
                    )
                    actions.append(AICopilotAction(
                        label="View Full Scheme Page",
                        action_type="VIEW_SCHEME",
                        target_url=f"/schemes/{target_sid}"
                    ))
                    rich_cards.append(RichCard(
                        card_type="SCHEME_CARD",
                        title=sch_name,
                        subtitle=f"Ministry: {min_str}",
                        data=details
                    ))

            elif intent == "BENEFIT_QUERY":
                response_mode = "GROUNDED"
                target_sid = active_sid or "SIH26092-005"
                sch = db.query(Scheme).filter(Scheme.scheme_id == target_sid).first()
                if sch:
                    purp = sch.purpose or sch.short_description or "Financial & statutory support"
                    benefits_text = sch.benefit_description or purp
                    funding_text = f"• **Funding / Loan Amount**: Up to ₹{sch.max_loan_amount:,.0f}\n" if sch.max_loan_amount else ""
                    sub_text = f"• **Capital Subsidy**: {sch.subsidy_percentage}%\n" if sch.subsidy_percentage else ""

                    answer_parts.append(
                        f"### 🎁 Key Statutory Benefits: **{sch.scheme_name}**\n\n"
                        f"{funding_text}{sub_text}"
                        f"• **Key Entitlements**: {benefits_text}\n"
                        f"• **Ministry / Department**: {sch.ministry or 'Government of India'}"
                    )
                    actions.append(AICopilotAction(
                        label="View Full Scheme Details",
                        action_type="VIEW_SCHEME",
                        target_url=f"/schemes/{target_sid}"
                    ))
                    rich_cards.append(RichCard(
                        card_type="SCHEME_CARD",
                        title=f"Key Benefits — {sch.scheme_name}",
                        subtitle=sch.ministry or "Government of India",
                        data={"benefits": benefits_text, "scheme_name": sch.scheme_name}
                    ))

            elif intent in ("SCHEME_COMPARISON", "SCHEME_DIFFERENCE"):
                response_mode = "TOOL_RESULT"
                deterministic_used = True

                # Extract schemes from message
                matched_sids = []
                if "pmegp" in msg_lower or "pmegp" in norm_msg:
                    matched_sids.append("SIH26092-001")
                if "mudra" in msg_lower or "pmmy" in msg_lower or "mudra" in norm_msg:
                    matched_sids.append("SIH26092-002")
                if "stand-up" in msg_lower or "stand up" in msg_lower or "standup" in norm_msg:
                    matched_sids.append("SIH26092-003")
                if "vishwakarma" in msg_lower or "vishwakarma" in norm_msg:
                    matched_sids.append("SIH26092-005")
                if "svanidhi" in msg_lower or "svanidhi" in norm_msg:
                    matched_sids.append("SIH26092-004")

                if len(matched_sids) < 2:
                    if active_sid and active_sid not in matched_sids:
                        matched_sids.append(active_sid)
                    if len(matched_sids) < 2:
                        default_pair = ["SIH26092-001", "SIH26092-002"] # PMEGP and MUDRA
                        for sid in default_pair:
                            if sid not in matched_sids and len(matched_sids) < 2:
                                matched_sids.append(sid)

                comp_res = CopilotTools.compare_schemes_structured(db, matched_sids[:2])
                schemes_list = comp_res.get("schemes", [])

                if len(schemes_list) >= 2:
                    s1, s2 = schemes_list[0], schemes_list[1]
                    answer_parts.append(
                        f"### ⚖️ Authoritative Comparison: **{s1['scheme_name']}** vs **{s2['scheme_name']}**\n\n"
                        f"| Dimension | **{s1['scheme_name'][:25]}** | **{s2['scheme_name'][:25]}** |\n"
                        f"| :--- | :--- | :--- |\n"
                        f"| **1. Eligibility** | {s1['eligibility'][:40]}... | {s2['eligibility'][:40]}... |\n"
                        f"| **2. Funding Limit** | {s1['funding']} | {s2['funding']} |\n"
                        f"| **3. Capital Subsidy** | {s1['subsidy']} | {s2['subsidy']} |\n"
                        f"| **4. Interest Rate** | {s1['interest']} | {s2['interest']} |\n"
                        f"| **5. Repayment Tenure** | {s1['repayment']} | {s2['repayment']} |\n"
                        f"| **6. Collateral** | {s1['collateral']} | {s2['collateral']} |\n"
                        f"| **7. Target Users** | {s1['target_users'][:40]}... | {s2['target_users'][:40]}... |\n"
                        f"| **8. Channel** | {s1['application_channel'][:40]}... | {s2['application_channel'][:40]}... |\n"
                        f"| **9. Geography** | {s1['geography']} | {s2['geography']} |\n"
                        f"| **10. Business Stage** | {s1['business_stage']} | {s2['business_stage']} |\n\n"
                        f"**Key Difference Summary**:\n"
                        f"• If you need **capital subsidy (15%-35%)** for a new enterprise, choose **{s1['scheme_name']}**.\n"
                        f"• If you need **fast collateral-free working capital** without subsidy delays, choose **{s2['scheme_name']}**."
                    )
                    actions.append(AICopilotAction(
                        label="Open Scheme Comparison Tool",
                        action_type="VIEW_SCHEME",
                        target_url=f"/compare?s1={s1['scheme_id']}&s2={s2['scheme_id']}"
                    ))
                    rich_cards.append(RichCard(
                        card_type="COMPARISON_TABLE",
                        title=f"Structured Scheme Comparison",
                        subtitle=f"{s1['scheme_name']} vs {s2['scheme_name']}",
                        data=comp_res
                    ))

            elif intent in (
                "GREETING", "CASUAL_GREETING", "LANGUAGE_SWITCH", "LANGUAGE_CHANGE",
                "PROFILE_UPDATE", "PROFILE_CORRECTION", "CASUAL_CONVERSATION",
                "OUT_OF_DOMAIN"
            ):
                # Strict Hard Gate: Never run RAG on non-retrieval conversational intents
                citations = []
                response_mode = "CASUAL"
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
                        "You are YojnaSetu AI Assistant, an authoritative Indian government scheme intelligence assistant. "
                        "You must answer the user's question using ONLY the provided official scheme documents in the grounded context. "
                        "STRICT RULES:\n"
                        "1. NEVER state 'You are legally eligible' or make definitive eligibility promises. You may only state that the applicant meets preliminary listed criteria and refer them to deterministic verification.\n"
                        "2. NEVER invent interest rates, loan amounts, capital subsidy percentages, or required document lists not present in the grounded context.\n"
                        "3. If the answer cannot be verified from the grounded context, explicitly state: 'I couldn't verify this information from the available official scheme data.' Do NOT fill gaps using generic assumptions.\n\n"
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
                        validated_synth, _ = AISecurityGuard.validate_factual_claims(synthesized_answer, deterministic_used=deterministic_used)
                        answer_parts.append(validated_synth)
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

        from app.ai.observability import RAGObservabilityTracker
        RAGObservabilityTracker.record_query(intent, deterministic_used=deterministic_used)

        raw_combined = "\n\n".join(answer_parts)
        validated_text, _ = AISecurityGuard.validate_factual_claims(raw_combined, deterministic_used=deterministic_used)
        final_answer = AISecurityGuard.scrub_output(sanitize_user_facing_text(validated_text))
        provider = get_ai_provider()

        # Real-time Multilingual Translation for Indian languages
        if target_lang and target_lang != "en":
            try:
                from app.services.translation_service import ChatbotTranslationService
                final_answer = ChatbotTranslationService.translate_text(final_answer, target_lang=target_lang)
                actions = ChatbotTranslationService.translate_actions(actions, target_lang=target_lang)
                suggested_questions = ChatbotTranslationService.translate_suggested_questions(suggested_questions, target_lang=target_lang)
                rich_cards = ChatbotTranslationService.translate_rich_cards(rich_cards, target_lang=target_lang)
            except Exception as e:
                logger.error("Multilingual response translation encountered an error, falling back to canonical English: %s", e)

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
            provider_name=provider.name,
            language=target_lang or "en"
        )

    @classmethod
    def generate_stream_chunks(cls, db: Session, req: AIChatRequest, current_user_id: Optional[str] = None) -> Generator[str, None, None]:
        """Yields incremental text chunks for SSE streaming response."""
        res = cls.process_query(db, req, current_user_id)
        words = res.answer.split(" ")

        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
