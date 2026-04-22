from enum import Enum

from redis import Redis
from redis.asyncio import Redis as RedisAsync

from app.core.config import settings


_redis_client: RedisAsync | None = None


LLM_RESPONSE_READY_CH = "llm_response_ready"
"""
Канал Redis, в который публикуются идентификаторы Telegram-чатов, 
для которых ответ от LLM готов к отправке.
"""

LLM_RESPONSE_TTL_SECONDS = 300
"""Время жизни ответа от LLM, в течение которого его необходимо отправить."""


class Intent(Enum):
    """
    Назначение клиента Redis.
    """

    APP = 1
    """Для использования в приложении (асинхронный)."""
    WORKER = 2
    """Для использования в Celery Workers (синхронный)."""


def token_key(tg_chat_id: int) -> str:
    """
    Формирует ключ хранения токена доступа.

    Args:
        tg_chat_id (int): Идентификатор Telegram-чата.

    Returns:
        str: Ключ Redis.
    """

    return f"token:{tg_chat_id}"


def llm_response_key(tg_chat_id: int) -> str:
    """
    Формирует ключ хранения ответа от LLM в Redis.

    Args:
        tg_chat_id (int): Идентификатор Telegram-чата.

    Returns:
        str: Ключ Redis.
    """

    return f"llm_response:{tg_chat_id}"


def get_redis(intent: Intent = Intent.APP) -> RedisAsync | Redis:
    """
    Получает Redis-клиент. В зависимости от назначения, клиент может быть разного типа:
     - асинхронный для использования в приложении. Клиент создаётся один раз при первом вызове, а затем переиспользуется.
     - синхронный для использования в Celery Workers. Новый клиент создаётся каждый раз при вызове.

    Args:
        intent (Intent): Назначение Redis клиента.

    Returns:
        RedisAsync | Redis: Клиент для работы с Redis (синхронный или асинхронный).
    """
    if intent == Intent.WORKER:
        return Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    global _redis_client

    if _redis_client is None:
        _redis_client = RedisAsync.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client
