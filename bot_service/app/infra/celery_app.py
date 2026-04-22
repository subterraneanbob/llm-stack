from celery import Celery
from celery.app import trace

from app.core.config import settings

# Убираем логирование ответов от LLM из сообщения о выполнении задачи
trace.LOG_SUCCESS = """\
Task %(name)s[%(id)s] succeeded in %(runtime)ss\
"""

celery_app = Celery(
    "bot_tasks",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

celery_app.autodiscover_tasks(["app.tasks"], related_name="llm_tasks")
