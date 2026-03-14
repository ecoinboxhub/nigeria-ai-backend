from pydantic import BaseModel, ConfigDict, Field


class CostEstimateInput(BaseModel):
    area_sqm: float = Field(gt=0)
    floors: int = Field(gt=0)
    complexity_index: float = Field(ge=0.5, le=2.0)
    labor_cost_index: float = Field(ge=0.5, le=2.0)
    materials_cost_index: float = Field(ge=0.5, le=2.5)


class CostEstimateResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    estimated_cost_ngn: float
    model_family: str
    target_mape: float = 0.1
