from fastapi import APIRouter

from app.services.health import router as health_router
from app.modules.project_tracker.router import router as project_tracker_router
from app.modules.procurement_assistant.router import router as procurement_router
from app.modules.safety_dashboard.router import router as safety_router
from app.modules.document_analyzer.router import router as document_router
from app.modules.cost_estimator.router import router as cost_router
from app.modules.workforce_scheduler.router import router as workforce_router
from app.modules.maintenance_predictor.router import router as maintenance_router
from app.modules.progress_visualizer.router import router as progress_router
from app.modules.tender_analyzer.router import router as tender_router
from app.modules.integration_suite.router import router as integration_router
from app.services.metrics import router as metrics_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(project_tracker_router, prefix="/project-tracker", tags=["project-tracker"])
api_router.include_router(procurement_router, prefix="/procurement", tags=["procurement"])
api_router.include_router(safety_router, prefix="/safety", tags=["safety"])
api_router.include_router(document_router, prefix="/document-analyzer", tags=["document-analyzer"])
api_router.include_router(cost_router, prefix="/cost-estimator", tags=["cost-estimator"])
api_router.include_router(workforce_router, prefix="/workforce", tags=["workforce"])
api_router.include_router(maintenance_router, prefix="/maintenance", tags=["maintenance"])
api_router.include_router(progress_router, prefix="/progress-visualizer", tags=["progress-visualizer"])
api_router.include_router(tender_router, prefix="/tender-analyzer", tags=["tender-analyzer"])
api_router.include_router(integration_router, prefix="/integration", tags=["integration"])
api_router.include_router(metrics_router)
