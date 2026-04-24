import asyncio

from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from redis.asyncio import Redis

from app.infra.redis import LLM_RESPONSE_READY_CH
from app.tasks.llm_tasks import get_llm_request_results

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
                    # Получаем результат выполнения задачи: идентификатор чата и ответ LLM
                    task_id = message["data"]
                    tg_chat_id, llm_response = get_llm_request_results(task_id)

                    # Отправляем ответ по частям (у Telegram есть ограничение на длину сообщения)
                    if tg_chat_id and llm_response:
                        for text_part in split_text(llm_response):
                            await bot.send_message(
                                tg_chat_id,
                                text_part,
                                parse_mode=ParseMode.MARKDOWN,
                            )

        except asyncio.CancelledError:
            await pubsub.unsubscribe(LLM_RESPONSE_READY_CH)
