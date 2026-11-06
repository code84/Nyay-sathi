# Assumptions

This document records design decisions and assumptions made during the development of Nyay Saathi.
Each entry explains what was assumed, why, and what the consequences would be if the assumption turns out to be wrong.

---

## Phase 0 — Project Setup

### A0-1: LLM provider is Gemini (free tier)
*Assumption:* Google Gemini free tier provides sufficient rate limits for development and early testing.  
*Rationale:* Zero upfront cost; `google-genai` SDK is actively maintained.  
*Risk:* Rate limits may be hit during load testing; model selection is kept behind `LLM_PROVIDER` / `LLM_MODEL` env vars for easy swapping.

### A0-2: CORS locked to localhost:3000 in development
*Assumption:* The frontend dev server always runs on port 3000.  
*Rationale:* Minimises attack surface; origins are configurable via `ALLOWED_ORIGINS` env var for staging/production.

### A0-3: Python 3.13 is the runtime
*Assumption:* Developers have Python 3.13 installed.  
*Rationale:* Current stable release at project start (Nov 2026). The venv pins this implicitly.

---

## Phase 1+

*(Add assumptions here as the project grows)*
