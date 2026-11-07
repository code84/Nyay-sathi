from datetime import date
from core.engine import load_playbook, load_all_playbooks, missing_library_refs
from core.rules import compute_deadlines, evaluate_flags, forum_for

T = date(2026, 11, 7)
def D(pb, facts, today=T):
    return {d.rule_id: d for d in compute_deadlines(load_playbook(pb), facts, today)}

def test_playbooks_load_and_refs_exist():
    pbs = load_all_playbooks()
    assert set(pbs) == {"refund", "notice_cheque_bounce", "notice_loan_recovery", "notice_general_demand"}
    for pb in pbs.values():
        assert missing_library_refs(pb) == [], pb.id

def test_refund_two_years():
    d = D("refund", {"refusal_date": "2026-06-01"})["complaint_limitation"]
    assert d.due_date == date(2028, 6, 1) and d.status == "ok" and d.approximate

def test_cheque_chain():
    d = D("notice_cheque_bounce", {"bank_info_date": "2026-10-01", "notice_receipt_date": "2026-10-10"})
    assert d["payee_notice_deadline"].due_date == date(2026, 10, 31)
    assert d["drawer_payment_window"].due_date == date(2026, 10, 25)
    assert d["complaint_deadline"].due_date == date(2026, 11, 25)
    assert d["drawer_payment_window"].status == "overdue"
    assert d["complaint_deadline"].status == "ok"

def test_month_end_clamps():
    d = D("notice_cheque_bounce", {"notice_receipt_date": "2026-01-16"})   # window ends Jan 31
    assert d["complaint_deadline"].due_date == date(2026, 2, 28)

def test_missing_fact_asks_for_it():
    d = D("notice_cheque_bounce", {})
    assert d["drawer_payment_window"].status == "needs_fact" and d["drawer_payment_window"].missing == "notice_receipt_date"
    assert d["complaint_deadline"].status == "needs_fact" and d["complaint_deadline"].missing == "notice_receipt_date"

def test_sender_deadline_from_fact():
    d = D("notice_general_demand", {"notice_receipt_date": "2026-11-01", "stated_days": 15})["sender_deadline"]
    assert d.due_date == date(2026, 11, 16) and d.status == "ok"
    assert D("notice_general_demand", {"notice_receipt_date": "2026-11-01"})["sender_deadline"].missing == "stated_days"

def test_drt_45_days_and_flags():
    pb = load_playbook("notice_loan_recovery")
    facts = {"measure_date": "2026-09-30", "possession_or_auction_notice": True}
    ds = compute_deadlines(pb, facts, T)
    drt = next(x for x in ds if x.rule_id == "drt_application")
    assert drt.due_date == date(2026, 11, 14) and drt.status == "due_soon"
    codes = {f.code for f in evaluate_flags(pb, facts, ds)}
    assert {"possession_or_auction", "deadline_close"} <= codes
    assert any(f.code == "deadline_close" and f.severity == "urgent" for f in evaluate_flags(pb, facts, ds))

def test_overdue_is_urgent():
    pb = load_playbook("refund")
    ds = compute_deadlines(pb, {"refusal_date": "2024-01-01"}, T)
    fl = evaluate_flags(pb, {"refusal_date": "2024-01-01"}, ds)
    assert any(f.code == "deadline_overdue" and f.severity == "urgent" for f in fl)

def test_unsecured_loan_warning():
    pb = load_playbook("notice_loan_recovery")
    assert any(f.code == "not_secured" for f in evaluate_flags(pb, {"is_secured_loan": False}, []))

def test_forum_tiers():
    pb = load_playbook("refund")
    f = lambda a: forum_for(pb, {"amount": a})["forum"]
    assert f(20000) == "District Commission" and f(5_000_000) == "District Commission"
    assert f(5_000_001) == "State Commission" and f(20_000_001) == "National Commission"
    assert forum_for(pb, {}) is None
