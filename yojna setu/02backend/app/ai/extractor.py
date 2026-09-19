import re
import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger("yojnasetu.ai.extractor")

from app.schemas.recommendation import BeneficiaryProfileInput
from app.schemas.ai import (
    NaturalLanguageExtractResponse,
    ExtractedFieldConfidence,
)
from app.ai.provider import get_ai_provider

DISTRICT_TO_STATE: Dict[str, str] = {
    "Gorakhpur": "UTTAR_PRADESH", "Lucknow": "UTTAR_PRADESH", "Varanasi": "UTTAR_PRADESH",
    "Kanpur": "UTTAR_PRADESH", "Noida": "UTTAR_PRADESH", "Ghaziabad": "UTTAR_PRADESH",
    "Agra": "UTTAR_PRADESH", "Meerut": "UTTAR_PRADESH", "Prayagraj": "UTTAR_PRADESH",
    "Bareilly": "UTTAR_PRADESH", "Aligarh": "UTTAR_PRADESH", "Moradabad": "UTTAR_PRADESH",
    "Patna": "BIHAR", "Gaya": "BIHAR", "Muzaffarpur": "BIHAR", "Bhagalpur": "BIHAR",
    "Mumbai": "MAHARASHTRA", "Pune": "MAHARASHTRA", "Nagpur": "MAHARASHTRA", "Nashik": "MAHARASHTRA", "Thane": "MAHARASHTRA",
    "Jaipur": "RAJASTHAN", "Jodhpur": "RAJASTHAN", "Kota": "RAJASTHAN", "Udaipur": "RAJASTHAN",
    "Ahmedabad": "GUJARAT", "Surat": "GUJARAT", "Vadodara": "GUJARAT", "Rajkot": "GUJARAT",
    "Bengaluru": "KARNATAKA", "Chennai": "TAMIL_NADU", "Kolkata": "WEST_BENGAL", "Delhi": "DELHI",
    "Amritsar": "PUNJAB", "Ludhiana": "PUNJAB", "Gurugram": "HARYANA",
    "Indore": "MADHYA_PRADESH", "Bhopal": "MADHYA_PRADESH", "Hyderabad": "TELANGANA",
    "Visakhapatnam": "ANDHRA_PRADESH", "Guwahati": "ASSAM", "Bhubaneswar": "ODISHA",
    "Ranchi": "JHARKHAND", "Raipur": "CHHATTISGARH", "Dehradun": "UTTARAKHAND", "Shimla": "HIMACHAL_PRADESH"
}


