from core.llm import get_llm
from core.notice import analyze_notice

text = ("Advocate R. Sharma, Delhi. Notice dated 3 June 2026. My client Mr Verma issued you a cheque for Rs 50,000 "
        "which was dishonoured. You are called upon to pay within 15 days of receipt of this notice, failing which a "
        "complaint under Section 138 of the Negotiable Instruments Act, 1881 will be filed.")
a = analyze_notice(get_llm(), text, {"notice_receipt_date": "2026-11-01"})
print(a.model_dump_json(indent=2))