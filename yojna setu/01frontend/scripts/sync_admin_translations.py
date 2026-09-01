import json
import os

locales_dir = r"c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src\i18n\locales"

admin_translations = {
    "en": {
        "dashboardTitle": "System Admin Dashboard",
        "schemeManagement": "Scheme Management",
        "schemesAudit": "Schemes Audit",
        "rulesEngine": "Rules Engine",
        "documentsChecklist": "Documents Checklist",
        "schemeChangelogs": "Scheme Changelogs",
        "aiRagHealth": "AI & RAG Health",
        "addScheme": "Add New Scheme",
        "editScheme": "Edit Scheme",
        "deactivateScheme": "Deactivate Scheme",
        "activateScheme": "Activate Scheme",
        "active": "ACTIVE",
        "inactive": "INACTIVE"
    },
    "hi": {
        "dashboardTitle": "सिस्टम एडमिन डैशबोर्ड",
        "schemeManagement": "योजना प्रबंधन",
        "schemesAudit": "योजना ऑडिट",
        "rulesEngine": "नियम इंजन",
        "documentsChecklist": "दस्तावेज़ चेकलिस्ट",
        "schemeChangelogs": "योजना परिवर्तन लॉग",
        "aiRagHealth": "एआई और आरएजी स्वास्थ्य",
        "addScheme": "नई योजना जोड़ें",
        "editScheme": "योजना संपादित करें",
        "deactivateScheme": "योजना निष्क्रिय करें",
        "activateScheme": "योजना सक्रिय करें",
        "active": "सक्रिय",
        "inactive": "निष्क्रिय"
    },
    "bn": {
        "dashboardTitle": "সিস্টেম অ্যাডমিন ড্যাশবোর্ড",
        "schemeManagement": "প্রকল্প পরিচালনা",
        "schemesAudit": "প্রকল্প নিরীক্ষা",
        "rulesEngine": "নিয়ম ইঞ্জিন",
        "documentsChecklist": "নথি চেকলিস্ট",
        "schemeChangelogs": "প্রকল্প পরিবর্তন লগ",
        "aiRagHealth": "এআই ও আরএজি স্বাস্থ্য",
        "addScheme": "নতুন প্রকল্প যোগ করুন",
        "editScheme": "প্রকল্প সম্পাদনা",
        "deactivateScheme": "প্রকল্প নিষ্ক্রিয় করুন",
        "activateScheme": "প্রকল্প সক্রিয় করুন",
        "active": "সক্রিয়",
        "inactive": "নিষ্ক্রিয়"
    },
    "te": {
        "dashboardTitle": "సిస్టమ్ అడ్మిన్ డాష్‌బోర్డ్",
        "schemeManagement": "పథకం నిర్వహణ",
        "schemesAudit": "పథకాల ఆడిట్",
        "rulesEngine": "నిబంధనల ఇంజిన్",
        "documentsChecklist": "పత్రాల చెక్‌లిస్ట్",
        "schemeChangelogs": "పథకం మార్పు లాగ్‌లు",
        "aiRagHealth": "ఏఐ & రాగ్ ఆరోగ్యం",
        "addScheme": "కొత్త పథకాన్ని జోడించండి",
        "editScheme": "పథకాన్ని సవరించండి",
        "deactivateScheme": "పథకాన్ని నిష్క్రియం చేయండి",
        "activateScheme": "పథకాన్ని సక్రియం చేయండి",
        "active": "యాక్టివ్",
        "inactive": "ఇన్యాక్టివ్"
    },
    "ta": {
        "dashboardTitle": "கணினி நிர்வாகி டாஷ்போர்டு",
        "schemeManagement": "திட்ட மேலாண்மை",
        "schemesAudit": "திட்ட தணிக்கை",
        "rulesEngine": "விதிகள் இயந்திரம்",
        "documentsChecklist": "ஆவண சரிபார்ப்பு பட்டியல்",
        "schemeChangelogs": "திட்ட மாற்ற பதிவுகள்",
        "aiRagHealth": "AI & RAG நிலை",
        "addScheme": "புதிய திட்டத்தைச் சேர்க்கவும்",
        "editScheme": "திட்டத்தைத் திருத்து",
        "deactivateScheme": "திட்டத்தை செயலிழக்கச் செய்",
        "activateScheme": "திட்டத்தை செயல்படுத்து",
        "active": "செயலில் உள்ளது",
        "inactive": "செயலிழந்தது"
    },
    "mr": {
        "dashboardTitle": "प्रणाली प्रशासक डॅशबोर्ड",
        "schemeManagement": "योजना व्यवस्थापन",
        "schemesAudit": "योजना लेखापरीक्षण",
        "rulesEngine": "नियम इंजिन",
        "documentsChecklist": "कागदपत्रे चेकलिस्ट",
        "schemeChangelogs": "योजना बदल नोंदी",
        "aiRagHealth": "एआय व आरएजी स्थिती",
        "addScheme": "नवीन योजना जोडा",
        "editScheme": "योजना संपादित करा",
        "deactivateScheme": "योजना निष्क्रिय करा",
        "activateScheme": "योजना सक्रिय करा",
        "active": "सक्रिय",
        "inactive": "निष्क्रिय"
    },
    "gu": {
        "dashboardTitle": "સિસ્ટમ એડમિન ડેશબોર્ડ",
        "schemeManagement": "યોજના સંચાલન",
        "schemesAudit": "યોજના ઓડિટ",
        "rulesEngine": "નિયમ એન્જિન",
        "documentsChecklist": "દસ્તાવેજ ચેકલિસ્ટ",
        "schemeChangelogs": "યોજના ફેરફાર લૉગ",
        "aiRagHealth": "એઆઈ અને આરએજી સ્થિતિ",
        "addScheme": "નવી યોજના ઉમેરો",
        "editScheme": "યોજના સંપાદિત કરો",
        "deactivateScheme": "યોજના નિષ્ક્રિય કરો",
        "activateScheme": "યોજના સક્રિય કરો",
        "active": "સક્રિય",
        "inactive": "નિષ્ક્રિય"
    },
    "kn": {
        "dashboardTitle": "ವ್ಯವಸ್ಥಾ ನಿರ್ವಾಹಕ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "schemeManagement": "ಯೋಜನಾ ನಿರ್ವಹಣೆ",
        "schemesAudit": "ಯೋಜನೆಗಳ ಲೆಕ್ಕಪರಿಶೋಧನೆ",
        "rulesEngine": "ನಿಯಮಗಳ ಎಂಜಿನ್",
        "documentsChecklist": "ದಾಖಲೆಗಳ ಪರಿಶೀಲನಾ ಪಟ್ಟಿ",
        "schemeChangelogs": "ಯೋಜನೆ ಬದಲಾವಣೆ ದಾಖಲೆಗಳು",
        "aiRagHealth": "ಎಐ ಮತ್ತು ಆರ್‌ಎಜಿ ಸ್ಥಿತಿ",
        "addScheme": "ಹೊಸ ಯೋಜನೆಯನ್ನು ಸೇರಿಸಿ",
        "editScheme": "ಯೋಜನೆಯನ್ನು ಸಂಪಾದಿಸಿ",
        "deactivateScheme": "ಯೋಜನೆ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸಿ",
        "activateScheme": "ಯೋಜನೆ ಸಕ್ರಿಯಗೊಳಿಸಿ",
        "active": "ಸಕ್ರಿಯ",
        "inactive": "ನಿಷ್ಕ್ರಿಯ"
    },
    "ml": {
        "dashboardTitle": "സിസ്റ്റം അഡ്മിൻ ഡാഷ്‌ബോർഡ്",
        "schemeManagement": "പദ്ധതി മാനേജ്‌മെന്റ്",
        "schemesAudit": "പദ്ധതി ഓഡിറ്റ്",
        "rulesEngine": "നിയമ എഞ്ചിൻ",
        "documentsChecklist": "രേഖകളുടെ ചെക്ക്‌ലിസ്റ്റ്",
        "schemeChangelogs": "പദ്ധതി മാറ്റ രേഖകൾ",
        "aiRagHealth": "എഐ & ആർഎജി സ്ഥിതി",
        "addScheme": "പുതിയ പദ്ധതി ചേർക്കുക",
        "editScheme": "പദ്ധതി തിരുത്തുക",
        "deactivateScheme": "പദ്ധതി നിർജ്ജീവമാക്കുക",
        "activateScheme": "പദ്ധതി സജീവമാക്കുക",
        "active": "സജീവം",
        "inactive": "നിർജ്ജീവം"
    },
    "pa": {
        "dashboardTitle": "ਸਿਸਟਮ ਐਡਮਿਨ ਡੈਸ਼ਬੋਰਡ",
        "schemeManagement": "ਸਕੀਮ ਪ੍ਰਬੰਧਨ",
        "schemesAudit": "ਸਕੀਮਾਂ ਦੀ ਆਡਿਟ",
        "rulesEngine": "ਨਿਯਮ ਇੰਜਣ",
        "documentsChecklist": "ਦਸਤਾਵੇਜ਼ ਚੈੱਕਲਿਸਟ",
        "schemeChangelogs": "ਸਕੀਮ ਤਬਦੀਲੀ ਲੌਗ",
        "aiRagHealth": "ਏਆਈ ਅਤੇ ਆਰਏਜੀ ਸਿਹਤ",
        "addScheme": "ਨਵੀਂ ਸਕੀਮ ਸ਼ਾਮਲ ਕਰੋ",
        "editScheme": "ਸਕੀਮ ਸੋਧੋ",
        "deactivateScheme": "ਸਕੀਮ ਨੂੰ ਅਕਿਰਿਆਸ਼ੀਲ ਕਰੋ",
        "activateScheme": "ਸਕੀਮ ਨੂੰ ਕਿਰਿਆਸ਼ੀਲ ਕਰੋ",
        "active": "ਕਿਰਿਆਸ਼ੀਲ",
        "inactive": "ਅਕਿਰਿਆਸ਼ੀਲ"
    },
    "or": {
        "dashboardTitle": "ସିଷ୍ଟମ ଆଡମିନ ଡ୍ୟାସବୋର୍ଡ",
        "schemeManagement": "ଯୋଜନା ପରିଚାଳନା",
        "schemesAudit": "ଯୋଜନା ଅଡିଟ୍",
        "rulesEngine": "ନିୟମ ଇଞ୍ଜିନ",
        "documentsChecklist": "ଦସ୍ତାବିଜ ଯାଞ୍ଚ ତାଲିକା",
        "schemeChangelogs": "ଯୋଜନା ପରିବର୍ତ୍ତନ ଲଗ୍",
        "aiRagHealth": "ଏଆଇ ଓ ଆରଏଜି ସ୍ୱାସ୍ଥ୍ୟ",
        "addScheme": "ନୂତନ ଯୋଜନା ଯୋଡନ୍ତୁ",
        "editScheme": "ଯୋଜନା ସମ୍ପାଦନ କରନ୍ତୁ",
        "deactivateScheme": "ଯୋଜନା ନିଷ୍କ୍ରିୟ କରନ୍ତୁ",
        "activateScheme": "ଯୋଜନା ସକ୍ରିୟ କରନ୍ତୁ",
        "active": "ସକ୍ରିୟ",
        "inactive": "ନିଷ୍କ୍ରିୟ"
    },
    "as": {
        "dashboardTitle": "ছিষ্টেম এডমিন ডেচবৰ্ড",
        "schemeManagement": "আঁচনি ব্যৱস্থাপনা",
        "schemesAudit": "আঁচনিৰ অডিট",
        "rulesEngine": "নিয়ম ইঞ্জিন",
        "documentsChecklist": "নথি চেকলিষ্ট",
        "schemeChangelogs": "আঁচনি পৰিৱৰ্তন লগ",
        "aiRagHealth": "এআই আৰু আৰএজি স্বাস্থ্য",
        "addScheme": "নতুন আঁচনি যোগ কৰক",
        "editScheme": "আঁচনি সম্পাদনা কৰক",
        "deactivateScheme": "আঁচনি নিষ্ক্ৰিয় কৰক",
        "activateScheme": "আঁচনি সক্ৰিয় কৰক",
        "active": "সক্ৰিয়",
        "inactive": "নিষ্ক্ৰিয়"
    }
}

for lang, data in admin_translations.items():
    filepath = os.path.join(locales_dir, f"{lang}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)
        content["admin"] = data
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        print(f"Updated {lang}.json with admin translations.")
    else:
        print(f"File not found: {filepath}")

print("All 12 languages updated successfully with admin section!")
