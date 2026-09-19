# Government Source Discovery Report — SIH26092

This report audits official government, regulatory, and institutional publications discovered for YojnaSetu Channel Partner Financial Intelligence, Prudential Rules, and Geospatial Routing.

---

## Source 1: NSFDC Allocation Guidelines & Prudential Norms for Disbursement
- **Source**: National Scheduled Castes Finance and Development Corporation (NSFDC)
- **URL**: `https://nsfdc.nic.in/allocation-of-funds`
- **Authority**: NSFDC, Ministry of Social Justice and Empowerment, Government of India (CPSE)
- **Data Type**: Official Policy Guidelines & Statutory Prudential Norms
- **Partner-Level?**: NO (Sets universal policy thresholds across institution types)
- **Institution-Level?**: NO (Applicable norm definition, not individual agency audit sheets)
- **Sector-Level?**: YES (Applies across all SCAs, RRBs, Public Sector Banks, and NBFC-MFIs)
- **Available Metrics**: 
  - Overdue status requirement: "There should not be any overdues payable to NSFDC"
  - Cumulative Fund Utilization requirement: "100% cumulative utilization level of earlier disbursements as at the end of preceding month"
  - Guarantee requirement: "Availability of adequate Government Guarantee/Bank Guarantee"
  - Regional Rural Banks Net NPA limit: "Net NPA must be less than 15% in at least 3 years out of last 6 years preceding the year of disbursement"
  - Regional Rural Banks Profitability: "Must have earned a net profit in at least 3 out of last 6 financial years preceding the year of disbursement"
- **Reporting Period**: Operational Policy (Active, retrieved September 2026; site updated 15.09.2026)
- **Identifier**: Section 3 & 3.1 "Norms for Disbursement"
- **Routing Usable?**: **YES for Prudential Rule Specification; NO for Individual Partner Status**
- **Reason**: The document defines the statutory criteria under which NSFDC releases funds to channel partners. It is the legal and policy bedrock for routing constraints. However, it does not publish partner-specific balance sheets.

---

## Source 2: NSFDC Lending Policy for NBFC-MFIs & Cooperative Societies
- **Source**: National Scheduled Castes Finance and Development Corporation (NSFDC)
- **URL**: `https://nsfdc.nic.in/storage/channel-partners/attachments/lending_policy_mfi.pdf` (and `/eligibility-requirements`)
- **Authority**: NSFDC, Ministry of Social Justice and Empowerment, Government of India
- **Data Type**: Credit Delivery & Channelizing Agency Eligibility Norms
- **Partner-Level?**: NO (Universal institutional qualification criteria)
- **Institution-Level?**: NO
- **Sector-Level?**: YES (NBFC-MFI and Co-operative sectors)
- **Available Metrics**:
  - NBFC-MFI Gross NPA: < 2.0% as per Annual Accounts of preceding financial year
  - NBFC-MFI Net NPA: < 0.5% as per Annual Accounts of preceding financial year
  - Co-operative Bank Net NPA: < 5.0% preceding FY or 5-year average < 5% with at least 3 years < 5%
  - Co-operative Bank Profitability: 3-year continuous profit or profit in 3 of last 5 years
  - Default history: Zero default on borrowings in the preceding 3 years
- **Reporting Period**: Active Lending Policy
- **Identifier**: NSFDC-LP-MFI-01 / NSFDC-LP-COOP-01
- **Routing Usable?**: **YES for Prudential Rule Definition**
- **Reason**: Mandates the asset-quality ceilings for non-bank financial intermediaries and cooperatives channelizing central government funds.

---

