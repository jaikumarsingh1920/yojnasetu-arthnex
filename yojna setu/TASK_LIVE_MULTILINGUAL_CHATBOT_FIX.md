# Technical Audit & Verification Report: Live Multilingual Chatbot Fix

## 1. Executive Summary & Root Cause Analysis

During live browser testing of the YojnaSetu AI Assistant, several critical conversational defects were identified and diagnosed through full end-to-end request tracing (from `ChatWindow.tsx` through Vite proxy `http://localhost:3000/api/v1/ai/chat` to FastAPI `http://127.0.0.1:8000/api/v1/ai/chat`):

### Root Cause 1: Missing `LANGUAGE_CHANGE` Handler in `agent.py`
- **Issue**: While `copilot_router.py` was classifying language change requests as `LANGUAGE_CHANGE`, the main conversational execution engine in `agent.py` lacked an `elif intent == "LANGUAGE_CHANGE":` branch in its routing gate.
- **Consequence**: Execution fell through all casual gates into the grounded RAG search fallback, executing `HybridSchemeRAG.hybrid_search("🗣️ Speak to me in Hindi")`. This retrieved 3 arbitrary schemes (`PM Vishwakarma`, `Mahila Coir Yojana`, `NSFDC Micro Finance Scheme`) and returned full scheme cards and citations.

### Root Cause 2: Inability & Speech Shorthand Expressions in Router
- **Issue**: Expressions like `"English samajh nahi aati"`, `"mujhe english nhi aati"`, and `"hindi me baaat kroo"` (repeated letters) did not match strict regex boundaries.
- **Consequence**: Inability expressions were incorrectly treated as general search queries.

### Root Cause 3: Internal Database Rule & SQL Expression Leakage
- **Issue**: Raw database strings in `SchemeRule` error messages contained formatting such as `Rule Code: RULE-0015 Field: application_route IN PM_SURAJ; AUTHORISED_SCA; AUTHORISED_CA Description: Direct application to NSFDC is not accepted`. The sanitizer regex stopped at the first semicolon `;`, leaving enum constants visible.
- **Consequence**: Semicolon-delimited internal identifiers leaked into user-facing response cards and citations.

---

## 2. Implemented Architecture & Defense-in-Depth

```
User Input ("🗣️ Speak to me in Hindi" / "hindi me baaat kroo" / "mujhe english nhi aati")
   │
   ▼
[1. Text Normalization & Emoji Stripping] (copilot_router.py)
   │
   ▼
[2. Priority Intent Classifier] (classify_intent)
   │
   ├──▶ intent == "LANGUAGE_CHANGE"
   │      │
   │      ▼
   │   [3. Session Memory Language Update] (memory["preferred_language"] = "hi")
   │      │
   │      ▼
   │   [4. Early Exit Gate] (0 RAG, 0 Citations, 0 Scheme Cards)
   │      │
   │      ▼
   │   [5. Localized Friendly Confirmation Response]
   │
   └──▶ intent == "FACTUAL_QUERY" / "FINANCIAL_QUERY" / "ELIGIBILITY_QUERY"
          │
          ▼
       [Deterministic Engine / RAG Search]
          │
          ▼
       [Multi-Layer Metadata Sanitizer] (agent.py, rag.py, SourceCitationCard.tsx)
          (Purges RULE-*, Field: ..., SQL operators, enum tokens)
          │
          ▼
       [Clean Grounded User Response]
```

---

## 3. Detailed File Changes

### 1. `02backend/app/ai/agent.py`
- Added explicit `elif intent == "LANGUAGE_CHANGE":` early-exit branch.
- Persisted detected target language (`hi`, `en`, `bn`, `ta`, `te`, `mr`, `gu`, `kn`, `ml`, `pa`, `or`, `as`) into session memory store.
- Enforced hard invariant: `citations = []`, `actions = []`, `rich_cards = []` for language switches.
- Deep sanitized all dictionary values inside `rich_cards[i].data`.
- Extended `sanitize_user_facing_text` regex to strip all variations of `Rule Code:`, `Field: ...`, `Requirement Field:`, `Requirement Value:`, `Verification Status:`, and replace internal enum constants (`PM_SURAJ`, `AUTHORISED_SCA`, `AUTHORISED_CA`, `TRADITIONAL_TRADE_*`, `SMALL_MICRO_BUSINESS`).