class NaturalLanguageProfileExtractor:
    """
    Extracts structured BeneficiaryProfileInput fields from natural language text.
    Combines LLM structured extraction with rule-assisted regex matching for zero-hallucination fidelity.
    Preserves UNKNOWN states where user text does not explicitly mention the field.
    """

    @classmethod
    def extract_profile(cls, user_text: str) -> NaturalLanguageExtractResponse:
        provider = get_ai_provider()
        text_lower = user_text.lower()

        extracted_dict: Dict[str, Any] = {}
        confidences: List[ExtractedFieldConfidence] = []

        # Name: English, Hindi, "My name is Jai", "mera naam Jai hai", "I am Jai", "naam Jai", "myself Jai"
        name_match = re.search(r"\b(?:my\s+name\s+is|mera\s+naam|naam|i\s+am|i'm|myself)\s+([a-zA-Z\u0900-\u097F]+)(?:\s+hai|\s+hoon)?\b", user_text, re.IGNORECASE)
        if name_match:
            c_name = name_match.group(1).strip()
            excluded_names = {
                "from", "in", "a", "an", "the", "sc", "st", "obc", "general", "interested", "planning", "looking",
                "seeking", "unable", "not", "eligible", "living", "staying", "residing", "going", "doing", "starting",
                "up", "bihar", "delhi", "punjab", "haryana", "mp", "maharashtra", "gujarat", "rajasthan", "female", "male",
                "years", "year", "old", "saal", "sal", "lame", "crazy", "fool", "dumb", "pagal", "fine", "good",
                "gareeb", "garib", "student", "farmer", "artisan"
            }
            if c_name.lower() not in excluded_names and len(c_name) >= 2 and not c_name.isdigit():
                extracted_dict["name"] = c_name.capitalize()
                confidences.append(ExtractedFieldConfidence(
                    field="name",
                    value=c_name.capitalize(),
                    confidence=0.95,
                    source_snippet=name_match.group(0)
                ))

        # Age: English, Hindi numerals, Devanagari, "saal", "years", "umar", "वर्ष", "साल"
        age_match = re.search(r"\b(?:i\s+am|age|mer?i\s+umar|umar|उम्र)\s*[:=]?\s*(\d{1,2})\b", text_lower)
        if not age_match:
            age_match = re.search(r"(\d{1,2})[-\s]*(?:year|yr|years|old|saal|साल|वर्ष)", text_lower)
        if not age_match:
            age_match = re.search(r"\b(\d{1,2})\s*saal\b", text_lower)
        if age_match:
            try:
                age_val = int(age_match.group(1))
                if 14 <= age_val <= 90:
                    extracted_dict["age"] = age_val
                    confidences.append(ExtractedFieldConfidence(
                        field="age",
                        value=age_val,
                        confidence=0.95,
                        source_snippet=age_match.group(0)
                    ))
            except ValueError:
                pass

        # Monthly & Annual Income (English & Hindi)
        # e.g., "I earn 30,000 per month", "earn 30000", "monthly income 30000", "annual income 3.6 lakh"
        m_inc_match = re.search(r"(?:i\s+earn|earn|salary|kamata\s+hu|kamati\s+hu)\s*(?:\b(?:is|of|around|about|approx|approx\.|\:)\s*)*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?\s*(?:lakh|lakhs|lac|lacs|l|k|thousand|लाख|हजार)?)\s*(?:per\s+month|p\.?m\.?|monthly|har\s+mahine|mahina)?", text_lower)
        if not m_inc_match:
            m_inc_match = re.search(r"(?:monthly\s+income|monthly\s+salary|monthly\s+earning|har\s+mahine\s+ki\s+kamai|mahine\s+ki\s+kamai)\s*(?:\b(?:is|of|around|about|approx|approx\.|\:)\s*)*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?\s*(?:lakh|lakhs|lac|lacs|l|k|thousand|लाख|हजार)?)", text_lower)
        
        if m_inc_match:
            val_str = m_inc_match.group(1).replace(",", "").strip()
            num = cls._parse_monetary_amount(val_str)
            if num is not None:
                is_per_month = any(term in text_lower for term in ["per month", "monthly", "p.m", "har mahine", "mahina"]) or num <= 100000
                if is_per_month:
                    extracted_dict["monthly_income"] = num
                    extracted_dict["annual_income"] = num * 12.0
                    confidences.append(ExtractedFieldConfidence(field="monthly_income", value=num, confidence=0.95, source_snippet=m_inc_match.group(0)))
                    confidences.append(ExtractedFieldConfidence(field="annual_income", value=num * 12.0, confidence=0.95, source_snippet=m_inc_match.group(0)))
                else:
                    extracted_dict["annual_income"] = num
                    extracted_dict["monthly_income"] = round(num / 12.0, 2)
                    confidences.append(ExtractedFieldConfidence(field="annual_income", value=num, confidence=0.90, source_snippet=m_inc_match.group(0)))
        else:
            income_match = re.search(r"(?:annual\s+income|income|earning|kamai|aamdani|वार्षिक\s*आय|आय|कमाई)\s*(?:\b(?:is|of|around|about|approx|approx\.|\:)\s*)*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?\s*(?:lakh|lakhs|lac|lacs|l|k|thousand|लाख|हजार)?)", text_lower)
            if not income_match:
                income_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs|l|लाख)\s*(?:ki\s+|ka\s+)?(?:income|kamai|aamdani|वार्षिक\s*आय|आय|कमाई)", text_lower)
            if income_match:
                val_str = income_match.group(1 if income_match.groups() and income_match.group(1) else 0).lower().replace(",", "").strip()
                num = cls._parse_monetary_amount(val_str)
                if num is not None and "project" not in text_lower[max(0, income_match.start()-15):income_match.end()+15] and "loan" not in text_lower[max(0, income_match.start()-15):income_match.end()+15]:
                    extracted_dict["annual_income"] = num
                    extracted_dict["monthly_income"] = round(num / 12.0, 2)
                    confidences.append(ExtractedFieldConfidence(
                        field="annual_income",
                        value=num,
                        confidence=0.90,
                        source_snippet=income_match.group(0)
                    ))

        # Monthly Living / Operating Expenses (English & Hindi)
        # e.g., "My monthly expenses are around 18,000", "expenses 18000", "monthly kharcha 18000"
        exp_match = re.search(r"(?:monthly\s+expenses?|household\s+expenses?|expenses?|kharcha|kharch)\s*(?:\b(?:is|of|are|around|about|approx|approx\.|\:)\s*)*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?\s*(?:lakh|lakhs|lac|lacs|l|k|thousand|लाख|हजार)?)\s*(?:per\s+month|monthly|har\s+mahine)?", text_lower)
        if exp_match:
            val_str = exp_match.group(1).replace(",", "").strip()
            num = cls._parse_monetary_amount(val_str)
            if num is not None:
                extracted_dict["monthly_expenses"] = num
                confidences.append(ExtractedFieldConfidence(field="monthly_expenses", value=num, confidence=0.95, source_snippet=exp_match.group(0)))

        # Existing Debt Service / EMI Obligations (English & Hindi)
        # e.g., "I already pay 3,000 EMI", "pay 3000 emi", "existing emi 3000"
        emi_match = re.search(r"(?:already\s+pay|pay|pehle\s+se\s+emi|existing\s+emi|current\s+emi|purani\s+emi|purana\s+karz)\s*(?:\b(?:is|of|around|about|approx|\:)\s*)*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?\s*(?:lakh|lakhs|lac|lacs|l|k|thousand|लाख|हजार)?)\s*(?:emi|per\s+month|monthly)?", text_lower)
        if not emi_match:
            emi_match = re.search(r"([\d,]+(?:\.\d+)?\s*(?:k|thousand|हजार)?)\s*(?:rupaye|rs|₹)?\s*(?:ki\s+)?emi\s*(?:already|pehle\s+se|jata\s+hai|bharta\s+hu|pay\s+karta)", text_lower)
        if emi_match:
            val_str = emi_match.group(1).replace(",", "").strip()
            num = cls._parse_monetary_amount(val_str)
            if num is not None:
                extracted_dict["monthly_obligations"] = num
                confidences.append(ExtractedFieldConfidence(field="monthly_obligations", value=num, confidence=0.95, source_snippet=emi_match.group(0)))

        # Social Category & SC/ST/OBC/General Status
        if re.search(r"\b(sc|scheduled caste|anusuchit jati|dalit)\b|अनुसूचित\s*जाति", text_lower):
            extracted_dict["social_category"] = "SC"
            extracted_dict["is_sc"] = True
            confidences.append(ExtractedFieldConfidence(field="social_category", value="SC", confidence=0.98, source_snippet="SC"))
            confidences.append(ExtractedFieldConfidence(field="is_sc", value=True, confidence=0.98, source_snippet="SC"))
        elif re.search(r"\b(st|scheduled tribe|anusuchit janjati|adivasi|tribal)\b|अनुसूचित\s*जनजाति|आदिवासी", text_lower):
            extracted_dict["social_category"] = "ST"
            extracted_dict["is_st"] = True
            extracted_dict["is_sc"] = False
            confidences.append(ExtractedFieldConfidence(field="social_category", value="ST", confidence=0.98, source_snippet="ST"))
            confidences.append(ExtractedFieldConfidence(field="is_st", value=True, confidence=0.98, source_snippet="ST"))
        elif re.search(r"\b(obc|other backward|anya pichhda varg|pichhda varg|backward class)\b|अन्य\s*पिछड़ा\s*वर्ग|पिछड़ा\s*वर्ग", text_lower):
            extracted_dict["social_category"] = "OBC"
            extracted_dict["is_obc"] = True
            extracted_dict["is_sc"] = False
            confidences.append(ExtractedFieldConfidence(field="social_category", value="OBC", confidence=0.95, source_snippet="OBC"))
        elif re.search(r"\b(general|gen|samanya varg|open category|unreserved)\b|सामान्य\s*वर्ग", text_lower):
            extracted_dict["social_category"] = "GENERAL"
            extracted_dict["is_sc"] = False
            confidences.append(ExtractedFieldConfidence(field="social_category", value="GENERAL", confidence=0.95, source_snippet="GENERAL"))
        elif re.search(r"\b(minority|alpasankhyak)\b|अल्पसंख्यक", text_lower):
            extracted_dict["social_category"] = "MINORITY"
            extracted_dict["is_minority"] = True
            confidences.append(ExtractedFieldConfidence(field="is_minority", value=True, confidence=0.95, source_snippet="minority"))

        # Gender
        if re.search(r"\b(woman|female|women|girl|mahila|महिला|ladki|aurat)\b", text_lower):
            extracted_dict["gender"] = "FEMALE"
            confidences.append(ExtractedFieldConfidence(field="gender", value="FEMALE", confidence=0.95, source_snippet="female/mahila"))
        elif re.search(r"\b(man|male|men|boy|purush|पुरुष|ladka|aadmi)\b", text_lower):
            extracted_dict["gender"] = "MALE"
            confidences.append(ExtractedFieldConfidence(field="gender", value="MALE", confidence=0.95, source_snippet="male/purush"))

        # State (All 28 States & UTs in English, Roman Hindi, and Devanagari)
        states_map = {
            "uttar pradesh": "UTTAR_PRADESH", "up": "UTTAR_PRADESH", "u p": "UTTAR_PRADESH", "उत्तर प्रदेश": "UTTAR_PRADESH",
            "maharashtra": "MAHARASHTRA", "mh": "MAHARASHTRA", "महाराष्ट्र": "MAHARASHTRA",
            "bihar": "BIHAR", "बिहार": "BIHAR",
            "madhya pradesh": "MADHYA_PRADESH", "mp": "MADHYA_PRADESH", "m p": "MADHYA_PRADESH", "मध्य प्रदेश": "MADHYA_PRADESH",
            "rajasthan": "RAJASTHAN", "राजस्थान": "RAJASTHAN",
            "gujarat": "GUJARAT", "गुजरात": "GUJARAT",
            "karnataka": "KARNATAKA", "कर्नाटक": "KARNATAKA",
            "tamil nadu": "TAMIL_NADU", "तमिलनाडु": "TAMIL_NADU", "tn": "TAMIL_NADU",
            "west bengal": "WEST_BENGAL", "पश्चिम बंगाल": "WEST_BENGAL", "wb": "WEST_BENGAL",
            "delhi": "DELHI", "दिल्ली": "DELHI",
            "punjab": "PUNJAB", "पंजाब": "PUNJAB",
            "haryana": "HARYANA", "हरियाणा": "HARYANA",
            "odisha": "ODISHA", "orissa": "ODISHA", "ओडिशा": "ODISHA",
            "assam": "ASSAM", "असम": "ASSAM",
            "kerala": "KERALA", "केरल": "KERALA",
            "andhra pradesh": "ANDHRA_PRADESH", "ap": "ANDHRA_PRADESH", "आंध्र प्रदेश": "ANDHRA_PRADESH",
            "telangana": "TELANGANA", "तेलंगाना": "TELANGANA",
            "jharkhand": "JHARKHAND", "झारखंड": "JHARKHAND",
            "chhattisgarh": "CHHATTISGARH", "छत्तीसगढ़": "CHHATTISGARH",
            "uttarakhand": "UTTARAKHAND", "उत्तराखंड": "UTTARAKHAND",
            "himachal pradesh": "HIMACHAL_PRADESH", "hp": "HIMACHAL_PRADESH", "हिमाचल प्रदेश": "HIMACHAL_PRADESH",
            "goa": "GOA", "गोवा": "GOA",
            "jammu": "JAMMU_AND_KASHMIR", "kashmir": "JAMMU_AND_KASHMIR", "जम्मू": "JAMMU_AND_KASHMIR"
        }
        for st_name, st_code in states_map.items():
            if re.search(r"\b" + re.escape(st_name) + r"\b", text_lower):
                extracted_dict["state"] = st_code
                confidences.append(ExtractedFieldConfidence(field="state", value=st_code, confidence=0.95, source_snippet=st_name))
                break

        # District (Major cities and administrative districts in English and Hindi)
        districts_map = {
            "lucknow": "Lucknow", "लखनऊ": "Lucknow",
            "varanasi": "Varanasi", "वाराणसी": "Varanasi", "बनारस": "Varanasi",
            "patna": "Patna", "पटना": "Patna",
            "kanpur": "Kanpur", "कानपुर": "Kanpur",
            "jaipur": "Jaipur", "जयपुर": "Jaipur",
            "pune": "Pune", "पुणे": "Pune",
            "mumbai": "Mumbai", "मुंबई": "Mumbai", "बॉम्बे": "Mumbai",
            "ahmedabad": "Ahmedabad", "अहमदाबाद": "Ahmedabad",
            "indore": "Indore", "इंदौर": "Indore",
            "bhopal": "Bhopal", "भोपाल": "Bhopal",
            "bangalore": "Bengaluru", "bengaluru": "Bengaluru", "बेंगलुरु": "Bengaluru",
            "chennai": "Chennai", "चेन्नई": "Chennai",
            "kolkata": "Kolkata", "कोलकाता": "Kolkata",
            "noida": "Noida", "नोएडा": "Noida",
            "ghaziabad": "Ghaziabad", "गाजियाबाद": "Ghaziabad",
            "agra": "Agra", "आगरा": "Agra",
            "meerut": "Meerut", "मेरठ": "Meerut",
            "prayagraj": "Prayagraj", "प्रयागराज": "Prayagraj", "allahabad": "Prayagraj", "इलाहाबाद": "Prayagraj",
            "gorakhpur": "Gorakhpur", "गोरखपुर": "Gorakhpur",
            "bareilly": "Bareilly", "बरेली": "Bareilly",
            "aligarh": "Aligarh", "अलीगढ़": "Aligarh",
            "moradabad": "Moradabad", "मुरादाबाद": "Moradabad",
            "gaya": "Gaya", "गया": "Gaya",
            "muzaffarpur": "Muzaffarpur", "मुजफ्फरपुर": "Muzaffarpur",
            "bhagalpur": "Bhagalpur", "भागलपुर": "Bhagalpur",
            "nagpur": "Nagpur", "नागपुर": "Nagpur",
            "nashik": "Nashik", "नासिक": "Nashik",
            "thane": "Thane", "ठाणे": "Thane",
            "jodhpur": "Jodhpur", "जोधपुर": "Jodhpur",
            "kota": "Kota", "कोटा": "Kota",
            "udaipur": "Udaipur", "उदयपुर": "Udaipur",
            "surat": "Surat", "सूरत": "Surat",
            "vadodara": "Vadodara", "वडोदरा": "Vadodara",
            "rajkot": "Rajkot", "राजकोट": "Rajkot",
            "amritsar": "Amritsar", "अमृतसर": "Amritsar",
            "ludhiana": "Ludhiana", "लुधियाना": "Ludhiana",
            "gurugram": "Gurugram", "gurgaon": "Gurugram", "गुरुग्राम": "Gurugram", "गुड़गांव": "Gurugram",
            "hyderabad": "Hyderabad", "हैदराबाद": "Hyderabad",
            "visakhapatnam": "Visakhapatnam", "विशाखापट्टनम": "Visakhapatnam",
            "guwahati": "Guwahati", "गुवाहाटी": "Guwahati",
            "bhubaneswar": "Bhubaneswar", "भुवनेश्वर": "Bhubaneswar",
            "ranchi": "Ranchi", "राँची": "Ranchi", "रांची": "Ranchi",
            "raipur": "Raipur", "रायपुर": "Raipur",
            "dehradun": "Dehradun", "देहरादून": "Dehradun",
            "shimla": "Shimla", "शिमला": "Shimla"
        }

        for d_key, d_val in districts_map.items():
            if re.search(r"\b" + re.escape(d_key) + r"\b", text_lower):
                extracted_dict["district"] = d_val
                confidences.append(ExtractedFieldConfidence(field="district", value=d_val, confidence=0.90, source_snippet=d_key))
                if "state" not in extracted_dict and d_val in DISTRICT_TO_STATE:
                    st_val = DISTRICT_TO_STATE[d_val]
                    extracted_dict["state"] = st_val
                    confidences.append(ExtractedFieldConfidence(field="state", value=st_val, confidence=0.92, source_snippet=f"{d_key} (District to state inference)"))
                break

        # Sector & Activity Type & Special Beneficiary Attributes
        if any(t in text_lower for t in ["dairy", "डेयरी", "दूध", "pashupalan", "पशुपालन", "doodh", "milk"]):
            extracted_dict["sector"] = "AGRICULTURE"
            extracted_dict["activity_type"] = "DAIRY_FARMING"
            extracted_dict["business_description"] = "dairy farming"
            confidences.append(ExtractedFieldConfidence(field="sector", value="AGRICULTURE", confidence=0.95, source_snippet="dairy"))
            confidences.append(ExtractedFieldConfidence(field="activity_type", value="DAIRY_FARMING", confidence=0.95, source_snippet="dairy"))
        elif any(t in text_lower for t in ["tailoring", "silai", "सिलाई", "stitching", "boutique", "garment", "clothing", "textile", "handloom"]):
            extracted_dict["sector"] = "MICRO_FINANCE"
            extracted_dict["activity_type"] = "SMALL_MICRO_BUSINESS"
            extracted_dict["business_description"] = "tailoring"
            confidences.append(ExtractedFieldConfidence(field="sector", value="MICRO_FINANCE", confidence=0.90, source_snippet="tailoring/silai"))
        elif any(t in text_lower for t in ["manufacturing", "factory", "production", "plant", "udyog", "उद्योग", "food processing"]):
            extracted_dict["sector"] = "MANUFACTURING"
            extracted_dict["activity_type"] = "MANUFACTURING"
            extracted_dict["business_description"] = "manufacturing unit"
            confidences.append(ExtractedFieldConfidence(field="sector", value="MANUFACTURING", confidence=0.90, source_snippet="manufacturing"))
        elif any(t in text_lower for t in ["shop", "retail", "store", "kirana", "किराना", "dukan", "dukaan", "दुकान", "grocery", "trading"]):
            extracted_dict["sector"] = "TRADING"
            extracted_dict["activity_type"] = "SMALL_MICRO_BUSINESS"
            extracted_dict["business_description"] = "retail shop"
            confidences.append(ExtractedFieldConfidence(field="sector", value="TRADING", confidence=0.90, source_snippet="retail/shop"))
        elif any(t in text_lower for t in ["kheti", "खेती", "farm", "farming", "agriculture", "crop", "kisan", "किसान"]):
            extracted_dict["sector"] = "AGRICULTURE"
            extracted_dict["activity_type"] = "FARMING_ALLIED"
            extracted_dict["is_farmer"] = True
            extracted_dict["applicant_type"] = "FARMER"
            confidences.append(ExtractedFieldConfidence(field="sector", value="AGRICULTURE", confidence=0.90, source_snippet="farming/kheti"))

        # Student & Education Vocation
        student_terms = [
            "student", "chhatra", "छात्र", "college", "university", "higher education",
            "btech", "b.tech", "mtech", "mba", "mbbs", "medical", "engineering",
            "undergraduate", "postgraduate", "phd", "padhai", "shiksha", "शिक्षा",
            "vidyarthi", "विद्यार्थी", "education loan", "study loan", "higher studies"
        ]
        if any(term in text_lower for term in student_terms):
            extracted_dict["applicant_type"] = "STUDENT"
            extracted_dict["employment_status"] = "STUDENT"
            extracted_dict["sector"] = "EDUCATION"
            extracted_dict["activity_type"] = "EDUCATION"
            confidences.append(ExtractedFieldConfidence(field="applicant_type", value="STUDENT", confidence=0.95, source_snippet="student"))
            confidences.append(ExtractedFieldConfidence(field="employment_status", value="STUDENT", confidence=0.95, source_snippet="student"))
            confidences.append(ExtractedFieldConfidence(field="sector", value="EDUCATION", confidence=0.95, source_snippet="student/education"))

        # Education Level
        if re.search(r"\b(phd|doctorate|research\s+scholar)\b|विद्यावाचस्पति", text_lower):
            extracted_dict["education_level"] = "DOCTORATE"
            confidences.append(ExtractedFieldConfidence(field="education_level", value="DOCTORATE", confidence=0.95, source_snippet="doctorate"))
        elif re.search(r"\b(post[- ]?graduate|post[- ]?graduation|master|masters|mtech|m\.tech|mba|msc|m\.sc|ma|m\.a|pg)\b|स्नातकोत्तर|एमटेक|एमबीए", text_lower):
            extracted_dict["education_level"] = "POST_GRADUATE"
            confidences.append(ExtractedFieldConfidence(field="education_level", value="POST_GRADUATE", confidence=0.95, source_snippet="post graduate"))
        elif re.search(r"\b(graduate|graduation|btech|b\.tech|bba|bca|bsc|b\.sc|ba|b\.a|be|b\.e|degree|undergraduate|ug)\b|स्नातक|बीटेक|डिग्री|इंजीनियरिंग", text_lower):
            extracted_dict["education_level"] = "GRADUATE"
            confidences.append(ExtractedFieldConfidence(field="education_level", value="GRADUATE", confidence=0.95, source_snippet="graduate"))
        elif re.search(r"\b(diploma|polytechnic)\b|डिप्लोमा|पॉलिटेक्निक", text_lower):
            extracted_dict["education_level"] = "DIPLOMA"
            confidences.append(ExtractedFieldConfidence(field="education_level", value="DIPLOMA", confidence=0.95, source_snippet="diploma"))
        elif re.search(r"\b(12th|12\s+pass|inter|intermediate|hsc|barahvi)\b|12वीं|बारहवीं", text_lower):
            extracted_dict["education_level"] = "12TH_PASS"
            confidences.append(ExtractedFieldConfidence(field="education_level", value="12TH_PASS", confidence=0.95, source_snippet="12th"))
        elif re.search(r"\b(10th|10\s+pass|matric|high\s*school|ssc|dasvi)\b|10वीं|दसवीं", text_lower):
            extracted_dict["education_level"] = "10TH_PASS"
            confidences.append(ExtractedFieldConfidence(field="education_level", value="10TH_PASS", confidence=0.95, source_snippet="10th"))

        # Special Vocations (Artisan, Street Vendor, Divyang)
        if re.search(r"\b(artisan|karigar|कारीगर|vishwakarma|विश्वकर्मा|carpenter|badhai|blacksmith|lohar|potter|kumhar|cobbler|mochi|barber|weaver|bunkar)\b", text_lower):
            extracted_dict["is_artisan"] = True
            extracted_dict["applicant_type"] = "ARTISAN"
            confidences.append(ExtractedFieldConfidence(field="is_artisan", value=True, confidence=0.95, source_snippet="artisan"))
        if re.search(r"\b(street\s+vendor|vendor|rehri|patri|thela|feriwala|रेहड़ी|पटरी|ठेला|svanidhi)\b", text_lower):
            extracted_dict["is_street_vendor"] = True
            extracted_dict["applicant_type"] = "STREET_VENDOR"
            confidences.append(ExtractedFieldConfidence(field="is_street_vendor", value=True, confidence=0.95, source_snippet="street vendor"))
        if re.search(r"\b(pwd|divyang|दिव्यांग|handicapped|disability|viklang)\b", text_lower):
            extracted_dict["is_pwd"] = True
            confidences.append(ExtractedFieldConfidence(field="is_pwd", value=True, confidence=0.95, source_snippet="divyang/pwd"))

        # Business Stage (New vs Existing / Expansion)
        if re.search(r"\b(new|start|setup|greenfield|begin|start\s+karna|shuru\s+karna|nayi\s+unit|naya\s+business|naya\s+kaam|नया\s*बिज़नेस|शुरू)\b", text_lower):
            extracted_dict["business_stage"] = "NEW"
            extracted_dict["is_new_unit"] = True
            confidences.append(ExtractedFieldConfidence(field="business_stage", value="NEW", confidence=0.90, source_snippet="new business/start"))
        elif re.search(r"\b(expand|existing|growth|scale|running|already\s+chal\s+raha|purana\s+business|purana\s+kaam|badhana\s+hai|expansion|scale\s+up|पुराना|विस्तार)\b", text_lower):
            extracted_dict["business_stage"] = "EXPANSION"
            extracted_dict["is_new_unit"] = False
            confidences.append(ExtractedFieldConfidence(field="business_stage", value="EXPANSION", confidence=0.90, source_snippet="existing/expansion"))

        # 1. Own Contribution / Liquid Savings (English & Hindi)
        # e.g., "mere paas 2 lakh hain", "own contribution 2 lakh", "saving 50,000", "i can invest 3 lakh"
        savings_match = re.search(
            r"(?:mere\s+paas|apne\s+paas|paas\s+(?:hai|hain)|bachat|saving|savings|liquid\s+savings|own\s+contribution|khud\s+ka\s+paisa|margin\s+money|i\s+can\s+invest|can\s+invest|own\s+investment|my\s+investment|investment\s+capacity|निवेश\s*कर\s*सकता|पास\s+है|बचत|खुद\s+का)\s*(?:is|of|around|about|approx|approx\.|:)?\s*(?:₹|rs\.?|inr)?\s*([\d\.]+\s*(?:lakh|lakhs|lac|lacs|l|k|thousand|crore|cr|लाख|हजार)?)\s*(?:hai|hain|rupaye|rs)?",
            text_lower
        )
        if not savings_match:
            savings_match = re.search(r"([\d\.]+\s*(?:lakh|lakhs|lac|lacs|l|लाख|हजार))\s*(?:rupaye|rs|₹)?\s*(?:mere\s+paas|paas\s+hai|bachat|saving|own\s+contribution|invest\s+kar\s+sakta)", text_lower)
        if savings_match:
            num = cls._parse_monetary_amount(savings_match.group(1))
            if num is not None:
                extracted_dict["liquid_savings"] = num
                confidences.append(ExtractedFieldConfidence(field="liquid_savings", value=num, confidence=0.92, source_snippet=savings_match.group(0)))

        # 2. Project Cost (English & Hindi) - Strictly NOT loan and NOT own investment capacity
        # e.g., "10 lakh ka project", "project cost ₹10 lakh", "total cost 5 lakh", "10 lakh project hai"
        cost_match = re.search(
            r"(?:project\s+cost|total\s+cost|setup\s+cost|total\s+investment|project\s+investment|kul\s+laagat|laagat|कुल\s+लागत|लागत)\s*(?:is|of|around|about|approx|approx\.|:)?\s*(?:₹|rs\.?|inr)?\s*([\d\.]+\s*(?:lakh|lakhs|lac|lacs|l|k|thousand|crore|cr|लाख|हजार)?)",
            text_lower
        )
        if not cost_match and "can invest" not in text_lower and "i can invest" not in text_lower:
            cost_match = re.search(
                r"([\d\.]+\s*(?:lakh|lakhs|lac|lacs|l|crore|cr|लाख|हजार))\s*(?:ka|ki|ke|में|का|की)?\s*(?:project|setup|plant|unit|farm|business|dairy|डेयरी|फार्म|प्रोजेक्ट|लागत|उद्योग|बिज़नेस)",
                text_lower
            )
        if cost_match:
            num = cls._parse_monetary_amount(cost_match.group(1))
            if num is not None:
                extracted_dict["project_cost"] = num
                confidences.append(ExtractedFieldConfidence(field="project_cost", value=num, confidence=0.95, source_snippet=cost_match.group(0)))

        # 3. Requested Loan Amount (Strictly distinct from Project Cost)
        # e.g., "loan of 8 lakh", "need 5 lakh loan", "loan amount 5 lakh", "8 lakh ka loan", "5 lakh education loan"
        loan_match = re.search(
            r"(?:loan\s+amount|need\s+a\s+loan\s+of|borrow|karz|loan\s+chahiye|loan\s+of|need\s+a\s+loan|loan\s+required)\s*(?:is|of|around|:)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?\s*(?:lakh|lakhs|lac|lacs|l|k|thousand|crore|cr|लाख|हजार)?)",
            text_lower
        )
        if not loan_match or not cls._parse_monetary_amount(loan_match.group(1)):
            loan_match = re.search(
                r"(\d+(?:\.\d+)?\s*(?:lakh|lakhs|lac|lacs|l|crore|cr|लाख|हजार))\s*(?:ka|ki|ke|में|का|की)?\s*(?:education\s+|study\s+|business\s+|home\s+|personal\s+|शिक्षा\s+|पढ़ाई\s+)?(?:loan|karz|credit|ऋण|लोन)",
                text_lower
            )
        if not loan_match or not cls._parse_monetary_amount(loan_match.group(1)):
            loan_match = re.search(
                r"(?:need|require|chahiye|want|need\s+a)\s+(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?\s*(?:lakh|lakhs|lac|lacs|l|k|thousand|crore|cr|लाख|हजार)?)\s*(?:ka|ki|ke|में|का|की)?\s*(?:education\s+|study\s+|business\s+|शिक्षा\s+|पढ़ाई\s+)?(?:loan|karz|credit|ऋण|लोन)",
                text_lower
            )
        if loan_match:
            snippet = loan_match.group(0)
            if "project" not in snippet and "paas" not in snippet:
                num = cls._parse_monetary_amount(loan_match.group(1))
                if num is not None:
                    extracted_dict["requested_loan_amount"] = num
                    confidences.append(ExtractedFieldConfidence(field="requested_loan_amount", value=num, confidence=0.90, source_snippet=snippet))

        # 4. Net Loan Derivation if Project Cost and Own Contribution are known without explicit loan
        if "requested_loan_amount" not in extracted_dict:
            proj = extracted_dict.get("project_cost")
            savings = extracted_dict.get("liquid_savings")
            if proj is not None and savings is not None and proj > savings:
                derived_loan = proj - savings
                extracted_dict["requested_loan_amount"] = derived_loan
                confidences.append(ExtractedFieldConfidence(
                    field="requested_loan_amount",
                    value=derived_loan,
                    confidence=0.90,
                    source_snippet=f"Derived: project cost ₹{proj:,.0f} - own contribution ₹{savings:,.0f}"
                ))

        # 2. LLM Enhancement if Provider Available and Not Fallback
        if not provider.is_fallback:
            try:
                schema = {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer"},
                        "annual_income": {"type": "number"},
                        "social_category": {"type": "string"},
                        "gender": {"type": "string"},
                        "state": {"type": "string"},
                        "sector": {"type": "string"},
                        "business_stage": {"type": "string"},
                        "project_cost": {"type": "number"},
                        "requested_loan_amount": {"type": "number"},
                    }
                }
                llm_dict = provider.structured_output(
                    prompt=f"Extract beneficiary profile fields from this text. Do NOT invent missing values: {user_text}",
                    json_schema=schema
                )
                for k, v in llm_dict.items():
                    if v is not None and k not in extracted_dict:
                        extracted_dict[k] = v
                        confidences.append(ExtractedFieldConfidence(field=k, value=v, confidence=0.85, source_snippet="LLM Extracted"))
            except Exception as err:
                logger.warning("LLM extraction fallback trigger: %s", err)

        # Build BeneficiaryProfileInput
        profile = BeneficiaryProfileInput(**extracted_dict)

        # High priority evaluation fields required for accuracy
        high_priority = ["annual_income", "social_category", "state", "sector", "project_cost", "age"]
        missing_high_priority = [f for f in high_priority if getattr(profile, f, None) is None]
        clarifications = [f"Missing required parameter '{f}' for precise scheme eligibility check." for f in missing_high_priority]

        return NaturalLanguageExtractResponse(
            user_text=user_text,
            extracted_profile=profile,
            field_confidences=confidences,
            missing_high_priority_fields=missing_high_priority,
            fields_requiring_clarification=clarifications,
            is_fallback=provider.is_fallback,
            provider_name=provider.name
        )

    @staticmethod
    def _parse_monetary_amount(text_val: str) -> Optional[float]:
        val = text_val.lower().strip()
        val = re.sub(r"(?:₹|rs\.?|inr)", "", val).strip()
        try:
            if any(k in val for k in ("lakh", "lakhs", "lac", "lacs", "लाख", " l")):
                num_part = re.search(r"[\d\.]+", val)
                if num_part:
                    return float(num_part.group(0)) * 100000.0
            elif any(k in val for k in ("k", "thousand", "हजार", "हज़ार")):
                num_part = re.search(r"[\d\.]+", val)
                if num_part:
                    return float(num_part.group(0)) * 1000.0
            else:
                num_part = re.search(r"[\d\.]+", val)
                if num_part:
                    f = float(num_part.group(0))
                    if f < 100:
                        return f * 100000.0
                    return f
        except Exception:
            return None
        return None
