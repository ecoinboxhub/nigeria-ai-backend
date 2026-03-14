import logging
from datetime import UTC, datetime

import mlflow
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.services.weather_service import weather_service

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def hourly_weather_pull() -> None:
    cities = weather_service.fetch_all_configured_cities()
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(f"{settings.mlflow_experiment_prefix}_weather")
    with mlflow.start_run(run_name="hourly_weather_pull"):
        mlflow.log_param("cities", len(cities))
        mlflow.log_param("run_at", datetime.now(UTC).isoformat())
    logger.info("weather pull completed for %s cities", len(cities))


def start_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(hourly_weather_pull, "interval", hours=1, id="weather_pull", replace_existing=True)
    _scheduler.start()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
