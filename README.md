# YojnaSetu — National Government Scheme Discovery & AI Guidance Platform

**YojnaSetu** is an AI-powered national government scheme discovery, eligibility verification, and financial guidance platform for Indian citizens. It connects citizens directly to verified government schemes with real-time recommendations, deterministic eligibility rules, financial calculators, multilingual support, and direct links to official government application portals.

---

## Key Features

- **Full-Stack 12-Language Support**: Dynamically supports English, Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Kannada, Malayalam, Punjabi, Odia, and Assamese.
- **Conversational AI Copilot**: Grounded RAG-based AI assistant for intent classification, zero-RAG casual conversation, and deterministic eligibility/financial tool execution.
- **Deterministic Eligibility & Financial Engine**: Verifies applicant rules against exact thresholds and calculates loan EMIs, government subsidies, and interest rates.
- **Recommend & Redirect Model**: Directs citizens to official government portals (`pmegp.msme.gov.in`, `mudra.org.in`, etc.) for official submissions.
- **Save Scheme & Email Features**: Bookmark schemes and email scheme summaries in the user's preferred language.
- **Voice Assistance**: Speech recognition and TTS supporting BCP-47 codes for all 12 Indian languages.

---

## Repository Structure

```
yojna setu/
├── 01frontend/        # React + TypeScript + Vite + TailwindCSS + i18next
├── 02backend/         # FastAPI + SQLAlchemy + SQLite + Pytest
├── 03ai/              # Hybrid RAG, Embeddings & LLM Prompting Layer
├── 04data/            # Government Scheme Datasets & Seed Migration Files
├── 05tests/           # End-to-end and API Test Suites
└── 06docs/            # System Architecture & Documentation
```

---

## Quick Start

### 1. Backend Setup

```bash
cd "yojna setu/02backend"
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd "yojna setu/01frontend"
npm install
npm run dev
```

The application will be running locally at `http://localhost:3000`.

---

## Verification & Testing

Run the full pytest backend suite:

```bash
cd "yojna setu/02backend"
python -m pytest -v
```

Build the frontend production bundle:

```bash
cd "yojna setu/01frontend"
npm run build
```
