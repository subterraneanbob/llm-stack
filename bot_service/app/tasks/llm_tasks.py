from typing import NamedTuple

from celery import Task
from celery.exceptions import TimeoutError

from app.core.errors import OpenRouterError
from app.infra.celery_app import celery_app
from app.infra.redis import (
    LLM_RESPONSE_READY_CH,
    Intent,
    get_redis,
)
from app.services.openrouter_client import make_chat_completion

redis = get_redis(Intent.WORKER)


class LLMRequestTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        """
        Публикует идентификатор в Redis PubSub при успешном завершении задачи.
        """
        redis.publish(LLM_RESPONSE_READY_CH, task_id)


class LLMRequestTaskResult(NamedTuple):
    """
    Результат работы запроса к LLM: ответ и идентификатор чата, куда его нужно доставить.
    """

    tg_chat_id: int
    llm_response: str


@celery_app.task(name="app.tasks.llm_tasks.llm_request", base=LLMRequestTask)
def llm_request(tg_chat_id: int, prompt: str) -> LLMRequestTaskResult:
    """
    Задача, которая выполняет запрос к сервису OpenRouter.ai с указанным запросом к LLM.
    В ответе сохраняется ответ от LLM и идентификатор Telegram-чата.

    Args:
        tg_chat_id (int): Идентификатор Telegram-чата, откуда был получен запрос.
        prompt (str): Запрос к LLM.

    Returns:
        LLMRequestTaskResult: Результат работы запроса к LLM.
    """
    try:
        llm_response = make_chat_completion(prompt)
    except OpenRouterError:
        llm_response = (
            "Не удалось отправить сообщение к OpenRouter. "
            "Пожалуйста, повторите запрос позже."
        )

    return LLMRequestTaskResult(tg_chat_id, llm_response)


def get_llm_request_results(task_id: str) -> LLMRequestTaskResult:
    """
    Получает результат выполнения задачи `llm_request` и удаляет её из хранилища.

    Args:
        task_id (str): Идентификатор задачи.

    Returns:
        LLMRequestTaskResult: Результат работы запроса к LLM.
    """

    task = celery_app.AsyncResult(task_id)
    try:
        result = task.get(timeout=5)
        task.forget()

        return result
    except TimeoutError:
        # Метод get() без тайм-аута может заблокировать поток выполнения, если задача ещё не выполнена
        # или задачи с идентификатором task_id не существует.
        return LLMRequestTaskResult(0, "")
