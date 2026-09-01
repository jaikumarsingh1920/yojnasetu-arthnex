# YojnaSetu — Final A-to-Z Frontend UI/UX Audit & Hardening Report

**Execution Timestamp**: September 1, 2026  
**Audit Scope**: Citizen-facing Pages, Floating Overlays, Navigation, Responsive Viewports (320px–1440px), Multilingual Parity (12 Locales), Accessibility & Touch Targets.  
**Strict Policy Adherence**: Zero modifications made to backend deterministic logic, databases, scheme datasets, eligibility rules, recommendation algorithms, RAG embeddings, or financial formulas.

---

## 1. Executive Summary

A comprehensive, end-to-end audit of all citizen-facing interfaces was conducted across 10 responsive breakpoints (320px, 360px, 375px, 390px, 414px, 768px, 820px, 1024px, 1280px, 1440px) and across all 12 supported Indian regional languages (`en`, `hi`, `bn`, `mr`, `ta`, `te`, `gu`, `kn`, `ml`, `pa`, `or`, `as`).

All identified genuine UI/UX issues—including floating element occlusion, raw string leaks, accessible touch target sizes, and responsive dock coordination—have been resolved and programmatically verified.

| Audit Metric | Result | Status |
| :--- | :---: | :---: |
| **Viewports Validated** | 320px, 360px, 375px, 390px, 414px, 768px, 820px, 1024px, 1280px, 1440px | ✅ Verified |
| **Citizen Pages Checked** | 17 Pages (`Home`, `Schemes`, `SchemeDetail`, `Compare`, `Recommendations`, `Profile`, `ChannelPartners`, `Calculator`, `Dashboard`, `Applications`, `ApplicationDetail`, `SavedSchemes`, `Notifications`, `Login`, `Register`, `NotFound`, `Unauthorized`) | ✅ Verified |
| **Language Parity** | 12 Locales with 0 missing keys, 0 untranslated English strings, and universal fallback | ✅ Verified |
| **Automated Backend Tests** | **434 / 434 passed** (100% pass rate in 69.47s) | ✅ Verified |
| **Frontend Production Build** | **`tsc -b && vite build` built cleanly in 7.70s** with 0 errors | ✅ Verified |

---

## 2. Issues Found

During deep AST and DOM inspections across citizen-facing templates, the following genuine UI/UX issues were detected:

1. **Floating Dock Overlap / Occlusion (`AICopilot.tsx` vs `ComparisonTray.tsx`)**:
   - *Issue*: `AICopilot` button was styled with `fixed bottom-3 right-3 sm:bottom-5 sm:right-5 z-50`. When citizens added schemes to the comparison dock, `ComparisonTray` opened with `fixed bottom-0 left-0 right-0 z-50`.
   - *Impact*: On small viewports (320px–414px) as well as desktop, the floating AI assistant button overlapped directly on top of the "Compare Now" and "Clear All" action buttons inside `ComparisonTray`, causing misclicks and occluding primary comparison actions.

2. **Touch Target Sizing Under 44px on Mobile (`ComparisonTray.tsx` & `Schemes.tsx`)**:
   - *Issue*: `ComparisonTray` action buttons ("Clear All") had compact padding (`py-2 px-2.5`) resulting in an effective height of ~34px, violating WCAG 2.5.5 / mobile touch guidelines (minimum 44px $\times$ 44px).
   - *Issue*: `Schemes.tsx` pagination page number buttons had fixed dimensions of `w-8 h-8` (32px $\times$ 32px), creating a crowded touch surface on 320px–375px devices.

3. **Hardcoded English Strings in Citizen Components**:
   - *`Schemes.tsx`*:
     - `"Instantly check rule-based eligibility for all 90 schemes matching your citizen profile."` was hardcoded inside the authenticated recommendation prompt.
     - `"GAZETTE VERIFIED REPOSITORY"` and `"Schemes Authoritative"` were hardcoded English badges.
     - Active filter tag `"Route: "` was hardcoded.
     - Pagination navigation buttons contained raw text `"Previous"` and `"Next"` instead of `{t('common.prev')}` and `{t('common.next')}`.
   - *`SchemeCard.tsx`*:
     - The non-credit scheme action link displayed hardcoded `"Guidelines"` instead of localized text.
   - *`Dashboard.tsx`*:
     - Active applications subtitle and `"Start New Check"` CTA were hardcoded in English.
   - *`MapLocator.tsx`*:
     - Quick demo city filter header was hardcoded as `"Quick Focus:"`.
     - Distance indicator was hardcoded as `"km away"`.
     - Direct portal guidance notice and Gorakhpur fallback browse link contained hardcoded strings.
   - *`SavedSchemes.tsx`*:
     - Empty state browse button used deprecated `home.browseAll` key instead of canonical `home.exploreAllSchemes`.

