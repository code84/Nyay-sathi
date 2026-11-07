import json, types
import pytest
from fastapi.testclient import TestClient
from app import deps
from app.main import app
from core.llm import FakeLLM

TRIAGE = json.dumps({"language": "en", "playbook": "refund", "english_query": "refund refused"})
EXT = json.dumps({"facts": {"seller_name": {"value": "ShopX", "evidence_quote": "ShopX"}}})
NOTICE = ("Advocate R. Sharma. Notice dated 3 June 2026. You issued a cheque for Rs 50,000 which was dishonoured. "
          "Pay within 15 days of receipt of this notice failing which a complaint under Section 138 of the Negotiable Instruments Act, 1881 will be filed.")
def q(v, quote): return {"value": v, "quote": quote}
NEXT = json.dumps({"notice_type": "cheque_bounce", "sender": q("Advocate R. Sharma", "Advocate R. Sharma"),
                   "notice_date": q("2026-06-03", "3 June 2026"), "amount": q("50000", "Rs 50,000"),
                   "deadline": q("15 days", "Pay within 15 days of receipt of this notice"),
                   "laws_cited": [q("Section 138", "Section 138 of the Negotiable Instruments Act, 1881")]})
ANS = json.dumps({"text": "The notice says you must pay within 15 days of receiving it [N-002].",
                  "citations": [{"item_id": "N-002", "quote": "within fifteen days of the receipt of the said notice"}], "confidence": "library"})

@pytest.fixture(autouse=True)
def clean():
    deps._hits.clear(); app.dependency_overrides.clear(); yield; app.dependency_overrides.clear()

def client(replies=()):
    app.dependency_overrides[deps.get_llm_dep] = lambda: FakeLLM(list(replies))
    return TestClient(app, raise_server_exceptions=False)

def test_health():
    assert client().get("/health").json() == {"status": "ok"}

def test_chat_first_turn_asks_questions():
    r = client([TRIAGE, EXT]).post("/chat", json={"message": "ShopX refused my refund"})
    j = r.json()
    assert r.status_code == 200 and j["route"] == "case" and len(j["questions"]) == 2 and j["case"]["facts"]["seller_name"]["value"] == "ShopX"

def test_chat_validation():
    c = client()
    assert c.post("/chat", json={"message": ""}).status_code == 422
    assert c.post("/chat", json={"message": "x" * 4001}).status_code == 422
    assert c.post("/chat", json={"message": "hi", "case": {"playbook_id": "nope"}}).status_code == 400

def test_notice_analyze():
    r = client([NEXT, ANS]).post("/notice/analyze", json={"text": NOTICE, "user_facts": {"notice_receipt_date": "2026-06-05"}})
    j = r.json()
    assert r.status_code == 200 and j["playbook_id"] == "notice_cheque_bounce" and j["answer"]["confidence"] == "library"
    assert any(d["due_date"] == "2026-06-20" for d in j["deadlines"])
    assert client().post("/notice/analyze", json={"text": "short"}).status_code == 422

def test_draft_endpoints_and_export():
    c = client()
    case = {"playbook_id": "refund", "facts": {"seller_name": {"value": "ShopX", "evidence_quote": "ShopX"}}}
    d = c.post("/draft/demand", json=case).json()
    assert "ShopX" in d["text"] and "order_date" in d["blanks"]
    assert c.post("/draft/demand", json={"playbook_id": "notice_cheque_bounce"}).status_code == 400
    p = c.post("/export", json={"title": "Demand notice", "text": d["text"]})
    assert p.status_code == 200 and p.content[:4] == b"%PDF" and p.headers["content-type"] == "application/pdf"
    assert c.post("/export", json={"text": "नमस्ते hello"}).status_code == 200      # Hindi must not crash the PDF

def test_playbooks_and_sources():
    c = client()
    assert {p["id"] for p in c.get("/playbooks").json()} >= {"refund", "notice_cheque_bounce"}
    s = c.get("/sources/C-005").json()
    assert s["id"] == "C-005" and s["source_url"] and s["excerpt"]
    assert c.get("/sources/ZZ-999").status_code == 404

def test_rate_limit(monkeypatch):
    monkeypatch.setattr(deps, "settings", types.SimpleNamespace(rate_limit_per_min=2))
    c = client()
    assert [c.get("/playbooks").status_code for _ in range(3)] == [200, 200, 429]

def test_model_failures_are_friendly():
    r = client([]).post("/chat", json={"message": "hello there"})          # fake model has no replies -> error
    assert r.status_code == 503 and "temporarily unavailable" in r.json()["detail"] and "Error" not in r.text
    r = client(["not json", "still not json"]).post("/chat", json={"message": "hello there"})
    assert r.status_code == 502

def test_cors():
    c = client()
    ok = c.options("/chat", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    bad = c.options("/chat", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "access-control-allow-origin" not in bad.headers
