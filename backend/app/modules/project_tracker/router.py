from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.modules.project_tracker.schemas import DelayInput, DelayPrediction
from app.modules.project_tracker.service import predict_delay

router = APIRouter()


@router.post('/predict-delay', response_model=DelayPrediction, dependencies=[Depends(require_role([Role.ADMIN, Role.PM, Role.ANALYST]))])
def predict_delay_endpoint(payload: DelayInput) -> DelayPrediction:
    return predict_delay(payload)
