from aiogram import Bot

from app.core.config import settings
from app.core.errors import OpenRouterError
from app.infra.celery_app import celery_app
from app.services.openrouter_client import make_chat_completion

bot = Bot(token=settings.telegram_bot_token)


@celery_app.task(name="app.tasks.llm_tasks.llm_request")
def llm_request(tg_chat_id: int, prompt: str):

    try:
        return make_chat_completion(prompt)
    except OpenRouterError:
        return "Не удалось отправить сообщение к OpenRouter. Повторите запрос позже."
