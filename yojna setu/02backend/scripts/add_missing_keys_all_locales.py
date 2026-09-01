"""
Script to add the 7 missing keys across all 12 locales.
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")

MISSING_KEYS = {
    "en": {
        "compare": {
            "bankAssisted": "Channel Partner / Bank Assisted",
            "directOnlinePortal": "Direct Online Portal",
            "channelPartner": "Channel Partner / Agency"
        },
        "nav": {
            "publicNav": "Public Navigation"
        },
        "common": {
            "personalized": "Personalized"
        },
        "map": {
            "authorizedForScheme": "Authorized for selected scheme",
            "authPending": "Scheme-specific authorization not confirmed"
        }
    },
    "hi": {
        "compare": {
            "bankAssisted": "चैनल भागीदार / बैंक सहायता",
            "directOnlinePortal": "प्रत्यक्ष ऑनलाइन पोर्टल",
            "channelPartner": "चैनल भागीदार / एजेंसी"
        },
        "nav": {
            "publicNav": "सार्वजनिक नेविगेशन"
        },
        "common": {
            "personalized": "व्यक्तिगत"
        },
        "map": {
            "authorizedForScheme": "चयनित योजना हेतु अधिकृत",
            "authPending": "योजना-विशिष्ट प्राधिकरण की पुष्टि नहीं"
        }
    },
    "bn": {
        "compare": {
            "bankAssisted": "চ্যানেল অংশীদার / ব্যাংক সহায়ক",
            "directOnlinePortal": "সরাসরি অনলাইন পোর্টাল",
            "channelPartner": "চ্যানেল অংশীদার / সংস্থা"
        },
        "nav": {
            "publicNav": "সাধারণ নেভিগেশন"
        },
        "common": {
            "personalized": "ব্যক্তিগতকৃত"
        },
        "map": {
            "authorizedForScheme": "নির্বাচিত প্রকল্পের জন্য অনুমোদিত",
            "authPending": "প্রকল্প-নির্দিষ্ট অনুমোদন নিশ্চিত নয়"
        }
    },
    "mr": {
        "compare": {
            "bankAssisted": "चॅनेल भागीदार / बँक सहाय्य",
            "directOnlinePortal": "थेट ऑनलाइन पोर्टल",
            "channelPartner": "चॅनेल भागीदार / संस्था"
        },
        "nav": {
            "publicNav": "सार्वजनिक नेव्हिगेशन"
        },
        "common": {
            "personalized": "वैयक्तिकृत"
        },
        "map": {
            "authorizedForScheme": "निवडलेल्या योजनेसाठी अधिकृत",
            "authPending": "योजना-विशिष्ट प्राधिकरण निश्चित नाही"
        }
    },
    "ta": {
        "compare": {
            "bankAssisted": "கூட்டாளர் / வங்கி உதவி",
            "directOnlinePortal": "நேரடி ஆன்லைன் போர்டல்",
            "channelPartner": "சேனல் கூட்டாளர் / நிறுவனம்"
        },
        "nav": {
            "publicNav": "பொது வழிசெலுத்தல்"
        },
        "common": {
            "personalized": "தனிப்பயனாக்கப்பட்ட"
        },
        "map": {
            "authorizedForScheme": "தேர்ந்தெடுக்கப்பட்ட திட்டத்திற்கு அங்கீகரிக்கப்பட்டது",
            "authPending": "திட்ட-குறிப்பிட்ட அங்கீகாரம் உறுதிப்படுத்தப்படவில்லை"
        }
    },
    "te": {
        "compare": {
            "bankAssisted": "ఛానల్ భాగస్వామి / బ్యాంక్ సహాయం",
            "directOnlinePortal": "ప్రత్యక్ష ఆన్‌లైన్ పోర్టల్",
            "channelPartner": "ఛానల్ భాగస్వామి / ఏజెన్సీ"
        },
        "nav": {
            "publicNav": "పబ్లిక్ నావిగేషన్"
        },
        "common": {
            "personalized": "వ్యక్తిగతీకరించిన"
        },
        "map": {
            "authorizedForScheme": "ఎంపిక చేసిన పథకానికి అధికారం ఉంది",
            "authPending": "పథక నిర్దిష్ట అనుమతి ధృవీకరించబడలేదు"
        }
    },
    "gu": {
        "compare": {
            "bankAssisted": "ચેનલ પાર્ટનર / બેંક સહાયતા",
            "directOnlinePortal": "સીધું ઓનલાઇન પોર્ટલ",
            "channelPartner": "ચેનલ પાર્ટનર / એજન્સી"
        },
        "nav": {
            "publicNav": "જાહેર નેવિગેશન"
        },
        "common": {
            "personalized": "વ્યક્તિગત"
        },
        "map": {
            "authorizedForScheme": "પસંદ કરેલ યોજના માટે અધિકૃત",
            "authPending": "યોજના-વિશિષ્ટ સત્તા ખાતરી નથી"
        }
    },
    "kn": {
        "compare": {
            "bankAssisted": "ಚಾನೆಲ್ ಪಾಲುದಾರ / ಬ್ಯಾಂಕ್ ನೆರವು",
            "directOnlinePortal": "ನೇರ ಆನ್‌ಲೈನ್ ಪೋರ್ಟಲ್",
            "channelPartner": "ಚಾನೆಲ್ ಪಾಲುದಾರ / ಸಂಸ್ಥೆ"
        },
        "nav": {
            "publicNav": "ಸಾರ್ವಜನಿಕ ನ್ಯಾವಿಗೇಷನ್"
        },
        "common": {
            "personalized": "ವೈಯಕ್ತೀಕರಿಸಿದ"
        },
        "map": {
            "authorizedForScheme": "ಆಯ್ಕೆಮಾಡಿದ ಯೋಜನೆಗೆ ಅಧಿಕೃತ",
            "authPending": "ಯೋಜನೆ-ನಿರ್ದಿಷ್ಟ ದೃಢೀಕರಣವಾಗಿಲ್ಲ"
        }
    },
    "ml": {
        "compare": {
            "bankAssisted": "ചാനൽ പങ്കാളി / ബാങ്ക് സഹായം",
            "directOnlinePortal": "നേരിട്ടുള്ള ഓൺലൈൻ പോർട്ടൽ",
            "channelPartner": "ചാനൽ പങ്കാളി / ഏജൻസി"
        },
        "nav": {
            "publicNav": "പൊതു നാവിഗേഷൻ"
        },
        "common": {
            "personalized": "വ്യക്തിഗതമാക്കിയത്"
        },
        "map": {
            "authorizedForScheme": "തിരഞ്ഞെടുത്ത പദ്ധതിക്ക് അംഗീകാരം",
            "authPending": "പദ്ധതി അനുമതി സ്ഥിരീകരിച്ചിട്ടില്ല"
        }
    },
    "pa": {
        "compare": {
            "bankAssisted": "ਚੈਨਲ ਸਾਥੀ / ਬੈਂਕ ਸਹਾਇਤਾ",
            "directOnlinePortal": "ਸਿੱਧਾ ਆਨਲਾਈਨ ਪੋਰਟਲ",
            "channelPartner": "ਚੈਨਲ ਸਾਥੀ / ਏਜੰਸੀ"
        },
        "nav": {
            "publicNav": "ਜਨਤਕ ਨੈਵੀਗੇਸ਼ਨ"
        },
        "common": {
            "personalized": "ਨਿੱਜੀ ਬਣਾਇਆ"
        },
        "map": {
            "authorizedForScheme": "ਚੁਣੀ ਗਈ ਸਕੀਮ ਲਈ ਅਧਿਕਾਰਤ",
            "authPending": "ਸਕੀਮ-ਵਿਸ਼ੇਸ਼ ਅਧਿਕਾਰ ਦੀ ਪੁਸ਼ਟੀ ਨਹੀਂ"
        }
    },
    "or": {
        "compare": {
            "bankAssisted": "ଚ୍ୟାନେଲ ଅଂଶୀଦାର / ବ୍ୟାଙ୍କ ସହାୟତା",
            "directOnlinePortal": "ସିଧାସଳଖ ଅନଲାଇନ୍ ପୋର୍ଟାଲ୍",
            "channelPartner": "ଚ୍ୟାନେଲ ଅଂଶୀଦାର / ସଂସ୍ଥା"
        },
        "nav": {
            "publicNav": "ସାର୍ବଜନୀନ ନାଭିଗେସନ୍"
        },
        "common": {
            "personalized": "ବ୍ୟକ୍ତିଗତ"
        },
        "map": {
            "authorizedForScheme": "ଚୟନିତ ଯୋଜନା ପାଇଁ ଅଧିକୃତ",
            "authPending": "ଯୋଜନା-ନିର୍ଦ୍ଦିଷ୍ଟ ପ୍ରାଧିକରଣ ନିଶ୍ଚିତ ନୁହେଁ"
        }
    },
    "as": {
        "compare": {
            "bankAssisted": "চেনেল অংশীদাৰ / বেংক সহায়ক",
            "directOnlinePortal": "পোনপটীয়া অনলাইন পৰ্টেল",
            "channelPartner": "চেনেল অংশীদাৰ / সংস্থা"
        },
        "nav": {
            "publicNav": "ৰাজহুৱা নেভিগেচন"
        },
        "common": {
            "personalized": "ব্যক্তিগতকৃত"
        },
        "map": {
            "authorizedForScheme": "নিৰ্বাচিত আঁচনিৰ বাবে কৰ্তৃত্বপ্ৰাপ্ত",
            "authPending": "আঁচনি-নিৰ্দিষ্ট প্ৰাধিকাৰ নিশ্চিত নহয়"
        }
    }
}

def sync():
    langs = ["en", "hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]
    for lang in langs:
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.exists(file_path):
            print(f"Skipping {file_path}")
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        lang_data = MISSING_KEYS.get(lang, MISSING_KEYS["en"])
        for section, keys in lang_data.items():
            if section not in data:
                data[section] = {}
            for k, v in keys.items():
                data[section][k] = v

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Synced missing keys for {lang}")

if __name__ == "__main__":
    sync()
