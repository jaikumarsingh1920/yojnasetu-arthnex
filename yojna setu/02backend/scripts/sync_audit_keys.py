import json
import os

locales_dir = r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src\i18n\locales'

translations = {
    'en': {
        'schemes': {
            'findForMyProfileDesc': 'Instantly check rule-based eligibility for all 90 schemes matching your citizen profile.',
            'gazetteRepositoryBadge': 'Gazette Verified Repository',
            'authoritativeCount': 'Schemes Authoritative',
            'routeLabel': 'Route',
        },
        'schemeCard': {
            'guidelines': 'Guidelines',
        },
        'dashboard': {
            'activeApplicationsSub': 'Review current status, required document checklists, and assigned partner offices.',
            'startNewCheck': 'Start New Check',
        },
        'partnerLocator': {
            'quickFocus': 'Quick Focus:',
            'applyPortalNotice': 'Click "Apply on Official Portal" above to submit your application directly on the ministry portal.',
            'browseGorakhpur': 'Browse verified Gorakhpur & UP centres →',
            'kmAway': 'km away',
        }
    },
    'hi': {
        'schemes': {
            'findForMyProfileDesc': 'अपनी नागरिक प्रोफ़ाइल से मेल खाने वाली सभी 90 योजनाओं के लिए नियम-आधारित पात्रता तुरंत जाँचें।',
            'gazetteRepositoryBadge': 'राजपत्र सत्यापित रिपॉजिटरी',
            'authoritativeCount': 'प्रामाणिक योजनाएँ',
            'routeLabel': 'मार्ग',
        },
        'schemeCard': {
            'guidelines': 'दिशा-निर्देश',
        },
        'dashboard': {
            'activeApplicationsSub': 'वर्तमान स्थिति, आवश्यक दस्तावेज़ चेकलिस्ट और आवंटित पार्टनर कार्यालयों की समीक्षा करें।',
            'startNewCheck': 'नई पात्रता जाँच शुरू करें',
        },
        'partnerLocator': {
            'quickFocus': 'त्वरित केंद्र:',
            'applyPortalNotice': 'मंत्रालय पोर्टल पर सीधे आवेदन जमा करने के लिए ऊपर "आधिकारिक पोर्टल पर आवेदन करें" पर क्लिक करें।',
            'browseGorakhpur': 'सत्यापित गोरखपुर और यूपी केंद्र देखें →',
            'kmAway': 'किमी दूर',
        }
    },
    'bn': {
        'schemes': {
            'findForMyProfileDesc': 'আপনার নাগরিক প্রোফাইলের সাথে মেলে এমন সমস্ত 90টি প্রকল্পের নিয়ম-ভিত্তিক যোগ্যতা তাৎক্ষণিকভাবে পরীক্ষা করুন।',
            'gazetteRepositoryBadge': 'গেজেট যাচাইকৃত সংগ্রহস্থল',
            'authoritativeCount': 'প্রামাণিক প্রকল্প',
            'routeLabel': 'রুট',
        },
        'schemeCard': {
            'guidelines': 'নির্দেশিকা',
        },
        'dashboard': {
            'activeApplicationsSub': 'বর্তমান স্থিতি, প্রয়োজনীয় নথিপত্র চেকলিস্ট এবং নির্ধারিত পার্টনার অফিস পর্যালোচনা করুন।',
            'startNewCheck': 'নতুন যোগ্যতা যাচাই শুরু করুন',
        },
        'partnerLocator': {
            'quickFocus': 'দ্রুত কেন্দ্র:',
            'applyPortalNotice': 'মন্ত্রণালয়ের পোর্টালে সরাসরি আবেদন জমা দিতে উপরে "অফিসিয়াল পোর্টালে আবেদন করুন"-এ ক্লিক করুন।',
            'browseGorakhpur': 'যাচাইকৃত গোরখপুর এবং ইউপি কেন্দ্রগুলি দেখুন →',
            'kmAway': 'কিমি দূরে',
        }
    },
    'mr': {
        'schemes': {
            'findForMyProfileDesc': 'आपल्या नागरिक प्रोफाइलशी जुळणाऱ्या सर्व 90 योजनांसाठी नियम-आधारित पात्रता त्वरित तपासा.',
            'gazetteRepositoryBadge': 'राजपत्र पडताळणीकृत भांडार',
            'authoritativeCount': 'अधिकृत योजना',
            'routeLabel': 'मार्ग',
        },
        'schemeCard': {
            'guidelines': 'मार्गदर्शक तत्त्वे',
        },
        'dashboard': {
            'activeApplicationsSub': 'सद्यस्थिती, आवश्यक कागदपत्र चेकलिस्ट आणि नियुक्त भागीदार कार्यालयांचे पुनरावलोकन करा.',
            'startNewCheck': 'नवीन पात्रता तपासणी सुरू करा',
        },
        'partnerLocator': {
            'quickFocus': 'त्वरित केंद्र:',
            'applyPortalNotice': 'मंत्रालयाच्या पोर्टलवर थेट अर्ज सादर करण्यासाठी वरील "अधिकृत पोर्टलवर अर्ज करा" वर क्लिक करा.',
            'browseGorakhpur': 'पडताळणीकृत गोरखपूर आणि यूपी केंद्रे पहा →',
            'kmAway': 'किमी अंतरावर',
        }
    },
    'ta': {
        'schemes': {
            'findForMyProfileDesc': 'உங்கள் குடிமக்கள் சுயவிவரத்துடன் பொருந்தும் அனைத்து 90 திட்டங்களுக்கும் விதி அடிப்படையிலான தகுதியை உடனடியாகச் சரிபார்க்கவும்.',
            'gazetteRepositoryBadge': 'அரசிதழ் சரிபார்க்கப்பட்ட களஞ்சியம்',
            'authoritativeCount': 'அங்கீகரிக்கப்பட்ட திட்டங்கள்',
            'routeLabel': 'பாதை',
        },
        'schemeCard': {
            'guidelines': 'வழிகாட்டுதல்கள்',
        },
        'dashboard': {
            'activeApplicationsSub': 'தற்போதைய நிலை, தேவையான ஆவண சரிபார்ப்பு பட்டியல் மற்றும் ஒதுக்கப்பட்ட கூட்டாளர் அலுவலகங்களை மதிப்பாய்வு செய்யவும்.',
            'startNewCheck': 'புதிய தகுதி சரிபார்ப்பைத் தொடங்கு',
        },
        'partnerLocator': {
            'quickFocus': 'விரைவு மையங்கள்:',
            'applyPortalNotice': 'அமைச்சக போர்ட்டலில் நேரடியாக விண்ணப்பத்தை சமர்ப்பிக்க மேலே உள்ள "அதிகாரப்பூர்வ போர்ட்டலில் விண்ணப்பிக்கவும்" என்பதைக் கிளிக் செய்யவும்.',
            'browseGorakhpur': 'சரிபார்க்கப்பட்ட கோரக்பூர் & உபி மையங்களைப் பார்க்கவும் →',
            'kmAway': 'கிமீ தொலைவில்',
        }
    },
    'te': {
        'schemes': {
            'findForMyProfileDesc': 'మీ పౌర ప్రొఫైల్‌తో సరిపోలే మొత్తం 90 పథకాల కోసం నిబంధనల ఆధారిత అర్హతను తక్షణమే తనిఖీ చేయండి.',
            'gazetteRepositoryBadge': 'గెజిట్ ధృవీకరించబడిన నిల్వ',
            'authoritativeCount': 'అధికారిక పథకాలు',
            'routeLabel': 'మార్గం',
        },
        'schemeCard': {
            'guidelines': 'మార్గదర్శకాలు',
        },
        'dashboard': {
            'activeApplicationsSub': 'ప్రస్తుత స్థితి, అవసరమైన పత్రాల చెక్‌లిస్ట్ మరియు కేటాయించిన భాగస్వామి కార్యాలయాలను సమీక్షించండి.',
            'startNewCheck': 'కొత్త అర్హత తనిఖీని ప్రారంభించండి',
        },
        'partnerLocator': {
            'quickFocus': 'శీఘ్ర కేంద్రాలు:',
            'applyPortalNotice': 'మంత్రిత్వ శాఖ పోర్టల్‌లో నేరుగా దరఖాస్తును సమర్పించడానికి ఎగువన ఉన్న "అధికారిక పోర్టల్‌లో దరఖాస్తు చేయండి"పై క్లిక్ చేయండి.',
            'browseGorakhpur': 'ధృవీకరించబడిన గోరఖ్‌పూర్ & యుపి కేంద్రాలను బ్రౌజ్ చేయండి →',
            'kmAway': 'కి.మీ దూరంలో',
        }
    },
    'gu': {
        'schemes': {
            'findForMyProfileDesc': 'તમારી નાગરિક પ્રોફાઇલ સાથે મેળ ખાતી તમામ 90 યોજનાઓ માટે નિયમ-આધારિત પાત્રતા તાત્કાલિક તપાસો.',
            'gazetteRepositoryBadge': 'ગેઝેટ ચકાસાયેલ ભંડાર',
            'authoritativeCount': 'સત્તાવાર યોજનાઓ',
            'routeLabel': 'માર્ગ',
        },
        'schemeCard': {
            'guidelines': 'માર્ગદર્શિકા',
        },
        'dashboard': {
            'activeApplicationsSub': 'વર્તમાન સ્થિતિ, જરૂરી દસ્તાવેજ ચેકલિસ્ટ અને ફાળવેલ ભાગીદાર કચેરીઓની સમીક્ષા કરો.',
            'startNewCheck': 'નવી પાત્રતા ચકાસણી શરૂ કરો',
        },
        'partnerLocator': {
            'quickFocus': 'ઝડપી કેન્દ્રો:',
            'applyPortalNotice': 'મંત્રાલયના પોર્ટલ પર સીધી અરજી સબમિટ કરવા માટે ઉપર "સત્તાવાર પોર્ટલ પર અરજી કરો" પર ક્લિક કરો.',
            'browseGorakhpur': 'ચકાસાયેલ ગોરખપુર અને યુપી કેન્દ્રો જુઓ →',
            'kmAway': 'કિમી દૂર',
        }
    },
    'kn': {
        'schemes': {
            'findForMyProfileDesc': 'ನಿಮ್ಮ ನಾಗರಿಕ ಪ್ರೊಫೈಲ್‌ಗೆ ಹೊಂದಿಕೆಯಾಗುವ ಎಲ್ಲಾ 90 ಯೋಜನೆಗಳಿಗೆ ನಿಯಮ-ಆಧಾರಿತ ಅರ್ಹತೆಯನ್ನು ತಕ್ಷಣ ಪರಿಶೀಲಿಸಿ.',
            'gazetteRepositoryBadge': 'ಗೆಜೆಟ್ ಪರಿಶೀಲಿತ ಭಂಡಾರ',
            'authoritativeCount': 'ಅಧಿಕೃತ ಯೋಜನೆಗಳು',
            'routeLabel': 'ಮಾರ್ಗ',
        },
        'schemeCard': {
            'guidelines': 'ಮಾರ್ಗಸೂಚಿಗಳು',
        },
        'dashboard': {
            'activeApplicationsSub': 'ಪ್ರಸ್ತುತ ಸ್ಥಿತಿ, ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳ ಪರಿಶೀಲನಾಪಟ್ಟಿ ಮತ್ತು ನಿಯೋಜಿತ ಪಾಲುದಾರ ಕಚೇರಿಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.',
            'startNewCheck': 'ಹೊಸ ಅರ್ಹತಾ ಪರಿಶೀಲನೆ ಪ್ರಾರಂಭಿಸಿ',
        },
        'partnerLocator': {
            'quickFocus': 'ತ್ವರಿತ ಕೇಂದ್ರಗಳು:',
            'applyPortalNotice': 'ಸಚಿವಾಲಯದ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ನೇರವಾಗಿ ಅರ್ಜಿಯನ್ನು ಸಲ್ಲಿಸಲು ಮೇಲಿನ "ಅಧಿಕೃತ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ" ಕ್ಲಿಕ್ ಮಾಡಿ.',
            'browseGorakhpur': 'ಪರಿಶೀಲಿಸಿದ ಗೋರಖ್‌ಪುರ ಮತ್ತು ಯುಪಿ ಕೇಂದ್ರಗಳನ್ನು ಬ್ರೌಸ್ ಮಾಡಿ →',
            'kmAway': 'ಕಿಮೀ ದೂರದಲ್ಲಿ',
        }
    },
    'ml': {
        'schemes': {
            'findForMyProfileDesc': 'നിങ്ങളുടെ പൗര പ്രൊഫൈലുമായി പൊരുത്തപ്പെടുന്ന 90 സ്കീമുകളുടെയും നിയമപരമായ യോഗ്യത തൽക്ഷണം പരിശോധിക്കുക.',
            'gazetteRepositoryBadge': 'ഗസറ്റ് സ്ഥിരീകരിച്ച ശേഖരം',
            'authoritativeCount': 'ആധികാരിക പദ്ധതികൾ',
            'routeLabel': 'റൂട്ട്',
        },
        'schemeCard': {
            'guidelines': 'മാർഗ്ഗനിർദ്ദേശങ്ങൾ',
        },
        'dashboard': {
            'activeApplicationsSub': 'നിലവിലെ അവസ്ഥ, ആവശ്യമായ രേഖകളുടെ ചെക്ക്‌ലിസ്റ്റ്, അനുവദിച്ച പങ്കാളി ഓഫീസുകൾ എന്നിവ അവലോകനം ചെയ്യുക.',
            'startNewCheck': 'പുതിയ യോഗ്യതാ പരിശോധന ആരംഭിക്കുക',
        },
        'partnerLocator': {
            'quickFocus': 'ദ്രുത കേന്ദ്രങ്ങൾ:',
            'applyPortalNotice': 'മന്ത്രാലയ പോർട്ടലിൽ നേരിട്ട് അപേക്ഷ സമർപ്പിക്കാൻ മുകളിലുള്ള "ഔദ്യോഗിക പോർട്ടലിൽ അപേക്ഷിക്കുക" ക്ലിക്ക് ചെയ്യുക.',
            'browseGorakhpur': 'സ്ഥിരീകരിച്ച ഗോരഖ്പൂർ & യുപി കേന്ദ്രങ്ങൾ കാണുക →',
            'kmAway': 'കിമീ അകലെ',
        }
    },
    'pa': {
        'schemes': {
            'findForMyProfileDesc': 'ਆਪਣੇ ਨਾਗਰਿਕ ਪ੍ਰੋਫਾਈਲ ਨਾਲ ਮੇਲ ਖਾਂਦੀਆਂ ਸਾਰੀਆਂ 90 ਸਕੀਮਾਂ ਲਈ ਨਿਯਮ-ਅਧਾਰਤ ਯੋਗਤਾ ਦੀ ਤੁਰੰਤ ਜਾਂਚ ਕਰੋ।',
            'gazetteRepositoryBadge': 'ਗਜ਼ਟ ਪ੍ਰਮਾਣਿਤ ਭੰਡਾਰ',
            'authoritativeCount': 'ਪ੍ਰਮਾਣਿਕ ਸਕੀਮਾਂ',
            'routeLabel': 'ਰੂਟ',
        },
        'schemeCard': {
            'guidelines': 'ਦਿਸ਼ਾ-ਨਿਰਦੇਸ਼',
        },
        'dashboard': {
            'activeApplicationsSub': 'ਮੌਜੂਦਾ ਸਥਿਤੀ, ਲੋੜੀਂਦੇ ਦਸਤਾਵੇਜ਼ ਚੈੱਕਲਿਸਟ ਅਤੇ ਨਿਰਧਾਰਤ ਭਾਈਵਾਲ ਦਫਤਰਾਂ ਦੀ ਸਮੀਖਿਆ ਕਰੋ।',
            'startNewCheck': 'ਨਵੀਂ ਯੋਗਤਾ ਜਾਂਚ ਸ਼ੁਰੂ ਕਰੋ',
        },
        'partnerLocator': {
            'quickFocus': 'ਤੇਜ਼ ਕੇਂਦਰ:',
            'applyPortalNotice': 'ਮੰਤਰਾਲੇ ਦੇ ਪੋਰਟਲ \'ਤੇ ਸਿੱਧਾ ਅਰਜ਼ੀ ਜਮ੍ਹਾਂ ਕਰਨ ਲਈ ਉੱਪਰ "ਅਧਿਕਾਰਤ ਪੋਰਟਲ \'ਤੇ ਅਰਜ਼ੀ ਦਿਓ" \'ਤੇ ਕਲਿੱਕ ਕਰੋ।',
            'browseGorakhpur': 'ਪ੍ਰਮਾਣਿਤ ਗੋਰਖਪੁਰ ਅਤੇ ਯੂਪੀ ਕੇਂਦਰ ਦੇਖੋ →',
            'kmAway': 'ਕਿਮੀ ਦੂਰ',
        }
    },
    'or': {
        'schemes': {
            'findForMyProfileDesc': 'ଆପଣଙ୍କ ନାଗରିକ ପ୍ରୋଫାଇଲ୍ ସହିତ ମେଳ ଖାଉଥିବା ସମସ୍ତ 90ଟି ଯୋଜନା ପାଇଁ ନିୟମ-ଆଧାରିତ ଯୋଗ୍ୟତା ତୁରନ୍ତ ଯାଞ୍ଚ କରନ୍ତୁ।',
            'gazetteRepositoryBadge': 'ଗେଜେଟ୍ ପ୍ରମାଣିତ ସଂଗ୍ରହସ୍ଥଳ',
            'authoritativeCount': 'ପ୍ରାମାଣିକ ଯୋଜନା',
            'routeLabel': 'ମାର୍ଗ',
        },
        'schemeCard': {
            'guidelines': 'ମାର୍ଗଦର୍ଶିକା',
        },
        'dashboard': {
            'activeApplicationsSub': 'ବର୍ତ୍ତମାନର ସ୍ଥିତି, ଆବଶ୍ୟକୀୟ ଦଲିଲ୍ ଯାଞ୍ଚ ତାଲିକା ଏବଂ ନିର୍ଦ୍ଧାରିତ ଅଂଶୀଦାର କାର୍ଯ୍ୟାଳୟଗୁଡ଼ିକର ସମୀକ୍ଷା କରନ୍ତୁ।',
            'startNewCheck': 'ନୂତନ ଯୋଗ୍ୟତା ଯାଞ୍ଚ ଆରମ୍ଭ କରନ୍ତୁ',
        },
        'partnerLocator': {
            'quickFocus': 'ତ୍ୱରିତ କେନ୍ଦ୍ର:',
            'applyPortalNotice': 'ମନ୍ତ୍ରଣାଳୟ ପୋର୍ଟାଲରେ ସିଧାସଳଖ ଆବେଦନ ଦାଖଲ କରିବାକୁ ଉପରେ "ଅଫିସିଆଲ୍ ପୋର୍ଟାଲରେ ଆବେଦନ କରନ୍ତୁ" କ୍ଲିକ୍ କରନ୍ତୁ।',
            'browseGorakhpur': 'ପ୍ରମାଣିତ ଗୋରଖପୁର ଏବଂ ୟୁପି କେନ୍ଦ୍ରଗୁଡ଼ିକ ଦେଖନ୍ତୁ →',
            'kmAway': 'କିମି ଦୂରରେ',
        }
    },
    'as': {
        'schemes': {
            'findForMyProfileDesc': 'আপোনাৰ নাগৰিক প্ৰফাইলৰ সৈতে মিল থকা সকলো 90 খন আঁচনিৰ বাবে নিয়ম-ভিত্তিক যোগ্যতা তৎক্ষণাৎ পৰীক্ষা কৰক।',
            'gazetteRepositoryBadge': 'গেজেট প্ৰমাণিত সংগ্ৰহস্থল',
            'authoritativeCount': 'প্ৰামাণিক আঁচনি',
            'routeLabel': 'পথ',
        },
        'schemeCard': {
            'guidelines': 'নিৰ্দেশাৱলী',
        },
        'dashboard': {
            'activeApplicationsSub': 'বৰ্তমান স্থিতি, প্ৰয়োজনীয় নথিপত্ৰৰ পৰীক্ষা তালিকা আৰু নিৰ্ধাৰিত সহযোগী কাৰ্যালয়সমূহ পৰ্যালোচনা কৰক।',
            'startNewCheck': 'নতুন যোগ্যতা পৰীক্ষা আৰম্ভ কৰক',
        },
        'partnerLocator': {
            'quickFocus': 'দ্ৰুত কেন্দ্ৰ:',
            'applyPortalNotice': 'মন্ত্ৰালয়ৰ পৰ্টেলত পোনপটীয়াকৈ আবেদন জমা দিবলৈ ওপৰৰ "আনুষ্ঠানিক পৰ্টেলত আবেদন কৰক"ত ক্লিক কৰক।',
            'browseGorakhpur': 'প্ৰমাণিত গোৰখপুৰ আৰু ইউপি কেন্দ্ৰসমূহ চাওক →',
            'kmAway': 'কিমি দূৰত',
        }
    }
}

for lang, namespaces in translations.items():
    file_path = os.path.join(locales_dir, f'{lang}.json')
    if not os.path.exists(file_path):
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for ns, keys in namespaces.items():
        if ns not in data:
            data[ns] = {}
        for k, val in keys.items():
            data[ns][k] = val
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {lang}.json with new audit keys.")
