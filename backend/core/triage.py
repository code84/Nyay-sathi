import re
from .engine import load_all_playbooks
from .llm import LLM, LLMTimeoutError
from .schemas import Flag, Triage

# Plain-code safety net. It only ADDS a warning; it never blocks the user.
_DANGER = re.compile(r"\b(kill|threat\w*|beat|assault|arrest\w*|FIR|police|suicide)\b"
                     r"|मार\s*डाल|धमकी|जान\s*से|गिरफ्तार|पुलिस|आत्महत्या", re.I)

# Fast keyword pre-triage — avoids LLM call for obvious cases (also handles Hinglish/Hindi)
_KEYWORD_ROUTES: list[tuple[str, re.Pattern]] = [
    ("refund", re.compile(
        r"\b(refund|wapsi|vapas|money\s*back|paise\s*wapas|seller|amazon|flipkart|meesho|myntra|"
        r"nahi\s*mila|nahi\s*diya|consumer|complaint|product|order|delivered|delivery|defective|"
        r"cancel|wrong\s*item|galat\s*saman|shopping|return)\b", re.I)),
    ("notice_cheque_bounce", re.compile(
        r"\b(cheque|check\s*bounce|dishonour|dishonor|bank\s*return|insufficient\s*fund|"
        r"section\s*138|138|notice\s*mila|legal\s*notice.*cheque|cheque.*bounce|"
        r"bounced|returned\s*unpaid|chek|चेक|बाउंस)\b", re.I)),
    ("notice_loan_recovery", re.compile(
        r"\b(loan|EMI|sarfaesi|recovery\s*notice|bank\s*notice|possession|auction|"
        r"secured\s*loan|NPA|lender|outstanding\s*loan|repay|instalment|installment|"
        r"loan.*notice|notice.*loan|क़र्ज़|लोन|emi|किस्त)\b", re.I)),
]

def _keyword_triage(text: str) -> Triage | None:
    """Fast path: return a Triage result based on keywords, no LLM needed."""
    for playbook_id, pattern in _KEYWORD_ROUTES:
        if pattern.search(text):
            # Detect language heuristically
            has_devanagari = bool(re.search(r"[\u0900-\u097F]", text))
            has_roman_hindi = bool(re.search(r"\b(mera|meri|kya|hai|nahi|kar|ho|gaya|aaya|chahiye|karu|karun)\b", text, re.I))
            lang = "hi" if has_devanagari else ("hinglish" if has_roman_hindi else "en")
            return Triage(playbook=playbook_id, language=lang, english_query=playbook_id.replace("_", " "))
    return None


def danger_flags(text: str) -> list[Flag]:
    if _DANGER.search(text or ""):
        return [Flag(code="safety_or_threat", severity="urgent",
                     message="You mention threats, violence, police or self-harm. If you or anyone is in danger, "
                             "contact local emergency services or a trusted person now, and speak to a lawyer. "
                             "This tool only gives general legal information.")]
    return []


def triage(llm: LLM, user_text: str) -> Triage:
    # Try keyword-based fast path first
    fast = _keyword_triage(user_text)
    if fast:
        return fast

    pbs = load_all_playbooks()
    menu = "\n".join(f"- {p.id}: {p.title} (keywords: {', '.join(p.triggers)})" for p in pbs.values())
    prompt = (
        f"Playbooks:\n{menu}\n"
        "- general: purely informational question, no personal problem\n"
        "- none: completely unrelated\n\n"
        f"User message:\n{user_text}\n\n"
        "Return JSON: language (en|hi|hinglish|other), playbook (id or general or none), "
        "english_query (short phrase), out_of_scope_reason (empty unless none)."
    )
    try:
        t = llm.ask_json(prompt, Triage, system="Classify legal-help requests. Return JSON only.")
    except LLMTimeoutError:
        return Triage(playbook="none", language="en",
                      out_of_scope_reason="I'm having trouble right now. Could you describe your problem in simple English?")
    if t.playbook not in {**pbs, "general": None}:
        t.playbook = "none"
    return t
