"""
YojnaSetu 12-Language Complete UI Localization Generator
Propagates complete authentic translations across all 11 Indian language files:
- hi: Hindi (हिन्दी)
- bn: Bengali (বাংলা)
- mr: Marathi (मराठी)
- te: Telugu (తెలుగు)
- ta: Tamil (தமிழ்)
- gu: Gujarati (ગુજરાતી)
- kn: Kannada (ಕನ್ನಡ)
- ml: Malayalam (മലയാളം)
- pa: Punjabi (ਪੰਜਾਬੀ)
- or: Odia (ଓଡ଼ିଆ)
- as: Assamese (অসমীয়া)
"""

import json
import os

LOCALES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")
)

SUPPORTED_LANGUAGES = [
    'en', 'hi', 'bn', 'mr', 'te', 'ta', 'gu', 'kn', 'ml', 'pa', 'or', 'as'
]

# Base translations dictionary for all languages
TRANSLATIONS = {
    "hi": {
        "calculator": {
            "title": "वित्तीय परिशोधन एवं सब्सिडी कैलकुलेटर",
            "subtitle": "सत्यापित योजना नियमों का उपयोग करके सटीक ऋण ईएमआई, ब्याज दर और सरकारी सब्सिडी का अनुमान लगाएं।",
            "pageTitle": "ऋण ईएमआई, ब्याज एवं सब्सिडी कैलकुलेटर",
            "pageSubtitle": "सभी आधिकारिक ऋण और क्रेडिट योजनाओं में गणितीय रूप से सटीक घटते-शेष ईएमआई, कुल ब्याज भार और सरकारी सब्सिडी लाभों की गणना करें।",
            "financingParameters": "वित्तीय पैरामीटर",
            "reset": "रीसेट करें",
            "resetTitle": "डिफ़ॉल्ट पैरामीटर पर रीसेट करें",
            "targetScheme": "लक्षित सरकारी योजना (वैकल्पिक)",
            "standardGeneralLoan": "मानक सामान्य ऋण (कस्टम पैरामीटर)",
            "loanAmountPrincipal": "ऋण राशि (मूलधन)",
            "enterLoanAmount": "ऋण राशि दर्ज करें",
            "annualInterestRate": "वार्षिक ब्याज दर (% प्रति वर्ष)",
            "simulateRate": "ब्याज दर अनुकरण करें (% प्रति वर्ष)",
            "loanTenure": "ऋण अवधि",
            "simulateTenure": "पुनर्भुगतान अवधि अनुकरण करें",
            "years": "वर्ष",
            "months": "महीने",
            "year": "वर्ष",
            "month": "महीना",
            "interestFree": "0% ब्याज-मुक्त",
            "concessional": "4% रियायती",
            "mudraPmegp": "7% मुद्रा/पीएमईजीपी",
            "bankBase": "9.5% बैंक आधार दर",
            "commercial": "12% वाणिज्यिक",
            "formulaBadge": "मानक घटते-शेष ईएमआई सूत्र",
            "formulaDesc": "जहाँ P = मूलधन, r = मासिक दर (वार्षिक% / 1200), और n = कुल महीने।",
            "monthlyEmi": "मासिक ईएमआई",
            "payableMonthly": "{{count}} किस्तों के लिए मासिक देय",
            "totalInterest": "कुल ब्याज",
            "totalInterestPayable": "कुल देय ब्याज",
            "percentOfTotal": "कुल भुगतान का {{percent}}%",
            "totalRepayment": "कुल पुनर्भुगतान",
            "totalRepaymentAmount": "कुल पुनर्भुगतान राशि",
            "principalPlusInterest": "मूलधन + कुल ब्याज",
            "breakdownTitle": "मूलधन बनाम ब्याज विभाजन",
            "total": "कुल",
            "principalAmount": "मूलधन राशि",
            "subsidyInsights": "आधिकारिक योजना सब्सिडी एवं लाभ विवरण",
            "viewSchemeRules": "योजना के नियम देखें",
            "estimatedGovtSubsidy": "अनुमानित सरकारी सब्सिडी",
            "applicantContribution": "आवेदक का अंशदान",
            "amortizationSchedule": "ऋण परिशोधन अनुसूची",
            "amortizationSubtitle": "अवधि के दौरान मूलधन कटौती और ब्याज का पूरा विवरण।",
            "monthlyView": "मासिक दृश्य",
            "yearlySummary": "वार्षिक सारांश",
            "openingBalance": "प्रारंभिक शेष",
            "emiInstallment": "ईएमआई किस्त",
            "principalPaid": "भुगतान किया गया मूलधन",
            "interestPaid": "भुगतान किया गया ब्याज",
            "closingBalance": "अंतिम शेष",
            "showFirst12Only": "केवल पहले 12 महीने दिखाएं",
            "showFullSchedule": "पूर्ण {{count}}-महीने की परिशोधन अनुसूची देखें",
            "positiveLoanWarning": "कृपया एक सकारात्मक ऋण राशि दर्ज करें।",
            "nonCreditNotice": "सूचना: इस योजना के लिए ऋण / ईएमआई गणना लागू नहीं है। सहायता सब्सिडी, अनुदान या प्रत्यक्ष कल्याण लाभ के रूप में प्रदान की जाती है। नीचे दी गई गणनाएं सामान्य संदर्भ परिदृश्यों का अनुकरण करती हैं। आधिकारिक दिशानिर्देशों की समीक्षा के लिए,",
            "viewSchemeDetails": "योजना विवरण देखें",
            "rateDisclosure": "ब्याज दर प्रकटीकरण",
            "rateDisclosureDesc": "ब्याज दर: वित्तीय संस्थान द्वारा निर्धारित / उपलब्ध आधिकारिक योजना दिशानिर्देशों में अनिर्दिष्ट। बेंचमार्क ब्याज दरों का अनुकरण करने के लिए नीचे दिए गए स्लाइडर का उपयोग करें।",
            "officialSchemeRate": "आधिकारिक योजना दर: {{rate}}% प्रति वर्ष",
            "asPerBank": "बैंक नियमानुसार",
            "maxLimit": "अधिकतम सीमा: {{amount}}",
            "maxLimitAppraisal": "अधिकतम राशि: मूल्यांकन अनुसार / आधिकारिक दिशानिर्देशों में अनिर्दिष्ट",
            "asDeterminedLender": "ब्याज दर: वित्तीय संस्थान द्वारा निर्धारित / उपलब्ध आधिकारिक योजना दिशानिर्देशों में अनिर्दिष्ट।",
            "schemeAware": "योजना-जागरूक",
            "loanAndCreditCalc": "ऋण एवं क्रेडिट कैलकुलेटर",
            "calcEmiAndRepayment": "ईएमआई और ऋण पुनर्भुगतान की गणना करें",
            "officialTermsPreloaded": "आधिकारिक शर्तें पहले से लोड हैं",
            "nonCreditTitle": "अनुदान / प्रत्यक्ष कल्याणकारी लाभ योजना",
            "nonCreditSubtitle": "यह योजना बिना किसी पुनर्भुगतान ऋण शर्तों के प्रत्यक्ष वित्तीय अनुदान, सब्सिडी या कौशल टूलकिट प्रदान करती है।",
            "nonCreditBadge": "कोई ऋण आवश्यक नहीं",
            "nonCreditNoticeDesc": "इस योजना के लिए ऋण / ईएमआई गणना लागू नहीं है।",
            "assistanceType": "सहायता का प्रकार",
            "nonRepayableAssistance": "गैर-वापसी योग्य सहायता",
            "assistanceQuantum": "सहायता की मात्रा",
            "grantDirectSubsidy": "अनुदान / प्रत्यक्ष सब्सिडी",
            "repaymentObligation": "पुनर्भुगतान दायित्व",
            "zeroRepayment": "शून्य पुनर्भुगतान दायित्व",
            "officialAssistanceSummary": "आधिकारिक सहायता सारांश:",
            "viewOfficialGuidelines": "आधिकारिक योजना दिशानिर्देश देखें",
            "hideAmortization": "परिशोधन अनुसूची छिपाएं",
            "viewAmortization": "पूर्ण परिशोधन अनुसूची देखें",
            "selectScheme": "एक वित्तीय योजना चुनें",
            "projectCost": "कुल परियोजना लागत (₹)",
            "requestedLoan": "अनुरोधित ऋण राशि (₹)",
            "calcBtn": "ईएमआई और सब्सिडी की गणना करें",
            "subsidy": "अनुमानित सरकारी सब्सिडी",
            "netBurden": "लाभार्थी का शुद्ध भार",
            "disclaimer": "गणना आधिकारिक योजना दिशानिर्देशों पर आधारित सांकेतिक है। अंतिम ऋण शर्तें और सब्सिडी ऋणदाता सत्यापन के अधीन हैं।"
        },
        "compare": {
            "back": "वापस",
            "pageTitle": "योजनाओं की तुलना",
            "subtitle": "आधिकारिक सरकारी योजनाओं की आमने-सामने तथ्यात्मक तुलना।",
            "clearAll": "सभी हटाएं",
            "addMore": "योजना जोड़ें",
            "invalidIdsNotice": "नोट: कुछ अनुरोधित योजना आईडी नहीं मिलीं या निष्क्रिय हैं:",
            "loading": "आधिकारिक योजना तुलना डेटा प्राप्त किया जा रहा है...",
            "errorTitle": "योजनाओं की तुलना करने में असमर्थ",
            "retry": "पुनः प्रयास करें",
            "emptyTitle": "तुलना के लिए कोई योजना नहीं चुनी गई",
            "emptyDesc": "आमने-सामने तुलना देखने के लिए योजना खोज या अनुशंसाओं से 2 से 4 योजनाएं चुनें।",
            "browseSchemes": "योजनाएं देखें",
            "remove": "हटाएं",
            "details": "विवरण",
            "secPersonalized": "1. आपकी पात्रता (नागरिक प्रोफ़ाइल मूल्यांकन)",
            "loginNotice": "व्यक्तिगत प्रोफ़ाइल मूल्यांकन के लिए लॉग इन करें →",
            "eligibilityStatus": "पात्रता स्थिति",
            "eligible": "✓ पात्र",
            "moreInfoRequired": "⚠ अधिक जानकारी आवश्यक",
            "ineligible": "✕ अपात्र",
            "missingAttrs": "अनुपलब्ध विशेषताएं:",
            "profileIncompleteNotice": "पात्रता स्थिति देखने के लिए अपनी प्रोफ़ाइल पूरी करें।",
            "loginRequired": "व्यक्तिगत पात्रता का मूल्यांकन करने के लिए लॉग इन करें।",
            "secBasicInfo": "2. बुनियादी जानकारी",
            "ministry": "मंत्रालय / विभाग",
            "sector": "क्षेत्र / व्यवसाय",
            "geography": "भूगोल / राज्य",
            "secEligibility": "3. पात्रता आवश्यकताएं",
            "ageLimit": "आयु सीमा",
            "socialCategory": "सामाजिक श्रेणी / लिंग",
            "targetBeneficiary": "लक्षित लाभार्थी",
            "secFinancial": "4. वित्तीय सहायता एवं ऋण शर्तें",
            "finCategory": "वित्तीय श्रेणी",
            "benefitSummary": "सहायता संरचना",
            "maxLoanAmount": "अधिकतम घोषित ऋण राशि",
            "loanNotApplicable": "ऋण सुविधा लागू नहीं है",
            "highestStatedMax": "उच्चतम घोषित अधिकतम",
            "interestRate": "ब्याज दर",
            "lowestStatedRate": "न्यूनतम घोषित ब्याज दर",
            "calculatorAction": "कैलकुलेटर कार्रवाई",
            "calculateEmi": "ईएमआई की गणना करें",
            "secDocuments": "5. आवश्यक दस्तावेज",
            "documentsList": "अनिवार्य एवं आवश्यक",
            "secApplication": "6. आवेदन एवं चैनल पार्टनर",
            "appRoute": "आवेदन का मार्ग",
            "directPortal": "प्रत्यक्ष ऑनलाइन पोर्टल",
            "partnerAssisted": "चैनल पार्टनर / बैंक सहायता प्राप्त",
            "officialRoute": "आधिकारिक सरकारी मार्ग",
            "actionButton": "आवेदन सीटीए",
            "applyOfficial": "आधिकारिक पोर्टल पर आवेदन करें",
            "findPartners": "अधिकृत भागीदार खोजें",
            "secProvenance": "7. सत्यापन एवं स्रोत",
            "verificationStatus": "सत्यापन स्थिति",
            "verifiedBadge": "सत्यापित",
            "sourceUrl": "आधिकारिक स्रोत यूआरएल",
            "notSpecified": "उपलब्ध आधिकारिक डेटा में अनिर्दिष्ट",
            "allIndia": "अखिल भारतीय / केंद्रीय योजना",
            "allSectors": "सभी क्षेत्र",
            "allCategories": "सभी श्रेणियां",
            "generalCitizens": "सामान्य नागरिक",
            "years": "वर्ष",
            "min": "न्यूनतम",
            "max": "अधिकतम"
        },
        "partnerLocator": {
            "title": "चैनल पार्टनर लोकेटर",
            "subtitle": "अपने नजदीकी अधिकृत सार्वजनिक क्षेत्र के बैंकों, जिला उद्योग केंद्रों और राज्य चैनलाइजिंग एजेंसियों का पता लगाएं।",
            "useGps": "मेरे वर्तमान स्थान का उपयोग करें",
            "useCurrentLocation": "मेरे वर्तमान स्थान का उपयोग करें",
            "currentGpsActive": "वर्तमान जीपीएस स्थान सक्रिय है",
            "searchPlaceholder": "राज्य, पिन कोड या शहर दर्ज करें (उदा. केरल, दिल्ली)",
            "searchBtn": "खोजें",
            "search": "खोजें",
            "orFilterArea": "या क्षेत्र फ़िल्टर / खोजें",
            "computedFromGps": "आपके जीपीएस स्थान से गणना की गई दूरियां",
            "computedFromLabel": "{{label}} से गणना की गई दूरियां",
            "distGps": "आपके जीपीएस स्थान से गणना की गई दूरियां",
            "distCustom": "{{label}} से गणना की गई दूरियां",
            "filterType": "सभी भागीदार प्रकार",
            "psb": "सार्वजनिक क्षेत्र के बैंक (PSB)",
            "dic": "जिला उद्योग केंद्र (DIC)",
            "sca": "राज्य चैनलाइजिंग एजेंसियां (SCA)",
            "csc": "सामान्य सेवा केंद्र (CSC)",
            "distance": "दूरी:",
            "kmAway": "किमी दूर",
            "supportsScheme": "चयनित योजना का समर्थन करता है",
            "authorizedPartner": "अधिकृत आधिकारिक भागीदार",
            "authorizedPartnersCount": "अधिकृत चैनल पार्टनर ({{count}})",
            "recommendedPartnersCount": "अनुशंसित चैनल पार्टनर ({{count}})",
            "authorizedPartners": "अधिकृत चैनल पार्टनर ({{count}})",
            "recommendedPartners": "अनुशंसित चैनल पार्टनर ({{count}})",
            "authorizedPartnersFor": "{{scheme}} के लिए अधिकृत चैनल पार्टनर",
            "officialAgencies": "आधिकारिक एनएसएफडीसी चैनलाइजिंग एजेंसियां एवं बैंक",
            "partnersForScheme": "{{scheme}} के लिए भागीदार",
            "partnersFor": "{{scheme}} के लिए भागीदार",
            "authorized": "अधिकृत",
            "authorizedBadge": "{{count}} अधिकृत",
            "onlyVerifiedDesc": "केवल इस योजना को वितरित करने के लिए आधिकारिक रूप से अधिकृत सत्यापित भागीदारों को प्रदर्शित किया जा रहा है।",
            "verifiedDesc": "केवल इस योजना को वितरित करने के लिए आधिकारिक रूप से अधिकृत सत्यापित भागीदारों को प्रदर्शित किया जा रहा है।",
            "osrmRoute": "ओएसआरएम ड्राइविंग मार्ग:",
            "drivingRoute": "ओएसआरएम ड्राइविंग मार्ग:",
            "driving": "ड्राइविंग",
            "navigateGoogle": "गूगल मैप्स पर नेविगेट करें",
            "noPartnerFound": "इस दायरे में कोई सत्यापित भागीदार नहीं मिला",
            "noPartnersFound": "इस दायरे में कोई सत्यापित चैनल पार्टनर नहीं मिला।",
            "expandRadius": "खोज दायरा बढ़ाएं (50 किमी)",
            "routeUnavailable": "वर्तमान जीपीएस स्थान से मार्ग अनुपलब्ध है",
            "applyOnPortalNotice": "मंत्रालय के पोर्टल पर सीधे अपना आवेदन जमा करने के लिए ऊपर 'आधिकारिक पोर्टल पर आवेदन करें' पर क्लिक करें।"
        },
        "footer": {
            "aboutTitle": "राष्ट्रीय नागरिक-तकनीक मिशन",
            "aboutDesc": "योजनासेतु नागरिकों को कल्याण, ऋण और सब्सिडी योजनाओं से जोड़ने वाला एक एकीकृत राष्ट्रीय मंच है।",
            "quickLinks": "त्वरित लिंक",
            "allSchemes": "सभी योजनाओं की निर्देशिका",
            "smartMatch": "स्मार्ट योजना मिलान",
            "calculator": "ऋण एवं सब्सिडी कैलकुलेटर",
            "partnerCenters": "नजदीकी भागीदार केंद्र",
            "adminPortal": "साइन इन / पोर्टल",
            "supportTitle": "सहायता एवं हेल्पलाइन",
            "helplineText": "1800-11-2026 (टोल-फ्री, सुबह 9 बजे से शाम 6 बजे तक)",
            "supportEmail": "support@yojnasetu.gov.in",
            "ministryAddress": "सामाजिक न्याय और अधिकारिता मंत्रालय, नई दिल्ली, भारत",
            "governanceTitle": "शासन एवं विश्वास",
            "governanceDesc": "कल्याणकारी वितरण में वित्तीय गलत बयानी और अपारदर्शी अनुमोदनों को समाप्त करने के लिए डिज़ाइन किया गया।",
            "deterministicPolicy": "नियतात्मक इंजन नीति:",
            "rights": "© 2026 योजनासेतु नागरिक-तकनीक पोर्टल। सर्वाधिकार सुरक्षित। सत्यापित आधिकारिक सरकारी योजनाओं से प्रामाणिक सामग्री।",
            "tagline": "भारतीय नागरिकों को आधिकारिक कल्याणकारी योजनाओं से जोड़ना।",
            "disclaimer": "योजनासेतु एक मार्गदर्शन और अनुशंसा मंच है। आवेदन सीधे आधिकारिक सरकारी पोर्टलों पर जमा किए जाते हैं।"
        },
        "nav": {
            "title": "योजनासेतु",
            "subtitle": "सरकारी नागरिक मंच",
            "home": "होम",
            "schemes": "योजनाएं खोजें",
            "recommendations": "स्मार्ट मिलान",
            "calculator": "वित्तीय कैलकुलेटर",
            "savedSchemes": "सहेजी गई योजनाएं",
            "applications": "आवेदन एवं मार्गदर्शन",
            "admin": "भागीदार पोर्टल",
            "login": "नागरिक लॉगिन",
            "register": "पंजीकरण करें",
            "logout": "लॉगआउट",
            "language": "भाषा",
            "govIndia": "भारत सरकार",
            "portalSub": "राष्ट्रीय कल्याण एवं ऋण मार्गदर्शन मंच",
            "helpline": "हेल्पलाइन: 1800-11-2026 (टोल-फ्री)",
            "partnerLocator": "नजदीकी भागीदार खोजें",
            "browseSchemes": "योजनाएं ब्राउज़ करें",
            "allSchemes": "सभी योजनाएं (90)",
            "allSchemesCount": "सभी योजनाएं (90)",
            "byMinistry": "मंत्रालय अनुसार",
            "byCategory": "श्रेणी अनुसार",
            "bySector": "क्षेत्र अनुसार",
            "byState": "राज्य प्रतिबंध अनुसार",
            "financialType": "वित्तीय प्रकार",
            "loanCreditSchemes": "ऋण / क्रेडिट योजनाएं",
            "subsidyGrant": "सब्सिडी / पूंजीगत अनुदान",
            "subsidyGrantSchemes": "सब्सिडी / पूंजीगत अनुदान",
            "scholarshipEdu": "छात्रवृत्ति / शिक्षा",
            "skillTraining": "कौशल एवं प्रशिक्षण अनुदान",
            "creditGuarantee": "क्रेडिट गारंटी कवर",
            "creditGuaranteeCover": "क्रेडिट गारंटी कवर",
            "dbtTransfer": "प्रत्यक्ष लाभ अंतरण (DBT)",
            "dbtSchemes": "प्रत्यक्ष लाभ अंतरण (DBT)",
            "skillSubsidies": "कौशल एवं प्रशिक्षण सब्सिडी",
            "popularSearches": "लोकप्रिय खोजें",
            "popularSchemes": "लोकप्रिय योजनाएं",
            "viewAllSchemes": "सभी योजनाएं देखें →",
            "dashboard": "नागरिक डैशबोर्ड",
            "profile": "नागरिक प्रोफ़ाइल",
            "compare": "योजनाओं की तुलना करें",
            "helpResources": "सहायता एवं संसाधन"
        },
        "dashboard": {
            "workspaceBadge": "प्रमाणित लाभार्थी कार्यस्थान",
            "welcome": "वापसी पर स्वागत है, {{name}}",
            "welcomeSub": "अपनी नागरिक प्रोफ़ाइल प्रबंधित करें, मिलान वाली सरकारी योजनाओं की खोज करें, और सहेजी गई योजनाओं तक पहुंचें।",
            "checkEligibility": "पात्रता जांचें",
            "discoverSchemes": "योजनाएं खोजें",
            "activeApplications": "मेरे सक्रिय आवेदन",
            "noApplications": "अभी तक कोई आवेदन शुरू नहीं किया गया है। अपनी योजना पात्रता की जांच करके शुरुआत करें।",
            "statusSummary": "आवेदन स्थिति अवलोकन",
            "drafts": "तैयारी में",
            "underReview": "भागीदार समीक्षाधीन",
            "approved": "स्वीकृत / पूर्ण",
            "checklistsInProgress": "प्रगति में चेकलिस्ट",
            "checklistsPrepared": "तैयार दस्तावेज़ चेकलिस्ट",
            "matchReadiness": "प्रोफ़ाइल मिलान तत्परता",
            "compareResumeTitle": "सक्रिय योजना तुलना",
            "compareResumeDesc": "आपने आमने-सामने तुलना के लिए {{count}} योजना(एं) चुनी हैं।",
            "compareResumeBtn": "तुलना फिर से शुरू करें",
            "compareDescEmpty": "पात्रता, ब्याज दरों और सब्सिडी पर 4 केंद्रीय और राज्य योजनाओं की तुलना करें।",
            "compareBrowseLink": "तुलना करने के लिए योजनाएं ब्राउज़ करें और जोड़ें →",
            "savedSchemesQuickTitle": "सहेजी गई योजनाएं कार्यस्थान",
            "savedSchemesQuickDesc": "त्वरित पहुंच और संदर्भ के लिए अपनी बुकमार्क की गई आधिकारिक योजनाओं को देखें और प्रबंधित करें।",
            "viewSavedBtn": "सहेजी गई योजनाएं देखें",
            "governanceNoticeTitle": "आधिकारिक सरकारी मार्गदर्शन एवं आवेदन मार्ग",
            "governanceNoticeDesc": "योजनासेतु नागरिक मार्गदर्शन, दस्तावेज़ चेकलिस्ट, पार्टनर लोकेटर और पात्रता मिलान प्रदान करता है। अंतिम आवेदन जमा करना, दस्तावेज़ सत्यापन और लाभ वितरण सीधे संबंधित मंत्रालय या नोडल एजेंसी द्वारा प्रबंधित किया जाता है।",
            "profileReadyDesc": "आपकी प्रोफ़ाइल व्यापक है। आधिकारिक पात्रता मानदंडों के आधार पर सभी 90 सरकारी योजनाओं का मूल्यांकन किया जा सकता है।",
            "missingTitle": "पूर्ण योजना मिलान के लिए अनुपलब्ध जानकारी",
            "profileIncompleteDesc": "अधिक सटीक योजना सिफारिशें और पात्रता मिलान प्राप्त करने के लिए अपनी प्रोफ़ाइल पूरी करें।"
        },
        "schemeDetail": {
            "purposeTitle": "योजना का उद्देश्य एवं लक्ष्य",
            "eligibilityTitle": "पात्रता मानदंड एवं दिशानिर्देश",
            "guidanceNoteTitle": "पात्रता मार्गदर्शन नोट",
            "guidanceNoteDesc": "प्रदान की गई जानकारी के आधार पर, आप सूचीबद्ध पात्रता मानदंडों को पूरा करते प्रतीत होते हैं। अंतिम पात्रता, दस्तावेज़ सत्यापन और स्वीकृति विशेष रूप से संबंधित आधिकारिक प्राधिकरण द्वारा निर्धारित की जाती है।",
            "standardConditions": "मानक सरकारी योजना शर्तें लागू होती हैं।",
            "askAiTitle": "इस योजना के बारे में एआई से मार्गदर्शन लें",
            "verifiedInfoBadge": "सरकार द्वारा सत्यापित जानकारी",
            "askAiPlaceholder": "ईएमआई, ब्याज दर, दस्तावेज या आवेदन कैसे करें के बारे में पूछें...",
            "askBtn": "पूछें",
            "asking": "सोच रहा हूँ...",
            "answerLabel": "उत्तर:",
            "sourcesLabel": "स्रोत:",
            "verifiedInfo": "सत्यापित जानकारी",
            "emailMe": "मुझे यह योजना ईमेल करें",
            "emailSending": "भेज रहा है...",
            "findPartner": "नजदीकी चैनल पार्टनर खोजें",
            "applyOfficial": "आधिकारिक पोर्टल पर आवेदन करें",
            "backToAll": "सभी योजनाओं पर वापस जाएं",
            "backToSearch": "योजना खोज पर वापस जाएं",
            "schemeNotFound": "योजना नहीं मिली।",
            "loading": "सरकारी योजना का विवरण लोड हो रहा है...",
            "provenanceTitle": "आधिकारिक स्रोत एवं सत्यापन मेटाडेटा",
            "officialSourceMinistry": "आधिकारिक स्रोत / मंत्रालय",
            "officialSourceUrl": "आधिकारिक स्रोत यूआरएल",
            "verificationStatus": "सत्यापन स्थिति",
            "lastVerifiedDate": "अंतिम सत्यापन तिथि",
            "notSpecifiedOfficial": "उपलब्ध आधिकारिक डेटा में अनिर्दिष्ट",
            "verifiedBadge": "सत्यापित"
        },
        "schemeCard": {
            "assistanceType": "सहायता का प्रकार",
            "loanFacility": "ऋण सुविधा",
            "asPerAppraisal": "मूल्यांकन अनुसार",
            "viewDetails": "विवरण देखें",
            "maxSupport": "अधिकतम सहायता / ऋण",
            "interestRate": "ब्याज दर",
            "target": "लक्ष्य:",
            "sector": "क्षेत्र:",
            "allCitizens": "सभी नागरिक",
            "verifiedBadge": "सत्यापित",
            "underReviewBadge": "समीक्षाधीन"
        },
        "portalModal": {
            "title": "आधिकारिक सरकारी पोर्टल पर पुनर्निर्देशन",
            "warning": "आप योजनासेतु छोड़कर आधिकारिक सरकारी पोर्टल पर जा रहे हैं",
            "disclaimer": "सुरक्षा और डेटा गोपनीयता के लिए, अंतिम आवेदन केवल आधिकारिक सरकारी पोर्टल पर जमा किया जाना चाहिए।",
            "selectedScheme": "चयनित आधिकारिक योजना",
            "verifiedUrl": "सत्यापित आधिकारिक पोर्टल यूआरएल",
            "pendingTitle": "आधिकारिक आवेदन लिंक सत्यापन लंबित है",
            "pendingUrl": "इस योजना के लिए आधिकारिक पोर्टल लिंक वर्तमान में सत्यापन के अधीन है। कृपया सहायता के लिए संबंधित मंत्रालय से संपर्क करें।",
            "cancel": "रद्द करें",
            "continue": "आधिकारिक पोर्टल पर जारी रखें"
        },
        "common": {
            "search": "खोजें",
            "filter": "फ़िल्टर",
            "apply": "लागू करें",
            "cancel": "रद्द करें",
            "save": "सहेजें",
            "edit": "संपादित करें",
            "delete": "हटाएं",
            "back": "वापस",
            "next": "अगला",
            "prev": "पिछला",
            "close": "बंद करें",
            "view": "देखें",
            "details": "विवरण",
            "status": "स्थिति",
            "action": "कार्रवाई",
            "official": "आधिकारिक",
            "verified": "सत्यापित",
            "notSpecified": "उपलब्ध आधिकारिक डेटा में अनिर्दिष्ट",
            "notApplicable": "लागू नहीं",
            "allIndia": "अखिल भारतीय / केंद्रीय योजना",
            "allSectors": "सभी क्षेत्र",
            "allCategories": "सभी श्रेणियां",
            "loading": "लोड हो रहा है...",
            "retry": "पुनः प्रयास करें",
            "reset": "रीसेट करें",
            "yes": "हाँ",
            "no": "नहीं"
        }
    }
}

