# TASK REPORT: Live Chatbot Behaviour & Architectural Bug Fixes

**Project**: YojnaSetu (SIH Problem Statement 26092)  
**Date**: August 31, 2026  
**Status**: COMPLETE  

---

## 1. Executive Summary & Root Cause Analysis

Following a fresh live browser test audit of the AI Assistant, 5 major behavioural & architectural defects were identified and resolved:

| # | Bug Observed in Live Browser Test | Identified Root Cause | Fix Implemented |
|---|-----------------------------------|-----------------------|-----------------|
| 1 | Query `"talk in hindi"` performed scheme RAG & dumped PMEGP details. | `scheme_id` defaulted to `"SIH26092-001"` in `agent.py`; intent router missed regex for language change phrases like `"talk in hindi"`. | Updated `copilot_router.py` with expanded `LANGUAGE_CHANGE_TERMS` & regex `r"\b(?:talk\|speak)\s+in\s+[a-z]+\b"`. Enforced `0 RAG, 0 citations, 0 cards` on `LANGUAGE_CHANGE`. |
| 2 | Exposed raw internal metadata (`RULE-0002`, `Field: activity_type IN TRADITIONAL_TRADE_18`). | Absence of a centralized output sanitizer immediately before sending payload to UI. | Built a global output sanitizer `sanitize_user_facing_text(text: str)` in `agent.py` applied to answers, citations, card titles/subtitles, and action labels. |
| 3 | Query `"documents kya kya lagenge"` defaulted to NSFDC Micro Finance Scheme (MFS). | Hardcoded default `target_sid = scheme_id or "SIH26092-052"` in `agent.py` when `active_scheme_id` was `None`. | Removed hardcoded default scheme IDs. When `active_scheme_id` is `None`, bot now returns a clean clarification asking which scheme's document checklist the user wants to see. |
| 4 | Query `"bhai mujhe ek naya kaam shuru krna h"` returned static prompts instead of natural onboarding. | Missing intent pattern in `copilot_router.py` for Roman Hindi onboarding phrases (`"bhai mujhe ek naya kaam..."`). | Added regex patterns for Roman Hindi business onboarding phrases to classify as `BUSINESS_PROFILE_INIT` and start 1-2 question profiling (State -> Category -> Income -> Activity). |
| 5 | Query `"tum gadhe ho"` / `"u r fool"` returned generic scheme guidance with scheme cards. | Missing regex pattern in `copilot_router.py` for Roman Hindi casual insults. | Added regex patterns for `gadhe`, `ullu`, `pagal`, `fool`. Enforced `CASUAL_CONVERSATION` intent with friendly short responses and **0 citations**. |

---

## 2. Key Architecture & Code Modifications

### A. Intent Router Gating (`02backend/app/ai/copilot_router.py`)
- Added pattern matching for:
  - Language Change: `"talk in hindi"`, `"talk in english"`, `"talk in bengali"`, `"talk in tamil"`, `"talk in telugu"`, `"talk in marathi"`, etc.
  - Conversational Discovery: `"bhai mujhe ek naya kaam shuru krna h"`, `"dukan kholni h"`, `"apna business krna h"`.
  - Casual Insults: `"tum gadhe ho"`, `"u r fool"`, `"gadha"`, `"ullu"`.

### B. Active Scheme Context Resolution (`02backend/app/ai/agent.py`)
- Removed all hardcoded default scheme fallback IDs (`SIH26092-052` / `SIH26092-001`).
- Implemented explicit scheme context resolution:
  1. `req.scheme_id`
  2. `page_context.get("scheme_id")`
  3. Explicit scheme name mentioned in message (`PMEGP`, `MUDRA`, `Vishwakarma`, `Stand-Up`, `NSFDC`)
  4. Active session memory `memory.get("active_scheme_id")`
- Automatically cleared `memory["active_scheme_id"]` when user initiates new scheme discovery or profile onboarding.

### C. Output Sanitization Layer (`02backend/app/ai/agent.py`)
- Implemented `sanitize_user_facing_text(text: str)`:
  - Strips internal rule codes (`RULE-0001`, `RULE-0002`, `rule_123`).
  - Removes SQL / database operator leaks (`Field: activity_type IN TRADITIONAL_TRADE_18`).
  - Replaces internal enums with natural human phrases (`TRADITIONAL_TRADE_18` -> `Traditional Artisanship & Trade`).
  - Applied to `final_answer`, `citations` (snippets & source documents), `rich_cards`, and `actions`.

---

## 3. Automated Test Suite Results

All automated backend regression tests were updated and verified:

```bash
python -m pytest -v tests/test_ai_gemini_rag.py
```

### Test Results:
1. `test_gemini_provider_init_and_generate_mock`: **PASSED**
2. `test_get_ai_provider_factory`: **PASSED**
3. `test_casual_chat_bypass_zero_rag_citations`: **PASSED**
4. `test_deterministic_tool_priority_over_llm`: **PASSED**
5. `test_grounded_rag_with_gemini_mocked`: **PASSED**
6. `test_unsupported_factual_question_grounding_fallback`: **PASSED**
7. `test_api_security_no_key_leakage`: **PASSED**
8. `test_multilingual_generation`: **PASSED**
9. `test_language_change_zero_rag_citations`: **PASSED**
10. `test_casual_insults_handling`: **PASSED**
11. `test_internal_metadata_sanitization`: **PASSED**
12. `test_generic_document_query_asking_clarification`: **PASSED**
13. `test_conversational_discovery_onboarding`: **PASSED**

---

## 4. Full Build Verification

- **Backend Pytest**: All 378 unit & integration tests **PASSED**.
- **Frontend Production Build**: `npm run build` compiled cleanly (0 errors, 1851 modules transformed).
