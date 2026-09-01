# YojnaSetu: Final Dynamic Scheme Architecture & Canonical Consistency Report

**System Version**: 2.0.0-PROD  
**Database**: SQLite (`yojnasetu.db`) + Canonical CSV Master (`schemes_master_cleaned.csv`)  
**Audit Status**: 100% Verified Canonical Architecture (90 Schemes, 126 Rules, 98 Statutory Documents, 105 Channel Partners, 90 Verified Provenance Records)  
**Test Suite**: 398 / 398 Tests Passed (100%)  
**Frontend Bundle**: Clean Vite Production Build (0 TypeScript Errors)  

---

## 1. Executive Summary & Core Architectural Paradigm

YojnaSetu has been transitioned to a **single canonical scheme data architecture**. In this architecture:
- Every user-facing view, calculation engine, recommendation model, RAG vector store, comparison table, and AI conversational copilot consumes from the **single authoritative canonical dataset**.
- Hardcoded scheme arrays, duplicate mock objects, fake loan defaults (e.g. arbitrary `0%` interest or `₹0` loans for grant schemes), and misleading application-processing workflows have been eliminated.
- YojnaSetu is explicitly established as an **assisted discovery, deterministic eligibility evaluation, document readiness preparation, and official government portal routing platform**.

```
                       ┌─────────────────────────────────────────────────────────┐
                       │          SINGLE CANONICAL SCHEME DATA SOURCE            │
                       │   04data/raw/schemes_master_cleaned.csv  +  SQLite DB   │
                       └────────────────────────────┬────────────────────────────┘
                                                    │
                                                    ▼
                       ┌─────────────────────────────────────────────────────────┐
                       │                    FASTAPI BACKEND                      │
                       │       (Schemes, Rules, Documents, Partners, Provenance) │
                       └──────┬─────────────────────┬─────────────────────┬──────┘
                              │                     │                     │
               ┌──────────────┴────────┐  ┌─────────┴─────────┐  ┌────────┴─────────────┐
               │  Deterministic Logic  │  │ Dynamic RAG & AI  │  │ User / Admin Service │
               │  • Eligibility Engine │  │ • SQLite TF-IDF   │  │ • Document Checklist │
               │  • Financial Calc     │  │ • Query Classifier│  │ • Saved Schemes      │
               │  • Recommendation     │  │ • Agent Sandbox   │  │ • Data Governance    │
               └──────────────┬────────┘  └─────────┬─────────┘  └────────┬─────────────┘
                              │                     │                     │
                              └─────────────────────┼─────────────────────┘
                                                    ▼
                       ┌─────────────────────────────────────────────────────────┐
                       │                   REACT FRONTEND (SPA)                  │
                       │   • Scheme Details & Dynamic Financial Calculator       │
                       │   • Multi-Scheme Comparison Matrix                      │
                       │   • Explainable Recommendations & Readiness Checklist   │
                       │   • Dynamic Partner Locator & Official Portal Routing   │
                       │   • Admin Data Governance & Provenance Auditing         │
                       └─────────────────────────────────────────────────────────┘
```

---

## 2. Canonical Scheme Data Source & Synchronization

### 2.1 Storage & Single Source of Truth
- **Master Files**: [04data/raw/schemes_master_cleaned.csv](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/04data/raw/schemes_master_cleaned.csv) and [90_SCHEMES_COMPLETE_DATASET.csv](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/90_SCHEMES_COMPLETE_DATASET.csv).
- **SQLite Database**: `02backend/app/yojnasetu.db` and `02backend/yojnasetu.db`.
- **Database Schema**:
  - `schemes`: 90 central/state schemes with official attributes, ministry ownership, financial classification, and official portal URLs.
  - `scheme_verifications`: 90 provenance records with SHA-256 integrity hashes, official source documents, page numbers, and verification timestamps.
  - `scheme_rules`: 126 deterministic eligibility and financial rules evaluated without LLM hallucination.
  - `scheme_documents`: 98 statutory document requirements categorized by `REQUIRED`, `CONDITIONAL`, and `OPTIONAL`.
  - `partners` & `partner_scheme_mappings`: 105 verified physical branches (PSBs, RRBs, NBFC-MFIs, State Channelizing Agencies).
  - `scheme_changelogs`: Complete data lineage audit trail.

---

## 3. Semantic Missing-Data & Assistance-Type Modeling

A key failure mode of naive welfare portals is coercing missing or non-credit data into `0`, `₹0`, `0%`, or `N/A`. YojnaSetu strictly separates:

| Scheme Category | Assistance Type | Interest Rate Field | Max Loan Amount Field | Calculator UI Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Credit / Term Loan** (e.g. PMEGP, Mudra) | Bank Loan / Composite | Numeric (`% p.a.`) or `None` (as per lending bank) | Numeric (`₹X Lakh / Cr`) | Computes EMI, Interest breakdown, and Amortization |
| **Capital Subsidy / Grant** (e.g. PM-KISAN, PMMVY, MSE-CDP) | Direct Benefit Transfer / Grant | `NOT_APPLICABLE` (`None`) | `NOT_APPLICABLE` (`None`) | Displays **"Loan / EMI calculation is not applicable for this scheme."** |
| **Credit Guarantee** (e.g. CGTMSE, CGSS) | Guarantee Cover | `NOT_APPLICABLE` (`None`) | Guarantee Limit (e.g. ₹5 Cr / ₹10 Cr) | Explains collateral waiver & guarantee coverage limits |
| **Skill Training / Toolkit** (e.g. PM-DAKSH, PM Vishwakarma) | Free Training & Toolkits | `NOT_APPLICABLE` (`None`) | Concessional Loan / Toolkit Grant | Displays stipend & toolkit disbursement details |
| **Unspecified Interest Rates** (e.g. PM Mudra Yojana) | Discretionary Bank Loan | `None` (`interest_rate: null`) | Loan Ceiling | Displays **"Interest rate determined by lending bank as per RBI guidelines"** (no fake 0% or 7% default) |

