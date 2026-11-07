from typing import Literal, Optional, Any
from pydantic import BaseModel, Field


class LibraryItem(BaseModel):
    id: str
    title: str
    topic: str
    applies_to: list[str]
    source_url: str
    source_name: str
    source_pdf: Optional[str] = None
    source_confidence: str
    edition_note: Optional[str] = None
    last_verified: str
    status: str                      # DRAFT or VERIFIED
    excerpt: list[str]
    meaning: str
    limits: str

    @property
    def is_verified(self) -> bool:
        return self.status.strip().upper().startswith("VERIFIED")


class Fact(BaseModel):
    """One fact in a case file, always tied to the user's own words."""
    value: Any
    evidence_quote: Optional[str] = None


class CaseFile(BaseModel):
    playbook_id: str
    language: str = "en"
    english_query: str = ""                 # short English search phrase for the library
    facts: dict[str, Fact] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)


class Triage(BaseModel):
    language: Literal["en", "hi", "hinglish", "other"] = "en"
    playbook: str = "none"
    english_query: str = ""
    out_of_scope_reason: str = ""


class Quoted(BaseModel):
    """A value read from a notice, with the exact text it came from."""
    value: Optional[str] = None
    quote: Optional[str] = None


class NoticeExtract(BaseModel):
    notice_type: Literal["cheque_bounce", "loan_recovery", "general_demand", "unknown"] = "unknown"
    sender: Quoted = Quoted()
    notice_date: Quoted = Quoted()
    demand: Quoted = Quoted()
    amount: Quoted = Quoted()
    deadline: Quoted = Quoted()
    laws_cited: list[Quoted] = Field(default_factory=list)
    consequence: Quoted = Quoted()


class Citation(BaseModel):
    item_id: str
    quote: Optional[str] = None


class Flag(BaseModel):
    code: str
    severity: Literal["info", "warn", "urgent"] = "info"
    message: str


class Answer(BaseModel):
    text: str
    citations: list[Citation] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)
    confidence: Literal["library", "general", "unsure"] = "unsure"
