"""
Nyay Saathi — FastAPI application entry point.

Phase 0: minimal app with a /health endpoint.
CORS is restricted to the Next.js dev server (localhost:3000).
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()  # loads backend/.env if present (never committed)

app = FastAPI(
    title="Nyay Saathi API",
    description="Legal-help assistant for India — backend API.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — only allow the Next.js dev server; tighten further in production.
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
async def health_check() -> dict:
    """Liveness probe — returns ok when the server is running."""
    return {"status": "ok"}
