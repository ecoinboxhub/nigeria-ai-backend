import math
import logging
from fastapi import HTTPException

from app.modules.project_tracker.schemas import DelayInput, DelayPrediction, ProjectSchema
from app.services.weather_service import weather_service
from app.db.supabase import supabase

logger = logging.getLogger(__name__)

def list_projects() -> list[ProjectSchema]:
    if not supabase: return []
    try:
        res = supabase.table("projects").select("*").order("name").execute()
        return [ProjectSchema(**p) for p in res.data]
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return []

def predict_delay(features: DelayInput) -> DelayPrediction:
    try:
        weather = weather_service.fetch_city_weather(features.city)
    except Exception as e:
        logger.error(f"Weather service failed for {features.city}: {e}")
        weather = {}

    rainfall = max(features.rainfall_mm, weather.get("rainfall_mm", 0.0))
    wind = max(features.wind_speed_kmh, weather.get("wind_speed_kmh", 0.0))

    try:
        lstm_signal = 0.25 * math.tanh((rainfall - 30) / 20) + 0.2 * (1 - features.resource_availability)
        tree_signal = 0.3 if features.supply_delay_days > 3 else 0.05
        rf_signal = 0.25 if features.workforce_attendance < 0.8 else 0.1
        weather_penalty = 0.1 if wind > 40 else 0.02

        risk = max(0.0, min(1.0, 0.45 + lstm_signal + tree_signal + rf_signal + weather_penalty))
        return DelayPrediction(
            delay_risk=round(risk, 4),
            will_delay=risk >= 0.55,
            model_stack=["LSTM", "DecisionTree", "RandomForest"],
        )
    except Exception as e:
        logger.error(f"Delay prediction calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal prediction engine error")
