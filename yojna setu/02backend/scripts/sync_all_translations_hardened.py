"""
Comprehensive script to harden translations across all 12 locales:
en, hi, bn, mr, ta, te, gu, kn, ml, pa, or, as.

Fixes:
1. All 33 literal raw keys (auth.emailLabel, calculator.loanAmount, etc.)
2. New semantic Home page hierarchy keys
3. Citizen-facing applications and profile keys in all 11 non-English locales
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")

# Core keys to inject/update across locales
TRANSLATION_PACK = {
    "en": {
        "home": {
            "findMatchingSchemes": "Find Matching Schemes",
            "exploreAllSchemes": "Explore All Schemes",
            "matchingFlow": "Personalized Scheme Matching",
            "smartMatchingTitle": "Find Government Schemes You May Be Eligible For",
            "smartMatchingDescription": "Answer a few questions about your age, category, location, occupation and business needs. YojnaSetu checks your profile against official scheme eligibility rules.",
            "personalizedMatching": "Personalized scheme matching",
            "ruleBasedEligibility": "Rule-based eligibility checks",
            "officialSources": "Official government sources",
            "noDocumentUpload": "No document upload required",
            "howItWorksTitle": "How YojnaSetu Works",
            "howItWorksSub": "A transparent 4-step path to discover schemes you may qualify for and access official application routes.",
            "stepTellUs": "Tell us about yourself",
            "stepTellUsDesc": "Share basic profile details like your age, social category, location, and vocation in complete privacy.",
            "stepCheckEligibility": "Check eligibility",
            "stepCheckEligibilityDesc": "Our deterministic engine evaluates official statutory scheme criteria against your profile.",
            "stepDiscoverSchemes": "Discover matching schemes",
            "stepDiscoverSchemesDesc": "Receive a curated list of government schemes with transparent match reasons and financial benefits.",
            "stepOfficialRoute": "Follow official application route",
            "stepOfficialRouteDesc": "Apply directly on official ministry portals or locate verified local channel partner assistance centers.",
            "exploreByCategory": "Explore Schemes by Category",
            "exploreByCategorySub": "Browse verified government welfare portfolios organized by sector and trade.",
            "trustBadge": "Official Information Architecture",
            "trustTitle": "Directly Sourced from Official Government Gazettes & Portfolios",
            "trustDesc": "YojnaSetu operates as an independent civic-tech portal providing deterministic eligibility guidance derived from published ministry guidelines, official portals, and authorized channel partner directories.",
            "trustPillar1": "Gazette Verified",
            "trustPillar1Desc": "Every scheme mapped to published ministry notifications and official source citations.",
            "trustPillar2": "Deterministic Rule Engine",
            "trustPillar2Desc": "Transparent criteria evaluations without black-box estimation or guesswork.",
            "trustPillar3": "Authorized Channel Partners",
            "trustPillar3Desc": "120+ verified state channelizing agencies, bank branches, and facilitation centers.",
            "trustPillar4": "Privacy First",
            "trustPillar4Desc": "Zero PII or document uploads required to discover and compare schemes.",
            "finalCtaTitle": "Ready to Discover Schemes You May Be Eligible For?",
            "finalCtaSubtitle": "Takes less than 2 minutes. Answer a few questions to get personalized government scheme guidance.",
            "finalCtaButton": "Find Matching Schemes",
            "popularTitle": "Popular Search Themes",
            "viewAllSchemes": "Explore All Schemes",
            "quickStats": {
                "citizensServed": "Citizens Guided",
                "financialTools": "Financial Calculators",
                "schemesCount": "Verified Schemes"
            }
        },
        "auth": {
            "emailLabel": "Email Address",
            "loginButton": "Sign In",
            "passwordLabel": "Password",
            "phoneLabel": "Mobile Number",
            "registerButton": "Create Account"
        },
        "calculator": {
            "calculateButton": "Calculate Benefits & EMI",
            "limitWarning": "Exceeds Maximum Loan Amount",
            "loanAmount": "Loan Amount (₹)",
            "monthlyEMI": "Estimated Monthly EMI",
            "subsidyEstimate": "Estimated Capital Subsidy"
        },
        "footer": {
            "copyright": "All Rights Reserved. Official Civic-Tech Initiative."
        },
        "recommendations": {
            "breakdownLabel": "Eligibility Breakdown",
            "formAge": "Your Age (Years)",
            "formCategory": "Social Category",
            "formGender": "Gender",
            "formIncome": "Annual Household Income (₹)",
            "formOccupation": "Occupation / Trade",
            "formState": "State / Union Territory",
            "scoreLabel": "Match Score",
            "submitForm": "Find Matching Schemes",
            "threeWaysTitle": "Three Pathways to Discover Schemes"
        },
        "schemes": {
            "benefitTitle": "Financial Benefits & Assistance",
            "docsTitle": "Required Documents & Proofs",
            "eligibilityTitle": "Eligibility Criteria & Conditions",
            "officialPortal": "Official Application Portal",
            "saveScheme": "Save Scheme",
            "saved": "Saved to Portfolio",
            "verifiedBadge": "Verified Official Scheme"
        },
        "applications": {
            "appId": "Application ID",
            "lastUpdated": "Last Updated",
            "scheme": "Scheme",
            "status": "Status",
            "viewDetails": "View Details"
        }
    },
    "hi": {
        "home": {
            "findMatchingSchemes": "मिलान योजनाएं खोजें",
            "exploreAllSchemes": "सभी योजनाएं देखें",
            "matchingFlow": "व्यक्तिगत योजना मिलान",
            "smartMatchingTitle": "वे सरकारी योजनाएं खोजें जिनके लिए आप पात्र हो सकते हैं",
            "smartMatchingDescription": "अपनी आयु, वर्ग, स्थान, व्यवसाय और उद्यम आवश्यकताओं के बारे में कुछ सरल प्रश्नों के उत्तर दें। योजनासेतु आधिकारिक पात्रता नियमों के अनुसार आपका मिलान करता है।",
            "personalizedMatching": "व्यक्तिगत योजना मिलान",
            "ruleBasedEligibility": "नियम-आधारित पात्रता जांच",
            "officialSources": "आधिकारिक सरकारी स्रोत",
            "noDocumentUpload": "दस्तावेज अपलोड की आवश्यकता नहीं",
            "howItWorksTitle": "योजनासेतु कैसे काम करता है",
            "howItWorksSub": "योजनाओं को खोजने और आधिकारिक आवेदन मार्ग तक पहुंचने की 4-चरणीय पारदर्शी प्रक्रिया।",
            "stepTellUs": "अपने बारे में बताएं",
            "stepTellUsDesc": "बिना किसी दस्तावेज के पूर्ण गोपनीयता के साथ अपनी आयु, सामाजिक वर्ग, राज्य और व्यवसाय साझा करें।",
            "stepCheckEligibility": "पात्रता जांचें",
            "stepCheckEligibilityDesc": "हमारा नियम-आधारित इंजन आपकी जानकारी का आधिकारिक सरकारी मानदंडों से मिलान करता है।",
            "stepDiscoverSchemes": "मिलान योजनाएं पाएं",
            "stepDiscoverSchemesDesc": "स्पष्ट कारणों और वित्तीय लाभों के साथ अपने लिए उपयुक्त योजनाओं की सूची प्राप्त करें।",
            "stepOfficialRoute": "आधिकारिक आवेदन प्रक्रिया अपनाएं",
            "stepOfficialRouteDesc": "सीधे आधिकारिक मंत्रालय पोर्टल पर आवेदन करें या अधिकृत स्थानीय चैनल भागीदार केंद्र खोजें।",
            "exploreByCategory": "श्रेणी अनुसार योजनाएं देखें",
            "exploreByCategorySub": "विभिन्न क्षेत्रों और व्यवसायों के अनुसार आयोजित सरकारी कल्याणकारी योजनाएं देखें।",
            "trustBadge": "आधिकारिक सूचना प्रणाली",
            "trustTitle": "आधिकारिक सरकारी गजट और पोर्टलों से सीधे सत्यापित",
            "trustDesc": "योजनासेतु एक स्वतंत्र नागरिक-तकनीक पोर्टल है जो आधिकारिक मंत्रालय दिशानिर्देशों और पोर्टलों से सत्यापित पात्रता मार्गदर्शन प्रदान करता है।",
            "trustPillar1": "गजट द्वारा सत्यापित",
            "trustPillar1Desc": "प्रत्येक योजना आधिकारिक मंत्रालय अधिसूचनाओं और उद्धरणों से सत्यापित है।",
            "trustPillar2": "नियम-आधारित इंजन",
            "trustPillar2Desc": "वैधानिक मानदंडों पर आधारित पारदर्शी पात्रता मूल्यांकन।",
            "trustPillar3": "अधिकृत चैनल भागीदार",
            "trustPillar3Desc": "120+ सत्यापित राज्य एजेंसियां, बैंक शाखाएं और नागरिक सुविधा केंद्र।",
            "trustPillar4": "पूर्ण गोपनीयता",
            "trustPillar4Desc": "योजनाएं खोजने के लिए किसी व्यक्तिगत दस्तावेज या आधार अपलोड की आवश्यकता नहीं।",
            "finalCtaTitle": "क्या आप अपने लिए उपयुक्त योजनाएं खोजने के लिए तैयार हैं?",
            "finalCtaSubtitle": "2 मिनट से भी कम समय लगता है। व्यक्तिगत सरकारी योजना मार्गदर्शन पाने के लिए उत्तर दें।",
            "finalCtaButton": "मिलान योजनाएं खोजें",
            "popularTitle": "लोकप्रिय खोज विषय",
            "viewAllSchemes": "सभी योजनाएं देखें",
            "quickStats": {
                "citizensServed": "मार्गदर्शन प्राप्त नागरिक",
                "financialTools": "वित्तीय कैलकुलेटर",
                "schemesCount": "सत्यापित योजनाएं"
            }
        },
        "auth": {
            "emailLabel": "ईमेल पता",
            "loginButton": "लॉगिन करें",
            "passwordLabel": "पासवर्ड",
            "phoneLabel": "मोबाइल नंबर",
            "registerButton": "खाता बनाएं"
        },
        "calculator": {
            "calculateButton": "ईएमआई और लाभ की गणना करें",
            "limitWarning": "अधिकतम ऋण सीमा से अधिक",
            "loanAmount": "ऋण राशि (₹)",
            "monthlyEMI": "अनुमानित मासिक ईएमआई",
            "subsidyEstimate": "अनुमानित पूंजी सब्सिडी"
        },
        "footer": {
            "copyright": "सर्वाधिकार सुरक्षित। आधिकारिक नागरिक-तकनीक पहल।"
        },
        "recommendations": {
            "breakdownLabel": "पात्रता विवरण",
            "formAge": "आपकी आयु (वर्ष)",
            "formCategory": "सामाजिक वर्ग",
            "formGender": "लिंग",
            "formIncome": "वार्षिक पारिवारिक आय (₹)",
            "formOccupation": "व्यवसाय / कार्य",
            "formState": "राज्य / केंद्र शासित प्रदेश",
            "scoreLabel": "मिलान स्कोर",
            "submitForm": "मिलान योजनाएं खोजें",
            "threeWaysTitle": "योजनाएं खोजने के 3 तरीके"
        },
        "schemes": {
            "benefitTitle": "वित्तीय लाभ एवं सहायता",
            "docsTitle": "आवश्यक दस्तावेज एवं प्रमाण",
            "eligibilityTitle": "पात्रता मानदंड एवं शर्तें",
            "officialPortal": "आधिकारिक आवेदन पोर्टल",
            "saveScheme": "योजना सहेजें",
            "saved": "सहेजी गई",
            "verifiedBadge": "सत्यापित आधिकारिक योजना"
        },
        "applications": {
            "appId": "आवेदन आईडी",
            "lastUpdated": "अंतिम अद्यतन",
            "scheme": "योजना",
            "status": "स्थिति",
            "viewDetails": "विवरण देखें"
        }
    },
    "bn": {
        "home": {
            "findMatchingSchemes": "উপযুক্ত প্রকল্প খুঁজুন",
            "exploreAllSchemes": "সকল প্রকল্প দেখুন",
            "matchingFlow": "ব্যক্তিগতকৃত প্রকল্প মিলানো",
            "smartMatchingTitle": "আপনি যে সরকারি প্রকল্পগুলির যোগ্য হতে পারেন তা খুঁজুন",
            "smartMatchingDescription": "আপনার বয়স, বিভাগ, রাজ্য, পেশা এবং ব্যবসার চাহিদা সম্পর্কে কয়েকটি প্রশ্নের উত্তর দিন। যোজনাসেতু সরকারি নিয়ম অনুসারে আপনার যোগ্যতা যাচাই করে।",
            "personalizedMatching": "ব্যক্তিগতকৃত প্রকল্প মিলানো",
            "ruleBasedEligibility": "নিয়ম-ভিত্তিক যোগ্যতা যাচাই",
            "officialSources": "সরকারি দাপ্তরিক উৎস",
            "noDocumentUpload": "নথিপত্র আপলোড করার প্রয়োজন নেই",
            "howItWorksTitle": "যোজনাসেতু কীভাবে কাজ করে",
            "howItWorksSub": "প্রকল্প খুঁজে পাওয়ার এবং আবেদন করার ৪-ধাপের স্বচ্ছ প্রক্রিয়া।",
            "stepTellUs": "আপনার সম্পর্কে বলুন",
            "stepTellUsDesc": "নথিপত্র আপলোড না করেই সম্পূর্ণ গোপনীয়তায় আপনার বয়স, জাতিগত বিভাগ এবং পেশার তথ্য দিন।",
            "stepCheckEligibility": "যোগ্যতা যাচাই করুন",
            "stepCheckEligibilityDesc": "আমাদের অ্যালগরিদম সরকারি প্রকল্প শর্তের সাথে আপনার তথ্যের মিল খুঁজে বের করে।",
            "stepDiscoverSchemes": "উপযুক্ত প্রকল্প আবিষ্কার করুন",
            "stepDiscoverSchemesDesc": "স্বচ্ছ কারণ এবং আর্থিক সুবিধা সহ আপনার জন্য মানানসই প্রকল্পগুলির তালিকা পান।",
            "stepOfficialRoute": "দাপ্তরিক আবেদন পথ অনুসরণ করুন",
            "stepOfficialRouteDesc": "সরাসরি মন্ত্রণালয়ের পোর্টালে আবেদন করুন বা স্থানীয় অনুমোদিত সহায়তা কেন্দ্র খুঁজুন।",
            "exploreByCategory": "বিভাগ অনুসারে প্রকল্প অন্বেষণ করুন",
            "exploreByCategorySub": "বিভিন্ন খাত ও জীবিকার জন্য নির্দিষ্ট সরকারি কল্যাণমূলক পোর্টফোলিও দেখুন।",
            "trustBadge": "দাপ্তরিক তথ্য ব্যবস্থা",
            "trustTitle": "সরকারি গেজেট ও পোর্টাল থেকে সরাসরি যাচাইকৃত",
            "trustDesc": "যোজনাসেতু একটি স্বাধীন নাগরিক-প্রযুক্তি পোর্টাল যা সরকারি নির্দেশিকা থেকে সংগৃহীত নির্ভরযোগ্য তথ্য প্রদান করে।",
            "trustPillar1": "গেজেট যাচাইকৃত",
            "trustPillar1Desc": "প্রতিটি প্রকল্প প্রকাশিত মন্ত্রণালয়ের বিজ্ঞপ্তি থেকে যাচাইকৃত।",
            "trustPillar2": "নিয়ম-ভিত্তিক ইঞ্জিন",
            "trustPillar2Desc": "আইনগত শর্তাবলীর ওপর ভিত্তি করে স্বচ্ছ মূল্যায়ন।",
            "trustPillar3": "অনুমোদিত অংশীদার",
            "trustPillar3Desc": "১২০+ যাচাইকৃত রাজ্য সংস্থা, ব্যাংক শাখা এবং সহায়তা কেন্দ্র।",
            "trustPillar4": "গোপনীয়তা প্রথম",
            "trustPillar4Desc": "প্রকল্প খুঁজতে কোনো ব্যক্তিগত নথি বা আধার আপলোডের প্রয়োজন নেই।",
            "finalCtaTitle": "আপনার জন্য উপযুক্ত প্রকল্পগুলি আবিষ্কার করতে প্রস্তুত?",
            "finalCtaSubtitle": "২ মিনিটেরও কম সময় লাগে। ব্যক্তিগত নির্দেশিকা পেতে কয়েকটি প্রশ্নের উত্তর দিন।",
            "finalCtaButton": "উপযুক্ত প্রকল্প খুঁজুন",
            "popularTitle": "জনপ্রিয় অনুসন্ধানের বিষয়",
            "viewAllSchemes": "সকল প্রকল্প দেখুন",
            "quickStats": {
                "citizensServed": "সহায়তাপ্রাপ্ত নাগরিক",
                "financialTools": "আর্থিক ক্যালকুলেটর",
                "schemesCount": "যাচাইকৃত প্রকল্প"
            }
        },
        "auth": {
            "emailLabel": "ইমেল ঠিকানা",
            "loginButton": "লগইন করুন",
            "passwordLabel": "পাসওয়ার্ড",
            "phoneLabel": "মোবাইল নম্বর",
            "registerButton": "অ্যাকাউন্ট তৈরি করুন"
        },
        "calculator": {
            "calculateButton": "ইএমআই ও সুবিধা হিসাব করুন",
            "limitWarning": "সর্বোচ্চ ঋণসীমার অতিরিক্ত",
            "loanAmount": "ঋণের পরিমাণ (₹)",
            "monthlyEMI": "আনুমানিক মাসিক ইএমআই",
            "subsidyEstimate": "আনুমানিক মূলধন ভর্তুকি"
        },
        "footer": {
            "copyright": "সর্বস্বত্ব সংরক্ষিত। দাপ্তরিক নাগরিক প্রযুক্তি উদ্যোগ।"
        },
        "recommendations": {
            "breakdownLabel": "যোগ্যতার বিবরণ",
            "formAge": "আপনার বয়স (বছর)",
            "formCategory": "সামাজিক বিভাগ",
            "formGender": "লিঙ্গ",
            "formIncome": "বার্ষিক পারিবারিক আয় (₹)",
            "formOccupation": "পেশা / কাজ",
            "formState": "রাজ্য / কেন্দ্রশাসিত অঞ্চল",
            "scoreLabel": "ম্যাচ স্কোর",
            "submitForm": "উপযুক্ত প্রকল্প খুঁজুন",
            "threeWaysTitle": "প্রকল্প খোঁজার ৩টি উপায়"
        },
        "schemes": {
            "benefitTitle": "আর্থিক সুবিধা ও সহায়তা",
            "docsTitle": "প্রয়োজনীয় নথি ও প্রমাণ",
            "eligibilityTitle": "যোগ্যতার মানদণ্ড ও শর্তাবলী",
            "officialPortal": "দাপ্তরিক আবেদন পোর্টাল",
            "saveScheme": "প্রকল্প সংরক্ষণ করুন",
            "saved": "সংরক্ষিত",
            "verifiedBadge": "যাচাইকৃত দাপ্তরিক প্রকল্প"
        },
        "applications": {
            "appId": "আবেদন আইডি",
            "lastUpdated": "সর্বশেষ আপডেট",
            "scheme": "প্রকল্প",
            "status": "অবস্থা",
            "viewDetails": "বিস্তারিত দেখুন"
        }
    },
    "mr": {
        "home": {
            "findMatchingSchemes": "पात्र योजना शोधा",
            "exploreAllSchemes": "सर्व योजना पहा",
            "matchingFlow": "वैयक्तिकृत योजना जुळणी",
            "smartMatchingTitle": "तुम्ही ज्या सरकारी योजनांसाठी पात्र असू शकता त्या शोधा",
            "smartMatchingDescription": "तुमचे वय, वर्ग, राज्य, व्यवसाय आणि गरजा याबद्दल काही सोप्या प्रश्नांची उत्तरे द्या. योजनासेतू अधिकृत नियमांनुसार तुमची पात्रता तपासते.",
            "personalizedMatching": "वैयक्तिकृत योजना जुळणी",
            "ruleBasedEligibility": "नियम-आधारित पात्रता तपासणी",
            "officialSources": "अधिकृत सरकारी स्रोत",
            "noDocumentUpload": "कागदपत्र अपलोड करण्याची गरज नाही",
            "howItWorksTitle": "योजनासेतू कसे कार्य करते",
            "howItWorksSub": "योजना शोधण्याची आणि अधिकृत अर्जापर्यंत पोहोचण्याची पारदर्शक ४-टप्प्यांची प्रक्रिया.",
            "stepTellUs": "तुमच्याबद्दल सांगा",
            "stepTellUsDesc": "कागदपत्र अपलोड न करता पूर्ण गोपनीयतेत तुमचे वय, सामाजिक वर्ग, राज्य आणि व्यवसाय सांगा.",
            "stepCheckEligibility": "पात्रता तपासा",
            "stepCheckEligibilityDesc": "आमचे नियम-आधारित इंजिन सरकारी निकषांनुसार तुमची पात्रता तपासते.",
            "stepDiscoverSchemes": "पात्र योजना शोधा",
            "stepDiscoverSchemesDesc": "स्पष्ट कारणे आणि आर्थिक लाभांसह तुमच्यासाठी योग्य योजनांची यादी मिळवा.",
            "stepOfficialRoute": "अधिकृत अर्ज प्रक्रिया",
            "stepOfficialRouteDesc": "थेट अधिकृत मंत्रालयाच्या पोर्टलवर अर्ज करा किंवा अधिकृत स्थानिक मदत केंद्र शोधा.",
            "exploreByCategory": "श्रेणीनुसार योजना शोधा",
            "exploreByCategorySub": "विविध उद्योग आणि व्यवसायांसाठी तयार केलेल्या सरकारी कल्याणकारी योजना पहा.",
            "trustBadge": "अधिकृत माहिती प्रणाली",
            "trustTitle": "सरकारी राजपत्रातून आणि पोर्टलमधून थेट सत्यापित",
            "trustDesc": "योजनासेतू हे एक स्वतंत्र नागरिक-तंत्रज्ञान पोर्टल आहे जे अधिकृत मार्गदर्शक तत्त्वांवरून सत्यापित माहिती पुरवते.",
            "trustPillar1": "राजपत्र सत्यापित",
            "trustPillar1Desc": "प्रत्येक योजना प्रसिद्ध केलेल्या अधिकृत अधिसूचनेशी जोडलेली आहे.",
            "trustPillar2": "नियम-आधारित इंजिन",
            "trustPillar2Desc": "कायदेशीर निकषांवर आधारित पारदर्शक मूल्यांकन.",
            "trustPillar3": "अधिकृत भागीदार",
            "trustPillar3Desc": "१२०+ सत्यापित राज्य संस्था, बँक शाखा आणि मदत केंद्रे.",
            "trustPillar4": "गोपनीयतेला प्राधान्य",
            "trustPillar4Desc": "योजना शोधण्यासाठी वैयक्तिक कागदपत्रे किंवा आधार अपलोड आवश्यक नाही.",
            "finalCtaTitle": "तुमच्यासाठी योग्य योजना शोधण्यास तयार आहात?",
            "finalCtaSubtitle": "२ मिनिटांपेक्षा कमी वेळ लागतो. वैयक्तिक मार्गदर्शन मिळवण्यासाठी उत्तरे द्या.",
            "finalCtaButton": "पात्र योजना शोधा",
            "popularTitle": "लोकप्रिय शोध विषय",
            "viewAllSchemes": "सर्व योजना पहा",
            "quickStats": {
                "citizensServed": "मार्गदर्शन घेतलेले नागरिक",
                "financialTools": "आर्थिक कॅल्क्युलेटर",
                "schemesCount": "सत्यापित योजना"
            }
        },
        "auth": {
            "emailLabel": "ईमेल पत्ता",
            "loginButton": "लॉगिन करा",
            "passwordLabel": "पासवर्ड",
            "phoneLabel": "मोबाइल नंबर",
            "registerButton": "खाते तयार करा"
        },
        "calculator": {
            "calculateButton": "ईएमआय आणि लाभ मोजा",
            "limitWarning": "कमाल कर्ज मर्यादेपेक्षा जास्त",
            "loanAmount": "कर्ज रक्कम (₹)",
            "monthlyEMI": "अंदाजे मासिक ईएमआय",
            "subsidyEstimate": "अंदाजे भांडवली सबसिडी"
        },
        "footer": {
            "copyright": "सर्व हक्क राखीव. अधिकृत नागरिक-तंत्रज्ञान उपक्रम."
        },
        "recommendations": {
            "breakdownLabel": "पात्रता तपशील",
            "formAge": "तुमचे वय (वर्षे)",
            "formCategory": "सामाजिक प्रवर्ग",
            "formGender": "लिंग",
            "formIncome": "वार्षिक कौटुंबिक उत्पन्न (₹)",
            "formOccupation": "व्यवसाय / काम",
            "formState": "राज्य / केंद्रशासित प्रदेश",
            "scoreLabel": "मॅच स्कोअर",
            "submitForm": "पात्र योजना शोधा",
            "threeWaysTitle": "योजना शोधण्याचे ३ मार्ग"
        },
        "schemes": {
            "benefitTitle": "आर्थिक लाभ आणि सहाय्य",
            "docsTitle": "आवश्यक कागदपत्रे आणि पुरावे",
            "eligibilityTitle": "पात्रता निकष आणि अटी",
            "officialPortal": "अधिकृत अर्ज पोर्टल",
            "saveScheme": "योजना जतन करा",
            "saved": "जतन केले",
            "verifiedBadge": "सत्यापित अधिकृत योजना"
        },
        "applications": {
            "appId": "अर्ज आयडी",
            "lastUpdated": "शेवटचे अपडेट",
            "scheme": "योजना",
            "status": "स्थिती",
            "viewDetails": "तपशील पहा"
        }
    },
    "ta": {
        "home": {
            "findMatchingSchemes": "பொருத்தமான திட்டங்களைக் கண்டறியவும்",
            "exploreAllSchemes": "அனைத்து திட்டங்களையும் காண்க",
            "matchingFlow": "தனிப்பயனாக்கப்பட்ட திட்டப் பொருத்தம்",
            "smartMatchingTitle": "நீங்கள் தகுதிபெறக்கூடிய அரசுத் திட்டங்களைக் கண்டறியவும்",
            "smartMatchingDescription": "உங்கள் வயது, பிரிவு, இருப்பிடம், தொழில் மற்றும் வணிகத் தேவைகள் பற்றிய சில கேள்விகளுக்கு பதிலளிக்கவும். யோஜனாசேது அதிகாரப்பூர்வ விதிகளின்படி உங்கள் தகுதியைச் சரிபார்க்கிறது.",
            "personalizedMatching": "தனிப்பயனாக்கப்பட்ட திட்டப் பொருத்தம்",
            "ruleBasedEligibility": "விதிகள் அடிப்படையிலான தகுதிச் சரிபார்ப்பு",
            "officialSources": "அதிகாரப்பூர்வ அரசு ஆதாரங்கள்",
            "noDocumentUpload": "ஆவண பதிவேற்றம் தேவையில்லை",
            "howItWorksTitle": "யோஜனாசேது எவ்வாறு செயல்படுகிறது",
            "howItWorksSub": "திட்டங்களைக் கண்டறிந்து அதிகாரப்பூர்வமாக விண்ணப்பிப்பதற்கான எளிய 4 படி வழிமுறை.",
            "stepTellUs": "உங்களைப் பற்றி கூறுங்கள்",
            "stepTellUsDesc": "எந்த ஆவணமும் பதிவேற்றாமல் முழு தனியுரிமையுடன் உங்கள் விவரங்களைப் பகிரவும்.",
            "stepCheckEligibility": "தகுதியைச் சரிபார்க்கவும்",
            "stepCheckEligibilityDesc": "அரசுத் திட்ட விதிகளுடன் உங்கள் சுயவிவரத்தை எங்கள் விதி எஞ்சின் ஒப்பிடுகிறது.",
            "stepDiscoverSchemes": "பொருத்தமான திட்டங்களைப் பெறுங்கள்",
            "stepDiscoverSchemesDesc": "காரணங்கள் மற்றும் நிதிப் பலன்களுடன் உங்களுக்கான திட்டங்களின் பட்டியலைப் பெறுங்கள்.",
            "stepOfficialRoute": "அதிகாரப்பூர்வ விண்ணப்ப வழிமுறை",
            "stepOfficialRouteDesc": "அமைச்சக இணையதளத்தில் நேரடியாக விண்ணப்பிக்கவும் அல்லது உதவி மையங்களை அணுகவும்.",
            "exploreByCategory": "பிரிவு வாரியாகத் திட்டங்களை ஆராயுங்கள்",
            "exploreByCategorySub": "தொழில் மற்றும் துறை வாரியாக ஒழுங்கமைக்கப்பட்ட அரசு நலத்திட்டங்கள்.",
            "trustBadge": "அதிகாரப்பூர்வ தகவல் கட்டமைப்பு",
            "trustTitle": "அரசு அரசிதழ்கள் மற்றும் போர்ட்டல்களிலிருந்து சரிபார்க்கப்பட்டது",
            "trustDesc": "யோஜனாசேது என்பது அரசு வழிகாட்டுதல்களிலிருந்து பெறப்பட்ட தகுதி வழிகாட்டலை வழங்கும் குடிமக்கள்-தொழில்நுட்ப தளம்.",
            "trustPillar1": "அரசிதழ் சரிபார்க்கப்பட்டது",
            "trustPillar1Desc": "ஒவ்வொரு திட்டமும் வெளியிடப்பட்ட அதிகாரப்பூர்வ அறிவிப்புகளுடன் இணைக்கப்பட்டுள்ளது.",
            "trustPillar2": "விதிகள் சார்ந்த எஞ்சின்",
            "trustPillar2Desc": "வெளிப்படையான தகுதி மதிப்பீடுகள்.",
            "trustPillar3": "அங்கீகரிக்கப்பட்ட கூட்டாளர்கள்",
            "trustPillar3Desc": "120+ சரிபார்க்கப்பட்ட அரசு முகமைகள் மற்றும் வங்கி உதவி மையங்கள்.",
            "trustPillar4": "தனியுரிமை முதன்மை",
            "trustPillar4Desc": "திட்டங்களை அறிய தனிப்பட்ட ஆவணங்கள் அல்லது ஆதார் தேவையில்லை.",
            "finalCtaTitle": "உங்களுக்கான அரசுத் திட்டங்களைக் கண்டறிய தயாரா?",
            "finalCtaSubtitle": "2 நிமிடங்களுக்கும் குறைவான நேரம். வழிகாட்டல் பெற சில கேள்விகளுக்கு பதிலளிக்கவும்.",
            "finalCtaButton": "பொருத்தமான திட்டங்களைக் கண்டறியவும்",
            "popularTitle": "பிரபலமான தேடல்கள்",
            "viewAllSchemes": "அனைத்து திட்டங்களையும் காண்க",
            "quickStats": {
                "citizensServed": "வழிகாட்டப்பட்ட குடிமக்கள்",
                "financialTools": "நிதி கால்குலேட்டர்கள்",
                "schemesCount": "சரிபார்க்கப்பட்ட திட்டங்கள்"
            }
        },
        "auth": {
            "emailLabel": "மின்னஞ்சல் முகவரி",
            "loginButton": "உள்நுழைக",
            "passwordLabel": "கடவுச்சொல்",
            "phoneLabel": "மொபைல் எண்",
            "registerButton": "கணக்கை உருவாக்கவும்"
        },
        "calculator": {
            "calculateButton": "இஎம்ஐ மற்றும் பலன்களைக் கணக்கிடுங்கள்",
            "limitWarning": "அதிகபட்ச கடன் வரம்பை மீறுகிறது",
            "loanAmount": "கடன் தொகை (₹)",
            "monthlyEMI": "மதிப்பிடப்பட்ட மாதாந்திர இஎம்ஐ",
            "subsidyEstimate": "மதிப்பிடப்பட்ட மூலதன மானியம்"
        },
        "footer": {
            "copyright": "அனைத்து உரிமைகளும் பாதுகாக்கப்பட்டவை. அதிகாரப்பூர்வ முன்முயற்சி."
        },
        "recommendations": {
            "breakdownLabel": "தகுதி விவரம்",
            "formAge": "உங்கள் வயது (ஆண்டுகள்)",
            "formCategory": "சமூகப் பிரிவு",
            "formGender": "பாலினம்",
            "formIncome": "ஆண்டு குடும்ப வருமானம் (₹)",
            "formOccupation": "தொழில் / பணி",
            "formState": "மாநிலம் / யூனியன் பிரதேசம்",
            "scoreLabel": "பொருத்த மதிப்பெண்",
            "submitForm": "பொருத்தமான திட்டங்களைக் கண்டறியவும்",
            "threeWaysTitle": "திட்டங்களைக் கண்டறிய 3 வழிகள்"
        },
        "schemes": {
            "benefitTitle": "நிதி நன்மைகள் மற்றும் உதவி",
            "docsTitle": "தேவையான ஆவணங்கள் மற்றும் சான்றுகள்",
            "eligibilityTitle": "தகுதி வரம்புகள் மற்றும் நிபந்தனைகள்",
            "officialPortal": "அதிகாரப்பூர்வ விண்ணப்ப போர்டல்",
            "saveScheme": "திட்டத்தைச் சேமிக்கவும்",
            "saved": "சேமிக்கப்பட்டது",
            "verifiedBadge": "சரிபார்க்கப்பட்ட அரசுத் திட்டம்"
        },
        "applications": {
            "appId": "விண்ணப்ப ஐடி",
            "lastUpdated": "கடைசியாக புதுப்பிக்கப்பட்டது",
            "scheme": "திட்டம்",
            "status": "நிலை",
            "viewDetails": "விவரங்களைக் காண்க"
        }
    },
    "te": {
        "home": {
            "findMatchingSchemes": "సరిపోలే పథకాలను కనుగొనండి",
            "exploreAllSchemes": "అన్ని పథకాలను చూడండి",
            "matchingFlow": "వ్యక్తిగతీకరించిన పథక సరిపోలిక",
            "smartMatchingTitle": "మీరు అర్హత పొందగల ప్రభుత్వ పథకాలను కనుగొనండి",
            "smartMatchingDescription": "మీ వయస్సు, వర్గం, ప్రాంతం, వృత్తి మరియు అవసరాల గురించి కొన్ని ప్రశ్నలకు సమాధానం ఇవ్వండి. యోజనాసేతు అధికారిక నిబంధనల ప్రకారం మీ అర్హతను పరిశీలిస్తుంది.",
            "personalizedMatching": "వ్యక్తిగతీకరించిన పథక సరిపోలిక",
            "ruleBasedEligibility": "నిబంధనల ఆధారిత అర్హత తనిఖీ",
            "officialSources": "అధికారిక ప్రభుత్వ వనరులు",
            "noDocumentUpload": "పత్రాల అప్‌లోడ్ అవసరం లేదు",
            "howItWorksTitle": "యోజనాసేతు ఎలా పనిచేస్తుంది",
            "howItWorksSub": "పథకాలను కనుగొని అధికారికంగా దరఖాస్తు చేసుకోవడానికి సులభమైన 4 దశల ప్రక్రియ.",
            "stepTellUs": "మీ గురించి చెప్పండి",
            "stepTellUsDesc": "ఎలాంటి పత్రాలు సమర్పించకుండా పూర్తి గోప్యతతో మీ వివరాలను పంచుకోండి.",
            "stepCheckEligibility": "అర్హతను తనిఖీ చేయండి",
            "stepCheckEligibilityDesc": "మా రూల్ ఇంజిన్ మీ వివరాలను అధికారిక నిబంధనలతో పరిశీలిస్తుంది.",
            "stepDiscoverSchemes": "సరిపోలే పథకాలను పొందండి",
            "stepDiscoverSchemesDesc": "వివరణలు మరియు ఆర్థిక ప్రయోజనాలతో కూడిన పథకాల జాబితాను పొందండి.",
            "stepOfficialRoute": "అధికారిక దరఖాస్తు మార్గం",
            "stepOfficialRouteDesc": "మంత్రిత్వ శాఖ పోర్టల్‌లో నేరుగా దరఖాస్తు చేసుకోండి లేదా స్థానిక సహాయ కేంద్రాన్ని కనుగొనండి.",
            "exploreByCategory": "వర్గం వారీగా పథకాలను అన్వేషించండి",
            "exploreByCategorySub": "రంగాల వారీగా ఏర్పాటు చేసిన ప్రభుత్వ సంక్షేమ పథకాలను చూడండి.",
            "trustBadge": "అధికారిక సమాచార వ్యవస్థ",
            "trustTitle": "ప్రభుత్వ గెజిట్‌లు మరియు పోర్టల్‌ల నుండి ధృవీకరించబడింది",
            "trustDesc": "యోజనాసేతు అనేది ప్రభుత్వ మార్గదర్శకాల ఆధారంగా అర్హత సమాచారాన్ని అందించే పౌర-సాంకేతిక వేదిక.",
            "trustPillar1": "గెజిట్ ధృవీకరించబడింది",
            "trustPillar1Desc": "ప్రతి పథకం ప్రచురించిన అధికారిక నోటిఫికేషన్‌లతో లింక్ చేయబడింది.",
            "trustPillar2": "నిబంధనల ఆధారిత ఇంజిన్",
            "trustPillar2Desc": "స్పష్టమైన అర్హత మూల్యాంకనాలు.",
            "trustPillar3": "అధికారిక భాగస్వాములు",
            "trustPillar3Desc": "120+ ధృవీకరించబడిన రాష్ట్ర సంస్థలు మరియు బ్యాంక్ సహాయ కేంద్రాలు.",
            "trustPillar4": "గోప్యతకు ప్రాధాన్యత",
            "trustPillar4Desc": "పథకాలను కనుగొనడానికి పత్రాలు లేదా ఆధార్ అప్‌లోడ్ అవసరం లేదు.",
            "finalCtaTitle": "మీకు తగిన పథకాలను కనుగొనడానికి సిద్ధంగా ఉన్నారా?",
            "finalCtaSubtitle": "2 నిమిషాల కంటే తక్కువ సమయం పడుతుంది. మార్గదర్శకత్వం కోసం సమాధానం ఇవ్వండి.",
            "finalCtaButton": "సరిపోలే పథకాలను కనుగొనండి",
            "popularTitle": "ప్రముఖ శోధనలు",
            "viewAllSchemes": "అన్ని పథకాలను చూడండి",
            "quickStats": {
                "citizensServed": "సహాయం పొందిన పౌరులు",
                "financialTools": "ఆర్థిక కాలిక్యులేటర్లు",
                "schemesCount": "ధృవీకరించబడిన పథకాలు"
            }
        },
        "auth": {
            "emailLabel": "ఈమెయిల్ చిరునామా",
            "loginButton": "లాగిన్ చేయండి",
            "passwordLabel": "పాస్‌వర్డ్",
            "phoneLabel": "మొబైల్ నంబర్",
            "registerButton": "ఖాతాను సృష్టించండి"
        },
        "calculator": {
            "calculateButton": "ఇఎంఐ మరియు ప్రయోజనాలను లెక్కించండి",
            "limitWarning": "గరిష్ట రుణ పరిమితిని మించింది",
            "loanAmount": "రుణ మొత్తం (₹)",
            "monthlyEMI": "అంచనా నెలవారీ ఇఎంఐ",
            "subsidyEstimate": "అంచనా మూలధన సబ్సిడీ"
        },
        "footer": {
            "copyright": "సర్వహక్కులు ప్రత్యేకించబడ్డాయి. అధికారిక పౌర-సాంకేతిక చొరవ."
        },
        "recommendations": {
            "breakdownLabel": "అర్హత వివరాలు",
            "formAge": "మీ వయస్సు (సంవత్సరాలు)",
            "formCategory": "సామాజిక వర్గం",
            "formGender": "లింగం",
            "formIncome": "వార్షిక కుటుంబ ఆదాయం (₹)",
            "formOccupation": "వృత్తి / పని",
            "formState": "రాష్ట్రం / కేంద్రపాలిత ప్రాంతం",
            "scoreLabel": "సరిపోలిక స్కోరు",
            "submitForm": "సరిపోలే పథకాలను కనుగొనండి",
            "threeWaysTitle": "పథకాలను కనుగొనడానికి 3 మార్గాలు"
        },
        "schemes": {
            "benefitTitle": "ఆర్థిక ప్రయోజనాలు మరియు సహాయం",
            "docsTitle": "అవసరమైన పత్రాలు మరియు రుజువులు",
            "eligibilityTitle": "అర్హత ప్రమాణాలు మరియు షరతులు",
            "officialPortal": "అధికారిక దరఖాస్తు పోర్టల్",
            "saveScheme": "పథకాన్ని భద్రపరచండి",
            "saved": "భద్రపరచబడింది",
            "verifiedBadge": "ధృవీకరించబడిన అధికారిక పథకం"
        },
        "applications": {
            "appId": "దరఖాస్తు ఐడి",
            "lastUpdated": "చివరిగా నవీకరించబడింది",
            "scheme": "పథకం",
            "status": "స్థితి",
            "viewDetails": "వివరాలు చూడండి"
        }
    },
    "gu": {
        "home": {
            "findMatchingSchemes": "યોગ્ય યોજનાઓ શોધો",
            "exploreAllSchemes": "બધી યોજનાઓ જુઓ",
            "matchingFlow": "વ્યક્તિગત યોજના મેળવણ",
            "smartMatchingTitle": "તમે જે સરકારી યોજનાઓ માટે પાત્ર હોઈ શકો તે શોધો",
            "smartMatchingDescription": "તમારી ઉંમર, કેટેગરી, રાજ્ય, વ્યવસાય અને જરૂરિયાતો વિશે થોડા પ્રશ્નોના જવાબો આપો. યોજનાસેતુ સત્તાવાર નિયમો અનુસાર તમારી પાત્રતા તપાસે છે.",
            "personalizedMatching": "વ્યક્તિગત યોજના મેળવણ",
            "ruleBasedEligibility": "નિયમ આધારિત પાત્રતા ચકાસણી",
            "officialSources": "સત્તાવાર સરકારી સ્ત્રોતો",
            "noDocumentUpload": "દસ્તાવેજ અપલોડ કરવાની જરૂર નથી",
            "howItWorksTitle": "યોજનાસેતુ કેવી રીતે કાર્ય કરે છે",
            "howItWorksSub": "યોજનાઓ શોધવા અને સત્તાવાર અરજી સુધી પહોંચવા માટેની ૪ સરળ પ્રક્રિયા.",
            "stepTellUs": "તમારા વિશે જણાવો",
            "stepTellUsDesc": "દસ્તાવેજો અપલોડ કર્યા વિના સંપૂર્ણ ગોપનીયતા સાથે તમારી માહિતી શેર કરો.",
            "stepCheckEligibility": "પાત્રતા તપાસો",
            "stepCheckEligibilityDesc": "અમારું એન્જિન સત્તાવાર માપદંડો સામે તમારી પાત્રતાનું મૂલ્યાંકન કરે છે.",
            "stepDiscoverSchemes": "યોગ્ય યોજનાઓ મેળવો",
            "stepDiscoverSchemesDesc": "સ્પષ્ટ વિગતો અને નાણાકીય લાભો સાથેની યોજનાઓની સૂચિ મેળવો.",
            "stepOfficialRoute": "સત્તાવાર અરજી પદ્ધતિ",
            "stepOfficialRouteDesc": "સીધા મંત્રાલયના પોર્ટલ પર અરજી કરો અથવા અધિકૃત સહાયતા કેન્દ્ર શોધો.",
            "exploreByCategory": "કેટેગરી મુજબ યોજનાઓ જુઓ",
            "exploreByCategorySub": "ક્ષેત્ર અને વ્યવસાય મુજબ આયોજિત સરકારી કલ્યાણકારી યોજનાઓ જુઓ.",
            "trustBadge": "સત્તાવાર માહિતી પ્રણાલી",
            "trustTitle": "સરકારી ગેઝેટ અને પોર્ટલ પરથી સીધું ચકાસાયેલ",
            "trustDesc": "યોજનાસેતુ એ સ્વતંત્ર નાગરિક-ટેક પોર્ટલ છે જે સત્તાવાર માર્ગદર્શિકા પરથી પાત્રતા માહિતી પૂરી પાડે છે.",
            "trustPillar1": "ગેઝેટ ચકાસાયેલ",
            "trustPillar1Desc": "દરેક યોજના સત્તાવાર સૂચનાઓ સાથે જોડાયેલી છે.",
            "trustPillar2": "નિયમ આધારિત એન્જિન",
            "trustPillar2Desc": "પારદર્શક પાત્રતા મૂલ્યાંકન.",
            "trustPillar3": "અધિકૃત ભાગીદારો",
            "trustPillar3Desc": "૧૨૦+ ચકાસાયેલ રાજ્ય એજન્સીઓ અને સહાય કેન્દ્રો.",
            "trustPillar4": "ગોપનીયતા પ્રથમ",
            "trustPillar4Desc": "યોજના શોધવા માટે વ્યક્તિગત દસ્તાવેજ કે આધાર જરૂરી નથી.",
            "finalCtaTitle": "તમારા માટે યોગ્ય યોજનાઓ શોધવા તૈયાર છો?",
            "finalCtaSubtitle": "૨ મિનિટ કરતાં ઓછો સમય લાગે છે. માર્ગદર્શન મેળવવા માટે પ્રશ્નોના ઉત્તર આપો.",
            "finalCtaButton": "યોગ્ય યોજનાઓ શોધો",
            "popularTitle": "લોકપ્રિય શોધ",
            "viewAllSchemes": "બધી યોજનાઓ જુઓ",
            "quickStats": {
                "citizensServed": "માર્ગદર્શન મેળવનાર નાગરિકો",
                "financialTools": "નાણાકીય કેલ્ક્યુલેટર",
                "schemesCount": "ચકાસાયેલ યોજનાઓ"
            }
        },
        "auth": {
            "emailLabel": "ઈમેલ સરનામું",
            "loginButton": "લૉગિન કરો",
            "passwordLabel": "પાસવર્ડ",
            "phoneLabel": "મોબાઈલ નંબર",
            "registerButton": "ખાતું બનાવો"
        },
        "calculator": {
            "calculateButton": "ઈએમઆઈ અને લાભો ગણો",
            "limitWarning": "મહત્તમ લોન મર્યાદાથી વધુ",
            "loanAmount": "લોનની રકમ (₹)",
            "monthlyEMI": "અંદાજિત માસિક ઈએમઆઈ",
            "subsidyEstimate": "અંદાજિત સબસિડી"
        },
        "footer": {
            "copyright": "સર્વાધિકાર સુરક્ષિત. સત્તાવાર નાગરિક પહેલ."
        },
        "recommendations": {
            "breakdownLabel": "પાત્રતા વિગતો",
            "formAge": "તમારી ઉંમર (વર્ષ)",
            "formCategory": "સામાજિક વર્ગ",
            "formGender": "જાતિ",
            "formIncome": "વાર્ષિક પારિવારિક આવક (₹)",
            "formOccupation": "વ્યવસાય / કામ",
            "formState": "રાજ્ય / કેન્દ્રશાસિત પ્રદેશ",
            "scoreLabel": "મેચ સ્કોર",
            "submitForm": "યોગ્ય યોજનાઓ શોધો",
            "threeWaysTitle": "યોજનાઓ શોધવાના ૩ રસ્તા"
        },
        "schemes": {
            "benefitTitle": "નાણાકીય લાભ અને સહાય",
            "docsTitle": "જરૂરી દસ્તાવેજો અને પુરાવા",
            "eligibilityTitle": "પાત્રતાના માપદંડ અને શરતો",
            "officialPortal": "સત્તાવાર અરજી પોર્ટલ",
            "saveScheme": "યોજના સાચવો",
            "saved": "સાચવેલ છે",
            "verifiedBadge": "ચકાસાયેલ સરકારી યોજના"
        },
        "applications": {
            "appId": "અરજી આઈડી",
            "lastUpdated": "છેલ્લે અપડેટ કરેલ",
            "scheme": "યોજના",
            "status": "સ્થિતિ",
            "viewDetails": "વિગતો જુઓ"
        }
    },
    "kn": {
        "home": {
            "findMatchingSchemes": "ಹೊಂದಾಣಿಕೆಯ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ",
            "exploreAllSchemes": "ಎಲ್ಲಾ ಯೋಜನೆಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
            "matchingFlow": "ವೈಯಕ್ತೀಕರಿಸಿದ ಯೋಜನೆ ಹೊಂದಾಣಿಕೆ",
            "smartMatchingTitle": "ನೀವು ಅರ್ಹರಾಗಬಹುದಾದ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ",
            "smartMatchingDescription": "ನಿಮ್ಮ ವಯಸ್ಸು, ವರ್ಗ, ಸ್ಥಳ, ವೃತ್ತಿ ಮತ್ತು ವ್ಯವಹಾರದ ಅಗತ್ಯತೆಗಳ ಬಗ್ಗೆ ಕೆಲವು ಸರಳ ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಿಸಿ. ಯೋಜನಾಸೇತು ಅಧಿಕೃತ ನಿಯಮಗಳ ಪ್ರಕಾರ ನಿಮ್ಮ ಅರ್ಹತೆಯನ್ನು ಪರಿಶೀಲಿಸುತ್ತದೆ.",
            "personalizedMatching": "ವೈಯಕ್ತೀಕರಿಸಿದ ಯೋಜನೆ ಹೊಂದಾಣಿಕೆ",
            "ruleBasedEligibility": "ನಿಯಮ ಆಧಾರಿತ ಅರ್ಹತಾ ಪರಿಶೀಲನೆ",
            "officialSources": "ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಮೂಲಗಳು",
            "noDocumentUpload": "ದಾಖಲೆ ಅಪ್‌ಲೋಡ್ ಮಾಡುವ ಅಗತ್ಯವಿಲ್ಲ",
            "howItWorksTitle": "ಯೋಜನಾಸೇತು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ",
            "howItWorksSub": "ಯೋಜನೆಗಳನ್ನು ಅನ್ವೇಷಿಸಲು ಮತ್ತು ಅಧಿಕೃತವಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಸುಲಭವಾದ 4-ಹಂತದ ಪ್ರಕ್ರಿಯೆ.",
            "stepTellUs": "ನಿಮ್ಮ ಬಗ್ಗೆ ತಿಳಿಸಿ",
            "stepTellUsDesc": "ಯಾವುದೇ ದಾಖಲೆ ಸಲ್ಲಿಸದೆ ಸಂಪೂರ್ಣ ಗೌಪ್ಯತೆಯಲ್ಲಿ ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಹಂಚಿಕೊಳ್ಳಿ.",
            "stepCheckEligibility": "ಅರ್ಹತೆಯನ್ನು ಪರಿಶೀಲಿಸಿ",
            "stepCheckEligibilityDesc": "ನಮ್ಮ ನಿಯಮ ಎಂಜಿನ್ ನಿಮ್ಮ ಮಾಹಿತಿಯನ್ನು ಅಧಿಕೃತ ಯೋಜನೆಗಳ ಮಾನದಂಡಗಳೊಂದಿಗೆ ಪರಿಶೀಲಿಸುತ್ತದೆ.",
            "stepDiscoverSchemes": "ಹೊಂದಾಣಿಕೆಯ ಯೋಜನೆಗಳನ್ನು ಅನ್ವೇಷಿಸಿ",
            "stepDiscoverSchemesDesc": "ಸ್ಪಷ್ಟ ಕಾರಣಗಳು ಮತ್ತು ಆರ್ಥಿಕ ಪ್ರಯೋಜನಗಳೊಂದಿಗೆ ನಿಮಗೆ ಸೂಕ್ತವಾದ ಯೋಜನೆಗಳ ಪಟ್ಟಿಯನ್ನು ಪಡೆಯಿರಿ.",
            "stepOfficialRoute": "ಅಧಿಕೃತ ಅರ್ಜಿ ಮಾರ್ಗ",
            "stepOfficialRouteDesc": "ನೇರವಾಗಿ ಸಚಿವಾಲಯದ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ ಅಥವಾ ಸ್ಥಳೀಯ ಅಧಿಕೃತ ಸಹಾಯ ಕೇಂದ್ರಗಳನ್ನು ಹುಡುಕಿ.",
            "exploreByCategory": "ವರ್ಗವಾರು ಯೋಜನೆಗಳನ್ನು ಅನ್ವೇಷಿಸಿ",
            "exploreByCategorySub": "ಕ್ಷೇತ್ರ ಮತ್ತು ವೃತ್ತಿಗೆ ತಕ್ಕಂತೆ ಆಯೋಜಿಸಲಾದ ಸರ್ಕಾರಿ ಕಲ್ಯಾಣ ಯೋಜನೆಗಳು.",
            "trustBadge": "ಅಧಿಕೃತ ಮಾಹಿತಿ ವ್ಯವಸ್ಥೆ",
            "trustTitle": "ಸರ್ಕಾರಿ ಗೆಜೆಟ್‌ಗಳು ಮತ್ತು ಪೋರ್ಟಲ್‌ಗಳಿಂದ ನೇರವಾಗಿ ಪರಿಶೀಲಿಸಲಾಗಿದೆ",
            "trustDesc": "ಯೋಜನಾಸೇತು ಸರ್ಕಾರಿ ಮಾರ್ಗಸೂಚಿಗಳಿಂದ ಅರ್ಹತಾ ಮಾರ್ಗದರ್ಶನ ನೀಡುವ ಸ್ವತಂತ್ರ ನಾಗರಿಕ-ತಂತ್ರಜ್ಞಾನ ವೇದಿಕೆಯಾಗಿದೆ.",
            "trustPillar1": "ಗೆಜೆಟ್ ಪರಿಶೀಲಿಸಲಾಗಿದೆ",
            "trustPillar1Desc": "ಪ್ರತಿಯೊಂದು ಯೋಜನೆಯನ್ನು ಅಧಿಕೃತ ಅಧಿಸೂಚನೆಗಳೊಂದಿಗೆ ಪರಿಶೀಲಿಸಲಾಗಿದೆ.",
            "trustPillar2": "ನಿಯಮ ಆಧಾರಿತ ಎಂಜಿನ್",
            "trustPillar2Desc": "ಪಾರದರ್ಶಕ ಅರ್ಹತಾ ಮೌಲ್ಯಮಾಪನ.",
            "trustPillar3": "ಅಧಿಕೃತ ಪಾಲುದಾರರು",
            "trustPillar3Desc": "120+ ಪರಿಶೀಲಿಸಿದ ರಾಜ್ಯ ಸಂಸ್ಥೆಗಳು ಮತ್ತು ಸಹಾಯ ಕೇಂದ್ರಗಳು.",
            "trustPillar4": "ಗೌಪ್ಯತೆಗೆ ಮೊದಲ ಆದ್ಯತೆ",
            "trustPillar4Desc": "ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು ದಾಖಲೆ ಅಥವಾ ಆಧಾರ್ ಅಪ್‌ಲೋಡ್ ಅಗತ್ಯವಿಲ್ಲ.",
            "finalCtaTitle": "ನಿಮಗೆ ಸೂಕ್ತವಾದ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು ಸಿದ್ಧರಿದ್ದೀರಾ?",
            "finalCtaSubtitle": "2 ನಿಮಿಷಕ್ಕಿಂತ ಕಡಿಮೆ ಸಮಯ ತೆಗೆದುಕೊಳ್ಳುತ್ತದೆ. ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ಉತ್ತರಿಸಿ.",
            "finalCtaButton": "ಹೊಂದಾಣಿಕೆಯ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ",
            "popularTitle": "ಜನಪ್ರಿಯ ಹುಡುಕಾಟಗಳು",
            "viewAllSchemes": "ಎಲ್ಲಾ ಯೋಜನೆಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
            "quickStats": {
                "citizensServed": "ಮಾರ್ಗದರ್ಶನ ಪಡೆದ ನಾಗರಿಕರು",
                "financialTools": "ಆರ್ಥಿಕ ಕ್ಯಾಲ್ಕುಲೇಟರ್‌ಗಳು",
                "schemesCount": "ಪರಿಶೀಲಿಸಿದ ಯೋಜನೆಗಳು"
            }
        },
        "auth": {
            "emailLabel": "ಇಮೇಲ್ ವಿಳಾಸ",
            "loginButton": "ಲಾಗಿನ್ ಮಾಡಿ",
            "passwordLabel": "ಪಾಸ್‌ವರ್ಡ್",
            "phoneLabel": "ಮೊಬೈಲ್ ಸಂಖ್ಯೆ",
            "registerButton": "ಖಾತೆ ರಚಿಸಿ"
        },
        "calculator": {
            "calculateButton": "ಇಎಂಐ ಮತ್ತು ಪ್ರಯೋಜನಗಳನ್ನು ಲೆಕ್ಕಹಾಕಿ",
            "limitWarning": "ಗರಿಷ್ಠ ಸಾಲದ ಮಿತಿಯನ್ನು ಮೀರಿದೆ",
            "loanAmount": "ಸಾಲದ ಮೊತ್ತ (₹)",
            "monthlyEMI": "ಅಂದಾಜು ಮಾಸಿಕ ಇಎಂಐ",
            "subsidyEstimate": "ಅಂದಾಜು ಬಂಡವಾಳ ಸಬ್ಸಿಡಿ"
        },
        "footer": {
            "copyright": "ಎಲ್ಲಾ ಹಕ್ಕುಗಳನ್ನು ಕಾಯ್ದಿರಿಸಲಾಗಿದೆ. ಅಧಿಕೃತ ನಾಗರಿಕ ತಂತ್ರಜ್ಞಾನ ಉಪಕ್ರಮ."
        },
        "recommendations": {
            "breakdownLabel": "ಅರ್ಹತೆಯ ವಿವರ",
            "formAge": "ನಿಮ್ಮ ವಯಸ್ಸು (ವರ್ಷಗಳು)",
            "formCategory": "ಸಾಮಾಜಿಕ ವರ್ಗ",
            "formGender": "ಲಿಂಗ",
            "formIncome": "ವಾರ್ಷಿಕ ಕುಟುಂಬ ಆದಾಯ (₹)",
            "formOccupation": "ವೃತ್ತಿ / ಕೆಲಸ",
            "formState": "ರಾಜ್ಯ / ಕೇಂದ್ರಾಡಳಿತ ಪ್ರದೇಶ",
            "scoreLabel": "ಹೊಂದಾಣಿಕೆ ಸ್ಕೋರ್",
            "submitForm": "ಹೊಂದಾಣಿಕೆಯ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ",
            "threeWaysTitle": "ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು 3 ಮಾರ್ಗಗಳು"
        },
        "schemes": {
            "benefitTitle": "ಆರ್ಥಿಕ ಪ್ರಯೋಜನಗಳು ಮತ್ತು ನೆರವು",
            "docsTitle": "ಅಗತ್ಯ ದಾಖಲೆಗಳು ಮತ್ತು ಪುರಾವೆಗಳು",
            "eligibilityTitle": "ಅರ್ಹತಾ ಮಾನದಂಡಗಳು ಮತ್ತು ಷರತ್ತುಗಳು",
            "officialPortal": "ಅಧಿಕೃತ ಅರ್ಜಿ ಪೋರ್ಟಲ್",
            "saveScheme": "ಯೋಜನೆಯನ್ನು ಉಳಿಸಿ",
            "saved": "ಉಳಿಸಲಾಗಿದೆ",
            "verifiedBadge": "ಪರಿಶೀಲಿಸಿದ ಅಧಿಕೃತ ಯೋಜನೆ"
        },
        "applications": {
            "appId": "ಅರ್ಜಿ ಐಡಿ",
            "lastUpdated": "ಕೊನೆಯ ನವೀಕರಣ",
            "scheme": "ಯೋಜನೆ",
            "status": "ಸ್ಥಿತಿ",
            "viewDetails": "ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ"
        }
    },
    "ml": {
        "home": {
            "findMatchingSchemes": "യോജിച്ച പദ്ധതികൾ കണ്ടെത്തുക",
            "exploreAllSchemes": "എല്ലാ പദ്ധതികളും കാണുക",
            "matchingFlow": "വ്യക്തിഗത പദ്ധതി പൊരുത്തപ്പെടുത്തൽ",
            "smartMatchingTitle": "നിങ്ങൾക്ക് അർഹതയുള്ള സർക്കാർ പദ്ധതികൾ കണ്ടെത്തുക",
            "smartMatchingDescription": "നിങ്ങളുടെ പ്രായം, വിഭാഗം, സംസ്ഥാനം, തൊഴിൽ എന്നിവയെക്കുറിച്ചുള്ള ലളിതമായ ചോദ്യങ്ങൾക്ക് മറുപടി നൽകുക. യോജനാസേതു ഔദ്യോഗിക നിയമങ്ങൾ അനുസരിച്ച് നിങ്ങളുടെ അർഹത പരിശോധിക്കുന്നു.",
            "personalizedMatching": "വ്യക്തിഗത പദ്ധതി പൊരുത്തപ്പെടുത്തൽ",
            "ruleBasedEligibility": "നിയമാധിഷ്ഠിത അർഹതാ പരിശോധന",
            "officialSources": "ഔദ്യോഗിക സർക്കാർ സ്രോതസ്സുകൾ",
            "noDocumentUpload": "രേഖകൾ അപ്‌ലോഡ് ചെയ്യേണ്ടതില്ല",
            "howItWorksTitle": "യോജനാസേതു എങ്ങനെ പ്രവർത്തിക്കുന്നു",
            "howItWorksSub": "പദ്ധതികൾ കണ്ടെത്താനും ഔദ്യോഗികമായി അപേക്ഷിക്കാനുമുള്ള സുതാര്യമായ 4 ഘട്ടങ്ങൾ.",
            "stepTellUs": "നിങ്ങളെക്കുറിച്ച് പറയുക",
            "stepTellUsDesc": "രേഖകൾ അപ്‌ലോഡ് ചെയ്യാതെ പൂർണ്ണ സ്വകാര്യതയോടെ നിങ്ങളുടെ വിവരങ്ങൾ പങ്കിടുക.",
            "stepCheckEligibility": "അർഹത പരിശോധിക്കുക",
            "stepCheckEligibilityDesc": "ഔദ്യോഗിക മാനദണ്ഡങ്ങളുമായി നിങ്ങളുടെ വിവരങ്ങൾ ഞങ്ങളുടെ റൂൾ എഞ്ചിൻ പരിശോധിക്കുന്നു.",
            "stepDiscoverSchemes": "യോജിച്ച പദ്ധതികൾ കണ്ടെത്തുക",
            "stepDiscoverSchemesDesc": "വ്യക്തമായ വിവരങ്ങളും ആനുകൂല്യങ്ങളും ഉൾപ്പെടെയുള്ള പദ്ധതികളുടെ പട്ടിക നേടുക.",
            "stepOfficialRoute": "ഔദ്യോഗിക അപേക്ഷാ വഴി",
            "stepOfficialRouteDesc": "നേരിട്ട് മന്ത്രാലയ പോർട്ടലിൽ അപേക്ഷിക്കുക അല്ലെങ്കിൽ പ്രാദേശിക സഹായ കേന്ദ്രങ്ങൾ കണ്ടെത്തുക.",
            "exploreByCategory": "വിഭാഗം തിരിച്ച് പദ്ധതികൾ കണ്ടെത്തുക",
            "exploreByCategorySub": "മേഖലയും തൊഴിലും അടിസ്ഥാനമാക്കി ക്രമീകരിച്ച സർക്കാർ ക്ഷേമ പദ്ധതികൾ.",
            "trustBadge": "ഔദ്യോഗിക വിവര ശൃംഖല",
            "trustTitle": "സർക്കാർ ഗസറ്റുകളിൽ നിന്നും പോർട്ടലുകളിൽ നിന്നും പരിശോധിച്ചുറപ്പിച്ചത്",
            "trustDesc": "ഔദ്യോഗിക മാർഗ്ഗനിർദ്ദേശങ്ങളിൽ നിന്ന് അർഹതാ വിവരങ്ങൾ നൽകുന്ന സ്വതന്ത്ര പൗര-സാങ്കേതിക പ്ലാറ്റ്‌ഫോം.",
            "trustPillar1": "ഗസറ്റ് പരിശോധിച്ചുറപ്പിച്ചത്",
            "trustPillar1Desc": "ഓരോ പദ്ധതിയും ഔദ്യോഗിക അറിയിപ്പുകളുമായി ബന്ധിപ്പിച്ചിരിക്കുന്നു.",
            "trustPillar2": "നിയമാധിഷ്ഠിത എഞ്ചിൻ",
            "trustPillar2Desc": "സുതാര്യമായ അർഹതാ വിലയിരുത്തൽ.",
            "trustPillar3": "അംഗീകൃത പങ്കാളികൾ",
            "trustPillar3Desc": "120+ അംഗീകൃത സംസ്ഥാന ഏജൻസികളും സഹായ കേന്ദ്രങ്ങളും.",
            "trustPillar4": "സ്വകാര്യത പ്രധാനം",
            "trustPillar4Desc": "പദ്ധതികൾ കണ്ടെത്താൻ രേഖകളോ ആധാറോ ആവശ്യമില്ല.",
            "finalCtaTitle": "നിങ്ങൾക്ക് അനുയോജ്യമായ പദ്ധതികൾ കണ്ടെത്താൻ തയ്യാറാണോ?",
            "finalCtaSubtitle": "2 മിനിറ്റിൽ താഴെ സമയം മാത്രം. മാർഗ്ഗനിർദ്ദേശത്തിനായി മറുപടി നൽകുക.",
            "finalCtaButton": "യോജിച്ച പദ്ധതികൾ കണ്ടെത്തുക",
            "popularTitle": "ജനപ്രിയ തിരയലുകൾ",
            "viewAllSchemes": "എല്ലാ പദ്ധതികളും കാണുക",
            "quickStats": {
                "citizensServed": "സഹായം ലഭിച്ച പൗരന്മാർ",
                "financialTools": "സാമ്പത്തിക കാൽക്കുലേറ്ററുകൾ",
                "schemesCount": "പരിശോധിച്ച പദ്ധതികൾ"
            }
        },
        "auth": {
            "emailLabel": "ഇമെയിൽ വിലാസം",
            "loginButton": "ലോഗിൻ ചെയ്യുക",
            "passwordLabel": "പാസ്‌വേഡ്",
            "phoneLabel": "മൊബൈൽ നമ്പർ",
            "registerButton": "അക്കൗണ്ട് ഉണ്ടാക്കുക"
        },
        "calculator": {
            "calculateButton": "ഇഎംഐയും ആനുകൂല്യങ്ങളും കണക്കാക്കുക",
            "limitWarning": "പരമാവധി വായ്പ പരിധി കവിഞ്ഞു",
            "loanAmount": "വായ്പാ തുക (₹)",
            "monthlyEMI": "പ്രതീക്ഷിക്കുന്ന പ്രതിമാസ ഇഎംഐ",
            "subsidyEstimate": "പ്രതീക്ഷിക്കുന്ന മൂലധന സബ്‌സിഡി"
        },
        "footer": {
            "copyright": "എല്ലാ അവകാശങ്ങളും നിക്ഷിപ്തം. ഔദ്യോഗിക സംരംഭം."
        },
        "recommendations": {
            "breakdownLabel": "അർഹതാ വിശദാംശങ്ങൾ",
            "formAge": "നിങ്ങളുടെ പ്രായം (വർഷങ്ങൾ)",
            "formCategory": "സാമൂഹിക വിഭാഗം",
            "formGender": "ലിംഗഭേദം",
            "formIncome": "വാർഷിക കുടുംബ വരുമാനം (₹)",
            "formOccupation": "തൊഴിൽ / ജോലി",
            "formState": "സംസ്ഥാനം / കേന്ദ്രഭരണ പ്രദേശം",
            "scoreLabel": "പൊരുത്ത സ്കോർ",
            "submitForm": "യോജിച്ച പദ്ധതികൾ കണ്ടെത്തുക",
            "threeWaysTitle": "പദ്ധതികൾ കണ്ടെത്താനുള്ള 3 വഴികൾ"
        },
        "schemes": {
            "benefitTitle": "സാമ്പത്തിക ആനുകൂല്യങ്ങളും സഹായവും",
            "docsTitle": "ആവശ്യമായ രേഖകളും തെളിവുകളും",
            "eligibilityTitle": "അർഹതാ മാനദണ്ഡങ്ങളും വ്യവസ്ഥകളും",
            "officialPortal": "ഔദ്യോഗിക അപേക്ഷാ പോർട്ടൽ",
            "saveScheme": "പദ്ധതി സേവ് ചെയ്യുക",
            "saved": "സേവ് ചെയ്തു",
            "verifiedBadge": "പരിശോധിച്ച ഔദ്യോഗിക പദ്ധതി"
        },
        "applications": {
            "appId": "അപേക്ഷാ ഐഡി",
            "lastUpdated": "അവസാനം പുതുക്കിയത്",
            "scheme": "പദ്ധതി",
            "status": "നില",
            "viewDetails": "വിശദാംശങ്ങൾ കാണുക"
        }
    },
    "pa": {
        "home": {
            "findMatchingSchemes": "ਢੁਕਵੀਆਂ ਸਕੀਮਾਂ ਲੱਭੋ",
            "exploreAllSchemes": "ਸਾਰੀਆਂ ਸਕੀਮਾਂ ਦੇਖੋ",
            "matchingFlow": "ਨਿੱਜੀ ਸਕੀਮ ਮੇਲ",
            "smartMatchingTitle": "ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਲੱਭੋ ਜਿਨ੍ਹਾਂ ਦੇ ਤੁਸੀਂ ਯੋਗ ਹੋ ਸਕਦੇ ਹੋ",
            "smartMatchingDescription": "ਆਪਣੀ ਉਮਰ, ਸ਼੍ਰੇਣੀ, ਸੂਬੇ, ਕਿੱਤੇ ਅਤੇ ਲੋੜਾਂ ਬਾਰੇ ਕੁਝ ਸਧਾਰਨ ਸਵਾਲਾਂ ਦੇ ਜਵਾਬ ਦਿਓ। ਯੋਜਨਾਸੇਤੂ ਸਰਕਾਰੀ ਨਿਯਮਾਂ ਅਨੁਸਾਰ ਤੁਹਾਡੀ ਯੋਗਤਾ ਦੀ ਜਾਂਚ ਕਰਦਾ ਹੈ।",
            "personalizedMatching": "ਨਿੱਜੀ ਸਕੀਮ ਮੇਲ",
            "ruleBasedEligibility": "ਨਿਯਮ-ਅਧਾਰਿਤ ਯੋਗਤਾ ਜਾਂਚ",
            "officialSources": "ਸਰਕਾਰੀ ਅਧਿਕਾਰਤ ਸਰੋਤ",
            "noDocumentUpload": "ਦਸਤਾਵੇਜ਼ ਅਪਲੋਡ ਕਰਨ ਦੀ ਲੋੜ ਨਹੀਂ",
            "howItWorksTitle": "ਯੋਜਨਾਸੇਤੂ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ",
            "howItWorksSub": "ਸਕੀਮਾਂ ਲੱਭਣ ਅਤੇ ਅਧਿਕਾਰਤ ਤੌਰ 'ਤੇ ਅਰਜ਼ੀ ਦੇਣ ਲਈ ਆਸਾਨ 4-ਕਦਮੀ ਪ੍ਰਕਿਰਿਆ।",
            "stepTellUs": "ਆਪਣੇ ਬਾਰੇ ਦੱਸੋ",
            "stepTellUsDesc": "ਬਿਨਾਂ ਕੋਈ ਦਸਤਾਵੇਜ਼ ਦਿੱਤੇ ਪੂਰੀ ਗੋਪਨੀਯਤਾ ਨਾਲ ਆਪਣੀ ਜਾਣਕਾਰੀ ਸਾਂਝੀ ਕਰੋ।",
            "stepCheckEligibility": "ਯੋਗਤਾ ਦੀ ਜਾਂਚ ਕਰੋ",
            "stepCheckEligibilityDesc": "ਸਾਡਾ ਨਿਯਮ ਇੰਜਣ ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਦੇ ਨਿਯਮਾਂ ਨਾਲ ਤੁਹਾਡੀ ਜਾਣਕਾਰੀ ਦੀ ਜਾਂਚ ਕਰਦਾ ਹੈ।",
            "stepDiscoverSchemes": "ਢੁਕਵੀਆਂ ਸਕੀਮਾਂ ਪ੍ਰਾਪਤ ਕਰੋ",
            "stepDiscoverSchemesDesc": "ਸਪਸ਼ਟ ਕਾਰਨਾਂ ਅਤੇ ਲਾਭਾਂ ਦੇ ਨਾਲ ਆਪਣੇ ਲਈ ਢੁਕਵੀਆਂ ਸਕੀਮਾਂ ਦੀ ਸੂਚੀ ਪ੍ਰਾਪਤ ਕਰੋ।",
            "stepOfficialRoute": "ਅਧਿਕਾਰਤ ਅਰਜ਼ੀ ਰਸਤਾ",
            "stepOfficialRouteDesc": "ਸਿੱਧੇ ਮੰਤਰਾਲੇ ਦੇ ਪੋਰਟਲ 'ਤੇ ਅਰਜ਼ੀ ਦਿਓ ਜਾਂ ਸਥਾਨਕ ਸਹਾਇਤਾ ਕੇਂਦਰ ਲੱਭੋ।",
            "exploreByCategory": "ਸ਼੍ਰੇਣੀ ਅਨੁਸਾਰ ਸਕੀਮਾਂ ਦੇਖੋ",
            "exploreByCategorySub": "ਵੱਖ-ਵੱਖ ਖੇਤਰਾਂ ਅਤੇ ਕਿੱਤਿਆਂ ਅਨੁਸਾਰ ਤਿਆਰ ਕੀਤੀਆਂ ਸਰਕਾਰੀ ਭਲਾਈ ਸਕੀਮਾਂ।",
            "trustBadge": "ਅਧਿਕਾਰਤ ਸੂਚਨਾ ਪ੍ਰਣਾਲੀ",
            "trustTitle": "ਸਰਕਾਰੀ ਗਜ਼ਟ ਅਤੇ ਪੋਰਟਲਾਂ ਤੋਂ ਸਿੱਧਾ ਪ੍ਰਮਾਣਿਤ",
            "trustDesc": "ਯੋਜਨਾਸੇਤੂ ਇੱਕ ਨਾਗਰਿਕ-ਤਕਨਾਲੋਜੀ ਪੋਰਟਲ ਹੈ ਜੋ ਅਧਿਕਾਰਤ ਦਿਸ਼ਾ-ਨਿਰਦੇਸ਼ਾਂ ਤੋਂ ਜਾਣਕਾਰੀ ਪ੍ਰਦਾਨ ਕਰਦਾ ਹੈ।",
            "trustPillar1": "ਗਜ਼ਟ ਪ੍ਰਮਾਣਿਤ",
            "trustPillar1Desc": "ਹਰੇਕ ਸਕੀਮ ਅਧਿਕਾਰਤ ਨੋਟੀਫਿਕੇਸ਼ਨਾਂ ਨਾਲ ਪ੍ਰਮਾਣਿਤ ਹੈ।",
            "trustPillar2": "ਨਿਯਮ-ਅਧਾਰਿਤ ਇੰਜਣ",
            "trustPillar2Desc": "ਪਾਰਦਰਸ਼ੀ ਯੋਗਤਾ ਮੁਲਾਂਕਣ।",
            "trustPillar3": "ਅਧਿਕਾਰਤ ਭਾਈਵਾਲ",
            "trustPillar3Desc": "120+ ਪ੍ਰਮਾਣਿਤ ਰਾਜ ਏਜੰਸੀਆਂ ਅਤੇ ਬੈਂਕ ਸਹਾਇਤਾ ਕੇਂਦਰ।",
            "trustPillar4": "ਗੋਪਨੀਯਤਾ ਪਹਿਲਾਂ",
            "trustPillar4Desc": "ਸਕੀਮਾਂ ਲੱਭਣ ਲਈ ਦਸਤਾਵੇਜ਼ ਜਾਂ ਆਧਾਰ ਦੀ ਲੋੜ ਨਹੀਂ।",
            "finalCtaTitle": "ਆਪਣੇ ਲਈ ਢੁਕਵੀਆਂ ਸਕੀਮਾਂ ਲੱਭਣ ਲਈ ਤਿਆਰ ਹੋ?",
            "finalCtaSubtitle": "2 ਮਿੰਟ ਤੋਂ ਵੀ ਘੱਟ ਸਮਾਂ ਲੱਗਦਾ ਹੈ। ਮਾਰਗਦਰਸ਼ਨ ਲਈ ਜਵਾਬ ਦਿਓ।",
            "finalCtaButton": "ਢੁਕਵੀਆਂ ਸਕੀਮਾਂ ਲੱਭੋ",
            "popularTitle": "ਪ੍ਰਸਿੱਧ ਖੋਜਾਂ",
            "viewAllSchemes": "ਸਾਰੀਆਂ ਸਕੀਮਾਂ ਦੇਖੋ",
            "quickStats": {
                "citizensServed": "ਮਾਰਗਦਰਸ਼ਨ ਪ੍ਰਾਪਤ ਨਾਗਰਿਕ",
                "financialTools": "ਵਿੱਤੀ ਕੈਲਕੁਲੇਟਰ",
                "schemesCount": "ਪ੍ਰਮਾਣਿਤ ਸਕੀਮਾਂ"
            }
        },
        "auth": {
            "emailLabel": "ਈਮੇਲ ਪਤਾ",
            "loginButton": "ਲਾਗਇਨ ਕਰੋ",
            "passwordLabel": "ਪਾਸਵਰਡ",
            "phoneLabel": "ਮੋਬਾਈਲ ਨੰਬਰ",
            "registerButton": "ਖਾਤਾ ਬਣਾਓ"
        },
        "calculator": {
            "calculateButton": "ਈਐਮਆਈ ਅਤੇ ਲਾਭਾਂ ਦੀ ਗਣਨਾ ਕਰੋ",
            "limitWarning": "ਵੱਧ ਤੋਂ ਵੱਧ ਕਰਜ਼ਾ ਸੀਮਾ ਤੋਂ ਵੱਧ",
            "loanAmount": "ਕਰਜ਼ਾ ਰਕਮ (₹)",
            "monthlyEMI": "ਅੰਦਾਜ਼ਨ ਮਾਸਿਕ ਈਐਮਆਈ",
            "subsidyEstimate": "ਅੰਦਾਜ਼ਨ ਸਬਸਿਡੀ"
        },
        "footer": {
            "copyright": "ਸਾਰੇ ਅਧਿਕਾਰ ਰਾਖਵੇਂ ਹਨ। ਅਧਿਕਾਰਤ ਨਾਗਰਿਕ ਪਹਿਲਕਦਮੀ।"
        },
        "recommendations": {
            "breakdownLabel": "ਯੋਗਤਾ ਦੇ ਵੇਰਵੇ",
            "formAge": "ਤੁਹਾਡੀ ਉਮਰ (ਸਾਲ)",
            "formCategory": "ਸਮਾਜਿਕ ਸ਼੍ਰੇਣੀ",
            "formGender": "ਲਿੰਗ",
            "formIncome": "ਸਾਲਾਨਾ ਪਰਿਵਾਰਕ ਆਮਦਨ (₹)",
            "formOccupation": "ਕਿੱਤਾ / ਕੰਮ",
            "formState": "ਰਾਜ / ਕੇਂਦਰ ਸ਼ਾਸਿਤ ਪ੍ਰਦੇਸ਼",
            "scoreLabel": "ਮੈਚ ਸਕੋਰ",
            "submitForm": "ਢੁਕਵੀਆਂ ਸਕੀਮਾਂ ਲੱਭੋ",
            "threeWaysTitle": "ਸਕੀਮਾਂ ਲੱਭਣ ਦੇ 3 ਤਰੀਕੇ"
        },
        "schemes": {
            "benefitTitle": "ਵਿੱਤੀ ਲਾਭ ਅਤੇ ਸਹਾਇਤਾ",
            "docsTitle": "ਲੋੜੀਂਦੇ ਦਸਤਾਵੇਜ਼ ਅਤੇ ਸਬੂਤ",
            "eligibilityTitle": "ਯੋਗਤਾ ਦੇ ਮਾਪਦੰਡ ਅਤੇ ਸ਼ਰਤਾਂ",
            "officialPortal": "ਅਧਿਕਾਰਤ ਅਰਜ਼ੀ ਪੋਰਟਲ",
            "saveScheme": "ਸਕੀਮ ਸੰਭਾਲੋ",
            "saved": "ਸੰਭਾਲੀ ਗਈ",
            "verifiedBadge": "ਪ੍ਰਮਾਣਿਤ ਸਰਕਾਰੀ ਸਕੀਮ"
        },
        "applications": {
            "appId": "ਅਰਜ਼ੀ ਆਈਡੀ",
            "lastUpdated": "ਆਖਰੀ ਅੱਪਡੇਟ",
            "scheme": "ਸਕੀਮ",
            "status": "ਸਥਿਤੀ",
            "viewDetails": "ਵੇਰਵੇ ਦੇਖੋ"
        }
    },
    "or": {
        "home": {
            "findMatchingSchemes": "ଉପଯୁକ୍ତ ଯୋଜନା ଖୋଜନ୍ତୁ",
            "exploreAllSchemes": "ସମସ୍ତ ଯୋଜନା ଦେଖନ୍ତୁ",
            "matchingFlow": "ବ୍ୟକ୍ତିଗତ ଯୋଜନା ମେଳ",
            "smartMatchingTitle": "ଆପଣ ଯୋଗ୍ୟ ହୋଇପାରୁଥିବା ସରକାରୀ ଯୋଜନାଗୁଡିକ ଖୋଜନ୍ତୁ",
            "smartMatchingDescription": "ଆପଣଙ୍କ ବୟସ, ବର୍ଗ, ରାଜ୍ୟ, ବୃତ୍ତି ଏବଂ ବ୍ୟବସାୟ ଆବଶ୍ୟକତା ବିଷୟରେ କିଛି ସରଳ ପ୍ରଶ୍ନର ଉତ୍ତର ଦିଅନ୍ତୁ। ଯୋଜନାସେତୁ ସରକାରୀ ନିୟମ ଅନୁଯାୟୀ ଆପଣଙ୍କ ଯୋଗ୍ୟତା ଯାଞ୍ଚ କରେ।",
            "personalizedMatching": "ବ୍ୟକ୍ତିଗତ ଯୋଜନା ମେଳ",
            "ruleBasedEligibility": "ନିୟମ-ଆଧାରିତ ଯୋଗ୍ୟତା ଯାଞ୍ଚ",
            "officialSources": "ସରକାରୀ ସୂତ୍ର",
            "noDocumentUpload": "ଦସ୍ତାବିଜ ଅପଲୋଡ୍ ଆବଶ୍ୟକ ନାହିଁ",
            "howItWorksTitle": "ଯୋଜନାସେତୁ କିପରି କାମ କରେ",
            "howItWorksSub": "ଯୋଜନା ଖୋଜିବା ଏବଂ ଆବେଦନ କରିବା ପାଇଁ ୪-ପଦକ୍ଷେପ ପ୍ରକ୍ରିୟା।",
            "stepTellUs": "ଆପଣଙ୍କ ବିଷୟରେ କୁହନ୍ତୁ",
            "stepTellUsDesc": "କୌଣସି ଦସ୍ତାବିଜ ବିନା ସମ୍ପୂର୍ଣ୍ଣ ଗୋପନୀୟତା ସହିਤ ଆପଣଙ୍କ ବିବରଣୀ ସେୟାର କରନ୍ତୁ।",
            "stepCheckEligibility": "ଯୋଗ୍ୟତା ଯାଞ୍ଚ କରନ୍ତୁ",
            "stepCheckEligibilityDesc": "ସରକାରୀ ଯୋଜନା ନିୟମ ସହିତ ଆମର ନିୟମ ଇଞ୍ଜିନ୍ ଯାଞ୍ଚ କରେ।",
            "stepDiscoverSchemes": "ଉପଯୁକ୍ତ ଯୋଜନା ପାଆନ୍ତୁ",
            "stepDiscoverSchemesDesc": "ସ୍ପଷ୍ଟ କାରଣ ଏବଂ ଆର୍ଥିକ ଲାଭ ସହିତ ଯୋଜନା ତାଲିକା ପାଆନ୍ତୁ।",
            "stepOfficialRoute": "ସରକାରୀ ଆବେଦନ ପ୍ରକ୍ରିୟା",
            "stepOfficialRouteDesc": "ମନ୍ତ୍ରଣାଳୟ ପୋର୍ଟାଲରେ ସିଧାସଳଖ ଆବେଦନ କରନ୍ତୁ କିମ୍ବା ସହାୟତା କେନ୍ଦ୍ର ଖୋଜନ୍ତୁ।",
            "exploreByCategory": "ବର୍ଗ ଅନୁଯାୟୀ ଯୋଜନା ଦେଖନ୍ତୁ",
            "exploreByCategorySub": "ବିଭିନ୍ନ କ୍ଷେତ୍ର ଏବଂ ବୃତ୍ତି ଅନୁଯାୟୀ ପ୍ରସ୍ତୁତ ସରକାରୀ କଲ୍ୟାଣକାରୀ ଯୋଜନା।",
            "trustBadge": "ସରକାରୀ ସୂଚନା ବ୍ୟବସ୍ଥା",
            "trustTitle": "ସରକାରୀ ଗେଜେଟ୍ ଏବଂ ପୋର୍ଟାଲରୁ ପ୍ରମାଣିତ",
            "trustDesc": "ଯୋଜନାସେତୁ ଏକ ନାଗରିକ-ପ୍ରଯୁକ୍ତିବିଦ୍ୟା ପୋର୍ଟାଲ ଯାହା ନିର୍ଭରଯୋଗ୍ୟ ଯୋଗ୍ୟତା ମାର୍ଗଦର୍ଶନ ପ୍ରଦାନ କରେ।",
            "trustPillar1": "ଗେଜେଟ୍ ପ୍ରମାଣିତ",
            "trustPillar1Desc": "ପ୍ରତ୍ୟେକ ଯୋଜନା ସରକାରୀ ବିଜ୍ଞପ୍ତି ସହିତ ଯୋଡା ଯାଇଛି।",
            "trustPillar2": "ନିୟମ-ଆଧାରିତ ଇଞ୍ଜିନ୍",
            "trustPillar2Desc": "ସ୍ୱଚ୍ଛ ଯୋଗ୍ୟତା ମୂଲ୍ୟାଙ୍କନ।",
            "trustPillar3": "ଅଧିକୃତ ଅଂଶୀଦାର",
            "trustPillar3Desc": "୧୨୦+ ପ୍ରମାଣିତ ରାଜ୍ୟ ସଂସ୍ଥା ଏବଂ ବ୍ୟାଙ୍କ ସହାୟତା କେନ୍ଦ୍ର।",
            "trustPillar4": "ଗୋପନୀୟତା ପ୍ରଥମ",
            "trustPillar4Desc": "ଯୋଜନା ଖୋଜିବା ପାଇଁ ଦସ୍ତାବିଜ କିମ୍ବା ଆଧାର ଆବଶ୍ୟକ ନାହିଁ।",
            "finalCtaTitle": "ଆପଣଙ୍କ ପାଇଁ ଉପଯୁକ୍ତ ଯୋଜନା ଖୋଜିବାକୁ ପ୍ରସ୍ତୁତ କି?",
            "finalCtaSubtitle": "୨ ମିନିଟରୁ କମ୍ ସମୟ ଲାଗେ। ମାର୍ଗଦର୍ଶନ ପାଇଁ ଉତ୍ତର ଦିଅନ୍ତୁ।",
            "finalCtaButton": "ଉପଯୁକ୍ତ ଯୋଜନା ଖୋଜନ୍ତୁ",
            "popularTitle": "ଲୋକପ୍ରିୟ ଅନୁସନ୍ଧାନ",
            "viewAllSchemes": "ସମସ୍ତ ଯୋଜନା ଦେଖନ୍ତୁ",
            "quickStats": {
                "citizensServed": "ମାର୍ଗଦର୍ଶିତ ନାଗରିକ",
                "financialTools": "ଆର୍ଥିକ କାଲକୁଲେଟର",
                "schemesCount": "ପ୍ରମାଣିତ ଯୋଜନା"
            }
        },
        "auth": {
            "emailLabel": "ଇମେଲ ଠିକଣା",
            "loginButton": "ଲଗ୍ ଇନ୍ କରନ୍ତୁ",
            "passwordLabel": "ପାସୱାର୍ଡ",
            "phoneLabel": "ମୋବାଇଲ୍ ନମ୍ବର",
            "registerButton": "ଖାତା ସୃଷ୍ଟି କରନ୍ତୁ"
        },
        "calculator": {
            "calculateButton": "ଇଏମଆଇ ଏବଂ ଲାଭ ଗଣନା କରନ୍ତୁ",
            "limitWarning": "ସର୍ବାଧିକ ଋଣ ସୀମାରୁ ଅଧିକ",
            "loanAmount": "ଋଣ ରାଶି (₹)",
            "monthlyEMI": "ଆନୁମାନିକ ମାସିକ ଇଏମଆଇ",
            "subsidyEstimate": "ଆନୁମାନିକ ସବସିଡି"
        },
        "footer": {
            "copyright": "ସର୍ବସ୍ୱତ୍ୱ ସଂରକ୍ଷିତ। ସରକାରୀ ନାଗରିକ ପଦକ୍ଷେପ।"
        },
        "recommendations": {
            "breakdownLabel": "ଯୋଗ୍ୟତା ବିବରଣୀ",
            "formAge": "ଆପଣଙ୍କ ବୟସ (ବର୍ଷ)",
            "formCategory": "ସାମାଜିକ ବର୍ଗ",
            "formGender": "ଲିଙ୍ଗ",
            "formIncome": "ବାର୍ଷିକ ପାରିବାରିକ ଆୟ (₹)",
            "formOccupation": "ବୃତ୍ତି / କାମ",
            "formState": "ରାଜ୍ୟ / କେନ୍ଦ୍ରଶାସିତ ଅଞ୍ଚଳ",
            "scoreLabel": "ମ୍ୟାଚ୍ ସ୍କୋର",
            "submitForm": "ଉପଯୁକ୍ତ ଯୋଜନା ଖୋଜନ୍ତୁ",
            "threeWaysTitle": "ଯୋଜନା ଖୋଜିବାର ୩ଟି ଉପାୟ"
        },
        "schemes": {
            "benefitTitle": "ଆର୍ଥିକ ଲାଭ ଏବଂ ସହାୟତା",
            "docsTitle": "ଆବଶ୍ୟକ ଦସ୍ତାବିଜ ଏବଂ ପ୍ରମାଣପତ୍ର",
            "eligibilityTitle": "ଯୋଗ୍ୟତା ମାନଦଣ୍ଡ ଏବଂ ସର୍ତ୍ତ",
            "officialPortal": "ସରକାରୀ ଆବେଦନ ପୋର୍ଟାଲ",
            "saveScheme": "ଯୋଜନା ସଂରକ୍ଷଣ କରନ୍ତୁ",
            "saved": "ସଂରକ୍ଷିତ",
            "verifiedBadge": "ପ୍ରମାଣିତ ସରକାରୀ ଯୋଜନା"
        },
        "applications": {
            "appId": "ଆବେଦନ ଆଇଡି",
            "lastUpdated": "ଶେଷ ଅଦ୍ୟତନ",
            "scheme": "ଯୋଜନା",
            "status": "ସ୍ଥିତି",
            "viewDetails": "ବିବରଣୀ ଦେଖନ୍ତୁ"
        }
    },
    "as": {
        "home": {
            "findMatchingSchemes": "উপযুক্ত আঁচনি বিচাৰক",
            "exploreAllSchemes": "সকলো আঁচনি চাওক",
            "matchingFlow": "ব্যক্তিগতকৃত আঁচনি মিলোৱা",
            "smartMatchingTitle": "আপুনি যোগ্য হ'ব পৰা চৰকাৰী আঁচনিবোৰ বিচাৰক",
            "smartMatchingDescription": "আপোনাৰ বয়স, শ্ৰেণী, ৰাজ্য, বৃত্তি আৰু ব্যৱসায়িক প্ৰয়োজনীয়তা সম্পৰ্কে কিছুমান সহজ প্ৰশ্নৰ উত্তৰ দিয়ক। যোজনা সেতুৱে চৰকাৰী নিয়ম অনুসৰি আপোনাৰ যোগ্যতা পৰীক্ষা কৰে।",
            "personalizedMatching": "ব্যক্তিগতকৃত আঁচনি মিলোৱা",
            "ruleBasedEligibility": "নিয়ম-ভিত্তিক যোগ্যতা পৰীক্ষা",
            "officialSources": "চৰকাৰী আনুষ্ঠানিক উৎস",
            "noDocumentUpload": "নথি আপলোড কৰাৰ প্ৰয়োজন নাই",
            "howItWorksTitle": "যোজনা সেতু কেনেকৈ কাম কৰে",
            "howItWorksSub": "আঁচনি বিচাৰি পোৱা আৰু আবেদন কৰাৰ ৪-পদক্ষেপৰ স্বচ্ছ প্ৰক্ৰিয়া।",
            "stepTellUs": "আপোনাৰ বিষয়ে কওক",
            "stepTellUsDesc": "কোনো নথি দাখিল নকৰাকৈ সম্পূৰ্ণ গোপনীয়তাত আপোনাৰ তথ্য দিয়ক।",
            "stepCheckEligibility": "যোগ্যতা পৰীক্ষা কৰক",
            "stepCheckEligibilityDesc": "আমাৰ নিয়ম ইঞ্জিন চৰকাৰী নিয়মৰ সৈতে আপোনাৰ তথ্য পৰীক্ষা কৰে।",
            "stepDiscoverSchemes": "উপযুক্ত আঁচনি বিচাৰি পাওক",
            "stepDiscoverSchemesDesc": "স্পষ্ট কাৰণ আৰু বিত্তীয় সুবিধাৰ সৈতে আঁচনিৰ তালিকা লাভ কৰক।",
            "stepOfficialRoute": "আনুষ্ঠানিক আবেদন পথ",
            "stepOfficialRouteDesc": "মন্ত্রণালয়ৰ পৰ্টেলত পোনপটীয়াকৈ আবেদন কৰক বা স্থানীয় সহায় কেন্দ্ৰ বিচাৰক।",
            "exploreByCategory": "শ্ৰেণী অনুসৰি আঁচনি চাওক",
            "exploreByCategorySub": "বিভিন্ন খণ্ড আৰু বৃত্তিৰ বাবে নিৰ্ধাৰিত চৰকাৰী কল্যাণমূলক আঁচনি।",
            "trustBadge": "আনুষ্ঠানিক তথ্য ব্যৱস্থা",
            "trustTitle": "চৰকাৰী গেজেট আৰু পৰ্টেলৰ পৰা প্ৰমাণিত",
            "trustDesc": "যোজনা সেতু হৈছে চৰকাৰী নিৰ্দেশনাৰ পৰা সঠিক যোগ্যতা নিৰ্দেশনা প্ৰদান কৰা এটা নাগৰিক-প্ৰযুক্তি মঞ্চ।",
            "trustPillar1": "গেজেট প্ৰমাণিত",
            "trustPillar1Desc": "প্ৰতিটো আঁচনি আনুষ্ঠানিক অধিসূচনাৰ সৈতে সংযুক্ত।",
            "trustPillar2": "নিয়ম-ভিত্তিক ইঞ্জিন",
            "trustPillar2Desc": "স্বচ্ছ যোগ্যতা মূল্যায়ন।",
            "trustPillar3": "অনুমোদিত অংশীদাৰ",
            "trustPillar3Desc": "১২০+ প্ৰমাণিত ৰাজ্যিক সংস্থা আৰু বেংক সাহায্য কেন্দ্ৰ।",
            "trustPillar4": "গোপনীয়তা প্ৰথম",
            "trustPillar4Desc": "আঁচনি বিচাৰিবলৈ কোনো নথি বা আধাৰৰ প্ৰয়োজন নাই।",
            "finalCtaTitle": "আপোনাৰ বাবে উপযুক্ত আঁচনি বিচাৰিবলৈ সাজু নেকি?",
            "finalCtaSubtitle": "২ মিনিটতকৈ কম সময় লাগে। নিৰ্দেশনা পাবলৈ উত্তৰ দিয়ক।",
            "finalCtaButton": "উপযুক্ত আঁচনি বিচাৰক",
            "popularTitle": "জনপ্ৰিয় সন্ধান",
            "viewAllSchemes": "সকলো আঁচনি চাওক",
            "quickStats": {
                "citizensServed": "সহায়প্ৰাপ্ত নাগৰিক",
                "financialTools": "বিত্তীয় কেলকুলেটৰ",
                "schemesCount": "প্ৰমাণিত আঁচনি"
            }
        },
        "auth": {
            "emailLabel": "ইমেইল ঠিকনা",
            "loginButton": "লগইন কৰক",
            "passwordLabel": "পাছৱৰ্ড",
            "phoneLabel": "ম'বাইল নম্বৰ",
            "registerButton": "একাউণ্ট সৃষ্টি কৰক"
        },
        "calculator": {
            "calculateButton": "ইএমআই আৰু লাভৰ হিচাপ কৰক",
            "limitWarning": "সৰ্বাধিক ঋণৰ সীমাতকৈ অধিক",
            "loanAmount": "ঋণৰ পৰিমাণ (₹)",
            "monthlyEMI": "আনুমানিক মাহেকীয়া ইএমআই",
            "subsidyEstimate": "আনুমানিক ৰাজসাহায্য"
        },
        "footer": {
            "copyright": "সকলো স্বত্ব সংৰক্ষিত। চৰকাৰী নাগৰিক উদ্যোগ।"
        },
        "recommendations": {
            "breakdownLabel": "যোগ্যতাৰ বিৱৰণ",
            "formAge": "আপোনাৰ বয়স (বছৰ)",
            "formCategory": "সামাজিক শ্ৰেণী",
            "formGender": "লিংগ",
            "formIncome": "বাৰ্ষিক পাৰিবাৰিক আয় (₹)",
            "formOccupation": "বৃত্তি / কাম",
            "formState": "ৰাজ্য / কেন্দ্ৰীয় শাসিত অঞ্চল",
            "scoreLabel": "মিলৰ স্ক'ৰ",
            "submitForm": "উপযুক্ত আঁচনি বিচাৰক",
            "threeWaysTitle": "আঁচনি বিচাৰিবলৈ ৩টা উপায়"
        },
        "schemes": {
            "benefitTitle": "বিত্তীয় সুবিধা আৰু সাহাৰ্য",
            "docsTitle": "প্ৰয়োজনীয় নথি আৰু প্ৰমাণ",
            "eligibilityTitle": "যোগ্যতাৰ মাপকাঠী আৰু চৰ্ত",
            "officialPortal": "আনুষ্ঠানিক আবেদন পৰ্টেল",
            "saveScheme": "আঁচনি সংৰক্ষণ কৰক",
            "saved": "সংৰক্ষিত",
            "verifiedBadge": "প্ৰমাণিত চৰকাৰী আঁচনি"
        },
        "applications": {
            "appId": "আবেদন আইডি",
            "lastUpdated": "অন্তিম নবীকৰণ",
            "scheme": "আঁচনি",
            "status": "স্থিতি",
            "viewDetails": "বিৱৰণ চাওক"
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

def run_sync():
    print("Hardening all 12 translation files...")
    for lang, pack in TRANSLATION_PACK.items():
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.exists(file_path):
            print(f"Skipping missing file {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        deep_merge(data, pack)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Successfully synced {lang}.json")

if __name__ == "__main__":
    run_sync()
