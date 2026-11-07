from typing import Any, Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from core.notice import NoticeAnalysis, analyze_notice
from ..deps import get_llm_dep, rate_limit

router = APIRouter(dependencies=[Depends(rate_limit)])


class NoticeIn(BaseModel):
    text: str = Field(min_length=20, max_length=15000)
    user_facts: dict[str, Any] = Field(default_factory=dict)
    language: Literal["en", "hi", "hinglish", "other"] = "en"


@router.post("/notice/analyze", response_model=NoticeAnalysis)
def analyze(body: NoticeIn, llm=Depends(get_llm_dep)):
    return analyze_notice(llm, body.text, body.user_facts, body.language)
