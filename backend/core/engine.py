"""Loads and validates playbooks (data files). The engine is generic; the law lives in the YAML + library."""
from typing import Literal, Optional
import yaml
from pydantic import BaseModel, Field
from .config import settings
from .library import load_library


class Add(BaseModel):
    days: int = 0
    months: int = 0
    years: int = 0
    days_from_fact: Optional[str] = None      # take the number of days from a fact (e.g. a deadline the sender stated)


class DeadlineRule(BaseModel):
    id: str
    label: str
    start_fact: Optional[str] = None          # a date fact to count from ...
    after_rule: Optional[str] = None          # ... or the due date of an earlier rule
    add: Add
    library: list[str] = Field(default_factory=list)
    warn_days: int = 14
    approximate: bool = False
    note: str = ""


class Condition(BaseModel):
    fact: str
    gt: Optional[float] = None
    lt: Optional[float] = None
    equals: Optional[bool | str] = None


class RedFlag(BaseModel):
    id: str
    when: Condition
    message: str
    severity: Literal["warn", "urgent"] = "warn"


class Tier(BaseModel):
    name: str
    upto: Optional[float] = None              # inclusive upper limit; None = no limit


class Forum(BaseModel):
    fact: str
    library: list[str]
    tiers: list[Tier]
    caveat: str = ""


class Playbook(BaseModel):
    id: str
    type: Literal["case", "document"]
    title: str
    triggers: list[str] = Field(default_factory=list)
    facts_to_collect: list[str] = Field(default_factory=list)
    required_facts: list[str] = Field(default_factory=list)      # must be known before we give a full answer
    fact_types: dict[str, str] = Field(default_factory=dict)     # fact name -> date | number | bool (default text)
    ask_facts: list[str] = Field(default_factory=list)           # facts to ask the notice recipient for (the notice cannot contain them)
    notice_date_fact: Optional[str] = None                       # which fact the notice's own date feeds
    amount_fact: Optional[str] = None
    deadline_days_fact: Optional[str] = None                     # which fact gets the number of days the sender demands
    deadline_rules: list[DeadlineRule] = Field(default_factory=list)
    red_flags: list[RedFlag] = Field(default_factory=list)
    forum: Optional[Forum] = None
    options_ladder: list[str] = Field(default_factory=list)


def load_playbook(playbook_id: str) -> Playbook:
    path = settings.playbooks_dir / playbook_id / "playbook.yaml"
    return Playbook.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_all_playbooks() -> dict[str, Playbook]:
    out = {}
    for p in sorted(settings.playbooks_dir.glob("*/playbook.yaml")):
        if p.parent.name.startswith("_"):
            continue
        pb = load_playbook(p.parent.name)
        out[pb.id] = pb
    return out


def missing_library_refs(pb: Playbook) -> list[str]:
    """Every library id a playbook mentions must exist."""
    lib = load_library()
    ids = [i for r in pb.deadline_rules for i in r.library] + (pb.forum.library if pb.forum else [])
    return sorted({i for i in ids if i not in lib})
