"""Honesty checker: plain code, no AI. Decides whether an answer is allowed to reach the user."""
import re
from .schemas import Answer, Flag, LibraryItem

_DEV = str.maketrans("०१२३४५६७८९", "0123456789")
_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
          "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20, "twenty-five": 25, "thirty": 30,
          "forty": 40, "forty-five": 45, "fifty": 50, "sixty": 60, "ninety": 90, "hundred": 100}
_NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*-?\s*(days?|months?|years?|%|lakhs?|crores?)")
_SEC = re.compile(r"(?<![a-z])(?:sections?|sec\.|s\.|धारा)\s*(\d+[a-z]?)", re.I)
_ACT = re.compile(r"\b((?:[A-Z][A-Za-z()&'-]*\s+){1,8}Act,?\s*(?:19|20)\d\d)\b")
_CASE = re.compile(r"\b[A-Z][\w.&'-]*(?:\s[A-Z][\w.&'-]*){0,4}\s(?:v\.|vs\.?|versus)\s[A-Z][\w.&'-]*(?:\s[A-Z][\w.&'-]*){0,4}")
_TAG = re.compile(r"\[([A-Z]-\d{3})\]")
_LEGAL_WORDS = re.compile(r"\b(must|shall|entitled|liable|deadline|within|court|commission|tribunal|"
                          r"penalt\w*|punish\w*|fine|compensation|refund|law)\b", re.I)

def _alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())

def _norm(t: str) -> str:
    t = t.lower().translate(_DEV)
    for w, n in sorted(_WORDS.items(), key=lambda x: -len(x[0])):
        t = re.sub(rf"\b{re.escape(w)}\b", str(n), t)
    return re.sub(r"per\s*cent\.?|percent", "%", t)

def _numbers(t: str) -> set:
    return {(m.group(1).replace(",", ""), "%" if m.group(2) == "%" else m.group(2).rstrip("s"))
            for m in _NUM.finditer(_norm(t))}

def _item_text(i: LibraryItem) -> str:
    return " ".join([i.title, i.source_name, " ".join(i.excerpt), i.meaning, i.limits])

def check(answer: Answer, items: list[LibraryItem], allowed_text: str = "") -> list[Flag]:
    """items = the library items that were given to the model. allowed_text = the user's own words/facts."""
    flags: list[Flag] = []
    by_id = {i.id: i for i in items}
    corpus = " ".join(_item_text(i) for i in items)
    alnum_corpus = _alnum(corpus)
    def bad(code, msg): flags.append(Flag(code=code, severity="urgent", message=msg))
    def warn(code, msg): flags.append(Flag(code=code, severity="warn", message=msg))

    for tag in set(_TAG.findall(answer.text)):
        if tag not in by_id:
            bad("unknown_citation", f"Tag [{tag}] is not one of the provided items")
    for c in answer.citations:
        item = by_id.get(c.item_id)
        if not item:
            bad("unknown_citation", f"Citation {c.item_id} is not one of the provided items")
        elif c.quote and _alnum(c.quote) not in _alnum(" ".join(item.excerpt)):
            # Imperfect quote — warn only, don't block. LLMs sometimes truncate quotes slightly.
            warn("bad_quote", f"Quote for {c.item_id} could not be verified exactly")
    if answer.confidence == "library" and not answer.citations:
        bad("no_citation", "confidence is 'library' but nothing is cited")

    ok_secs = {m.lower() for m in _SEC.findall(corpus)}
    for s in {m.lower() for m in _SEC.findall(answer.text.translate(_DEV))} - ok_secs:
        bad("unsupported_section", f"Section {s} is not in the provided items")
    for a in _ACT.findall(answer.text):
        name = re.sub(r"^the\s+", "", a.strip(), flags=re.I)
        if _alnum(name) not in alnum_corpus:
            bad("unsupported_act", f"Act '{a}' is not in the provided items")
    for m in _CASE.finditer(answer.text):
        if _alnum(m.group(0)) not in alnum_corpus:
            bad("unsupported_case", f"Case '{m.group(0)}' is not in the provided items")

    for n, unit in _numbers(answer.text) - _numbers(corpus + " " + allowed_text):
        # Unrecognised numbers warn only — the LLM may have phrased a known number differently.
        warn("unsupported_number", f"'{n} {unit}' could not be matched to a library source")

    for sent in re.split(r"(?<=[.!?।])\s+", answer.text):
        if _LEGAL_WORDS.search(sent) and not _TAG.search(sent):
            flags.append(Flag(code="uncited_legal_claim", severity="warn", message=sent.strip()[:120]))
    return flags

def blocking(flags: list[Flag]) -> list[Flag]:
    return [f for f in flags if f.severity == "urgent"]