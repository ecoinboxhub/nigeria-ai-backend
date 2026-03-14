from pydantic import BaseModel, ConfigDict, Field


class DelayInput(BaseModel):
    rainfall_mm: float = Field(ge=0)
    temperature_c: float
    wind_speed_kmh: float = Field(ge=0)
    resource_availability: float = Field(ge=0, le=1)
    workforce_attendance: float = Field(ge=0, le=1)
    supply_delay_days: int = Field(ge=0)
    city: str = "Lagos"


class DelayPrediction(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    delay_risk: float
    will_delay: bool
    model_stack: list[str]
