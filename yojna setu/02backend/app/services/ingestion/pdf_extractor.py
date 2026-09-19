import io
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
import pdfplumber

logger = logging.getLogger("yojnasetu.ingestion.pdf_extractor")


@dataclass
class PDFExtractionResult:
    success: bool
    is_scanned: bool
    ocr_status: str  # NOT_NEEDED, PERFORMED, UNAVAILABLE_OR_LOW_QUALITY
    page_count: int
    extracted_data: Dict[str, Any]
    evidence: Dict[str, Any]
    missing_fields: List[str]
    notes: List[str] = field(default_factory=list)


class OCRFallbackDetector:
    """
    Evaluates whether a PDF is text-based or a scanned/image-only document.
    Enforces quality thresholds before accepting extracted prose as facts.
    Never silently accepts low-confidence or degraded OCR.
    """

    @classmethod
    def evaluate(cls, pages_text: List[str]) -> Dict[str, Any]:
        if not pages_text:
            return {
                "is_scanned": True,
                "ocr_status": "UNAVAILABLE_OR_LOW_QUALITY",
                "reason": "PDF contains zero readable pages."
            }

        total_chars = sum(len(p.strip()) for p in pages_text)
        avg_chars = total_chars / len(pages_text) if pages_text else 0

        # Normal text-based government guideline pages contain 300 - 3000 chars per page
        if avg_chars < 50:
            return {
                "is_scanned": True,
                "ocr_status": "UNAVAILABLE_OR_LOW_QUALITY",
                "reason": f"PDF appears to be scanned/image-only (average {avg_chars:.1f} characters/page). Selectable text is sparse."
            }

        return {
            "is_scanned": False,
            "ocr_status": "NOT_NEEDED",
            "reason": f"Text-based PDF confirmed with {total_chars} characters across {len(pages_text)} pages."
        }


