from core.library import load_library
from core.llm import FakeLLM
from core.schemas import NoticeExtract
from pathlib import Path

def test_library_loads():
    lib = load_library()
    assert len(lib) >= 29
    for item in lib.values():
        assert item.excerpt and item.meaning and item.limits, item.id
        if item.source_pdf:
            assert (Path("library").parent / item.source_pdf).exists(), item.id

def test_ask_json_retries():
    llm = FakeLLM(["not json", '{"notice_type": "cheque_bounce"}'])
    out = llm.ask_json("x", NoticeExtract)
    assert out.notice_type == "cheque_bounce"