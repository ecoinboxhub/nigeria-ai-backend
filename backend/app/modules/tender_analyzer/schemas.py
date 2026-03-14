from pydantic import BaseModel, Field


class TenderInput(BaseModel):
    tender_id: str
    text: str = Field(min_length=50)


class TenderRisk(BaseModel):
    risk: str
    level: str
    confidence: float


class TenderOutput(BaseModel):
    tender_id: str
    risks: list[TenderRisk]
    summary: str
