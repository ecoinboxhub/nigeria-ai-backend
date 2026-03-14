from pydantic import BaseModel, ConfigDict, Field


class SafetyLogInput(BaseModel):
    project_id: str
    city: str = "Lagos"
    log_text: str = Field(min_length=10)


class HazardFinding(BaseModel):
    hazard: str
    severity: str
    confidence: float
    regulation_reference: str = ""
    recommended_action: str = ""


class SafetyAnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: str
    findings: list[HazardFinding]
    recall_target: float = 0.8
