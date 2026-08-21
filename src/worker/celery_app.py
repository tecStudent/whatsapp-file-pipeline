from celery import Celery

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "whatsapp_file_pipeline",
    broker=settings.redis_url,
    include=["src.worker.tasks"],
)
celery_app.conf.update(
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    result_serializer="json",
    task_acks_late=True,
    task_ignore_result=True,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    timezone="UTC",
    worker_prefetch_multiplier=1,
)
