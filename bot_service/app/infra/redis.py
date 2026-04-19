from redis.asyncio import Redis

from app.core.config import settings


_redis_client: Redis | None = None


def get_redis() -> Redis:
    """
    Получает Redis-клиент. Клиент создаётся один раз при первом вызове функции.

    Returns:
        Redis: Клиент для работы с Redis.
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client
