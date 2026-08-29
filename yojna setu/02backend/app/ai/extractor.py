import re
import logging
from typing import Dict, Any, Tuple, List, Optional

from app.schemas.recommendation import BeneficiaryProfileInput
from app.schemas.ai import (
    NaturalLanguageExtractResponse,
    ExtractedFieldConfidence,
)
from app.ai.provider import get_ai_provider

logger = logging.getLogger("yojnasetu.ai.extractor")


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

        # 1. Regex & Keyword Rule Extraction (Deterministic & Provable)
        # Age
        age_match = re.search(r"(\d{2})\s*(?:year|yr|years|old)", text_lower)
        if not age_match:
            age_match = re.search(r"age\s*(?:is|:)?\s*(\d{2})", text_lower)
        if age_match:
            try:
                age_val = int(age_match.group(1))
                if 18 <= age_val <= 75:
                    extracted_dict["age"] = age_val
                    confidences.append(ExtractedFieldConfidence(
                        field="age",
                        value=age_val,
                        confidence=0.95,
                        source_snippet=age_match.group(0)
                    ))
            except ValueError:
                pass

        # Annual Income
        income_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|l)", text_lower)
        if not income_match:
            income_match = re.search(r"(?:income|earning|annual income)\s*(?:is|of|around|:)?\s*(?:₹|rs\.?|inr)?\s*([\d\.]+)", text_lower)

        if income_match:
            val_str = income_match.group(0).lower().strip()
            num = cls._parse_monetary_amount(val_str)
            if num is not None:
                extracted_dict["annual_income"] = num
                confidences.append(ExtractedFieldConfidence(
                    field="annual_income",
                    value=num,
                    confidence=0.90,
                    source_snippet=income_match.group(0)
                ))

        # Social Category & SC Status
        if re.search(r"\b(sc|scheduled caste)\b", text_lower):
            extracted_dict["social_category"] = "SC"
            extracted_dict["is_sc"] = True
            confidences.append(ExtractedFieldConfidence(field="social_category", value="SC", confidence=0.98, source_snippet="SC"))
            confidences.append(ExtractedFieldConfidence(field="is_sc", value=True, confidence=0.98, source_snippet="SC"))
        elif re.search(r"\b(st|scheduled tribe)\b", text_lower):
            extracted_dict["social_category"] = "ST"
            extracted_dict["is_sc"] = False
            confidences.append(ExtractedFieldConfidence(field="social_category", value="ST", confidence=0.98, source_snippet="ST"))
            confidences.append(ExtractedFieldConfidence(field="is_sc", value=False, confidence=0.98, source_snippet="ST"))
        elif re.search(r"\b(obc|other backward)\b", text_lower):
            extracted_dict["social_category"] = "OBC"
            extracted_dict["is_sc"] = False
            confidences.append(ExtractedFieldConfidence(field="social_category", value="OBC", confidence=0.95, source_snippet="OBC"))

        # Gender
        if re.search(r"\b(woman|female|women|girl)\b", text_lower):
            extracted_dict["gender"] = "FEMALE"
            confidences.append(ExtractedFieldConfidence(field="gender", value="FEMALE", confidence=0.95, source_snippet="woman/female"))
        elif re.search(r"\b(man|male|men|boy)\b", text_lower):
            extracted_dict["gender"] = "MALE"
            confidences.append(ExtractedFieldConfidence(field="gender", value="MALE", confidence=0.95, source_snippet="man/male"))

        # State
        states_map = {
            "uttar pradesh": "UTTAR_PRADESH", "up": "UTTAR_PRADESH",
            "maharashtra": "MAHARASHTRA", "mh": "MAHARASHTRA",
            "bihar": "BIHAR", "madhya pradesh": "MADHYA_PRADESH", "mp": "MADHYA_PRADESH",
            "rajasthan": "RAJASTHAN", "gujarat": "GUJARAT", "karnataka": "KARNATAKA",
            "tamil nadu": "TAMIL_NADU", "west bengal": "WEST_BENGAL", "delhi": "DELHI"
        }
        for st_name, st_code in states_map.items():
            if re.search(r"\b" + re.escape(st_name) + r"\b", text_lower):
                extracted_dict["state"] = st_code
                confidences.append(ExtractedFieldConfidence(field="state", value=st_code, confidence=0.95, source_snippet=st_name))
                break

        # Sector
        if re.search(r"\b(tailoring|textile|boutique|garment|clothing)\b", text_lower):
            extracted_dict["sector"] = "MICRO_FINANCE"
            extracted_dict["activity_type"] = "SMALL_MICRO_BUSINESS"
            confidences.append(ExtractedFieldConfidence(field="sector", value="MICRO_FINANCE", confidence=0.85, source_snippet="tailoring"))
        elif re.search(r"\b(dairy|farm|farming|agriculture|crop|cattle)\b", text_lower):
            extracted_dict["sector"] = "AGRICULTURE"
            confidences.append(ExtractedFieldConfidence(field="sector", value="AGRICULTURE", confidence=0.90, source_snippet="dairy/farming"))
        elif re.search(r"\b(factory|manufacturing|production|unit|plant)\b", text_lower):
            extracted_dict["sector"] = "MANUFACTURING"
            confidences.append(ExtractedFieldConfidence(field="sector", value="MANUFACTURING", confidence=0.90, source_snippet="manufacturing"))
        elif re.search(r"\b(shop|retail|trading|store|vendor)\b", text_lower):
            extracted_dict["sector"] = "TRADING"
            confidences.append(ExtractedFieldConfidence(field="sector", value="TRADING", confidence=0.85, source_snippet="trading/shop"))

        # Business Stage
        if re.search(r"\b(new|start|setup|greenfield|begin)\b", text_lower):
            extracted_dict["business_stage"] = "NEW"
            extracted_dict["is_new_unit"] = True
            confidences.append(ExtractedFieldConfidence(field="business_stage", value="NEW", confidence=0.90, source_snippet="new business"))
        elif re.search(r"\b(expand|existing|growth|scale|running)\b", text_lower):
            extracted_dict["business_stage"] = "EXPANSION"
            extracted_dict["is_new_unit"] = False
            confidences.append(ExtractedFieldConfidence(field="business_stage", value="EXPANSION", confidence=0.90, source_snippet="existing/expansion"))

        # Project Cost & Loan Amount
        cost_match = re.search(r"(?:project cost|total cost|cost|setup cost)\s*(?:is|of|around|:)?\s*(?:₹|rs\.?|inr)?\s*([\d\.]+\s*(?:lakh|lakhs|l|k|thousand)?)", text_lower)
        if cost_match:
            num = cls._parse_monetary_amount(cost_match.group(1))
            if num is not None:
                extracted_dict["project_cost"] = num
                confidences.append(ExtractedFieldConfidence(field="project_cost", value=num, confidence=0.90, source_snippet=cost_match.group(0)))

        loan_match = re.search(r"(?:loan|loan amount|need a loan|borrow)\s*(?:is|of|around|:)?\s*(?:₹|rs\.?|inr)?\s*([\d\.]+\s*(?:lakh|lakhs|l|k|thousand)?)", text_lower)
        if loan_match:
            num = cls._parse_monetary_amount(loan_match.group(1))
            if num is not None:
                extracted_dict["requested_loan_amount"] = num
                confidences.append(ExtractedFieldConfidence(field="requested_loan_amount", value=num, confidence=0.90, source_snippet=loan_match.group(0)))

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
            if "lakh" in val or "l" in val:
                num_part = re.search(r"[\d\.]+", val)
                if num_part:
                    return float(num_part.group(0)) * 100000.0
            elif "k" in val or "thousand" in val:
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
