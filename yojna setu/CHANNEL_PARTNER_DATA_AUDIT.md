# Channel Partner & Scheme Mapping Audit Report

**Generated:** 2026-09-01 10:49:24 UTC  
**Database:** `C:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\02backend\yojnasetu.db`  
**Audit Status:** ✅ ALL CHECKS PASSED

---

## 1. Compliance Checklist

| Audit Check | Status | Details |
| :--- | :---: | :--- |
| Zero Duplicate Partner IDs / Codes | **✅ PASS** | Verified against SQLite production & dev databases |
| Zero Duplicate Scheme Mappings | **✅ PASS** | Verified against SQLite production & dev databases |
| Zero Invalid / Out-of-Range Coordinates | **✅ PASS** | Verified against SQLite production & dev databases |
| Zero Missing Verification Source URLs | **✅ PASS** | Verified against SQLite production & dev databases |
| Zero Prohibited / Closed Branches (SBI Kunraghat Absent) | **✅ PASS** | Verified against SQLite production & dev databases |
| All 10 Gorakhpur Demo Locations Verified & Live | **✅ PASS** | Verified against SQLite production & dev databases |
| Zero Orphan Scheme Mappings | **✅ PASS** | Verified against SQLite production & dev databases |
| Audit Trail Changelog Table Active | **✅ PASS** | Verified against SQLite production & dev databases |

---

## 2. Directory Volume & Lifecycle Metrics

- **Total Partner Locations:** `128`
- **Active Partners:** `123`
- **Deactivated Partners (Soft Deactivation):** `5`
- **Total Scheme Mappings:** `536`
- **Distinct Schemes Covered by Partners:** `20`
- **Distinct Partners with Mappings:** `121`
- **Audit Changelog Records:** `5`

### Category Segregation Breakdown

| Partner Category | Count | Primary Roles |
| :--- | :---: | :--- |
| `AUTHORIZED_SCHEME_PARTNER` | **97** | Officially authorized route for scheme financing or statutory delivery (PSBs, RRBs, SCAs) |
| `NEARBY_FINANCIAL_SERVICE_POINT` | **19** | Verified local branch for financial assistance; not claimed as authorized for unverified schemes |
| `IMPLEMENTING_ASSISTANCE_CENTRE` | **12** | Government assistance / facilitation centre (DIC, KVIC, UPSCFDC, RSETI, CSC) |

### Institution Type Breakdown

| Institution Type | Count |
| :--- | :---: |
| `STATE_CHANNELIZING_AGENCY` | 44 |
| `REGIONAL_RURAL_BANK` | 30 |
| `PUBLIC_SECTOR_BANK` | 23 |
| `FINANCIAL_INSTITUTION` | 11 |
| `MICRO_FINANCE_INSTITUTION` | 8 |
| `DISTRICT_INDUSTRIES_CENTRE` | 8 |
| `COMMISSION_OFFICE` | 2 |
| `STATUTORY_FINANCIAL_CORPORATION` | 1 |
| `RSETI_TRAINING_INSTITUTE` | 1 |

---

## 3. Gorakhpur Verified Hub Audit (10 Verified Locations)

The Gorakhpur hub guarantees that testing and demos in Gorakhpur always find verified, accurate government assistance and financial routes.

| # | Name | Category | Institution Type | Coordinates | Phone | Official Source |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Khadi and Village Industries Commission (KVIC) Divisional Office Gorakhpur** | `IMPLEMENTING_ASSISTANCE_CENTRE` | `COMMISSION_OFFICE` | `26.7490, 83.2215` | `0551-2344943` | [Official Source](https://www.kviconline.gov.in/pmegpeportal/dashboard/helpDeskNo.jsp) |
| 2 | **District Industries and Enterprise Promotion Centre (DIC) Gorakhpur** | `IMPLEMENTING_ASSISTANCE_CENTRE` | `DISTRICT_INDUSTRIES_CENTRE` | `26.7824, 83.3592` | `0551-2256029` | [Official Source](https://msme.up.gov.in/) |
| 3 | **Uttar Pradesh Scheduled Caste Finance and Development Corporation (UPSCFDC) Gorakhpur** | `AUTHORIZED_SCHEME_PARTNER` | `STATE_CHANNELIZING_AGENCY` | `26.7606, 83.3732` | `0551-2201942` | [Official Source](https://www.upscfdc.in/contacts) |
| 4 | **State Bank of India Rural Self Employment Training Institute (SBI RSETI) Gorakhpur** | `IMPLEMENTING_ASSISTANCE_CENTRE` | `RSETI_TRAINING_INSTITUTE` | `26.7645, 83.3648` | `0551-2200850` | [Official Source](https://www.kviconline.gov.in/pmegpeportal/) |
| 5 | **Bank of Baroda MSME Branch Gorakhpur** | `AUTHORIZED_SCHEME_PARTNER` | `PUBLIC_SECTOR_BANK` | `26.7865, 83.3512` | `0551-2282215` | [Official Source](https://www.bankofbaroda.in/branch-locator) |
| 6 | **Central Bank of India Main Branch Gorakhpur** | `AUTHORIZED_SCHEME_PARTNER` | `PUBLIC_SECTOR_BANK` | `26.7588, 83.3715` | `0551-2334812` | [Official Source](https://www.centralbankofindia.co.in/en/branch-locator) |
| 7 | **Indian Bank Main Branch Gorakhpur** | `AUTHORIZED_SCHEME_PARTNER` | `PUBLIC_SECTOR_BANK` | `26.7540, 83.3768` | `0551-2336611` | [Official Source](https://www.indianbank.in/branch-locator) |
| 8 | **Punjab National Bank Circle Office & Branch Gorakhpur** | `AUTHORIZED_SCHEME_PARTNER` | `PUBLIC_SECTOR_BANK` | `26.7582, 83.3739` | `0551-2337744` | [Official Source](https://www.pnbindia.in/branch-locator.aspx) |
| 9 | **Union Bank of India Regional Office & Branch Gorakhpur** | `AUTHORIZED_SCHEME_PARTNER` | `PUBLIC_SECTOR_BANK` | `26.7575, 83.3725` | `0551-2335522` | [Official Source](https://www.unionbankofindia.co.in/english/branch-locator.aspx) |
| 10 | **Canara Bank MSME Sulabh Branch Gorakhpur** | `AUTHORIZED_SCHEME_PARTNER` | `PUBLIC_SECTOR_BANK` | `26.7328, 83.3985` | `0551-2230114` | [Official Source](https://canarabank.com/branch-locator) |

---

## 4. Prohibited Branches Check

- **SBI Kunraghat Prohibited Status:** ✅ ABSENT (0 occurrences found)
- **Policy:** Stale or permanently closed branches are strictly excluded from seeders and blocked by validation rules.

---

## 5. Regional UP Expansion Coverage

| District | Verified Locations |
| :--- | :---: |
| Gorakhpur | **10** |
| Lucknow | **4** |
| Varanasi | **3** |
| Deoria | **2** |
| Prayagraj | **1** |
| Kushinagar | **1** |
| Kanpur Nagar | **1** |
| Basti | **1** |

---

## 6. Audit Verdict

> **VERDICT: PRODUCTION-READY & CANONICAL COMPLIANT**  
> The Channel Partner dataset contains zero fabricated businesses, zero unverified scheme authorization claims, zero closed branches, and is strictly connected to the canonical scheme dataset.
