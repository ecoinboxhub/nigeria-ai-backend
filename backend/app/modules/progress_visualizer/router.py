from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.modules.progress_visualizer.schemas import ProgressInput, ProgressOutput
from app.modules.progress_visualizer.service import analyze_progress

router = APIRouter()


@router.post('/analyze', response_model=ProgressOutput, dependencies=[Depends(require_role([Role.ADMIN, Role.PM, Role.ANALYST]))])
def analyze_progress_endpoint(payload: ProgressInput) -> ProgressOutput:
    return analyze_progress(payload)
