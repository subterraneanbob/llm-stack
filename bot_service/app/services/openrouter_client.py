import httpx

from app.core.config import settings
from app.core.errors import OpenRouterError


HTTP_CLIENT_TIMEOUT_SECONDS = 5 * 60


def _parse_message(json_response: dict) -> str:
    """
    Разбирает ответ от OpenRouter API и возвращает сообщение LLM.

    Args:
        json_response: Ответ от OpenRouter API (ожидается словарь).

    Raises:
        OpenRouterError: Если из полученного ответа не удалось извлечь сообщение.

    Returns:
        str: Ответ, полученный от LLM.
    """
    try:
        message = json_response["choices"][0]["message"]
        return message.get("content", "")

    except (KeyError, IndexError, TypeError) as ex:
        raise OpenRouterError(
            "Malformed response received from OpenRouter.ai service"
        ) from ex


def make_chat_completion(prompt: str) -> str:
    """
    Получает ответ LLM на запрос пользователя.

    Args:
        prompt (str): Сообщение пользователя.

    Raises:
        OpenRouterError: Если не удалось подключиться к OpenRouter.ai, API вернул ошибку
            или ответ в формате, который не удалось разобрать.

    Returns:
        str: Ответ, полученный от LLM.
    """

    payload = {
        "messages": {
            "role": "user",
            "content": prompt,
        },
        "model": settings.openrouter_model,
    }

    with httpx.Client(
        base_url=settings.openrouter_base_url,
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        },
        timeout=HTTP_CLIENT_TIMEOUT_SECONDS,
    ) as client:
        try:
            response = client.post("/chat/completions", json=payload)
            response.raise_for_status()

            return _parse_message(response.json())
        except httpx.HTTPError as ex:
            raise OpenRouterError("Unable to contact OpenRouter.ai service") from ex
