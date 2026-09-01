# TASK AUDIT: CITIZEN PROFILE + SMART MATCHING — COMPLETE END-TO-END INTEGRATION

## Executive Summary
This document provides the authoritative implementation and verification audit for the **Citizen Profile and Smart Matching System** on the YojnaSetu Government Citizen Platform.

The Citizen Profile acts as the central canonical input connecting:
$$\text{CITIZEN PROFILE} \longrightarrow \text{DETERMINISTIC ELIGIBILITY} \longrightarrow \text{SMART MATCHING} \longrightarrow \text{SCHEME DETAILS} \longrightarrow \text{DOCUMENT GUIDANCE} \longrightarrow \text{FINANCIAL CALCULATOR} \longrightarrow \text{AUTHORIZED PARTNERS} \longrightarrow \text{OFFICIAL APPLICATION}$$

---

## 1. Canonical Profile Model & Field Schema
The canonical profile is encapsulated in `BeneficiaryProfileInput` ([profile.py](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/02backend/app/schemas/profile.py)) and persisted directly into the user record in PostgreSQL via `profile_data` JSON serialization.

### Canonical Schema Attributes:
| Domain | Field | Type | Validation / Constraints | Purpose in Workflow |
| :--- | :--- | :--- | :--- | :--- |
| **Personal & Social** | `age` | `int` | $0 \le \text{age} \le 120$ | Matches age ceilings, youth/senior programs, girl-child welfare (SSY) |
| | `gender` | `str` | Normalized (`FEMALE`, `MALE`, `TRANSGENDER`, `OTHER`) | Affirmative gender subventions, Stand-Up India, TREAD |
| | `social_category` | `str` | Normalized (`SC`, `ST`, `OBC`, `GENERAL`, `MINORITY`) | Concessional credit (NSFDC, NSTFDC, NBCFDC, NMDFC) |
| | `is_sc` | `bool` | Auto-derived from `social_category == 'SC'` | Backward compatibility with legacy SC rules |
| | `is_pwd` | `bool` | Boolean flag | Divyangjan concessional loans and accessibility assistance |
| | `is_minority` | `bool` | Boolean flag | Notified minority affirmative lending |
| | `state` | `str` | State code (e.g. `MAHARASHTRA`, `ALL_INDIA`) | State domicile filtering & Channel Partner regional locator |
| | `district` | `str` | Optional district name | District nodal office matching |
| **Economic & Income** | `annual_income` | `float` | $\ge 0.0$ | Income ceiling compliance (means-tested DBT & interest subsidies) |
| | `employment_status` | `str` | `SELF_EMPLOYED`, `UNEMPLOYED`, `SALARIED`, etc. | Livelihood vs. worker social security matching |
| **Education & Vocation** | `education_level` | `str` | `BELOW_8TH`, `8TH_PASS`, `10TH_PASS`, `GRADUATE`, etc. | Minimum educational criteria (e.g. PMEGP 8th pass rule) |
| | `applicant_type` | `str` | `INDIVIDUAL`, `ARTISAN`, `FARMER`, `STREET_VENDOR`, etc. | Target group classification |
| | `is_artisan` | `bool` | Boolean flag | PM Vishwakarma 18 traditional trades credit & toolkit |
| | `is_farmer` | `bool` | Boolean flag | PM Kisan & Agri-Infrastructure financing |
| | `is_street_vendor` | `bool` | Boolean flag | PM SVANidhi working capital micro-loans |
| | `is_safai_karamchari` | `bool` | Boolean flag | NSKFDC sanitation worker rehabilitation schemes |
| **Enterprise & Credit** | `sector` | `str` | `MSME`, `AGRICULTURE`, `TEXTILES`, `HANDICRAFTS`, etc. | Economic sector matching |
| | `activity_type` | `str` | `TRADITIONAL_TRADE_18`, `DAIRY_FARMING`, etc. | Activity eligibility filtering |
| | `business_stage` | `str` | `NEW_BUSINESS`, `EXISTING_BUSINESS`, `EXPANSION` | Greenfield vs. expansion project matching |
| | `is_new_unit` | `bool` | Auto-set based on `business_stage` | Greenfield startup criteria |
| | `project_cost` | `float` | $\ge 0.0$ | Max project cost rules & capital subsidy sizing |
| | `requested_loan_amount` | `float` | $\ge 0.0$ | Pre-fills Financial Calculator across all loan schemes |
| | `collateral_available` | `bool` | Boolean flag | Collateral-free CGTMSE preference |
| | `application_route` | `str` | `DIRECT_PORTAL`, `PARTNER_ASSISTED` | Application guidance default selection |

