# Government Financial Data Sources & Provenance Registry (SIH26092)

## 1. Executive Summary & Statutory Data Hierarchy

This document provides a legally defensible, authoritative provenance catalog for all financial, statutory, and regulatory datasets ingested by **YojnaSetu** for Channel Partner Financial Intelligence and Intelligent Routing.

In strict adherence to the **Anti-Fabrication and Truth-in-Data Mandate**, YojnaSetu strictly separates:
- **`INSTITUTION_LEVEL` Data**: Statutory financial indicators (Gross NPA, Net NPA, CRAR, Operating Profits) belonging to the regulated corporate legal entity (e.g., Bank of Baroda, Baroda U.P. Bank).
- **`BRANCH_LEVEL` Data**: Specific branch/office points of presence. (Under Indian banking regulations, individual bank branches do not publish public balance sheets or branch-specific NPA ratios).
- **`POLICY_LEVEL` Data**: Statutory eligibility rules, criteria, and disbursement norms published by NSFDC / MoSJE.
- **`SECTOR_LEVEL` Data**: Aggregate industry-wide trends (e.g., SIDBI Microfinance Pulse). *Strictly firewalled: sector averages are never converted into individual partner financial health.*

---

## 2. Authoritative Source Catalog

### Source 1: NSFDC Lending Policy & Guidelines for Implementation
- **Authority**: National Scheduled Castes Finance and Development Corporation (NSFDC)
- **Ministry**: Ministry of Social Justice and Empowerment (MoSJE), Government of India
- **Official URL**: [https://nsfdc.nic.in/allocation-of-funds](https://nsfdc.nic.in/allocation-of-funds)
- **Official Portal**: [https://nsfdc.nic.in/](https://nsfdc.nic.in/)
- **Document**: *Notional Allocation of Funds & Norms for Disbursement (Section 3 & Section 3.1)*
- **Publication Date**: Updated periodically; codified in operational lending guidelines
- **Reporting Period**: Standing Prudential Policy (Effective 2024–2026)
- **Metrics**: 
  - `OVERDUE_STATUS` (`== "CLEAR"` / `"NO_OVERDUE"`)
  - `FUND_UTILIZATION_PERCENT` (`>= 100.0%` cumulative)
  - `GUARANTEE_STATUS` (`== "ADEQUATE"`)
  - `NNPA_PERCENT` (`< 15.0%` for Regional Rural Banks)
  - `PROFITABLE_YEARS_COUNT` (`>= 3` years of net profit in preceding 6 financial years for RRBs)
- **Scope**: `POLICY_LEVEL` (Prudential Criteria)
- **Partner-Level?**: No. These define the statutory eligibility criteria; they do not contain individual live partner ledgers in open public data.
- **Institution-Level?**: Yes, when applied to evaluate institution balance sheets.
- **Sector-Level?**: No.
- **Policy-Level?**: **Yes (Authoritative Policy Root)**.
- **Routing Usable?**: **Yes (Deterministic Prudential Rule Definition)**.
- **Limitations**: NSFDC does not publish live, partner-by-partner monthly utilization certificates (UCs) or daily overdue ledgers on its open web portal.

---

### Source 2: Reserve Bank of India — DBIE & Statistical Tables Relating to Banks in India
- **Authority**: Reserve Bank of India (RBI)
- **Official URL**: [https://dbie.rbi.org.in/](https://dbie.rbi.org.in/) and [https://www.rbi.org.in/](https://www.rbi.org.in/)
- **Document**: *Statistical Tables Relating to Banks in India (Table B7: Asset Quality & Capital Adequacy Indicators of Scheduled Commercial Banks)*; *Report on Trend and Progress of Banking in India*
- **Publication Date**: Annual Audited Releases (Latest comprehensive statistical table: November 2024; FY2024-25 provisional/audited results: June–July 2025)
- **Reporting Period**: Financial Year ending 31 March 2024 (audited) and 31 March 2025 (audited statutory disclosures)
- **Metrics**:
  - `GNPA_PERCENT` (Gross Non-Performing Assets Ratio)
  - `NNPA_PERCENT` (Net Non-Performing Assets Ratio)
  - `CRAR_PERCENT` (Capital to Risk-Weighted Assets Ratio)
  - `NET_PROFIT_AMOUNT` (Net Annual Profit in ₹ Crore)
- **Scope**: `INSTITUTION_LEVEL`
- **Partner-Level?**: No (Branch-level balance sheets are not published).
- **Institution-Level?**: **Yes (Bank Legal Entity Level)**.
- **Sector-Level?**: Aggregates available; bank-wise schedules used.
- **Policy-Level?**: No.
- **Routing Usable?**: **Yes (Official Financial Indicator for PSBs & Commercial Banks)**.
- **Limitations**: Scheduled Commercial Banks are evaluated under RBI Prudential Framework for Resolution of Stressed Assets. The NSFDC RRB NNPA rule (<15%) is marked `NOT_APPLICABLE` to PSBs.

---

### Source 3: NABARD — Key Statistics of Regional Rural Banks
- **Authority**: National Bank for Agriculture and Rural Development (NABARD)
- **Official URL**: [https://www.nabard.org/](https://www.nabard.org/)
- **Document**: *Key Statistics of Regional Rural Banks in India (Annual Statement of Financial Condition, Asset Quality and Operations of RRBs)*
- **Publication Date**: Annual statutory release (Latest: August 2024 / July 2025)
- **Reporting Period**: Financial Years 2023–24 and 2024–25 (as of 31 March)
- **Metrics**:
  - `NNPA_PERCENT` (Net NPA of each individual RRB)
  - `GNPA_PERCENT` (Gross NPA of each individual RRB)
  - `NET_PROFIT_AMOUNT` (Operating Profit / Net Profit)
  - `PROFITABLE_YEARS_COUNT` (Historical trend over 6-year operational audit)
- **Scope**: `INSTITUTION_LEVEL`
- **Partner-Level?**: No (RRB bank-wide data; not individual branch-level).
- **Institution-Level?**: **Yes (Individual Regional Rural Bank Level)**.
- **Sector-Level?**: Aggregates available; RRB-specific schedules utilized.
- **Policy-Level?**: No.
- **Routing Usable?**: **Yes (Authoritative Input for NSFDC RRB NNPA < 15% and Profitability Rules)**.
- **Limitations**: Data is audited annually; mid-year un-audited quarterly returns for RRBs are not universally published across all 43 RRBs.

---

### Source 4: Department of Financial Services (DFS) — Consolidated Review of RRBs & Gazette Notifications
- **Authority**: Department of Financial Services, Ministry of Finance, Government of India
- **Official URL**: [https://financialservices.gov.in/](https://financialservices.gov.in/)
- **Document**: *Consolidated Performance Review of Regional Rural Banks*; *Extraordinary Gazette Notifications on RRB Amalgamation (Section 23A of RRB Act 1976)*
- **Publication Date**: Annual Reviews (Latest: 2024–2025); Gazette Notifications (2019, 2020, May 2025 "One State, One RRB" roadmap)
- **Reporting Period**: 2019–2025
- **Metrics**:
  - `PROFITABLE_YEARS_COUNT` (Preceding 6 financial years profit status)
  - Legal successor mapping for amalgamated RRBs (e.g., Purvanchal Bank + Kashi Gomti Samyut Gramin Bank -> Baroda U.P. Bank)
- **Scope**: `INSTITUTION_LEVEL`
- **Partner-Level?**: No.
- **Institution-Level?**: **Yes (RRB Corporate Lineage & Profitability History)**.
- **Sector-Level?**: Yes.
- **Policy-Level?**: Statutory Amalgamation Law.
- **Routing Usable?**: **Yes (Entity Resolution Lineage & Profitability Validation)**.
- **Limitations**: Legal amalgamations alter asset books; historical records must be traced with explicit successor continuity.

---

### Source 5: Ministry of Social Justice and Empowerment (MoSJE) & Parliamentary Questions (Sansad)
- **Authority**: Ministry of Social Justice and Empowerment / Lok Sabha & Rajya Sabha Secretariat
- **Official URL**: [https://socialjustice.gov.in/](https://socialjustice.gov.in/) and [https://sansad.in/](https://sansad.in/)
- **Document**: *MoSJE Annual Reports*; *Demands for Grants*; *Lok Sabha Unstarred Questions & Annexures on NSFDC/NBCFDC Fund Disbursements*
- **Publication Date**: Regular Parliamentary Sessions (2023, 2024, 2025)
- **Reporting Period**: State-wise cumulative allocations (FY2021-22 to FY2024-25)
- **Metrics**: State-level notional allocations, cumulative sanctions, and overall corporation recoveries.
- **Scope**: `POLICY_LEVEL` / `SECTOR_LEVEL`
- **Partner-Level?**: No. Parliamentary tables report state-wise and corporation totals; individual partner ledger accounts are classified as internal administrative accounts.
- **Institution-Level?**: No (Aggregated by State Channelizing Agency totals, not bank branch level).
- **Sector-Level?**: Yes.
- **Policy-Level?**: Yes.
- **Routing Usable?**: **Verification of Corporate Guarantee backing and Scheme Channeling Status**.
- **Limitations**: Partner-level live fund utilization ledgers are non-public internal administrative filings.

---

### Source 6: SIDBI — Microfinance Pulse & Regulatory Sector Disclosures
- **Authority**: Small Industries Development Bank of India (SIDBI) in collaboration with Equifax India
- **Official URL**: [https://www.sidbi.in/](https://www.sidbi.in/)
- **Document**: *Microfinance Pulse (Quarterly Industry Report on NBFC-MFIs, SFBs, and Rural Credit)*
- **Publication Date**: Quarterly (Latest: Q3 & Q4 2024 / 2025)
- **Reporting Period**: Quarterly 30+ DPD, 90+ DPD portfolio delinquency benchmarks
- **Metrics**: Macroeconomic portfolio at risk (PAR 30+, PAR 90+) across micro-lending tiers.
- **Scope**: `SECTOR_LEVEL`
- **Partner-Level?**: **NO (Strictly Forbidden from partner financial attribution)**.
- **Institution-Level?**: No.
- **Sector-Level?**: **YES (Macro Industry Benchmark Only)**.
- **Policy-Level?**: No.
- **Routing Usable?**: **NO for Partner Health / YES for Contextual Display Only**.
- **Limitations**: In compliance with Section 10 of SIH26092 requirements, SIDBI sector data is strictly firewalled and is NEVER transformed into an individual channel partner's NPA or health rating.

---

### Source 7: Official Statutory Partner Disclosures (Audited Annual Statements)
- **Authority**: Respective Legal Institutions (e.g., Bank of Baroda, Baroda U.P. Bank, State Bank of India, UPSCFDC)
- **Official URLs**:
  - Bank of Baroda: [https://www.bankofbaroda.in/](https://www.bankofbaroda.in/)
  - Baroda U.P. Bank: [https://www.barodaupbank.in/](https://www.barodaupbank.in/)
  - Punjab National Bank: [https://www.pnbindia.in/](https://www.pnbindia.in/)
  - State Bank of India: [https://www.sbi.co.in/](https://www.sbi.co.in/)
  - UPSCFDC: [http://upscfdc.up.gov.in/](http://upscfdc.up.gov.in/)
- **Document**: *Audited Annual Financial Statements & Investor Presentations (Form A & Form B under Section 29 of Banking Regulation Act 1949)*
- **Publication Date**: May–July 2024 / May–July 2025
- **Reporting Period**: Full Financial Year (FY24 / FY25)
- **Metrics**: Net NPA, Gross NPA, Capital Adequacy, Statutory Reserves, State Guarantee Backing.
- **Scope**: `INSTITUTION_LEVEL`
- **Partner-Level?**: No (Branch balance sheets do not exist under statutory accounting).
- **Institution-Level?**: **Yes (Authoritative Audited Legal Entity Metric)**.
- **Sector-Level?**: No.
- **Policy-Level?**: No.
- **Routing Usable?**: **Yes (Supplements RBI/NABARD datasets)**.
- **Limitations**: Relies on annual disclosure timeline. Must be labeled `SOURCE_AUTHORITY: BANK_OFFICIAL` or `NABARD` as appropriate.

---

## 3. Summary of Public Availability for SIH26092 Metrics

| Metric | Public Availability Status | Legal Entity Grounding | Handling in YojnaSetu |
| :--- | :--- | :--- | :--- |
| **Gross NPA Ratio (%)** | **Available** (Annual/Audited) | Legal Institution (Bank / RRB) | Exposed with date, source, and `INSTITUTION_LEVEL` scope |
| **Net NPA Ratio (%)** | **Available** (Annual/Audited) | Legal Institution (Bank / RRB) | Evaluated against NSFDC RRB rule (<15%); PSB marked `OFFICIAL_FINANCIAL_INDICATOR` |
| **Profitability Track Record** | **Available** (DFS / NABARD) | Legal Institution (RRB) | Evaluated against 3-of-6 year net operating profit rule |
| **Statutory Guarantee** | **Available** (State Statutes) | State Channelizing Agency | Verified from state enabling statutes & budget allocation acts |
| **Cumulative Fund Utilization (%)** | **NOT Publicly Available** | Implementing Agency / Branch | Marked `NOT_PUBLICLY_VERIFIED` (`ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION`) |
| **NSFDC Overdue Debt Ledger** | **NOT Publicly Available** | Implementing Agency / Branch | Marked `NOT_PUBLICLY_VERIFIED` (`ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION`) |

---

## 4. Legal Defensibility Statement

> "Where official statutory financial evidence exists, YojnaSetu incorporates it with verified provenance, authoritative source URL, publication date, reporting period, and institution-level scope. Where partner-level administrative ledgers (such as live utilization certificates and overdue repayment schedules) are restricted internal filings of the Ministry, YojnaSetu explicitly discloses the limitation rather than fabricating synthetic metrics or pretending that unverified partners are 100% healthy."