---

## 4. Deterministic Engines vs AI Responsibilities

### 4.1 Strict Separation of Questions
1. **Question A: "Can the citizen qualify for this scheme?"**  
   - Handled exclusively by `DeterministicEligibilityEngine`.
   - Evaluates boolean operators (`EQ`, `IN`, `LTE`, `GTE`, `BETWEEN`, `SUBSET_OF`) against statutory rules.
   - Status outputs: `ELIGIBLE`, `INELIGIBLE`, or `MORE_INFORMATION_REQUIRED`.
   - AI / Gemini is **never** permitted to decide eligibility.

2. **Question B: "What financial terms apply if qualified?"**  
   - Handled exclusively by `DeterministicFinancialEngine`.
   - Uses `Decimal` precision arithmetic.
   - Returns full parameter traceability (`master_numeric`, `source_doc`, `source_page`).
   - If scheme is non-credit, immediately returns status `NOT_APPLICABLE` with descriptive advisory warnings.

### 4.2 Dynamic Retrieval-Augmented Generation (RAG)
- `SchemeVectorStore` builds dynamic TF-IDF and BM25 index chunks **at runtime directly from SQLite**.
- Chunks include scheme objectives, eligibility summaries, statutory documents, and verified ministry URLs.
- Sanitizer cleans all internal rule codes (`RULE-XXXX`), raw database headers (`FIELD:`), and SQL keywords before returning text to the citizen.
- Conversational queries (language switches, greetings, generic questions) exit early without pulling random scheme cards or fabricating numbers.

---

## 5. Elimination of Misleading Workflows

| Removed Misleading Feature | Architectural Replacement | Truthful Citizen-Centric Framing |
| :--- | :--- | :--- |
| **"Application Processing Queue" / "Under Review" / "Sanctioned"** | Citizen Document Checklist & Official Routing | Clarified that YojnaSetu **does not process or sanction government applications**. Citizens prepare their checklists and apply on official `.gov.in` / `.nic.in` portals. |
| **Admin "Application Approval Workflow"** | Data Governance & Provenance Audit Panel | Admin tabs: **Overview, Schemes Audit, Rules Engine, Document Checklist, Scheme Changelogs, AI/RAG Health**. |
| **Hardcoded `DIRECT_PORTAL_SCHEME_IDS`** | Dynamic Partner Mapping API | If no physical branch is mapped in the area, UI dynamically instructs citizen to apply via the official government portal. |
| **Hardcoded `0%` Interest Rate Defaults** | Explicit Sentinel Resolution (`NOT_APPLICABLE`, `UNSPECIFIED_BANK_RATE`) | Displays statutory rate or clarifies that lending bank determines rate under RBI norms. |

---

## 6. Verification & Test Results

### 6.1 Pytest Test Suite
```bash
python -m pytest tests/ -q
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 54%]
........................................................................ [ 72%]
........................................................................ [ 90%]
......................................                                   [100%]
398 passed in 80.16s (0:01:20)
```
- **Total Tests**: 398
- **Passed**: 398 (100%)
- **Failed**: 0
- **Errors**: 0

### 6.2 Data Quality & Provenance Audit
```bash
python scripts/audit_scheme_data.py
Audit complete: 90/90 schemes passed all strict data quality checks.
0 fake values, 0 broken URLs, 0 missing mandatory fields.
```

### 6.3 Frontend Production Build
```bash
npm run build
> tsc -b && vite build
✓ 1852 modules transformed.
dist/index.html                     0.81 kB │ gzip:   0.46 kB
dist/assets/index-BH5XTIEO.css     85.29 kB │ gzip:  17.75 kB
dist/assets/index-Cy5Scxhz.js   1,436.91 kB │ gzip: 387.87 kB
✓ built in 6.23s
```
- **TypeScript Errors**: 0
- **Build Status**: Succeeded

---

## 7. Known System Constraints & Operational Guidance

1. **State-Specific Branch Density**:
   - Channel partner branch data is currently concentrated on National Public Sector Banks, Regional Rural Banks (RRBs), NBFC-MFIs, and State Channelizing Agencies (SCAs) mapped to NSFDC / MSME programs.
   - For schemes without mapped physical branches, the UI dynamically and truthfully routes the citizen to the verified official government portal (`.gov.in` / `.nic.in`).
2. **Bank Discretionary Lending Terms**:
   - Under schemes like PM Mudra Yojana (PMMY) or Stand-Up India, final interest rates and collateral terms are subject to borrower credit assessment and RBI lending guidelines. YojnaSetu explicitly displays this bank discretion rather than assuming arbitrary fixed rates.
