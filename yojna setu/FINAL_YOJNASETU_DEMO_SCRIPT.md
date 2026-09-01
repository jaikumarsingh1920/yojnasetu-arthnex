# YojnaSetu (योजनासेतु) — SIH 2026 Live Demo Script
**3 to 5-Minute Live Demonstration Flow for Grand Finale Jury**

---

## Demo Overview & Persona
- **Presenter**: Lead Developer / Product Presenter
- **Target Persona**: **Priya Sharma**, a 26-year-old SC female entrepreneur from Kanpur, Uttar Pradesh, running a small handloom & textile workshop, seeking a ₹2 Lakh concessional loan and subsidy support.
- **Total Duration**: 4 Minutes 30 Seconds

---

## Step-by-Step Demo Flow

### **Minute 0:00 – 0:30 | Introduction & Instant 12-Language Localization**
- **Action**: Open YojnaSetu Homepage (`http://localhost:3000` or public ngrok URL).
- **Spoken Script**:
  > *"Respected Jury members, over 85% of India's micro-entrepreneurs belong to marginalized communities and operate in regional languages. When they search for government welfare schemes, they encounter fragmented portals and bureaucratic jargon. Welcome to YojnaSetu — our AI-assisted, explainable scheme matching platform. Notice as I switch our language selector from English to Hindi, Bengali, Tamil, or Marathi — the entire interface, including financial calculators, badges, and navigation, seamlessly transforms with 100% key parity across all 12 scheduled Indian languages."*
- **Visual**: Switch language to **Hindi (हिन्दी)** and back to **English** to demonstrate live dynamic re-rendering.

---

### **Minute 0:30 – 1:15 | Smart Citizen Profile & Natural Language Input**
- **Action**: Click on **"Smart Matching"** / **"Find Schemes"**.
- **Spoken Script**:
  > *"Citizens don't need to struggle through complex bureaucratic criteria. In YojnaSetu, an entrepreneur can simply describe their background or use our quick profile form. Let's input Priya's profile: Age 26, Social Category: Scheduled Caste (SC), Gender: Female, State: Uttar Pradesh, Business: Handloom / Textile, Seeking: ₹2 Lakh loan."*
- **Visual**: Click **"Evaluate Matching Schemes"**. The system instantly runs deterministic rule checks across our 126 backend rules.

---

### **Minute 1:15 – 2:00 | Explainable Results & Criteria Match Breakdown**
- **Action**: Highlight the top recommended schemes (e.g. *NSFDC Term Loan Scheme / PMEGP / Mahila Samriddhi Yojana*). Click **"View Criteria Breakdown"**.
- **Spoken Script**:
  > *"Unlike black-box recommendation engines that hallucinate, YojnaSetu is 100% explainable. Look at this Score Breakdown: it shows exactly WHY Priya qualified — her age (26) matches the 18–45 criteria (+25 pts), her SC category satisfies the target beneficiary rule (+30 pts), and her loan requirement fits within the scheme limits (+25 pts). If she didn't qualify, our 'Why I Don't Qualify' tab explains the exact disqualification reason with zero ambiguity."*
- **Visual**: Show the positive breakdown badges and the transparent dimensional points.

---

### **Minute 2:00 – 2:45 | Scheme Deep-Dive, Provenance & Scheme-Aware Financial Calculator**
- **Action**: Open the Scheme Detail page for *NSFDC Mahila Samriddhi Yojana / PMEGP*.
- **Spoken Script**:
  > *"Every single scheme card in YojnaSetu is backed by verified official provenance, citing the gazette notification, nodal ministry, and last verified date. When we scroll to our Scheme-Aware Financial Calculator, notice how it automatically binds to the scheme's verified interest rate — in this case, a 4% concessional rate for women entrepreneurs. If this were a non-credit grant scheme, our engine semantically marks it as 'Not Applicable' rather than showing deceptive ₹0 loan sliders."*
- **Visual**: Slide the loan slider to ₹2,00,000 to show real-time monthly EMI, subsidy calculation, and repayment schedule.

---

### **Minute 2:45 – 3:30 | Required Document Readiness & Geocoded Channel Partner Map**
- **Action**: Scroll to the **"Required Documents Checklist"**, then navigate to the **"Channel Partner Map"**.
- **Spoken Script**:
  > *"One of the primary causes of welfare rejection is missing documents. YojnaSetu provides an actionable checklist with issuing authorities and acceptable formats. But where does Priya go to apply? She doesn't have to visit middlemen. Our Geospatial Partner Locator pinpoints the nearest authorized NSFDC Channelizing Agency in her district, displaying exact branch coordinates, contact info, and step-by-step driving directions."*
- **Visual**: Click on the partner pin on the interactive Leaflet map to show distance, address, and directions.

---

### **Minute 3:30 – 4:00 | RAG-Grounded AI Copilot & Official Portal Routing**
- **Action**: Click the floating **"YojnaSetu AI"** Copilot button and type/speak: *"What is the subsidy percentage under PMEGP for SC women?"*
- **Spoken Script**:
  > *"For conversational queries, our database-grounded AI Copilot provides immediate, verified answers with source citations. Notice that the AI answers strictly using our database facts and includes official links. When Priya is ready to apply, she clicks 'Apply on Official Portal', which guides her directly to the official government gateway."*
- **Visual**: Show the AI reply with verified badge and source citations; trigger the official portal exit modal.

---

### **Minute 4:00 – 4:30 | Conclusion & Impact Summary**
- **Spoken Script**:
  > *"To summarize: YojnaSetu does not replace government sanctioning authorities or store private identity documents. Instead, it provides a transparent, multilingual, and explainable bridge that guides marginalized entrepreneurs from confusion to complete application readiness. Thank you, and we look forward to your questions!"*

---

## Presenter Quick Reference Card

| Stage | Key Message | Visual To Show |
| :--- | :--- | :--- |
| **0:00 Language** | 12 Languages with 100% key parity | Navbar language switcher in Hindi/Tamil |
| **0:45 Profile** | Rapid self-declaration without friction | Profile input form with SC / Woman filters |
| **1:30 Explainability** | Transparent criteria match breakdown | Points breakdown (+25 age, +30 category) |
| **2:15 Financials** | Scheme-aware calculations & subsidies | EMI slider bound to 4% interest rate |
| **3:00 Partner Map** | 105 authorized NSFDC branches mapped | Interactive Leaflet map with distance |
| **3:45 AI Copilot** | Zero hallucination, strict DB grounding | Chat message with official citation |
