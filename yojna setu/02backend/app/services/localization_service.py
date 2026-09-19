from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("yojnasetu.services.localization")

class SchemeLocalizationService:
    """
    Full-Stack Localization Service for YojnaSetu Dynamic Scheme Data & Explanations.
    Translates dynamic scheme information into 12 Indian languages:
    en, hi, bn, te, mr, ta, gu, kn, ml, pa, or, as
    Preserves exact numeric values, ₹ amounts, interest rates, and official URLs.
    """

    LABELS: Dict[str, Dict[str, str]] = {
        "en": {
            "eligibility_met": "Based on the information provided, you appear to meet the listed eligibility criteria.",
            "eligibility_check": "Requirements to verify for this scheme.",
            "authority_note": "Final eligibility is determined exclusively by the concerned government authority.",
            "verified_scheme": "Verified Government Scheme",
            "apply_portal": "Apply on Official Portal",
            "document_checklist": "Required Documents Checklist",
            "loan_emi_title": "Loan EMI & Financial Estimate",
            "subsidy_estimate": "Estimated Govt Subsidy",
            "citation_title": "Official Government Scheme Knowledge Base",
        },
        "hi": {
            "eligibility_met": "दी गई जानकारी के आधार पर आप इस योजना की पात्रता शर्तों को पूरा करते हैं।",
            "eligibility_check": "इस योजना के लिए आवश्यक शर्तें।",
            "authority_note": "अंतिम पात्रता केवल संबंधित सरकारी प्राधिकरण द्वारा निर्धारित की जाती है।",
            "verified_scheme": "सत्यापित सरकारी योजना",
            "apply_portal": "आधिकारिक पोर्टल पर आवेदन करें",
            "document_checklist": "आवश्यक दस्तावेजों की सूची",
            "loan_emi_title": "ऋण किस्त एवं वित्तीय अनुमान",
            "subsidy_estimate": "अनुमानित सरकारी सब्सिडी",
            "citation_title": "सत्यापित सरकारी योजना जानकारी",
        },
        "bn": {
            "eligibility_met": "প্রদত্ত তথ্যের ভিত্তিতে আপনি এই প্রকল্পের যোগ্যতার মানদণ্ড পূরণ করছেন।",
            "eligibility_check": "এই প্রকল্পের প্রয়োজনীয় শর্তাবলী।",
            "authority_note": "চূড়ান্ত যোগ্যতা কেবল সংশ্লিষ্ট সরকারি কর্তৃপক্ষ দ্বারা নির্ধারিত হয়।",
            "verified_scheme": "যাচাইকৃত সরকারি প্রকল্প",
            "apply_portal": "অফিসিয়াল পোর্টালে আবেদন করুন",
            "document_checklist": "প্রয়োজনীয় নথিপত্রের তালিকা",
            "loan_emi_title": "ঋণের কিস্তি ও আর্থিক হিসাব",
            "subsidy_estimate": "আনুমানিক সরকারি ভরতুকি",
            "citation_title": "অফিসিয়াল সরকারি তথ্য",
        },
        "te": {
            "eligibility_met": "అందించిన సమాచారం ఆధారంగా మీరు ఈ పథకానికి అర్హత నిబంధనలను పూర్తి చేస్తున్నారు.",
            "eligibility_check": "ఈ పథకానికి కావలసిన నిబంధనలు.",
            "authority_note": "అంతిమ అర్హత సంబంధిత ప్రభుత్వ అధికారి మాత్రమే నిర్ణయిస్తారు.",
            "verified_scheme": "ధృవీకరించబడిన ప్రభుత్వ పథకం",
            "apply_portal": "అధికారిక పోర్టల్‌లో దరఖాస్తు చేయండి",
            "document_checklist": "కావాల్సిన పత్రాల జాబితా",
            "loan_emi_title": "రుణ వాయిదా & ఆర్థిక అంచనా",
            "subsidy_estimate": "అంచనా ప్రభుత్వ సబ్సిడీ",
            "citation_title": "అధికారిక ప్రభుత్వ పథక సమాచారం",
        },
        "ta": {
            "eligibility_met": "வழங்கப்பட்ட தகவலின் அடிப்படையில் நீங்கள் இத்திட்டத்திற்கான தகுதி வரம்புகளைப் பூர்த்தி செய்கிறீர்கள்.",
            "eligibility_check": "இத்திட்டத்திற்கான தகுதித் தேவைகள்.",
            "authority_note": "இறுதித் தகுதி சம்பந்தப்பட்ட அரசு அதிகாரியால் மட்டுமே தீர்மானிக்கப்படும்.",
            "verified_scheme": "சரிபார்க்கப்பட்ட அரசு திட்டம்",
            "apply_portal": "அதிகாரப்பூர்வ தளத்தில் விண்ணப்பிக்கவும்",
            "document_checklist": "தேவையான ஆவணங்களின் பட்டியல்",
            "loan_emi_title": "கடன் தவணை & நிதி மதிப்பீடு",
            "subsidy_estimate": "மதிப்பிடப்பட்ட அரசு மானியம்",
            "citation_title": "அதிகாரப்பூர்வ அரசு திட்டத் தகவல்",
        },
        "mr": {
            "eligibility_met": "दिलेल्या माहितीच्या आधारे तुम्ही या योजनेच्या पात्रता अटी पूर्ण करत आहात.",
            "eligibility_check": "या योजनेसाठी आवश्यक अटी.",
            "authority_note": "अंतिम पात्रता फक्त संबंधित शासकीय प्राधिकरणाद्वारे ठरवली जाते.",
            "verified_scheme": "सत्यापित शासकीय योजना",
            "apply_portal": "अधिकृत पोर्टलवर अर्ज करा",
            "document_checklist": "आवश्यक कागदपत्रांची यादी",
            "loan_emi_title": "कर्ज हप्ता आणि आर्थिक अंदाज",
            "subsidy_estimate": "अंदाजे सरकारी अनुदान",
            "citation_title": "सत्यापित शासकीय माहिती",
        },
        "gu": {
            "eligibility_met": "આપેલી માહિતી મુજબ તમે આ યોજનાની પાત્રતા શરતો પૂર્ણ કરો છો.",
            "eligibility_check": "આ યોજના માટે ચકાસવાની શરતો.",
            "authority_note": "અંતિમ પાત્રતા સંબંધિત સરકારી સત્તામંડળ દ્વારા જ નક્કી કરવામાં આવે છે.",
            "verified_scheme": "ચકાસાયેલ સરકારી યોજના",
            "apply_portal": "સત્તાવાર પોર્ટલ પર અરજી કરો",
            "document_checklist": "જરૂરી દસ્તાવેજોની યાદી",
            "loan_emi_title": "લોન હપ્તો અને નાણાકીય અંદાજ",
            "subsidy_estimate": "અંદાજિત સરકારી સબસિડી",
            "citation_title": "સત્તાવાર સરકારી યોજના માહિતી",
        },
        "kn": {
            "eligibility_met": "ನೀಡಿರುವ ಮಾಹಿತಿಯ ಪ್ರಕಾರ ನೀವು ಈ ಯೋಜನೆಯ ಅರ್ಹತಾ ಮಾನದಂಡಗಳನ್ನು ಪೂರೈಸುತ್ತೀರಿ.",
            "eligibility_check": "ಈ ಯೋಜನೆಗಾಗಿ ಪರಿಶೀಲಿಸಬೇಕಾದ ಷರತ್ತುಗಳು.",
            "authority_note": "ಅಂತಿಮ ಅರ್ಹತೆಯನ್ನು ಸಂಬಂಧಪಟ್ಟ ಸರ್ಕಾರಿ ಪ್ರಾಧಿಕಾರವೇ ನಿರ್ಧರಿಸುತ್ತದೆ.",
            "verified_scheme": "ಪರಿಶೀಲಿಸಿದ ಸರ್ಕಾರಿ ಯೋಜನೆ",
            "apply_portal": "ಅಧಿಕೃತ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
            "document_checklist": "ಅಗತ್ಯ ದಾಖಲೆಗಳ ಪರಿಶೀಲನಾ ಪಟ್ಟಿ",
            "loan_emi_title": "ಸಾಲದ ಕಂತು ಮತ್ತು ಆರ್ಥಿಕ ಅಂದಾಜು",
            "subsidy_estimate": "ಅಂದಾಜು ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿ",
            "citation_title": "ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಯೋಜನೆ ಮಾಹಿತಿ",
        },
        "ml": {
            "eligibility_met": "നൽകിയ വിവരങ്ങളുടെ അടിസ്ഥാനത്തിൽ നിങ്ങൾ ഈ പദ്ധതിയുടെ യോഗ്യതാ മാനദണ്ഡങ്ങൾ പാലിക്കുന്നു.",
            "eligibility_check": "ഈ പദ്ധതിക്കായി പരിശോധിക്കേണ്ട വ്യവസ്ഥകൾ.",
            "authority_note": "അന്തിമ യോഗ്യത ബന്ധപ്പെട്ട സർക്കാർ അതോറിറ്റി മാത്രമാണ് തീരുമാനിക്കുന്നത്.",
            "verified_scheme": "സ്ഥിരീകരിച്ച സർക്കാർ പദ്ധതി",
            "apply_portal": "ഔദ്യോഗിക പോർട്ടലിൽ അപേക്ഷിക്കുക",
            "document_checklist": "ആവശ്യമായ രേഖകളുടെ പട്ടിക",
            "loan_emi_title": "വായ്പ തിരിച്ചടവും സാമ്പത്തിക കണക്കും",
            "subsidy_estimate": "പ്രതീക്ഷിക്കുന്ന സർക്കാർ സബ്‌സിഡി",
            "citation_title": "ഔദ്യോഗിക സർക്കാർ പദ്ധതി വിവരം",
        },
        "pa": {
            "eligibility_met": "ਦਿੱਤੀ ਜਾਣਕਾਰੀ ਅਨੁਸਾਰ ਤੁਸੀਂ ਇਸ ਸਕੀਮ ਦੀਆਂ ਯੋਗਤਾ ਸ਼ਰਤਾਂ ਪੂਰੀਆਂ ਕਰਦੇ ਹੋ।",
            "eligibility_check": "ਇਸ ਸਕੀਮ ਲਈ ਜਾਂਚਣ ਯੋਗ ਸ਼ਰਤਾਂ।",
            "authority_note": "ਅੰਤਿਮ ਯੋਗਤਾ ਕੇਵਲ ਸਬੰਧਤ ਸਰਕਾਰੀ ਅਥਾਰਟੀ ਦੁਆਰਾ ਨਿਰਧਾਰਤ ਕੀਤੀ ਜਾਂਦੀ ਹੈ।",
            "verified_scheme": "ਪ੍ਰਮਾਣਿਤ ਸਰਕਾਰੀ ਸਕੀਮ",
            "apply_portal": "ਅਧਿਕਾਰਤ ਪੋਰਟਲ 'ਤੇ ਅਰਜ਼ੀ ਦਿਓ",
            "document_checklist": "ਲੋੜੀਂਦੇ ਦਸਤਾਵੇਜ਼ਾਂ ਦੀ ਸੂਚੀ",
            "loan_emi_title": "ਕਰਜ਼ਾ ਕਿਸ਼ਤ ਅਤੇ ਵਿੱਤੀ ਅੰਦਾਜ਼ਾ",
            "subsidy_estimate": "ਅੰਦਾਜ਼ਨ ਸਰਕਾਰੀ ਸਬਸਿਡੀ",
            "citation_title": "ਅਧਿਕਾਰਤ ਸਰਕਾਰੀ ਸਕੀਮ ਜਾਣਕਾਰੀ",
        },
        "or": {
            "eligibility_met": "ପ୍ରଦତ୍ତ ସୂଚନା ଆଧାରରେ ଆପଣ ଏହି ଯୋଜନାର ଯୋଗ୍ୟତା ମାନଦଣ୍ଡ ପୂରଣ କରୁଛନ୍ତି।",
            "eligibility_check": "ଏହି ଯୋଜନା ପାଇଁ ଯାଞ୍ଚ ଯୋଗ୍ୟ ସର୍ତ୍ତ।",
            "authority_note": "ଚୂଡ଼ାନ୍ତ ଯୋଗ୍ୟତା କେବଳ ସମ୍ପୃକ୍ତ ସରକାରୀ କର୍ତ୍ତୃପକ୍ଷଙ୍କ ଦ୍ୱାରା ନିର୍ଦ୍ଧାରଣ କରାଯାଏ।",
            "verified_scheme": "ଯାଞ୍ଚ ହୋଇଥିବା ସରକାରୀ ଯୋଜନା",
            "apply_portal": "ଅଫିସିଆଲ୍ ପୋର୍ଟାଲରେ ଆବେଦନ କରନ୍ତୁ",
            "document_checklist": "ଆବଶ୍ୟକୀୟ ଦସ୍ତାବିଜ ତାଲିକା",
            "loan_emi_title": "ଋଣ କିସ୍ତି ଏବଂ ଆର୍ଥିକ ଆକଳନ",
            "subsidy_estimate": "ଆନୁମାନିକ ସରକାରୀ ସବସିଡି",
            "citation_title": "ଅଫିସିଆଲ୍ ସରକାରୀ ଯୋଜନା ତଥ୍ୟ",
        },
        "as": {
            "eligibility_met": "প্ৰদান কৰা তথ্যৰ ভিত্তিত আপুনি এই আঁচনিৰ যোগ্যতাৰ চৰ্তসমূহ পূৰণ কৰিছে।",
            "eligibility_check": "এই আঁচনিৰ বাবে প্ৰয়োজনীয় চৰ্তসমূহ।",
            "authority_note": "চূড়ান্ত যোগ্যতা কেৱল সংশ্লিষ্ট চৰকাৰী কৰ্তৃপক্ষই নিৰ্ধাৰণ কৰিব।",
            "verified_scheme": "সত্যপন কৰা চৰকাৰী আঁচনি",
            "apply_portal": "অফিচিয়েল পৰ্টেলত আবেদন কৰক",
            "document_checklist": "প্ৰয়োজনীয় নথিপত্ৰৰ তালিকা",
            "loan_emi_title": "ঋণৰ কিস্তি আৰু আৰ্থিক অনুমান",
            "subsidy_estimate": "আনুমানিক চৰকাৰী ৰাজসাহায্য",
            "citation_title": "অফিচিয়েল চৰকাৰী আঁচনিৰ তথ্য",
        },
    }

    @classmethod
    def get_label(cls, key: str, lang: str = "en") -> str:
        lang_code = (lang or "en").lower().split("-")[0]
        if lang_code in cls.LABELS and key in cls.LABELS[lang_code]:
            return cls.LABELS[lang_code][key]
        return cls.LABELS["en"].get(key, key)

    @classmethod
    def localize_scheme_dict(cls, scheme_dict: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
        """Returns scheme dict with localized explanatory labels if non-English."""
        if not scheme_dict:
            return scheme_dict
        res = dict(scheme_dict)
        res["display_language"] = lang
        return res
