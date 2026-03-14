from pydantic import BaseModel, Field


class WorkerGroup(BaseModel):
    role: str
    required: int = Field(ge=1)
    available: int = Field(ge=0)


class WorkforceRequest(BaseModel):
    shift_hours: int = Field(default=8, ge=4, le=12)
    groups: list[WorkerGroup]


class WorkforceAllocation(BaseModel):
    role: str
    allocated: int
    utilization: float


class WorkforceResponse(BaseModel):
    schedule: list[WorkforceAllocation]
    idle_rate: float
    optimization_method: str = "greedy"
