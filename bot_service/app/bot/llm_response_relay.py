import asyncio

from aiogram import Bot
from redis.asyncio import Redis

from app.infra.redis import LLM_RESPONSE_READY_CH, llm_response_key

MESSAGE_SIZE_LIMIT = 4096


def split_text(text: str, limit: int = MESSAGE_SIZE_LIMIT) -> list[str]:
    """
    Разбивает текст на части длиной не более `limit` символов.
    Разбивка производится по символу переноса строки, если он не найден, то просто
    берётся первые `limit` символов.

    Args:
        text (str): Исходный текст.
        limit (int, optional): Максимальный размер одной части.

    Returns:
        list[str]: Список частей, которые получились при разбивке исходного текста.
    """
    parts = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit

        parts.append(text[:split_at].strip())
        text = text[split_at:].strip()

    parts.append(text)
    return parts


class LLMResponseRelay:
    """
    Класс, который получает уведомления о поступлении нового ответа LLM
    и отправляет их пользователю Telegram.
    """

    def __init__(self, redis: Redis):
        self.redis = redis
        self._process_task = asyncio.Future()
        self._process_task.set_result(None)

    def start(self, bot: Bot):
        """
        Запускает цикл отправки ответов от LLM в фоновом режиме.

        Args:
            bot (Bot): Telegram-бот, который используется для отправки ответов.
        """
        self._process_task = asyncio.create_task(self.process(bot))

    async def stop(self):
        """
        Прекращает отправку ответов от LLM.
        """

        self._process_task.cancel()
        await asyncio.gather(self._process_task, return_exceptions=True)

    async def process(self, bot: Bot):
        """
        Запускает цикл отправки ответов от LLM.

        Args:
            bot (Bot): Telegram-бот, который используется для отправки ответов.
        """

        pubsub = self.redis.pubsub()

        await pubsub.subscribe(LLM_RESPONSE_READY_CH)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    tg_chat_id = message["data"]
                    response_key = llm_response_key(tg_chat_id)

                    # Проверяем, что сообщение не пустое, разбиваем ответ LLM на части
                    # (у Telegram есть ограничение на длину сообщения),
                    # отправляем пользователю и помечаем ключ Redis на удаление.
                    if (llm_response := await self.redis.get(response_key)) is not None:
                        for text_part in split_text(llm_response):
                            await bot.send_message(tg_chat_id, text_part)

                        await self.redis.unlink(response_key)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(LLM_RESPONSE_READY_CH)
