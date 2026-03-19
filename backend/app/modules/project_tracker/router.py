from fastapi import APIRouter, Depends
from app.core.rbac import Role, require_role
from app.modules.project_tracker.schemas import DelayInput, DelayPrediction, ProjectSchema
from app.modules.project_tracker.service import predict_delay, list_projects

router = APIRouter()

@router.get("/", response_model=list[ProjectSchema], dependencies=[Depends(require_role([Role.ADMIN, Role.PM, Role.ANALYST, Role.USER]))])
def get_projects_endpoint() -> list[ProjectSchema]:
    return list_projects()

@router.get("/weather/{city}", dependencies=[Depends(require_role([Role.ADMIN, Role.PM, Role.ANALYST, Role.USER]))])
def get_weather_endpoint(city: str):
    from app.services.weather_service import weather_service
    return weather_service.fetch_city_weather(city)

@router.post('/predict-delay', response_model=DelayPrediction, dependencies=[Depends(require_role([Role.ADMIN, Role.PM, Role.ANALYST]))])
def predict_delay_endpoint(payload: DelayInput) -> DelayPrediction:
    return predict_delay(payload)
