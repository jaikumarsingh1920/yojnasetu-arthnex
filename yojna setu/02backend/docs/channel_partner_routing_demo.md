# Channel Partner Intelligent Routing — Gorakhpur Live Demonstration (SIH26092)

## 1. Demonstration Parameters

- **Applicant Location**: Gorakhpur, Uttar Pradesh (Latitude: `26.7606° N`, Longitude: `83.3732° E`)
- **Target Enterprise Project**: Dairy Farming & Livestock Development
- **Required Financing Amount**: ₹3,00,000 (₹3 Lakh)
- **Facility Requested**: Term Loan (Asset Acquisition / Infrastructure)
- **Statutory Scheme**: NSFDC Term Loan Scheme (`SIH26092-053`) / PMEGP (`SIH26092-001`) / PMMY Kishore (`SIH26092-002`)
- **Backend Routing Endpoint**: `/api/v1/partners/nearest` (and `/api/v1/partner/financial-health/{partner_id}`)

---

## 2. End-to-End Routing Execution & Results

### Summary of Nearest Eligible Points of Presence

| Rank | Partner Branch / Point of Presence | Legal Institution | Institution Type | Haversine Distance | Net NPA (Audited) | Financial Scope | Routing Status | Applicable Rule Outcome |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **1** | **Central Bank of India Main Branch Gorakhpur** | Central Bank of India | Public Sector Bank | **0.26 km** | 0.55% (FY25) | `INSTITUTION_LEVEL` | `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION` | Commercial Bank Regulated by RBI; RRB NNPA rule `NOT_APPLICABLE` |
| **2** | **Punjab National Bank Circle Office & Branch Gorakhpur** | Punjab National Bank | Public Sector Bank | **0.28 km** | 0.40% (FY25) | `INSTITUTION_LEVEL` | `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION` | Commercial Bank Regulated by RBI; RRB NNPA rule `NOT_APPLICABLE` |
| **3** | **Union Bank of India Regional Office & Branch Gorakhpur** | Union Bank of India | Public Sector Bank | **0.35 km** | 0.63% (FY25) | `INSTITUTION_LEVEL` | `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION` | Commercial Bank Regulated by RBI; RRB NNPA rule `NOT_APPLICABLE` |
| **4** | **Indian Bank Main Branch Gorakhpur** | Indian Bank | Public Sector Bank | **0.82 km** | 0.19% (FY25) | `INSTITUTION_LEVEL` | `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION` | Commercial Bank Regulated by RBI; RRB NNPA rule `NOT_APPLICABLE` |
| **5** | **Bank of Baroda MSME Branch Gorakhpur** | Bank of Baroda | Public Sector Bank | **3.61 km** | 0.58% (FY25) | `INSTITUTION_LEVEL` | `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION` | Commercial Bank Regulated by RBI; RRB NNPA rule `NOT_APPLICABLE` |
| **6** | **Baroda U.P. Bank Head Office Gorakhpur** | Baroda U.P. Bank | Regional Rural Bank | **3.64 km** | 2.10% (FY25) | `INSTITUTION_LEVEL` | `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION` | NSFDC RRB NNPA < 15% (`2.10% < 15.0%` -> **PASS**); Profit 4/6 yrs -> **PASS** |
| **7** | **Canara Bank MSME Sulabh Branch Gorakhpur** | Canara Bank | Public Sector Bank | **3.98 km** | 0.70% (FY25) | `INSTITUTION_LEVEL` | `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION` | Commercial Bank Regulated by RBI; RRB NNPA rule `NOT_APPLICABLE` |

---

## 3. Deep Evidence Breakdown for Selected Partners

### Case A: Baroda U.P. Bank Head Office Gorakhpur (3.64 km away)
- **Point of Presence**: Baroda U.P. Bank Head Office, Taramandal / Buddh Vihar Commercial Complex, Gorakhpur
- **Legal Institution**: Baroda U.P. Bank (Corporate ID: `RRB-BUPB-01`, NABARD Code: `NAB-RRB-UP-01`)
- **Institution Type**: `REGIONAL_RURAL_BANK` (Sponsored by Bank of Baroda)
- **Distance**: 3.64 km
- **Routing Status**: `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION`
- **Applicable Rules Evaluated**:
  1. `NSFDC_RRB_NNPA_001` (Net NPA < 15%):
     - **Observed Value**: `2.10%`
     - **Threshold**: `< 15.0%`
     - **Result**: **PASS**
     - **Source**: NABARD Key Statistics of RRBs FY25
     - **Scope**: `INSTITUTION_LEVEL`
  2. `NSFDC_RRB_PROFIT_001` (Net Profit in >= 3 of preceding 6 financial years):
     - **Observed Value**: `4.0 years`
     - **Threshold**: `>= 3.0 years`
     - **Result**: **PASS**
     - **Source**: DFS Consolidated Performance Review of RRBs
     - **Scope**: `INSTITUTION_LEVEL`
  3. `NSFDC_GEN_OVERDUE_001` (Zero Overdues to NSFDC):
     - **Observed Status**: `NOT_PUBLICLY_VERIFIED`
     - **Result**: Policy Requirement; Non-public administrative filing in internal Ministry MIS.
  4. `NSFDC_GEN_UTILIZATION_001` (100% Cumulative Fund Utilization):
     - **Observed Status**: `NOT_PUBLICLY_VERIFIED`
     - **Result**: Policy Requirement; Non-public administrative filing in internal Ministry MIS.
