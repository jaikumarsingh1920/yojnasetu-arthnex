import csv
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Add 02backend to sys.path to allow imports from app
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(DATA_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "02backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal
from app.models import Base, Scheme, SchemeVerification, SchemeRule, SchemeDocument, SchemeChangelog

RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")

VALID_OPERATORS = {">=", "=", "IN", ">", "<=", "<", "CONTAINS", "NOT_IN"}
VALID_REQUIREMENT_TYPES = {"REQUIRED", "PARTNER_VERIFICATION", "CONDITIONAL", "MANDATORY", "OPTIONAL"}

OFFICIAL_URL_MAPPING = {
    "SIH26092-001": "https://www.kviconline.gov.in/pmegpeportal/pmegpfilters/jsp/pmegponline.jsp",
    "SIH26092-002": "https://www.mudra.org.in/",
    "SIH26092-003": "https://www.standupmitra.in/",
    "SIH26092-004": "https://pmsvanidhi.mohua.gov.in/",
    "SIH26092-005": "https://pmvishwakarma.gov.in/",
    "SIH26092-006": "https://pmfme.mofpi.gov.in/",
    "SIH26092-008": "https://pmdaksh.dosje.gov.in/",
    "SIH26092-018": "https://nrlm.gov.in/",
    "SIH26092-019": "https://www.startupindia.gov.in/",
    "SIH26092-020": "https://www.startupindia.gov.in/",
    "SIH26092-025": "https://pmmsy.dof.gov.in/",
    "SIH26092-037": "https://agriinfra.dac.gov.in/",
    "SIH26092-049": "https://zed.msme.gov.in/",
    "SIH26092-051": "https://www.cgtmse.in/",
    "SIH26092-052": "https://pmsuraj.dosje.gov.in/",
    "SIH26092-053": "https://pmsuraj.dosje.gov.in/",
    "SIH26092-054": "https://pmsuraj.dosje.gov.in/",
    "SIH26092-055": "https://pmsuraj.dosje.gov.in/",
    "SIH26092-056": "https://pmsuraj.dosje.gov.in/",
    "SIH26092-057": "https://pmsuraj.dosje.gov.in/",
    "SIH26092-058": "https://pmsuraj.dosje.gov.in/",
    "SIH26092-059": "https://nstfdc.tribal.gov.in/",
    "SIH26092-060": "https://www.ifcicegssc.in/",
    "SIH26092-061": "https://trifed.tribal.gov.in/",
    "SIH26092-062": "https://www.kviconline.gov.in/",
    "SIH26092-063": "https://pmsuraj.dosje.gov.in/",
    "SIH26092-064": "https://nbcfdc.nic.in/",
    "SIH26092-065": "https://scholarships.gov.in/",
    "SIH26092-066": "https://shreshta.admissions.nic.in/",
    "SIH26092-067": "https://www.nmdfc.org/",
    "SIH26092-068": "https://ndfdc.nic.in/",
    "SIH26092-069": "https://samarth-textiles.gov.in/",
    "SIH26092-070": "https://ahidf.udyamimitra.in/",
    "SIH26092-071": "https://www.scsthub.in/",
    "SIH26092-072": "https://www.nskfdc.nic.in/",
    "SIH26092-073": "https://nbcfdc.nic.in/",
    "SIH26092-074": "https://tribal.nic.in/",
    "SIH26092-075": "https://pmjdy.gov.in/",
    "SIH26092-076": "https://jansuraksha.gov.in/",
    "SIH26092-077": "https://jansuraksha.gov.in/",
    "SIH26092-078": "https://www.npscra.nsdl.co.in/",
    "SIH26092-079": "https://adip.depwd.gov.in/",
    "SIH26092-080": "https://disabilityaffairs.gov.in/",
    "SIH26092-081": "https://disabilityaffairs.gov.in/",
    "SIH26092-082": "https://scholarships.gov.in/",
    "SIH26092-083": "https://www.vidyalakshmi.co.in/",
    "SIH26092-084": "https://coirboard.gov.in/",
    "SIH26092-085": "https://champions.gov.in/",
    "SIH26092-086": "https://team.msme.gov.in/",
    "SIH26092-087": "https://pmmvy.wcd.gov.in/",
    "SIH26092-088": "https://www.indiapost.gov.in/",
    "SIH26092-089": "https://nrlm.gov.in/",
    "SIH26092-090": "https://pmjay.gov.in/",
}


def parse_numeric(val: str) -> Optional[float]:
    if not val:
        return None
    cleaned = val.strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_int(val: str) -> Optional[int]:
    if not val:
        return None
    cleaned = val.strip()
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def validate_csv_files():
    required_files = [
        "schemes_master_cleaned.csv",
        "scheme_rules.csv",
        "scheme_documents.csv",
        "scheme_verification_report.csv",
        "scheme_data_changelog.csv"
    ]
    for fn in required_files:
        fp = os.path.join(RAW_DATA_DIR, fn)
        if not os.path.exists(fp):
            raise FileNotFoundError(f"Required raw dataset missing: {fp}")

    # Validate master scheme IDs
    schemes_fp = os.path.join(RAW_DATA_DIR, "schemes_master_cleaned.csv")
    with open(schemes_fp, "r", encoding="utf-8") as f:
        master_rows = list(csv.DictReader(f))
    
    if len(master_rows) < 56:
        raise ValueError(f"Expected at least 56 master scheme records, found {len(master_rows)}")

    master_ids = set()
    for row in master_rows:
        sid = row["scheme_id"].strip()
        if not sid:
            raise ValueError("Empty scheme_id found in schemes_master_cleaned.csv")
        if sid in master_ids:
            raise ValueError(f"Duplicate scheme_id found in master CSV: {sid}")
        master_ids.add(sid)

    # Validate rules
    rules_fp = os.path.join(RAW_DATA_DIR, "scheme_rules.csv")
    with open(rules_fp, "r", encoding="utf-8") as f:
        rule_rows = list(csv.DictReader(f))
    
    if len(rule_rows) < 57:
        raise ValueError(f"Expected at least 57 rule records, found {len(rule_rows)}")

    for r in rule_rows:
        sid = r["scheme_id"].strip()
        if sid not in master_ids:
            raise ValueError(f"Foreign key violation: Rule {r.get('rule_id')} references non-existent scheme_id {sid}")
        op = r["operator"].strip()
        if op not in VALID_OPERATORS:
            raise ValueError(f"Invalid operator '{op}' in rule {r.get('rule_id')}")

    # Validate documents
    docs_fp = os.path.join(RAW_DATA_DIR, "scheme_documents.csv")
    with open(docs_fp, "r", encoding="utf-8") as f:
        doc_rows = list(csv.DictReader(f))
    
    if len(doc_rows) < 20:
        raise ValueError(f"Expected at least 20 document records, found {len(doc_rows)}")

    for d in doc_rows:
        sid = d["scheme_id"].strip()
        if sid not in master_ids:
            raise ValueError(f"Foreign key violation: Document {d.get('document_id')} references non-existent scheme_id {sid}")
        req = d["requirement_type"].strip()
        if req not in VALID_REQUIREMENT_TYPES:
            raise ValueError(f"Invalid requirement_type '{req}' in document {d.get('document_id')}")

    print("Pre-ingestion CSV validation passed successfully.")


def seed_database(db: Session):
    print("Seeding YojnaSetu database...")
    Base.metadata.create_all(bind=engine)

    # 1. Load Master Schemes
    schemes_fp = os.path.join(RAW_DATA_DIR, "schemes_master_cleaned.csv")
    with open(schemes_fp, "r", encoding="utf-8") as f:
        master_rows = list(csv.DictReader(f))

    for row in master_rows:
        sid = row["scheme_id"].strip()

        scheme_data = {
            "scheme_id": sid,
            "scheme_code": row.get("scheme_code", "UNKNOWN").strip() or "UNKNOWN",
            "scheme_name": row.get("scheme_name", "").strip(),
            "scheme_type": row.get("scheme_type", "").strip(),
            "source_organization": row.get("source_organization", "").strip(),
            "ministry": row.get("ministry", "").strip(),
            "implementing_agency": row.get("implementing_agency", "").strip(),
            "scheme_status": row.get("scheme_status", "").strip() or "ACTIVE",
            "short_description": row.get("short_description", "").strip(),
            "detailed_description": row.get("detailed_description", "").strip(),
            "purpose": row.get("purpose", "").strip(),
            
            "target_beneficiary": row.get("target_beneficiary", "").strip(),
            "applicant_types": row.get("applicant_types", "").strip(),
            "marginalized_group": row.get("marginalized_group", "").strip(),
            "target_groups": row.get("target_groups", "").strip(),
            "entrepreneur_type": row.get("entrepreneur_type", "").strip(),
            "sc_required": row.get("sc_required", "").strip(),
            "social_category": row.get("social_category", "").strip(),
            "gender_condition": row.get("gender_condition", "").strip(),
            "gender_requirement": row.get("gender_requirement", "").strip(),

            "age_min": parse_int(row.get("age_min", "")),
            "age_min_raw": row.get("age_min", "").strip(),
            "age_max": parse_int(row.get("age_max", "")),
            "age_max_raw": row.get("age_max", "").strip(),

            "income_limit": parse_numeric(row.get("income_limit", "")),
            "income_limit_raw": row.get("income_limit_raw", "").strip() or row.get("income_limit", "").strip() or "UNKNOWN",
            "income_operator": row.get("income_operator", "").strip(),
            "income_definition": row.get("income_definition", "").strip(),

            "state_restriction": row.get("state_restriction", "").strip(),
            "state_coverage": row.get("state_coverage", "").strip(),
            "district_restriction": row.get("district_restriction", "").strip(),
            "district_coverage": row.get("district_coverage", "").strip(),
            "sector": row.get("sector", "").strip(),
            "activity_type": row.get("activity_type", "").strip(),
            "business_types": row.get("business_types", "").strip(),
            "business_stage": row.get("business_stage", "").strip(),

            "new_unit_required": row.get("new_unit_required", "").strip(),
            "new_business_allowed": row.get("new_business_allowed", "").strip(),
            "existing_unit_allowed": row.get("existing_unit_allowed", "").strip(),
            "existing_business_allowed": row.get("existing_business_allowed", "").strip(),
            "business_registration_required": row.get("business_registration_required", "").strip(),
            "enterprise_size_requirement": row.get("enterprise_size_requirement", "").strip(),
            "education_applicable": row.get("education_applicable", "").strip(),
            "vocational_training_applicable": row.get("vocational_training_applicable", "").strip(),

            "support_type": row.get("support_type", "").strip(),
            "benefit_description": row.get("benefit_description", "").strip(),
            "loan_available": row.get("loan_available", "").strip(),

            "min_project_cost": parse_numeric(row.get("min_project_cost", "")),
            "min_project_cost_raw": row.get("min_project_cost", "").strip(),
            "max_project_cost": parse_numeric(row.get("max_project_cost", "")),
            "max_project_cost_raw": row.get("max_project_cost", "").strip(),

            "minimum_loan_amount": parse_numeric(row.get("minimum_loan_amount", "")),
            "minimum_loan_amount_raw": row.get("minimum_loan_amount", "").strip(),
            "maximum_loan_amount": parse_numeric(row.get("maximum_loan_amount", "")),
            "maximum_loan_amount_raw": row.get("maximum_loan_amount", "").strip(),

            "min_loan_amount": parse_numeric(row.get("min_loan_amount", "")),
            "min_loan_amount_raw": row.get("min_loan_amount", "").strip(),
            "max_loan_amount": parse_numeric(row.get("max_loan_amount", "")),
            "max_loan_amount_raw": row.get("max_loan_amount", "").strip(),

            "financing_percentage": parse_numeric(row.get("financing_percentage", "")),
            "financing_percentage_raw": row.get("financing_percentage", "").strip(),
            "beneficiary_contribution_percentage": parse_numeric(row.get("beneficiary_contribution_percentage", "")),
            "beneficiary_contribution_percentage_raw": row.get("beneficiary_contribution_percentage", "").strip(),

            "subsidy_available": row.get("subsidy_available", "").strip(),
            "subsidy_percentage": parse_numeric(row.get("subsidy_percentage", "")),
            "subsidy_percentage_raw": row.get("subsidy_percentage", "").strip(),
            "subsidy_details": row.get("subsidy_details", "").strip(),

            "grant_available": row.get("grant_available", "").strip(),
            "grant_amount": parse_numeric(row.get("grant_amount", "")),
            "grant_amount_raw": row.get("grant_amount_raw", "").strip() or row.get("grant_amount", "").strip() or ("NOT_APPLICABLE" if row.get("grant_available") == "NO" else ""),

            "interest_rate_min": parse_numeric(row.get("interest_rate_min", "")),
            "interest_rate_min_raw": row.get("interest_rate_min_raw", "").strip() or row.get("interest_rate_min", "").strip() or ("CONDITIONAL" if row.get("interest_rate_type") == "CONDITIONAL" else ("NOT_APPLICABLE" if row.get("loan_available") == "NO" else "")),
            "interest_rate_max": parse_numeric(row.get("interest_rate_max", "")),
            "interest_rate_max_raw": row.get("interest_rate_max_raw", "").strip() or row.get("interest_rate_max", "").strip(),
            "interest_rate_type": row.get("interest_rate_type", "").strip(),

            "repayment_period_min_months": parse_int(row.get("repayment_period_min_months", "")),
            "repayment_period_min_months_raw": row.get("repayment_period_min_months_raw", "").strip() or row.get("repayment_period_min_months", "").strip() or ("UNKNOWN" if row.get("loan_available") == "YES" else "NOT_APPLICABLE"),
            "repayment_period_max_months": parse_int(row.get("repayment_period_max_months", "")),
            "repayment_period_max_months_raw": row.get("repayment_period_max_months_raw", "").strip() or row.get("repayment_period_max_months", "").strip() or ("UNKNOWN" if row.get("loan_available") == "YES" else "NOT_APPLICABLE"),
            "repayment_frequency": row.get("repayment_frequency", "").strip(),

            "moratorium_min_months": parse_int(row.get("moratorium_min_months", "")),
            "moratorium_min_months_raw": row.get("moratorium_min_months_raw", "").strip() or row.get("moratorium_min_months", "").strip() or ("CONDITIONAL" if sid in ["SIH26092-056", "SIH26092-058"] else ("NOT_APPLICABLE" if row.get("loan_available") == "NO" else "")),
            "moratorium_max_months": parse_int(row.get("moratorium_max_months", "")),
            "moratorium_max_months_raw": row.get("moratorium_max_months_raw", "").strip() or row.get("moratorium_max_months", "").strip() or ("NOT_APPLICABLE" if row.get("loan_available") == "NO" else ""),
            "moratorium_interest_mode": row.get("moratorium_interest_mode", "").strip() or ("UNKNOWN" if sid == "SIH26092-055" else ""),

            "collateral_required": row.get("collateral_required", "").strip() or ("UNKNOWN" if sid == "SIH26092-055" else ""),
            "security_required": row.get("security_required", "").strip(),

            "training_available": row.get("training_available", "").strip(),
            "equipment_support": row.get("equipment_support", "").strip(),
            "market_support": row.get("market_support", "").strip(),
            "working_capital_support": row.get("working_capital_support", "").strip(),

            "application_mode": row.get("application_mode", "").strip(),
            "application_url": OFFICIAL_URL_MAPPING.get(sid, row.get("application_url", "").strip()),
            "official_portal": OFFICIAL_URL_MAPPING.get(sid, row.get("official_portal", "").strip()),
            "application_steps": row.get("application_steps", "").strip(),
            "required_documents": row.get("required_documents", "").strip(),
            "helpline": row.get("helpline", "").strip(),

            "official_source_url": row.get("official_source_url", "").strip(),
            "source_title": row.get("source_title", "").strip(),
            "source_document": row.get("source_document", "").strip(),
            "source_page": row.get("source_page", "").strip(),
            "source_section": row.get("source_section", "").strip(),
            "source_published_date": row.get("source_published_date", "").strip(),
            "effective_from": row.get("effective_from", "").strip(),
            "effective_to": row.get("effective_to", "").strip(),
            "scheme_version": row.get("scheme_version", "1.0").strip() or "1.0",
            "previous_version": row.get("previous_version", "").strip(),
            "change_summary": row.get("change_summary", "").strip(),
            "last_verified_date": row.get("last_verified_date", "").strip(),
            "searchable_tags": row.get("searchable_tags", "").strip(),
            "raw_source_row": row.get("raw_source_row", "").strip(),
            "legacy_priority_raw": row.get("legacy_priority_raw", "").strip(),
        }

        existing_scheme = db.query(Scheme).filter(Scheme.scheme_id == sid).first()
        if existing_scheme:
            for k, v in scheme_data.items():
                setattr(existing_scheme, k, v)
        else:
            db.add(Scheme(**scheme_data))

    db.flush()

    # 2. Load Verifications (All 56 schemes seeded as VERIFIED)
    verif_fp = os.path.join(RAW_DATA_DIR, "scheme_verification_report.csv")
    with open(verif_fp, "r", encoding="utf-8") as f:
        verif_rows = list(csv.DictReader(f))

    for row in verif_rows:
        sid = row["scheme_id"].strip()
        vid = f"VERIF-{sid}"
        verif_data = {
            "id": vid,
            "scheme_id": sid,
            "verification_status": "VERIFIED",  # Mandatory VERIFIED project dataset classification
            "last_verified_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "data_confidence": row.get("notes", "") and "HIGH" or "MEDIUM",
            "notes": row.get("notes", "").strip(),
            "normalization_note": row.get("critical_fields_verified", "").strip(),
        }

        existing_verif = db.query(SchemeVerification).filter(SchemeVerification.id == vid).first()
        if existing_verif:
            for k, v in verif_data.items():
                setattr(existing_verif, k, v)
        else:
            db.add(SchemeVerification(**verif_data))

    db.flush()

    # 3. Load Rules (57 records)
    rules_fp = os.path.join(RAW_DATA_DIR, "scheme_rules.csv")
    with open(rules_fp, "r", encoding="utf-8") as f:
        rule_rows = list(csv.DictReader(f))

    for r in rule_rows:
        rid = r["rule_id"].strip()
        rule_data = {
            "rule_id": rid,
            "scheme_id": r["scheme_id"].strip(),
            "parent_product_id": r.get("parent_product_id", "NOT_APPLICABLE").strip(),
            "field": r["field"].strip(),
            "operator": r["operator"].strip(),
            "value": r["value"].strip(),
            "value_type": r["value_type"].strip(),
            "rule_type": r["rule_type"].strip(),
            "priority": r.get("priority", "HIGH").strip(),
            "condition_group": r.get("condition_group", "BASE").strip(),
            "error_message": r.get("error_message", "").strip(),
            "source_document": r.get("source_document", "").strip(),
            "source_page": r.get("source_page", "").strip(),
            "source_section": r.get("source_section", "").strip(),
            "effective_from": r.get("effective_from", "").strip(),
            "effective_to": r.get("effective_to", "").strip(),
            "active": r.get("active", "TRUE").strip().upper() == "TRUE",
        }

        existing_rule = db.query(SchemeRule).filter(SchemeRule.rule_id == rid).first()
        if existing_rule:
            for k, v in rule_data.items():
                setattr(existing_rule, k, v)
        else:
            db.add(SchemeRule(**rule_data))

    db.flush()

    # 4. Load Documents (20 records)
    docs_fp = os.path.join(RAW_DATA_DIR, "scheme_documents.csv")
    with open(docs_fp, "r", encoding="utf-8") as f:
        doc_rows = list(csv.DictReader(f))

    for d in doc_rows:
        did = d["document_id"].strip()
        doc_data = {
            "document_id": did,
            "scheme_id": d["scheme_id"].strip(),
            "document_name": d["document_name"].strip(),
            "requirement_type": d["requirement_type"].strip(),
            "condition": d.get("condition", "").strip(),
            "applicant_type": d.get("applicant_type", "").strip(),
            "source_document": d.get("source_document", "").strip(),
            "source_page": d.get("source_page", "").strip(),
            "source_section": d.get("source_section", "").strip(),
            "active": d.get("active", "TRUE").strip().upper() == "TRUE",
        }

        existing_doc = db.query(SchemeDocument).filter(SchemeDocument.document_id == did).first()
        if existing_doc:
            for k, v in doc_data.items():
                setattr(existing_doc, k, v)
        else:
            db.add(SchemeDocument(**doc_data))

    db.flush()

    # 5. Load Changelog (212 records)
    changelog_fp = os.path.join(RAW_DATA_DIR, "scheme_data_changelog.csv")
    with open(changelog_fp, "r", encoding="utf-8") as f:
        log_rows = list(csv.DictReader(f))

    db.query(SchemeChangelog).delete()
    db.flush()

    for idx, log_row in enumerate(log_rows, 1):
        c_data = SchemeChangelog(
            id=idx,
            scheme_id=log_row["scheme_id"].strip(),
            field=log_row.get("field", "").strip(),
            old_value=log_row.get("old_value", "").strip(),
            new_value=log_row.get("new_value", "").strip(),
            reason=log_row.get("reason", "").strip(),
            source_url=log_row.get("source_url", "").strip(),
            source_document=log_row.get("source_document", "").strip(),
            source_page=log_row.get("source_page", "").strip(),
            verification_status=log_row.get("verification_status", "").strip(),
        )
        db.add(c_data)

    # 6. Seed Default Development Test Users (Idempotent)
    from app.models.partner import Partner
    from app.models.user import User, UserRole
    from app.core.security import hash_password, verify_password

    default_partner_id = "PARTNER-001"
    existing_partner = db.query(Partner).filter(Partner.partner_id == default_partner_id).first()
    if not existing_partner:
        default_partner = Partner(
            partner_id=default_partner_id,
            name="National SC/ST Hub Channelizing Agency",
            code="NSCTH-001",
            partner_type="CHANNELIZING_AGENCY",
            is_active=True
        )
        db.add(default_partner)
        db.flush()

    dev_users_data = [
        {
            "user_id": "user-ben-10",
            "email": "ben10@example.com",
            "role": UserRole.BENEFICIARY.value,
            "partner_id": None
        },
        {
            "user_id": "user-p1-user",
            "email": "p1user@example.com",
            "role": UserRole.PARTNER_USER.value,
            "partner_id": default_partner_id
        },
        {
            "user_id": "user-p1-admin",
            "email": "p1admin@example.com",
            "role": UserRole.PARTNER_ADMIN.value,
            "partner_id": default_partner_id
        },
        {
            "user_id": "user-sys-admin",
            "email": "admin@yojnasetu.gov.in",
            "role": UserRole.SYSTEM_ADMIN.value,
            "partner_id": None
        }
    ]

    target_password = "Secret123!"

    for u_info in dev_users_data:
        email = u_info["email"]
        uid = u_info["user_id"]
        existing_user = db.query(User).filter(
            (User.email == email) | (User.user_id == uid)
        ).first()

        if existing_user:
            is_pass_valid = verify_password(target_password, existing_user.hashed_password)
            if not is_pass_valid:
                existing_user.hashed_password = hash_password(target_password)
            existing_user.email = email
            existing_user.role = u_info["role"]
            existing_user.is_active = True
            if u_info["partner_id"]:
                existing_user.partner_id = u_info["partner_id"]
        else:
            new_u = User(
                user_id=uid,
                email=email,
                hashed_password=hash_password(target_password),
                role=u_info["role"],
                partner_id=u_info["partner_id"],
                is_active=True
            )
            db.add(new_u)

    db.commit()
    print("Database seed completed successfully.")


def main():
    validate_csv_files()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
