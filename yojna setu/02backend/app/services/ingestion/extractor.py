import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.services.ingestion.financial_extractor import FinancialFactExtractor

logger = logging.getLogger("yojnasetu.ingestion.extractor")


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, content: str, source_url: str) -> Dict[str, Any]:
        """Extracts candidate scheme parameters from raw content."""
        pass


class OfficialGovHTMLExtractor(BaseExtractor):
    """
    Structured Extractor for official government welfare scheme portals and guideline pages.
    Extracts core eligibility limits, financial caps, subsidies, and target groups.
    Preserves exact evidence and never invents missing information.
    """

    def extract(self, content: str, source_url: str) -> Dict[str, Any]:
        if not content:
            return {}

        extracted: Dict[str, Any] = {
            "source_url": source_url,
            "evidence": {}
        }

        # 1. Scheme Title / Name
        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.IGNORECASE | re.DOTALL)
        if not title_match:
            title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        if title_match:
            clean_title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
            # Clean common portal suffixes
            clean_title = re.split(r"[-|:–]", clean_title)[0].strip()
            if len(clean_title) >= 4:
                extracted["scheme_name"] = clean_title
                extracted["evidence"]["scheme_name"] = title_match.group(0)[:200]

        # 2. Ministry / Implementing Agency
        ministry_match = re.search(
            r"(?:Ministry|Department)\s+of\s+[\w\s,&]+",
            content,
            re.IGNORECASE
        )
        if ministry_match:
            clean_min = ministry_match.group(0).strip().rstrip(".,")
            extracted["ministry"] = clean_min
            extracted["evidence"]["ministry"] = clean_min

        # 3. Numeric Financial Facts (Disambiguated via FinancialFactExtractor)
        fin_facts = FinancialFactExtractor().extract_financial_facts(content)
        if fin_facts.get("max_loan_amount") is not None:
            extracted["max_loan_amount"] = fin_facts["max_loan_amount"]
            extracted["evidence"]["max_loan_amount"] = fin_facts["provenance"].get("max_loan_amount", {}).get("raw", "")
        if fin_facts.get("max_project_cost") is not None:
            extracted["max_project_cost"] = fin_facts["max_project_cost"]
            extracted["evidence"]["max_project_cost"] = fin_facts["provenance"].get("max_project_cost", {}).get("raw", "")
        if fin_facts.get("subsidy_percentage") is not None:
            extracted["subsidy_percentage"] = fin_facts["subsidy_percentage"]
            extracted["evidence"]["subsidy_percentage"] = fin_facts["provenance"].get("subsidy_percentage", {}).get("raw", "")
        if fin_facts.get("interest_rate") is not None:
            extracted["interest_rate_max"] = fin_facts["interest_rate"]
            extracted["evidence"]["interest_rate_max"] = fin_facts["provenance"].get("interest_rate", {}).get("raw", "")

        # 6. Age Criteria (e.g. "18 years and above", "Age between 18 to 35 years", "Minimum age: 18 years")
        age_match = re.search(
            r"(?:minimum\s+age|age\s+criteria|applicant\s+should\s+be)\s*(?:is|of)?\s*[:=-]?\s*(\d{1,2})\s*(?:years|yrs)?",
            content,
            re.IGNORECASE
        )
        if age_match:
            try:
                extracted["age_min"] = int(age_match.group(1))
                extracted["evidence"]["age_min"] = age_match.group(0)
            except ValueError:
                pass

        age_range_match = re.search(
            r"between\s+(\d{1,2})\s*(?:to|-|and)\s*(\d{1,2})\s*(?:years|yrs)",
            content,
            re.IGNORECASE
        )
        if age_range_match:
            try:
                extracted["age_min"] = int(age_range_match.group(1))
                extracted["age_max"] = int(age_range_match.group(2))
                extracted["evidence"]["age_range"] = age_range_match.group(0)
            except ValueError:
                pass

        # 7. Income Limit (e.g. "annual family income below ₹3,00,000", "income limit: Rs. 1.8 Lakh")
        income_match = re.search(
            r"(?:family\s+income|annual\s+income|income\s+limit)\s*(?:below|up\s+to|not\s+exceeding)?\s*[:=-]?\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(lakhs?)?",
            content,
            re.IGNORECASE
        )
        if income_match:
            inc_str = income_match.group(1).replace(",", "").strip()
            unit_inc = (income_match.group(2) or "").lower().strip()
            try:
                base_inc = float(inc_str)
                if "lakh" in unit_inc:
                    base_inc *= 100000.0
                extracted["income_limit"] = base_inc
                extracted["evidence"]["income_limit"] = income_match.group(0)
            except ValueError:
                pass

        # 8. Target Beneficiary & Groups
        target_groups = []
        c_lower = content.lower()
        if "street vendor" in c_lower or "urban vendor" in c_lower:
            target_groups.append("STREET_VENDOR")
        if "artisan" in c_lower or "craftsperson" in c_lower or "traditional trade" in c_lower:
            target_groups.append("ARTISAN")
        if "women" in c_lower or "mahila" in c_lower:
            target_groups.append("WOMEN")
        if "scheduled caste" in c_lower or " sc " in c_lower:
            target_groups.append("SC")
        if "scheduled tribe" in c_lower or " st " in c_lower:
            target_groups.append("ST")
        if "micro enterprise" in c_lower or "small business" in c_lower or "msme" in c_lower:
            target_groups.append("MICRO_ENTERPRISE")

        if target_groups:
            extracted["target_groups"] = ", ".join(target_groups)
            extracted["evidence"]["target_groups"] = f"Detected target patterns: {target_groups}"

        # 9. Application Portal / URL
        portal_match = re.search(r'https?://(?:www\.)?[\w\-\.]+\.gov\.in[^\s"\'<>]*', content, re.IGNORECASE)
        if portal_match:
            extracted["official_portal"] = portal_match.group(0)
            extracted["application_url"] = portal_match.group(0)
        else:
            extracted["official_portal"] = source_url
            extracted["application_url"] = source_url

        extracted["official_source_url"] = source_url

        # 10. Moratorium (e.g. "moratorium of 12 months", "moratorium up to 18 months")
        mora_match = re.search(r"moratorium\s*(?:of|period|up\s+to)?\s*[:=-]?\s*(\d{1,3})\s*(?:months?|mths?|yrs?|years?)", content, re.IGNORECASE)
        if mora_match:
            try:
                extracted["moratorium_max_months"] = int(mora_match.group(1))
                extracted["evidence"]["moratorium_max_months"] = mora_match.group(0)
            except ValueError:
                pass

        # 11. Tenure / Repayment (e.g. "repayment tenure of 36 months", "repayment period up to 60 months", "tenure: 5 years")
        tenure_match = re.search(r"(?:repayment\s+period|repayment\s+tenure|loan\s+tenure|tenure)\s*(?:of|is|up\s+to)?\s*[:=-]?\s*(\d{1,3})\s*(months?|years?|yrs?)", content, re.IGNORECASE)
        if tenure_match:
            try:
                val = int(tenure_match.group(1))
                unit = tenure_match.group(2).lower()
                if "year" in unit or "yr" in unit:
                    val *= 12
                extracted["repayment_period_max_months"] = val
                extracted["evidence"]["repayment_period_max_months"] = tenure_match.group(0)
            except ValueError:
                pass

        # 12. Scheme Status (e.g. ACTIVE, CLOSED, WITHDRAWN)
        if re.search(r"\b(?:scheme\s+(?:closed|withdrawn|discontinued)|closed\s+for\s+applications)\b", content, re.IGNORECASE):
            extracted["scheme_status"] = "CLOSED"
        elif re.search(r"\b(?:scheme\s+is\s+active|accepting\s+applications|currently\s+open)\b", content, re.IGNORECASE):
            extracted["scheme_status"] = "ACTIVE"

        # 13. Linked Official Guidelines / PDFs
        pdf_matches = re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', content, re.IGNORECASE)
        if pdf_matches:
            from urllib.parse import urljoin
            valid_pdfs = []
            for pm in pdf_matches:
                if pm.startswith("http"):
                    valid_pdfs.append(pm)
                elif pm.startswith("/"):
                    valid_pdfs.append(urljoin(source_url, pm))
            if valid_pdfs:
                extracted["linked_pdfs"] = valid_pdfs[:5]

        return extracted