- **Why this partner?**:
  - Located 3.64 km from Gorakhpur citizen.
  - Formally authorized implementing partner for NSFDC Term Loan Scheme.
  - Authorized for `TERM_LOAN` credit facility.
  - Meets statutory RRB Net NPA ceiling (2.10% vs 15.0% threshold).
  - Profitable in 4 out of last 6 financial years.
- **Limitations Disclosed**: Current partner-level utilization certificates and overdue repayment ledgers are non-public internal administrative filings.

---

### Case B: Central Bank of India Main Branch Gorakhpur (0.26 km away)
- **Point of Presence**: Central Bank of India Main Branch, Golghar, Gorakhpur
- **Legal Institution**: Central Bank of India (RBI Code: `CBI-PSB-003`)
- **Institution Type**: `PUBLIC_SECTOR_BANK`
- **Distance**: 0.26 km
- **Routing Status**: `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION`
- **Financial Indicators**:
  - **Net NPA Ratio**: `0.55%` (Source: RBI DBIE / Audited Annual Results FY25 as of 31 March 2025)
  - **Gross NPA Ratio**: `3.18%` (Source: RBI DBIE / Audited Annual Results FY25)
  - **CRAR Ratio**: `15.08%` (Source: RBI DBIE Statistical Tables Table B7 as of 31 March 2024)
- **Financial Scope**: `INSTITUTION_LEVEL` ("Parent institution regulatory indicator; branch-level balance sheets are not published under banking regulations").
- **Rule Applicability**:
  - `NSFDC_RRB_NNPA_001`: `NOT_APPLICABLE` (NSFDC RRB Net NPA criterion applies strictly to Regional Rural Banks, not Scheduled Commercial Banks).
  - General Overdue & Utilization criteria: `POLICY_REQUIREMENTS` (Partner-level administrative ledgers marked `NOT_PUBLICLY_VERIFIED`).

---

## 4. Why No Real Partner in Gorakhpur is Currently Restricted

In compliance with **Section 29 of the Mandate** ("Do not manufacture a restricted partner just for the demo. If no real partner is currently restricted: say so"):

1. **Solvency of Operating Institutions**: All 7 channel partner branches located in Gorakhpur belong to solvent, operating legal institutions:
   - Central Bank of India (NNPA 0.55%)
   - Punjab National Bank (NNPA 0.40%)
   - Union Bank of India (NNPA 0.63%)
   - Indian Bank (NNPA 0.19%)
   - Bank of Baroda (NNPA 0.58%)
   - Baroda U.P. Bank (NNPA 2.10%)
   - Canara Bank (NNPA 0.70%)
2. **Zero Fabrication Policy**: The system refuses to inject synthetic 22.5% NNPA records into the production database simply to "stage" an exclusion in Gorakhpur.
3. **Verified Hard Restriction Behavior in Test Suite**:
   - In isolated automated adversarial tests (`test_rrb_high_nnpa_hard_exclusion_scenario`), when an RRB partner is evaluated with NNPA = 16.0% or 22.5%, the engine immediately sets `routing_status: "RESTRICTED_HIGH_NPA"`, marks it non-routable, and overrides distance ranking so that applications are NEVER sent to restricted partners.

---

## 5. Answers to SIH Technical Reviewer Questions

| Question | Deterministic System Answer |
| :--- | :--- |
| **"Where did this NPA number come from?"** | "From NABARD Key Statistics of RRBs FY25 (for Baroda U.P. Bank) and RBI DBIE Statistical Tables Table B7 / Audited Disclosures (for PSBs)." |
| **"Is this branch's financial health or its parent institution's?"** | "This is `INSTITUTION_LEVEL` data belonging to the legal banking corporation. Branch-level balance sheets are not published under Indian banking regulations." |
| **"Is this data live?"** | "No. It is officially audited statutory data as of 31 March 2025. Live partner-by-partner utilization certificates are non-public administrative filings." |
| **"Does the 15% NNPA rule apply to PSBs?"** | "No. Under NSFDC operational guidelines, the 15% NNPA rule applies exclusively to Regional Rural Banks. PSBs are governed by RBI statutory guidelines." |
| **"Why did you route to Baroda U.P. Bank?"** | "It is located 3.64 km away, is authorized for NSFDC Term Loan Scheme, supports Term Loans, has verified Net NPA of 2.10% (<15% limit), and was profitable in 4 of the last 6 financial years." |
