# Channel Partner Financial Data Provenance & Anti-Fabrication Principles

## 1. Principles of Financial Data Integrity
In accordance with SIH26092 mandates and ethical AI governance standards:
1. **Zero Fabrication**: No financial metric (Gross NPA, Net NPA, Overdue Amount, Fund Utilization %, Net Profit, Guarantee Status) is ever simulated, guessed, or invented.
2. **Missing != Healthy**: The absence of an observation means the metric is strictly classified as `NOT_PUBLICLY_VERIFIED` or `UNKNOWN`. Absence of negative news never implies financial health.
3. **Multi-Dimensionality**: We strictly reject pseudo-scientific aggregate scores such as "Financial Health = 87/100". Financial health consists of distinct legal and prudential dimensions evaluated individually against versioned statutory rules.
4. **Sector-Level Isolation**: Macro-economic or sector-level intelligence (such as SIDBI Microfinance Pulse delinquency trends across MFIs) is labeled `SECTOR_CONTEXT`. It provides situational awareness but CANNOT serve as evidence to disqualify an individual partner.
5. **Generic Policy != Individual Status**: A regulatory rule requiring 100% fund utilization sets the qualification threshold; it never implies that a given partner has achieved 100% unless official partner-level records exist.

---

## 2. Regulatory Authority Hierarchy
When resolving data points or identifying applicable thresholds, YojnaSetu strictly adheres to the following authority hierarchy:

| Dimension | Primary Authority (Tier 1) | Secondary Authority (Tier 2) | Fallback / Context (Tier 3) |
| :--- | :--- | :--- | :--- |
| **Prudential Disbursement Norms** | National Scheduled Castes Finance & Development Corporation (NSFDC) | Ministry of Social Justice & Empowerment (MoSJE) | General Banking Circulars |
| **Commercial Bank NPA & Profitability** | Reserve Bank of India (RBI DBIE / Statistical Tables) | Audited Annual Reports / Pillar 3 Filings | DFS Banking Disclosures |
| **Regional Rural Bank (RRB) Metrics** | NABARD / Department of Financial Services (DFS) | Individual RRB Audited Accounts | Sponsor Bank Disclosures |
| **Institutional Lineage & Mergers** | DFS Gazette Notifications | RBI Banking Notifications | State Welfare Gazette |
| **SCA Governance & Guarantees** | State Welfare Department / State Finance Dept | NSFDC Annual Reports | State Budget Allocations |
| **Microfinance Sector Trends** | SIDBI Microfinance Pulse | MFIN / Sa-Dhan Publications | Industry Reports (Context only) |

---

## 3. Conflict Resolution Policy
If conflicting observations exist between two official authorities (e.g. RBI DBIE reports NNPA of 1.23% for FY24 while the bank's audited press release reports 1.18%):
1. **Both Records Preserved**: Neither record is silently overwritten or deleted. Both remain stored with distinct `source_authority`, `publication_date`, and `source_document` citations.
2. **Deterministic Precedence**:
   - For statutory banking metrics: The statutory regulator (RBI/NABARD) takes precedence over unaudited marketing releases.
   - For same-tier sources: The later audited balance sheet with explicit reporting period end date (`period_end`) takes precedence.
3. **Unresolved Divergence**: If divergence cannot be reconciled objectively, the record is flagged `CONFLICTING_OFFICIAL_DATA` and routing falls back to the more conservative prudential evaluation.

---

## 4. Freshness Policy
1. **Periodic vs. Real-Time**: Annual audited statements (Form B balance sheets) remain valid throughout the following operating financial year until the subsequent statutory audit is published.
2. **No False "LIVE" Labels**: Periodic annual/quarterly reports are labeled `LATEST_AVAILABLE_OFFICIAL` with explicit `data_as_of` and `period_end` dates. The label "LIVE" is strictly reserved for real-time API feeds.
3. **Staleness Threshold**: Banking reports exceeding 18 months from the reporting period end date are flagged `STALE`. Stale data is never used to clear a restricted partner without human admin review.

---

## 5. Financial Scope Policy
Every financial metric and observation in YojnaSetu strictly records and displays its `financial_scope`:

1. **`INSTITUTION_LEVEL`**:
   - Covers official regulatory indicators published at the parent legal entity level (e.g. RBI DBIE Statistical Tables for Scheduled Commercial Banks, NABARD Key Statistics for RRBs).
   - Under statutory banking regulations, branches do not publish individual balance sheets or Profit & Loss statements.
   - All branch-level UI displays explicitly state: *"Parent institution regulatory indicator (branch-level balance sheets are not published under banking regulations)"*.
2. **`POLICY_LEVEL`**:
   - Covers statutory lending norms codified in scheme guidelines (e.g. NSFDC 100% cumulative fund utilization rule, zero overdues payable to NSFDC).
   - Establishes eligibility criteria; does NOT assert individual partner performance without authenticated agency data.
3. **`SECTOR_LEVEL`**:
   - Covers macro-economic and industry delinquency trends (e.g. SIDBI Microfinance Pulse).
   - Strictly firewalled as contextual information; never attached as partner-level observation or used for routing exclusion.
4. **`BRANCH_LEVEL`**:
   - Restricted strictly to verified physical point-of-presence data (coordinates, operational status, contact information). Branch-level financial balance sheet claims are rejected unless backed by branch-specific official audit documentation.

