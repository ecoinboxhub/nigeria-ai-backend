import logging
from app.modules.tender_analyzer.schemas import TenderInput, TenderOutput, TenderRisk

logger = logging.getLogger(__name__)

RISK_MAP = {
    "liquidated damages": ("High penalty exposure", "high", 0.87),
    "unrealistic timeline": ("Schedule risk", "high", 0.84),
    "advance payment bond": ("Cash flow constraint", "medium", 0.78),
    "currency fluctuation": ("FX risk", "medium", 0.76),
    "termination for convenience": ("Termination risk", "high", 0.82),
}


def analyze_tender(payload: TenderInput) -> TenderOutput:
    text = payload.text.lower()
    risks: list[TenderRisk] = []

    for token, (name, level, confidence) in RISK_MAP.items():
        if token in text:
            risks.append(TenderRisk(risk=name, level=level, confidence=confidence))

    if not risks:
        risks.append(TenderRisk(risk="No major risk phrase detected", level="low", confidence=0.62))

    summary = " ".join([r.risk for r in risks])
    return TenderOutput(tender_id=payload.tender_id, risks=risks, summary=summary)
