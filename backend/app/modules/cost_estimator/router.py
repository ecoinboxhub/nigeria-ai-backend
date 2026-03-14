from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.modules.cost_estimator.schemas import CostEstimateInput, CostEstimateResponse
from app.modules.cost_estimator.service import estimate_cost

router = APIRouter()


@router.post('/estimate', response_model=CostEstimateResponse, dependencies=[Depends(require_role([Role.ADMIN, Role.PM, Role.ANALYST]))])
def estimate_cost_endpoint(payload: CostEstimateInput) -> CostEstimateResponse:
    return estimate_cost(payload)
