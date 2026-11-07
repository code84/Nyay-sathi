from core.llm import get_llm
from core.schemas import NoticeExtract

llm = get_llm()
text = "Notice dated 3 June 2026 from Mr Sharma: pay Rs 50,000 within 15 days of receipt."
out = llm.ask_json(
    "Return JSON with these fields: notice_type, sender{value,quote}, "
    "amount{value,quote}, deadline{value,quote}. Text: " + text,
    NoticeExtract,
)
print(out.model_dump_json(indent=2))

print(llm.ask("मेरा मकान मालिक डिपॉज़िट वापस नहीं कर रहा। एक वाक्य में बताओ कि पहला कदम क्या है?"))