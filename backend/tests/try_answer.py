from core.llm import get_llm
from core.retriever import retrieve
from core.answer import grounded_answer

q = "A seller refused my refund of Rs 20000. Where can I complain and how long do I have?"
items = retrieve("refund complaint where to file time limit", "refund")
a = grounded_answer(get_llm(), q, items, case_text="refund Rs 20000")
print(a.text)
print(a.confidence)
print([f.code for f in a.flags])