"""Rule-based warning signs. These are signs, not proof. Every signal shows the exact words that triggered it."""
import re
from typing import Literal
from pydantic import BaseModel, Field


class ScamSignal(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    quote: str
    why: str


class ScamReport(BaseModel):
    risk: Literal["none", "some", "high"] = "none"
    signals: list[ScamSignal] = Field(default_factory=list)
    note: str = ("These are warning signs, not proof. Before paying or replying, verify the sender through "
                 "a phone number or website you find yourself, not the one in the notice.")


_RULES = [
    ("upi_or_wallet_payment", "high",
     r"\b(upi|qr code|google ?pay|gpay|phonepe|paytm|gift ?cards?|bitcoin|crypto\w*)\b",
     "Payment is asked through UPI, a wallet, gift cards or crypto. Legal notices rarely ask for payment this way."),
    ("arrest_threat", "high",
     r"\b(digital arrest|arrest warrant|will be arrested|arrested immediately|non[- ]bailable)\b|गिरफ्तार",
     "Threatens arrest. A notice from a lawyer or lender cannot arrest anyone."),
    ("asks_sensitive_info", "high",
     r"\b(otp|cvv|atm pin|aadhaar|aadhar|card number|net ?banking password)\b",
     "Asks for an OTP, card or ID details. A genuine notice does not need these."),
    ("very_short_deadline", "medium",
     r"\bwithin\s+(?:24|48|12)\s*hours?\b|\bimmediately\b|\burgent(?:ly)?\b",
     "Pressure to act within hours. Genuine notices usually give days."),
    ("agency_name", "medium",
     r"\b(cbi|enforcement directorate|trai|customs|narcotics|cyber ?crime branch|income tax department)\b",
     "Names a government agency. Confirm through the agency's official office or website."),
    ("personal_email", "low", r"[\w.+-]+@(?:gmail|yahoo|outlook|hotmail|rediffmail)\.\w+",
     "Uses a free personal email address for a legal or official matter."),
]


def scam_check(text: str) -> ScamReport:
    sigs = []
    for code, sev, pat, why in _RULES:
        m = re.search(pat, text, re.I)
        if m:
            sigs.append(ScamSignal(code=code, severity=sev, quote=m.group(0), why=why))
    if not re.search(r"\b(advocate|attorney|lawyer|court|case no|ref(?:erence)?)\b|वकील|अदालत", text, re.I):
        sigs.append(ScamSignal(code="no_lawyer_court_or_case_ref", severity="low", quote="(not found in the text)",
                               why="No lawyer, court or case reference is named."))
    sevs = {s.severity for s in sigs}
    risk = "high" if "high" in sevs else "some" if sigs else "none"
    return ScamReport(risk=risk, signals=sigs)
