from pydantic import BaseModel, Field


class EquipmentInput(BaseModel):
    equipment_type: str
    runtime_hours: float = Field(ge=0)
    vibration_index: float = Field(ge=0)
    temperature_c: float
    last_maintenance_days: int = Field(ge=0)


class MaintenancePrediction(BaseModel):
    failure_risk: float
    maintenance_due_in_days: int
