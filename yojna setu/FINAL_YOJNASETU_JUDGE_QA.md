# YojnaSetu (योजनासेतु) — Grand Finale Jury Q&A Guide
**20 Rigorous Technical, Operational & Architectural Questions with Verifiable Answers**

---

### **Q1: Why is AI required here? Why not use a standard SQL database filter?**
**Answer**:  
A standard SQL filter requires citizens to understand precise bureaucratic terms (e.g. *concessional credit lines*, *sub-component subsidy slabs*, *margin money thresholds*). AI is utilized in two specific, safe ways:
1. **Natural Language Semantic Understanding**: Translates a citizen’s informal description (*"I want to start a small tailoring shop with 2 stitching machines"*) into structured profile parameters.
2. **Contextual Conversational Q&A**: Answers citizen queries via RAG grounded strictly in verified scheme documentation.  
Crucially, **eligibility evaluation itself is not delegated to the LLM**; it is executed by our deterministic backend engine to ensure zero hallucinations.

---

### **Q2: Why not just use the government's official myScheme portal?**
**Answer**:  
myScheme is an excellent national directory, but it functions primarily as a top-down information repository. YojnaSetu addresses key structural gaps:
1. **Explainable Rationale**: myScheme provides black-box filtering; YojnaSetu provides an exact point-by-point criteria breakdown explaining *why* an applicant qualifies or fails.
2. **Scheme-Aware Financial Projections**: YojnaSetu differentiates credit vs. non-credit grants, calculating amortized EMIs and subsidy reductions.
3. **Geospatial Channel Partner Routing**: Directs marginalized citizens to physical, authorized State Channelizing Agencies (SCAs) and NSFDC partner branches on an interactive map.
4. **12-Language Deep Localization**: Full UI localization across 12 scheduled languages with 1,092 synchronized keys per locale.

---

### **Q3: How do you prevent AI hallucinations when advising citizens?**
**Answer**:  
We employ an architectural separation of concerns:
- **Zero Generative Eligibility**: Mathematical and statutory eligibility is evaluated by deterministic Python rule algorithms.
- **RAG Database Grounding**: The AI Copilot only answers based on retrieved structured scheme records from our database. If information is absent, the system explicitly returns *"Information not specified in official gazette — please confirm with concerned authority"* rather than guessing.

---

### **Q4: How is eligibility calculated?**
**Answer**:  
Eligibility is computed across 126 explicit rule constraints stored in our `scheme_rules` relational table. When a citizen profile is submitted:
1. Exact conditions (age bounds, gender requirements, caste categories, income ceilings, and business stage) are evaluated using boolean comparison operators.
2. Matched criteria award weighted dimension points (Demographic, Financial, Sectoral, Geographic).
3. If any mandatory rule fails (e.g., age > 45 on an youth scheme), the scheme is immediately categorized under *Why I Don't Qualify* with the exact failure reason.

---

### **Q5: Can the AI model decide or alter citizen eligibility?**
**Answer**:  
**No.** The AI model has zero authority to decide or alter eligibility scores. Eligibility is 100% deterministic and auditable in our Python backend engine.

---

### **Q6: Where does the scheme data come from?**
**Answer**:  
Our dataset comprises 90 central and state government schemes compiled from authoritative sources:
- Official gazette notifications and ministry operational guidelines (e.g., Ministry of MSME, Ministry of Social Justice and Empowerment, Ministry of Finance).
- Official portal schemas from `myScheme.gov.in`.
- Official credit schemes and partner directories from the National Scheduled Castes Finance and Development Corporation (NSFDC).  
Every scheme record contains an immutable `official_source_url` and `last_verified_date`.

---

### **Q7: How is data freshness and scheme guideline revisions handled?**
**Answer**:  
1. **Scheme Changelog Ledger**: The database maintains a `scheme_changelogs` table (currently 212 records) tracking every parameter modification with timestamps and source references.
2. **Admin Governance Workbench**: System administrators have dedicated tools to audit, update rules, and verify scheme active states.
3. **Citizen Transparency**: The UI explicitly displays the *Last Verified Date* and links to the live official portal.

---

### **Q8: What happens when official information is missing or discretionary?**
**Answer**:  
We use explicit semantic states instead of showing deceptive blanks, zeros, or placeholders:
- Missing interest rates are labeled as *"Determined by financing bank based on project appraisal"*.
- Non-specified state boundaries are labeled as *"Pan-India applicability (confirm with nodal agency)"*.
- Non-credit schemes display *"Not Applicable (Grant/Subsidy Support)"*.

