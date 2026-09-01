"""
Synchronizes curated, vertical Compare page translation keys across all 12 locales.
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")

COMPARE_TRANSLATIONS = {
    "en": {
        "secOverview": "Scheme Overview",
        "secOverviewSubtitle": "Core mandate, ministry sponsoring body, and geographical scope",
        "secEligibility": "Eligibility Criteria",
        "secEligibilitySubtitle": "Age, income, social category, and vocational qualification",
        "secFinancial": "Financial Assistance & Credit Terms",
        "secFinancialSubtitle": "Credit ceiling, interest rates, tenure, subsidy, and collateral",
        "secDocuments": "Documents & Proofs",
        "secDocumentsSubtitle": "Mandatory identity, residence, business, and conditional proofs",
        "secApplication": "Application & Access Route",
        "secApplicationSubtitle": "Submission channels, authorized portal links, and channel partners",
        "secVerification": "Verification & Official Coverage",
        "secVerificationSubtitle": "Official gazette audit, statutory source validation, and update recency",
        "secPersonalized": "Your Eligibility Fit",
        "profileAssessmentSubtitle": "Automated assessment based on your registered citizen profile",
        "schemeType": "Scheme Type",
        "ministry": "Ministry / Department",
        "targetBeneficiary": "Target Beneficiary",
        "schemePurpose": "Scheme Purpose & Benefits",
        "geographicCoverage": "Geographic Coverage",
        "ageCriteria": "Age Criteria",
        "incomeLimit": "Income Limit / Ceiling",
        "socialCategory": "Social Category & Gender",
        "occupation": "Sector / Vocation",
        "otherConditions": "Key Conditions",
        "loanAvailable": "Loan Facility Available",
        "creditFacility": "Credit Facility",
        "maxLoan": "Maximum Stated Loan",
        "interestRate": "Interest Rate",
        "tenure": "Repayment Tenure",
        "moratorium": "Moratorium Period",
        "subsidy": "Subsidy / Grant Assistance",
        "marginMoney": "Beneficiary Contribution",
        "collateral": "Collateral Requirement",
        "requiredDocs": "Mandatory Documents",
        "optionalDocs": "Optional / Conditional Proofs",
        "applicationMode": "Application Mode",
        "applicationRoute": "Application Route",
        "officialPortal": "Official Portal",
        "channelAgency": "Implementing Agency",
        "govVerification": "Government Verification",
        "officialSource": "Official Source",
        "lastVerified": "Last Verified Date",
        "notApplicable": "Not applicable",
        "yes": "Yes",
        "no": "No",
        "noCreditWelfare": "No — Grant / Subsidy / Welfare Scheme",
        "compareSchemes": "Compare Schemes",
        "vs": "VS",
        "sameAcrossSchemes": "Same across selected schemes",
        "allIndia": "All India / Central Scheme",
        "noDocsRequired": "Standard KYC & ID Proof only",
        "noOptionalDocs": "No conditional documents specified",
        "noneSpecified": "Not specified in official guidelines",
        "locatePartners": "Find Authorized Partners",
        "openCalculator": "Calculate EMI",
        "months": "months",
        "years": "years",
        "highestStated": "Highest stated",
        "lowestStated": "Lowest stated",
        "clearComparison": "Clear Comparison",
        "removeScheme": "Remove",
        "selectUpTo4": "Compare 2 to 4 schemes side-by-side in clear vertical sections.",
        "noIncomeLimit": "No mandatory income ceiling specified",
        "standardOfficialNorms": "Standard KYC and official ministry guidelines apply",
        "interestSubvention": "Direct interest subvention / credit guarantee",
        "grantAssistance": "Direct benefit transfer / non-loan subsidy",
        "standardMarginMoney": "Standard 5% - 10% or as per lending institution",
        "noCollateral": "No collateral required (Credit Guarantee covered)",
        "collateralNorms": "No collateral for loans up to statutory limits (RBI guidelines)"
    },
    "hi": {
        "secOverview": "योजना का संक्षिप्त विवरण",
        "secOverviewSubtitle": "मूल अधिदेश, मंत्रालय प्रायोजक निकाय और भौगोलिक दायरा",
        "secEligibility": "पात्रता मानदंड",
        "secEligibilitySubtitle": "आयु, आय, सामाजिक वर्ग और व्यावसायिक योग्यता",
        "secFinancial": "वित्तीय सहायता एवं ऋण शर्तें",
        "secFinancialSubtitle": "ऋण सीमा, ब्याज दर, अवधि, सब्सिडी और गारंटी",
        "secDocuments": "दस्तावेज़ एवं प्रमाण",
        "secDocumentsSubtitle": "अनिवार्य पहचान, निवास, व्यवसाय और सशर्त प्रमाण",
        "secApplication": "आवेदन एवं पहुंच माध्यम",
        "secApplicationSubtitle": "आवेदन के माध्यम, आधिकारिक पोर्टल लिंक और चैनल भागीदार",
        "secVerification": "सत्यापन एवं आधिकारिक स्रोत",
        "secVerificationSubtitle": "आधिकारिक राजपत्र ऑडिट, वैधानिक स्रोत सत्यापन और अद्यतन स्थिति",
        "secPersonalized": "आपकी पात्रता का मूल्यांकन",
        "profileAssessmentSubtitle": "आपके पंजीकृत नागरिक प्रोफ़ाइल के आधार पर स्वचालित मूल्यांकन",
        "schemeType": "योजना का प्रकार",
        "ministry": "मंत्रालय / विभाग",
        "targetBeneficiary": "लक्षित लाभार्थी",
        "schemePurpose": "योजना का उद्देश्य एवं लाभ",
        "geographicCoverage": "भौगोलिक दायरा",
        "ageCriteria": "आयु सीमा",
        "incomeLimit": "आय सीमा",
        "socialCategory": "सामाजिक वर्ग एवं लिंग",
        "occupation": "क्षेत्र / व्यवसाय",
        "otherConditions": "मुख्य शर्तें",
        "loanAvailable": "ऋण सुविधा उपलब्ध",
        "creditFacility": "ऋण सुविधा",
        "maxLoan": "अधिकतम ऋण राशि",
        "interestRate": "ब्याज दर",
        "tenure": "पुनर्भुगतान अवधि",
        "moratorium": "मोराटोरियम अवधि",
        "subsidy": "सब्सिडी / अनुदान सहायता",
        "marginMoney": "लाभार्थी अंशदान",
        "collateral": "संपार्श्विक (गारंटी)",
        "requiredDocs": "अनिवार्य दस्तावेज़",
        "optionalDocs": "वैकल्पिक / सशर्त प्रमाण",
        "applicationMode": "आवेदन का तरीका",
        "applicationRoute": "आवेदन मार्ग",
        "officialPortal": "आधिकारिक पोर्टल",
        "channelAgency": "कार्यान्वयन एजेंसी",
        "govVerification": "सरकारी सत्यापन",
        "officialSource": "आधिकारिक स्रोत",
        "lastVerified": "अंतिम सत्यापन तिथि",
        "notApplicable": "लागू नहीं",
        "yes": "हाँ",
        "no": "नहीं",
        "noCreditWelfare": "नहीं — अनुदान / सब्सिडी / कल्याणकारी योजना",
        "compareSchemes": "योजनाओं की तुलना",
        "vs": "बनाम",
        "sameAcrossSchemes": "चुनी गई सभी योजनाओं में समान",
        "allIndia": "अखिल भारतीय / केंद्रीय योजना",
        "noDocsRequired": "केवल मानक केवाईसी एवं पहचान प्रमाण",
        "noOptionalDocs": "कोई सशर्त दस्तावेज़ निर्दिष्ट नहीं",
        "noneSpecified": "आधिकारिक दिशानिर्देशों में अनिर्दिष्ट",
        "locatePartners": "अधिकृत भागीदार खोजें",
        "openCalculator": "ईएमआई कैलकुलेटर",
        "months": "माह",
        "years": "वर्ष",
        "highestStated": "सर्वाधिक घोषित",
        "lowestStated": "न्यूनतम घोषित",
        "clearComparison": "तुलना हटाएं",
        "removeScheme": "हटाएं",
        "selectUpTo4": "2 से 4 योजनाओं की स्पष्ट लंबवत वर्गों में तुलना करें।",
        "noIncomeLimit": "कोई अनिवार्य आय सीमा निर्दिष्ट नहीं",
        "standardOfficialNorms": "मानक केवाईसी और आधिकारिक मंत्रालय दिशानिर्देश लागू",
        "interestSubvention": "प्रत्यक्ष ब्याज छूट / क्रेडिट गारंटी",
        "grantAssistance": "प्रत्यक्ष लाभ अंतरण / गैर-ऋण सब्सिडी",
        "standardMarginMoney": "मानक 5% - 10% या ऋणदाता संस्थान अनुसार",
        "noCollateral": "कोई गारंटी आवश्यक नहीं (क्रेडिट गारंटी योजना कवर्ड)",
        "collateralNorms": "आरबीआई दिशानिर्देशों अनुसार सीमा तक कोई गारंटी नहीं"
    }
}

# Auto-derive other languages from Hindi / English for clean localization
OTHER_LANGS = ["bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]

def sync():
    langs = ["en", "hi"] + OTHER_LANGS
    for lang in langs:
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.exists(file_path):
            print(f"Skipping {file_path}")
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "compare" not in data:
            data["compare"] = {}

        lang_trans = COMPARE_TRANSLATIONS.get(lang, None)
        if not lang_trans:
            # Fallback to English but keep existing translated keys
            lang_trans = COMPARE_TRANSLATIONS["en"]

        for k, v in lang_trans.items():
            if k not in data["compare"] or lang in ["en", "hi"]:
                data["compare"][k] = v

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Synced compare keys for {lang}")

if __name__ == "__main__":
    sync()
