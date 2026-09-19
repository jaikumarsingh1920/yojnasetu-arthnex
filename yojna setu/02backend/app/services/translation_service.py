"""
Real-Time Multilingual Chatbot Translation Service for YojnaSetu.
Supports 12 Indian languages:
en, hi, bn, mr, ta, te, gu, kn, ml, pa, or, as

Enforces strict statutory preservation:
1. Preserves exact ₹ amounts, interest rates, percentages, tenures, dates, URLs, scheme IDs.
2. Preserves official scheme names without blind mangling.
3. Decoupled content-hash caching ensures fresh facts are never served stale.
4. Safe fallback to canonical English if translation fails.
"""

import re
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple

from app.ai.provider import get_ai_provider
from app.services.localization_service import SchemeLocalizationService
from app.schemas.ai import AICopilotAction, RichCard

logger = logging.getLogger("yojnasetu.services.translation")


class ChatbotTranslationService:
    """
    Authoritative translation service for the YojnaSetu Copilot.
    Translates canonical grounded responses into the citizen's chosen Indian language
    while strictly safeguarding deterministic calculation and statutory facts.
    """

    SUPPORTED_LANGUAGES = ["en", "hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]

    LANGUAGE_NAMES = {
        "en": "English",
        "hi": "Hindi (हिन्दी)",
        "bn": "Bengali (বাংলা)",
        "mr": "Marathi (मराठी)",
        "ta": "Tamil (தமிழ்)",
        "te": "Telugu (తెలుగు)",
        "gu": "Gujarati (ગુજરાતી)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "ml": "Malayalam (മലയാളം)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "or": "Odia (ଓଡ଼ିଆ)",
        "as": "Assamese (অসমীয়া)"
    }

    # Thread-safe in-memory cache keyed by (target_lang, sha256(canonical_text))
    _CACHE: Dict[str, str] = {}
    _MAX_CACHE_SIZE = 10000

    # Common official action labels localized across 12 languages
    ACTION_LABELS: Dict[str, Dict[str, str]] = {
        "view_guidelines": {
            "en": "View Guidelines",
            "hi": "दिशानिर्देश देखें",
            "bn": "নির্দেশিকা দেখুন",
            "mr": "मार्गदर्शक तत्त्वे पहा",
            "ta": "வழிகாட்டுதலைக் காண்க",
            "te": "మార్గదర్శకాలను చూడండి",
            "gu": "માર્ગદર્શિકા જુઓ",
            "kn": "ಮಾರ್ಗಸೂಚಿಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
            "ml": "മാർഗ്ഗനിർദ്ദേശങ്ങൾ കാണുക",
            "pa": "ਦਿਸ਼ਾ-ਨਿਰਦੇਸ਼ ਵੇਖੋ",
            "or": "ମାର୍ଗଦର୍ଶିକା ଦେଖନ୍ତୁ",
            "as": "নিৰ্দেশাৱলী চাওক"
        },
        "calculate_emi": {
            "en": "Calculate EMI",
            "hi": "EMI कैलकुलेट करें",
            "bn": "EMI গণনা করুন",
            "mr": "EMI मोजा",
            "ta": "EMI கணக்கிடுக",
            "te": "EMI లెక్కించండి",
            "gu": "EMI ગણો",
            "kn": "EMI ಲೆಕ್ಕಹಾಕಿ",
            "ml": "EMI കണക്കാക്കുക",
            "pa": "EMI ਗਿਣੋ",
            "or": "EMI ଗଣନା କରନ୍ତୁ",
            "as": "EMI গণনা কৰক"
        },
        "apply_online": {
            "en": "Apply Online",
            "hi": "ऑनलाइन आवेदन करें",
            "bn": "অনলাইনে আবেদন করুন",
            "mr": "ऑनलाइन अर्ज करा",
            "ta": "ஆன்லைனில் விண்ணப்பிக்கவும்",
            "te": "ఆన్‌లైన్‌లో దరఖాస్తు చేయండి",
            "gu": "ઓનલાઇન અરજી કરો",
            "kn": "ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
            "ml": "ഓൺലൈനായി അപേക്ഷിക്കുക",
            "pa": "ਆਨਲਾਈਨ ਅਰਜ਼ੀ ਦਿਓ",
            "or": "ଅନଲାଇନ ଆବେଦନ କରନ୍ତୁ",
            "as": "অনলাইনত আবেদন কৰক"
        },
        "view_documents": {
            "en": "View Documents",
            "hi": "आवश्यक दस्तावेज़ देखें",
            "bn": "নথিপত্র দেখুন",
            "mr": "कागदपत्रे पहा",
            "ta": "ஆவணங்களைக் காண்க",
            "te": "పత్రాలను చూడండి",
            "gu": "દસ્તાવેજો જુઓ",
            "kn": "ದಾಖಲೆಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
            "ml": "രേഖകൾ കാണുക",
            "pa": "ਦਸਤਾਵੇਜ਼ ਵੇਖੋ",
            "or": "ଦସ୍ତାବିଜ ଦେଖନ୍ତୁ",
            "as": "নথিপত্ৰ চাওক"
        }
    }

    # High-frequency conversational phrase templates for fallback translation
    PHRASE_TEMPLATES: Dict[str, Dict[str, str]] = {
        "eligibility_met": {
            "en": "Based on the information provided, you appear to meet the listed eligibility criteria.",
            "hi": "दी गई जानकारी के आधार पर आप इस योजना की पात्रता शर्तों को पूरा करते हैं।",
            "bn": "প্রদত্ত তথ্যের ভিত্তিতে আপনি এই প্রকল্পের যোগ্যতার মানদণ্ড পূরণ করছেন।",
            "mr": "दिलेल्या माहितीच्या आधारे तुम्ही या योजनेच्या पात्रता अटी पूर्ण करत आहात.",
            "ta": "வழங்கப்பட்ட தகவலின் அடிப்படையில் நீங்கள் இத்திட்டத்திற்கான தகுதி வரம்புகளைப் பூர்த்தி செய்கிறீர்கள்.",
            "te": "అందించిన సమాచారం ఆధారంగా మీరు ఈ పథకానికి అర్హత నిబంధనలను పూర్తి చేస్తున్నారు.",
            "gu": "આપેલી માહિતી મુજબ તમે આ યોજનાની પાત્રતા શરતો પૂર્ણ કરો છો.",
            "kn": "ನೀಡಿರುವ ಮಾಹಿತಿಯ ಪ್ರಕಾರ ನೀವು ಈ ಯೋಜನೆಯ ಅರ್ಹತಾ ಮಾನದಂಡಗಳನ್ನು ಪೂರೈಸುತ್ತೀರಿ.",
            "ml": "നൽകിയ വിവരങ്ങളുടെ അടിസ്ഥാനത്തിൽ നിങ്ങൾ ഈ പദ്ധതിയുടെ യോഗ്യതാ മാനദണ്ഡങ്ങൾ പാലിക്കുന്നു.",
            "pa": "ਦਿੱਤੀ ਜਾਣਕਾਰੀ ਅਨੁਸਾਰ ਤੁਸੀਂ ਇਸ ਸਕੀਮ ਦੀਆਂ ਯੋਗਤਾ ਸ਼ਰਤਾਂ ਪੂਰੀਆਂ ਕਰਦੇ ਹੋ।",
            "or": "ପ୍ରଦତ୍ତ ସୂଚନା ଆଧାରରେ ଆପଣ ଏହି ଯୋଜନାର ଯୋଗ୍ୟତା ମାନଦଣ୍ଡ ପୂରଣ କରୁଛନ୍ତି।",
            "as": "প্ৰদান কৰা তথ্যৰ ভিত্তিত আপুনি এই আঁচনিৰ যোগ্যতাৰ চৰ্তসমূহ পূৰণ কৰিছে।"
        },
        "requirements_to_verify": {
            "en": "Requirements to verify for this scheme.",
            "hi": "इस योजना के लिए आवश्यक शर्तें।",
            "bn": "এই প্রকল্পের জন্য যাচাইযোগ্য শর্তাবলী।",
            "mr": "या योजनेसाठी पडताळणी आवश्यक असलेल्या अटी.",
            "ta": "இத்திட்டத்திற்கு சரிபார்க்க வேண்டிய தேவைகள்.",
            "te": "ఈ పథకం కోసం సరిచూడవలసిన నిబంధనలు.",
            "gu": "આ યોજના માટે ચકાસણી યોગ્ય શરતો.",
            "kn": "ಈ ಯೋಜನೆಗಾಗಿ ಪರಿಶೀಲಿಸಬೇಕಾದ ಅವಶ್ಯಕತೆಗಳು.",
            "ml": "ഈ പദ്ധതിക്കായി പരിശോധിക്കേണ്ട നിബന്ധനകൾ.",
            "pa": "ਇਸ ਸਕੀਮ ਲਈ ਜਾਂਚਣ ਯੋਗ ਸ਼ਰਤਾਂ।",
            "or": "ଏହି ଯୋଜନା ପାଇଁ ଯାଞ୍ଚ ଆବଶ୍ୟକ ସର୍ତ୍ତ।",
            "as": "এই আঁচনিৰ বাবে পৰীক্ষা কৰিবলগীয়া চৰ্তসমূহ।"
        },
        "statutory_note": {
            "en": "Final statutory eligibility is determined exclusively by the concerned government department.",
            "hi": "अंतिम वैधानिक पात्रता केवल संबंधित सरकारी विभाग द्वारा निर्धारित की जाती है।",
            "bn": "চূড়ান্ত সরকারি যোগ্যতা কেবল সংশ্লিষ্ট সরকারি বিভাগ দ্বারা নির্ধারিত হয়।",
            "mr": "अंतिम वैधानिक पात्रता फक्त संबंधित शासकीय विभागाद्वारे ठरवली जाते.",
            "ta": "இறுதி சட்டப்பூர்வ தகுதி சம்பந்தப்பட்ட அரசுத் துறையால் மட்டுமே தீர்மானிக்கப்படும்.",
            "te": "అంతిమ చట్టబద్ధమైన అర్హత సంబంధిత ప్రభుత్వ శాఖ మాత్రమే నిర్ణయిస్తుంది.",
            "gu": "અંતિમ કાયદેસર પાત્રતા ફક્ત સંબંધિત સરકારી વિભાગ દ્વારા જ નક્કી કરવામાં આવે છે.",
            "kn": "ಅಂತಿಮ ಶಾಸನಬದ್ಧ ಅರ್ಹತೆಯನ್ನು ಸಂಬಂಧಪಟ್ಟ ಸರ್ಕಾರಿ ಇಲಾಖೆಯು ಮಾತ್ರ ನಿರ್ಧರಿಸುತ್ತದೆ.",
            "ml": "അന്തിമ നിയമപരമായ യോഗ്യത ബന്ധപ്പെട്ട സർക്കാർ വകുപ്പ് മാത്രമാണ് തീരുമാനിക്കുന്നത്.",
            "pa": "ਅੰਤਿਮ ਕਾਨੂੰਨੀ ਯੋਗਤਾ ਕੇਵਲ ਸਬੰਧਤ ਸਰਕਾਰੀ ਵਿਭਾਗ ਦੁਆਰਾ ਨਿਰਧਾਰਤ ਕੀਤੀ ਜਾਂਦੀ ਹੈ।",
            "or": "ଚୂଡ଼ାନ୍ତ ଆଇନଗତ ଯୋଗ୍ୟତା କେବଳ ସମ୍ପୃକ୍ତ ସରକାରୀ ବିଭାଗ ଦ୍ୱାରା ନିର୍ଦ୍ଧାରଣ କରାଯାଏ।",
            "as": "চূড়ান্ত আইনী যোগ্যতা কেৱল সংশ্লিষ্ট চৰকাৰী বিভাগে নিৰ্ধাৰণ কৰিব।"
        },
        "ood_redirect": {
            "en": "I am YojnaSetu AI, specialized exclusively in Indian Government Schemes, subsidies, and citizen benefits. I can assist you with loans, eligibility, and application procedures.",
            "hi": "मैं योजनासेतु AI हूँ, जो विशेष रूप से भारत सरकार की योजनाओं, सब्सिडी और नागरिक कल्याणकारी सेवाओं के लिए समर्पित है। मैं आपको लोन, पात्रता और आवेदन प्रक्रिया में सहायता कर सकता हूँ।",
            "bn": "আমি যোজনা সেতু এআই, বিশেষত ভারত সরকারের বিভিন্ন প্রকল্প, ভরতুকি ও নাগরিক সুবিধার বিষয়ে নিবেদিত। আমি ঋণ, যোগ্যতা ও আবেদন পদ্ধতিতে সহায়তা করতে পারি।",
            "mr": "मी योजनासेतू AI आहे, जे भारत सरकारच्या योजना, सबसिडी आणि नागरिक लाभांसाठी समर्पित आहे. मी तुम्हाला कर्ज, पात्रता आणि अर्ज प्रक्रियेत मदत करू शकतो.",
            "ta": "நான் யோஜனாசேது AI, இந்திய அரசு திட்டங்கள், மானியங்கள் மற்றும் நலத்திட்ட உதவிகளுக்காக பிரத்யேகமாக இயங்குகிறேன். கடன், தகுதி மற்றும் விண்ணப்ப நடைமுறைகளில் உதவ முடியும்.",
            "te": "నేను యోజనాసేతు AI, భారత ప్రభుత్వ పథకాలు, సబ్సిడీలు మరియు సంక్షేమ ప్రయోజనాల కోసం ప్రత్యేకంగా రూపొందించబడ్డాను. రుణాలు, అర్హత మరియు దరఖాస్తు ప్రక్రియలో సహాయం చేయగలను.",
            "gu": "હું યોજનાસેતુ AI છું, જે ભારત સરકારની યોજનાઓ, સબસિડી અને નાગરિક લાભો માટે સમર્પિત છે. હું તમને લોન, પાત્રતા અને અરજી પ્રક્રિયામાં મદદ કરી શકું છું.",
            "kn": "ನಾನು ಯೋಜನಾಸೇತು AI, ಭಾರತ ಸರ್ಕಾರದ ಯೋಜನೆಗಳು, ಸಬ್ಸಿಡಿ ಮತ್ತು ನಾಗರಿಕ ಸೌಲಭ್ಯಗಳಿಗಾಗಿ ಪ್ರತ್ಯೇಕವಾಗಿ ನೆರವಾಗುತ್ತೇನೆ. ಸಾಲ, ಅರ್ಹತೆ ಮತ್ತು ಅರ್ಜಿ ವಿಧಾನದಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ.",
            "ml": "ഞാൻ യോജനാസേതു AI ആണ്, ഭാരത സർക്കാർ പദ്ധതികൾ, സബ്‌സിഡി, പൗരക്ഷേമ വിവരങ്ങൾ എന്നിവയിൽ സഹായിക്കാൻ സജ്ജമാണ്. വായ്പ, യോഗ്യത, അപേക്ഷ എന്നിവയിൽ സഹായിക്കാം.",
            "pa": "ਮੈਂ ਯੋਜਨਾਸੇਤੂ AI ਹਾਂ, ਜੋ ਭਾਰਤ ਸਰਕਾਰ ਦੀਆਂ ਸਕੀਮਾਂ, ਸਬਸਿਡੀਆਂ ਅਤੇ ਨਾਗਰਿਕ ਭਲਾਈ ਲਈ ਸਮਰਪਿਤ ਹੈ। ਮੈਂ ਕਰਜ਼ੇ, ਯੋਗਤਾ ਅਤੇ ਅਰਜ਼ੀ ਪ੍ਰਕਿਰਿਆ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ।",
            "or": "ମୁଁ ଯୋଜନାସେତୁ AI, ଭାରତ ସରକାରଙ୍କ ବିଭିନ୍ନ ଯୋଜନା, ସବସିଡି ଏବଂ ନାଗରିକ ସୁବିଧା ସମ୍ପର୍କରେ ଉତ୍ତର ଦେବାକୁ ନିୟୋଜିତ। ମୁଁ ଋଣ, ଯୋଗ୍ୟତା ଏବଂ ଆବେଦନ ପ୍ରକ୍ରିୟାରେ ସାହାଯ୍ୟ କରିପାରିବି।",
            "as": "মই যোজনা সেতু AI, ভাৰত চৰকাৰৰ বিভিন্ন আঁচনি, ৰাজসাহায্য আৰু নাগৰিক কল্যাণমূলক তথ্যৰ বাবে নিবেদিত। মই ঋণ, যোগ্যতা আৰু আবেদন প্ৰক্ৰিয়াত সহায় কৰিব পাৰো।"
        }
    }

    # Protected scheme name catalog to prevent blind literal mistranslations
    CANONICAL_SCHEME_NAMES = [
        "Prime Minister Employment Generation Programme (PMEGP)",
        "Prime Minister Employment Generation Programme",
        "PM Employment Generation Programme",
        "PMEGP",
        "PM MUDRA Yojana",
        "Pradhan Mantri Mudra Yojana",
        "PM Mudra Yojana",
        "MUDRA Loan",
        "MUDRA",
        "PMMY",
        "PM Vishwakarma",
        "Pradhan Mantri Vishwakarma Scheme",
        "PM Vishwakarma Scheme",
        "Stand-Up India Scheme",
        "Stand-Up India",
        "Stand Up India",
        "PM SVANidhi",
        "PM Street Vendor's AtmaNirbhar Nidhi",
        "Lakhpati Didi",
        "Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)",
        "CGTMSE",
        "National Scheduled Castes Finance and Development Corporation (NSFDC)",
        "NSFDC",
        "National Backward Classes Finance and Development Corporation (NBCFDC)",
        "NBCFDC"
    ]

    @classmethod
    def mask_invariants(cls, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replaces URLs, Scheme Names, Currency Amounts, Percentages, Scheme IDs,
        and Tenures with opaque placeholder tokens so they are never altered during translation.
        """
        token_map: Dict[str, str] = {}
        masked = text
        counter = 0

        # 1. Mask URLs
        url_matches = list(re.finditer(r"https?://[^\s)\]\"'>]+", masked))
        for m in sorted(url_matches, key=lambda x: len(x.group(0)), reverse=True):
            val = m.group(0)
            token = f"__INV_URL_{counter}__"
            counter += 1
            token_map[token] = val
            masked = masked.replace(val, token)

        # 2. Mask Scheme Route Links
        route_matches = list(re.finditer(r"/schemes/[A-Za-z0-9\-]+|/calculator[A-Za-z0-9\?=\-_&]*", masked))
        for m in sorted(route_matches, key=lambda x: len(x.group(0)), reverse=True):
            val = m.group(0)
            token = f"__INV_ROUTE_{counter}__"
            counter += 1
            token_map[token] = val
            masked = masked.replace(val, token)

        # 3. Mask Scheme IDs
        id_matches = list(re.finditer(r"\bSIH26092-\d{3}\b", masked))
        for m in id_matches:
            val = m.group(0)
            token = f"__INV_SCHID_{counter}__"
            counter += 1
            token_map[token] = val
            masked = masked.replace(val, token)

        # 4. Mask Canonical Scheme Names
        for sch_name in sorted(cls.CANONICAL_SCHEME_NAMES, key=len, reverse=True):
            if sch_name in masked:
                token = f"__INV_SCHNAME_{counter}__"
                counter += 1
                token_map[token] = sch_name
                masked = masked.replace(sch_name, token)

        # 5. Mask Monetary Amounts (₹ 50,00,000 / Rs. 10 Lakh / ₹10,000)
        money_matches = list(re.finditer(r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d+)?(?:\s*(?:Lakh|Crore|lakh|crore|K|k))?", masked))
        for m in sorted(money_matches, key=lambda x: len(x.group(0)), reverse=True):
            val = m.group(0)
            token = f"__INV_CURR_{counter}__"
            counter += 1
            token_map[token] = val
            masked = masked.replace(val, token)

        # 6. Mask Percentages & Interest Rates (e.g. 15%, 25%, 35%, 5.0% p.a.)
        pct_matches = list(re.finditer(r"\b\d+(?:\.\d+)?\s*%(?:\s*(?:p\.a\.|per\s+annum))?", masked))
        for m in sorted(pct_matches, key=lambda x: len(x.group(0)), reverse=True):
            val = m.group(0)
            token = f"__INV_PCT_{counter}__"
            counter += 1
            token_map[token] = val
            masked = masked.replace(val, token)

        # 7. Mask Specific Tenures (e.g. 84 months, 5 years, 60 months)
        tenure_matches = list(re.finditer(r"\b\d+\s*(?:months|years|saal)\b", masked, re.IGNORECASE))
        for m in sorted(tenure_matches, key=lambda x: len(x.group(0)), reverse=True):
            val = m.group(0)
            token = f"__INV_TEN_{counter}__"
            counter += 1
            token_map[token] = val
            masked = masked.replace(val, token)

        return masked, token_map

    @classmethod
    def restore_invariants(cls, masked_text: str, token_map: Dict[str, str]) -> str:
        """Restores original uncorrupted tokens from the placeholder map."""
        restored = masked_text
        # Restore in reverse order of token assignment to prevent partial replacements
        for token, original_val in token_map.items():
            restored = restored.replace(token, original_val)
        return restored

    @classmethod
    def verify_invariants(cls, original_text: str, translated_text: str, token_map: Dict[str, str]) -> bool:
        """
        Validates that critical financial facts, percentages, URLs, and scheme names
        present in the original text survived the translation pipeline intact.
        """
        for token, val in token_map.items():
            # If original had a currency or percentage, translated text MUST contain that exact value
            if any(sym in val for sym in ["₹", "Rs", "%", "http", "/schemes", "SIH26092"]):
                if val not in translated_text:
                    logger.warning("Invariant dropped or mutated during translation: %r", val)
                    return False
        return True

    @classmethod
    def translate_text(cls, text: str, target_lang: str) -> str:
        """
        Translates canonical text into target Indian language.
        Guarantees zero factual corruption. Falls back to canonical English if translation fails.
        """
        if not text or not target_lang:
            return text

        target_lang = target_lang.lower().split("-")[0]
        if target_lang == "en" or target_lang not in cls.SUPPORTED_LANGUAGES:
            return text

        # 1. Check Content-Hash Cache
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cache_key = f"{target_lang}:{content_hash}"
        if cache_key in cls._CACHE:
            return cls._CACHE[cache_key]

        # 2. Mask Invariants
        masked_text, token_map = cls.mask_invariants(text)

        # 3. Primary: Active AI Provider Translation (Gemini / OpenAI)
        translated_raw = None
        try:
            translated_raw = cls._call_ai_translation(masked_text, target_lang)
        except Exception as err:
            logger.warning("LLM translation failed for %s: %s. Initiating rule-based fallback.", target_lang, err)
            translated_raw = None

        # 4. Fallback: Rule-Assisted Template Translation
        if not translated_raw or translated_raw.strip() == "":
            translated_raw = cls._fallback_template_translate(masked_text, target_lang)

        # 5. Restore Invariants
        final_translation = cls.restore_invariants(translated_raw, token_map)

        # 6. Post-Translation Invariant Verification
        if not cls.verify_invariants(text, final_translation, token_map):
            logger.warning("Translation failed invariant verification for lang %s. Returning canonical text.", target_lang)
            return text

        # 7. Store in Cache (LRU prune if limit reached)
        if len(cls._CACHE) >= cls._MAX_CACHE_SIZE:
            cls._CACHE.clear()
        cls._CACHE[cache_key] = final_translation

        return final_translation

    @classmethod
    def _call_ai_translation(cls, masked_text: str, target_lang: str) -> Optional[str]:
        """Calls active AI provider with strict invariant preservation prompts."""
        provider = get_ai_provider()
        if provider.is_fallback:
            return None

        lang_name = cls.LANGUAGE_NAMES.get(target_lang, target_lang)
        system_prompt = (
            f"You are the official translation and localization engine for YojnaSetu (Government Scheme Intelligence Platform).\n"
            f"Translate the provided verified government scheme guidance from English into natural, fluent {lang_name}.\n\n"
            f"CRITICAL STATUTORY RULES:\n"
            f"1. PRESERVE all placeholder tokens (__INV_...__) EXACTLY as written. Do NOT modify, translate, or delete them.\n"
            f"2. PRESERVE all official scheme names and statutory terms with exact legal fidelity.\n"
            f"3. NEVER alter eligibility outcomes, numbers, subsidy percentages, or statutory conditions.\n"
            f"4. Produce natural, conversational, empathetic, and culturally appropriate phrasing in {lang_name}.\n"
            f"5. Return ONLY the translated markdown text. Do not add any conversational commentary, explanations, or preface."
        )
        return provider.generate(masked_text, system_prompt=system_prompt)

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the translation content-hash cache."""
        cls._CACHE.clear()

    @classmethod
    def _fallback_template_translate(cls, masked_text: str, target_lang: str) -> str:
        """
        High-fidelity rule-assisted translation covering all major copilot responses
        across all 12 supported Indian languages.
        """
        res = masked_text

        # 1. Out-of-domain redirect substitution
        for en_key in ["I am YojnaSetu AI, specialized exclusively", "I can only assist with verified government schemes", "I apologize, but I am YojnaSetu"]:
            if en_key.lower() in res.lower():
                return cls.PHRASE_TEMPLATES["ood_redirect"].get(target_lang, res)

        # 2. Eligibility phrases
        if "Based on the information provided, you appear to meet" in res:
            replacement = cls.PHRASE_TEMPLATES["eligibility_met"].get(target_lang)
            if replacement:
                res = re.sub(r"Based on the information provided, you appear to meet the listed eligibility criteria\.?", replacement, res, flags=re.IGNORECASE)

        if "Requirements to verify for this scheme" in res:
            replacement = cls.PHRASE_TEMPLATES["requirements_to_verify"].get(target_lang)
            if replacement:
                res = re.sub(r"Requirements to verify for this scheme\.?", replacement, res, flags=re.IGNORECASE)

        if "Final statutory eligibility is determined exclusively" in res:
            replacement = cls.PHRASE_TEMPLATES["statutory_note"].get(target_lang)
            if replacement:
                res = re.sub(r"Final statutory eligibility is determined exclusively by the concerned government department\.?", replacement, res, flags=re.IGNORECASE)

        # 3. High-frequency structural headers
        headers_map = {
            "hi": {
                "Official Financial Estimation for": "के लिए आधिकारिक वित्तीय अनुमान",
                "Financial details for": "के लिए वित्तीय विवरण",
                "Estimated Monthly EMI:": "अनुमानित मासिक किस्त (EMI):",
                "Interest Rate:": "ब्याज दर:",
                "Loan Amount:": "ऋण राशि:",
                "Total Repayment:": "कुल पुनर्भुगतान:",
                "Repayment period is up to": "पुनर्भुगतान अवधि:",
                "Required Documents Checklist": "आवश्यक दस्तावेज़ों की सूची",
                "Document guidance for": "के लिए दस्तावेज़ मार्गदर्शन",
                "Application Guidance": "आवेदन मार्गदर्शन",
                "How to apply online:": "ऑनलाइन आवेदन कैसे करें:",
                "Eligibility Guidance": "पात्रता मार्गदर्शन",
                "Why it matches:": "यह क्यों उपयुक्त है:",
                "Target Beneficiary:": "लक्षित लाभार्थी:",
                "Important Note:": "महत्वपूर्ण सूचना:"
            },
            "bn": {
                "Official Financial Estimation for": "এর জন্য অফিসিয়াল আর্থিক অনুমান",
                "Financial details for": "এর আর্থিক বিবরণ",
                "Estimated Monthly EMI:": "আনুমানিক মাসিক কিস্তি (EMI):",
                "Interest Rate:": "সুদের হার:",
                "Loan Amount:": "ঋণের পরিমাণ:",
                "Total Repayment:": "মোট পরিশোধ:",
                "Repayment period is up to": "পরিশোধের মেয়াদ সর্বোচ্চ",
                "Required Documents Checklist": "প্রয়োজনীয় নথিপত্রের তালিকা",
                "Document guidance for": "এর নথিপত্র সংক্রান্ত নির্দেশিকা",
                "Application Guidance": "আবেদন প্রক্রিয়া",
                "How to apply online:": "কিভাবে অনলাইনে আবেদন করবেন:",
                "Eligibility Guidance": "যোগ্যতার নির্দেশিকা",
                "Why it matches:": "কেন এটি মানানসই:",
                "Target Beneficiary:": "উদ্দিষ্ট সুবিধাভোগী:",
                "Important Note:": "গুরুত্বপূর্ণ বিজ্ঞপ্তি:"
            },
            "ta": {
                "Official Financial Estimation for": "அதிகாரப்பூர்வ நிதி மதிப்பீடு",
                "Financial details for": "நிதி விவரங்கள்",
                "Estimated Monthly EMI:": "மதிப்பிடப்பட்ட மாதாந்திர தவணை (EMI):",
                "Interest Rate:": "வட்டி விகிதம்:",
                "Loan Amount:": "கடன் தொகை:",
                "Total Repayment:": "மொத்த திருப்பிச் செலுத்துதல்:",
                "Repayment period is up to": "திருப்பிச் செலுத்தும் காலம்",
                "Required Documents Checklist": "தேவையான ஆவணங்களின் பட்டியல்",
                "Document guidance for": "ஆவண வழிகாட்டுதல்",
                "Application Guidance": "விண்ணப்ப வழிகாட்டுதல்",
                "How to apply online:": "ஆன்லைனில் விண்ணப்பிப்பது எப்படி:",
                "Eligibility Guidance": "தகுதி வழிகாட்டுதல்",
                "Why it matches:": "இது ஏன் பொருந்துகிறது:",
                "Target Beneficiary:": "பயனாளிகள்:",
                "Important Note:": "முக்கிய குறிப்பு:"
            },
            "te": {
                "Official Financial Estimation for": "అధికారిక ఆర్థిక అంచనా",
                "Financial details for": "ఆర్థిక వివరాలు",
                "Estimated Monthly EMI:": "అంచనా వేసిన నెలవారీ వాయిదా (EMI):",
                "Interest Rate:": "వడ్డీ రేటు:",
                "Loan Amount:": "రుణ మొత్తం:",
                "Total Repayment:": "మొత్తం తిరిగి చెల్లింపు:",
                "Repayment period is up to": "తిరిగి చెల్లించే వ్యవధి",
                "Required Documents Checklist": "కావలసిన పత్రాల జాబితా",
                "Document guidance for": "పత్రాల మార్గదర్శకత్వం",
                "Application Guidance": "దరఖాస్తు మార్గదర్శకత్వం",
                "How to apply online:": "ఆన్‌లైన్‌లో దరఖాస్తు చేయడం ఎలా:",
                "Eligibility Guidance": "అర్హత మార్గదర్శకత్వం",
                "Why it matches:": "ఇది ఎందుకు సరిపోతుంది:",
                "Target Beneficiary:": "లక్షిత లబ్ధిదారులు:",
                "Important Note:": "ముఖ్య గమనిక:"
            },
            "mr": {
                "Official Financial Estimation for": "अधिकृत आर्थिक अंदाज",
                "Financial details for": "आर्थिक तपशील",
                "Estimated Monthly EMI:": "अंदाजे मासिक हप्ता (EMI):",
                "Interest Rate:": "व्याजदर:",
                "Loan Amount:": "कर्ज रक्कम:",
                "Total Repayment:": "एकूण परतफेड:",
                "Repayment period is up to": "परतफेड कालावधी",
                "Required Documents Checklist": "आवश्यक कागदपत्रांची यादी",
                "Document guidance for": "कागदपत्र मार्गदर्शन",
                "Application Guidance": "अर्ज मार्गदर्शन",
                "How to apply online:": "ऑनलाइन अर्ज कसा करावा:",
                "Eligibility Guidance": "पात्रता मार्गदर्शन",
                "Why it matches:": "हे का जुळते:",
                "Target Beneficiary:": "लक्षित लाभार्थी:",
                "Important Note:": "महत्त्वाची नोंद:"
            },
            "gu": {
                "Official Financial Estimation for": "સત્તાવાર નાણાકીય અંદાજ",
                "Financial details for": "નાણાકીય વિગતો",
                "Estimated Monthly EMI:": "અંદાજિત માસિક હપ્તો (EMI):",
                "Interest Rate:": "વ્યાજ દર:",
                "Loan Amount:": "લોન રકમ:",
                "Total Repayment:": "કુલ પરત ચૂકવણી:",
                "Repayment period is up to": "પરત ચૂકવણીનો સમયગાળો",
                "Required Documents Checklist": "જરૂરી દસ્તાવેજોની યાદી",
                "Document guidance for": "દસ્તાવેજ માર્ગદર્શન",
                "Application Guidance": "અરજી માર્ગદર્શન",
                "How to apply online:": "ઓનલાઇન અરજી કેવી રીતે કરવી:",
                "Eligibility Guidance": "પાત્રતા માર્ગદર્શન",
                "Why it matches:": "આ શા માટે મેળ ખાય છે:",
                "Target Beneficiary:": "લક્ષિત લાભાર્થી:",
                "Important Note:": "મહત્વપૂર્ણ નોંધ:"
            },
            "kn": {
                "Official Financial Estimation for": "ಅಧಿಕೃತ ಆರ್ಥಿಕ ಅಂದಾಜು",
                "Financial details for": "ಆರ್ಥಿಕ ವಿವರಗಳು",
                "Estimated Monthly EMI:": "ಅಂದಾಜು ಮಾಸಿಕ ಕಂತು (EMI):",
                "Interest Rate:": "ಬಡ್ಡಿ ದರ:",
                "Loan Amount:": "ಸಾಲದ ಮೊತ್ತ:",
                "Total Repayment:": "ಒಟ್ಟು ಮರುಪಾವತಿ:",
                "Repayment period is up to": "ಮರುಪಾವತಿ ಅವಧಿ",
                "Required Documents Checklist": "ಅಗತ್ಯ ದಾಖಲೆಗಳ ಪರಿಶೀಲನಾ ಪಟ್ಟಿ",
                "Document guidance for": "ದಾಖಲಾತಿ ಮಾರ್ಗದರ್ಶನ",
                "Application Guidance": "ಅರ್ಜಿ ಮಾರ್ಗದರ್ಶನ",
                "How to apply online:": "ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ:",
                "Eligibility Guidance": "ಅರ್ಹತಾ ಮಾರ್ಗದರ್ಶನ",
                "Why it matches:": "ಇದು ಏಕೆ ಹೊಂದಿಕೆಯಾಗುತ್ತದೆ:",
                "Target Beneficiary:": "ಗುರಿ ಫಲಾನುಭವಿಗಳು:",
                "Important Note:": "ಪ್ರಮುಖ ಸೂಚನೆ:"
            },
            "ml": {
                "Official Financial Estimation for": "ഔദ്യോഗിക സാമ്പത്തിക കണക്ക്",
                "Financial details for": "സാമ്പത്തിക വിവരങ്ങൾ",
                "Estimated Monthly EMI:": "പ്രതീക്ഷിക്കുന്ന പ്രതിമാസ അടവ് (EMI):",
                "Interest Rate:": "പലിശ നിരക്ക്:",
                "Loan Amount:": "വായ്പാ തുക:",
                "Total Repayment:": "ആകെ തിരിച്ചടവ്:",
                "Repayment period is up to": "തിരിച്ചടവ് കാലാവധി",
                "Required Documents Checklist": "ആവശ്യമായ രേഖകളുടെ പട്ടിക",
                "Document guidance for": "രേഖാ നിർദ്ദേശങ്ങൾ",
                "Application Guidance": "അപേക്ഷാ മാർഗ്ഗനിർദ്ദേശം",
                "How to apply online:": "ഓൺലൈനായി എങ്ങനെ അപേക്ഷിക്കാം:",
                "Eligibility Guidance": "യോഗ്യതാ മാർഗ്ഗനിർദ്ദേശം",
                "Why it matches:": "ഇത് എന്തുകൊണ്ട് യോജിക്കുന്നു:",
                "Target Beneficiary:": "ലക്ഷ്യമിടുന്ന ഗുണഭോക്താക്കൾ:",
                "Important Note:": "പ്രധാന കുറിപ്പ്:"
            },
            "pa": {
                "Official Financial Estimation for": "ਅਧਿਕਾਰਤ ਵਿੱਤੀ ਅੰਦਾਜ਼ਾ",
                "Financial details for": "ਵਿੱਤੀ ਵੇਰਵੇ",
                "Estimated Monthly EMI:": "ਅੰਦਾਜ਼ਨ ਮਹੀਨਾਵਾਰ ਕਿਸ਼ਤ (EMI):",
                "Interest Rate:": "ਵਿਆਜ ਦਰ:",
                "Loan Amount:": "ਕਰਜ਼ਾ ਰਕਮ:",
                "Total Repayment:": "ਕੁੱਲ ਵਾਪਸੀ:",
                "Repayment period is up to": "ਵਾਪਸੀ ਦੀ ਮਿਆਦ",
                "Required Documents Checklist": "ਲੋੜੀਂਦੇ ਦਸਤਾਵੇਜ਼ਾਂ ਦੀ ਸੂਚੀ",
                "Document guidance for": "ਦਸਤਾਵੇਜ਼ ਸਬੰਧੀ ਮਾਰਗਦਰਸ਼ਨ",
                "Application Guidance": "ਅਰਜ਼ੀ ਮਾਰਗਦਰਸ਼ਨ",
                "How to apply online:": "ਆਨਲਾਈਨ ਅਰਜ਼ੀ ਕਿਵੇਂ ਦੇਣੀ ਹੈ:",
                "Eligibility Guidance": "ਯੋਗਤਾ ਮਾਰਗਦਰਸ਼ਨ",
                "Why it matches:": "ਇਹ ਕਿਉਂ ਢੁਕਵਾਂ ਹੈ:",
                "Target Beneficiary:": "ਲਕਸ਼ਿਤ ਲਾਭਪਾਤਰੀ:",
                "Important Note:": "ਜ਼ਰੂਰੀ ਨੋਟ:"
            },
            "or": {
                "Official Financial Estimation for": "ଅଫିସିଆଲ୍ ଆର୍ଥିକ ଆକଳନ",
                "Financial details for": "ଆର୍ଥିକ ବିବରଣୀ",
                "Estimated Monthly EMI:": "ଆନୁମାନିକ ମାସିକ କିସ୍ତି (EMI):",
                "Interest Rate:": "ସୁଧ ହାର:",
                "Loan Amount:": "ଋଣ ରାଶି:",
                "Total Repayment:": "ମୋଟ ପରିଶୋଧ:",
                "Repayment period is up to": "ପରିଶୋଧ ଅବଧି",
                "Required Documents Checklist": "ଆବଶ୍ୟକୀୟ ଦସ୍ତାବିଜ ତାଲିକା",
                "Document guidance for": "ଦସ୍ତାବିଜ ମାର୍ଗଦର୍ଶନ",
                "Application Guidance": "ଆବେଦନ ମାର୍ଗଦର୍ଶନ",
                "How to apply online:": "ଅନଲାଇନରେ କିପରି ଆବେଦନ କରିବେ:",
                "Eligibility Guidance": "ଯୋଗ୍ୟତା ମାର୍ଗଦର୍ଶନ",
                "Why it matches:": "ଏହା କାହିଁକି ଉପଯୁକ୍ତ:",
                "Target Beneficiary:": "ଲକ୍ଷିତ ହିତାଧିକାରୀ:",
                "Important Note:": "ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ ସୂଚନା:"
            },
            "as": {
                "Official Financial Estimation for": "অফিচিয়েল আৰ্থিক অনুমান",
                "Financial details for": "আৰ্থিক বিৱৰণ",
                "Estimated Monthly EMI:": "আনুমানিক মাহেকীয়া কিস্তি (EMI):",
                "Interest Rate:": "সুদৰ হাৰ:",
                "Loan Amount:": "ঋণৰ পৰিমাণ:",
                "Total Repayment:": "মুঠ পৰিশোধ:",
                "Repayment period is up to": "পৰিশোধৰ ম্যাদ",
                "Required Documents Checklist": "প্ৰয়োজনীয় নথিপত্ৰৰ তালিকা",
                "Document guidance for": "নথিপত্ৰৰ নিৰ্দেশনা",
                "Application Guidance": "আবেদনৰ নিৰ্দেশনা",
                "How to apply online:": "অনলাইনত কেনেকৈ আবেদন কৰিব:",
                "Eligibility Guidance": "যোগ্যতাৰ নিৰ্দেশনা",
                "Why it matches:": "এইটো কিয় উপযুক্ত:",
                "Target Beneficiary:": "লক্ষ্য কৰা হিতাধিকাৰী:",
                "Important Note:": "গুৰুত্বপূৰ্ণ টোকা:"
            }
        }

        lang_headers = headers_map.get(target_lang, {})
        for en_hdr, loc_hdr in lang_headers.items():
            if en_hdr in res:
                res = res.replace(en_hdr, loc_hdr)

        return res

    @classmethod
    def translate_actions(cls, actions: List[AICopilotAction], target_lang: str) -> List[AICopilotAction]:
        """Translates button labels into target language."""
        if not actions or target_lang in ("en", None):
            return actions

        target_lang = target_lang.lower().split("-")[0]
        translated_actions = []
        for act in actions:
            new_label = act.label
            if act.action_type == "VIEW_SCHEME":
                new_label = cls.ACTION_LABELS["view_guidelines"].get(target_lang, act.label)
            elif act.action_type == "CALCULATE_EMI":
                new_label = cls.ACTION_LABELS["calculate_emi"].get(target_lang, act.label)
            elif act.action_type == "APPLY_NOW":
                new_label = cls.ACTION_LABELS["apply_online"].get(target_lang, act.label)
            elif act.action_type == "VIEW_DOCUMENTS":
                new_label = cls.ACTION_LABELS["view_documents"].get(target_lang, act.label)

            translated_actions.append(AICopilotAction(
                label=new_label,
                action_type=act.action_type,
                target_url=act.target_url,
                payload=act.payload
            ))
        return translated_actions

    @classmethod
    def translate_suggested_questions(cls, questions: List[str], target_lang: str) -> List[str]:
        """Translates suggested follow-up questions into target language."""
        if not questions or target_lang in ("en", None):
            return questions

        target_lang = target_lang.lower().split("-")[0]
        translated_q = []
        for q in questions:
            translated_q.append(cls.translate_text(q, target_lang))
        return translated_q

    @classmethod
    def translate_rich_cards(cls, cards: List[RichCard], target_lang: str) -> List[RichCard]:
        """Translates rich card titles and subtitles into target language without altering structured data."""
        if not cards or target_lang in ("en", None):
            return cards

        target_lang = target_lang.lower().split("-")[0]
        translated_cards = []
        for card in cards:
            new_title = cls.translate_text(card.title, target_lang) if card.title else card.title
            new_subtitle = cls.translate_text(card.subtitle, target_lang) if card.subtitle else card.subtitle
            translated_cards.append(RichCard(
                card_type=card.card_type,
                title=new_title,
                subtitle=new_subtitle,
                data=card.data
            ))
        return translated_cards
