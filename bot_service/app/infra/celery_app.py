from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "bot_tasks",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

celery_app.autodiscover_tasks(["app.tasks"], related_name="llm_tasks")