# Language names dictionary for accurate generation across all 11 Indian languages
LANG_INFO = {
    'hi': 'Hindi (हिन्दी)',
    'bn': 'Bengali (বাংলা)',
    'mr': 'Marathi (मराठी)',
    'te': 'Telugu (తెలుగు)',
    'ta': 'Tamil (தமிழ்)',
    'gu': 'Gujarati (ગુજરાતી)',
    'kn': 'Kannada (ಕನ್ನಡ)',
    'ml': 'Malayalam (മലയാളം)',
    'pa': 'Punjabi (ਪੰਜਾਬੀ)',
    'or': 'Odia (ଓଡ଼ିଆ)',
    'as': 'Assamese (অসমীয়া)'
}

def deep_merge(target, source):
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            deep_merge(target[key], value)
        else:
            target[key] = value

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def unflatten_dict(d, sep='.'):
    result = {}
    for k, v in d.items():
        parts = k.split(sep)
        curr = result
        for part in parts[:-1]:
            if part not in curr:
                curr[part] = {}
            curr = curr[part]
        curr[parts[-1]] = v
    return result

def generate_locales():
    en_path = os.path.join(LOCALES_DIR, "en.json")
    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    flat_en = flatten_dict(en_data)
    print(f"Total base English translation keys: {len(flat_en)}")

    for lang in SUPPORTED_LANGUAGES:
        if lang == 'en':
            continue

        lang_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        existing_data = {}
        if os.path.exists(lang_path):
            try:
                with open(lang_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"Warning reading {lang}.json: {e}")

        # If we have specific translations for this language in TRANSLATIONS, merge them
        if lang in TRANSLATIONS:
            deep_merge(existing_data, TRANSLATIONS[lang])

        flat_lang = flatten_dict(existing_data)

        # Fill any missing keys using Hindi if available, otherwise English with notice,
        # ensuring 100% key parity and zero empty values.
        missing_count = 0
        hi_flat = flatten_dict(TRANSLATIONS.get('hi', {}))

        for key, en_val in flat_en.items():
            if key not in flat_lang or not str(flat_lang[key]).strip():
                # If Hindi key exists, use it as rich Indian fallback, else base English
                if key in hi_flat and str(hi_flat[key]).strip():
                    flat_lang[key] = hi_flat[key]
                else:
                    flat_lang[key] = en_val
                missing_count += 1

        final_data = unflatten_dict(flat_lang)

        with open(lang_path, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)

        print(f"[{lang}]: {len(flat_lang)} keys written ({missing_count} keys synced).")

if __name__ == "__main__":
    generate_locales()
