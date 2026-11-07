"""Dates, forum and red flags: plain code, no AI. Dates are never computed by the model."""
from datetime import date, timedelta
from typing import Literal, Optional
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from .engine import Playbook, Condition
from .schemas import Flag


class DeadlineResult(BaseModel):
    rule_id: str
    label: str
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    days_left: Optional[int] = None
    status: Literal["ok", "due_soon", "overdue", "needs_fact"]
    library: list[str] = []
    missing: str = ""                 # which fact is needed when status == needs_fact
    approximate: bool = False
    note: str = ""


def _to_date(v) -> Optional[date]:
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v.strip()[:10])
        except ValueError:
            return None
    return None


def compute_deadlines(pb: Playbook, facts: dict, today: Optional[date] = None) -> list[DeadlineResult]:
    today = today or date.today()
    done: dict[str, DeadlineResult] = {}
    for r in pb.deadline_rules:
        base = dict(rule_id=r.id, label=r.label, library=r.library, approximate=r.approximate, note=r.note)
        if r.after_rule:
            prev = done.get(r.after_rule)
            start = prev.due_date if prev else None
            need = (prev.missing if prev else r.after_rule) if not start else ""
        else:
            start = _to_date(facts.get(r.start_fact))
            need = "" if start else (r.start_fact or "")
        days = r.add.days
        if r.add.days_from_fact:
            try:
                days = int(float(facts[r.add.days_from_fact]))
            except (KeyError, TypeError, ValueError):
                start, need = None, r.add.days_from_fact
        if not start:
            res = DeadlineResult(**base, status="needs_fact", missing=need)
        else:
            due = start + relativedelta(years=r.add.years, months=r.add.months) + timedelta(days=days)
            left = (due - today).days
            status = "overdue" if left < 0 else "due_soon" if left <= r.warn_days else "ok"
            res = DeadlineResult(**base, start_date=start, due_date=due, days_left=left, status=status)
        done[r.id] = res
    return list(done.values())


def _holds(c: Condition, facts: dict) -> bool:
    if c.fact not in facts or facts[c.fact] is None:
        return False
    v = facts[c.fact]
    try:
        if c.gt is not None and not float(v) > c.gt:
            return False
        if c.lt is not None and not float(v) < c.lt:
            return False
    except (TypeError, ValueError):
        return False
    if c.equals is not None and v != c.equals:
        return False
    return True


def evaluate_flags(pb: Playbook, facts: dict, deadlines: list[DeadlineResult]) -> list[Flag]:
    flags = [Flag(code=f.id, severity=f.severity, message=f.message) for f in pb.red_flags if _holds(f.when, facts)]
    for d in deadlines:
        if d.status == "overdue":
            flags.append(Flag(code="deadline_overdue", severity="urgent",
                              message=f"{d.label}: the date {d.due_date} may already have passed. See a lawyer now."))
        elif d.status == "due_soon":
            flags.append(Flag(code="deadline_close", severity="urgent" if d.days_left <= 7 else "warn",
                              message=f"{d.label}: about {d.days_left} day(s) left (by {d.due_date}). Act now and confirm with a lawyer."))
    return flags


def forum_for(pb: Playbook, facts: dict) -> Optional[dict]:
    if not pb.forum or facts.get(pb.forum.fact) is None:
        return None
    amount = float(facts[pb.forum.fact])
    for t in pb.forum.tiers:
        if t.upto is None or amount <= t.upto:
            return {"forum": t.name, "library": pb.forum.library, "caveat": pb.forum.caveat}
    return None
