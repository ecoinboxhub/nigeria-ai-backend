from pydantic import BaseModel, ConfigDict, Field


class DocumentInput(BaseModel):
    title: str
    text: str = Field(min_length=50)


class ClauseExtraction(BaseModel):
    clause: str
    present: bool
    comment: str
    confidence: float = 0.7


class DocumentAnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    title: str
    clauses: list[ClauseExtraction]
    compliance_score: float
