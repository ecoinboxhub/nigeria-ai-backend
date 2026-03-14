import mlflow

from app.core.config import settings


def setup_mlflow() -> None:
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
