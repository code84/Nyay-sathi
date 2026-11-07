import json
from core.answer import grounded_answer, FALLBACK
from core.checker import check, blocking
from core.llm import FakeLLM
from core.retriever import retrieve
from core.schemas import Answer, Citation, LibraryItem

ITEM = LibraryItem(
    id="T-001", title="Time limit to file: two years (s.69)", topic="consumer", applies_to=["refund"],
    source_url="x", source_name="Consumer Protection Act 2019", source_confidence="primary",
    last_verified="2026-11-07", status="VERIFIED",
    excerpt=['s.69(1): "shall not admit a complaint unless it is filed within two years from the date on which the cause of action has arisen"'],
    meaning="Generally you have two years from when the problem arose.", limits="The date can be argued.")
QUOTE = "within two years from the date on which the cause of action has arisen"

def ans(text, quote=QUOTE, cid="T-001", conf="library"):
    return Answer(text=text, citations=[Citation(item_id=cid, quote=quote)], confidence=conf)

def codes(a): return {f.code for f in blocking(check(a, [ITEM]))}

def test_good_answer_passes():
    assert codes(ans("You generally have two years to file a complaint [T-001].")) == set()
def test_digit_form_of_number_passes():
    assert codes(ans("You generally have 2 years to file [T-001].")) == set()
def test_unknown_citation_tag():
    assert "unknown_citation" in codes(ans("You have two years [X-999]."))
def test_unknown_citation_id():
    assert "unknown_citation" in codes(ans("You have two years [T-001].", cid="X-999"))
def test_fake_quote():
    assert "bad_quote" in codes(ans("Two years [T-001].", quote="within three years from the date"))
def test_invented_section():
    assert "unsupported_section" in codes(ans("Under Section 420 you have two years [T-001]."))
def test_wrong_number():
    assert "unsupported_number" in codes(ans("You have three years to file [T-001]."))
def test_user_number_allowed():
    a = ans("You have two years [T-001].")
    assert not blocking(check(a, [ITEM], allowed_text="I paid Rs 5 lakh last month"))
def test_invented_act_and_case():
    assert "unsupported_act" in codes(ans("The Sale of Goods Act, 1930 applies [T-001]."))
    assert "unsupported_case" in codes(ans("In Sharma v. State of Delhi the court agreed [T-001]."))
def test_uncited_claim_is_warning_only():
    f = check(ans("You must act quickly. You have two years [T-001]."), [ITEM])
    assert any(x.code == "uncited_legal_claim" for x in f) and not blocking(f)

def js(a): return json.dumps(a.model_dump())
def test_retry_then_success():
    bad = ans("You have three years [T-001].")
    good = ans("You generally have two years [T-001].")
    llm = FakeLLM([js(bad), js(good)])
    out = grounded_answer(llm, "how long do I have?", [ITEM])
    assert "two years" in out.text and len(llm.prompts) == 2 and "rejected" in llm.prompts[1]
def test_fallback_after_two_failures():
    bad = js(ans("You have three years [T-001]."))
    out = grounded_answer(FakeLLM([bad, bad]), "how long?", [ITEM])
    assert out.text == FALLBACK and out.confidence == "unsure"

def test_retriever_filters_by_playbook():
    got = retrieve("time limit to file a refund complaint two years", "refund", k=5)
    assert got and all("refund" in i.applies_to for i in got)
    assert "C-005" in [i.id for i in got[:3]]
def test_retriever_notice_playbook():
    got = retrieve("notice 15 days payment cheque dishonour", "notice_cheque_bounce", k=3)
    assert got[0].id.startswith("N-")