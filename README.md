# Nyay Saathi

Nyay Saathi ("Justice Companion" in Hindi) is a legal-help web application for people in India.
It helps users understand their rights, navigate common legal situations, and prepare documents
by answering questions in plain language. The backend is built with FastAPI (Python) and uses
the Google Gemini API for AI-assisted responses; the frontend is built with Next.js, Tailwind CSS,
and shadcn/ui.

> **Important:** Nyay Saathi provides general legal information only. It is **not** a substitute
> for advice from a qualified lawyer. Nothing in this application constitutes legal advice,
> creates a lawyer-client relationship, or should be relied upon for any specific legal situation.

---

## Run locally

### Prerequisites

- Python 3.13+
- Node.js 18+

### Backend

```bash
# 1. Create and activate the virtual environment
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
# source .venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
# Then open .env and fill in LLM_API_KEY and LLM_MODEL

# 4. Start the server
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend

# 1. Install dependencies (already done if you cloned after Phase 0)
npm install

# 2. Set up environment variables
copy .env.local.example .env.local   # Windows
# cp .env.local.example .env.local   # macOS / Linux

# 3. Start the dev server
npm run dev
# App available at http://localhost:3000
```

---

## Project structure

```
nyay-saathi/
├── backend/
│   ├── app/            # FastAPI application
│   │   ├── main.py     # Entry point, CORS, routes
│   │   └── routes/     # Route handlers (added in later phases)
│   ├── core/           # Shared utilities (config, LLM client, …)
│   ├── playbooks/      # YAML playbooks for legal scenarios
│   ├── library/        # Indexed legal reference documents
│   ├── tests/          # pytest test suite
│   └── outputs/        # Generated PDFs / exports (gitignored)
├── frontend/           # Next.js 16 app
├── docs/               # Architecture decisions, assumptions, AI log
└── .github/            # CI workflows (added in later phases)
```
