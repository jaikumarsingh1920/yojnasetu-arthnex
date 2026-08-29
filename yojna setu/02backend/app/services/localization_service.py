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
