from pydantic import BaseModel, ConfigDict, Field


class ProgressInput(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    planned_completion_pct: float = Field(ge=0, le=100)
    detected_completion_pct: float | None = Field(default=None, ge=0, le=100)
    image_base64: str | None = None


class DetectedObject(BaseModel):
    label: str
    confidence: float
    bbox: list[float]


class ProgressOutput(BaseModel):
    deviation_pct: float
    exceeds_threshold: bool
    threshold_pct: float = 15.0
    detected_objects: list[DetectedObject] = Field(default_factory=list)
    ppe_compliance_score: float = 0.0
    detected_completion_pct: float = 0.0