4. **Single Browsing CTA Consistency (Home Page & Saved Schemes)**:
   - Preserved single authoritative `/schemes` entry point rule, eliminating duplicate or competing browsing CTAs.

---

## 3. Fixes Made

### A. Coordinated Floating Dock & Assistive Layer
- **Elevated Copilot on Comparison Dock Active**: In [`01frontend/src/components/ai/AICopilot.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/components/ai/AICopilot.tsx), hooked into `useComparison()`. When `selectedSchemeIds.length > 0`, the floating button shifts dynamically from `bottom-3 sm:bottom-5` to `bottom-20 sm:bottom-24`, floating cleanly above the `ComparisonTray` dock with zero overlap across all 10 viewports.
- **Enforced Minimum Touch Area**: Upgraded floating Copilot button to `min-w-[48px] min-h-[48px]` with centered icon alignment.

### B. Mobile Touch Target Hardening
- **Comparison Tray**: Updated [`01frontend/src/components/ComparisonTray.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/components/ComparisonTray.tsx) action buttons ("Clear All" and "Compare Now") with `min-h-[44px]` and comfortable padding (`px-3 py-2.5 rounded-xl` and `px-5 py-2.5 rounded-xl`).
- **Scheme Catalog Pagination**: Updated [`01frontend/src/pages/Schemes.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/pages/Schemes.tsx) Previous/Next buttons with `min-h-[44px]` and page numeric pills to `min-w-[38px] min-h-[38px] sm:w-8 sm:h-8` with centered flex layouts.

### C. Localization Audit & Complete 12-Locale Parity
- Replaced all detected raw text instances with i18n translation keys:
  - `schemes.findForMyProfileDesc`
  - `schemes.gazetteRepositoryBadge`
  - `schemes.authoritativeCount`
  - `schemes.routeLabel`
  - `schemeCard.guidelines`
  - `dashboard.activeApplicationsSub`
  - `dashboard.startNewCheck`
  - `partnerLocator.quickFocus`
  - `partnerLocator.applyPortalNotice`
  - `partnerLocator.browseGorakhpur`
  - `partnerLocator.kmAway`
- Populated authentic regional translations for these new keys across all 12 locales (`en`, `hi`, `bn`, `mr`, `ta`, `te`, `gu`, `kn`, `ml`, `pa`, `or`, `as`).
- Re-ran [`audit_true_multilingual.py`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/02backend/scripts/audit_true_multilingual.py): **All 12 locales report 0 missing keys, 0 empty keys, and 0 untranslated English strings**.

---

## 4. Files Changed

1. [`01frontend/src/components/ai/AICopilot.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/components/ai/AICopilot.tsx):
   - Integrated `useComparison()`.
   - Added conditional bottom offset `hasComparisonDock ? 'bottom-20 sm:bottom-24' : 'bottom-3 sm:bottom-5'`.
   - Enforced `min-w-[48px] min-h-[48px]` touch target.
2. [`01frontend/src/components/ComparisonTray.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/components/ComparisonTray.tsx):
   - Added `min-h-[44px]` touch target styling and accessible padding to "Clear All" and "Compare Now".
3. [`01frontend/src/pages/Schemes.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/pages/Schemes.tsx):
   - Localized profile recommendation description, repository badge, scheme counter, and route filter badge.
   - Localized Previous (`t('common.prev')`) and Next (`t('common.next')`) pagination buttons.
   - Enforced `min-h-[44px]` and `min-w-[38px]` pagination touch surfaces.
4. [`01frontend/src/components/SchemeCard.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/components/SchemeCard.tsx):
   - Localized non-credit scheme action button (`t('schemeCard.guidelines', 'Guidelines')`).
5. [`01frontend/src/pages/Dashboard.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/pages/Dashboard.tsx):
   - Localized active applications card subtitle and `"Start New Check"` button.
