import re
import logging

logger = logging.getLogger("yojnasetu.ai.router")


class CanonicalIntent(str):
    """
    String subclass that compares equal to both its canonical intent name
    and any legacy backward-compatible alias strings (e.g. GREETING == CASUAL_GREETING).
    Serializes to its canonical name.
    """
    def __new__(cls, canonical: str, aliases: tuple = ()):
        obj = str.__new__(cls, canonical)
        obj.canonical = canonical
        obj.aliases = set(aliases)
        return obj

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other or other in self.aliases or other == self.canonical
        return super().__eq__(other)

    def __hash__(self):
        return hash(str(self))


INTENT_GREETING = CanonicalIntent("GREETING", ("CASUAL_GREETING",))
INTENT_LANGUAGE_SWITCH = CanonicalIntent("LANGUAGE_CHANGE", ("LANGUAGE_SWITCH",))
INTENT_PROFILE_UPDATE = CanonicalIntent("PROFILE_UPDATE", ("PROFILE_CORRECTION",))
INTENT_SCHEME_DISCOVERY = CanonicalIntent("BUSINESS_PROFILE_INIT", ("SCHEME_DISCOVERY", "RECOMMENDATION_QUERY"))
INTENT_SCHEME_DETAILS = CanonicalIntent("SCHEME_DETAILS", ())
INTENT_ELIGIBILITY_CHECK = CanonicalIntent("ELIGIBILITY_QUERY", ("ELIGIBILITY_CHECK",))
INTENT_DOCUMENTS = CanonicalIntent("DOCUMENT_QUERY", ("DOCUMENTS",))
INTENT_FINANCIAL_CALCULATION = CanonicalIntent("FINANCIAL_QUERY", ("FINANCIAL_CALCULATION",))
INTENT_PARTNER_LOCATION = CanonicalIntent("PARTNER_DISCOVERY", ("PARTNER_LOCATION",))
INTENT_SCHEME_COMPARISON = CanonicalIntent("SCHEME_COMPARISON", ("SCHEME_DIFFERENCE",))
INTENT_FOLLOW_UP = CanonicalIntent("FOLLOW_UP", ("WHY_MATCH_QUERY", "CONTEXTUAL_QUERY"))
INTENT_CASUAL_CONVERSATION = CanonicalIntent("CASUAL_CONVERSATION", ())
INTENT_OUT_OF_DOMAIN = CanonicalIntent("OUT_OF_DOMAIN", ())
INTENT_UNKNOWN = CanonicalIntent("GENERAL_SCHEME_QUERY", ("UNKNOWN", "NEED_CLARIFICATION"))


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
        "hello bhai", "hi bhai", "hey bhai", "namaste bhai", "hlo bhai", "hi bot",
        "hello bot", "hi sir", "hello sir", "hi yojnasetu", "hello yojnasetu", "hey bot",
        "नमस्ते", "नमस्ते भाई", "नमस्ते जी", "नमस्कार", "प्रणाम", "हेलो", "हाय"
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
        r"\b(?:u|you|tum|aap)?\s*(?:are|r)?\s*(?:a\s*)?(?:fool|idiot|dumb|stupid|bad|useless|gadhe|gadha|ullu|pagal|lame|boring|crazy|bakwas|bekar)\b",
        r"\bare\s+(?:you|u)\s+a?\s*fool\b", r"\byou(?:'|\s*re|\s+are)?\s+(?:stupid|lame|boring)\b", r"\bare\s+(?:you|u)\s+(?:dumb|lame)\b",
        r"\bare\s+(?:you|u)\s+smart\b", r"\byou\s+are\s+(?:helpful|useless|awesome|great|lame)\b",
        r"\b(?:you\s+are\s+lame|you\s+r\s+lame|ur\s+lame|you\s+lame)\b",
        r"\b(?:tum\s+pagal\s+ho|tum\s+bhi\s+pagal\s+ho|pagal\s+ho\s+tum|pagal\s+hai\s+kya)\b",
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
        "partner office", "kaha jau", "kaun sa bank", "nearest place to proceed", "where can i proceed",
        "where to proceed", "where to apply", "nearest place", "nearest branch", "nearest center", "nearest office"
    ]

    AFFORDABILITY_PATTERNS = [
        r"\b(?:affordable|affordability|can\s+i\s+afford|can\s+we\s+afford|afford\s+it|afford\s+this|afford\s+kar\s+sakta|afford\s+hoga|chuka\s+paunga|repayment\s+burden|debt\s+burden|kya\s+mai\s+chuka|chuka\s+sakte|burden\s+kitna|repay\s+kar\s+paunga|loan\s+bhar\s+paunga|afford\s+kar\s+paunga|financial\s+health|loan\s+affordability|assess\s+loan\s+affordability|check\s+financial\s+health)\b"
    ]

    SCHEME_COMPARISON_TERMS = [
        "compare", "difference between", "versus", "vs", "which scheme is better",
        "which one is better", "which is better", "better between",
        "compare schemes", "pmegp vs mudra", "dono me kya farak hai", "difference kya hai",
        "dono schemes me farak", "me difference", "antar kya hai", "farak kya hai"
    ]

    OUT_OF_DOMAIN_PATTERNS = [
        r"\b(?:python|java|javascript|c\+\+|coding|write\s+(?:a\s+)?code|write\s+(?:a\s+)?script|algorithm|quicksort|debug\s+my\s+code|react\s+component|html\s+css)\b",
        r"\b(?:recipe|cooking|how\s+to\s+bake|how\s+to\s+cook|bake\s+(?:a\s+)?cake|chocolate\s+cake|biryani|paneer|curry|food\s+recipe|butter\s+chicken)\b",
        r"\b(?:actor|actress|bollywood|hollywood|netflix|box\s+office|sing\s+a\s+song|favourite\s+movie)\b",
        r"\b(?:election\s+kaun\s+jitega|who\s+will\s+win\s+election|vote\s+for|voting\s+candidate|political\s+party|bjp\s+vs\s+congress|modi\s+vs\s+rahul)\b",
        r"\b(?:tell\s+me\s+a\s+joke|solve\s+this\s+riddle|astrology|horoscope|rashifal|kundli|capital\s+of\s+[a-zA-Z]+)\b",
        r"\b(?:cricket|football|ipl|captain\s+of|match\s+today|ipl\s+score|virat\s+kohli|rohit\s+sharma|ms\s+dhoni|best\s+cricketer|world\s+cup)\b"
    ]

    EXPLAIN_REJECTION_PATTERNS = [
        r"\b(?:why\s+(?:am\s+i|was\s+i|m\s+i)?\s*(?:not\s+eligible|ineligible|rejected))\b",
        r"\b(?:kyu\s+(?:eligible\s+nahi|reject\s+hua|patra\s+nahi|reject\s+kiya))\b",
        r"\b(?:mai\s+patra\s+kyu\s+nahi|ineligible\s+kyu\s+bataya|rejection\s+reason|rejection\s+ka\s+reason)\b",
        r"\b(?:why\s+did\s+i\s+get\s+rejected|reason\s+for\s+rejection|why\s+was\s+i\s+not\s+eligible)\b",
        r"\b(?:meri\s+eligibility\s+kyu\s+reject|kyu\s+reject|kyun\s+reject|reject\s+(?:hui|hua|kiya|kyu|kyun))\b",
        r"\b(?:why|kyu|kyun)\s+.*?\b(?:reject|rejected|ineligible)\b"
    ]

    SUBSIDY_PATTERNS = [
        r"\b(?:subsidy\s+kitni|kitni\s+subsidy|how\s+much\s+subsidy|subsidy\s+percentage|capital\s+subsidy|anudan\s+kitna|subsidy\s+milegi|subsidy\s+amount|isme\s+subsidy)\b"
    ]

    SCHEME_DETAILS_PATTERNS = [
        r"\b(?:details\s+of|tell\s+me\s+about\s+\w+|ke\s+baare\s+mein\s+batao|ke\s+bare\s+me\s+batao|scheme\s+details|yojana\s+ki\s+jankari|yojana\s+details)\b"
    ]

    SCHEME_DISCOVERY_INIT_TERMS = [
        "i need a government scheme", "i want a government scheme", "need a scheme",
        "mujhe scheme chahiye", "bhai scheme chahiye", "scheme chahiye",
        "mujhe loan chahiye", "i need financial help", "business ke liye loan chahiye",
        "loan chahiye", "business loan", "business loan chahiye", "loan chahiye bhai",
        "business loan chahiye bhai", "karz chahiye", "loan mil sakta hai",
        "need loan", "need a loan", "loan for business",
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
        "why this match", "why recommended", "why is this scheme recommended",
        "why is this recommended", "why recommended for me", "kyu suggest", "kyu match"
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
            elif t in ("yojna", "yojnaa", "yojana", "yojanaa", "योजना", "योजनाएं", "योजनाओं", "स्कीम", "प्रकल्प", "திட்டம்", "పథకం", "ಯೋಜನೆ", "പദ്ധതി", "યોજના", "ਸਕੀਮ", "ଯୋଜନା", "আঁচনি"):
                norm_tokens.append("yojana")
            elif t in ("lie", "liye", "lye", "लिए", "জন্য", "ஆக", "కోసం", "ಸಲುವಾಗಿ", "വേണ്ടി", "માટે", "ਲਈ", "ପାଇଁ", "বাবে"):
                norm_tokens.append("liye")
            elif t in ("garib", "gareeb", "गरीब"):
                norm_tokens.append("gareeb")
            elif t in ("btao", "batao", "bataiye", "बताओ", "बताएं", "बताइए", "বলুন", "கூறுங்கள்", "చెప్పండి", "ತಿಳಿಸಿ", "പറയുക", "જણાવો", "ਦੱਸੋ", "କୁହନ୍ତୁ", "কওক"):
                norm_tokens.append("batao")
            elif t in ("chahiye", "चाहिए", "হবে", "வேண்டும்", "కావాలి", "ಬೇಕು", "വേണം", "જોઈએ", "ਚਾਹੀਦਾ", "ଆବଶ୍ୟକ", "লাগে"):
                norm_tokens.append("chahiye")
            elif t in ("mujhe", "मुझे", "আমি", "நான்", "నేను", "ನಾನು", "ഞാൻ", "મને", "ਮੈਂ", "ମୁଁ", "মই", "मला"):
                norm_tokens.append("mujhe")
            elif t in ("business", "बिज़नेस", "बिजनेस", "व्यापार", "कारोबार", "ব্যবসা", "தொழில்", "వ్యాపారం", "ವ್ಯವಹಾರ", "ബിസിനസ്സ്", "વ્યવસાય", "ਕਾਰੋਬਾਰ", "ବ୍ୟବସାୟ"):
                norm_tokens.append("business")
            elif t in ("loan", "लोन", "ऋण", "कर्ज", "ঋণ", "ঋণের", "கடன்", "கடனுக்கு", "రుణం", "రుణానికి", "ಸಾಲ", "ಸಾಲಕ್ಕೆ", "വായ്പ", "വായ്പയ്ക്ക്", "લોન", "ਕਰਜ਼ਾ", "ਕਰਜ਼ੇ", "ଋଣ", "ঋণৰ"):
                norm_tokens.append("loan")
            elif t in ("subsidy", "सब्सिडी", "अनुदान", "সাবসিডি", "மானிய", "సబ్సిడీ", "ಸಹಾಯಧನ", "സബ്സിഡി", "ਸਬਸਿਡੀ"):
                norm_tokens.append("subsidy")
            elif t in ("document", "documents", "दस्तावेज़", "दस्तावेज", "कागजात", "कागदपत्रे", "कागदपत्र", "নথি", "নথিপত্র", "ஆவணங்கள்", "పత్రాలు", "ದಾಖಲೆಗಳು", "രേഖകൾ", "દસ્તાવેજો", "દસ્તાવેજ", "ਦਸਤਾਵੇਜ਼", "ଦସ୍ତାବିଜ", "নথি-পত্ৰ"):
                norm_tokens.append("document")
            elif t in ("eligible", "eligibility", "पात्र", "पात्रता", "योग्य", "যোগ্য", "যোগ্যতা", "தகுதியானவரா", "தகுதி", "అర్హుడనా", "అర్హత", "ಅರ್ಹನೇ", "ಅರ್ಹತೆ", "അർഹനാണോ", "യോഗ്യത", "પાત્ર", "પાત્રતા", "ਯੋਗ", "ਯੋਗਤਾ", "ଯୋଗ୍ୟ", "ଯୋଗ୍ୟତା"):
                norm_tokens.append("eligible")
            elif t in ("dairy", "dery", "daity", "dairyy", "deri", "डेयरी"):
                norm_tokens.append("dairy")
            elif t in ("shuru", "शुरू"):
                norm_tokens.append("shuru")
            elif t in ("karna", "krna", "करना"):
                norm_tokens.append("karna")
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
            if "ৰ" in text or "ৱ" in text or "বিচাৰো" in text or "আঁচনি" in text or "কওक" in text:
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
            marathi_markers = [
                "मला", "आहे", "कर्ज", "हवे", "सुरू", "करायचा", "करायचे", "साठी",
                "कोणती", "कागदपत्रे", "कागदपत्र", "लागतात", "पात्रता", "काय", "नाही",
                "माहिती", "सांगा", "करावे", "योजनेबद्दल", "योजनांची", "पाहिजे", "असेल",
                "वर्षांसाठी", "किती", "मिळेल", "करावा", "सांगावे", "मी", "अर्ज"
            ]
            if any(w in text for w in marathi_markers):
                hindi_exclusive = ["मुझे", "चाहिए", "करना", "बताएं", "बताओ", "दस्तावेज़", "हूँ", "हैं", "के लिए"]
                if not any(hw in text for hw in hindi_exclusive):
                    return "mr"
            return "hi"

        # Roman script Hinglish or English
        msg = text.lower()
        if any(w in msg for w in [
            "bhai", "chahiye", "karna", "mujhe", "karte", "kaise", "samajh", "milega",
            "karo", "kroo", "baat", "baaat", "mai", "gareeb", "garib", "hu", "hai",
            "yojna", "yojana", "dery", "batao", "bataiye", "dastavez",
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
        raw_lower = raw_msg.strip().lower()
        norm_lower = (norm_msg or "").strip().lower()
        clean_no_punct = re.sub(r"[^\w\s]", "", raw_lower).strip()

        # 0. Bare language name or single token: "hindi", "english", "bengali", etc.
        bare_langs = {
            "hindi", "english", "bengali", "bangla", "tamil", "telugu", "marathi", "gujarati",
            "kannada", "malayalam", "punjabi", "odia", "oriya", "assamese", "angrezi",
            "हिंदी", "अंग्रेज़ी", "বাংলা", "தமிழ்", "తెలుగు", "मराठी", "ગુજરાતી", "ಕನ್ನಡ",
            "മലയാളം", "ਪੰਜਾਬੀ", "ଓଡ଼ିଆ", "অসমীয়া"
        }
        if clean_no_punct in bare_langs or norm_lower in bare_langs:
            return True

        if re.match(r"^\s*(?:in\s+|please\s+|talk\s+in\s+|speak\s+in\s+)?(?:" + lang_regex + r")(?:\s+please|\s+mein|\s+me|\s+bhasha|\s+language)?\s*$", raw_lower, re.IGNORECASE):
            return True

        # 1. Action command in English ("talk in hindi", "talk to me in hindi", "speak to me in hindi", "reply in hindi")
        if re.search(r"\b(?:please\s+)?(?:talk|speak|tell|write|chat|convers|say|reply|answer|explain)\s+(?:to\s+me\s+)?(?:in|i|into|me)?\s*" + lang_regex + r"\b", norm_msg, re.IGNORECASE):
            return True
        if re.search(r"\b(?:please\s+)?(?:talk|speak|tell|write|chat|convers|say|reply|answer|explain)\s+(?:to\s+me\s+)?(?:in|i|into|me)?\s*" + lang_regex + r"\b", raw_msg, re.IGNORECASE):
            return True

        # 2. Switch / change language ("switch to hindi", "change language to english")
        if re.search(r"\b(?:switch|change)\s+(?:language\s+)?to\s+" + lang_regex + r"\b", norm_msg, re.IGNORECASE):
            return True

        # 3. Roman Hindi / regional action ("hindi mein baat kar", "hindi bolo", "mujhse hindi me baat karo")
        if re.search(r"\b" + lang_regex + r"\s+(?:mein|me|in)?\s*(?:baat|bolo|likho|samjhao|batao|please|reply|jawab)?\s*(?:kar|karna|do|karo)?\b", norm_msg, re.IGNORECASE):
            if any(action in norm_msg for action in ["baat", "bolo", "likho", "samjhao", "batao", "please", "mein", "me", "kar", "reply", "jawab"]):
                return True

        if re.search(r"\b(?:mujhse|mujhe)\s+" + lang_regex + r"\s+(?:me|mein)\s+(?:baat\s+karo|baat\s+karein|bolo|samjhao)\b", raw_lower, re.IGNORECASE):
            return True

        # 4. Inability expressions ("mujhe english nahi aati", "english samajh nahi aati")
        if re.search(r"\b(?:mujhe|mujhko|mjhe)?\s*(?:english|eng)\s+(?:samajh|samjh|aati|aata|aate)?\s*(?:nahi|nhi|nahin|na)\s*(?:aati|aata|aate|samajh|samjh|maloom|pata)?\b", norm_msg, re.IGNORECASE):
            return True
        if re.search(r"\b(?:mujhe|mujhko|mjhe)?\s*(?:english|eng)\s+(?:samajh|samjh|aati|aata|aate)?\s*(?:nhi|nahi|nahin|na)\s*(?:aati|aata|aate|samajh|samjh|maloom|pata)?\b", raw_msg, re.IGNORECASE):
            return True

        # 5. Direct native script language change commands
        script_phrases = [
            "हिंदी में बात करो", "हिंदी में बात करें", "हिंदी में बोलो", "हिंदी में लिखो", "हिंदी में समझाओ", "हिंदी में", "हिंदी", "मुझे अंग्रेज़ी नहीं आती",
            "বাংলায় কথা বলো", "বাংলায় বলুন", "বাংলায় লিখুন", "বাংলায় বোঝান", "বাংলায়",
            "தமிழில் பேசுங்கள்", "தமிழில் பேசு", "தமிழில் எழுதுங்கள்", "தமிழில் விளக்குங்கள்", "தமிழில்",
            "తెలుగులో మాట్లాడు", "తెలుగులో మాట్లాడండి", "తెలుగులో వివరించండి", "తెలుగులో",
            "मराठीत बोला", "मराठीत सांगा", "मराठी मध्ये", "मराठी",
            "ગુજરાતીમાં બોલો", "ગુજરાતીમાં સમજાવો", "ગુજરાતીમાં",
            "ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ", "ಕನ್ನಡದಲ್ಲಿ ಹೇಳಿ", "ಕನ್ನಡದಲ್ಲಿ", "ಕನ್ನಡ",
            "മലയാളത്തിൽ പറയുക", "മലയാളത്തിൽ സംസാരിക്കൂ", "മലയാളത്തിൽ",
            "ਪੰਜਾਬੀ ਵਿੱਚ ਗੱਲ ਕਰੋ", "ਪੰਜਾਬੀ ਵਿੱਚ ਬੋਲੋ", "ਪੰਜਾਬੀ ਵਿੱਚ ਸਮਝਾਓ", "ਪੰਜਾਬੀ ਵਿੱਚ",
            "ଓଡ଼ିଆରେ କୁହନ୍ତୁ", "ଓଡ଼ିଆରେ କଥାବାର୍ତ୍ତା କରନ୍ତୁ", "ଓଡ଼ିଆରେ ବୁଝାନ୍ତୁ", "ଓଡ଼ିଆରେ",
            "অসমীয়াত কথা পাতক", "অসমীয়াত কওক", "অসমীয়াত বুজাওক", "অসমীয়াত"
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
    def is_profile_update_query(cls, raw_msg: str, norm_msg: str) -> bool:
        """
        Detects statements providing citizen profile information (name, location, age, caste, etc.)
        when NOT asking an explicit scheme discovery/comparison/calculation query.
        """
        raw_lower = raw_msg.strip().lower()
        norm_lower = (norm_msg or "").strip().lower()

        # If user asks for scheme discovery, comparison, eligibility, calculation, or partner location, it is NOT pure profile update
        discovery_indicators = [
            "which scheme", "what scheme", "koi scheme", "koi yojna", "yojna batao", "scheme batao",
            "eligible for", "am i eligible", "eligibility", "patrata", "calculate", "calculate emi",
            "what is emi", "what is my emi", "how much emi", "kitni emi", "emi kitni", "emi calculator",
            "interest rate", "compare", "difference", "documents", "kaha apply", "how to apply", "suggest scheme",
            "recommend scheme", "scheme details", "yojana details", "nearest", "branch", "where is",
            "where to", "kaha jau", "kaun sa bank", "partner", "better between", "which is better",
            "which one is better", "vs", "versus"
        ]
        if any(ind in raw_lower for ind in discovery_indicators):
            return False

        if any(raw_lower.startswith(q) for q in ["where ", "where's ", "kaha ", "which ", "kaun ", "nearest ", "how "]):
            return False

        # 1. Name introduction
        if re.search(r"\b(?:my\s+name\s+is|mera\s+naam|naam|myself)\s+([a-zA-Z\u0900-\u097F]+)", raw_lower):
            return True
        if re.search(r"\bi\s+am\s+([a-zA-Z\u0900-\u097F]+)\b", raw_lower) and not re.search(r"\bi\s+am\s+(?:from|in|eligible|interested|looking|planning|not|sc|st|obc|general)\b", raw_lower):
            tokens = raw_lower.split()
            if len(tokens) <= 4:
                return True

        # 2. Location statements
        from app.ai.extractor import DISTRICT_TO_STATE
        for dist in DISTRICT_TO_STATE.keys():
            if re.search(rf"\b{re.escape(dist.lower())}\b", raw_lower):
                return True

        states = [
            "uttar pradesh", "up", "bihar", "maharashtra", "delhi", "madhya pradesh", "mp",
            "rajasthan", "gujarat", "punjab", "haryana", "karnataka", "tamil nadu", "west bengal",
            "odisha", "assam", "kerala", "telangana", "andhra pradesh", "jharkhand", "chhattisgarh",
            "uttarakhand", "himachal pradesh", "goa", "jammu", "kashmir"
        ]
        for st in states:
            if re.search(rf"\b{re.escape(st)}\b", raw_lower) and len(raw_lower.split()) <= 6:
                return True

        # 3. Age / category statements without scheme query
        if re.search(r"\b(?:i\s+am|i'm|main|meri\s+umar|my\s+age)\s+(?:is\s+)?\d{1,2}(?:\s*(?:years?|yrs?|saal|sal))?\b", raw_lower):
            return True
        if re.search(r"\b(?:i\s+am|i'm|main)\s+(?:sc|st|obc|general|female|male)\b", raw_lower):
            return True

        # 4. Financial statements without question
        if re.search(r"\b(?:i\s+earn|earn|salary|kamata\s+hu|kamati\s+hu|monthly\s+income|annual\s+income)\b", raw_lower):
            if not any(q in raw_lower for q in ["which", "how", "kaunsi", "kya", "batao", "afford"]):
                return True
        if re.search(r"\b(?:expenses?|monthly\s+expenses?|kharcha|kharch)\b", raw_lower):
            if not any(q in raw_lower for q in ["which", "how", "kaunsi", "kya", "batao", "afford"]):
                return True
        if re.search(r"\b(?:already\s+pay|pay|pehle\s+se\s+emi|existing\s+emi|current\s+emi|purani\s+emi)\b", raw_lower):
            if not any(q in raw_lower for q in ["which", "how", "kaunsi", "kya", "batao", "afford"]):
                return True
        if re.search(r"\b(?:i\s+need|need|chahiye)\s+(?:a\s+)?(?:\d+(?:\.\d+)?\s*(?:lakh|lac|k|crore)?)\s*(?:loan|funding)?\b", raw_lower):
            if not any(q in raw_lower for q in ["which", "how", "kaunsi", "kya", "batao"]):
                return True

        # 5. Explicit profile correction terms
        if any(term in norm_lower for term in cls.PROFILE_CORRECTION_TERMS):
            return True

        return False

    @classmethod
    def classify_intent(cls, message: str, page_context: dict = None) -> CanonicalIntent:
        """
        Main classifier mapping message to functional intent with normalized features.
        Guarantees deterministic high-confidence routing BEFORE scheme retrieval.
        """
        raw_msg = re.sub(r"</?untrusted_content>", "", message).strip()
        msg_lower = raw_msg.lower().strip()
        clean_msg = re.sub(r"[^\w\s]", "", msg_lower).strip()
        norm_msg = cls.normalize_query(raw_msg)
        page_context = page_context or {}
        current_route = page_context.get("current_route", "")

        # 1. Exact Casual Greetings (0 RAG, High Priority Gate)
        if (clean_msg in cls.CASUAL_GREETINGS or msg_lower in cls.CASUAL_GREETINGS or norm_msg in cls.CASUAL_GREETINGS
            or re.match(r"^(?:hi|hello|hey|namaste|namaskar|hlo|heya)\b(?:\s+(?:there|yojnasetu|yojna\s+setu|bot|bhai|bhaiya|ji|sir|bro|assistant))?[!\.]*$", msg_lower)):
            return INTENT_GREETING

        # 2. Identity Queries (0 RAG)
        if any(term in msg_lower for term in cls.IDENTITY_TERMS) or clean_msg in cls.IDENTITY_TERMS or norm_msg in cls.IDENTITY_TERMS:
            return CanonicalIntent("IDENTITY_QUERY", ())

        # 3. Explicit Language Change Request (0 RAG, Absolute Priority Gate)
        if cls.is_language_change_query(raw_msg, norm_msg):
            return INTENT_LANGUAGE_SWITCH

        # 4. Profile Update / Introductions / Locations (0 RAG, Absolute Priority Gate)
        if cls.is_profile_update_query(raw_msg, norm_msg):
            return INTENT_PROFILE_UPDATE

        # 5. Explicit Rejection Explanation Intent
        for pattern in cls.EXPLAIN_REJECTION_PATTERNS:
            if re.search(pattern, norm_msg, re.IGNORECASE) or re.search(pattern, msg_lower, re.IGNORECASE):
                return CanonicalIntent("EXPLAIN_REJECTION", ())

        # 6. Out-of-Domain Guardrail Intent (Cricket, Movies, Recipes, Coding, Politics, Trivia)
        for pattern in cls.OUT_OF_DOMAIN_PATTERNS:
            if re.search(pattern, norm_msg, re.IGNORECASE) or re.search(pattern, msg_lower, re.IGNORECASE):
                return INTENT_OUT_OF_DOMAIN

        # 7. Casual Feedback & Chit-chat (0 RAG)
        for pattern in cls.CASUAL_FEEDBACK_PATTERNS:
            if re.search(pattern, norm_msg, re.IGNORECASE) or re.search(pattern, msg_lower, re.IGNORECASE):
                return INTENT_CASUAL_CONVERSATION

        for pattern in cls.CASUAL_CHITCHAT_PATTERNS:
            if re.search(pattern, norm_msg, re.IGNORECASE) or re.search(pattern, msg_lower, re.IGNORECASE):
                return INTENT_CASUAL_CONVERSATION

        if clean_msg in ["cool", "nice", "great", "lol", "haha", "hahaha", "okay", "ok", "awesome", "sweet", "perfect", "thanks", "thank you", "shukriya", "bye", "goodbye", "thik hai", "accha", "fool", "idiot", "dumb", "lame", "crazy"]:
            return INTENT_CASUAL_CONVERSATION
        if re.search(r"\b(?:you\s+are\s+lame|you\s+r\s+lame|ur\s+lame|you\s+lame|tum\s+pagal\s+ho|tum\s+pagal)\b", msg_lower):
            return INTENT_CASUAL_CONVERSATION

        # 8. Partner Discovery Intent
        if any(term in norm_msg for term in cls.PARTNER_DISCOVERY_TERMS) or any(term in msg_lower for term in cls.PARTNER_DISCOVERY_TERMS) or re.search(r"\bnearest\s+(?:place|bank|branch|office|center|csc)\b", msg_lower):
            return INTENT_PARTNER_LOCATION

        # 9. Scheme Comparison Intent
        if any(term in norm_msg for term in cls.SCHEME_COMPARISON_TERMS) or any(term in msg_lower for term in cls.SCHEME_COMPARISON_TERMS) or re.search(r"\b(?:difference|versus|vs|compare|farak|antar|tulna)\b", norm_msg, re.IGNORECASE) or re.search(r"\b(?:difference|versus|vs|compare|farak|antar|tulna)\b", msg_lower, re.IGNORECASE):
            return INTENT_SCHEME_COMPARISON

        # 10. Subsidy Specific Query
        for pattern in cls.SUBSIDY_PATTERNS:
            if re.search(pattern, norm_msg, re.IGNORECASE) or re.search(pattern, msg_lower, re.IGNORECASE):
                return CanonicalIntent("SUBSIDY_QUERY", ())

        # 11. Affordability / Repayment Burden Query
        for pattern in cls.AFFORDABILITY_PATTERNS:
            if re.search(pattern, norm_msg, re.IGNORECASE) or re.search(pattern, msg_lower, re.IGNORECASE):
                return CanonicalIntent("AFFORDABILITY_QUERY", ())

        # 12. Explicit Tool Intents (Saved Schemes, Application, Financial, Document, Eligibility)
        if any(term in norm_msg for term in ["saved schemes", "mere saved schemes", "saved scheme", "show my saved schemes"]):
            return CanonicalIntent("SAVED_SCHEMES_LIST", ())

        if any(term in norm_msg for term in ["save this scheme", "isko save kar do", "save karlo", "save scheme", "remember this scheme", "useful hai save", "save this"]):
            return CanonicalIntent("SAVE_SCHEME", ())

        if "save hai" in norm_msg or "saved hai" in norm_msg or "is saved" in norm_msg:
            return CanonicalIntent("SAVED_SCHEME_CHECK", ())

        if any(term in norm_msg for term in ["isko hata do", "remove saved", "unsave"]):
            return CanonicalIntent("REMOVE_SAVED_SCHEME", ())

        # 13. Application Tracking
        if re.search(r"\b(?:track(?:\s+my)?\s+application|application\s+status|check\s+(?:my\s+)?application(?:\s+status)?|status\s+of\s+(?:my\s+)?application|track\s+status|application\s+tracking|where\s+is\s+my\s+application|application\s+(?:is\s+)?under\s+review|under\s+review)\b", norm_msg) or re.search(r"\b(?:application\s+ka\s+status|status\s+kya\s+hai|application\s+track|track\s+karna)\b", norm_msg):
            return CanonicalIntent("APPLICATION_QUERY", ())

        if any(term in norm_msg for term in ["apply for a business loan", "apply for business loan", "apply for a loan", "apply for loan", "want to apply for a loan", "want to apply for a business loan"]):
            return INTENT_SCHEME_DISCOVERY

        if any(term in norm_msg for term in ["apply", "application", "kaha apply", "form kaha", "how do i apply", "how to apply", "online apply kar", "csc se apply"]):
            return CanonicalIntent("APPLICATION_QUERY", ())

        # 14. Financial Calculation Intent
        if any(term in norm_msg for term in ["emi", "calculator", "interest rate", "byaj", "installment", "repayment", "subsidy amount", "loan limit", "loan calculation", "how much can i borrow", "kitna loan"]) or re.search(r"\bcalculate\s+emi\b", msg_lower):
            return INTENT_FINANCIAL_CALCULATION

        # 15. Documents Intent
        if any(term in norm_msg for term in ["document", "documents", "certificate", "id proof", "address proof", "passport photo", "paperwork", "paper kaunse", "what documents", "dastavez", "kagazat"]):
            return INTENT_DOCUMENTS

        # 16. Eligibility Discovery vs Single-Scheme Check Intent
        if re.search(r"\b(?:which|what|konsi|kaunsi|show|find|list)\s+(?:schemes?|yojna|yojana)\b.*?\beligible\b", norm_msg) or re.search(r"\bschemes?\s+(?:am\s+i\s+)?eligible\b", norm_msg):
            return INTENT_SCHEME_DISCOVERY

        if any(term in norm_msg for term in ["eligible", "eligibility", "can i apply", "am i eligible", "qualify", "requirements to apply", "patrata"]):
            return INTENT_ELIGIBILITY_CHECK

        if any(term in norm_msg for term in ["benefit", "benefits", "fayde", "fayda", "labh", "kya milega", "what do i get"]):
            return CanonicalIntent("BENEFIT_QUERY", ())

        # 17. Emotional / General Help
        if any(term in norm_msg for term in cls.EMOTIONAL_HELP_TERMS) or any(term in msg_lower for term in cls.EMOTIONAL_HELP_TERMS):
            return CanonicalIntent("EMOTIONAL_HELP", ())

        if any(term in norm_msg for term in cls.ABOUT_YOJNASETU_TERMS) or clean_msg in cls.ABOUT_YOJNASETU_TERMS:
            return CanonicalIntent("GENERAL_HELP", ())

        # 18. "Why match?" Explanation Query
        if any(term in norm_msg for term in cls.WHY_MATCH_TERMS) or clean_msg in ["kyu", "kyun", "why"] or re.search(r"\bwhy\s+.*?\b(?:recommend|recommended|suggest|suggested|match|matched|eligible)\b", norm_msg, re.IGNORECASE) or re.search(r"\bwhy\s+(?:am\s+i\s+eligible|eligible|recommended)\b", norm_msg, re.IGNORECASE):
            return INTENT_FOLLOW_UP

        # 19. Scheme Details Query
        for pattern in cls.SCHEME_DETAILS_PATTERNS:
            if re.search(pattern, norm_msg, re.IGNORECASE) or re.search(pattern, msg_lower, re.IGNORECASE):
                return INTENT_SCHEME_DETAILS

        # 20. Explicit Scheme Discovery & Recommendation Query
        rec_terms = [
            "best scheme", "recommend", "suggest", "which scheme", "suitable for me",
            "schemes for women", "schemes for sc", "schemes for st", "schemes for artisans",
            "now show me the best schemes", "show me the best schemes", "show me best schemes",
            "show me schemes", "show best schemes", "show schemes", "find schemes", "list schemes",
            "yojna dikhao", "schemes dikhao", "yojana dikhao", "ab scheme batao", "best schemes batao",
            "schemes batao", "ab schemes batao", "now show schemes"
        ]
        if any(term in norm_msg for term in rec_terms):
            return INTENT_SCHEME_DISCOVERY

        is_short_profile_ans = len(norm_msg.split()) <= 3 and not any(q in norm_msg for q in ["yojna", "yojana", "scheme", "loan", "batao", "btao", "chahiye", "lie", "liye", "help", "kya"])
        if (any(term in norm_msg for term in cls.PROFILE_ANSWER_TERMS) or clean_msg in cls.PROFILE_ANSWER_TERMS) and is_short_profile_ans:
            return INTENT_SCHEME_DISCOVERY

        sector_trade_keywords = [
            "dairy", "farming", "tailoring", "stitching", "retail", "dukan",
            "animal husbandry", "poultry", "fisheries", "fish", "textile", "handicraft",
            "artisan", "carpenter", "blacksmith", "cobbler", "barber", "potter", "weaver",
            "kheti", "doodh", "silai", "leather", "solar", "food processing", "livestock"
        ]
        if any(sec in norm_msg for sec in sector_trade_keywords):
            if any(term in norm_msg for term in ["yojana", "scheme", "loan", "subsidy", "batao", "chahiye", "liye", "karna", "business"]):
                return INTENT_SCHEME_DISCOVERY
            return INTENT_UNKNOWN

        if any(term in norm_msg for term in cls.VAGUE_INDIAN_EXPRESSIONS):
            return INTENT_SCHEME_DISCOVERY

        if any(term in norm_msg for term in cls.SCHEME_DISCOVERY_INIT_TERMS) or any(term in msg_lower for term in cls.SCHEME_DISCOVERY_INIT_TERMS) or clean_msg in cls.SCHEME_DISCOVERY_INIT_TERMS or norm_msg in cls.SCHEME_DISCOVERY_INIT_TERMS:
            return INTENT_SCHEME_DISCOVERY

        if re.search(r"\b(?:isme|iske|iska|ye)\s+(?:kitna\s+)?(?:loan|emi|interest|document|documents|paper|apply)\b", norm_msg):
            if "document" in norm_msg or "paper" in norm_msg:
                return INTENT_DOCUMENTS
            if "loan" in norm_msg or "emi" in norm_msg or "interest" in norm_msg:
                return INTENT_FINANCIAL_CALCULATION
            if "apply" in norm_msg:
                return CanonicalIntent("APPLICATION_QUERY", ())

        if any(term in norm_msg for term in cls.PROFILE_ANSWER_TERMS) or clean_msg in cls.PROFILE_ANSWER_TERMS:
            return INTENT_SCHEME_DISCOVERY

        # Route-based contextual defaults
        if "/applications/" in current_route:
            return CanonicalIntent("APPLICATION_QUERY", ())
        if "/calculator" in current_route:
            return INTENT_FINANCIAL_CALCULATION
        if "/locator" in current_route:
            return INTENT_PARTNER_LOCATION

        return INTENT_UNKNOWN
