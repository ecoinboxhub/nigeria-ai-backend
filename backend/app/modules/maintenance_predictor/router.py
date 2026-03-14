from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.modules.maintenance_predictor.schemas import EquipmentInput, MaintenancePrediction
from app.modules.maintenance_predictor.service import predict_maintenance

router = APIRouter()


@router.post('/predict', response_model=MaintenancePrediction, dependencies=[Depends(require_role([Role.ADMIN, Role.PM, Role.ANALYST]))])
def predict_maintenance_endpoint(payload: EquipmentInput) -> MaintenancePrediction:
    return predict_maintenance(payload)
