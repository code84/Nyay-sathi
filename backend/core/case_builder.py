import re
from datetime import date
from typing import Optional
import yaml
from pydantic import BaseModel, Field
from .config import settings
from .engine import Playbook
from .llm import LLM
from .schemas import CaseFile, Fact


class Extraction(BaseModel):
    facts: dict[str, Fact] = Field(default_factory=dict)


SYSTEM = ("You extract facts from a user's message for a legal-help tool. Return JSON only. "
          "Include a fact ONLY if the user clearly stated it. Never guess or infer. "
          "For every fact give 'evidence_quote': the exact words copied from the user's message that state it.")


def _flat(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().casefold()


def _coerce(kind: str, v):
    """Turn a model-supplied value into a clean typed value, or None if it is not usable."""
    if v is None or v == "":
        return None
    if kind == "date":
        s = str(v).strip()
        # Try ISO format first (YYYY-MM-DD)
        try:
            return date.fromisoformat(s[:10]).isoformat()
        except ValueError:
            pass
        # Fallback: try dateutil parser for natural language dates like "6 november 2026"
        try:
            from dateutil import parser as dateparser
            return dateparser.parse(s, dayfirst=True).date().isoformat()
        except Exception:
            return None
    if kind == "number":
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
        s = re.sub(r"rs\.?|inr|rupees|₹|,", "", str(v).lower()).strip()
        return float(s) if re.fullmatch(r"\d+(\.\d+)?", s) else None   # rejects '1.5 lakh' etc.
    if kind == "bool":
        if isinstance(v, bool):
            return v
        return {"true": True, "yes": True, "false": False, "no": False}.get(str(v).strip().lower())
    return str(v).strip() or None


def update_case(llm: LLM, case: CaseFile, user_message: str, pb: Playbook, today: Optional[date] = None) -> CaseFile:
    today = today or date.today()
    # If we were waiting on specific facts, tell the LLM which question was just asked
    # so it can correctly map a short reply (e.g. "6 november 2026") to the right fact.
    context_hint = ""
    if case.missing:
        qs = load_questions(pb.id)
        lang = "hi" if case.language == "hi" else "en"
        last_q = qs.get(case.missing[0], {}).get(lang) or case.missing[0].replace("_", " ")
        context_hint = f"\n\nThe previous question asked to the user was: \"{last_q}\"\nThe user's message is most likely a direct answer to that question."
    prompt = (f"Today's date is {today.isoformat()}.\nFacts to look for (name: type): "
              + ", ".join(f"{n}: {pb.fact_types.get(n, 'text')}" for n in pb.facts_to_collect)
              + "\nRules: dates as YYYY-MM-DD, only if day, month and year are clear (resolve 'yesterday' etc. from today's date; "
                "if the year is missing and unclear, leave the fact out). amount: number of rupees only. "
                "bool facts: true or false.\n"
              f'Return {{"facts": {{"<name>": {{"value": ..., "evidence_quote": "..."}}}}}}'
              + context_hint
              + f"\n\nUser message:\n{user_message}")
    ext = llm.ask_json(prompt, Extraction, system=SYSTEM)
    msg = _flat(user_message)
    for name, fact in ext.facts.items():
        if name not in pb.facts_to_collect:
            continue
        q = fact.evidence_quote
        if not q or _flat(q) not in msg:          # no real quote from the user = fact rejected
            continue
        v = _coerce(pb.fact_types.get(name, "text"), fact.value)
        if v is None:
            continue
        case.facts[name] = Fact(value=v, evidence_quote=q)
    case.missing = [f for f in pb.required_facts if f not in case.facts]
    return case


def case_values(case: CaseFile) -> dict:
    return {k: f.value for k, f in case.facts.items()}


def case_text(case: CaseFile) -> str:
    return "\n".join(f"{k}: {f.value}  (user said: \"{f.evidence_quote}\")" for k, f in case.facts.items())


def load_questions(playbook_id: str) -> dict:
    p = settings.playbooks_dir / playbook_id / "questions.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}


def next_questions(case: CaseFile, pb: Playbook, max_q: int = 2) -> list[str]:
    qs = load_questions(pb.id)
    lang = "hi" if case.language == "hi" else "en"     # Hinglish and other languages get English questions for now
    out = []
    for f in case.missing[:max_q]:
        out.append(qs.get(f, {}).get(lang) or f"Please tell me: {f.replace('_', ' ')}")
    return out
