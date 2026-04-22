from app.core.errors import OpenRouterError
from app.infra.celery_app import celery_app
from app.infra.redis import (
    LLM_RESPONSE_READY_CH,
    LLM_RESPONSE_TTL_SECONDS,
    Intent,
    get_redis,
    llm_response_key,
)
from app.services.openrouter_client import make_chat_completion

redis = get_redis(Intent.WORKER)


@celery_app.task(name="app.tasks.llm_tasks.llm_request")
def llm_request(tg_chat_id: int, prompt: str):
    try:
        response = make_chat_completion(prompt)
    except OpenRouterError:
        response = (
            "Не удалось отправить сообщение к OpenRouter. "
            "Пожалуйста, повторите запрос позже."
        )

    redis.set(llm_response_key(tg_chat_id), response, ex=LLM_RESPONSE_TTL_SECONDS)
    redis.publish(LLM_RESPONSE_READY_CH, tg_chat_id)
