from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.modules.procurement_assistant.schemas import ProcurementQuery, ProcurementResponse
from app.modules.procurement_assistant.service import supplier_intelligence

router = APIRouter()


@router.post('/supplier-intelligence', response_model=ProcurementResponse, dependencies=[Depends(require_role([Role.ADMIN, Role.PROCUREMENT, Role.PM]))])
def supplier_intelligence_endpoint(payload: ProcurementQuery) -> ProcurementResponse:
    return supplier_intelligence(payload)
