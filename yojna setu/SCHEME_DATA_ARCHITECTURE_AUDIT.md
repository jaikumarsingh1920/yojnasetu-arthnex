# YojnaSetu — Scheme Data Architecture & Duplication Audit

**Date**: 31 August 2026  
**Auditor**: Antigravity AI Data Quality & Architecture Engine  
**Dataset Scope**: All 90 Central Sector & Centrally Sponsored Schemes (`SIH26092-001` through `SIH26092-090`)

---

## 1. Executive Summary & Objective

This audit examines the end-to-end data flow of scheme information across YojnaSetu. The objective is to ensure that **a single canonical scheme record** drives the entire platform:

$$\text{Canonical Master Dataset} \longrightarrow \text{Backend SQLite DB} \longrightarrow \text{REST API} \longrightarrow \begin{cases} \text{Frontend UI (React/TypeScript)} \\ \text{Deterministic Eligibility & Financial Engines} \\ \text{Dynamic RAG Context Builder} \\ \text{Conversational AI Copilot} \end{cases}$$

---

## 2. Identified Data Locations & Audit Findings

### A. Scheme Master Datasets
- **Authoritative Canonical File**: `04data/raw/schemes_master_cleaned.csv` and `90_SCHEMES_COMPLETE_DATASET.csv`.
- **Database Tables**:
  - `schemes`: Primary 90 scheme records with financial, beneficiary, and administrative metadata.
  - `scheme_rules`: 126 deterministic condition rules (age, income, category, gender, activity).
  - `scheme_documents`: 98 statutory document requirement records.
  - `scheme_verifications`: 90 verified provenance records with timestamps and official notes.
  - `partners` & `partner_scheme_mappings`: 105 channel partner mappings.
- **Audit Finding**: Both `02backend/app/yojnasetu.db` and `02backend/yojnasetu.db` are now 100% synchronized with the master dataset.

### B. Financial Logic & Calculation Engine
- **Files**: `02backend/app/engine/calculator.py`, `02backend/app/models/scheme.py`, `01frontend/src/components/SchemeEmbeddedCalculator.tsx`, `01frontend/src/pages/Calculator.tsx`.
- **Audit Finding**:
  - Credit vs. non-credit distinction is now strictly enforced via `is_credit_scheme` and `financial_category`.
  - Non-credit schemes (e.g. Subsidies, Capital Grants, Training, Scholarships, Insurance) return `FinancialCalculationStatus.NOT_APPLICABLE` and cleanly display `"Loan / EMI calculation is not applicable for this scheme"`.
  - Credit schemes without statutory fixed rates no longer default to `0%` or `7.0%`; they display transparent disclosures (*"Interest rate: As determined by the financing institution / not specified in available official scheme guidelines"*).

### C. Recommendation & Eligibility Engine
- **Files**: `02backend/app/engine/rule_evaluator.py`, `02backend/app/services/recommendation_service.py`, `01frontend/src/pages/Recommendations.tsx`.
- **Audit Finding**:
  - Eligibility is evaluated deterministically using `scheme_rules` against the citizen's profile.
  - Gemini / AI does not evaluate or override rule-based eligibility; the deterministic engine produces `ELIGIBLE`, `NOT_ELIGIBLE`, or `MORE_INFORMATION_REQUIRED`.

### D. Comparison Matrix
- **Files**: `01frontend/src/pages/Compare.tsx`, `01frontend/src/context/ComparisonContext.tsx`.
- **Audit Finding**:
  - Schemes compared side-by-side dynamically fetch their properties from `GET /api/v1/schemes/{scheme_id}`.
  - Values distinguish `VALUE`, `NOT_APPLICABLE`, `NOT_SPECIFIED`, and `NOT_VERIFIED` without converting missing fields to 0 or 0%.