---

## 2. Profile Readiness Score & Missing Information Engine
Profile completion is dynamically calculated against 10 core evaluation dimensions:
1. `age`
2. `gender`
3. `social_category`
4. `state`
5. `annual_income`
6. `applicant_type`
7. `education_level`
8. `sector`
9. `business_stage`
10. `project_cost` / `requested_loan_amount`

$$\text{Readiness Score} = \left( \frac{\text{Completed Core Fields}}{10} \right) \times 100\%$$

Each missing core field generates a `MissingFieldDetail` with:
- **`field`**: Parameter name.
- **`label`**: Citizen-friendly human title.
- **`reason`**: Explanation of which schemes rely on this parameter.

---

## 3. Explainable Smart Matching Integration (90 Schemes)
The recommendation engine deterministically partitions the 90-scheme database into 3 distinct status tiers:

1. **Eligible Schemes (Passed All Hard Rules)**:
   - Ranked by deterministic soft-fit heuristic (Max 100 points across Need, Category, Sector, Stage, Geography, Amount).
   - Lists affirmative passed rules (e.g. `✓ Age 28 meets eligibility criteria`, `✓ Annual family income ₹1,80,000 is under ₹3,00,000 ceiling`, `✓ Scheduled Caste category qualifies for NSFDC concessional credit`).
   - Action Links:
     - **"View Scheme Details"**: Links to `/schemes/:schemeId?amount=:loanAmount`.
     - **"Calculate EMI"**: Links to `/schemes/:schemeId?amount=:loanAmount#calculator` with pre-filled loan amount.
     - **"Find Authorized Channel Partners"**: Links to `/channel-partners?scheme_id=:schemeId&state=:state`.
     - **"Apply on Official Portal"**: Secure modal showing verified official portal URL and gazette reference.

2. **More Information Required (`INSUFFICIENT_INFORMATION`)**:
   - Explicitly displays the exact missing profile fields (e.g. `⚠ Missing Annual Family Income: Required to verify income ceiling compliance`).
   - Provides a direct **"Complete Profile →"** CTA button allowing instant completion and auto-recalculation.

3. **Ineligible Schemes (`INELIGIBLE`)**:
   - Factually displays the exact deterministic failed rules (e.g. `✕ Applicant age 42 exceeds scheme maximum entry age of 35`, `✕ Scheme restricted to Scheduled Tribe beneficiaries`).
   - **Zero AI hallucinations** — strictly evaluated from database rules.

---

## 4. Privacy & Zero-Document Upload Policy
- **Zero Document Uploads**: The system strictly never asks for, receives, or stores scanned documents, PDF files, Aadhaar images, or bank passbooks.
- **No PII Retention in Session**: Calculations and eligibility evaluations run statelessly or against the structured profile parameters.
- **Transparent Banner**: The profile interface prominently displays the National Civic-Tech Privacy Guarantee.

---

## 5. Persistence & Multi-Authentication Architecture
- **Local Authentication**: Profile is loaded and saved via JWT bearer authentication at `GET /api/v1/profile` and `PUT /api/v1/profile`.
- **Google OAuth**: Users signing in via Google are seamlessly assigned their persistent profile record.
- **Single Profile Guarantee**: Every user has exactly one canonical profile record in PostgreSQL.
- **Guest Fallback**: For unauthenticated citizens, profile details are cached in browser `localStorage` and can be immediately promoted upon login.

---

## 6. Full Multilingual i18n Synchronization
All profile attributes, validation error messages, readiness meters, field labels, and explainability badges are 100% synchronized across all 12 supported Indian languages:
1. English (`en`)
2. Hindi (`hi`)
3. Bengali (`bn`)
4. Telugu (`te`)
5. Marathi (`mr`)
6. Tamil (`ta`)
7. Gujarati (`gu`)
8. Kannada (`kn`)
9. Malayalam (`ml`)
10. Odia (`or`)
11. Punjabi (`pa`)
12. Assamese (`as`)

---

## 7. Verification & Automated Test Results
- **Dedicated Profile Test Suite** ([test_citizen_profile_smart_matching.py](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/02backend/tests/test_citizen_profile_smart_matching.py)): **17 / 17 Tests Passed (100%)**.
- **Full Backend Pytest Suite**: **335 / 335 Tests Passed (100%)** in 35 test files.
- **Frontend TypeScript Build** (`npm run build`): **0 Errors, Compiled Successfully**.
