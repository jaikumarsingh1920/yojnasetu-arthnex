import uuid
import logging
from typing import Dict, Any, List, Optional
from app.models.document import SchemeDocument

logger = logging.getLogger("yojnasetu.ingestion.document_generator")


class SchemeDocumentGenerator:
    """
    Deterministic SchemeDocument Generator.
    Converts extracted document requirements from official guidelines into canonical SchemeDocument records.
    """

    KNOWN_DOCUMENT_METADATA = {
        "aadhaar": ("Aadhaar Card", "MANDATORY", "Proof of citizen identity and demographic verification"),
        "pan": ("PAN Card", "MANDATORY", "Proof of tax registration and financial identity"),
        "caste": ("Caste / Category Certificate", "CONDITIONAL", "Required for affirmative action and concessional category benefits"),
        "income": ("Income Certificate", "CONDITIONAL", "Required for schemes with family income ceilings"),
        "project report": ("Detailed Project Report (DPR)", "MANDATORY", "Itemized project cost, machinery estimate, and revenue projection"),
        "dpr": ("Detailed Project Report (DPR)", "MANDATORY", "Itemized project cost, machinery estimate, and revenue projection"),
        "bank": ("Bank Passbook / Statement", "MANDATORY", "Proof of active bank account and IFSC details for direct disbursement"),
        "passbook": ("Bank Passbook / Statement", "MANDATORY", "Proof of active bank account and IFSC details for direct disbursement"),
        "udyam": ("UDYAM Registration Certificate", "CONDITIONAL", "Required for registered MSME enterprise units"),
        "address": ("Proof of Address / Residence", "MANDATORY", "Electricity bill, ration card, or voter ID verifying applicant domicile"),
        "domicile": ("Domicile / Residence Certificate", "CONDITIONAL", "Required for state-specific residency verification"),
        "quotation": ("Machinery Quotations / Invoices", "CONDITIONAL", "Proforma invoice from certified suppliers for capital equipment"),
    }

    @classmethod
    def generate_documents_for_scheme(
        cls,
        scheme_id: str,
        data: Dict[str, Any],
        source_doc: Optional[str] = None,
        source_page: Optional[str] = None,
        source_sec: Optional[str] = None
    ) -> List[SchemeDocument]:
        documents: List[SchemeDocument] = []
        doc = source_doc or data.get("source_document") or "Official Scheme Guidelines"
        page = source_page or data.get("source_page") or "Guidelines Document"
        sec = source_sec or data.get("source_section") or "Required Documentation"

        req_text = str(data.get("required_documents") or "").lower()
        if not req_text:
            # Fallback: if no documents specified in guideline, generate standard baseline documents
            req_text = "aadhaar, bank passbook, detailed project report"

        matched_keys = set()
        for kw, (d_name, req_type, condition) in cls.KNOWN_DOCUMENT_METADATA.items():
            if kw in req_text and d_name not in matched_keys:
                matched_keys.add(d_name)
                documents.append(SchemeDocument(
                    document_id=f"DOC-{uuid.uuid4().hex[:10]}",
                    scheme_id=scheme_id,
                    document_name=d_name,
                    requirement_type=req_type,
                    condition=condition,
                    applicant_type="INDIVIDUAL",
                    source_document=doc,
                    source_page=page,
                    source_section=sec,
                    active=True
                ))

        logger.info(f"Generated {len(documents)} SchemeDocument records for scheme {scheme_id}")
        return documents
