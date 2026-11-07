"""Fills a template from the case file. No AI. Anything unknown stays a visible [___ blank ___]."""
import re
from datetime import date
from .config import settings
from .schemas import CaseFile


def inr(n: float) -> str:
    s = str(int(round(n)))
    if len(s) <= 3:
        return "Rs " + s
    head, tail = s[:-3], s[-3:]
    return "Rs " + re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head) + "," + tail


def _fmt(name: str, v) -> str:
    if name == "amount" or name.endswith("_amount"):
        return inr(float(v))
    if name.endswith("_date"):
        d = date.fromisoformat(str(v))
        return f"{d.day} {d.strftime('%B %Y')}"
    return str(v)


def render_template(template: str, case: CaseFile) -> tuple[str, list[str]]:
    blanks: list[str] = []

    def sub(m):
        name = m.group(1)
        if name in case.facts:
            return _fmt(name, case.facts[name].value)
        blanks.append(name)
        return f"[___ {name.replace('_', ' ')} ___]"

    text = re.sub(r"\{\{(\w+)\}\}", sub, template)
    return text, sorted(set(blanks)) + sorted(set(re.findall(r"\[___ (.+?) ___\]", template)))


def demand_notice(case: CaseFile) -> tuple[str, list[str]]:
    path = settings.playbooks_dir / case.playbook_id / "templates" / "demand_notice.md"
    return render_template(path.read_text(encoding="utf-8"), case)


def reply_draft(case: CaseFile) -> tuple[str, list[str]]:
    path = settings.playbooks_dir / "_shared" / "reply_acknowledgement.md"
    return render_template(path.read_text(encoding="utf-8"), case)
