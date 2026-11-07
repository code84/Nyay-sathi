import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from core.drafts import demand_notice, reply_draft
from core.engine import load_all_playbooks
from core.flow import TurnResult, case_turn
from core.notice import analyze_notice
from core.schemas import CaseFile, Flag
from ..deps import get_llm_dep, rate_limit

router = APIRouter(dependencies=[Depends(rate_limit)])

# Messages longer than this are likely pasted notice text, not conversation
_NOTICE_TEXT_MIN_LEN = 200

def _strip_markdown(text: str) -> str:
    """Remove markdown formatting so the LLM sees clean notice text."""
    t = text
    t = re.sub(r"#{1,6}\s+", "", t)                      # headings
    t = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", t)       # bold/italic
    t = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", t)          # underscore bold/italic
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)        # links → keep label
    t = re.sub(r"`[^`]+`", "", t)                          # inline code
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.MULTILINE) # bullet points
    t = re.sub(r"^\s*\d+\.\s+", "", t, flags=re.MULTILINE) # numbered lists
    t = re.sub(r"\n{3,}", "\n\n", t)                       # excess blank lines
    return t.strip()


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=15000)   # raised to allow pasted notice text
    case: Optional[CaseFile] = None
    answer_now: bool = False


class DraftOut(BaseModel):
    text: str
    blanks: list[str]


@router.post("/chat", response_model=TurnResult)
def chat(body: ChatIn, llm=Depends(get_llm_dep)):
    if body.case and body.case.playbook_id not in load_all_playbooks():
        raise HTTPException(400, "Unknown playbook")

    result = case_turn(llm, body.case, body.message, answer_now=body.answer_now)

    # If triage identified this as a notice-type query AND the message is long
    # enough to be actual notice text, analyze it directly instead of looping.
    if result.route == "notice" and len(body.message.strip()) >= _NOTICE_TEXT_MIN_LEN:
        lang = body.case.language if body.case else "en"
        clean_text = _strip_markdown(body.message)
        analysis = analyze_notice(llm, clean_text, language=lang)
        # Convert scam signals to flags so the frontend can show them
        scam_flags = [
            Flag(code=f"scam_{s.code}", severity=s.severity, message=s.explanation)
            for s in analysis.scam.signals
        ] if analysis.scam.signals else []
        return TurnResult(
            route="case",
            case=analysis.case,
            flags=analysis.flags + scam_flags,
            answer=analysis.answer,
            deadlines=analysis.deadlines,
            ready=True,
        )

    return result


@router.post("/draft/demand", response_model=DraftOut)
def draft_demand(case: CaseFile):
    try:
        text, blanks = demand_notice(case)
    except (FileNotFoundError, OSError):
        raise HTTPException(400, "No demand-notice template for this playbook")
    return DraftOut(text=text, blanks=blanks)


@router.post("/draft/reply", response_model=DraftOut)
def draft_reply(case: CaseFile):
    text, blanks = reply_draft(case)
    return DraftOut(text=text, blanks=blanks)