class OfficialGovPDFExtractor:
    """
    Structured Extractor for official government guideline circulars,
    gazette notifications, and operational manuals using pdfplumber.
    Preserves exact page numbers, section headers, and raw text evidence.
    """

    def extract(self, pdf_input: Union[bytes, str], source_url: str) -> PDFExtractionResult:
        notes: List[str] = []
        pages_text: List[str] = []

        try:
            if isinstance(pdf_input, bytes):
                pdf_file = io.BytesIO(pdf_input)
            else:
                pdf_file = pdf_input

            with pdfplumber.open(pdf_file) as pdf:
                page_count = len(pdf.pages)
                for idx, page in enumerate(pdf.pages):
                    txt = page.extract_text() or ""
                    pages_text.append(txt)

        except Exception as e:
            logger.error(f"Failed to open PDF from {source_url}: {e}")
            return PDFExtractionResult(
                success=False,
                is_scanned=False,
                ocr_status="FAILED",
                page_count=0,
                extracted_data={},
                evidence={},
                missing_fields=[],
                notes=[f"PDF read error: {str(e)}"]
            )

        # 1. Evaluate whether PDF is scanned or text-based
        eval_res = OCRFallbackDetector.evaluate(pages_text)
        if eval_res["is_scanned"]:
            return PDFExtractionResult(
                success=False,
                is_scanned=True,
                ocr_status=eval_res["ocr_status"],
                page_count=len(pages_text),
                extracted_data={"source_url": source_url},
                evidence={},
                missing_fields=["all_fields_unreadable"],
                notes=[eval_res["reason"], "Flagged for manual administrative review or specialized OCR pipeline."]
            )

        # 2. Extract structured scheme parameters across pages
        extracted: Dict[str, Any] = {
            "official_source_url": source_url,
            "source_type": "PDF"
        }
        evidence: Dict[str, Any] = {}
        full_text = "\n".join(pages_text)

        # A. Scheme Title / Name (typically Page 1)
        p1 = pages_text[0] if pages_text else ""
        title_patterns = [
            r"(?:guidelines\s+of|operational\s+guidelines\s+for|scheme\s+guidelines\s+for|scheme\s+of|notification\s+for)\s*[:–-]?\s*([^\n\r]+)",
            r"([A-Z0-9\s,\-–\(\)]{6,80}(?:YOJANA|SCHEME|MISSION|PROGRAMME|PROGRAM|NIDHI|VIKAS))"
        ]
        for pat in title_patterns:
            m = re.search(pat, p1, re.IGNORECASE)
            if m:
                clean_name = m.group(1).strip()
                if len(clean_name) >= 5 and len(clean_name) < 150:
                    extracted["scheme_name"] = clean_name
                    evidence["scheme_name"] = {
                        "text": m.group(0),
                        "source_page": "Page 1",
                        "source_section": "Document Header"
                    }
                    break

        # B. Ministry / Department
        min_match = re.search(r"(?:Government\s+of\s+India\s*\n)?(Ministry\s+of\s+[A-Za-z\s,&]+|Department\s+of\s+[A-Za-z\s,&]+)", p1, re.IGNORECASE)
        if min_match:
            min_clean = min_match.group(1).strip().split("\n")[0].strip()
            min_clean = re.sub(r",?\s*(?:Government\s+of\s+India|GoI).*$", "", min_clean, flags=re.IGNORECASE).strip()
            extracted["ministry"] = min_clean
            evidence["ministry"] = {
                "text": min_clean,
                "source_page": "Page 1",
                "source_section": "Authority Header"
            }

        # C. Scan all pages for financial limits, age, income, and subsidies with page citations
        for page_idx, page_content in enumerate(pages_text):
            page_num = f"Page {page_idx + 1}"

            # Maximum Loan / Project Cost
            if "max_loan_amount" not in extracted:
                cost_m = re.search(
                    r"(?:maximum\s+(?:project\s+cost|loan(?:\s+amount)?)|loan\s+up\s+to|ceiling\s+of|composite\s+loan\s+up\s+to)[^<\n\r]*?(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(lakhs?|crores?|thousand)?",
                    page_content,
                    re.IGNORECASE
                )
                if cost_m:
                    amt_s = cost_m.group(1).replace(",", "").strip()
                    unit_s = (cost_m.group(2) or "").lower().strip()
                    try:
                        amt = float(amt_s)
                        if "lakh" in unit_s and amt < 100000:
                            amt *= 100000.0
                        elif "crore" in unit_s and amt < 10000000:
                            amt *= 10000000.0
                        elif "thousand" in unit_s and amt < 1000:
                            amt *= 1000.0
                        extracted["max_loan_amount"] = amt
                        extracted["max_loan_amount_raw"] = cost_m.group(0)
                        evidence["max_loan_amount"] = {
                            "text": cost_m.group(0),
                            "source_page": page_num,
                            "source_section": "Financial Assistance"
                        }
                    except ValueError:
                        pass

            # Subsidy Percentage
            if "subsidy_percentage" not in extracted:
                sub_m = re.search(
                    r"(?:subsidy(?:\s+rate|\s+percentage)?|capital\s+subsidy|margin\s+money\s+subsidy)\s*(?:up\s+to|of|is)?\s*[:=-]?\s*(\d{1,2}(?:\.\d+)?)\s*%",
                    page_content,
                    re.IGNORECASE
                )
                if sub_m:
                    try:
                        extracted["subsidy_percentage"] = float(sub_m.group(1))
                        extracted["subsidy_percentage_raw"] = sub_m.group(0)
                        evidence["subsidy_percentage"] = {
                            "text": sub_m.group(0),
                            "source_page": page_num,
                            "source_section": "Subsidy / Margin Money"
                        }
                    except ValueError:
                        pass

            # Interest Rate
            if "interest_rate_max" not in extracted:
                int_m = re.search(
                    r"(?:interest\s+rate|interest\s+subvention)\s*(?:of|up\s+to)?\s*[:=-]?\s*(\d{1,2}(?:\.\d+)?)\s*%",
                    page_content,
                    re.IGNORECASE
                )
                if int_m:
                    try:
                        extracted["interest_rate_max"] = float(int_m.group(1))
                        extracted["interest_rate_max_raw"] = int_m.group(0)
                        evidence["interest_rate_max"] = {
                            "text": int_m.group(0),
                            "source_page": page_num,
                            "source_section": "Interest Subvention / Rate"
                        }
                    except ValueError:
                        pass

            # Age Criteria
            if "age_min" not in extracted:
                age_m = re.search(
                    r"(?:minimum\s+age|applicant\s+must\s+be\s+above|age\s+above|age\s+criteria)\s*(?:of|is)?\s*[:=-]?\s*(\d{1,2})\s*(?:years|yrs)",
                    page_content,
                    re.IGNORECASE
                )
                if age_m:
                    try:
                        extracted["age_min"] = int(age_m.group(1))
                        extracted["age_min_raw"] = age_m.group(0)
                        evidence["age_min"] = {
                            "text": age_m.group(0),
                            "source_page": page_num,
                            "source_section": "Eligibility Criteria"
                        }
                    except ValueError:
                        pass

            # Income Limit
            if "income_limit" not in extracted:
                inc_m = re.search(
                    r"(?:family\s+income|annual\s+income|income\s+limit)\s*(?:below|up\s+to|not\s+exceeding)?\s*[:=-]?\s*(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(lakhs?)?",
                    page_content,
                    re.IGNORECASE
                )
                if inc_m:
                    inc_str = inc_m.group(1).replace(",", "").strip()
                    unit_inc = (inc_m.group(2) or "").lower().strip()
                    try:
                        inc = float(inc_str)
                        if "lakh" in unit_inc:
                            inc *= 100000.0
                        extracted["income_limit"] = inc
                        extracted["income_limit_raw"] = inc_m.group(0)
                        evidence["income_limit"] = {
                            "text": inc_m.group(0),
                            "source_page": page_num,
                            "source_section": "Income Ceiling"
                        }
                    except ValueError:
                        pass

        # D. Target Groups Detection
        tg: List[str] = []
        c_lower = full_text.lower()
        if "street vendor" in c_lower or "urban vendor" in c_lower:
            tg.append("STREET_VENDOR")
        if "artisan" in c_lower or "craftsperson" in c_lower or "traditional trade" in c_lower or "craftsman" in c_lower:
            tg.append("ARTISAN")
        if "women" in c_lower or "mahila" in c_lower or "female" in c_lower:
            tg.append("WOMEN")
        if "scheduled caste" in c_lower or " sc " in c_lower:
            tg.append("SC")
        if "scheduled tribe" in c_lower or " st " in c_lower:
            tg.append("ST")
        if "other backward class" in c_lower or " obc " in c_lower:
            tg.append("OBC")
        if "minority" in c_lower or "minorities" in c_lower:
            tg.append("MINORITY")
        if "disability" in c_lower or "divyang" in c_lower or "pwd" in c_lower:
            tg.append("DIVYANGJAN")
        if "micro enterprise" in c_lower or "msme" in c_lower or "small enterprise" in c_lower:
            tg.append("MICRO_ENTERPRISE")

        if tg:
            extracted["target_groups"] = ", ".join(tg)
            evidence["target_groups"] = {
                "text": f"Matched demographic indicators: {tg}",
                "source_page": "Cross-document",
                "source_section": "Target Beneficiaries"
            }

        # E. Required Documents
        docs = []
        doc_patterns = [
            ("Aadhaar Card", r"aadhaar"),
            ("PAN Card", r"\bpan\s+card\b|\bpan\b"),
            ("Caste Certificate", r"caste\s+certificate|community\s+certificate"),
            ("Income Certificate", r"income\s+certificate"),
            ("Bank Passbook / Account Details", r"bank\s+passbook|bank\s+statement|account\s+details"),
            ("Detailed Project Report (DPR)", r"project\s+report|dpr|business\s+proposal"),
            ("UDYAM Registration Certificate", r"udyam|msme\s+registration"),
            ("Proof of Address / Residence", r"domicile|residence\s+proof|address\s+proof"),
        ]
        for doc_name, dpat in doc_patterns:
            if re.search(dpat, full_text, re.IGNORECASE):
                docs.append(doc_name)
        if docs:
            extracted["required_documents"] = ", ".join(docs)
            evidence["required_documents"] = {
                "text": f"Identified statutory checklist items: {docs}",
                "source_page": "Checklist section",
                "source_section": "Required Documentation"
            }

        # Identify missing fields
        expected_fields = ["scheme_name", "ministry", "max_loan_amount", "subsidy_percentage", "age_min", "income_limit", "target_groups"]
        missing = [f for f in expected_fields if f not in extracted]

        return PDFExtractionResult(
            success=True,
            is_scanned=False,
            ocr_status=eval_res["ocr_status"],
            page_count=len(pages_text),
            extracted_data=extracted,
            evidence=evidence,
            missing_fields=missing,
            notes=notes
        )
