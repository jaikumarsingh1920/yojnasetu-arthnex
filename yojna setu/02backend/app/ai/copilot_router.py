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
        r"\b(?:u|you|tum|aap)?\s*(?:are|r)?\s*(?:a\s*)?(?:fool|idiot|dumb|stupid|bad|useless|gadhe|gadha|ullu|pagal)\b",
        r"\bare\s+(?:you|u)\s+a?\s*fool\b", r"\byou(?:'|\s*re|\s+are)?\s+stupid\b", r"\bare\s+(?:you|u)\s+dumb\b",
        r"\bare\s+(?:you|u)\s+smart\b", r"\byou\s+are\s+(?:helpful|useless|awesome|great)\b",
        r"\bwho\s+won\b", r"\bmatch\b", r"\bcricket\b", r"\bweather\b", r"\bnews\b", r"\bmovie\b",
        r"\bthanks\b", r"\bthank\s+you\b", r"\bshukriya\b", r"\bbye\b", r"\bgoodbye\b", r"\bchitchat\b"
    ]

    CASUAL_FEEDBACK_PATTERNS = [
        r"\b(?:nahi|nhi)\s+(?:chal|kam|kaam)\s*(?:raha|rha)\b",
        r"\b(?:chal|kam|kaam)\s+(?:nahi|nhi)\s*(?:raha|rha)\b",
        r"\bkuch\s+(?:nahi|nhi)\s*(?:chal|ho)\s*(?:raha|rha)\b",
        r"\b(?:not\s+working|not\s+running|doesnt\s+work|doesn't\s+work|isnt\s+working|isn't\s+working)\b",
        r"\b(?:kuch\s+)?samajh\s+nahi\s*(?:aa\s*raha|aaya|aata)\b",
        r"\b(?:arre|are|kya|oy|oye)\s+(?:yaar|bhai|bhaiya)\b",
        r"\bkaise\s+chalta\s+hai\b"
    ]

    PARTNER_DISCOVERY_TERMS = [
        "partner", "channel partner", "nearest partner", "authorized partner", "bank near me",
        "nearest bank", "which bank", "where to apply near me", "csc center", "csc near me",
        "partner office", "kaha jau", "kaun sa bank"
    ]

    SCHEME_COMPARISON_TERMS = [
        "compare", "difference between", "versus", "vs", "which scheme is better",
        "compare schemes", "pmegp vs mudra", "dono me kya farak hai"
    ]

    SCHEME_DISCOVERY_INIT_TERMS = [
        "i need a government scheme", "i want a government scheme", "need a scheme",
        "mujhe scheme chahiye", "bhai scheme chahiye", "scheme chahiye",
        "mujhe loan chahiye", "i need financial help", "business ke liye loan chahiye",
        "which scheme am i eligible for", "mujhe business start karna hai",
        "bhai mujhe business", "business start karna hai", "start a business",
        "i want to start a business", "find schemes for sc entrepreneurs",
        "schemes for sc entrepreneurs", "schemes for st entrepreneurs", "schemes for women entrepreneurs",
        "nayi shop", "business kholna", "mujhe business", "start business",
        "nayi company", "business lagana hai", "want to start a business",
        "need a loan for business", "which scheme for me", "best scheme for me",
        "mere liye kuch hai kya", "mere liye koi yojna", "koi govt scheme hai",
        "loan mil jayega kya", "business ke liye kuch milega", "government se paisa",
        "dukan kholni hai", "apna business karna hai", "mai apna kaam start karna",
        "bhai mujhe ek naya kaam shuru karna hai", "bhai mujhe ek naya kaam",
        "naya kaam shuru", "kaam shuru karna", "ek naya kaam",
        "mujhe koi yojna batao", "mujhe koi yojana batao", "koi yojna batao", "koi yojana batao",
        "yojna batao", "yojana batao", "koi scheme batao", "scheme batao", "yojna chahiye", "yojana chahiye",
        "mai gareeb hu", "gareeb hu", "garib hu", "mai garib hu", "gareeb", "garib",
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
        "মই ব্যৱসায় আৰম্ভ কৰিব বিচাৰো", "মোক ঋণ লাগে", "ব্যৱসায়", "ঋଣ"
    ]

    VAGUE_INDIAN_EXPRESSIONS = [
        "mere liye kya hai", "mujhe kya milega", "government kuch deti hai kya",
        "kitna paisa milega", "free mein kuch milega", "subsidy milegi",
        "meri category ke liye kya hai", "students ke liye", "ladkiyon ke liye",
        "sc walon ke liye", "farmers ke liye", "business walon ke liye",
        "mai gareeb hu", "gareeb hu", "garib hu", "paise nahi hai", "paisa nahi hai"
    ]

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
    def normalize_query(cls, text: str) -> str:
        """
        Normalizes natural language inputs, Hinglish, Roman Hindi abbreviations,
        voice transcription shorthand, emojis, and repeated character elongations.
        """
        if not text:
            return ""
        # 1. Strip untrusted wrappers
        raw = re.sub(r"</?untrusted_content>", "", text).strip()
        msg = raw.lower()

        # 2. Keep Unicode scripts (Devanagari, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Gurmukhi, Odia), Latin letters, digits, and spaces
        clean = re.sub(r"[^\w\s\u0900-\u0D7F]", " ", msg)

        # 3. Collapse 3+ repeated characters down to 1 (e.g. bhaiii -> bhai, krooo -> kro, plsss -> pls)
        clean = re.sub(r"([a-zA-Z])\1{2,}", r"\1", clean)

        # 4. Collapse common 2-letter repeats in Roman Hindi
        clean = re.sub(r"\bba+t\b", "baat", clean)
        clean = re.sub(r"\bkro+\b", "karo", clean)
        clean = re.sub(r"\bme+\b", "mein", clean)

        # 5. Token-level normalization for Roman Hindi & voice shorthand
        tokens = clean.split()
        norm_tokens = []
        for t in tokens:
            if t in ("m", "me", "mein", "mai", "main", "mey", "ma"):
                norm_tokens.append("mein")
            elif t in ("kr", "kar", "karo", "kroo", "kare", "karen"):
                norm_tokens.append("kar")
            elif t in ("krna", "karna"):
                norm_tokens.append("karna")
            elif t in ("nhi", "nhn", "nahi", "nahin", "na"):
                norm_tokens.append("nahi")
            elif t in ("rha", "raha"):
                norm_tokens.append("raha")
            elif t in ("rhi", "rahi"):
                norm_tokens.append("rahi")
            elif t in ("rhe", "rahe"):
                norm_tokens.append("rahe")
            elif t in ("h", "hai", "hain", "hn"):
                norm_tokens.append("hai")
            elif t in ("bhai", "bhaii", "bhaiii", "bhaiya", "bro"):
                norm_tokens.append("bhai")
            elif t in ("likh", "likho", "likhna"):
                norm_tokens.append("likho")
            elif t in ("bol", "bolo", "bolna"):
                norm_tokens.append("bolo")
            elif t in ("eng", "english", "angrezi"):
                norm_tokens.append("english")
            elif t in ("hin", "hindi"):
                norm_tokens.append("hindi")
            elif t in ("plz", "pls", "please"):
                norm_tokens.append("please")
            elif t in ("dery", "daity", "dairyy", "deri"):
                norm_tokens.append("dairy")
            elif t in ("yojna", "yojnaa", "yojana", "yojanaa"):
                norm_tokens.append("yojana")
            elif t in ("lie", "liye", "lye"):
                norm_tokens.append("liye")
            elif t in ("garib", "gareeb"):
                norm_tokens.append("gareeb")
            elif t in ("btao", "batao", "bataiye"):
                norm_tokens.append("batao")
            else:
                norm_tokens.append(t)

        return " ".join(norm_tokens)

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
        if any(w in msg for w in [
            "bhai", "chahiye", "karna", "mujhe", "karte", "kaise", "samajh", "milega",
            "karo", "kroo", "baat", "baaat", "mai", "gareeb", "garib", "hu", "hai",
            "yojna", "yojana", "dery", "dairy", "batao", "bataiye", "dastavez",
            "liye", "lie", "shuru", "kaam", "paisa", "paise", "nhi", "nahi", "bolo"
        ]):
            return "hi"

        return "en"

    @classmethod
    def is_language_change_query(cls, raw_msg: str, norm_msg: str) -> bool:
        """
        Robust check for language switching queries across English, Hindi, and 10 regional Indian languages.
        """
        lang_regex = r"(?:hindi|english|bengali|tamil|telugu|marathi|gujarati|kannada|malayalam|punjabi|odia|assamese|angrezi|বাংলা|தமிழ்|తెలుగు|मराठी|ગુજરાતી|ಕನ್ನಡ|മലയാളം|ਪੰਜਾਬੀ|ଓଡ଼ିଆ|অসমীয়া|हिंदी|अंग्रेज़ी)"

        # 1. Action command in English ("talk in hindi", "talk i hindi", "speak in english", "speak to me in hindi", "write in hindi", "please reply in hindi")
        if re.search(r"\b(?:please\s+)?(?:talk|speak|tell|write|chat|convers|say|reply|answer|explain)\s+(?:to\s+me\s+)?(?:in|i|into|me)?\s*" + lang_regex + r"\b", norm_msg, re.IGNORECASE):
            return True
        if re.search(r"\b(?:please\s+)?(?:talk|speak|tell|write|chat|convers|say|reply|answer|explain)\s+(?:to\s+me\s+)?(?:in|i|into|me)?\s*" + lang_regex + r"\b", raw_msg, re.IGNORECASE):
            return True

        # 2. Switch / change language ("switch to hindi", "change language to english")
        if re.search(r"\b(?:switch|change)\s+(?:language\s+)?to\s+" + lang_regex + r"\b", norm_msg, re.IGNORECASE):
            return True

        # 3. Roman Hindi / regional action ("hindi mein baat kar", "hindi mein bolo", "hindi mein likho", "hindi bolo", "english mein baat kar")
        if re.search(r"\b" + lang_regex + r"\s+(?:mein|in)?\s*(?:baat|bolo|likho|samjhao|batao|please|reply|jawab)?\s*(?:kar|karna|do|karo)?\b", norm_msg, re.IGNORECASE):
            if any(action in norm_msg for action in ["baat", "bolo", "likho", "samjhao", "batao", "please", "mein", "kar", "reply", "jawab"]):
                return True

        # 4. Inability expressions ("mujhe english nahi aati", "english nahi aati", "english samajh nahi aati")
        if re.search(r"\b(?:mujhe|mujhko|mjhe)?\s*(?:english|eng)\s+(?:samajh|samjh|aati|aata|aate)?\s*(?:nahi|nhi|nahin|na)\s*(?:aati|aata|aate|samajh|samjh|maloom|pata)?\b", norm_msg, re.IGNORECASE):
            return True
        if re.search(r"\b(?:mujhe|mujhko|mjhe)?\s*(?:english|eng)\s+(?:samajh|samjh|aati|aata|aate)?\s*(?:nhi|nahi|nahin|na)\s*(?:aati|aata|aate|samajh|samjh|maloom|pata)?\b", raw_msg, re.IGNORECASE):
            return True

        # 5. Direct native script language change commands
        script_phrases = [
            "हिंदी में बात करो", "हिंदी में बात करें", "हिंदी में बोलो", "हिंदी में लिखो", "हिंदी में", "हिंदी", "मुझे अंग्रेज़ी नहीं आती",
            "বাংলায় কথা বলো", "বাংলায় বলুন", "বাংলায় লিখুন",
            "தமிழில் பேசுங்கள்", "தமிழில் பேசு", "தமிழில் எழுதுங்கள்",
            "తెలుగులో మాట్లాడు", "తెలుగులో మాట్లాడండి",
            "मराठीत बोला",
            "ગુજરાતીમાં બોલો"
        ]
        if any(p in raw_msg for p in script_phrases):
            return True

        # 6. Quick phrases ("hindi please", "english please", "speak english", "speak hindi", "write in hindi", "write in english")
        if re.search(r"\b(?:speak|talk|write|reply|answer)\s+" + lang_regex + r"\b", norm_msg, re.IGNORECASE):
            return True
        if re.search(r"\b" + lang_regex + r"\s+please\b", norm_msg, re.IGNORECASE):
            return True

        return False

    @classmethod
    def classify_intent(cls, message: str, page_context: dict = None) -> str:
        """
        Main classifier mapping message to functional intent with normalized features.
        """
        raw_msg = re.sub(r"</?untrusted_content>", "", message).strip()
        msg_lower = raw_msg.lower().strip()
        clean_msg = re.sub(r"[^\w\s]", "", msg_lower).strip()
        norm_msg = cls.normalize_query(raw_msg)
        page_context = page_context or {}
        current_route = page_context.get("current_route", "")

        # 1. Exact Casual Greetings (0 RAG)
        if clean_msg in cls.CASUAL_GREETINGS or msg_lower in cls.CASUAL_GREETINGS or norm_msg in cls.CASUAL_GREETINGS:
            return "CASUAL_GREETING"

        # 2. Identity Queries (0 RAG)
        if any(term in msg_lower for term in cls.IDENTITY_TERMS) or clean_msg in cls.IDENTITY_TERMS or norm_msg in cls.IDENTITY_TERMS:
            return "IDENTITY_QUERY"

        # 3. Explicit Language Change Request (0 RAG, Absolute Priority Gate)
        if cls.is_language_change_query(raw_msg, norm_msg):
            return "LANGUAGE_CHANGE"

        # 4. Casual Feedback & Chit-chat (0 RAG)
        for pattern in cls.CASUAL_FEEDBACK_PATTERNS:
            if re.search(pattern, norm_msg, re.IGNORECASE) or re.search(pattern, msg_lower, re.IGNORECASE):
                return "CASUAL_CONVERSATION"

        for pattern in cls.CASUAL_CHITCHAT_PATTERNS:
            if re.search(pattern, norm_msg, re.IGNORECASE) or re.search(pattern, msg_lower, re.IGNORECASE):
                return "CASUAL_CONVERSATION"

        if clean_msg in ["cool", "nice", "great", "lol", "haha", "okay", "ok", "awesome", "sweet", "perfect", "thanks", "thank you", "shukriya", "bye", "goodbye", "thik hai", "accha", "fool", "idiot", "dumb"]:
            return "CASUAL_CONVERSATION"

        # 5. Partner Discovery Intent
        if any(term in norm_msg for term in cls.PARTNER_DISCOVERY_TERMS) or any(term in msg_lower for term in cls.PARTNER_DISCOVERY_TERMS):
            return "PARTNER_DISCOVERY"

        # 6. Scheme Comparison Intent
        if any(term in norm_msg for term in cls.SCHEME_COMPARISON_TERMS) or any(term in msg_lower for term in cls.SCHEME_COMPARISON_TERMS):
            return "SCHEME_COMPARISON"

        # 7. Explicit Tool Intents (Saved Schemes, Application, Financial, Document, Eligibility)
        if any(term in norm_msg for term in ["saved schemes", "mere saved schemes", "saved scheme", "show my saved schemes"]):
            return "SAVED_SCHEMES_LIST"

        if any(term in norm_msg for term in ["save this scheme", "isko save kar do", "save karlo", "save scheme", "remember this scheme", "useful hai save", "save this"]):
            return "SAVE_SCHEME"

        if "save hai" in norm_msg or "saved hai" in norm_msg or "is saved" in norm_msg:
            return "SAVED_SCHEME_CHECK"

        if any(term in norm_msg for term in ["isko hata do", "remove saved", "unsave"]):
            return "REMOVE_SAVED_SCHEME"

        if any(term in norm_msg for term in ["apply", "application", "kaha apply", "form kaha", "how do i apply", "how to apply"]):
            return "APPLICATION_QUERY"

        if any(term in norm_msg for term in ["emi", "calculator", "interest rate", "installment", "repayment", "subsidy amount", "loan limit", "loan calculation", "how much can i borrow", "kitna loan"]):
            return "FINANCIAL_QUERY"

        if any(term in norm_msg for term in ["document", "documents", "certificate", "id proof", "address proof", "passport photo", "paperwork", "paper kaunse", "what documents", "dastavez"]):
            return "DOCUMENT_QUERY"

        if any(term in norm_msg for term in ["eligible", "eligibility", "can i apply", "am i eligible", "qualify", "requirements to apply", "patrata"]):
            return "ELIGIBILITY_QUERY"

        # 8. Emotional / Confused User Help (0 RAG)
        if any(term in norm_msg for term in cls.EMOTIONAL_HELP_TERMS) or any(term in msg_lower for term in cls.EMOTIONAL_HELP_TERMS):
            return "EMOTIONAL_HELP"

        # 9. About YojnaSetu / Platform Capabilities (0 RAG)
        if any(term in norm_msg for term in cls.ABOUT_YOJNASETU_TERMS) or clean_msg in cls.ABOUT_YOJNASETU_TERMS:
            return "GENERAL_HELP"

        # 10. Profile Correction / Update Intent
        if any(term in norm_msg for term in cls.PROFILE_CORRECTION_TERMS):
            return "PROFILE_CORRECTION"

        # 11. "Why match?" Explanation Query
        if any(term in norm_msg for term in cls.WHY_MATCH_TERMS) or clean_msg in ["kyu", "kyun", "why"]:
            return "WHY_MATCH_QUERY"

        # 12. Explicit Scheme Discovery & Recommendation Query
        if any(term in norm_msg for term in ["best scheme", "recommend", "suggest", "which scheme", "suitable for me", "schemes for women", "schemes for sc", "schemes for st", "schemes for artisans"]):
            return "RECOMMENDATION_QUERY"

        # 13. Direct profile answering in multi-turn onboarding (e.g. "tailoring shop", "dairy", "UP", "SC", "2 lakh")
        is_short_profile_ans = len(norm_msg.split()) <= 3 and not any(q in norm_msg for q in ["yojna", "yojana", "scheme", "loan", "batao", "btao", "chahiye", "lie", "liye", "help", "kya"])
        if (any(term in norm_msg for term in cls.PROFILE_ANSWER_TERMS) or clean_msg in cls.PROFILE_ANSWER_TERMS) and is_short_profile_ans:
            return "SCHEME_DISCOVERY"

        # 14. Sector / Trade Specific Query (e.g. "dairy ke liye yojna", "silai ke liye loan", "farming schemes")
        sector_trade_keywords = [
            "dairy", "farming", "tailoring", "stitching", "retail", "dukan",
            "animal husbandry", "poultry", "fisheries", "fish", "textile", "handicraft",
            "artisan", "carpenter", "blacksmith", "cobbler", "barber", "potter", "weaver",
            "kheti", "doodh", "silai", "leather", "solar", "food processing", "livestock"
        ]
        if any(sec in norm_msg for sec in sector_trade_keywords):
            return "GENERAL_SCHEME_QUERY"

        # 15. Vague Indian Need Expressions & Discovery Init (0 specific scheme/sector)
        if any(term in norm_msg for term in cls.VAGUE_INDIAN_EXPRESSIONS):
            return "BUSINESS_PROFILE_INIT"

        if any(term in norm_msg for term in cls.SCHEME_DISCOVERY_INIT_TERMS) or clean_msg in cls.SCHEME_DISCOVERY_INIT_TERMS or norm_msg in cls.SCHEME_DISCOVERY_INIT_TERMS:
            return "BUSINESS_PROFILE_INIT"

        # 16. Contextual Pronoun References ("isme loan", "iske documents", "isme apply kaise karu")
        if re.search(r"\b(?:isme|iske|iska|ye)\s+(?:kitna\s+)?(?:loan|emi|interest|document|documents|paper|apply)\b", norm_msg):
            if "document" in norm_msg or "paper" in norm_msg:
                return "DOCUMENT_QUERY"
            if "loan" in norm_msg or "emi" in norm_msg or "interest" in norm_msg:
                return "FINANCIAL_QUERY"
            if "apply" in norm_msg:
                return "APPLICATION_QUERY"

        if any(term in norm_msg for term in cls.PROFILE_ANSWER_TERMS) or clean_msg in cls.PROFILE_ANSWER_TERMS:
            return "SCHEME_DISCOVERY"

        # Route-based contextual defaults
        if "/applications/" in current_route:
            return "APPLICATION_QUERY"
        if "/calculator" in current_route:
            return "FINANCIAL_QUERY"
        if "/locator" in current_route:
            return "PARTNER_DISCOVERY"

        return "GENERAL_SCHEME_QUERY"
