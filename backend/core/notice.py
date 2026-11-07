import re
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from .answer import grounded_answer
from .case_builder import _coerce, load_questions
from .checker import _SEC, _ACT, _alnum, _item_text, _norm
from .engine import Playbook, load_playbook
from .extractor import extract_notice
from .flow import LANGS
from .llm import LLM
from .retriever import retrieve
from .rules import DeadlineResult, compute_deadlines, evaluate_flags
from .scam_check import ScamReport, scam_check
from .schemas import Answer, CaseFile, Fact, Flag, LibraryItem, NoticeExtract, Quoted

PLAYBOOK_FOR = {"cheque_bounce": "notice_cheque_bounce", "loan_recovery": "notice_loan_recovery",
                "general_demand": "notice_general_demand"}
UNKNOWN_MSG = ("I could not tell what kind of notice this is, so I have not explained its legal effect. "
               "Below are the details I could read and any warning signs. Please show the notice to a lawyer, "
               "especially if it has a deadline.")


class FormField(BaseModel):
    fact: str
    kind: str
    label: str


class LawMatch(BaseModel):
    quote: str
    verified: bool
    library_ids: list[str] = Field(default_factory=list)


class NoticeAnalysis(BaseModel):
    extract: NoticeExtract
    dropped_fields: list[str] = Field(default_factory=list)
    playbook_id: str = "unknown"
    case: Optional[CaseFile] = None
    deadlines: list[DeadlineResult] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)
    ask: list[FormField] = Field(default_factory=list)
    scam: ScamReport
    law_matches: list[LawMatch] = Field(default_factory=list)
    answer: Optional[Answer] = None
    message: str = ""


def _days_from(text: Optional[str]) -> Optional[int]:
    m = re.search(r"(\d+)\s*(?:days?|din\b|दिन)", _norm(text or ""))
    return int(m.group(1)) if m else None


def match_laws(laws: list[Quoted], items: list[LibraryItem]) -> list[LawMatch]:
    out = []
    for law in laws:
        text = f"{law.quote or ''} {law.value or ''}"
        secs = {s.lower() for s in _SEC.findall(text)}
        acts = [re.sub(r"^the\s+", "", a, flags=re.I) for a in _ACT.findall(text)]
        ids = [i.id for i in items
               if (secs & {s.lower() for s in _SEC.findall(_item_text(i))})
               or any(_alnum(a) in _alnum(_item_text(i)) for a in acts)]
        out.append(LawMatch(quote=law.quote or law.value or "", verified=bool(ids), library_ids=ids))
    return out


def _derive_facts(pb: Playbook, ex: NoticeExtract) -> dict[str, Fact]:
    f: dict[str, Fact] = {}
    def put(name, q: Quoted):
        if name and q.value is not None:
            f[name] = Fact(value=q.value, evidence_quote=q.quote)
    put("sender", ex.sender)
    put("demand", ex.demand)
    put("notice_date", ex.notice_date)
    put(pb.notice_date_fact, ex.notice_date)
    put(pb.amount_fact, ex.amount)
    d = _days_from(ex.deadline.quote)
    if pb.deadline_days_fact and d is not None:
        f[pb.deadline_days_fact] = Fact(value=d, evidence_quote=ex.deadline.quote)
    for name, fact in list(f.items()):                       # clean types
        v = _coerce(pb.fact_types.get(name, "text"), fact.value)
        if v is None:
            del f[name]
        else:
            fact.value = v
    return f


def analyze_notice(llm: LLM, notice_text: str, user_facts: Optional[dict] = None,
                   language: str = "en", today: Optional[date] = None) -> NoticeAnalysis:
    today = today or date.today()
    ex, dropped = extract_notice(llm, notice_text)
    scam = scam_check(notice_text)
    pb_id = PLAYBOOK_FOR.get(ex.notice_type)
    if not pb_id:
        return NoticeAnalysis(extract=ex, dropped_fields=dropped, scam=scam, message=UNKNOWN_MSG)
    pb = load_playbook(pb_id)
    facts = _derive_facts(pb, ex)
    for name, v in (user_facts or {}).items():               # what the user entered in the form
        if name in pb.fact_types or name in pb.facts_to_collect:
            c = _coerce(pb.fact_types.get(name, "text"), v)
            if c is not None:
                facts[name] = Fact(value=c, evidence_quote="(entered by the user)")
    case = CaseFile(playbook_id=pb_id, language=language, facts=facts)
    values = {k: f.value for k, f in facts.items()}
    deadlines = compute_deadlines(pb, values, today)
    flags = evaluate_flags(pb, values, deadlines)
    qs = load_questions(pb_id)
    lang = "hi" if language == "hi" else "en"
    ask = [FormField(fact=n, kind=pb.fact_types.get(n, "text"), label=qs.get(n, {}).get(lang) or n.replace("_", " "))
           for n in pb.ask_facts if n not in facts]
    items = retrieve(f"{pb.title} {ex.demand.value or ''}", pb_id)
    laws = match_laws(ex.laws_cited, items)
    for lm in laws:
        if not lm.verified:
            flags.append(Flag(code="law_not_in_library", severity="warn",
                              message=f"The notice cites '{lm.quote}', which is not in my verified library. Ask a lawyer what it means."))
    case_text = "\n".join(f"{k}: {f.value}  (from the notice: \"{f.evidence_quote}\")" for k, f in facts.items())
    ans = grounded_answer(llm, "Explain this notice in plain language: what it demands, the time limits that apply, "
                          "and what the person can do next.", items, case_text=case_text,
                          language=LANGS.get(language, "English"), is_general=False, user_tone="calm")
    return NoticeAnalysis(extract=ex, dropped_fields=dropped, playbook_id=pb_id, case=case, deadlines=deadlines,
                          flags=flags, ask=ask, scam=scam, law_matches=laws, answer=ans)