## Source 3: NSFDC Management Information System (MIS) / Public Web Portal
- **Source**: NSFDC Portal & Channel Partners Registry
- **URL**: `https://nsfdc.nic.in/our-channel-partners` and `https://nsfdc.nic.in/performance-data`
- **Authority**: NSFDC, Ministry of Social Justice and Empowerment
- **Data Type**: Channel Partner Directory & Aggregate Performance Statistics
- **Partner-Level?**: PARTIALLY (Publishes partner contact directories, nodal officer details, and registered addresses)
- **Institution-Level?**: YES for physical presence and channel status
- **Sector-Level?**: YES for aggregate quarterly/annual disbursement totals
- **Available Metrics**: Partner directory, state/district presence, nodal officers. **Partner-specific live fund utilization certificates and partner-specific overdue ledgers are NOT published on open public web endpoints** (they reside on restricted intranet MIS).
- **Reporting Period**: Updated periodically (Last verified: Sep 2026)
- **Identifier**: Channel Partner Registry Directory
- **Routing Usable?**: **YES for Partner Authorization and Spatial Presence; NO for Partner Overdues / Live Utilization**
- **Reason**: Transparency requires declaring missing live data as `NOT_PUBLICLY_VERIFIED` rather than simulating false figures.

---

## Source 4: Reserve Bank of India (RBI) — Statistical Tables Relating to Banks in India
- **Source**: Reserve Bank of India (RBI) Database on Indian Economy (DBIE)
- **URL**: `https://dbie.rbi.org.in/` / `https://www.rbi.org.in/`
- **Authority**: Reserve Bank of India (Banking Regulator of India)
- **Data Type**: Bank-Level Audited Financial Statements & Regulatory Asset Quality Indicators
- **Partner-Level?**: YES (for Scheduled Commercial Banks and Public Sector Banks)
- **Institution-Level?**: YES (Bank-wise accounting tables)
- **Sector-Level?**: Also aggregated by Bank Group (PSBs, Private Banks, Foreign Banks)
- **Available Metrics**:
  - Gross Non-Performing Assets (GNPA) Amount & Percentage
  - Net Non-Performing Assets (NNPA) Amount & Percentage
  - Capital to Risk-Weighted Assets Ratio (CRAR)
  - Return on Assets (RoA)
  - Net Profit / Loss for the Financial Year
- **Reporting Period**: FY 2022-23, FY 2023-24, FY 2024-25
- **Identifier**: RBI Table B6 (Movement of NPAs) & Table B7 (Gross and Net NPA Ratios by Bank)
- **Routing Usable?**: **YES (Authoritative Evidence for Bank Asset Quality)**
- **Reason**: Provides verified, legally audited regulatory disclosures for major channel partner banks (e.g., Bank of Baroda, Punjab National Bank, Central Bank of India, State Bank of India, Canara Bank, Union Bank of India).

---

## Source 5: NABARD / Department of Financial Services (DFS) — Review of Performance of RRBs
- **Source**: National Bank for Agriculture and Rural Development (NABARD) & Department of Financial Services, Ministry of Finance
- **URL**: `https://financialservices.gov.in/` / `https://www.nabard.org/`
- **Authority**: Ministry of Finance & NABARD (Apex Rural Banking Regulatory Body)
- **Data Type**: Institutional Statistics & Consolidated Reviews of Regional Rural Banks
- **Partner-Level?**: YES (Individual bank-wise data for all 43 Regional Rural Banks)
- **Institution-Level?**: YES (e.g., Baroda U.P. Bank, Aryavart Bank, Prathama UP Gramin Bank)
- **Sector-Level?**: Consolidated RRB Sector overview
- **Available Metrics**:
  - Gross NPA % (e.g., Baroda UP Bank: 5.75% in FY24, down from 7.53% in FY23)
  - Net NPA % (Baroda UP Bank: ~2.4% in FY24, safely below 15% threshold)
  - Net Profit / Loss (e.g., Baroda UP Bank: Profitable in FY22, FY23, and FY24; Net Profit ₹381 Cr in FY24)
  - Total Business & Branch Network
- **Reporting Period**: Annual Reviews (FY 2022-23, FY 2023-24, FY 2024-25)
- **Identifier**: DFS Consolidated Review of Regional Rural Banks / RRB Darpan
- **Routing Usable?**: **YES (Authoritative Evidence for Regional Rural Bank Norm Evaluation)**
- **Reason**: Governs the exact 15% Net NPA and 3-of-6-year profitability criteria mandated by NSFDC for RRBs.

---

