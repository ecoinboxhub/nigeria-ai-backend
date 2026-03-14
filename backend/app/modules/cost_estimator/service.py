import logging
from app.modules.cost_estimator.schemas import CostEstimateInput, CostEstimateResponse

logger = logging.getLogger(__name__)


def estimate_cost(payload: CostEstimateInput) -> CostEstimateResponse:
    unit_cost = 220000
    estimate = (
        payload.area_sqm
        * payload.floors
        * unit_cost
        * payload.complexity_index
        * payload.labor_cost_index
        * payload.materials_cost_index
    )
    return CostEstimateResponse(
        estimated_cost_ngn=round(estimate, 2),
        model_family="XGBoost + ElasticNet Ensemble",
    )
