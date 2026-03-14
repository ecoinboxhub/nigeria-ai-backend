from celery import Celery
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Make celery_app entirely optional. We handle failure gracefully later.
try:
    celery_app = Celery("construction_ai", broker=settings.redis_url, backend=settings.redis_url)
    celery_app.conf.task_routes = {
        "app.services.tasks.run_supplier_scraping": {"queue": "scraping"},
    }
except Exception as e:
    logger.warning(f"Failed to initialize Celery app (Redis likely unavailable): {e}")
    celery_app = None
