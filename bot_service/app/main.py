import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bot.dispatcher import create_bot, create_dispatcher, create_llm_response_relay
from app.core.config import settings


bot = create_bot()
dp = create_dispatcher()
llm_response_relay = create_llm_response_relay()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Запускает цикл обработки сообщений боту от пользователей и отправку ответов от LLM
    при старте приложения FastAPI.

    Args:
        app (FastAPI): Приложение FastAPI.
    """
    polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    llm_response_relay.start(bot)

    yield

    await llm_response_relay.stop()
    await dp.stop_polling()
    await polling_task


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health", tags=["system"])
async def health():
    """
    Получает статус системы и название окружения.
    """
    return {"status": "OK", "env": settings.env}
