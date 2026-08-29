import re
import logging

logger = logging.getLogger("yojnasetu.ai.router")


class AICopilotQueryRouter:
    """
    Classifies user natural-language queries into explicit functional intents.
    Normalizes Indian regional speech, Hinglish, Roman Hindi, voice errors,
    pronoun references ("isme", "iske"), profile corrections, and vague queries.
    """

    CASUAL_GREETINGS = {
        "hi", "hello", "hey", "heya", "hii", "heyy", "hlo", "namaste", "namaste ji",
        "namaskar", "good morning", "good evening", "good afternoon", "good night",
        "greetings", "hi there", "hello there", "hola", "yo", "ssup", "sup", "bhai",
        "hello bhai", "hi bhai", "hey bhai", "namaste bhai", "hlo bhai"
    }

    IDENTITY_TERMS = [
        "what's your name", "whats your name", "whats ur name", "what is your name",
        "who are you", "who r u", "your name", "who built you", "who created you",
        "who made you", "where are you from", "where are u from", "where do you live",
        "where r u from", "who design you", "what is your identity", "are you ai",
        "are you a robot", "are you real", "are you human", "tum kaun ho", "aap kaun ho",
        "kaun ho", "tumhara naam kya hai", "aapka naam kya hai", "tumhara naam", "aapka naam",
        "naam kya hai", "naam kya h", "tera naam", "ai ho kya", "robot ho"
    ]

    ABOUT_YOJNASETU_TERMS = [
        "what is yojnasetu", "what is yojna setu", "what can i do here",
        "how does this work", "how can i find a government scheme",
        "can you help me get a loan", "can you check my eligibility",
        "what can you do", "how can you help me", "ye kya hai", "kya kar sakte ho",
        "kya help karoge", "kis cheez me help karte ho"
    ]

    EMOTIONAL_HELP_TERMS = [
        "samajh nahi aa raha", "mujhe kuch pata nahi", "help karo", "confused hu",
        "ye bahut confusing hai", "kaise karu", "kaha se shuru karu", "bhai help chahiye",
        "kuch samajh nahi aa raha", "help me please"
    ]

    CASUAL_CHITCHAT_PATTERNS = [
        r"\bhow\s+(?:are|r)\s+(?:you|u)\b",
        r"\bkya\s+haal\s+hai\b", r"\bkaise\s+ho\b", r"\bkya\s+kar\s+rahe\s+ho\b",
        r"\bwhat\s+(?:are|r)\s+(?:you|u)\s+doing\b",
        r"\bwhat(?:'|\s*)s\s+up\b",
        r"\bi\s+love\s+u\b", r"\bi\s+love\s+you\b", r"\blove\s+you\b",
        r"\bare\s+(?:you|u)\s+a?\s*fool\b", r"\byou(?:'|\s*re|\s+are)?\s+stupid\b", r"\bare\s+(?:you|u)\s+dumb\b",
        r"\bare\s+(?:you|u)\s+smart\b", r"\byou\s+are\s+(?:helpful|useless|awesome|great)\b",
        r"\bwho\s+won\b", r"\bmatch\b", r"\bcricket\b", r"\bweather\b", r"\bnews\b", r"\bmovie\b",
        r"\bthanks\b", r"\bthank\s+you\b", r"\bshukriya\b", r"\bbye\b", r"\bgoodbye\b", r"\bchitchat\b"
    ]

    SCHEME_DISCOVERY_INIT_TERMS = [
        "i need a government scheme", "i want a government scheme", "need a scheme",
        "mujhe scheme chahiye", "bhai scheme chahiye", "scheme chahiye",
        "mujhe loan chahiye", "i need financial help", "business ke liye loan chahiye",
        "which scheme am i eligible for", "mujhe business start karna hai",
        "bhai mujhe business", "business start karna hai", "start a business",
        "nayi shop", "business kholna", "mujhe business", "start business",
        "nayi company", "business lagana hai", "want to start a business",
        "need a loan for business", "which scheme for me", "best scheme for me",
        "mere liye kuch hai kya", "mere liye koi yojna", "koi govt scheme hai",
        "loan mil jayega kya", "business ke liye kuch milega", "government se paisa",
        "dukan kholni h", "apna business krna h", "mai apna kaam start krna",
        # Multilingual 12 Indian Languages Test Cases & Keywords
        "আমি ব্যবসার জন্য ঋণ চাই", "আমি ব্যবসা শুরু করতে চাই", "ঋণ", "ব্যবসা",
        "எனக்கு தொழில் தொடங்க கடன் வேண்டும்", "எனக்கு தொழில் தொடங்க வேண்டும்", "கடன்", "தொழில்",
        "నేను వ్యాపారం ప్రారంభించాలనుకుంటున్నాను", "నాకు వ్యాపారం కోసం రుణం కావాలి", "రుణం", "వ్యాపారం",
        "मला व्यवसाय सुरू करायचा आहे", "मला व्यवसायासाठी कर्ज हवे आहे", "कर्ज", "व्यवसाय",
        "મારે વ્યવસાય શરૂ કરવો છે", "મારે વ્યાપાર માટે લોન જોઈએ છે", "વ્યવસાય", "લોન",
        "ನಾನು ವ್ಯವಹಾರ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ", "ನನಗೆ ಸಾಲ ಬೇಕು", "ವ್ಯವಹಾರ", "ಸಾಲ",
        "എനിക്ക് ഒരു ബിസിനസ് തുടങ്ങണം", "എനിക്ക് വായ്പ വേണം", "ബിസിനസ്", "വായ്പ",
        "ਮੈਨੂੰ ਕਾਰੋਬਾਰ ਸ਼ੁਰੂ ਕਰਨਾ ਹੈ", "ਮੈਨੂੰ ਲੋੜ ਹੈ ਸਰਕਾਰੀ ਯੋਜਨਾ ਦੀ", "ਕਾਰੋਬਾਰ", "ਕਰਜ਼ਾ",
        "ମୁଁ ବ୍ୟବସାୟ ଆରମ୍ଭ କରିବାକୁ ଚାହୁଁଛି", "ମୋତେ ଋଣ ଦରକାର", "ବ୍ୟବସାୟ", "ଋଣ",
        "মই ব্যৱসায় আৰম্ভ কৰিব বিচাৰো", "মোক ঋণ লাগে", "ব্যৱসায়", "ঋণ"
    ]

    VAGUE_INDIAN_EXPRESSIONS = [
        "mere liye kya hai", "mujhe kya milega", "government kuch deti hai kya",
        "kitna paisa milega", "free mein kuch milega", "subsidy milegi",
        "meri category ke liye kya hai", "students ke liye", "ladkiyon ke liye",
        "sc walon ke liye", "farmers ke liye", "business walon ke liye"
    ]

    @classmethod
    def detect_language(cls, text: str) -> str:
        """
        Detects script or tokens for 12 Indian languages:
        en, hi, bn, te, mr, ta, gu, kn, ml, pa, or, as
        """
        if not text:
            return "en"

        # 1. Script range matching
        if re.search(r"[\u0980-\u09FF]", text):  # Bengali / Assamese script
            if "ৰ" in text or "ৱ" in text or "বিচাৰো" in text:
                return "as"
            return "bn"
        if re.search(r"[\u0B80-\u0BFF]", text):  # Tamil script
            return "ta"
        if re.search(r"[\u0C00-\u0C7F]", text):  # Telugu script
            return "te"
        if re.search(r"[\u0C80-\u0CFF]", text):  # Kannada script
            return "kn"
        if re.search(r"[\u0D00-\u0D7F]", text):  # Malayalam script
            return "ml"
        if re.search(r"[\u0A80-\u0AFF]", text):  # Gujarati script
            return "gu"
        if re.search(r"[\u0A00-\u0A7F]", text):  # Gurmukhi / Punjabi script
            return "pa"
        if re.search(r"[\u0B00-\u0B7F]", text):  # Odia script
            return "or"
        if re.search(r"[\u0900-\u097F]", text):  # Devanagari (Hindi / Marathi)
            if any(w in text for w in ["मला", "आहे", "कर्ज", "हवे", "सुरू", "करायचा"]):
                return "mr"
            return "hi"

        # Roman script Hinglish or English
        msg = text.lower()
        if any(w in msg for w in ["bhai", "chahiye", "karna", "mujhe", "karte", "kaise", "samajh", "milega"]):
            return "hi"

        return "en"

    PROFILE_CORRECTION_TERMS = [
        "actually meri age", "nahi bhai mai", "actually i am", "correction",
        "change my age", "change category", "update my category"
    ]

    WHY_MATCH_TERMS = [
        "kyu", "mere liye kyu", "ye kaise match hua", "mujhe kyu suggest kiya",
        "why this match", "why recommended"
    ]

    PROFILE_ANSWER_TERMS = [
        "up", "uttar pradesh", "bihar", "maharashtra", "delhi", "mp", "madhya pradesh",
        "rajasthan", "gujarat", "tamil nadu", "karnataka", "west bengal", "punjab",
        "sc", "st", "obc", "general", "scheduled caste", "scheduled tribe",
        "female", "male", "woman", "mahila", "man",
        "1.8 lakh", "2 lakh", "1 lakh", "3 lakh", "5 lakh", "50000", "100000", "200000",
        "2l", "2 lac", "2 lacs", "50k",
        "tailoring", "stitching", "dairy", "milk", "shop", "retail", "manufacturing", "factory"
    ]

    @classmethod
    def classify_intent(cls, message: str, page_context: dict = None) -> str:
        raw_msg = re.sub(r"</?untrusted_content>", "", message).strip()
        msg = raw_msg.lower().strip()
        clean_msg = re.sub(r"[^\w\s]", "", msg).strip()
        page_context = page_context or {}
        current_route = page_context.get("current_route", "")

        # 1. Exact Casual Greetings (0 RAG)
        if clean_msg in cls.CASUAL_GREETINGS or msg in cls.CASUAL_GREETINGS:
            return "CASUAL_GREETING"

        # 2. Identity Queries (0 RAG)
        if any(term in msg for term in cls.IDENTITY_TERMS) or clean_msg in cls.IDENTITY_TERMS:
            return "IDENTITY_QUERY"

        # 3. Explicit Tool Intents (Saved Schemes, Application, Financial, Document, Eligibility)
        if any(term in msg for term in ["saved schemes", "mere saved schemes", "saved scheme", "show my saved schemes"]):
            return "SAVED_SCHEMES_LIST"

        if any(term in msg for term in ["save this scheme", "isko save kar do", "save karlo", "save scheme", "remember this scheme", "useful hai save", "save this"]):
            return "SAVE_SCHEME"

        if "save hai" in msg or "saved hai" in msg or "is saved" in msg:
            return "SAVED_SCHEME_CHECK"

        if any(term in msg for term in ["isko hata do", "remove saved", "unsave"]):
            return "REMOVE_SAVED_SCHEME"

        if any(term in msg for term in ["apply", "application", "kaha apply", "form kaha"]):
            return "APPLICATION_QUERY"

        if any(term in msg for term in ["emi", "calculator", "interest rate", "installment", "repayment", "subsidy amount", "loan limit", "loan calculation"]):
            return "FINANCIAL_QUERY"

        if any(term in msg for term in ["document", "documents", "certificate", "id proof", "address proof", "passport photo", "paperwork", "paper kaunse"]):
            return "DOCUMENT_QUERY"

        if any(term in msg for term in ["eligible", "eligibility", "can i apply", "am i eligible", "qualify", "requirements to apply"]):
            return "ELIGIBILITY_QUERY"

        # 4. Emotional / Confused User Help (0 RAG)
        if any(term in msg for term in cls.EMOTIONAL_HELP_TERMS):
            return "EMOTIONAL_HELP"

        # 5. About YojnaSetu / Platform Capabilities (0 RAG)
        if any(term in msg for term in cls.ABOUT_YOJNASETU_TERMS) or clean_msg in cls.ABOUT_YOJNASETU_TERMS:
            return "GENERAL_HELP"

        # 6. Casual Chit-chat & Small Talk (0 RAG)
        for pattern in cls.CASUAL_CHITCHAT_PATTERNS:
            if re.search(pattern, msg, re.IGNORECASE):
                return "CASUAL_CONVERSATION"

        if clean_msg in ["cool", "nice", "great", "lol", "haha", "okay", "ok", "awesome", "sweet", "perfect", "thanks", "thank you", "shukriya", "bye", "goodbye", "thik hai", "accha"]:
            return "CASUAL_CONVERSATION"

        # 7. Profile Correction / Update Intent
        if any(term in msg for term in cls.PROFILE_CORRECTION_TERMS):
            return "PROFILE_CORRECTION"

        # 8. "Why match?" Explanation Query
        if any(term in msg for term in cls.WHY_MATCH_TERMS) or clean_msg in ["kyu", "kyun", "why"]:
            return "WHY_MATCH_QUERY"

        # 9. Explicit Recommendation Query
        if any(term in msg for term in ["best scheme", "recommend", "suggest", "which scheme", "suitable for me", "schemes for women", "schemes for artisans"]):
            return "RECOMMENDATION_QUERY"

        # 10. Vague Indian Need Expressions & Discovery Init
        if any(term in msg for term in cls.VAGUE_INDIAN_EXPRESSIONS):
            return "BUSINESS_PROFILE_INIT"

        if any(term in msg for term in cls.SCHEME_DISCOVERY_INIT_TERMS) or clean_msg in cls.SCHEME_DISCOVERY_INIT_TERMS:
            return "BUSINESS_PROFILE_INIT"

        # 10. Contextual Pronoun References ("isme loan", "iske documents", "isme apply kaise karu")
        if re.search(r"\b(?:isme|iske|iska|ye)\s+(?:kitna\s+)?(?:loan|emi|interest|document|documents|paper|apply)\b", msg):
            if "document" in msg or "paper" in msg:
                return "DOCUMENT_QUERY"
            if "loan" in msg or "emi" in msg or "interest" in msg:
                return "FINANCIAL_QUERY"
            if "apply" in msg:
                return "APPLICATION_QUERY"

        if any(term in msg for term in cls.PROFILE_ANSWER_TERMS):
            return "BUSINESS_PROFILE_INIT"

        # Route-based contextual defaults
        if "/applications/" in current_route:
            return "APPLICATION_QUERY"
        if "/calculator" in current_route:
            return "FINANCIAL_QUERY"

        return "GENERAL_SCHEME_QUERY"
