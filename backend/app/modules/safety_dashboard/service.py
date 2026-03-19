import logging
from pathlib import Path

from langchain_core.prompts import PromptTemplate

from app.core.config import settings
from app.modules.safety_dashboard.schemas import HazardFinding, SafetyAnalysisResponse, SafetyLogInput
from app.services.rag.engine import get_llm_chain, get_vectorstore
from app.services.weather_service import weather_service
from app.utils.security_utils import sanitize_input_text

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """Context: {context}

Log: {log_text}
Weather: {rainfall_mm}mm, {temperature_c}°C, {wind_speed_kmh}km/h

Analyze for safety hazards and risks."""

SAFETY_PROMPT = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "log_text", "rainfall_mm", "temperature_c", "wind_speed_kmh"],
)

KEYWORDS = {
    "helmet": ("PPE violation", "high", "COREN Act 2018", "Enforce hard-hat compliance immediately."),
    "scaffold": ("Scaffold risk", "medium", "ILO Construction Safety", "Inspect scaffold integrity and tags."),
    "electrical": ("Electrical hazard", "high", "ILO Construction Safety", "Isolate power and secure wiring."),
    "spill": ("Slip hazard", "medium", "COREN Act 2018", "Clean spill and place warning signage."),
    "unguarded": ("Machine guarding issue", "high", "ILO Construction Safety", "Install guards before operation."),
}


def _rag_assist(log_text: str, weather: dict) -> str:
    try:
        persist_dir = Path(settings.chroma_persist_dir) / "safety_dashboard"
        persist_dir.mkdir(parents=True, exist_ok=True)
        vectordb = get_vectorstore(str(persist_dir), collection_name="safety_dashboard")
        chain = get_llm_chain(SAFETY_PROMPT, vectordb, k=5)
        query = (
            f"Log: {log_text}\n"
            f"Weather: rainfall: {weather.get('rainfall_mm', 0)}mm, "
            f"temperature: {weather.get('temperature_c', 30)}C, "
            f"wind: {weather.get('wind_speed_kmh', 0)}km/h"
        )
        out = chain.invoke({"query": query})
        if isinstance(out, dict):
            return str(out.get("result", ""))
        return str(out)
    except Exception as e:
        logger.error(f"RAG assistance failed in safety_dashboard: {e}")
        # Keep endpoint available even if local LLM/Chroma fails.
        return ""


def analyze_safety_log(payload: SafetyLogInput) -> SafetyAnalysisResponse:
    clean_text = sanitize_input_text(payload.log_text.lower())
    weather = weather_service.fetch_city_weather(payload.city)
    rag_hint = _rag_assist(clean_text, weather)

    findings: list[HazardFinding] = []
    for token, info in KEYWORDS.items():
        if token in clean_text:
            findings.append(
                HazardFinding(
                    hazard=info[0],
                    severity=info[1],
                    confidence=0.82,
                    regulation_reference=info[2],
                    recommended_action=f"{info[3]} {rag_hint[:80]}".strip(),
                )
            )

    if not findings:
        findings.append(
            HazardFinding(
                hazard="No critical hazard detected",
                severity="low",
                confidence=0.61,
                regulation_reference="ILO Construction Safety",
                recommended_action="Continue monitoring and daily toolbox talk.",
            )
        )

    return SafetyAnalysisResponse(project_id=payload.project_id, findings=findings)
