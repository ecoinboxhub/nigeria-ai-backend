from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.modules.safety_dashboard.schemas import SafetyAnalysisResponse, SafetyLogInput
from app.modules.safety_dashboard.service import analyze_safety_log

router = APIRouter()


@router.post('/analyze-log', response_model=SafetyAnalysisResponse, dependencies=[Depends(require_role([Role.ADMIN, Role.SAFETY, Role.PM]))])
def analyze_safety_log_endpoint(payload: SafetyLogInput) -> SafetyAnalysisResponse:
    return analyze_safety_log(payload)