---

### **Q9: Why is your financial calculator reliable?**
**Answer**:  
Unlike generic online calculators, our financial engine is **scheme-aware**:
- It binds directly to the specific scheme’s verified interest rate boundaries (e.g. 4% p.a. for NSFDC Mahila Samriddhi).
- It calculates front-ended vs. back-ended capital subsidies according to official guidelines before projecting loan repayment schedules.

---

### **Q10: How are non-credit schemes handled?**
**Answer**:  
54 of our 90 schemes are non-credit (training, skill development, technology transfer, or direct grants). For these schemes:
- Loan sliders are automatically disabled.
- The UI explicitly renders a *"Grant / Non-Credit Welfare Scheme"* badge.
- EMI cards are replaced with direct benefit summaries (e.g., free training stipends, equipment toolkits).

---

### **Q11: How does multilingual support work across 12 languages?**
**Answer**:  
We implemented an enterprise i18n architecture using `react-i18next`:
- 12 comprehensive JSON translation dictionaries in `01frontend/src/i18n/locales/` (`en`, `hi`, `bn`, `mr`, `te`, `ta`, `gu`, `kn`, `ml`, `pa`, `or`, `as`).
- Every language has **exact 100% key parity** with 1,092 translation keys.
- Language choice is stored in local storage and re-renders the entire application without page reloads.

---

### **Q12: How do you help citizens find the correct partner or assistance center?**
**Answer**:  
We geocoded 105 official NSFDC State Channelizing Agencies and partner branches across India. The interactive map uses the Haversine formula and OpenStreetMap/OSRM to compute real-time driving distances and provide step-by-step navigation from the citizen’s current location.

---

### **Q13: Does YojnaSetu process government applications or issue sanctions?**
**Answer**:  
**No.** YojnaSetu is strictly an intelligent discovery and readiness platform. Once a citizen prepares their checklist and evaluates eligibility, YojnaSetu routes them to the verified official portal or nearest authorized agency office for formal statutory submission.

---

### **Q14: Does YojnaSetu store sensitive citizen documents like Aadhaar or PAN cards?**
**Answer**:  
**No.** To uphold the highest privacy standards and comply with the Digital Personal Data Protection (DPDP) Act, YojnaSetu follows a **Zero Document Storage** architecture. We provide document checklists and readiness guidance; we never upload or store citizen biometric or identity documents.

---

### **Q15: How scalable is the platform architecture?**
**Answer**:  
- **Frontend**: Lightweight static bundle ($<530$ kB gzipped) deployed on global CDNs.
- **Backend**: Asynchronous, stateless FastAPI service capable of processing thousands of concurrent evaluations per second.
- **Database**: Relational indexed schema easily hosted on PostgreSQL or distributed cloud databases.

---

### **Q16: What is the most technically innovative aspect of YojnaSetu?**
**Answer**:  
The **dual-engine architecture**: combining natural language conversational accessibility with a **100% deterministic, explainable mathematical rule engine**. It delivers the intuitive ease of modern generative AI without inheriting the fatal risk of hallucinated welfare advice.

---

### **Q17: What is the biggest current limitation of the prototype?**
**Answer**:  
While all 90 schemes are thoroughly verified with provenance, state-level schemes vary across India's 28 states. Expanding to all state-specific sub-schemes requires continuous synchronization with state department gazettes.

---

### **Q18: How can government agencies (e.g. NSFDC or Ministry of MSME) adopt this?**
**Answer**:  
YojnaSetu can be integrated as a citizen-facing front-end guidance layer on top of existing ministry portals (like `myScheme` or `udyamregistration.gov.in`) via REST API plug-ins without altering existing backend verification infrastructure.

---

### **Q19: How easily can new schemes be added to the system?**
**Answer**:  
Our database schema is fully normalized. Adding a new scheme requires inserting the scheme record, defining its eligibility rules in `scheme_rules`, and linking required documents in `scheme_documents`. The engine immediately begins evaluating the new scheme with zero code changes.

---

### **Q20: What makes YojnaSetu defensible as an SIH prototype?**
**Answer**:  
1. **100% Working Codebase**: 398 automated pytest tests passing; frontend builds with 0 errors.
2. **Authentic Data Grounding**: 90 verified schemes with official URLs, 126 deterministic rules, 105 geocoded partners.
3. **Complete 12-Language Parity**: 1,092 translation keys across all 12 Indian languages.
4. **Honest Scope**: Zero unsupported claims or fake approval workflows; pure engineering excellence focused on citizen empowerment.