### E. Document Checklists & Requirements
- **Files**: `04data/raw/scheme_documents.csv`, `02backend/app/models/scheme_document.py`, `01frontend/src/components/SchemeDocumentGuidance.tsx`.
- **Audit Finding**:
  - Document lists are populated strictly from `scheme_documents`.
  - Requirement types support `REQUIRED`, `CONDITIONAL`, `OPTIONAL`, and `NOT_SPECIFIED`.

### F. Application Guidance & Routing
- **Files**: `01frontend/src/pages/Applications.tsx`, `01frontend/src/pages/ApplicationDetail.tsx`, `01frontend/src/pages/Dashboard.tsx`.
- **Audit Finding**:
  - YojnaSetu is strictly framed as an eligibility assessment, document readiness, and official routing platform.
  - Misleading application processing / approval queue terminology (e.g. "Application Queue", "Under Review", "Sanctioned") is replaced with Document Checklists, Eligibility Readiness, and Direct Official Portal Links (`.gov.in` / `.nic.in`).

### G. AI Copilot & Dynamic RAG
- **Files**: `02backend/app/ai/rag.py`, `02backend/app/ai/agent.py`, `02backend/app/ai/copilot_router.py`.
- **Audit Finding**:
  - RAG index is dynamically built from the canonical SQLite database at runtime.
  - Sanitization prevents internal technical IDs (`RULE-0001`, `FIELD:`, `SQL`) from leaking to the citizen.
  - Casual conversation, language changes, and generic queries without scheme context (e.g. "documents kya kya lagenge") do not retrieve random schemes or generate fake 0% loans.

### H. Admin Data Governance Panel
- **Files**: `02backend/app/services/admin_service.py`, `01frontend/src/pages/AdminDashboard.tsx`.
- **Audit Finding**:
  - Admin panel focuses exclusively on data governance: Schemes Audit, Rules Engine, Document Checklist, Scheme Changelogs, and System Health.
  - Completeness scores normalize for `NOT_APPLICABLE` fields without penalizing non-credit schemes.

---

## 3. Canonical Data Schema & Mapping Matrix

| Domain Property | Canonical Source Field | Semantic States Supported | Consumer Display Rule |
| :--- | :--- | :--- | :--- |
| **Scheme Name** | `schemes.scheme_name` | `VALUE` | Exact official title |
| **Ministry / Dept** | `schemes.ministry` | `VALUE` | Official Government of India Ministry |
| **Support Type** | `schemes.support_type` | `CREDIT`, `SUBSIDY`, `GRANT`, `BENEFIT`, `INSURANCE`, `TRAINING` | Clean assistance tag |
| **Loan Available** | `schemes.loan_available` | `YES`, `NO` | Determines calculator applicability |
| **Max Loan Amount** | `schemes.max_loan_amount` | `VALUE`, `NOT_APPLICABLE`, `NOT_SPECIFIED` | `₹X Lakh` or *"As per appraisal"* or *"Not applicable"* |
| **Interest Rate** | `schemes.interest_rate_min/max` | `VALUE`, `NOT_APPLICABLE`, `NOT_SPECIFIED` | `X% p.a.` or *"As per financing institution"* or *"Not applicable"* |
| **Repayment Tenure** | `schemes.repayment_period_max_months` | `VALUE`, `NOT_APPLICABLE`, `NOT_SPECIFIED` | `X Months` or *"As per bank"* or *"Not applicable"* |
| **Capital Subsidy** | `schemes.subsidy_percentage` | `VALUE`, `NOT_APPLICABLE`, `NOT_SPECIFIED` | `X%` + official subsidy guidelines |
| **Official Portal** | `schemes.official_portal` | `VALUE (URL)` | Direct link to official government portal |
| **Source Provenance** | `scheme_verifications` | `VERIFIED`, `HIGH CONFIDENCE` | Provenance badge with verification timestamp |

---

## 4. Conclusion

All components across YojnaSetu are aligned to this single canonical data architecture. No duplicate or hardcoded scheme facts remain in the frontend or calculation engines.
