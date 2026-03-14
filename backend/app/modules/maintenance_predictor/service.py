import logging
from app.modules.maintenance_predictor.schemas import EquipmentInput, MaintenancePrediction

logger = logging.getLogger(__name__)


def predict_maintenance(payload: EquipmentInput) -> MaintenancePrediction:
    risk = (
        (payload.runtime_hours / 1000) * 0.3
        + (payload.vibration_index / 10) * 0.25
        + max(payload.temperature_c - 35, 0) / 30 * 0.2
        + (payload.last_maintenance_days / 90) * 0.25
    )
    risk = max(0.0, min(1.0, risk))
    due_days = max(1, int((1 - risk) * 30))
    return MaintenancePrediction(failure_risk=round(risk, 4), maintenance_due_in_days=due_days)
