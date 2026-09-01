"""
Script to translate auth, route, stage, and common UI namespaces across all 11 non-English languages.
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")

SHARED_DATA = {
    "hi": {
        "profile": {
            "viewRecommendations": "स्मार्ट सिफारिशें देखें →"
        },
        "route": {
            "partner": "अधिकृत चैनल भागीदार सहायता (बैंक / एससीए)",
            "portal": "प्रत्यक्ष ऑनलाइन सरकारी पोर्टल"
        },
        "stage": {
            "existing": "मौजूदा व्यवसाय विस्तार",
            "new": "नई इकाई / ग्रीनफील्ड स्टार्टअप"
        }
    },
    "bn": {
        "profile": {
            "viewRecommendations": "প্রকল্প সুপারিশ দেখুন →"
        },
        "route": {
            "partner": "অনুমোদিত চ্যানেল অংশীদার সহায়তা (ব্যাংক / সংস্থা)",
            "portal": "সরাসরি সরকারি অনলাইন পোর্টাল"
        },
        "stage": {
            "existing": "বিদ্যমান ব্যবসার সম্প্রসারণ",
            "new": "নতুন ইউনিট / স্টার্টআপ"
        },
        "auth": {
            "loginTitle": "যোজনাসেতুতে লগইন করুন",
            "loginSubtitle": "প্রকল্প অনুসন্ধান, যোগ্যতা মিলানো এবং সংরক্ষিত প্রকল্প দেখুন",
            "registerTitle": "যোজনাসেতু অ্যাকাউন্ট তৈরি করুন",
            "registerSubtitle": "প্রকল্প সংরক্ষণ এবং ব্যক্তিগতকৃত বিজ্ঞপ্তি পেতে নিবন্ধন করুন",
            "fullName": "সম্পূর্ণ নাম",
            "email": "ইমেল ঠিকানা",
            "emailOrPhone": "ইমেল বা মোবাইল নম্বর",
            "password": "পাসওয়ার্ড",
            "confirmPassword": "পাসওয়ার্ড নিশ্চিত করুন",
            "phone": "মোবাইল নম্বর",
            "role": "অ্যাকাউন্টের ধরন",
            "citizen": "নাগরিক / উদ্যোক্তা",
            "partner": "চ্যানেল অংশীদার কর্মকর্তা",
            "signInBtn": "সাইন ইন করুন",
            "loginNow": "এখনই লগইন করুন",
            "registerBtn": "অ্যাকাউন্ট তৈরি করুন",
            "forgotPassword": "পাসওয়ার্ড ভুলে গেছেন?",
            "hasAccount": "ইতিমধ্যে নিবন্ধিত?",
            "noAccount": "অ্যাকাউন্ট নেই?",
            "logout": "লগআউট",
            "signInWithGoogle": "গুগল দিয়ে সাইন ইন করুন",
            "continueWithGoogle": "গুগল দিয়ে চালিয়ে যান"
        }
    },
    "mr": {
        "profile": {
            "viewRecommendations": "स्मार्ट शिफारसी पहा →"
        },
        "route": {
            "partner": "अधिकृत चॅनेल भागीदार सहाय्य (बँक / संस्था)",
            "portal": "थेट ऑनलाइन सरकारी पोर्टल"
        },
        "stage": {
            "existing": "विद्यमान व्यवसाय विस्तार",
            "new": "नवीन युनिट / स्टार्टअप"
        },
        "auth": {
            "loginTitle": "योजनासेतू मध्ये लॉगिन करा",
            "loginSubtitle": "योजना शोध आणि जतन केलेल्या योजनांमध्ये प्रवेश करा",
            "registerTitle": "योजनासेतू खाते तयार करा",
            "registerSubtitle": "योजना जतन करण्यासाठी आणि सूचना मिळवण्यासाठी नोंदणी करा",
            "fullName": "पूर्ण नाव",
            "email": "ईमेल पत्ता",
            "emailOrPhone": "ईमेल किंवा मोबाइल नंबर",
            "password": "पासवर्ड",
            "confirmPassword": "पासवर्ड पुष्टी करा",
            "phone": "मोबाइल नंबर",
            "role": "खात्याचा प्रकार",
            "citizen": "नागरिक / उद्योजक",
            "partner": "चॅनेल भागीदार अधिकारी",
            "signInBtn": "साइन इन करा",
            "loginNow": "आत्ताच लॉगिन करा",
            "registerBtn": "खाते तयार करा",
            "forgotPassword": "पासवर्ड विसरलात?",
            "hasAccount": "आधीच खाते आहे?",
            "noAccount": "खाते नाही?",
            "logout": "लॉगआउट",
            "signInWithGoogle": "गुगल द्वारे साइन इन करा",
            "continueWithGoogle": "गुगल सह पुढे जा"
        }
    },
    "ta": {
        "profile": {
            "viewRecommendations": "பரிந்துரைகளைக் காண்க →"
        },
        "route": {
            "partner": "அங்கீகரிக்கப்பட்ட கூட்டாளர் உதவி (வங்கி / முகமை)",
            "portal": "நேரடி அரசு இணையதளம்"
        },
        "stage": {
            "existing": "தற்போதுள்ள வணிக விரிவாக்கம்",
            "new": "புதிய தொழில் / தொடக்க நிறுவனம்"
        },
        "auth": {
            "loginTitle": "யோஜனாசேதுவில் உள்நுழைக",
            "loginSubtitle": "திட்டங்களைக் கண்டறிந்து சேமிக்கப்பட்டவற்றை அணுகவும்",
            "registerTitle": "யோஜனாசேது கணக்கை உருவாக்கவும்",
            "registerSubtitle": "தனிப்பயனாக்கப்பட்ட அறிவிப்புகளைப் பெற பதிவு செய்யவும்",
            "fullName": "முழுப் பெயர்",
            "email": "மின்னஞ்சல் முகவரி",
            "emailOrPhone": "மின்னஞ்சல் அல்லது தொலைபேசி எண்",
            "password": "கடவுச்சொல்",
            "confirmPassword": "கடவுச்சொல்லை உறுதிப்படுத்தவும்",
            "phone": "தொலைபேசி எண்",
            "role": "கணக்கு வகை",
            "citizen": "குடிமகன் / தொழில்முனைவோர்",
            "partner": "கூட்டாளர் அதிகாரி",
            "signInBtn": "உள்நுழைக",
            "loginNow": "இப்போது உள்நுழைக",
            "registerBtn": "கணக்கை உருவாக்கவும்",
            "forgotPassword": "கடவுச்சொல் மறந்துவிட்டதா?",
            "hasAccount": "ஏற்கனவே கணக்கு உள்ளதா?",
            "noAccount": "கணக்கு இல்லையா?",
            "logout": "வெளியேறுக",
            "signInWithGoogle": "கூகிள் மூலம் உள்நுழைக",
            "continueWithGoogle": "கூகிள் மூலம் தொடரவும்"
        }
    },
    "te": {
        "profile": {
            "viewRecommendations": "సిఫార్సులను చూడండి →"
        },
        "route": {
            "partner": "అధికారిక భాగస్వామి సహాయం (బ్యాంక్ / ఏజెన్సీ)",
            "portal": "ప్రత్యక్ష ప్రభుత్వ ఆన్‌లైన్ పోర్టల్"
        },
        "stage": {
            "existing": "ప్రస్తుత వ్యాపార విస్తరణ",
            "new": "కొత్త యూనిట్ / స్టార్టప్"
        },
        "auth": {
            "loginTitle": "యోజనాసేతులో లాగిన్ అవ్వండి",
            "loginSubtitle": "పథకాల శోధన మరియు భద్రపరిచిన పథకాలను చూడండి",
            "registerTitle": "యోజనాసేతు ఖాతాను సృష్టించండి",
            "registerSubtitle": "వ్యక్తిగతీకరించిన నోటిఫికేషన్ల కోసం నమోదు చేసుకోండి",
            "fullName": "పూర్తి పేరు",
            "email": "ఈమెయిల్ చిరునామా",
            "emailOrPhone": "ఈమెయిల్ లేదా ఫోన్ నంబర్",
            "password": "పాస్‌వర్డ్",
            "confirmPassword": "పాస్‌వర్డ్‌ను నిర్ధారించండి",
            "phone": "ఫోన్ నంబర్",
            "role": "ఖాతా రకం",
            "citizen": "పౌరుడు / వ్యాపారవేత్త",
            "partner": "భాగస్వామి అధికారి",
            "signInBtn": "సైన్ ఇన్ చేయండి",
            "loginNow": "ఇప్పుడే లాగిన్ చేయండి",
            "registerBtn": "ఖాతాను సృష్టించండి",
            "forgotPassword": "పాస్‌వర్డ్ మర్చిపోయారా?",
            "hasAccount": "ఇప్పటికే ఖాతా ఉందా?",
            "noAccount": "ఖాతా లేదా?",
            "logout": "లాగౌట్",
            "signInWithGoogle": "గూగుల్‌తో సైన్ ఇన్ చేయండి",
            "continueWithGoogle": "గూగుల్‌తో కొనసాగించండి"
        }
    },
    "gu": {
        "profile": {
            "viewRecommendations": "યોજના ભલામણો જુઓ →"
        },
        "route": {
            "partner": "અધિકૃત ચેનલ પાર્ટનર સહાયતા (બેંક / એજન્સી)",
            "portal": "સીધું સરકારી ઓનલાઇન પોર્ટલ"
        },
        "stage": {
            "existing": "હાલના વ્યવસાયનો વિસ્તાર",
            "new": "નવું એકમ / સ્ટાર્ટઅપ"
        },
        "auth": {
            "loginTitle": "યોજનાસેતુમાં લૉગિન કરો",
            "loginSubtitle": "યોજના શોધ અને સાચવેલી યોજનાઓ જોવા માટે",
            "registerTitle": "યોજનાસેતુ ખાતું બનાવો",
            "registerSubtitle": "સૂચનાઓ મેળવવા માટે નોંધણી કરો",
            "fullName": "પૂરું નામ",
            "email": "ઈમેલ સરનામું",
            "emailOrPhone": "ઈમેલ અથવા ફોન નંબર",
            "password": "પાસવર્ડ",
            "confirmPassword": "પાસવર્ડ કન્ફર્મ કરો",
            "phone": "ફોન નંબર",
            "role": "ખાતાનો પ્રકાર",
            "citizen": "નાગરિક / ઉદ્યોગસાહસિક",
            "partner": "પાર્ટનર અધિકારી",
            "signInBtn": "સાઇન ઇન કરો",
            "loginNow": "હમણાં લૉગિન કરો",
            "registerBtn": "ખાતું બનાવો",
            "forgotPassword": "પાસવર્ડ ભૂલી ગયા છો?",
            "hasAccount": "પહેલેથી નોંધાયેલા છો?",
            "noAccount": "ખાતું નથી?",
            "logout": "લૉગઆઉટ",
            "signInWithGoogle": "ગૂગલ સાથે સાઇન ઇન કરો",
            "continueWithGoogle": "ગૂગલ સાથે ચાલુ રાખો"
        }
    },
    "kn": {
        "profile": {
            "viewRecommendations": "ಯೋಜನಾ ಶಿಫಾರಸುಗಳನ್ನು ವೀಕ್ಷಿಸಿ →"
        },
        "route": {
            "partner": "ಅಧಿಕೃತ ಪಾಲುದಾರ ನೆರವು (ಬ್ಯಾಂಕ್ / ಸಂಸ್ಥೆ)",
            "portal": "ನೇರ ಸರ್ಕಾರಿ ಆನ್‌ಲೈನ್ ಪೋರ್ಟಲ್"
        },
        "stage": {
            "existing": "ಪ್ರಸ್ತುತ ವ್ಯವಹಾರ ವಿಸ್ತರಣೆ",
            "new": "ಹೊಸ ಘಟಕ / ನವೋದ್ಯಮ"
        },
        "auth": {
            "loginTitle": "ಯೋಜನಾಸೇತುಗೆ ಲಾಗಿನ್ ಮಾಡಿ",
            "loginSubtitle": "ಯೋಜನೆಗಳ ಶೋಧನೆ ಮತ್ತು ಉಳಿಸಿದ ಯೋಜನೆಗಳಿಗೆ ಪ್ರವೇಶ",
            "registerTitle": "ಯೋಜನಾಸೇತು ಖಾತೆಯನ್ನು ರಚಿಸಿ",
            "registerSubtitle": "ಸೂಚನೆಗಳನ್ನು ಪಡೆಯಲು ನೋಂದಾಯಿಸಿ",
            "fullName": "ಪೂರ್ಣ ಹೆಸರು",
            "email": "ಇಮೇಲ್ ವಿಳಾಸ",
            "emailOrPhone": "ಇಮೇಲ್ ಅಥವಾ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ",
            "password": "ಪಾಸ್‌ವರ್ಡ್",
            "confirmPassword": "ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ",
            "phone": "ಮೊಬೈಲ್ ಸಂಖ್ಯೆ",
            "role": "ಖಾತೆಯ ಪ್ರಕಾರ",
            "citizen": "ನಾಗರಿಕ / ಉದ್ಯಮಿ",
            "partner": "ಪಾಲುದಾರ ಅಧಿಕಾರಿ",
            "signInBtn": "ಸೈನ್ ಇನ್ ಮಾಡಿ",
            "loginNow": "ಈಗಲೇ ಲಾಗಿನ್ ಮಾಡಿ",
            "registerBtn": "ಖಾತೆ ರಚಿಸಿ",
            "forgotPassword": "ಪಾಸ್‌ವರ್ಡ್ ಮರೆತಿರಾ?",
            "hasAccount": "ಈಗಾಗಲೇ ಖಾತೆ ಹೊಂದಿದ್ದೀರಾ?",
            "noAccount": "ಖಾತೆ ಇಲ್ಲವೇ?",
            "logout": "ಲಾಗ್‌ಔಟ್",
            "signInWithGoogle": "ಗೂಗಲ್‌ನೊಂದಿಗೆ ಸೈನ್ ಇನ್ ಮಾಡಿ",
            "continueWithGoogle": "ಗೂಗಲ್‌ನೊಂದಿಗೆ ಮುಂದುವರಿಯಿರಿ"
        }
    },
    "ml": {
        "profile": {
            "viewRecommendations": "പദ്ധതി ശുപാർശകൾ കാണുക →"
        },
        "route": {
            "partner": "അംഗീകൃത പങ്കാളി സഹായം (ബാങ്ക് / ഏജൻസി)",
            "portal": "നേരിട്ടുള്ള സർക്കാർ ഓൺലൈൻ പോർട്ടൽ"
        },
        "stage": {
            "existing": "നിലവിലുള്ള ബിസിനസ്സ് വിപുലീകരണം",
            "new": "പുതിയ യൂണിറ്റ് / സ്റ്റാർട്ടപ്പ്"
        },
        "auth": {
            "loginTitle": "യോജനാസേതുവിൽ ലോഗിൻ ചെയ്യുക",
            "loginSubtitle": "പദ്ധതി കണ്ടെത്തലും സംരക്ഷിച്ച പദ്ധതികളും കാണുക",
            "registerTitle": "യോജനാസേതു അക്കൗണ്ട് ഉണ്ടാക്കുക",
            "registerSubtitle": "അറിയിപ്പുകൾ ലഭിക്കുന്നതിനായി രജിസ്റ്റർ ചെയ്യുക",
            "fullName": "പൂർണ്ണ പേര്",
            "email": "ഇമെയിൽ വിലാസം",
            "emailOrPhone": "ഇമെയിൽ അല്ലെങ്കിൽ ഫോൺ നമ്പർ",
            "password": "പാസ്‌വേഡ്",
            "confirmPassword": "പാസ്‌വേഡ് സ്ഥിരീകരിക്കുക",
            "phone": "ഫോൺ നമ്പർ",
            "role": "അക്കൗണ്ട് തരം",
            "citizen": "പൗരൻ / സംരംഭകൻ",
            "partner": "പങ്കാളി ഉദ്യോഗസ്ഥൻ",
            "signInBtn": "സൈൻ ഇൻ ചെയ്യുക",
            "loginNow": "ഇപ്പോൾ ലോഗിൻ ചെയ്യുക",
            "registerBtn": "അക്കൗണ്ട് ഉണ്ടാക്കുക",
            "forgotPassword": "പാസ്‌വേഡ് മറന്നോ?",
            "hasAccount": "ഇതിനകം അക്കൗണ്ട് ഉണ്ടോ?",
            "noAccount": "അക്കൗണ്ട് ഇല്ലേ?",
            "logout": "ലോഗൗട്ട്",
            "signInWithGoogle": "ഗൂഗിൾ ഉപയോഗിച്ച് സൈൻ ഇൻ ചെയ്യുക",
            "continueWithGoogle": "ഗൂഗിൾ ഉപയോഗിച്ച് തുടരുക"
        }
    },
    "pa": {
        "profile": {
            "viewRecommendations": "ਸਕੀਮ ਸਿਫ਼ਾਰਸ਼ਾਂ ਦੇਖੋ →"
        },
        "route": {
            "partner": "ਅਧਿਕਾਰਤ ਸਾਥੀ ਸਹਾਇਤਾ (ਬੈਂਕ / ਏਜੰਸੀ)",
            "portal": "ਸਿੱਧਾ ਸਰਕਾਰੀ ਆਨਲਾਈਨ ਪੋਰਟਲ"
        },
        "stage": {
            "existing": "ਮੌਜੂਦਾ ਕਾਰੋਬਾਰ ਦਾ ਵਿਸਥਾਰ",
            "new": "ਨਵੀਂ ਇਕਾਈ / ਸਟਾਰਟਅੱਪ"
        },
        "auth": {
            "loginTitle": "ਯੋਜਨਾਸੇਤੂ ਵਿੱਚ ਲਾਗਇਨ ਕਰੋ",
            "loginSubtitle": "ਸਕੀਮਾਂ ਦੀ ਖੋਜ ਅਤੇ ਸੰਭਾਲੀਆਂ ਸਕੀਮਾਂ ਤੱਕ ਪਹੁੰਚ",
            "registerTitle": "ਯੋਜਨਾਸੇਤੂ ਖਾਤਾ ਬਣਾਓ",
            "registerSubtitle": "ਨੋਟੀਫਿਕੇਸ਼ਨ ਪ੍ਰਾਪਤ ਕਰਨ ਲਈ ਰਜਿਸਟਰ ਕਰੋ",
            "fullName": "ਪੂਰਾ ਨਾਮ",
            "email": "ਈਮੇਲ ਪਤਾ",
            "emailOrPhone": "ਈਮੇਲ ਜਾਂ ਮੋਬਾਈਲ ਨੰਬਰ",
            "password": "ਪਾਸਵਰਡ",
            "confirmPassword": "ਪਾਸਵਰਡ ਦੀ ਪੁਸ਼ਟੀ ਕਰੋ",
            "phone": "ਮੋਬਾਈਲ ਨੰਬਰ",
            "role": "ਖਾਤਾ ਕਿਸਮ",
            "citizen": "ਨਾਗਰਿਕ / ਉਦਯੋਗਪਤੀ",
            "partner": "ਸਾਥੀ ਅਧਿਕਾਰੀ",
            "signInBtn": "ਸਾਈਨ ਇਨ ਕਰੋ",
            "loginNow": "ਹੁਣੇ ਲਾਗਇਨ ਕਰੋ",
            "registerBtn": "ਖਾਤਾ ਬਣਾਓ",
            "forgotPassword": "ਪਾਸਵਰਡ ਭੁੱਲ ਗਏ?",
            "hasAccount": "ਪਹਿਲਾਂ ਤੋਂ ਖਾਤਾ ਹੈ?",
            "noAccount": "ਖਾਤਾ ਨਹੀਂ ਹੈ?",
            "logout": "ਲਾਗਆਉਟ",
            "signInWithGoogle": "ਗੂਗਲ ਨਾਲ ਸਾਈਨ ਇਨ ਕਰੋ",
            "continueWithGoogle": "ਗੂਗਲ ਨਾਲ ਜਾਰੀ ਰੱਖੋ"
        }
    },
    "or": {
        "profile": {
            "viewRecommendations": "ଯୋଜନା ସୁପାରିଶ ଦେଖନ୍ତୁ →"
        },
        "route": {
            "partner": "ଅଧିକୃତ ଅଂଶୀଦାର ସହାୟତା (ବ୍ୟାଙ୍କ / ସଂସ୍ଥା)",
            "portal": "ସିଧାସଳଖ ସରକାରୀ ଅନଲାଇନ୍ ପୋର୍ଟାଲ୍"
        },
        "stage": {
            "existing": "ବିଦ୍ୟମାନ ବ୍ୟବସାୟ ସମ୍ପ୍ରସାରଣ",
            "new": "ନୂତନ ୟୁନିଟ୍ / ଷ୍ଟାର୍ଟଅପ୍"
        },
        "auth": {
            "loginTitle": "ଯୋଜନାସେତୁରେ ଲଗ୍ ଇନ୍ କରନ୍ତୁ",
            "loginSubtitle": "ଯୋଜନା ଅନୁସନ୍ଧାନ ଏବଂ ସଂରକ୍ଷିତ ଯୋଜନା ପ୍ରବେଶ କରନ୍ତୁ",
            "registerTitle": "ଯୋଜନାସେତୁ ଖାତା ସୃଷ୍ଟି କରନ୍ତୁ",
            "registerSubtitle": "ସୂଚନା ପାଇବା ପାଇଁ ପଞ୍ଜୀକରଣ କରନ୍ତୁ",
            "fullName": "ପୂରା ନାମ",
            "email": "ଇମେଲ ଠିକଣା",
            "emailOrPhone": "ଇମେଲ କିମ୍ବା ମୋବାଇଲ୍ ନମ୍ବର",
            "password": "ପାସୱାର୍ଡ",
            "confirmPassword": "ପାସୱାର୍ଡ ନିଶ୍ଚିତ କରନ୍ତୁ",
            "phone": "ମୋବାଇଲ୍ ନମ୍ବର",
            "role": "ଖାତା ପ୍ରକାର",
            "citizen": "ନାଗରିକ / ଉଦ୍ୟୋଗୀ",
            "partner": "ଅଂଶୀଦାର ଅଧିକାରୀ",
            "signInBtn": "ସାଇନ୍ ଇନ୍ କରନ୍ତୁ",
            "loginNow": "ବର୍ତ୍ତମାନ ଲଗ୍ ଇନ୍ କରନ୍ତୁ",
            "registerBtn": "ଖାତା ସୃଷ୍ଟି କରନ୍ତୁ",
            "forgotPassword": "ପାସୱାର୍ଡ ଭୁଲିଗଲେ କି?",
            "hasAccount": "ପୂର୍ବରୁ ଖାତା ଅଛି କି?",
            "noAccount": "ଖାତା ନାହିଁ କି?",
            "logout": "ଲଗ୍ ଆଉଟ୍",
            "signInWithGoogle": "ଗୁଗୁଲ୍ ସହିତ ସାଇନ୍ ଇନ୍ କରନ୍ତୁ",
            "continueWithGoogle": "ଗୁଗୁଲ୍ ସହିତ ଜାରି ରଖନ୍ତୁ"
        }
    },
    "as": {
        "profile": {
            "viewRecommendations": "আঁচনিৰ পৰামৰ্শ চাওক →"
        },
        "route": {
            "partner": "অনুমোদিত অংশীদাৰ সাহায্য (বেংক / সংস্থা)",
            "portal": "পোনপটীয়া চৰকাৰী অনলাইন পৰ্টেল"
        },
        "stage": {
            "existing": "বৰ্তমানৰ ব্যৱসায় সম্প্ৰসাৰণ",
            "new": "নতুন গোট / ষ্টাৰ্টআপ"
        },
        "auth": {
            "loginTitle": "যোজনা সেতু ত লগইন কৰক",
            "loginSubtitle": "আঁচনি সন্ধান আৰু সংৰক্ষিত আঁচনি চাওক",
            "registerTitle": "যোজনা সেতু একাউণ্ট সৃষ্টি কৰক",
            "registerSubtitle": "ব্যক্তিগতকৃত জাননী লাভ কৰিবলৈ পঞ্জীয়ন কৰক",
            "fullName": "সম্পূৰ্ণ নাম",
            "email": "ইমেইল ঠিকনা",
            "emailOrPhone": "ইমেইল বা ম'বাইল নম্বৰ",
            "password": "পাছৱৰ্ড",
            "confirmPassword": "পাছৱৰ্ড নিশ্চিত কৰক",
            "phone": "ম'বাইল নম্বৰ",
            "role": "একাউণ্টৰ ধৰণ",
            "citizen": "নাগৰিক / উদ্যোগী",
            "partner": "অংশীদাৰ বিষয়া",
            "signInBtn": "ছাইন ইন কৰক",
            "loginNow": "এতিয়াই লগইন কৰক",
            "registerBtn": "একাউণ্ট সৃষ্টি কৰক",
            "forgotPassword": "পাছৱৰ্ড পাহৰিলে নেকি?",
            "hasAccount": "ইতিমধ্যে পঞ্জীয়নভুক্ত নেকি?",
            "noAccount": "একাউণ্ট নাই নেকি?",
            "logout": "লগআউট",
            "signInWithGoogle": "গুগলৰ সৈতে ছাইন ইন কৰক",
            "continueWithGoogle": "গুগলৰ সৈতে আগবাঢ়ক"
        }
    }
}

def deep_merge(target, src):
    for k, v in src.items():
        if isinstance(v, dict):
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            deep_merge(target[k], v)
        else:
            target[k] = v

def run():
    print("Translating remaining UI namespaces across all 11 non-English locales...")
    for lang, data in SHARED_DATA.items():
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.exists(file_path):
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            target_data = json.load(f)

        deep_merge(target_data, data)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(target_data, f, ensure_ascii=False, indent=2)

        print(f"Updated {lang}.json")

if __name__ == "__main__":
    run()
