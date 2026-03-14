from celery import Celery

from app.core.config import settings

celery_app = Celery("construction_ai", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {
    "app.services.tasks.run_supplier_scraping": {"queue": "scraping"},
}