### 2. `02backend/app/ai/copilot_router.py`
- Added `is_language_change_query()` covering:
  - English commands with emojis: `"🗣️ Speak to me in Hindi"`, `"talk to me in english"`, `"please reply in hindi"`, `"speak hindi"`
  - Roman Hindi & misspellings: `"hindi me baaat kroo"`, `"hindi mein baat karo"`, `"hindi me likho"`, `"hindi me batao"`
  - Inability phrases: `"mujhe english nhi aati"`, `"mujhe english nahi aati"`, `"English samajh nahi aati"`
  - Native scripts for 12 Indian languages: Hindi (`हिंदी में बात करो`), Bengali (`বাংলায় কথা বলো`), Tamil (`தமிழில் பேசுங்கள்`), Telugu (`తెలుగులో మాట్లాడు`), Marathi (`मराठीत बोला`), Gujarati (`ગુજરાતીમાં બોલો`).

### 3. `02backend/app/ai/rag.py`
- Added index-time sanitization in `SchemeVectorStore._build_index()` to ensure raw rule metadata from `SchemeRule` table is sanitized before indexing into TF-IDF / vector chunks.

### 4. `01frontend/src/components/ai/SourceCitationCard.tsx`
- Hardened client-side `sanitizeClientSnippet` regex to strip semicolons and SQL expression strings from citations.

### 5. `02backend/tests/test_live_multilingual_chatbot.py`
- Created dedicated test suite covering language normalization, early exit, active scheme isolation, document clarification, and metadata sanitization.

---

## 4. Live Verification Matrix Results

All 12 live test cases were executed against both the Vite proxy endpoint (`http://localhost:3000/api/v1/ai/chat`) and the direct backend endpoint (`http://127.0.0.1:8000/api/v1/ai/chat`):

| Test ID | User Input | Detected Intent | RAG Called? | Citations | Cards | Verified Output Behavior |
|---|---|---|---|---|---|---|
| **TEST 1** | `hi` | `CASUAL_GREETING` | No | 0 | 0 | Friendly greeting in English |
| **TEST 2** | `whats your name` | `IDENTITY_QUERY` | No | 0 | 0 | YojnaSetu AI Citizen Assistant intro |
| **TEST 3** | `🗣️ Speak to me in Hindi` | `LANGUAGE_CHANGE` | No | 0 | 0 | **Hindi confirmation, 0 scheme cards** |
| **TEST 4** | `hindi me baat kro` | `LANGUAGE_CHANGE` | No | 0 | 0 | **Hindi confirmation, 0 scheme cards** |
| **TEST 5** | `mujhe english nhi aati` | `LANGUAGE_CHANGE` | No | 0 | 0 | **Hindi confirmation, 0 scheme cards** |
| **TEST 6** | `hindi me baaat kroo` | `LANGUAGE_CHANGE` | No | 0 | 0 | **Hindi confirmation, 0 scheme cards** |
| **TEST 7** | `mujhe business start karna hai` | `BUSINESS_PROFILE_INIT` | No | 0 | 0 | **Step-by-step profiling flow (State question)** |
| **TEST 8** | `documents kya kya lagenge` | `DOCUMENT_QUERY` | No | 0 | 0 | **Clarifies which scheme (0 random guessing)** |
| **TEST 9** | `PMEGP kya hai?` | `GENERAL_SCHEME_QUERY` | Yes | 3 | 0 | **Grounded PMEGP facts, 0 RULE-* metadata** |
| **TEST 10** | `Calculate EMI for ₹2 lakh at 7% for 5 years` | `FINANCIAL_QUERY` | No | 0 | 1 | **Deterministic financial EMI calculation card** |
| **TEST 11** | `Am I eligible for PMEGP?` | `ELIGIBILITY_QUERY` | No | 0 | 1 | **Deterministic eligibility evaluation card** |
| **TEST 12** | `english me baat karo` | `LANGUAGE_CHANGE` | No | 0 | 0 | **English confirmation, 0 scheme cards** |

---

## 5. Automated Regression & Build Verification

1. **Backend Pytest Suite**:
   ```
   ======================= 389 passed in 88.70s =======================
   ```
2. **Frontend Production Build**:
   ```
   ✓ 1851 modules transformed.
   ✓ built in 13.21s
   ```
3. **Live HTTP Matrix Test**:
   ```
   >>> ALL MATRIX TESTS PASSED ON http://localhost:3000/api/v1/ai/chat <<<
   >>> ALL MATRIX TESTS PASSED ON http://127.0.0.1:8000/api/v1/ai/chat <<<
   ```

---
*Verified and ready for live UI testing.*
