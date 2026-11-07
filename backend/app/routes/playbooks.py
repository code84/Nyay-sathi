from fastapi import APIRouter, Depends, HTTPException
from core.engine import load_all_playbooks
from core.library import load_library
from core.schemas import LibraryItem
from ..deps import rate_limit

router = APIRouter(dependencies=[Depends(rate_limit)])


@router.get("/playbooks")
def list_playbooks():
    return [{"id": p.id, "title": p.title, "type": p.type} for p in load_all_playbooks().values()]


@router.get("/sources/{item_id}", response_model=LibraryItem)
def get_source(item_id: str):
    """Feeds the citation side panel in the web page."""
    item = load_library().get(item_id)
    if not item:
        raise HTTPException(404, "Source not found")
    return item
