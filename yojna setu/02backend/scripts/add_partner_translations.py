"""
Adds comprehensive, translated keys for Channel Partner categories, trust badges,
contact actions, and 'No Partner Found' guidance to all 12 locale JSON files.
Also ensures 'schemes.viewDetails' is present in all 12 languages.
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")

TRANSLATIONS = {
    "en": {
        "partnerLocator": {
            "categoryAll": "All Partners",
            "categoryAuthorized": "Authorized Scheme Partners",
            "categoryAssistance": "Government Assistance Centres",
            "categoryTraining": "Training & Handholding",
            "categoryFinancial": "Nearby Financial Points",
            "categoryVerified": "Officially Verified",
            "badgeAuthorized": "OFFICIALLY VERIFIED SCHEME PARTNER",
            "badgeAssistance": "GOVERNMENT ASSISTANCE CENTRE",
            "badgeFinancial": "FINANCIAL INSTITUTION (GENERAL ROUTE)",
            "badgeTraining": "TRAINING & EDP CENTRE",
            "noPartnerTitle": "No verified authorized partner was found for this scheme in this area.",
            "noPartnerDesc": "Submissions for this scheme are handled directly via the official government portal or statutory district office.",
            "phone": "Phone",
            "email": "Email",
            "website": "Website",
            "officialSource": "Official Source",
            "lastVerified": "Last verified",
            "services": "Services",
            "getDirections": "Get Directions",
            "schemesSupported": "Schemes Supported",
            "call": "Call"
        },
        "schemes": {
            "viewDetails": "View Details"
        }
    },
    "hi": {
        "partnerLocator": {
            "categoryAll": "सभी भागीदार",
            "categoryAuthorized": "अधिकृत योजना भागीदार",
            "categoryAssistance": "सरकारी सहायता केंद्र",
            "categoryTraining": "प्रशिक्षण एवं मार्गदर्शन केंद्र",
            "categoryFinancial": "निकटवर्ती वित्तीय संस्थान",
            "categoryVerified": "आधिकारिक रूप से सत्यापित",
            "badgeAuthorized": "आधिकारिक रूप से सत्यापित योजना भागीदार",
            "badgeAssistance": "सरकारी सहायता केंद्र",
            "badgeFinancial": "वित्तीय संस्थान (सामान्य मार्ग)",
            "badgeTraining": "प्रशिक्षण एवं उद्यमिता विकास केंद्र",
            "noPartnerTitle": "इस क्षेत्र में इस योजना के लिए कोई सत्यापित अधिकृत भागीदार नहीं मिला।",
            "noPartnerDesc": "इस योजना के आवेदन आधिकारिक सरकारी पोर्टल या जिला कार्यालय के माध्यम से सीधे किए जाते हैं।",
            "phone": "फ़ोन",
            "email": "ईमेल",
            "website": "वेबसाइट",
            "officialSource": "आधिकारिक स्रोत",
            "lastVerified": "अंतिम सत्यापन",
            "services": "सेवाएं",
            "getDirections": "दिशा-निर्देश प्राप्त करें",
            "schemesSupported": "समर्थित योजनाएं",
            "call": "कॉल करें"
        },
        "schemes": {
            "viewDetails": "विवरण देखें"
        }
    },
    "bn": {
        "partnerLocator": {
            "categoryAll": "সকল অংশীদার",
            "categoryAuthorized": "অনুমোদিত প্রকল্প অংশীদার",
            "categoryAssistance": "সরকারি সহায়তা কেন্দ্র",
            "categoryTraining": "প্রশিক্ষণ ও সহায়তা কেন্দ্র",
            "categoryFinancial": "নিকটবর্তী আর্থিক প্রতিষ্ঠান",
            "categoryVerified": "সরকারিভাবে যাচাইকৃত",
            "badgeAuthorized": "সরকারিভাবে অনুমোদিত প্রকল্প অংশীদার",
            "badgeAssistance": "সরকারি সহায়তা কেন্দ্র",
            "badgeFinancial": "আর্থিক প্রতিষ্ঠান (সাধারণ রুট)",
            "badgeTraining": "প্রশিক্ষণ ও উদ্যোক্তা উন্নয়ন কেন্দ্র",
            "noPartnerTitle": "এই এলাকায় এই প্রকল্পের জন্য কোনো যাচাইকৃত অনুমোদিত অংশীদার পাওয়া যায়নি।",
            "noPartnerDesc": "এই প্রকল্পের আবেদন সরাসরি অফিসিয়াল সরকারি পোর্টাল বা জেলা অফিসের মাধ্যমে জমা দেওয়া হয়।",
            "phone": "ফোন",
            "email": "ইমেল",
            "website": "ওয়েবসাইট",
            "officialSource": "অফিসিয়াল উৎস",
            "lastVerified": "সর্বশেষ যাচাই",
            "services": "সেবাসমূহ",
            "getDirections": "পথনির্দেশ পান",
            "schemesSupported": "সমর্থিত প্রকল্পসমূহ",
            "call": "কল করুন"
        },
        "schemes": {
            "viewDetails": "বিস্তারিত দেখুন"
        }
    },
    "mr": {
        "partnerLocator": {
            "categoryAll": "सर्व भागीदार",
            "categoryAuthorized": "अधिकृत योजना भागीदार",
            "categoryAssistance": "शासकीय सहाय्य केंद्र",
            "categoryTraining": "प्रशिक्षण व मार्गदर्शन केंद्र",
            "categoryFinancial": "जवळपासच्या वित्तीय संस्था",
            "categoryVerified": "अधिकृतपणे सत्यापित",
            "badgeAuthorized": "अधिकृतपणे सत्यापित योजना भागीदार",
            "badgeAssistance": "शासकीय सहाय्य केंद्र",
            "badgeFinancial": "वित्तीय संस्था (सामान्य मार्ग)",
            "badgeTraining": "प्रशिक्षण व उद्योजकता विकास केंद्र",
            "noPartnerTitle": "या भागात या योजनेसाठी कोणताही सत्यापित अधिकृत भागीदार आढळला नाही.",
            "noPartnerDesc": "या योजनेचे अर्ज थेट अधिकृत शासकीय पोर्टल किंवा जिल्हा कार्यालयामार्फत केले जातात.",
            "phone": "फोन",
            "email": "ईमेल",
            "website": "वेबसाइट",
            "officialSource": "अधिकृत स्रोत",
            "lastVerified": "शेवटचे सत्यापन",
            "services": "सेवा",
            "getDirections": "दिशा मिळवा",
            "schemesSupported": "समर्थित योजना",
            "call": "कॉल करा"
        },
        "schemes": {
            "viewDetails": "तपशील पहा"
        }
    },
    "ta": {
        "partnerLocator": {
            "categoryAll": "அனைத்து கூட்டாளர்கள்",
            "categoryAuthorized": "அங்கீகரிக்கப்பட்ட திட்ட கூட்டாளர்கள்",
            "categoryAssistance": "அரசு உதவி மையங்கள்",
            "categoryTraining": "பயிற்சி மற்றும் வழிகாட்டுதல் மையங்கள்",
            "categoryFinancial": "அருகிலுள்ள நிதி நிறுவனங்கள்",
            "categoryVerified": "அதிகாரப்பூர்வமாக சரிபார்க்கப்பட்டது",
            "badgeAuthorized": "அதிகாரப்பூர்வமாக சரிபார்க்கப்பட்ட கூட்டாளர்",
            "badgeAssistance": "அரசு உதவி மையம்",
            "badgeFinancial": "நிதி நிறுவனம் (பொது வழி)",
            "badgeTraining": "பயிற்சி மற்றும் தொழில்முனைவோர் மையம்",
            "noPartnerTitle": "இப்பகுதியில் இத்திட்டத்திற்கான சரிபார்க்கப்பட்ட கூட்டாளர் இல்லை.",
            "noPartnerDesc": "இத்திட்டத்திற்கான விண்ணப்பங்கள் அதிகாரப்பூர்வ அரசு போர்ட்டல் மூலம் நேரடியாக சமர்ப்பிக்கப்படுகின்றன.",
            "phone": "தொலைபேசி",
            "email": "மின்னஞ்சல்",
            "website": "இணையதளம்",
            "officialSource": "அதிகாரப்பூர்வ ஆதாரம்",
            "lastVerified": "கடைசியாக சரிபார்க்கப்பட்டது",
            "services": "சேவைகள்",
            "getDirections": "திசைகளைப் பெறுக",
            "schemesSupported": "ஆதரிக்கப்படும் திட்டங்கள்",
            "call": "அழைக்க"
        },
        "schemes": {
            "viewDetails": "விவரங்களைக் காண்க"
        }
    },
    "te": {
        "partnerLocator": {
            "categoryAll": "అన్ని భాగస్వాములు",
            "categoryAuthorized": "అధీకృత పథకం భాగస్వాములు",
            "categoryAssistance": "ప్రభుత్వ సహాయ కేంద్రాలు",
            "categoryTraining": "శిక్షణ & మార్గదర్శక కేంద్రాలు",
            "categoryFinancial": "సమీప ఆర్థిక సంస్థలు",
            "categoryVerified": "అధికారికంగా ధృవీకరించబడింది",
            "badgeAuthorized": "అధికారికంగా ధృవీకరించబడిన పథక భాగస్వామి",
            "badgeAssistance": "ప్రభుత్వ సహాయ కేంద్రం",
            "badgeFinancial": "ఆర్థిక సంస్థ (సాధారణ మార్గం)",
            "badgeTraining": "శిక్షణ & వ్యవస్థాపకత అభివృద్ధి కేంద్రం",
            "noPartnerTitle": "ఈ ప్రాంతంలో ఈ పథకానికి ధృవీకరించబడిన భాగస్వాములు లేరు.",
            "noPartnerDesc": "ఈ పథకానికి దరఖాస్తులు అధికారిక ప్రభుత్వ పోర్టల్ ద్వారా నేరుగా నిర్వహించబడతాయి.",
            "phone": "ఫోన్",
            "email": "ఈమెయిల్",
            "website": "వెబ్‌సైట్",
            "officialSource": "అధికారిక మూలం",
            "lastVerified": "చివరిగా ధృవీకరించబడింది",
            "services": "సేవలు",
            "getDirections": "మార్గం పొందండి",
            "schemesSupported": "మద్దతు ఇచ్చే పథకాలు",
            "call": "కాల్ చేయండి"
        },
        "schemes": {
            "viewDetails": "వివరాలు చూడండి"
        }
    },
    "gu": {
        "partnerLocator": {
            "categoryAll": "બધા ભાગીદારો",
            "categoryAuthorized": "અધિકૃત યોજના ભાગીદારો",
            "categoryAssistance": "સરકારી સહાયતા કેન્દ્રો",
            "categoryTraining": "તાલીમ અને માર્ગદર્શન કેન્દ્રો",
            "categoryFinancial": "નજીકની નાણાકીય સંસ્થાઓ",
            "categoryVerified": "સત્તાવાર રીતે ચકાસાયેલ",
            "badgeAuthorized": "સત્તાવાર રીતે ચકાસાયેલ યોજના ભાગીદાર",
            "badgeAssistance": "સરકારી સહાયતા કેન્દ્ર",
            "badgeFinancial": "નાણાકીય સંસ્થા (સામાન્ય માર્ગ)",
            "badgeTraining": "તાલીમ અને સાહસિકતા કેન્દ્ર",
            "noPartnerTitle": "આ વિસ્તારમાં આ યોજના માટે કોઈ ચકાસાયેલ ભાગીદાર મળ્યા નથી.",
            "noPartnerDesc": "આ યોજના માટે અરજીઓ સત્તાવાર સરકારી પોર્ટલ દ્વારા સીધી કરવામાં આવે છે.",
            "phone": "ફોન",
            "email": "ઈમેલ",
            "website": "વેબસાઇટ",
            "officialSource": "સત્તાવાર સ્ત્રોત",
            "lastVerified": "છેલ્લી ચકાસણી",
            "services": "સેવાઓ",
            "getDirections": "દિશાઓ મેળવો",
            "schemesSupported": "સમર્થિત યોજનાઓ",
            "call": "કૉલ કરો"
        },
        "schemes": {
            "viewDetails": "વિગતો જુઓ"
        }
    },
    "kn": {
        "partnerLocator": {
            "categoryAll": "ಎಲ್ಲಾ ಪಾಲುದಾರರು",
            "categoryAuthorized": "ಅಧಿಕೃತ ಯೋಜನಾ ಪಾಲುದಾರರು",
            "categoryAssistance": "ಸರ್ಕಾರಿ ಸಹಾಯ ಕೇಂದ್ರಗಳು",
            "categoryTraining": "ತರಬೇತಿ ಮತ್ತು ಮಾರ್ಗದರ್ಶನ ಕೇಂದ್ರಗಳು",
            "categoryFinancial": "ಹತ್ತಿರದ ಹಣಕಾಸು ಸಂಸ್ಥೆಗಳು",
            "categoryVerified": "ಅಧಿಕೃತವಾಗಿ ಪರಿಶೀಲಿಸಲಾಗಿದೆ",
            "badgeAuthorized": "ಅಧಿಕೃತವಾಗಿ ಪರಿಶೀಲಿಸಲಾದ ಪಾಲುದಾರ",
            "badgeAssistance": "ಸರ್ಕಾರಿ ಸಹಾಯ ಕೇಂದ್ರ",
            "badgeFinancial": "ಹಣಕಾಸು ಸಂಸ್ಥೆ (ಸಾಮಾನ್ಯ ಮಾರ್ಗ)",
            "badgeTraining": "ತರಬೇತಿ ಮತ್ತು ಉದ್ಯಮಶೀಲತೆ ಕೇಂದ್ರ",
            "noPartnerTitle": "ಈ ಪ್ರದೇಶದಲ್ಲಿ ಈ ಯೋಜನೆಗೆ ಯಾವುದೇ ಪಾಲುದಾರರು ಕಂಡುಬಂದಿಲ್ಲ.",
            "noPartnerDesc": "ಈ ಯೋಜನೆಗೆ ಅರ್ಜಿಗಳನ್ನು ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಪೋರ್ಟಲ್ ಮೂಲಕ ನೇರವಾಗಿ ಸಲ್ಲಿಸಲಾಗುತ್ತದೆ.",
            "phone": "ದೂರವಾಣಿ",
            "email": "ಇಮೇಲ್",
            "website": "ವೆಬ್‌ಸೈಟ್",
            "officialSource": "ಅಧಿಕೃತ ಮೂಲ",
            "lastVerified": "ಕೊನೆಯ ಪರಿಶೀಲನೆ",
            "services": "ಸೇವೆಗಳು",
            "getDirections": "ದಿಕ್ಕುಗಳನ್ನು ಪಡೆಯಿರಿ",
            "schemesSupported": "ಬೆಂಬಲಿತ ಯೋಜನೆಗಳು",
            "call": "ಕರೆ ಮಾಡಿ"
        },
        "schemes": {
            "viewDetails": "ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ"
        }
    },
    "ml": {
        "partnerLocator": {
            "categoryAll": "എല്ലാ പങ്കാളികളും",
            "categoryAuthorized": "അംഗീകൃത പദ്ധതി പങ്കാളികൾ",
            "categoryAssistance": "സർക്കാർ സഹായ കേന്ദ്രങ്ങൾ",
            "categoryTraining": "പരിശീലന കേന്ദ്രങ്ങൾ",
            "categoryFinancial": "സമീപസ്ഥ ധനകാര്യ സ്ഥാപനങ്ങൾ",
            "categoryVerified": "ഔദ്യോഗികമായി പരിശോധിച്ചു",
            "badgeAuthorized": "ഔദ്യോഗികമായി പരിശോധിച്ച പദ്ധതി പങ്കാളി",
            "badgeAssistance": "സർക്കാർ സഹായ കേന്ദ്രം",
            "badgeFinancial": "ധനകാര്യ സ്ഥാപനം (പൊതു മാർഗ്ഗം)",
            "badgeTraining": "പരിശീലന കേന്ദ്രം",
            "noPartnerTitle": "ഈ പ്രദേശത്ത് ഈ പദ്ധതിക്കായി അംഗീകൃത പങ്കാളികളെ കണ്ടെത്തിയില്ല.",
            "noPartnerDesc": "ഈ പദ്ധതിയിലേക്കുള്ള അപേക്ഷകൾ ഔദ്യോഗിക സർക്കാർ പോർട്ടൽ വഴി നേരിട്ട് നൽകാം.",
            "phone": "ഫോൺ",
            "email": "ഇമെയിൽ",
            "website": "വെബ്സൈറ്റ്",
            "officialSource": "ഔദ്യോഗിക ഉറവിടം",
            "lastVerified": "അവസാനം പരിശോധിച്ചത്",
            "services": "സേവനങ്ങൾ",
            "getDirections": "ദിശ കണ്ടെത്തുക",
            "schemesSupported": "പിന്തുണയ്ക്കുന്ന പദ്ധതികൾ",
            "call": "വിളിക്കുക"
        },
        "schemes": {
            "viewDetails": "വിശദാംശങ്ങൾ കാണുക"
        }
    },
    "pa": {
        "partnerLocator": {
            "categoryAll": "ਸਾਰੇ ਭਾਈਵਾਲ",
            "categoryAuthorized": "ਅਧਿਕਾਰਤ ਸਕੀਮ ਭਾਈਵਾਲ",
            "categoryAssistance": "ਸਰਕਾਰੀ ਸਹਾਇਤਾ ਕੇਂਦਰ",
            "categoryTraining": "ਸਿਖਲਾਈ ਅਤੇ ਮਾਰਗਦਰਸ਼ਨ ਕੇਂਦਰ",
            "categoryFinancial": "ਨੇੜਲੀਆਂ ਵਿੱਤੀ ਸੰਸਥਾਵਾਂ",
            "categoryVerified": "ਸਰਕਾਰੀ ਤੌਰ 'ਤੇ ਤਸਦੀਕਸ਼ੁਦਾ",
            "badgeAuthorized": "ਸਰਕਾਰੀ ਤੌਰ 'ਤੇ ਤਸਦੀਕਸ਼ੁਦਾ ਸਕੀਮ ਭਾਈਵਾਲ",
            "badgeAssistance": "ਸਰਕਾਰੀ ਸਹਾਇਤਾ ਕੇਂਦਰ",
            "badgeFinancial": "ਵਿੱਤੀ ਸੰਸਥਾ (ਆਮ ਰਸਤਾ)",
            "badgeTraining": "ਸਿਖਲਾਈ ਅਤੇ ਉੱਦਮਤਾ ਕੇਂਦਰ",
            "noPartnerTitle": "ਇਸ ਖੇਤਰ ਵਿੱਚ ਇਸ ਸਕੀਮ ਲਈ ਕੋਈ ਤਸਦੀਕਸ਼ੁਦਾ ਭਾਈਵਾਲ ਨਹੀਂ ਮਿਲਿਆ।",
            "noPartnerDesc": "ਇਸ ਸਕੀਮ ਦੀਆਂ ਅਰਜ਼ੀਆਂ ਸਿੱਧੇ ਸਰਕਾਰੀ ਪੋਰਟਲ ਰਾਹੀਂ ਜਮ੍ਹਾਂ ਕੀਤੀਆਂ ਜਾਂਦੀਆਂ ਹਨ।",
            "phone": "ਫ਼ੋਨ",
            "email": "ਈਮੇਲ",
            "website": "ਵੈੱਬਸਾਈਟ",
            "officialSource": "ਅਧਿਕਾਰਤ ਸਰੋਤ",
            "lastVerified": "ਆਖਰੀ ਤਸਦੀਕ",
            "services": "ਸੇਵਾਵਾਂ",
            "getDirections": "ਦਿਸ਼ਾ ਪ੍ਰਾਪਤ ਕਰੋ",
            "schemesSupported": "ਸਮਰਥਿਤ ਸਕੀਮਾਂ",
            "call": "ਕਾਲ ਕਰੋ"
        },
        "schemes": {
            "viewDetails": "ਵੇਰਵੇ ਦੇਖੋ"
        }
    },
    "or": {
        "partnerLocator": {
            "categoryAll": "ସମସ୍ତ ଅଂଶୀଦାର",
            "categoryAuthorized": "ଅନୁମୋଦିତ ଯୋଜନା ଅଂଶୀଦାର",
            "categoryAssistance": "ସରକାରୀ ସହାୟତା କେନ୍ଦ୍ର",
            "categoryTraining": "ତାଲିମ ଓ ମାର୍ଗଦର୍ଶନ କେନ୍ଦ୍ର",
            "categoryFinancial": "ନିକଟସ୍ଥ ଆର୍ଥିକ ଅନୁଷ୍ଠାନ",
            "categoryVerified": "ଅଧିକାରିକ ଭାବରେ ଯାଞ୍ଚ ହୋଇଛି",
            "badgeAuthorized": "ଅଧିକାରିକ ଭାବରେ ଯାଞ୍ଚ ହୋଇଥିବା ଯୋଜନା ଅଂଶୀଦାର",
            "badgeAssistance": "ସରକାରୀ ସହାୟତା କେନ୍ଦ୍ର",
            "badgeFinancial": "ଆର୍ଥିକ ଅନୁଷ୍ଠାନ (ସାଧାରଣ ଉପାୟ)",
            "badgeTraining": "ତାଲିମ ଓ ଉଦ୍ୟୋଗ ବିକାଶ କେନ୍ଦ୍ର",
            "noPartnerTitle": "ଏହି ଅଞ୍ଚଳରେ ଏହି ଯୋଜନା ପାଇଁ କୌଣସି ଯାଞ୍ଚ ହୋଇଥିବା ଅଂଶୀଦାର ମିଳିଲା ନାହିଁ।",
            "noPartnerDesc": "ଏହି ଯୋଜନା ପାଇଁ ଆବେଦନ ସିଧାସଳଖ ସରକାରୀ ପୋର୍ଟାଲ ମାଧ୍ୟମରେ କରାଯାଏ।",
            "phone": "ଫୋନ୍",
            "email": "ଇମେଲ୍",
            "website": "ୱେବସାଇଟ୍",
            "officialSource": "ଅଧିକାରିକ ଉତ୍ସ",
            "lastVerified": "ଶେଷ ଯାଞ୍ଚ",
            "services": "ସେବାଗୁଡ଼ିକ",
            "getDirections": "ଦିଗ ନିର୍ଦ୍ଦେଶ ପାଆନ୍ତୁ",
            "schemesSupported": "ସମର୍ଥିତ ଯୋଜନାଗୁଡ଼ିକ",
            "call": "କଲ୍ କରନ୍ତୁ"
        },
        "schemes": {
            "viewDetails": "ବିବରଣୀ ଦେଖନ୍ତୁ"
        }
    },
    "as": {
        "partnerLocator": {
            "categoryAll": "সকলো অংশীদাৰ",
            "categoryAuthorized": "অনুমোদিত আঁচনি অংশীদাৰ",
            "categoryAssistance": "চৰকাৰী সাহায্য কেন্দ্ৰ",
            "categoryTraining": "প্ৰশিক্ষণ আৰু মাৰ্গদৰ্শন কেন্দ্ৰ",
            "categoryFinancial": "নিকটৱৰ্তী বিত্তীয় প্ৰতিষ্ঠান",
            "categoryVerified": "চৰকাৰীভাৱে পৰীক্ষিত",
            "badgeAuthorized": "চৰকাৰীভাৱে অনুমোদিত আঁচনি অংশীদাৰ",
            "badgeAssistance": "চৰকাৰী সাহায্য কেন্দ্ৰ",
            "badgeFinancial": "বিত্তীয় প্ৰতিষ্ঠান (সাধাৰণ পথ)",
            "badgeTraining": "প্ৰশিক্ষণ আৰু উদ্যোগ বিকাশ কেন্দ্ৰ",
            "noPartnerTitle": "এই অঞ্চলত এই আঁচনিৰ বাবে কোনো অনুমোদিত অংশীদাৰ পোৱা নগ'ল।",
            "noPartnerDesc": "এই আঁচনিৰ আবেদন পোনপটীয়াকৈ চৰকাৰী পৰ্টেলৰ জৰিয়তে দাখিল কৰা হয়।",
            "phone": "ফোন",
            "email": "ইমেইল",
            "website": "ৱেবছাইট",
            "officialSource": "চৰকাৰী উৎস",
            "lastVerified": "অন্তিম পৰীক্ষা",
            "services": "সেৱাসমূহ",
            "getDirections": "দিশ নিৰ্দেশনা প্ৰাপ্ত কৰক",
            "schemesSupported": "সমৰ্থিত আঁচনিসমূহ",
            "call": "কল কৰক"
        },
        "schemes": {
            "viewDetails": "বিৱৰণ চাওক"
        }
    }
}

def sync_translations():
    langs = ["en", "hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]
    for lang in langs:
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.exists(file_path):
            print(f"Skipping {file_path} (not found)")
            continue
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        lang_trans = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

        for ns, keys in lang_trans.items():
            if ns not in data:
                data[ns] = {}
            for k, v in keys.items():
                data[ns][k] = v

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Updated translations for {lang} in {file_path}")

if __name__ == "__main__":
    sync_translations()
