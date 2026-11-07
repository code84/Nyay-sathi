import re
from functools import lru_cache
from rank_bm25 import BM25Okapi
from .library import load_library
from .schemas import LibraryItem
from .config import settings

_WORD = re.compile(r"[a-z0-9]+")

def _tok(text: str) -> list[str]:
    return _WORD.findall(text.lower())

def _doc(i: LibraryItem) -> str:
    return " ".join([i.title, i.meaning, " ".join(i.excerpt), " ".join(i.applies_to)])

@lru_cache(maxsize=1)
def _all_items() -> tuple[LibraryItem, ...]:
    return tuple(load_library().values())

def retrieve(query: str, playbook_id: str | None = None, k: int = 5,
             allow_draft: bool | None = None) -> list[LibraryItem]:
    """query must be ENGLISH (the library is English). Returns the top-k items."""
    allow_draft = settings.allow_draft if allow_draft is None else allow_draft
    items = [i for i in _all_items() if allow_draft or i.is_verified]
    if playbook_id:
        items = [i for i in items if playbook_id in i.applies_to]
    if not items:
        return []
    scores = BM25Okapi([_tok(_doc(i)) for i in items]).get_scores(_tok(query))
    ranked = sorted(zip(scores, items), key=lambda x: -x[0])
    return [i for _, i in ranked[:k]]