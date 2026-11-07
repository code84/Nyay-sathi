from datetime import date
import re
from typing import Literal, Optional
from pydantic import BaseModel, Field
from .answer import grounded_answer
from .case_builder import update_case, case_values, case_text, next_questions
from .engine import load_playbook
from .llm import LLM
from .retriever import retrieve
from .rules import DeadlineResult, compute_deadlines, evaluate_flags, forum_for
from .schemas import Answer, CaseFile, Flag
from .triage import danger_flags, triage

LANGS = {"en": "English", "hi": "Hindi", "hinglish": "English", "other": "English"}

_GREETING = re.compile(
    r"^\s*(hi+|hello+|hey+|hola|howdy|good\s*(morning|evening|afternoon|day)|नमस्ते|नमस्कार|प्रणाम)[!?,.\s]*$",
    re.I | re.U,
)
_OFF_TOPIC = re.compile(
    r"\b(today'?s?\s*date|what\s*(day|date|time|is\s*today)|current\s*date|date\s*today|"
    r"aaj\s*(kya|ka)|kitne\s*baje|time\s*kya)\b",
    re.I | re.U,
)
_DISTRESSED = re.compile(
    r"\b(preshan|pareshan|tension|worried|scared|help\s*me|kya\s*kar(u|un|oon)|"
    r"dar\s*(lag|raha)|afraid|stress|please\s*help|bahut\s*(problem|mushkil)|"
    r"what\s*do\s*i\s*do|samajh\s*nahi\s*aa|don'?t\s*know\s*what\s*to\s*do|"
    r"ghabra|nervous|upset|ro\s*raha|ro\s*rahi)\b",
    re.I | re.U,
)
_URGENT = re.compile(
    r"\b(urgent|immediately|jaldi|abhi|aaj\s*hi|today\s*itself|deadline|"
    r"notice\s*mila|kal\s*tak|by\s*tomorrow|last\s*date|expire|running\s*out)\b",
    re.I | re.U,
)
_CONFUSED = re.compile(
    r"\b(confused|samajh\s*nahi|don'?t\s*understand|kya\s*matlab|"
    r"what\s*does\s*(it|this)\s*mean|matlab\s*kya\s*hai|explain|"
    r"not\s*sure\s*what|mujhe\s*nahi\s*pata)\b",
    re.I | re.U,
)


def _detect_tone(text: str) -> str:
    if _DISTRESSED.search(text):
        return "distressed"
    if _URGENT.search(text):
        return "urgent"
    if _CONFUSED.search(text):
        return "confused"
    return "calm"


_NOTICE_GREET = {
    "notice_cheque_bounce": (
        "I'm sorry you're dealing with a cheque bounce situation — that can be really stressful. "
        "I can help you understand your rights and next steps.\n\n"
        "To give you the most useful information, could you tell me a bit more about what happened? "
        "For example: did your cheque get returned by the bank, or did you receive a legal notice from someone whose cheque bounced? "
        "If you already have a written legal notice, you can paste its text here and I will analyse it for you."
    ),
    "notice_loan_recovery": (
        "I understand — a loan recovery notice can feel overwhelming. I'm here to help.\n\n"
        "Could you tell me more about your situation? "
        "For example: did you receive a written notice from your bank or lender? "
        "If you have the notice with you, paste its text here and I'll break it down for you. "
        "Or just describe what's happening and we'll go from there."
    ),
    "notice_general_demand": (
        "I see you've received some kind of demand or payment notice — let's work through it together.\n\n"
        "Could you describe what happened, or paste the text of the notice if you have it? "
        "The more you share, the better I can help."
    ),
}

GREETING_REPLY_EN = ("Hello! I'm Nyay Saathi, your legal-information assistant. "
                     "I can help you with refund problems, cheque bounce notices, and loan recovery notices. "
                     "What's going on? Feel free to describe your situation in your own words.")
GREETING_REPLY_HI = ("नमस्ते! मैं न्याय साथी हूँ। मैं आपकी रिफंड, चेक बाउंस या लोन वसूली की समस्याओं में मदद कर सकता हूँ। "
                     "बताइए, आपकी क्या परेशानी है?")


class TurnResult(BaseModel):
    route: Literal["case", "notice", "none"] = "case"
    case: Optional[CaseFile] = None
    questions: list[str] = Field(default_factory=list)
    ready: bool = False
    deadlines: list[DeadlineResult] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)
    forum: Optional[dict] = None
    answer: Optional[Answer] = None
    message: str = ""


def _conversational_answer(text: str) -> Answer:
    return Answer(text=text, citations=[], flags=[], confidence="general")


def case_turn(llm: LLM, case: Optional[CaseFile], user_message: str,
              today: Optional[date] = None, answer_now: bool = False) -> TurnResult:
    today = today or date.today()
    flags = danger_flags(user_message)

    # Handle greetings — respond warmly and reset conversation regardless of prior case state
    if _GREETING.match(user_message.strip()):
        lang = case.language if case else "en"
        reply = GREETING_REPLY_HI if lang == "hi" else GREETING_REPLY_EN
        return TurnResult(route="none", flags=flags, answer=_conversational_answer(reply))

    # Handle off-topic questions (e.g. "do you know today's date?")
    if _OFF_TOPIC.search(user_message):
        reply = (f"Today's date is {today.strftime('%d %B %Y').lstrip('0')}. "
                 + ("Is there anything about your legal situation I can help you with?"
                    if case is None else "Now, back to your case — "))
        if case is None:
            return TurnResult(route="none", flags=flags,
                              answer=_conversational_answer(reply))

    # Detect user's emotional tone — passed to the LLM to frame the answer accordingly
    tone = _detect_tone(user_message)

    if case is None:                                   # first message: decide which playbook
        t = triage(llm, user_message)

        # General informational question — skip case building, answer directly
        if t.playbook == "general":
            items = retrieve(t.english_query or user_message)
            answer = grounded_answer(llm, user_message, items,
                                     language=LANGS.get(t.language, "English"),
                                     is_general=True, user_tone=tone)
            return TurnResult(route="none", flags=flags, answer=answer)

        if t.playbook == "none":
            return TurnResult(route="none", flags=flags, message=t.out_of_scope_reason or
                              "I can currently help with refund problems and with understanding legal notices only.")
        if load_playbook(t.playbook).type == "document":
            msg = _NOTICE_GREET.get(t.playbook,
                "I can help with that. Could you tell me more about your situation, "
                "or paste the text of any legal notice you've received?")
            return TurnResult(route="notice", flags=flags, answer=_conversational_answer(msg))
        case = CaseFile(playbook_id=t.playbook, language=t.language, english_query=t.english_query)

    pb = load_playbook(case.playbook_id)
    case = update_case(llm, case, user_message, pb, today)
    facts = case_values(case)
    deadlines = compute_deadlines(pb, facts, today)
    flags += evaluate_flags(pb, facts, deadlines)
    ready = not case.missing
    answer = None
    if ready or answer_now:
        items = retrieve(case.english_query or pb.title, pb.id)
        q = user_message if answer_now else "Based on my case facts, explain in plain language where I stand and what my options are."
        answer = grounded_answer(llm, q, items, case_text=case_text(case),
                                 language=LANGS.get(case.language, "English"),
                                 is_general=False, user_tone=tone)
    return TurnResult(case=case, questions=[] if ready else next_questions(case, pb), ready=ready,
                      deadlines=deadlines, flags=flags, forum=forum_for(pb, facts), answer=answer)