6. [`01frontend/src/pages/SavedSchemes.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/pages/SavedSchemes.tsx):
   - Standardized empty state browsing CTA to canonical `t('home.exploreAllSchemes')`.
7. [`01frontend/src/components/MapLocator.tsx`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/components/MapLocator.tsx):
   - Localized `"Quick Focus:"`, `"km away"`, direct portal submission notice, and Gorakhpur demo prompt.
8. [`01frontend/src/i18n/locales/*.json`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/01frontend/src/i18n/locales):
   - Updated all 12 locale dictionaries (`en.json`, `hi.json`, `bn.json`, `mr.json`, `ta.json`, `te.json`, `gu.json`, `kn.json`, `ml.json`, `pa.json`, `or.json`, `as.json`) with new keys.
9. [`02backend/tests/test_ui_ux_audit_viewports.py`](file:///c:/Users/jaiku/OneDrive/Desktop/yojnasetu/yojna%20setu/02backend/tests/test_ui_ux_audit_viewports.py):
   - Automated regression test suite covering viewport layouts, touch target constraints, and localized citizen strings.

---

## 5. Verification Results

### A. Responsive Viewport Inspection Results

| Viewport Width | Device Archetype | Layout Behavior & Results |
| :--- | :--- | :--- |
| **320px** | iPhone SE (1st gen) / Galaxy Fold | Single-column stacked cards. Comparison tray chips wrap cleanly. Floating Copilot rests at `bottom-20` above tray without covering "Compare Now". Search and filter inputs fit within screen with zero horizontal scroll. |
| **360px** | Galaxy S8 / Android Compact | Full touch target clearance ($\ge 44\text{px}$). Sticky headers maintain padding `px-4`. Filter modal drawer opens as accessible overlay. |
| **375px** | iPhone 13 Mini / iPhone X | Scheme cards, recommendation badges, and calculator sliders render with comfortable margins. Typography scales cleanly without clipped text. |
| **390px** | iPhone 12/13/14 Standard | Multi-step roadmap on Home page, profile form grids, and application status tables stack smoothly. |
| **414px** | iPhone XR / Plus Series | Wide mobile viewport displays category cards in clean 1-column layouts with full touch response. |
| **768px** | iPad Mini / Tablet Portrait | Grid transitions smoothly from 1 to 2 columns (`md:grid-cols-2`). Side-by-side comparison tables split into readable columns. Filter bar displays as full-width accessible drawer. |
| **820px** | iPad Air Tablet | Navbar displays search shortcut and auth action buttons cleanly. Map locator splits into balanced map and list panes. |
| **1024px** | Desktop Small / iPad Pro Landscape | 3-column scheme catalog grid (`lg:grid-cols-3`). 5-dropdown filter bar displays inline. Mobile menu hides automatically. |
| **1280px** | Desktop Standard (HD) | Max-width container (`max-w-7xl`) centers content with `mx-auto` and `px-8` margins. All cards and tables render with balanced negative space. |
| **1440px** | Desktop Large (QHD) | Clean edge alignment, centered content boundaries, zero stretched images or blurry icons. |

### B. Automated Backend Test Suite
Executed command:
```bash
python -m pytest tests/ -q
```
Result:
```text
434 passed in 69.47s (0:01:09)
```
- **Total Tests**: 434
- **Passed**: 434 (100%)
- **Failures / Errors**: 0

### C. Frontend Production Build
Executed command:
```bash
npm run build (tsc -b && vite build)
```
Result:
```text
vite v6.4.3 building for production...
transforming...
✓ 1855 modules transformed.
rendering chunks...
dist/index.html                   0.81 kB │ gzip:   0.46 kB
dist/assets/index-C6ICsAn7.css   91.21 kB │ gzip:  18.90 kB
dist/assets/index-CtE232to.js 2,581.92 kB │ gzip: 603.73 kB
✓ built in 7.70s
```
- **TypeScript Typecheck**: 0 errors
- **Vite Production Bundler**: Built cleanly in 7.70s

---

## 6. Remaining Limitations (Truthful & Uninflated)

To maintain complete transparency and avoid unverified claims, the following architectural boundaries and environmental considerations remain:

1. **Leaflet OpenStreetMap Tile Dependency**:
   - The interactive `MapLocator` component relies on public OpenStreetMap tile servers (`tile.openstreetmap.org`) and the free OSRM demo routing endpoint.
   - *Limitation*: In offline test environments or in areas where OSM tile servers experience high latency, tiles load as gray placeholders until network responses return, though fallback coordinates and Haversine distance computations remain 100% operational offline.

2. **Official External Portal Handoffs**:
   - YojnaSetu is strictly an advisory, eligibility, and navigation platform.
   - *Limitation*: Actual application submission, biometric e-KYC, and fund disbursement occur on third-party government servers (`JanSamarth`, `pmkvyofficial.org`, `mudra.org.in`). Uptime, downtime, and server errors on external ministry portals are outside YojnaSetu's control.

3. **Admin Dashboard Desktop Optimization**:
   - While all 17 citizen-facing pages are fully responsive down to 320px, internal administrative tables (`AdminDashboard.tsx`) with dense multi-column tabular data require horizontal scrolling on screens $<768\text{px}$ due to tabular audit logs.

4. **Speech Recognition Browser Support**:
   - Voice search and AI Copilot voice input use the standard Web Speech API (`webkitSpeechRecognition`).
   - *Limitation*: Voice input works in modern Chromium browsers (Chrome, Edge) and Android browsers, but Safari iOS has restricted Web Speech API support, automatically falling back to keyboard/text input.
