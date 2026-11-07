import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config import settings
from .routes import chat, export, notice, playbooks

log = logging.getLogger("nyay")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Nyay Saathi API", description="General legal information. Not legal advice.")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins),
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.middleware("http")
async def access_log(request: Request, call_next):
    """Logs method, path, status and time only. Never the body: it may contain personal details."""
    t = time.perf_counter()
    try:
        resp = await call_next(request)
    except Exception as exc:
        log.error("unhandled %s on %s", type(exc).__name__, request.url.path)
        return JSONResponse(status_code=503, content={"detail": "The assistant is temporarily unavailable. Please try again."})
    log.info("%s %s -> %s (%.0f ms)", request.method, request.url.path, resp.status_code, (time.perf_counter() - t) * 1000)
    return resp


@app.exception_handler(ValueError)
async def bad_model_output(request: Request, exc: ValueError):
    return JSONResponse(status_code=502, content={"detail": "The AI model returned an unusable reply. Please try again."})


@app.exception_handler(Exception)
async def unavailable(request: Request, exc: Exception):
    log.error("unhandled %s on %s", type(exc).__name__, request.url.path)
    return JSONResponse(status_code=503, content={"detail": "The assistant is temporarily unavailable. Please try again."})


@app.get("/health")
def health():
    return {"status": "ok"}


for r in (chat.router, notice.router, export.router, playbooks.router):
    app.include_router(r)
