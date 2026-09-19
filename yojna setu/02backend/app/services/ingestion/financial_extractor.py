"""
Production-grade Deterministic Financial Fact Extractor for Government Welfare Schemes.

Extracts and normalizes numeric financial facts from official scheme guidelines,
statutory texts, and policy circulars with strict distinction between:
- Maximum / Minimum Project Cost (enterprise capital expenditure cap)
- Maximum / Minimum Loan Amount (credit facility)
- Capital Subsidy Percentage & Absolute Subsidy Amount
- Grant Amount
- Margin Money / Beneficiary Contribution Percentage
- Interest Rate (Min/Max % per annum, including 0% interest-free)
- Interest Subsidy / Subvention Percentage
- Repayment Period (Tenure in months)
- Moratorium Period (Grace period in months)
- Collateral Requirement (YES/NO/CONDITIONAL)
- Guarantee Coverage (CGTMSE / CGFMU / Guarantee % fee)
- Processing Fee

Maintains full audit provenance (raw text, normalized value, confidence).
Strictly does NOT conflate project cost with loan ceiling.
"""
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("yojnasetu.ingestion.financial_extractor")


class FinancialFactExtractor:
    """
    Deterministic rule-based numeric financial extractor with currency normalization,
    unit parsing, and context-aware disambiguation.
    """

    @staticmethod
    def parse_inr_amount(amount_str: str, unit_str: Optional[str] = None) -> Optional[float]:
        """
        Normalizes Indian currency string representations into float INR values.
        Supports:
        - ₹10 lakh / 10 lakhs / Rs. 10 Lakh / 10 lac -> 1,000,000.0
        - ₹1.5 crore / 1.5 crores / Rs 1.5 Cr -> 15,000,000.0
        - INR 1 million / 1 million -> 1,000,000.0
        - ₹50,000 / Rs. 50000 / 50 thousand / 50,000/- -> 50,000.0
        - 50k -> 50,000.0
        """
        if not amount_str:
            return None

        clean_amt = amount_str.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("INR", "").replace("/-", "").strip()
        try:
            val = float(clean_amt)
        except ValueError:
            return None

        unit = (unit_str or "").lower().strip()
        if "crore" in unit or unit in ("cr", "crs"):
            return val * 10000000.0
        elif "lakh" in unit or unit in ("lac", "lacs", "l"):
            return val * 100000.0
        elif "million" in unit:
            return val * 1000000.0
        elif "thousand" in unit or unit == "k":
            return val * 1000.0

        # Direct absolute amount check
        if val > 0:
            return val
        return None

    def extract_financial_facts(self, text: str) -> Dict[str, Any]:
        """
        Extracts structured financial facts from narrative text with strict context validation.
        """
        if not text:
            return {}

        results: Dict[str, Any] = {
            "min_project_cost": None,
            "max_project_cost": None,
            "min_loan_amount": None,
            "max_loan_amount": None,
            "subsidy_percentage": None,
            "subsidy_amount": None,
            "grant_amount": None,
            "margin_money_percentage": None,
            "interest_rate_min": None,
            "interest_rate_max": None,
            "interest_subsidy": None,
            "repayment_period_min_months": None,
            "repayment_period_max_months": None,
            "moratorium_min_months": None,
            "moratorium_max_months": None,
            "collateral_required": None,
            "guarantee_requirement": None,
            "processing_fee": None,
            "provenance": {}
        }

        # ── 1. Project Cost (Must NOT be conflated with Loan Amount) ──
        # e.g., "Project cost up to ₹50 lakh for manufacturing and 20 lakh for service", "project cost of ₹10 lakh to ₹25 lakh"
        proj_range_match = re.search(
            r"(?:project\s+cost|total\s+project\s+investment|cost\s+of\s+project)\s*(?:is|of|from)?\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(crores?|crs?|lakhs?|lacs?|thousand)?\s*(?:to|-)\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(crores?|crs?|lakhs?|lacs?|thousand)",
            text,
            re.IGNORECASE
        )
        if proj_range_match:
            p_min = self.parse_inr_amount(proj_range_match.group(1), proj_range_match.group(2) or proj_range_match.group(4))
            p_max = self.parse_inr_amount(proj_range_match.group(3), proj_range_match.group(4))
            if p_min:
                results["min_project_cost"] = p_min
            if p_max:
                results["max_project_cost"] = p_max
            results["provenance"]["project_cost"] = {"raw": proj_range_match.group(0).strip(), "confidence": "HIGH"}
        else:
            proj_cost_match = re.search(
                r"(?:maximum\s+project\s+cost|project\s+cost\s+(?:up\s+to|ceiling|limit|of|shall\s+not\s+exceed)|cost\s+of\s+project\s+(?:up\s+to|is|exceeds?)|total\s+project\s+cost\s+(?:up\s+to|is|of)?)\s*(?:is|of|:|-)?\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(crores?|crs?|lakhs?|lacs?|thousand)?",
                text,
                re.IGNORECASE
            )
            if proj_cost_match:
                parsed = self.parse_inr_amount(proj_cost_match.group(1), proj_cost_match.group(2))
                if parsed is not None:
                    results["max_project_cost"] = parsed
                    results["provenance"]["max_project_cost"] = {
                        "raw": proj_cost_match.group(0).strip(),
                        "confidence": "HIGH"
                    }

        # ── 2. Maximum & Minimum Loan / Credit Facility ──
        # e.g., "loan up to ₹10 lakh", "loan from ₹10 lakh to ₹1 crore", "composite loan up to ₹20 lakh", "loan of 50,000/-"
        loan_range_match = re.search(
            r"(?:loan|composite\s+loan|term\s+loan|credit\s+facility)\s*(?:amount\s+)?(?:from|between)\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(crores?|crs?|lakhs?|lacs?|thousand)?\s*(?:to|and|-)\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(crores?|crs?|lakhs?|lacs?|thousand)",
            text,
            re.IGNORECASE
        )
        if loan_range_match:
            l_min = self.parse_inr_amount(loan_range_match.group(1), loan_range_match.group(2) or loan_range_match.group(4))
            l_max = self.parse_inr_amount(loan_range_match.group(3), loan_range_match.group(4))
            if l_min:
                results["min_loan_amount"] = l_min
            if l_max:
                results["max_loan_amount"] = l_max
            results["provenance"]["loan_amount"] = {"raw": loan_range_match.group(0).strip(), "confidence": "HIGH"}
        else:
            loan_match = re.search(
                r"(?:maximum\s+(?:loan|credit)(?:\s+amount|\s+limit)?|(?:term\s+loan|composite\s+loan|credit\s+limit|loan\s+facility)\s+(?:up\s+to|ceiling|of)|(?:bank\s+)?loan(?:\s+component)?\s+(?:will\s+be\s+)?(?:up\s+to|of)|loan\s+(?:amount\s+)?up\s+to|provided\s+a\s+loan\s+of|loan\s+of)\s*(?:is|of|:|-)?\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(crores?|crs?|lakhs?|lacs?|thousand)?(?:/-)?",
                text,
                re.IGNORECASE
            )
            if loan_match:
                parsed = self.parse_inr_amount(loan_match.group(1), loan_match.group(2))
                if parsed is not None:
                    results["max_loan_amount"] = parsed
                    results["provenance"]["max_loan_amount"] = {
                        "raw": loan_match.group(0).strip(),
                        "confidence": "HIGH"
                    }

        # ── 3. Subsidy Percentage (Capital Subsidy / Margin Money Subsidy) ──
        # e.g., "subsidy of 35%", "capital subsidy of 15% to 35%", "25% government subsidy"
        subsidy_range_match = re.search(
            r"(?:capital\s+subsidy|margin\s+money\s+subsidy|government\s+subsidy|subsidy)\s*(?:is|of)?\s*(\d{1,2}(?:\.\d+)?)\s*%\s*(?:to|-)\s*(\d{1,2}(?:\.\d+)?)\s*%",
            text,
            re.IGNORECASE
        )
        if subsidy_range_match:
            try:
                s_min = float(subsidy_range_match.group(1))
                s_max = float(subsidy_range_match.group(2))
                if 0.0 < s_max <= 100.0:
                    results["subsidy_percentage"] = s_max
                    results["provenance"]["subsidy_percentage"] = {"raw": subsidy_range_match.group(0).strip(), "confidence": "HIGH"}
            except ValueError:
                pass
        else:
            subsidy_pct_match = re.search(
                r"(?:capital\s+subsidy|margin\s+money\s+subsidy|government\s+subsidy|fee\s+subsidy|subsidy\s+(?:rate|percentage|component))\s*(?:is|of|up\s+to|:|-)?\s*(\d{1,2}(?:\.\d+)?)\s*%",
                text,
                re.IGNORECASE
            )
            if not subsidy_pct_match:
                subsidy_pct_match = re.search(
                    r"(\d{1,2}(?:\.\d+)?)\s*%\s*(?:capital\s+subsidy|government\s+subsidy|subsidy)",
                    text,
                    re.IGNORECASE
                )
            if subsidy_pct_match:
                try:
                    pct = float(subsidy_pct_match.group(1))
                    if 0.0 < pct <= 100.0:
                        results["subsidy_percentage"] = pct
                        results["provenance"]["subsidy_percentage"] = {
                            "raw": subsidy_pct_match.group(0).strip(),
                            "confidence": "HIGH"
                        }
                except ValueError:
                    pass

        # ── 4. Subsidy Absolute Amount ──
        # e.g., "subsidy up to 1,25,000", "maximum subsidy of Rs. 2.5 lakh", "subsidy up to ₹2,00,000"
        subsidy_amt_match = re.search(
            r"(?:maximum\s+(?:[\w-]+\s+)*subsidy(?:\s+amount|\s+payable)?|subsidy\s+(?:cap|ceiling|limit)(?:\s+of)?|subsidy\s+up\s+to)\s*(?:is|of|:|-)?\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(crores?|crs?|lakhs?|lacs?|thousand)?(?!\s*%)(?:/-)?",
            text,
            re.IGNORECASE
        )
        if subsidy_amt_match:
            unit = subsidy_amt_match.group(2)
            parsed = self.parse_inr_amount(subsidy_amt_match.group(1), unit)
            if parsed is not None and (unit or parsed >= 1000.0):
                results["subsidy_amount"] = parsed
                results["provenance"]["subsidy_amount"] = {
                    "raw": subsidy_amt_match.group(0).strip(),
                    "confidence": "HIGH"
                }

        # ── 5. Grant Amount ──
        # e.g., "grant up to 5 Lakh", "financial assistance up to 10 Lakh (50% grant up to 5 Lakh)", "grant of ₹50,000"
        grant_match = re.search(
            r"(?:grant(?:\s+amount|\s+assistance)?\s+(?:up\s+to|of)|grant\s+of)\s*(?:is|of|:|-)?\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(crores?|crs?|lakhs?|lacs?|thousand)?(?!\s*%)(?:/-)?",
            text,
            re.IGNORECASE
        )
        if grant_match:
            unit = grant_match.group(2)
            parsed = self.parse_inr_amount(grant_match.group(1), unit)
            if parsed is not None and (unit or parsed >= 1000.0):
                results["grant_amount"] = parsed
                results["provenance"]["grant_amount"] = {
                    "raw": grant_match.group(0).strip(),
                    "confidence": "HIGH"
                }

        # ── 6. Margin Money / Beneficiary Contribution ──
        # e.g., "promoter contribution of 5%", "beneficiary contribution is 10%", "own contribution 5% to 10%"
        margin_match = re.search(
            r"(?:promoter(?:\s+contribution|\s+margin)|beneficiary\s+contribution|own\s+contribution|promoter\s+equity|margin\s+money)\s*(?:is|of|:|-)?\s*(\d{1,2}(?:\.\d+)?)\s*%",
            text,
            re.IGNORECASE
        )
        if margin_match:
            try:
                m_pct = float(margin_match.group(1))
                if 0.0 <= m_pct <= 100.0:
                    results["margin_money_percentage"] = m_pct
                    results["provenance"]["margin_money_percentage"] = {
                        "raw": margin_match.group(0).strip(),
                        "confidence": "HIGH"
                    }
            except ValueError:
                pass

        # ── 7. Interest Rate (Min / Max % p.a.) ──
        # e.g., "interest-free" -> 0%, "1% loan" -> 1%, "4% rate of interest" -> 4%, "rate of interest: 6% to 9%"
        if re.search(r"\b(?:interest-free|0%\s+interest|zero\s+interest)\b", text, re.IGNORECASE):
            results["interest_rate_min"] = 0.0
            results["interest_rate_max"] = 0.0
            results["provenance"]["interest_rate"] = {"raw": "interest-free", "confidence": "HIGH"}
        else:
            interest_range_match = re.search(
                r"(?:interest\s+rate|rate\s+of\s+interest)\s*(?:is|of)?\s*(\d{1,2}(?:\.\d+)?)\s*%\s*(?:to|-)\s*(\d{1,2}(?:\.\d+)?)\s*%",
                text,
                re.IGNORECASE
            )
            if interest_range_match:
                try:
                    i_min = float(interest_range_match.group(1))
                    i_max = float(interest_range_match.group(2))
                    if 0.0 <= i_min <= i_max <= 36.0:
                        results["interest_rate_min"] = i_min
                        results["interest_rate_max"] = i_max
                        results["provenance"]["interest_rate"] = {"raw": interest_range_match.group(0).strip(), "confidence": "HIGH"}
                except ValueError:
                    pass
            else:
                interest_match = re.search(
                    r"(?:rate\s+of\s+interest\s*(?:is|of|:)?\s*(\d{1,2}(?:\.\d+)?)\s*%|(\d{1,2}(?:\.\d+)?)\s*%\s*(?:rate\s+of\s+interest|interest\s+(?:subsidy\s+)?rate|rate\s+p\.a\.|annual\s+interest)|interest\s+(?:subsidy\s+)?rate\s*(?:is|of|:|-)?\s*(\d{1,2}(?:\.\d+)?)\s*%)",
                    text,
                    re.IGNORECASE
                )
                if interest_match:
                    try:
                        rate_str = interest_match.group(1) or interest_match.group(2) or interest_match.group(3)
                        rate = float(rate_str)
                        if 0.0 <= rate <= 36.0:
                            results["interest_rate_min"] = rate
                            results["interest_rate_max"] = rate
                            results["provenance"]["interest_rate"] = {"raw": interest_match.group(0).strip(), "confidence": "HIGH"}
                    except ValueError:
                        pass

        # ── 8. Interest Subsidy / Subvention ──
        # e.g., "interest subvention of 3%", "interest subsidy of 2%", "subvention up to 7%"
        subvention_match = re.search(
            r"(?:interest\s+subvention|interest\s+subsidy|subvention)\s*(?:is|of|up\s+to|:|-)?\s*(\d{1,2}(?:\.\d+)?)\s*%",
            text,
            re.IGNORECASE
        )
        if subvention_match:
            try:
                sub_rate = float(subvention_match.group(1))
                if 0.0 < sub_rate <= 15.0:
                    results["interest_subsidy"] = sub_rate
                    results["provenance"]["interest_subsidy"] = {"raw": subvention_match.group(0).strip(), "confidence": "HIGH"}
            except ValueError:
                pass

        # ── 9. Repayment Period (Tenure in months) ──
        # e.g., "repayment period of 5 years", "tenure of 3 to 7 years", "repayable in 36 months"
        tenure_range_match = re.search(
            r"(?:repayment\s+period|loan\s+tenure|repayable\s+in|tenure)\s*(?:is|of)?\s*(\d{1,2})\s*(?:to|-)\s*(\d{1,2})\s*years?",
            text,
            re.IGNORECASE
        )
        if tenure_range_match:
            try:
                y_min = int(tenure_range_match.group(1))
                y_max = int(tenure_range_match.group(2))
                results["repayment_period_min_months"] = y_min * 12
                results["repayment_period_max_months"] = y_max * 12
                results["provenance"]["repayment_period_months"] = {"raw": tenure_range_match.group(0).strip(), "confidence": "HIGH"}
            except ValueError:
                pass
        else:
            tenure_year_match = re.search(
                r"(?:repayment\s+period|loan\s+tenure|repayable\s+in|tenure)\s*(?:is|up\s+to|of|in|:|-)?\s*(\d{1,2})\s*years?",
                text,
                re.IGNORECASE
            )
            if tenure_year_match:
                try:
                    years = int(tenure_year_match.group(1))
                    results["repayment_period_max_months"] = years * 12
                    results["provenance"]["repayment_period_months"] = {"raw": tenure_year_match.group(0).strip(), "confidence": "HIGH"}
                except ValueError:
                    pass
            else:
                tenure_month_match = re.search(
                    r"(?:repayment\s+period|loan\s+tenure|repayable\s+in|tenure)\s*(?:is|up\s+to|of|in|:|-)?\s*(\d{1,3})\s*months?",
                    text,
                    re.IGNORECASE
                )
                if tenure_month_match:
                    try:
                        months = int(tenure_month_match.group(1))
                        results["repayment_period_max_months"] = months
                        results["provenance"]["repayment_period_months"] = {"raw": tenure_month_match.group(0).strip(), "confidence": "HIGH"}
                    except ValueError:
                        pass

        # ── 10. Moratorium (Grace period in months) ──
        # e.g., "moratorium of 6 months", "grace period of 1 year", "moratorium up to 3 years"
        moratorium_match = re.search(
            r"(?:moratorium(?:\s+period)?|grace\s+period|holiday\s+period)\s*(?:is|up\s+to|of|in|:|-)?\s*(\d{1,2})\s*(years?|months?)",
            text,
            re.IGNORECASE
        )
        if moratorium_match:
            try:
                num = int(moratorium_match.group(1))
                unit = moratorium_match.group(2).lower()
                m_months = num * 12 if "year" in unit else num
                results["moratorium_max_months"] = m_months
                results["provenance"]["moratorium_months"] = {"raw": moratorium_match.group(0).strip(), "confidence": "HIGH"}
            except ValueError:
                pass

        # ── 11. Collateral Requirement ──
        # e.g., "no collateral required", "collateral free", "without collateral" -> NO
        if re.search(r"\b(?:no\s+collateral|collateral\s+free|without\s+(?:any\s+)?collateral|zero\s+collateral|no\s+third\s+party\s+guarantee)\b", text, re.IGNORECASE):
            results["collateral_required"] = "NO"
            results["provenance"]["collateral_required"] = {"raw": "collateral-free", "confidence": "HIGH"}
        elif re.search(r"\b(?:collateral\s+is\s+mandatory|collateral\s+required|pledge\s+of\s+assets)\b", text, re.IGNORECASE):
            results["collateral_required"] = "YES"
            results["provenance"]["collateral_required"] = {"raw": "collateral-mandatory", "confidence": "HIGH"}

        # ── 12. Guarantee Requirement ──
        # e.g., "covered under CGTMSE", "credit guarantee coverage up to 85%", "CGFMU"
        guar_match = re.search(
            r"(?:covered\s+under\s+(?:cgtmse|cgssd|cgfmu)|credit\s+guarantee\s+(?:cover|coverage)?\s*(?:up\s+to\s*\d{1,2}%)?|cgtmse\s+coverage)",
            text,
            re.IGNORECASE
        )
        if guar_match:
            results["guarantee_requirement"] = guar_match.group(0).strip().upper()
            results["provenance"]["guarantee_requirement"] = {"raw": guar_match.group(0).strip(), "confidence": "HIGH"}

        # ── 13. Processing Fee ──
        # e.g., "no processing fee", "zero processing charges", "processing fee waived"
        if re.search(r"\b(?:no\s+processing\s+fee|zero\s+processing\s+charges?|processing\s+fee\s+waived|nil\s+processing\s+fee)\b", text, re.IGNORECASE):
            results["processing_fee"] = "NIL (Waived)"
            results["provenance"]["processing_fee"] = {"raw": "zero processing fee", "confidence": "HIGH"}

        # ── Backward-compatible convenience aliases ──
        results["interest_rate"] = results["interest_rate_max"] if results["interest_rate_max"] is not None else results["interest_rate_min"]
        results["repayment_period_months"] = results["repayment_period_max_months"] if results["repayment_period_max_months"] is not None else results["repayment_period_min_months"]
        results["moratorium_months"] = results["moratorium_max_months"] if results["moratorium_max_months"] is not None else results["moratorium_min_months"]

        return results

    extract_all_financial_facts = extract_financial_facts

