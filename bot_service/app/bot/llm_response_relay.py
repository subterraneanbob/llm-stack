import asyncio

from aiogram import Bot
from redis.asyncio import Redis

from app.infra.redis import LLM_RESPONSE_READY_CH, llm_response_key


class LLMResponseRelay:
    """
    Класс, который отправляет ответы от LLM обратно пользователю Telegram.
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

                    # Проверяем, что сообщение не пустое, отправляем ответ пользователю
                    # и помечаем ключ Redis на удаление.
                    if (llm_response := await self.redis.get(response_key)) is not None:
                        await bot.send_message(tg_chat_id, llm_response)
                        await self.redis.unlink(response_key)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(LLM_RESPONSE_READY_CH)
