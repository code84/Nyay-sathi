import time
from collections import defaultdict, deque
from functools import lru_cache
from fastapi import HTTPException, Request
from core.config import settings
from core.llm import LLM, get_llm


@lru_cache(maxsize=1)
def get_llm_dep() -> LLM:
    return get_llm()


_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    """Simple per-IP limit so a public demo cannot burn the free API key.
    Behind a proxy request.client.host may be the proxy; see README before deploying."""
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.rate_limit_per_min:
        raise HTTPException(429, "Too many requests. Please wait a minute and try again.")
    q.append(now)
