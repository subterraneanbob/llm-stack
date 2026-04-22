from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.bot.llm_response_relay import LLMResponseRelay
from app.core.config import settings
from app.infra.redis import get_redis


def create_bot() -> Bot:
    return Bot(token=settings.telegram_bot_token)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)

    return dp


def create_llm_response_relay() -> LLMResponseRelay:
    return LLMResponseRelay(get_redis())