## Source 6: Department of Financial Services (DFS) — RRB Amalgamation Gazettes
- **Source**: Ministry of Finance, Government of India
- **URL**: `https://financialservices.gov.in/`
- **Authority**: Central Government / Ministry of Finance
- **Data Type**: Statutory Amalgamation & Institutional Reorganization Notifications
- **Partner-Level?**: YES (Affects specific Regional Rural Banks)
- **Institution-Level?**: YES
- **Sector-Level?**: NO
- **Available Metrics**: Entity lineage, pre-merger constituent names, sponsor banks, headquarters, and effective amalgamation dates (e.g. Baroda UP Bank + Prathama UP Gramin Bank + Aryavart Bank -> Uttar Pradesh Gramin Bank).
- **Reporting Period**: Gazetted May 2025 / FY 2025-26
- **Identifier**: DFS Gazette Notification on RRB Amalgamation (Phase IV)
- **Routing Usable?**: **YES for Entity Resolution and Name Alias Resolution**
- **Reason**: Prevents duplicate partners, resolves historical vs. current legal names, and correctly maps financial records across pre- and post-merger entities.

---

## Source 7: SIDBI — Microfinance Pulse
- **Source**: Small Industries Development Bank of India (SIDBI) & Equifax India
- **URL**: `https://www.sidbi.in/`
- **Authority**: SIDBI (Statutory Financial Institution)
- **Data Type**: Quarterly Sectoral Delinquency & Portfolio Intelligence
- **Partner-Level?**: **NO** (Strictly sector and lender-category aggregations)
- **Institution-Level?**: NO
- **Sector-Level?**: **YES** (NBFC-MFI sector, Banks, SFBs, Non-profit MFIs)
- **Available Metrics**: 30+ DPD, 90+ DPD, 180+ DPD, geographic portfolio risk concentration by State/District.
- **Reporting Period**: Quarterly (Q1/Q2/Q3/Q4)
- **Identifier**: SIDBI-Equifax Microfinance Pulse Vol. XVIII-XXII
- **Routing Usable?**: **NO for partner routing exclusion; YES for Contextual Market Intelligence**
- **Reason**: Enforces Anti-Fabrication Rule: Sector delinquency trends must never be attributed to an individual partner or used to disqualify an individual agency.

---

## Source 8: Audited Annual Accounts & Statutory Disclosures of Channel Partners
- **Source**: Official web portals of individual partner banks / corporations
- **URL**: Official institution domains (e.g. `https://www.bankofbaroda.in`, `https://www.pnbindia.in`, `https://www.barodaupbank.in`)
- **Authority**: Licensed Scheduled Commercial Banks / Statutory State Corporations
- **Data Type**: Audited Annual Financial Statements & Pillar 3 Disclosures
- **Partner-Level?**: YES
- **Institution-Level?**: YES
- **Sector-Level?**: NO
- **Available Metrics**: Audited Gross NPA, Net NPA, Provisions, Net Profit, Capital Adequacy.
- **Reporting Period**: Annual / Quarterly audited releases
- **Identifier**: Audited Financial Statement / Annual Report FY2023-24 & FY2024-25
- **Routing Usable?**: **YES (Corroborating Official Evidence with Provenance)**
- **Reason**: Provides primary audited evidence with explicit publication timestamps and balance sheet provenance.

---

## Summary of Data Feasibility & Transparency Limits
1. **Publicly Verified Metrics**:
   - Bank-level Gross NPA and Net NPA: **VERIFIED** (RBI DBIE + Bank Disclosures)
   - RRB-level Gross NPA, Net NPA, and Profitability: **VERIFIED** (NABARD + DFS + RRB Audited Accounts)
   - State Government Guarantees for SCAs: **VERIFIED** (State budgetary allocations and enabling statutes)
2. **Non-Public / Restricted Metrics**:
   - Partner-level exact cumulative utilization certificate percentages of NSFDC disbursements: **NOT PUBLICLY VERIFIED** (Handled via internal ministry MIS)
   - Partner-level exact overdue amount payable to NSFDC: **NOT PUBLICLY VERIFIED** (Internal ministry ledgers)
3. **Transparent System Treatment**:
   Partners meeting all verified public requirements are routed with the transparent status:
   `ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION`
   clearly explaining that live utilization certificates and overdue ledgers are managed internally and not available on open public datasets.
