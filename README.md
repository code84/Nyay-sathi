# Nyay Saathi

**Nyay Saathi** ("Justice Companion" in Hindi) is a legal-help web application for ordinary people in India. It answers questions about refund disputes, cheque bounce notices, and loan recovery notices in plain Hindi or English — with every legal claim backed by a cited, verifiable source.

> **Important:** Nyay Saathi provides **general legal information only**. It is not a substitute for advice from a qualified lawyer. Nothing in this application constitutes legal advice, creates a lawyer-client relationship, or should be relied upon for any specific legal situation.

---

## Table of Contents

1. [What it does](#what-it-does)
2. [Tech Stack](#tech-stack)
3. [Architecture Overview](#architecture-overview)
4. [Backend Deep Dive](#backend-deep-dive)
5. [Frontend Deep Dive](#frontend-deep-dive)
6. [AI Pipeline](#ai-pipeline)
7. [Knowledge Base (Legal Library)](#knowledge-base-legal-library)
8. [Key Design Decisions](#key-design-decisions)
9. [Project Structure](#project-structure)
10. [Running Locally](#running-locally)
11. [API Reference](#api-reference)
12. [Configuration](#configuration)

---

## What it does

- **Conversational legal help** — multi-turn chat that collects facts from the user and gives a personalised, sourced answer
- **Legal notice analysis** — paste a cheque bounce, loan recovery, or demand notice and get a plain-language explanation with deadlines and next steps
- **Document drafts** — generates demand notice and reply-to-notice drafts based on collected facts
- **PDF export** — converts any draft to a downloadable A4 PDF
- **Bilingual** — full English and Hindi support; Hinglish input handled via keyword pre-triage
- **Case history** — conversations saved locally in the browser; switch between past cases at any time
- **Dark / light mode** — user preference persisted in localStorage

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI 0.162 (Python 3.13) |
| LLM provider | Groq (default) or Google Gemini — configurable via env |
| Retrieval | BM25 keyword search (`rank-bm25`) — no vectors, no embeddings |
| PDF generation | ReportLab |
| Frontend framework | Next.js 16.4 (App Router, Turbopack) |
| UI | React 19, Tailwind CSS v4, shadcn/ui (`@base-ui/react`) |
| Language | TypeScript 5 (strict) |
| Fonts | Inter, Merriweather, Noto Sans/Serif Devanagari |

---

## Architecture Overview

```
Browser (Next.js 16)
        │
        │  POST /chat          — conversational turns
        │  POST /notice/analyze — paste a legal notice
        │  POST /draft/demand   — generate demand notice
        │  POST /draft/reply    — generate reply draft
        │  POST /export         — convert text to PDF
        │  GET  /sources/{id}   — fetch a library item
        │  GET  /playbooks      — list available playbooks
        │
        ▼
FastAPI Backend (Python 3.13, Uvicorn)
        │
        ├── Keyword Pre-Triage (pure Python regex)
        │       └─ if keywords match → route instantly, no LLM call
        │
        ├── LLM Triage (1 LLM call) ─── classifies intent + language
        │
        ├── Case Builder (1 LLM call) ── extracts facts with evidence quotes
        │       └─ 4-layer validation: quote presence + type coercion + known fact names
        │
        ├── Retriever (BM25, no AI) ──── top-5 library items by keyword relevance
        │
        ├── Grounded Answer Generator (1 LLM call)
        │       └─ system prompt: cite everything, never invent, write empathetically
        │
        ├── Honesty Checker (pure Python)
        │       └─ blocks invented section numbers, Acts, court cases
        │       └─ warns on imperfect quotes and unrecognised numbers
        │
        ├── Rules Engine (pure Python)
        │       └─ deadline arithmetic (python-dateutil), deterministic
        │       └─ forum tier selection (District / State / National)
        │       └─ red flag evaluation
        │
        ├── Notice Extractor (1 LLM call) ─ structured fields from notice text
        │       └─ every field requires a verbatim quote from the notice
        │
        └── Scam Checker (pure regex) ── UPI requests, digital arrest, OTP asks
```

The server is **completely stateless** — the full `CaseFile` travels in every request and response. No sessions are stored server-side.

---

## Backend Deep Dive

### Entry Point — `app/main.py`

- FastAPI application with CORS middleware (origins from `ALLOWED_ORIGINS` env var)
- Access log middleware — logs method, path, status, latency only. **Never logs the request body** (personal details)
- Global exception handlers:
  - `ValueError` → HTTP 502 "AI model returned an unusable reply"
  - `Exception` → HTTP 503 "temporarily unavailable"
- Health endpoint: `GET /health`

### Configuration — `core/config.py`

Frozen dataclass populated from `backend/.env`:

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini` or `groq` |
| `LLM_MODEL` | — | Model name, e.g. `gemini-2.0-flash` |
| `LLM_API_KEY` | — | Provider API key |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS whitelist |
| `ALLOW_DRAFT` | `true` | Serve DRAFT library items |
| `RATE_LIMIT_PER_MIN` | `60` | Per-IP requests per minute |

### LLM Abstraction — `core/llm.py`

Provider-agnostic interface with three implementations:

- **`GeminiLLM`** — Google `google-genai` SDK, temperature 0.2, 30-second timeout
- **`GroqLLM`** — Groq SDK, temperature 0.2, 20-second timeout, `max_tokens=4096`, `max_retries=0`
- **`FakeLLM`** — canned replies for tests

All providers implement `ask()`, `stream()`, and `ask_json()` (parse + validate JSON, one retry on failure). `LLMTimeoutError` is raised on any API failure — caught at every call site, never propagates to a 503.

### Triage — `core/triage.py`

Two-stage routing:

1. **Keyword pre-triage (no LLM)** — regex patterns for refund, cheque bounce, loan recovery keywords in English, Hindi, and Hinglish. If matched, routes instantly without an LLM call.
2. **LLM triage** — only called when keywords don't give a clear signal. Returns `language`, `playbook`, `english_query`, and `out_of_scope_reason`.
3. **Tone detection** — detects `distressed`, `urgent`, `confused`, or `calm` tone from the user's message using regex. Passed to the answer generator to frame the response appropriately.

Also runs `danger_flags()` — pure regex check for threats, violence, police, self-harm keywords.

### Case Builder — `core/case_builder.py`

Extracts facts from user messages across multiple turns:

1. LLM must return both the fact `value` AND an `evidence_quote` — the exact words from the message
2. The quote is verified to actually appear in the user's message
3. The value is type-coerced: dates → ISO 8601 (via `dateutil.parser`), amounts → float, bools → True/False
4. Only fact names declared in the playbook's `facts_to_collect` are accepted

The prompt includes **context hint** — when waiting for a specific fact, the LLM is told what question was just asked so it can map a short reply ("6 November 2026") to the right fact.

### Rules Engine — `core/rules.py`

Fully deterministic, no AI:

- **Deadline calculation** — `python-dateutil.relativedelta` for month-end-safe arithmetic. Supports chained rules (rule B starts when rule A's deadline passes) and days-from-fact (notice states its own deadline)
- **Forum tier** — District (up to ₹50 lakh) / State (up to ₹2 crore) / National, based on the amount paid
- **Red flag evaluation** — evaluates playbook `RedFlag` conditions (gt/lt/equals on collected facts)

### Grounded Answer Generator — `core/answer.py`

**Two system prompts:**

- **`SYSTEM_SPECIFIC`** — for personal problems: empathy opener, step-by-step guidance, cite everything
- **`SYSTEM_GENERAL`** — for informational questions: direct and factual, no empathy opener, numbered lists when asked

**Tone-aware framing** — appends a `TONE_INSTRUCTION` to the system prompt based on detected tone:
- `distressed` → "Begin with 'Don't worry, this situation is manageable'"
- `urgent` → "Lead with the most time-sensitive action first"
- `confused` → "Use very simple language, explain legal terms in plain words"

**Generate → Check → Retry → Fallback** loop:
1. Generate answer
2. Run honesty checker
3. If blocking flags → retry once with specific error messages
4. If still failing → safe canned fallback

### Honesty Checker — `core/checker.py`

Pure Python code — no AI. Checks every answer before it reaches the user:

| Check | Severity | Effect |
|---|---|---|
| Invented section number | urgent | Blocks answer |
| Invented Act name | urgent | Blocks answer |
| Invented court case citation | urgent | Blocks answer |
| Citation tag not in provided items | urgent | Blocks answer |
| Imperfect quote (LLM truncated) | warn | Logged only |
| Unrecognised number | warn | Logged only |
| Legal claim without citation | warn | Logged only |

Internal checker codes (`bad_quote`, `unsupported_number`, `fallback`, etc.) are **never shown to users** — filtered in the frontend.

### Playbooks — `backend/playbooks/`

YAML configuration files — all legal domain knowledge lives here:

| Playbook | Type | Coverage |
|---|---|---|
| `refund` | case | Consumer Protection Act 2019 — online/offline refunds |
| `notice_cheque_bounce` | document | NI Act 1881 — dishonoured cheque notice |
| `notice_loan_recovery` | document | SARFAESI Act 2002 — secured loan recovery |
| `notice_general_demand` | document | General money demand notice |

Each playbook defines: facts to collect, required facts, fact types, deadline rules, red flags, forum tiers.

### Legal Library — `backend/library/`

29 Markdown files across 4 Acts + 4 source PDFs:

| Prefix | Act | Items |
|---|---|---|
| C-001 to C-010 | Consumer Protection Act, 2019 | 10 |
| N-001 to N-008 | Negotiable Instruments Act, 1881 | 8 |
| L-001 to L-006 | SARFAESI Act, 2002 | 6 |
| G-001 to G-005 | Limitation Act, 1963 | 5 |

Each item has: `id`, `title`, `status` (VERIFIED/DRAFT), `source_confidence`, `last_verified`, `excerpt[]` (verbatim quotes), `meaning`, `limits`.

### Retrieval — `core/retriever.py`

BM25 keyword search (`BM25Okapi`) — intentionally simple:
- No embeddings, no vector database, no external service
- English-only index (triage generates an English query even for Hindi messages)
- Optionally filtered by `playbook_id`
- Returns top-5 items (down from 12 to stay within LLM token limits)

### Notice Analysis — `core/notice.py` + `core/extractor.py`

For pasted legal notices:
1. Strip markdown formatting
2. LLM extracts structured fields (every field must include a verbatim quote from the notice)
3. Scam checker runs (UPI/digital arrest/OTP/agency name patterns)
4. Map notice type to playbook
5. Derive facts from extracted fields
6. Compute deadlines and flags
7. Generate plain-language explanation

### Scam Checker — `core/scam_check.py`

Pure regex. Checks for 6 warning signs:

| Signal | Severity | Pattern |
|---|---|---|
| UPI/wallet payment request | high | UPI IDs, QR codes, GPay, PhonePe, crypto |
| Digital arrest threat | high | "digital arrest", "arrest warrant", गिरफ्तार |
| Sensitive information request | high | OTP, CVV, ATM PIN, Aadhaar |
| Very short deadline | medium | Within 24/48 hours, "immediately" |
| Fake agency name | medium | CBI, TRAI, Enforcement Directorate |
| Personal email domain | low | Gmail, Yahoo, Outlook addresses |

---

## Frontend Deep Dive

### Pages

| Route | File | Purpose |
|---|---|---|
| `/` | `app/page.tsx` | Full landing page with embedded chat widget, features, FAQ |
| `/chat` | `app/chat/page.tsx` | Dedicated full-screen chat page |

### Key Components

| Component | Purpose |
|---|---|
| `ChatStream.tsx` | Full chat UI — streaming, voice input (Web Speech API), file attachment, citation chips, escalation cards, history callbacks |
| `HistoryPanel.tsx` | Sliding sidebar showing past conversations, New Case button, delete per conversation |
| `SourcePanel.tsx` | Slide-in drawer showing full library item when a citation chip is clicked |
| `EscalationCard.tsx` | Renders user-actionable flags (danger, deadlines, scam signals) below bot messages. All internal checker codes filtered out |
| `CitationChip.tsx` | Inline `[C-001]` button in bot messages — opens SourcePanel |
| `ThemeToggle.tsx` | Sun/moon toggle, persisted to localStorage |
| `LangToggle.tsx` | EN / हिं segmented control |
| `DisclaimerBanner.tsx` | Persistent top-of-page legal disclaimer |

### State Management

| State | Where stored | How |
|---|---|---|
| Language preference | `localStorage` | `lib/useLang.ts` — shared across tabs |
| Theme preference | `localStorage` | `lib/useTheme.ts` |
| Conversation history | `localStorage` | `lib/useHistory.ts` — up to 30 conversations |
| Case state (CaseFile) | React `useRef` in ChatStream | Sent back to server on every turn |
| Active conversation | React state in `page.tsx` | Switched via HistoryPanel |

### API Client — `lib/api.ts`

- `NEXT_PUBLIC_API_URL` empty → mock mode (canned responses, no backend needed)
- `NEXT_PUBLIC_API_URL` set → live mode
- Maps frontend `{message, case_state}` to backend `{message, case}`
- Converts single JSON `TurnResult` response into `ChatEvent` format for the UI
- Specific error messages for 429 (rate limit) and 503 (unavailable)

### Mock Mode

When `NEXT_PUBLIC_API_URL` is empty, `lib/mock.ts` intercepts all API calls:
- Simulates streaming with `setTimeout` delays
- Returns realistic REFUND, URGENT, and UNSURE canned answers
- Fully functional citation chips and SourcePanel

---

## AI Pipeline

```
User message
     │
     ▼
1. Keyword Pre-Triage (regex, 0ms)
     │  Matches? → route instantly
     │  No match? → LLM Triage
     ▼
2. LLM Triage (1 call, ~1s)
     │  language, playbook, english_query
     │
     ├─ "general" → Retriever → Answer Generator → Honesty Checker
     │
     ├─ "none" → Friendly out-of-scope message
     │
     ├─ document type → Conversational greeting
     │   User pastes notice? → Notice Extractor → Scam Checker →
     │                          Retriever → Answer Generator
     │
     └─ case type ──────────────────────────────────────────────┐
                                                                 │
3. Case Builder (1 call per turn)                               │
     │  Extract facts with evidence quotes                       │
     │  Missing required facts? → ask next question             │
     │  All facts collected? ──────────────────────────────────►│
                                                                 │
4. Retriever (BM25, 0ms)                                        │
     │  Top-5 library items for the case                        │
     ▼                                                           │
5. Answer Generator (1 call)   ◄────────────────────────────────┘
     │  SYSTEM_SPECIFIC or SYSTEM_GENERAL
     │  + tone instruction (distressed/urgent/confused/calm)
     │  + library items + case facts
     ▼
6. Honesty Checker (pure Python, 0ms)
     │  Pass? → return answer to user
     │  Fail? → retry with specific error message
     │  Still fail? → safe canned fallback
     ▼
7. Rules Engine (pure Python, 0ms)
     │  Deadline dates
     │  Forum tier
     │  Red flags
     ▼
Final TurnResult → Frontend
```

**LLM is used for exactly 4 tasks:** triage, fact extraction, notice extraction, answer generation.  
**Everything else is pure deterministic Python:** deadlines, forum tiers, flags, honesty checking, scam detection, keyword routing.

---

## Knowledge Base (Legal Library)

Each library item is a Markdown file with YAML front-matter:

```markdown
---
id: C-005
title: Time limit to file a consumer complaint (s.69)
topic: consumer
applies_to: [refund]
source_url: https://www.indiacode.nic.in/...
source_name: Consumer Protection Act, 2019
source_confidence: primary
last_verified: 2026-11-07
status: VERIFIED
---

## Excerpt
s.69(1): "shall not admit a complaint unless it is filed within two years..."

## Plain-language meaning
Generally you have two years from when the cause of action arose.

## Limits
What date the cause of action arose can be argued.
```

Source PDFs are stored in `library/sources/` — all downloaded from India Code (official government source).

---

## Key Design Decisions

### 1. Stateless server
The full `CaseFile` serialises into every request and response. The server stores nothing. This makes scaling trivial and eliminates session management complexity.

### 2. BM25 instead of embeddings
No vector database, no embedding model calls, no external service dependencies. The library is small and curated — keyword search is fast, transparent, and sufficient.

### 3. LLM for language, Python for logic
- LLM: classification, extraction, summarisation
- Python: deadline arithmetic, forum tiers, flag evaluation, honesty checking, scam detection

This means legal logic is auditable, deterministic, and testable without an LLM.

### 4. Four-layer fact validation
Evidence quote required → quote verified in message → type coercion → only known fact names accepted. The LLM cannot invent facts.

### 5. Layered hallucination prevention
System prompt instructions → evidence quote requirement → post-generation honesty checker → retry with specific errors → safe canned fallback. Each layer independently prevents bad information reaching the user.

### 6. Keyword pre-triage
Common Hinglish/Hindi phrases bypass the LLM triage entirely. This prevents `json_validate_failed` errors on models that struggle with non-English JSON output, and reduces latency for the most common queries.

### 7. Tone-aware single LLM call
Instead of a separate "framing" LLM call, the detected emotional tone (distressed/urgent/confused) is injected into the system prompt as a tone instruction. Same latency, same cost, conversational output.

---

## Project Structure

```
nyay-saathi/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point, CORS, middleware
│   │   ├── deps.py              # Rate limiter, LLM dependency injection
│   │   └── routes/
│   │       ├── chat.py          # POST /chat, /draft/demand, /draft/reply
│   │       ├── notice.py        # POST /notice/analyze
│   │       ├── export.py        # POST /export (PDF)
│   │       └── playbooks.py     # GET /playbooks, /sources/{id}
│   ├── core/
│   │   ├── config.py            # Settings from .env
│   │   ├── llm.py               # LLM abstraction (Gemini, Groq, Fake)
│   │   ├── triage.py            # Keyword pre-triage + LLM triage + tone detection
│   │   ├── case_builder.py      # Multi-turn fact extraction
│   │   ├── flow.py              # Main orchestrator (case_turn)
│   │   ├── answer.py            # Grounded answer generator (tone-aware)
│   │   ├── checker.py           # Honesty checker (pure Python)
│   │   ├── retriever.py         # BM25 keyword retrieval
│   │   ├── notice.py            # Notice analysis orchestrator
│   │   ├── extractor.py         # LLM-based notice field extraction
│   │   ├── scam_check.py        # Regex-based scam signal detection
│   │   ├── rules.py             # Deadline arithmetic + forum tiers + flags
│   │   ├── drafts.py            # Template-based document generation
│   │   ├── export.py            # ReportLab PDF generation
│   │   ├── engine.py            # Playbook loader and models
│   │   ├── library.py           # Library item loader (Markdown parser)
│   │   └── schemas.py           # Pydantic data models
│   ├── library/
│   │   ├── consumer/            # C-001 to C-010 (Consumer Protection Act)
│   │   ├── ni_act/              # N-001 to N-008 (NI Act)
│   │   ├── sarfaesi/            # L-001 to L-006 (SARFAESI Act)
│   │   ├── limitation/          # G-001 to G-005 (Limitation Act)
│   │   └── sources/             # Source PDFs (4 Acts)
│   ├── playbooks/
│   │   ├── refund/              # Refund playbook + questions + template
│   │   ├── notice_cheque_bounce/
│   │   ├── notice_loan_recovery/
│   │   ├── notice_general_demand/
│   │   └── _shared/             # Shared templates
│   ├── tests/
│   │   ├── test_phase2.py       # Library + LLM retry tests
│   │   ├── test_phase3.py       # Honesty checker + answer tests
│   │   ├── test_phase4.py       # Playbook + rules engine tests
│   │   ├── test_phase5.py       # Case builder + flow tests
│   │   ├── test_phase6.py       # Notice + scam checker tests
│   │   └── test_phase7.py       # Full API integration tests
│   ├── outputs/                 # Generated PDFs (gitignored)
│   ├── .env                     # Secrets (gitignored)
│   ├── .env.example             # Template
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx           # Root layout, metadata, fonts
│   │   ├── page.tsx             # Landing page + embedded chat
│   │   ├── chat/page.tsx        # Full-screen chat page
│   │   ├── icon.svg             # Favicon (balance scales)
│   │   └── globals.css          # Tailwind v4 + theme tokens
│   ├── components/
│   │   ├── ChatStream.tsx       # Full chat UI
│   │   ├── HistoryPanel.tsx     # Case history sidebar
│   │   ├── SourcePanel.tsx      # Citation detail drawer
│   │   ├── EscalationCard.tsx   # Flag display (user-facing only)
│   │   ├── CitationChip.tsx     # Inline citation button
│   │   ├── DisclaimerBanner.tsx # Legal disclaimer bar
│   │   ├── LangToggle.tsx       # EN/Hindi switcher
│   │   ├── ThemeToggle.tsx      # Dark/light mode toggle
│   │   ├── Fonts.tsx            # Google Fonts loader
│   │   └── ui/button.tsx        # shadcn/ui button
│   ├── lib/
│   │   ├── api.ts               # Backend API client
│   │   ├── types.ts             # TypeScript type mirrors of backend schemas
│   │   ├── i18n.ts              # EN/Hindi UI string table
│   │   ├── homeCopy.ts          # Landing page copy (EN/Hindi)
│   │   ├── mock.ts              # Canned responses for mock mode
│   │   ├── theme.ts             # Tailwind class strings
│   │   ├── useLang.ts           # Language state hook
│   │   ├── useTheme.ts          # Theme state hook
│   │   ├── useHistory.ts        # Conversation history hook
│   │   └── utils.ts             # cn() utility
│   ├── public/                  # Static assets
│   ├── .env.local               # Frontend env (gitignored)
│   ├── .env.local.example       # Template
│   └── package.json
├── docs/
│   └── assumptions.md           # Design decisions and assumptions
└── README.md
```

---

## Running Locally

### Prerequisites

- Python 3.13+
- Node.js 18+
- A Groq or Google Gemini API key

### Backend

```powershell
# 1. Create virtual environment
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env — set LLM_PROVIDER, LLM_MODEL, LLM_API_KEY

# 4. Start the server (port 8001 recommended if frontend is on 3000)
uvicorn app.main:app --port 8001
# API: http://localhost:8001
# Docs: http://localhost:8001/docs
```

### Frontend

```powershell
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment
copy .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8001

# 3. Start the dev server
npm run dev
# App: http://localhost:3000
```

Leave `NEXT_PUBLIC_API_URL` empty in `.env.local` to run in **mock mode** — no backend required, canned responses with full citation and source panel behaviour.

---

## API Reference

All endpoints return JSON. Rate limit: 60 requests/minute per IP.

### `POST /chat`

Main conversational endpoint.

**Request:**
```json
{
  "message": "My seller refused my refund of Rs 20,000",
  "case": null,
  "answer_now": false
}
```

**Response (`TurnResult`):**
```json
{
  "route": "case",
  "case": { "playbook_id": "refund", "language": "en", "facts": {}, "missing": ["seller_name"] },
  "questions": ["Who did you buy from? (the shop, website or app name)"],
  "ready": false,
  "deadlines": [],
  "flags": [],
  "forum": null,
  "answer": null,
  "message": ""
}
```

Pass `case` back unchanged on the next turn. When `ready: true`, `answer` is populated.

### `POST /notice/analyze`

Analyse a pasted legal notice directly.

**Request:**
```json
{
  "text": "LEGAL NOTICE... [full notice text]",
  "language": "en",
  "user_facts": {}
}
```

### `POST /draft/demand`

Generate a demand notice draft from a completed `CaseFile`.

### `POST /draft/reply`

Generate a reply-to-notice draft.

### `POST /export`

Convert text to PDF.

**Request:** `{ "title": "Demand Notice", "text": "..." }`  
**Response:** `application/pdf` bytes

### `GET /sources/{id}`

Fetch a single library item (e.g. `C-005`).

### `GET /playbooks`

List all available playbooks.

### `GET /health`

`{ "status": "ok" }`

---

## Configuration

### Backend — `backend/.env`

```env
LLM_PROVIDER=groq              # gemini or groq
LLM_MODEL=your-model-name      # e.g. llama-3.3-70b-versatile
LLM_API_KEY=your-api-key
ALLOWED_ORIGINS=http://localhost:3000
ALLOW_DRAFT=true               # serve DRAFT library items
RATE_LIMIT_PER_MIN=60
```

### Frontend — `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8001   # leave empty for mock mode
```

---

## Legal Disclaimer

This application provides **general legal information** only. It is not legal advice and does not create a lawyer-client relationship. The information is based on a small curated library of verified legal texts and may not be complete, current, or applicable to your specific situation. For large amounts, court deadlines, or complex matters, always consult a qualified lawyer or a free legal-aid service.

**Free legal aid in India:** State Legal Services Authority (SLSA) in every state — visit [nalsa.gov.in](https://nalsa.gov.in) or call **15100**.
