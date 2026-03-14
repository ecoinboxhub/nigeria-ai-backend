from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.modules.workforce_scheduler.schemas import WorkforceRequest, WorkforceResponse
from app.modules.workforce_scheduler.service import optimize_workforce

router = APIRouter()


@router.post('/optimize', response_model=WorkforceResponse, dependencies=[Depends(require_role([Role.ADMIN, Role.PM]))])
def optimize_workforce_endpoint(payload: WorkforceRequest) -> WorkforceResponse:
    return optimize_workforce(payload)
