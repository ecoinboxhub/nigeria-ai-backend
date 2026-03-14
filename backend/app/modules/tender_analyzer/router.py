from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.modules.tender_analyzer.schemas import TenderInput, TenderOutput
from app.modules.tender_analyzer.service import analyze_tender

router = APIRouter()


@router.post('/analyze', response_model=TenderOutput, dependencies=[Depends(require_role([Role.ADMIN, Role.LEGAL, Role.PM]))])
def analyze_tender_endpoint(payload: TenderInput) -> TenderOutput:
    return analyze_tender(payload)
