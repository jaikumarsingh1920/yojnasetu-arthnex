"""
Comprehensive Regional Translation Script
Fills all remaining untranslated keys across bn, mr, ta, te, gu, kn, ml, pa, or, as
using high-quality localized terms derived from official Indian welfare vocabulary.
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")

def run():
    # Load en and hi as reference
    with open(os.path.join(LOCALES_DIR, "en.json"), "r", encoding="utf-8") as f:
        en = json.load(f)
    with open(os.path.join(LOCALES_DIR, "hi.json"), "r", encoding="utf-8") as f:
        hi = json.load(f)

    # Core vocabulary mappings for standard government terms
    VOCAB = {
        "bn": {
            "Apply": "আবেদন করুন", "Cancel": "বাতিল", "Delete": "মুছুন", "Details": "বিস্তারিত", "Edit": "সম্পাদনা",
            "Save": "সংরক্ষণ", "Search": "অনুসন্ধান", "Back": "ফিরে যান", "Next": "পরবর্তী", "Submit": "জমা দিন",
            "Calculate": "গণনা করুন", "Compare": "তুলনা করুন", "Close": "বন্ধ করুন", "Loading": "লোড হচ্ছে...",
            "Calculate EMI & Subsidy": "ইএমআই ও ভর্তুকি হিসাব করুন",
            "Calculation is indicative based on official scheme": "সরকারি প্রকল্পের নিয়মের ওপর ভিত্তি করে গণনা নির্দেশক",
            "Net Beneficiary Burden": "সুবিধাভোগীর মোট ব্যয়",
            "Requested Loan Amount (?)": "অনুরোধ করা ঋণের পরিমাণ (₹)",
            "Total Project Cost (?)": "মোট প্রকল্প ব্যয় (₹)",
            "Estimated Govt Subsidy": "আনুমানিক সরকারি ভর্তুকি",
            "Active Applications": "সক্রিয় আবেদন",
            "Approved": "অনুমোদিত",
            "Check Eligibility": "যোগ্যতা পরীক্ষা করুন",
            "Carry Original Documents": "আবেদনকালে মূল নথিপত্র সঙ্গে রাখুন",
            "Mandatory Documents": "বাধ্যতামূলক নথিপত্র",
            "Conditional Documents": "শর্তসাপেক্ষ নথিপত্র",
            "Official Requirement": "সরকারি দাপ্তরিক শর্তাবলী",
            "Page Not Found": "পৃষ্ঠাটি পাওয়া যায়নি",
            "Something went wrong": "কিছু ভুল হয়েছে",
            "Unauthorized": "অননুমোদিত অ্যাক্সেস",
            "Distance": "দূরত্ব",
            "Authorized Partner": "অনুমোদিত অংশীদার",
            "Common Service Center (CSC)": "সাধারণ সেবা কেন্দ্র (সিএসসি)",
            "District Industries Centre (DIC)": "জেলা শিল্প কেন্দ্র (ডিআইসি)",
            "Official Application Portal": "দাপ্তরিক আবেদন পোর্টাল",
            "Redirecting to Official Portal": "সরকারি পোর্টালে পুনর্নির্দেশ করা হচ্ছে",
            "All Categories": "সকল বিভাগ",
            "All Ministries": "সকল মন্ত্রণালয়",
            "All Financial Types": "সকল আর্থিক ধরন",
            "All Beneficiaries": "সকল সুবিধাভোগী",
            "Active Filters": "সক্রিয় ফিল্টার"
        },
        "mr": {
            "Apply": "अर्ज करा", "Cancel": "रद्द करा", "Delete": "हटवा", "Details": "तपशील", "Edit": "संपादित करा",
            "Save": "जतन करा", "Search": "शोधा", "Back": "मागे", "Next": "पुढे", "Submit": "प्रस्तुत करा",
            "Calculate": "गणना करा", "Compare": "तुलना करा", "Close": "बंद करा", "Loading": "लोड होत आहे...",
            "Calculate EMI & Subsidy": "ईएमआय आणि सबसिडी मोजा",
            "Calculation is indicative based on official scheme": "सरकारी योजनेच्या नियमांवर आधारित ही गणना सूचक आहे",
            "Net Beneficiary Burden": "लाभार्थ्याचा एकूण भार",
            "Requested Loan Amount (?)": "आवश्यक कर्ज रक्कम (₹)",
            "Total Project Cost (?)": "एकूण प्रकल्प खर्च (₹)",
            "Estimated Govt Subsidy": "अंदाजे सरकारी सबसिडी",
            "Active Applications": "सक्रिय अर्ज",
            "Approved": "मंजूर",
            "Check Eligibility": "पात्रता तपासा",
            "Carry Original Documents": "अर्जाच्या वेळी मूळ कागदपत्रे सोबत ठेवा",
            "Mandatory Documents": "अनिवार्य कागदपत्रे",
            "Conditional Documents": "अटींवर आधारित कागदपत्रे",
            "Official Requirement": "अधिकृत सरकारी अटी",
            "Page Not Found": "पृष्ठ आढळले नाही",
            "Something went wrong": "काहीतरी चूक झाली",
            "Unauthorized": "अनधिकृत प्रवेश",
            "Distance": "अंतर",
            "Authorized Partner": "अधिकृत भागीदार",
            "Common Service Center (CSC)": "नागरिक सेवा केंद्र (सीएससी)",
            "District Industries Centre (DIC)": "जिल्हा उद्योग केंद्र (डीआयसी)",
            "Official Application Portal": "अधिकृत अर्ज पोर्टल",
            "Redirecting to Official Portal": "सरकारी पोर्टलवर पुनर्निर्देशित करत आहे",
            "All Categories": "सर्व प्रवर्ग",
            "All Ministries": "सर्व मंत्रालये",
            "All Financial Types": "सर्व आर्थिक प्रकार",
            "All Beneficiaries": "सर्व लाभार्थी",
            "Active Filters": "सक्रिय फिल्टर्स"
        },
        "ta": {
            "Apply": "விண்ணப்பிக்கவும்", "Cancel": "ரத்துசெய்", "Delete": "நீக்கு", "Details": "விவரங்கள்", "Edit": "திருத்து",
            "Save": "சேமிக்கவும்", "Search": "தேடுக", "Back": "பின்செல்", "Next": "அடுத்து", "Submit": "சமர்ப்பிக்கவும்",
            "Calculate": "கணக்கிடுக", "Compare": "ஒப்பிடுக", "Close": "மூடுக", "Loading": "ஏற்றப்படுகிறது...",
            "Calculate EMI & Subsidy": "இஎம்ஐ மற்றும் மானியத்தைக் கணக்கிடுங்கள்",
            "Calculation is indicative based on official scheme": "அரசுத் திட்ட விதிகளின்படி இந்த கணக்கீடு குறிப்பானது",
            "Net Beneficiary Burden": "பயனாளியின் நிகர செலவு",
            "Requested Loan Amount (?)": "கோரப்பட்ட கடன் தொகை (₹)",
            "Total Project Cost (?)": "மொத்த திட்டச் செலவு (₹)",
            "Estimated Govt Subsidy": "மதிப்பிடப்பட்ட அரசு மானியம்",
            "Active Applications": "செயலில் உள்ள விண்ணப்பங்கள்",
            "Approved": "ஒப்புதல் அளிக்கப்பட்டது",
            "Check Eligibility": "தகுதியைச் சரிபார்க்கவும்",
            "Carry Original Documents": "அசல் ஆவணங்களை உடன் எடுத்துச் செல்லவும்",
            "Mandatory Documents": "கட்டாய ஆவணங்கள்",
            "Conditional Documents": "நிபந்தனைக்குட்பட்ட ஆவணங்கள்",
            "Official Requirement": "அதிகாரப்பூர்வ தேவைகள்",
            "Page Not Found": "பக்கம் கிடைக்கவில்லை",
            "Something went wrong": "ஏதோ தவறு நடந்துவிட்டது",
            "Unauthorized": "அங்கீகரிக்கப்படாத அணுகல்",
            "Distance": "தூரம்",
            "Authorized Partner": "அங்கீகரிக்கப்பட்ட கூட்டாளர்",
            "Common Service Center (CSC)": "பொது சேவை மையம் (CSC)",
            "District Industries Centre (DIC)": "மாவட்ட தொழில் மையம் (DIC)",
            "Official Application Portal": "அதிகாரப்பூர்வ விண்ணப்ப போர்டல்",
            "Redirecting to Official Portal": "அரசு போர்ட்டலுக்கு திருப்பி விடப்படுகிறது",
            "All Categories": "அனைத்து பிரிவுகள்",
            "All Ministries": "அனைத்து அமைச்சகங்கள்",
            "All Financial Types": "அனைத்து நிதி வகைகள்",
            "All Beneficiaries": "அனைத்து பயனாளிகள்",
            "Active Filters": "செயலில் உள்ள வடிகட்டிகள்"
        },
        "te": {
            "Apply": "దరఖాస్తు చేసుకోండి", "Cancel": "రద్దు", "Delete": "తొలగించు", "Details": "వివరాలు", "Edit": "సవరించు",
            "Save": "భద్రపరచు", "Search": "శోధించండి", "Back": "వెనుకకు", "Next": "తరువాత", "Submit": "సమర్పించు",
            "Calculate": "లెక్కించు", "Compare": "పోల్చండి", "Close": "మూసివేయి", "Loading": "లోడ్ అవుతోంది...",
            "Calculate EMI & Subsidy": "ఇఎంఐ మరియు సబ్సిడీని లెక్కించండి",
            "Calculation is indicative based on official scheme": "ప్రభుత్వ నిబంధనల ప్రకారం ఈ లెక్కింపు సూచనాత్మకమైనది",
            "Net Beneficiary Burden": "లబ్ధిదారుడి నికర భారం",
            "Requested Loan Amount (?)": "కోరిన రుణ మొత్తం (₹)",
            "Total Project Cost (?)": "మొత్తం ప్రాజెక్ట్ ఖర్చు (₹)",
            "Estimated Govt Subsidy": "అంచనా ప్రభుత్వ సబ్సిడీ",
            "Active Applications": "క్రియాశీల దరఖాస్తులు",
            "Approved": "ఆమోదించబడింది",
            "Check Eligibility": "అర్హతను తనిఖీ చేయండి",
            "Carry Original Documents": "అసలు పత్రాలను వెంట తీసుకెళ్లండి",
            "Mandatory Documents": "తప్పనిసరి పత్రాలు",
            "Conditional Documents": "షరతులతో కూడిన పత్రాలు",
            "Official Requirement": "అధికారిక నిబంధనలు",
            "Page Not Found": "పేజీ కనుగొనబడలేదు",
            "Something went wrong": "ఏదో తప్పు జరిగింది",
            "Unauthorized": "అనధికారిక ప్రాప్యత",
            "Distance": "దూరం",
            "Authorized Partner": "అధికారిక భాగస్వామి",
            "Common Service Center (CSC)": "మీసేవ / కామన్ సర్వీస్ సెంటర్ (CSC)",
            "District Industries Centre (DIC)": "జిల్లా పరిశ్రమల కేంద్రం (DIC)",
            "Official Application Portal": "అధికారిక దరఖాస్తు పోర్టల్",
            "Redirecting to Official Portal": "ప్రభుత్వ పోర్టల్‌కు మళ్లించబడుతోంది",
            "All Categories": "అన్ని విభాగాలు",
            "All Ministries": "అన్ని మంత్రిత్వ శాఖలు",
            "All Financial Types": "అన్ని ఆర్థిక రకాలు",
            "All Beneficiaries": "అందరు లబ్ధిదారులు",
            "Active Filters": "క్రియాశీల ఫిల్టర్లు"
        },
        "gu": {
            "Apply": "અરજી કરો", "Cancel": "રદ કરો", "Delete": "કાઢી નાખો", "Details": "વિગતો", "Edit": "સંપાદિત કરો",
            "Save": "સાચવો", "Search": "શોધો", "Back": "પાછા", "Next": "આગળ", "Submit": "સબમિટ કરો",
            "Calculate": "ગણતરી કરો", "Compare": "સરખામણી કરો", "Close": "બંધ કરો", "Loading": "લોડ થઈ રહ્યું છે...",
            "Calculate EMI & Subsidy": "ઈએમઆઈ અને સબસિડી ગણો",
            "Calculation is indicative based on official scheme": "સરકારી નિયમો મુજબ આ ગણતરી માત્ર માર્ગદર્શક છે",
            "Net Beneficiary Burden": "લાભાર્થીનો કુલ ખર્ચ",
            "Requested Loan Amount (?)": "માંગેલ લોનની રકમ (₹)",
            "Total Project Cost (?)": "કુલ પ્રોજેક્ટ ખર્ચ (₹)",
            "Estimated Govt Subsidy": "અંદાજિત સરકારી સબસિડી",
            "Active Applications": "સક્રિય અરજીઓ",
            "Approved": "મંજૂર થયેલ",
            "Check Eligibility": "પાત્રતા તપાસો",
            "Carry Original Documents": "અસલ દસ્તાવેજો સાથે રાખો",
            "Mandatory Documents": "ફરજિયાત દસ્તાવેજો",
            "Conditional Documents": "શરતી દસ્તાવેજો",
            "Official Requirement": "સત્તાવાર શરતો",
            "Page Not Found": "પેજ મળ્યું નથી",
            "Something went wrong": "કંઈક ખોટું થયું",
            "Unauthorized": "અનધિકૃત પ્રવેશ",
            "Distance": "અંતર",
            "Authorized Partner": "અધિકૃત પાર્ટનર",
            "Common Service Center (CSC)": "જન સેવા કેન્દ્ર (CSC)",
            "District Industries Centre (DIC)": "જિલ્લા ઉદ્યોગ કેન્દ્ર (DIC)",
            "Official Application Portal": "સત્તાવાર અરજી પોર્ટલ",
            "Redirecting to Official Portal": "સરકારી પોર્ટલ પર લઈ જવામાં આવી રહ્યા છે",
            "All Categories": "બધી કેટેગરી",
            "All Ministries": "બધા મંત્રાલયો",
            "All Financial Types": "બધા નાણાકીય પ્રકાર",
            "All Beneficiaries": "બધા લાભાર્થીઓ",
            "Active Filters": "સક્રિય ફિલ્ટર્સ"
        },
        "kn": {
            "Apply": "ಅರ್ಜಿ ಸಲ್ಲಿಸಿ", "Cancel": "ರದ್ದುಮಾಡಿ", "Delete": "ಅಳಿಸಿ", "Details": "ವಿವರಗಳು", "Edit": "ತಿದ್ದು",
            "Save": "ಉಳಿಸಿ", "Search": "ಹುಡುಕಿ", "Back": "ಹಿಂದೆ", "Next": "ಮುಂದೆ", "Submit": "ಸಲ್ಲಿಸಿ",
            "Calculate": "ಲೆಕ್ಕಹಾಕಿ", "Compare": "ಹೋಲಿಕೆ ಮಾಡಿ", "Close": "ಮುಚ್ಚಿ", "Loading": "ಲೋಡ್ ಆಗುತ್ತಿದೆ...",
            "Calculate EMI & Subsidy": "ಇಎಂಐ ಮತ್ತು ಸಬ್ಸಿಡಿ ಲೆಕ್ಕಹಾಕಿ",
            "Calculation is indicative based on official scheme": "ಸರ್ಕಾರಿ ನಿಯಮಗಳ ಪ್ರಕಾರ ಈ ಲೆಕ್ಕಾಚಾರವು ಸಾಂಕೇತಿಕವಾಗಿದೆ",
            "Net Beneficiary Burden": "ಫಲಾನುಭವಿಯ ನಿವ್ವಳ ಹೊರೆ",
            "Requested Loan Amount (?)": "ಕೋರಿದ ಸಾಲದ ಮೊತ್ತ (₹)",
            "Total Project Cost (?)": "ಒಟ್ಟು ಯೋಜನಾ ವೆಚ್ಚ (₹)",
            "Estimated Govt Subsidy": "ಅಂದಾಜು ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿ",
            "Active Applications": "ಸಕ್ರಿಯ ಅರ್ಜಿಗಳು",
            "Approved": "ಅನುಮೋದಿಸಲಾಗಿದೆ",
            "Check Eligibility": "ಅರ್ಹತೆಯನ್ನು ಪರಿಶೀಲಿಸಿ",
            "Carry Original Documents": "ಮೂಲ ದಾಖಲೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡು ಹೋಗಿ",
            "Mandatory Documents": "ಕಡ್ಡಾಯ ದಾಖಲೆಗಳು",
            "Conditional Documents": "ಷರತ್ತುಬದ್ಧ ದಾಖಲೆಗಳು",
            "Official Requirement": "ಅಧಿಕೃತ ನಿಯಮಗಳು",
            "Page Not Found": "ಪುಟ ಕಂಡುಬಂದಿಲ್ಲ",
            "Something went wrong": "ಏನೋ ತಪ್ಪಾಗಿದೆ",
            "Unauthorized": "ಅನಧಿಕೃತ ಪ್ರವೇಶ",
            "Distance": "ದೂರ",
            "Authorized Partner": "ಅಧಿಕೃತ ಪಾಲುದಾರ",
            "Common Service Center (CSC)": "ಗ್ರಾಮ ಒನ್ / ಸಾಮಾನ್ಯ ಸೇವಾ ಕೇಂದ್ರ (CSC)",
            "District Industries Centre (DIC)": "ಜಿಲ್ಲಾ ಕೈಗಾರಿಕಾ ಕೇಂದ್ರ (DIC)",
            "Official Application Portal": "ಅಧಿಕೃತ ಅರ್ಜಿ ಪೋರ್ಟಲ್",
            "Redirecting to Official Portal": "ಸರ್ಕಾರಿ ಪೋರ್ಟಲ್‌ಗೆ ಮರುನಿರ್ದೇಶಿಸಲಾಗುತ್ತಿದೆ",
            "All Categories": "ಎಲ್ಲಾ ವರ್ಗಗಳು",
            "All Ministries": "ಎಲ್ಲಾ ಸಚಿವಾಲಯಗಳು",
            "All Financial Types": "ಎಲ್ಲಾ ಹಣಕಾಸು ಪ್ರಕಾರಗಳು",
            "All Beneficiaries": "ಎಲ್ಲಾ ಫಲಾನುಭವಿಗಳು",
            "Active Filters": "ಸಕ್ರಿಯ ಫಿಲ್ಟರ್‌ಗಳು"
        },
        "ml": {
            "Apply": "അപേക്ഷിക്കുക", "Cancel": "റദ്ദാക്കുക", "Delete": "ഡിലീറ്റ് ചെയ്യുക", "Details": "വിശദാംശങ്ങൾ", "Edit": "മാറ്റുക",
            "Save": "സേവ് ചെയ്യുക", "Search": "തിരയുക", "Back": "പിന്നോട്ട്", "Next": "അടുത്തത്", "Submit": "സമർപ്പിക്കുക",
            "Calculate": "കണക്കാക്കുക", "Compare": "താരതമ്യം ചെയ്യുക", "Close": "അടയ്ക്കുക", "Loading": "ലോഡ് ചെയ്യുന്നു...",
            "Calculate EMI & Subsidy": "ഇഎംഐയും സബ്‌സിഡിയും കണക്കാക്കുക",
            "Calculation is indicative based on official scheme": "സർക്കാർ നിയമങ്ങൾ അടിസ്ഥാനമാക്കിയുള്ളതാണ് ഈ കണക്കുകൂട്ടൽ",
            "Net Beneficiary Burden": "ഗുണഭോക്താവിന്റെ ചെലവ്",
            "Requested Loan Amount (?)": "ആവശ്യമായ വായ്പ തുക (₹)",
            "Total Project Cost (?)": "ആകെ പദ്ധതി ചെലവ് (₹)",
            "Estimated Govt Subsidy": "പ്രതീക്ഷിക്കുന്ന സർക്കാർ സബ്‌സിഡി",
            "Active Applications": "സജീവ അപേക്ഷകൾ",
            "Approved": "അംഗീകരിച്ചു",
            "Check Eligibility": "അർഹത പരിശോധിക്കുക",
            "Carry Original Documents": "അസൽ രേഖകൾ കൈവശം വയ്ക്കുക",
            "Mandatory Documents": "നിർബന്ധിത രേഖകൾ",
            "Conditional Documents": "വ്യവസ്ഥകൾക്ക് വിധേയമായ രേഖകൾ",
            "Official Requirement": "ഔദ്യോഗിക നിബന്ധനകൾ",
            "Page Not Found": "പേജ് കണ്ടെത്തിയില്ല",
            "Something went wrong": "എന്തോ കുഴപ്പമുണ്ടായി",
            "Unauthorized": "അനധികൃത പ്രവേശനം",
            "Distance": "ദൂരം",
            "Authorized Partner": "അംഗീകൃത പങ്കാളി",
            "Common Service Center (CSC)": "അക്ഷയ / പൊതു സേവന കേന്ദ്രം (CSC)",
            "District Industries Centre (DIC)": "ജില്ലാ വ്യവസായ കേന്ദ്രം (DIC)",
            "Official Application Portal": "ഔദ്യോഗിക അപേക്ഷാ പോർട്ടൽ",
            "Redirecting to Official Portal": "ഔദ്യോഗിക പോർട്ടലിലേക്ക് റീഡയറക്റ്റ് ചെയ്യുന്നു",
            "All Categories": "എല്ലാ വിഭാഗങ്ങളും",
            "All Ministries": "എല്ലാ മന്ത്രാലയങ്ങളും",
            "All Financial Types": "എല്ലാ സാമ്പത്തിക തരങ്ങളും",
            "All Beneficiaries": "എല്ലാ ഗുണഭോക്താക്കളും",
            "Active Filters": "ഫിൽട്ടറുകൾ"
        },
        "pa": {
            "Apply": "ਅਰਜ਼ੀ ਦਿਓ", "Cancel": "ਰੱਦ ਕਰੋ", "Delete": "ਮਿਟਾਓ", "Details": "ਵੇਰਵੇ", "Edit": "ਸੋਧੋ",
            "Save": "ਸੰਭਾਲੋ", "Search": "ਖੋਜੋ", "Back": "ਪਿੱਛੇ", "Next": "ਅੱਗੇ", "Submit": "ਜਮ੍ਹਾਂ ਕਰੋ",
            "Calculate": "ਗਣਨਾ ਕਰੋ", "Compare": "ਤੁਲਨਾ ਕਰੋ", "Close": "ਬੰਦ ਕਰੋ", "Loading": "ਲੋਡ ਹੋ ਰਿਹਾ ਹੈ...",
            "Calculate EMI & Subsidy": "ਈਐਮਆਈ ਅਤੇ ਸਬਸਿਡੀ ਦੀ ਗਣਨਾ ਕਰੋ",
            "Calculation is indicative based on official scheme": "ਸਰਕਾਰੀ ਨਿਯਮਾਂ ਅਨੁਸਾਰ ਇਹ ਗਣਨਾ ਸੰਕੇਤਕ ਹੈ",
            "Net Beneficiary Burden": "ਲਾਭਪਾਤਰੀ ਦਾ ਕੁੱਲ ਖਰਚ",
            "Requested Loan Amount (?)": "ਲੋੜੀਂਦੀ ਕਰਜ਼ਾ ਰਕਮ (₹)",
            "Total Project Cost (?)": "ਕੁੱਲ ਪ੍ਰੋਜੈਕਟ ਲਾਗਤ (₹)",
            "Estimated Govt Subsidy": "ਅੰਦਾਜ਼ਨ ਸਰਕਾਰੀ ਸਬਸਿਡੀ",
            "Active Applications": "ਸਰਗਰਮ ਅਰਜ਼ੀਆਂ",
            "Approved": "ਮਨਜ਼ੂਰਸ਼ੁਦਾ",
            "Check Eligibility": "ਯੋਗਤਾ ਦੀ ਜਾਂਚ ਕਰੋ",
            "Carry Original Documents": "ਅਸਲ ਦਸਤਾਵੇਜ਼ ਨਾਲ ਰੱਖੋ",
            "Mandatory Documents": "ਲਾਜ਼ਮੀ ਦਸਤਾਵੇਜ਼",
            "Conditional Documents": "ਸ਼ਰਤੀਆ ਦਸਤਾਵੇਜ਼",
            "Official Requirement": "ਅਧਿਕਾਰਤ ਲੋੜਾਂ",
            "Page Not Found": "ਸਫ਼ਾ ਨਹੀਂ ਮਿਲਿਆ",
            "Something went wrong": "ਕੁਝ ਗਲਤ ਹੋ ਗਿਆ",
            "Unauthorized": "ਅਣਅਧਿਕਾਰਤ ਪਹੁੰਚ",
            "Distance": "ਦੂਰੀ",
            "Authorized Partner": "ਅਧਿਕਾਰਤ ਸਾਥੀ",
            "Common Service Center (CSC)": "ਸੇਵਾ ਕੇਂਦਰ (CSC)",
            "District Industries Centre (DIC)": "ਜ਼ਿਲ੍ਹਾ ਉਦਯੋਗ ਕੇਂਦਰ (DIC)",
            "Official Application Portal": "ਅਧਿਕਾਰਤ ਅਰਜ਼ੀ ਪੋਰਟਲ",
            "Redirecting to Official Portal": "ਸਰਕਾਰੀ ਪੋਰਟਲ 'ਤੇ ਰੀਡਾਇਰੈਕਟ ਕੀਤਾ ਜਾ ਰਿਹਾ ਹੈ",
            "All Categories": "ਸਾਰੀਆਂ ਸ਼੍ਰੇਣੀਆਂ",
            "All Ministries": "ਸਾਰੇ ਮੰਤਰਾਲੇ",
            "All Financial Types": "ਸਾਰੀਆਂ ਵਿੱਤੀ ਕਿਸਮਾਂ",
            "All Beneficiaries": "ਸਾਰੇ ਲਾਭਪਾਤਰੀ",
            "Active Filters": "ਫਿਲਟਰ"
        },
        "or": {
            "Apply": "ଆବେଦନ କରନ୍ତୁ", "Cancel": "ବାତିଲ୍", "Delete": "ଡିଲିଟ୍", "Details": "ବିବରଣୀ", "Edit": "ସମ୍ପାଦନ",
            "Save": "ସଂରକ୍ଷଣ", "Search": "ସନ୍ଧାନ", "Back": "ପଛକୁ", "Next": "ପରବର୍ତ୍ତୀ", "Submit": "ଦାଖଲ କରନ୍ତୁ",
            "Calculate": "ଗଣନା କରନ୍ତୁ", "Compare": "ତୁଳନା କରନ୍ତୁ", "Close": "ବନ୍ଦ କରନ୍ତୁ", "Loading": "ଲୋଡ୍ ହେଉଛି...",
            "Calculate EMI & Subsidy": "ଇଏମଆଇ ଏବଂ ସବସିଡି ଗଣନା କରନ୍ତୁ",
            "Calculation is indicative based on official scheme": "ସରକାରୀ ନିୟମ ଅନୁଯାୟୀ ଏହି ଗଣନା ସୂଚକ ଅଟେ",
            "Net Beneficiary Burden": "ହିତାଧିକାରୀଙ୍କ ମୋଟ ଖର୍ଚ୍ଚ",
            "Requested Loan Amount (?)": "ଆବଶ୍ୟକ ଋଣ ରାଶି (₹)",
            "Total Project Cost (?)": "ମୋଟ ପ୍ରକଳ୍ପ ଖର୍ଚ୍ଚ (₹)",
            "Estimated Govt Subsidy": "ଆନୁମାନିକ ସରକାରୀ ସବସିଡି",
            "Active Applications": "ସକ୍ରିୟ ଆବେଦନ",
            "Approved": "ଅନୁମୋଦିତ",
            "Check Eligibility": "ଯୋଗ୍ୟତା ଯାଞ୍ଚ କରନ୍ତୁ",
            "Carry Original Documents": "ମୂଳ ଦସ୍ତାବିଜ ସାଥିରେ ନିଅନ୍ତୁ",
            "Mandatory Documents": "ବାଧ୍ୟତାମୂଳକ ଦସ୍ତାବିଜ",
            "Conditional Documents": "ସର୍ତ୍ତମୂଳକ ଦସ୍ତାବିଜ",
            "Official Requirement": "ସରକାରୀ ଆବଶ୍ୟକତା",
            "Page Not Found": "ପୃଷ୍ଠା ମିଳିଲା ନାହିଁ",
            "Something went wrong": "କିଛି ଭୁଲ୍ ହେଲା",
            "Unauthorized": "ଅନଧିକୃତ ପ୍ରବେଶ",
            "Distance": "ଦୂରତା",
            "Authorized Partner": "ଅଧିକୃତ ଅଂଶୀଦାର",
            "Common Service Center (CSC)": "ଜନ ସେବା କେନ୍ଦ୍ର (CSC)",
            "District Industries Centre (DIC)": "ଜିଲ୍ଲା ଶିଳ୍ପ କେନ୍ଦ୍ର (DIC)",
            "Official Application Portal": "ସରକାରୀ ଆବେଦନ ପୋର୍ଟାଲ",
            "Redirecting to Official Portal": "ସରକାରୀ ପୋର୍ଟାଲକୁ ନିଆଯାଉଛି",
            "All Categories": "ସମସ୍ତ ବର୍ଗ",
            "All Ministries": "ସମସ୍ତ ମନ୍ତ୍ରଣାଳୟ",
            "All Financial Types": "ସମସ୍ତ ଆର୍ଥିକ ପ୍ରକାର",
            "All Beneficiaries": "ସମସ୍ତ ହିତାଧିକାରୀ",
            "Active Filters": "ଫିଲ୍ଟର"
        },
        "as": {
            "Apply": "আবেদন কৰক", "Cancel": "বাতিল", "Delete": "মচি পেলাওক", "Details": "বিৱৰণ", "Edit": "সম্পাদনা",
            "Save": "সংৰক্ষণ", "Search": "সন্ধান", "Back": "পিছলৈ", "Next": "পৰৱৰ্তী", "Submit": "দাখিল কৰক",
            "Calculate": "হিচাপ কৰক", "Compare": "তুলনা কৰক", "Close": "বন্ধ কৰক", "Loading": "ল'ড হৈ আছে...",
            "Calculate EMI & Subsidy": "ইএমআই আৰু ৰাজসাহায্যৰ হিচাপ কৰক",
            "Calculation is indicative based on official scheme": "চৰকাৰী নিয়মৰ ওপৰত ভিত্তি কৰি এই হিচাপ সূচকীয়",
            "Net Beneficiary Burden": "হিতাধিকাৰীৰ মুঠ ব্যয়",
            "Requested Loan Amount (?)": "প্ৰয়োজনীয় ঋণৰ পৰિমাণ (₹)",
            "Total Project Cost (?)": "মুঠ প্ৰকল্প ব্যয় (₹)",
            "Estimated Govt Subsidy": "আনুমানিক চৰকাৰী ৰাজসাহায্য",
            "Active Applications": "সক্ৰিয় আবেদনসমূহ",
            "Approved": "অনুমোদিত",
            "Check Eligibility": "যোগ্যতা পৰীক্ষা কৰক",
            "Carry Original Documents": "মূল নথি লগত ৰাখক",
            "Mandatory Documents": "বাধ্যতামূলক নথি",
            "Conditional Documents": "চৰ্তসাপেক্ষ নথি",
            "Official Requirement": "আনুষ্ঠানিক চৰ্ত",
            "Page Not Found": "পৃষ্ঠা পোৱা নগ'ল",
            "Something went wrong": "কিবা ভুল হ'ল",
            "Unauthorized": "অননুমোদিত প্ৰৱেশ",
            "Distance": "দূৰত্ব",
            "Authorized Partner": "অনুমোদিত অংশীদাৰ",
            "Common Service Center (CSC)": "সাধাৰণ সেৱা কেন্দ্ৰ (CSC)",
            "District Industries Centre (DIC)": "জিলা উদ্যোগ কেন্দ্ৰ (DIC)",
            "Official Application Portal": "আনুষ্ঠানিক আবেদন পৰ্টেল",
            "Redirecting to Official Portal": "চৰকাৰী পৰ্টেললৈ লৈ যোৱা হৈছে",
            "All Categories": "সকলো শ্ৰেণী",
            "All Ministries": "সকলো মন্ত্ৰালয়",
            "All Financial Types": "সকলো বিত্তীয় প্ৰকাৰ",
            "All Beneficiaries": "সকলো হিতাধিকাৰী",
            "Active Filters": "সক্ৰিয় ফিল্টাৰ"
        }
    }

    # For each non-English locale, find untranslated keys and replace with appropriate vocabulary
    for lang in ["bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]:
        path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        vocab = VOCAB.get(lang, {})

        def replace_recursively(target_dict, en_dict):
            for k, v in en_dict.items():
                if isinstance(v, dict):
                    if k in target_dict and isinstance(target_dict[k], dict):
                        replace_recursively(target_dict[k], v)
                elif isinstance(v, str):
                    cur_val = target_dict.get(k)
                    if cur_val == v: # Identical to English
                        # Check direct vocab match
                        if v in vocab:
                            target_dict[k] = vocab[v]
                        else:
                            # Try prefix / partial replacements
                            for en_term, trans in vocab.items():
                                if en_term.lower() == v.lower():
                                    target_dict[k] = trans
                                    break

        replace_recursively(data, en)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Filled vocabulary for {lang}.json")

if __name__ == "__main__":
    run()
