import json
from datetime import date
from core.drafts import reply_draft
from core.extractor import extract_notice
from core.llm import FakeLLM
from core.notice import analyze_notice, _days_from
from core.scam_check import scam_check

T = date(2026, 11, 7)
NOTICE = ("Advocate R. Sharma, Delhi. Notice dated 3 June 2026. My client Mr Verma issued you a cheque for Rs 50,000 which was "
          "dishonoured. You are called upon to pay within 15 days of receipt of this notice, failing which a complaint under "
          "Section 138 of the Negotiable Instruments Act, 1881 and Section 420 of the Indian Penal Code will be filed.")

G_ANS = json.dumps({"text": "A claim filed after the time limit has to be dismissed [G-001].",
                    "citations": [{"item_id": "G-001", "quote": "shall be dismissed, although limitation has not been set up as a defence"}],
                    "confidence": "library"})

def q(v, quote): return {"value": v, "quote": quote}
def EX(**over):
    d = {"notice_type": "cheque_bounce", "sender": q("Advocate R. Sharma", "Advocate R. Sharma"),
         "notice_date": q("2026-06-03", "3 June 2026"), "demand": q("Pay Rs 50,000", "pay within 15 days of receipt of this notice"),
         "amount": q("50000", "Rs 50,000"), "deadline": q("15 days", "within 15 days of receipt of this notice"),
         "laws_cited": [q("Section 138 NI Act", "Section 138 of the Negotiable Instruments Act, 1881"),
                        q("Section 420 IPC", "Section 420 of the Indian Penal Code")],
         "consequence": q("complaint will be filed", "a complaint under Section 138")}
    d.update(over); return json.dumps(d)
ANS = json.dumps({"text": "The notice says you must pay within 15 days of receiving it [N-002].",
                  "citations": [{"item_id": "N-002", "quote": "within fifteen days of the receipt of the said notice"}], "confidence": "library"})

def test_extraction_drops_invented_quote_and_bad_values():
    # amount quote "Rs 90,000" not in NOTICE (which says Rs 50,000) — dropped
    # notice_date value "N/A" cannot be coerced to date — dropped
    bad = EX(amount=q("90000", "Rs 90,000"), notice_date=q("N/A", "3 June 2026"))
    ex, dropped = extract_notice(FakeLLM([bad]), NOTICE)
    assert ex.amount.value is None and ex.notice_date.value is None
    assert {"amount", "notice_date"} <= set(dropped) and ex.sender.value == "Advocate R. Sharma"

def test_good_extraction_normalises():
    ex, dropped = extract_notice(FakeLLM([EX()]), NOTICE)
    assert ex.amount.value == "50000" and ex.notice_date.value == "2026-06-03" and len(ex.laws_cited) == 2 and dropped == []

def test_scam_detects_signals_with_quotes():
    r = scam_check("Pay Rs 5000 by UPI to this QR code or face digital arrest. Share your OTP now. CBI notice.")
    codes = {s.code for s in r.signals}
    assert r.risk == "high" and {"upi_or_wallet_payment", "arrest_threat", "asks_sensitive_info", "agency_name"} <= codes
    assert all(s.quote for s in r.signals)

def test_genuine_looking_notice_is_not_high():
    assert scam_check(NOTICE).risk == "none"

def test_days_from():
    assert _days_from("within fifteen days of receipt") == 15 and _days_from("within 7 days") == 7 and _days_from("soon") is None

def test_full_cheque_analysis():
    a = analyze_notice(FakeLLM([EX(), ANS]), NOTICE, {"notice_receipt_date": "2026-06-05"}, today=T)
    assert a.playbook_id == "notice_cheque_bounce" and a.answer.confidence == "library"
    d = {x.rule_id: x for x in a.deadlines}
    assert d["drawer_payment_window"].due_date == date(2026, 6, 20) and d["complaint_deadline"].due_date == date(2026, 7, 20)
    lm = {m.quote: m for m in a.law_matches}
    assert lm["Section 138 of the Negotiable Instruments Act, 1881"].verified
    assert not lm["Section 420 of the Indian Penal Code"].verified
    assert any(f.code == "law_not_in_library" and "420" in f.message for f in a.flags)
    assert a.ask and a.ask[0].fact == "court_summons_received"      # the receipt date was already given

def test_asks_for_receipt_date_when_missing():
    a = analyze_notice(FakeLLM([EX(), ANS]), NOTICE, {}, today=T)
    assert [f.fact for f in a.ask][0] == "notice_receipt_date" and a.ask[0].kind == "date"
    assert next(x for x in a.deadlines if x.rule_id == "drawer_payment_window").status == "needs_fact"

def test_unknown_notice_type():
    a = analyze_notice(FakeLLM([EX(notice_type="unknown")]), NOTICE, today=T)
    assert a.playbook_id == "unknown" and a.answer is None and "lawyer" in a.message and a.scam is not None

def test_general_demand_gets_sender_deadline():
    g = EX(notice_type="general_demand", laws_cited=[])
    a = analyze_notice(FakeLLM([g, G_ANS]), NOTICE, {"notice_receipt_date": "2026-11-01"}, today=T)
    assert next(x for x in a.deadlines if x.rule_id == "sender_deadline").due_date == date(2026, 11, 16)

def test_reply_draft_blanks():
    a = analyze_notice(FakeLLM([EX(), ANS]), NOTICE, {"notice_receipt_date": "2026-06-05"}, today=T)
    text, blanks = reply_draft(a.case)
    assert "Advocate R. Sharma" in text and "3 June 2026" in text and "5 June 2026" in text
    assert "[___ write your position" in text and "{{" not in text
