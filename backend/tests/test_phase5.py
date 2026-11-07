import json
from datetime import date
from core.case_builder import update_case, next_questions, _coerce
from core.drafts import demand_notice, inr
from core.engine import load_playbook
from core.flow import case_turn
from core.llm import FakeLLM
from core.schemas import CaseFile, Fact
from core.triage import danger_flags

T = date(2026, 11, 7)
MSG = "I bought a phone from ShopX for Rs 20,000. It was defective and on 1 June 2026 they refused my refund."

def ext(**facts): return json.dumps({"facts": {k: {"value": v[0], "evidence_quote": v[1]} for k, v in facts.items()}})
GOOD = ext(seller_name=("ShopX", "ShopX"), amount=("20000", "Rs 20,000"), issue=("defective phone", "It was defective"),
           refusal_date=("2026-06-01", "1 June 2026"))
TRIAGE = json.dumps({"language": "en", "playbook": "refund", "english_query": "refund refused defective phone complaint"})
ANSWER = json.dumps({"text": "You generally have two years to file a complaint [C-005].",
                     "citations": [{"item_id": "C-005", "quote": "within two years from the date on which the cause of action has arisen"}],
                     "confidence": "library"})

def fresh(): return CaseFile(playbook_id="refund")

def test_extraction_keeps_real_facts():
    c = update_case(FakeLLM([GOOD]), fresh(), MSG, load_playbook("refund"), T)
    assert c.facts["amount"].value == 20000.0 and c.facts["refusal_date"].value == "2026-06-01" and c.missing == []

def test_invented_fact_is_dropped():
    bad = ext(seller_name=("ShopX", "ShopX"), amount=("50000", "Rs 50,000"))   # quote is not in the message
    c = update_case(FakeLLM([bad]), fresh(), MSG, load_playbook("refund"), T)
    assert "amount" not in c.facts and "seller_name" in c.facts and "amount" in c.missing

def test_bad_types_are_dropped():
    bad = ext(amount=("1.5 lakh", "Rs 20,000"), refusal_date=("June 1", "1 June 2026"))
    c = update_case(FakeLLM([bad]), fresh(), MSG, load_playbook("refund"), T)
    assert "amount" not in c.facts and "refusal_date" not in c.facts

def test_unknown_fact_name_ignored():
    c = update_case(FakeLLM([ext(favourite_colour=("red", "ShopX"))]), fresh(), MSG, load_playbook("refund"), T)
    assert c.facts == {}

def test_coerce():
    assert _coerce("number", "Rs. 20,000") == 20000.0 and _coerce("number", "1.5 lakh") is None
    assert _coerce("bool", "yes") is True and _coerce("date", "2026-02-30") is None

def test_questions_in_hindi_and_limit():
    c = CaseFile(playbook_id="refund", language="hi", missing=["amount", "issue", "refusal_date"])
    qs = next_questions(c, load_playbook("refund"))
    assert len(qs) == 2 and "रुपये" in qs[0]

def test_inr_format():
    assert inr(20000) == "Rs 20,000" and inr(2000000) == "Rs 20,00,000" and inr(100000) == "Rs 1,00,000" and inr(999) == "Rs 999"

def test_draft_has_blanks_not_inventions():
    c = update_case(FakeLLM([GOOD]), fresh(), MSG, load_playbook("refund"), T)
    text, blanks = demand_notice(c)
    assert "ShopX" in text and "Rs 20,000" in text and "1 June 2026" in text
    assert "[___ order date ___]" in text and "[___ payment mode ___]" in text and "[___ seller response ___]" in text
    assert "order_date" in blanks and "your name" in blanks and "{{" not in text

def test_danger_words():
    assert danger_flags("he threatened to kill me") and danger_flags("वह धमकी दे रहा है") and not danger_flags("refund please")

def test_flow_asks_then_answers():
    llm = FakeLLM([TRIAGE, ext(seller_name=("ShopX", "ShopX"))])
    r1 = case_turn(llm, None, "ShopX refused my refund", T)
    assert r1.route == "case" and not r1.ready and r1.answer is None and len(r1.questions) == 2
    llm.replies += [GOOD, ANSWER]
    r2 = case_turn(llm, r1.case, MSG, T)
    assert r2.ready and r2.answer and r2.answer.confidence == "library"
    assert r2.forum["forum"] == "District Commission"
    assert next(d for d in r2.deadlines if d.rule_id == "complaint_limitation").due_date == date(2028, 6, 1)

def test_flow_out_of_scope():
    r = case_turn(FakeLLM([json.dumps({"language": "en", "playbook": "none", "out_of_scope_reason": "divorce"})]), None, "divorce help", T)
    assert r.route == "none" and r.case is None and "divorce" in r.message

def test_flow_notice_route():
    r = case_turn(FakeLLM([json.dumps({"language": "en", "playbook": "notice_cheque_bounce", "english_query": "x"})]), None, "got a cheque notice", T)
    assert r.route == "notice"
