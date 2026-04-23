import json
import random
import time
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

from aiogram.filters import CommandObject
from fakeredis import FakeAsyncRedis
from httpx import Response
import pytest
from jose import jwt
import respx


from app.core.config import settings
from app.infra.redis import token_key

TOKEN_TTL = 3600


class MockRedis:
    """
    Тестовый двойник клиента Redis.
    """

    def __init__(self, mocker):
        fake_redis = FakeAsyncRedis(encoding="utf-8", decode_responses=True)
        mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)

        self.object = fake_redis

    async def set_token(self, tg_chat_id: int, access_token: str):
        """
        Сохраняет токен в Redis по ключу, соответствующему чату.

        Args:
            tg_chat_id: Идентификатор Telegram-чата.
            access_token: Токен доступа.
        """
        key = token_key(tg_chat_id)
        await self.object.set(key, access_token)

    async def validate_token(self, tg_chat_id: int, access_token: str | None):
        """
        Проверяет, совпадает ли сохранённый токен с переданным.

        Args:
            tg_chat_id: Идентификатор Telegram-чата.
            access_token: Токен доступа для сравнения.
        """
        key = token_key(tg_chat_id)
        stored_access_token = await self.object.get(key)

        assert stored_access_token == access_token


class MockMessage:
    """
    Тестовый двойник сообщения Telegram.
    """

    def __init__(self, tg_chat_id: int):
        message = AsyncMock()
        message.from_user = MagicMock(id=tg_chat_id)

        self.tg_chat_id = tg_chat_id
        self.object = message
        self.text = "Test message."

    @property
    def text(self) -> str:
        """
        Возвращает текст сообщения.
        """
        return self._text

    @text.setter
    def text(self, value):
        """
        Устанавливает текст сообщения.

        Args:
            value: Новый текст сообщения.
        """
        self._text = value
        self.object.text = value

    def validate_reply(self, reply_text: str):
        """
        Проверяет, было ли отправлено ответное сообщение с указанным текстом.

        Args:
            reply_text: Ожидаемый текст ответа.
        """
        self.object.answer.assert_called_once_with(reply_text)


class MockLLMRequestTask:
    """
    Тестовый двойник задачи LLM-запроса.
    """

    def __init__(self, mocker):
        self.object = mocker.patch("app.bot.handlers.llm_request.delay")

    def was_triggered_with(self, tg_chat_id: int, prompt: str):
        """
        Проверяет, что задача была запущена с указанными параметрами.

        Args:
            tg_chat_id: Идентификатор Telegram-чата.
            prompt: Текст запроса пользователя.
        """
        self.object.assert_called_once_with(tg_chat_id=tg_chat_id, prompt=prompt)

    def was_not_triggered(self):
        self.object.assert_not_called()


class MockOpenRouterClient:
    """
    Тестовый двойник HTTP-клиента для Openrouter.
    """

    OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, router: respx.MockRouter):
        self.router = router
        self.setup("Test response")

    def setup(self, response_text: str):
        """
        Устанавливает текст ответа.
        """
        self.route = self.router.post(self.OPENROUTER_ENDPOINT).mock(
            return_value=Response(
                200,
                json={
                    "choices": [
                        {"message": {"role": "assistant", "content": response_text}}
                    ]
                },
            )
        )

    def verify_route_call(self):
        """
        Проверяет, что HTTP вызов к /chat/completions был сделан.
        """
        assert self.route.called
        assert self.route.call_count == 1

    def verify_request(self, prompt: str):
        """
        Проверяет, что в теле запроса содержится запрос пользователя.
        """
        last_request = self.route.calls.last.request
        payload = json.loads(last_request.content)

        assert payload["messages"][0]["content"] == prompt


class AccessTokenWithClaims(NamedTuple):
    """
    Токен доступа вместе со списком полей, которые использовались для его создания.
    """

    token: str
    claims: dict


def generate_claims(**claims_override) -> dict:
    """
    Генерирует словарь полей (claims) для JWT токена.

    Args:
        **claims_override: Переопределения для claims.

    Returns:
        dict: Словарь полей.
    """
    subject = "47"
    role = "user"
    issued_at = int(time.time())
    expires_at = issued_at + TOKEN_TTL

    return {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": issued_at,
        "exp": expires_at,
    } | claims_override


def generate_token(claims: dict | None = None, jwt_secret: str | None = None) -> str:
    """
    Генерирует JWT токен доступа на основе claims и секретного ключа.

    Args:
        claims: Утверждения для токена (если не указано, будут сгенерированы по умолчанию).
        jwt_secret: Секретный ключ для подписи токена (если не указан, берётся из настроек).

    Returns:
        str: JWT токен в виде строки.
    """
    return jwt.encode(
        claims or generate_claims(), jwt_secret or settings.jwt_secret, settings.jwt_alg
    )


def token_command(token: str) -> CommandObject:
    """
    Создаёт команду /token для Telegram-бота с указанным значением токена.

    Args:
        token (str): Токен доступа.

    Returns:
        CommandObject: Команда для Telegram-бота.
    """
    return CommandObject(command="token", args=token)


@pytest.fixture
def access_token() -> str:
    """
    Возвращает корректный токен доступа.
    """
    return generate_token()


@pytest.fixture
def access_token_with_claims() -> AccessTokenWithClaims:
    """
    Возвращает корректный токен доступа вместе со списком claims.
    """
    claims = generate_claims()
    token = generate_token(claims)

    return AccessTokenWithClaims(token, claims)


@pytest.fixture(
    params=[
        "not-access-token",
        "header.payload.signature",
        "eyJhbGbiOiJIUz11NiIsInR5uCI6IkPXVCJ9.e42.wrong",
        "WRONG_SECRET_TOKEN",
    ]
)
def invalid_access_token(request) -> str:
    """
    Возвращает некорректный токен доступа:
     - 'мусорная' строка
     - токен с корректным форматом, но неверным содержимым
     - корректный токен, подписанный неверным ключом
    """
    token = request.param

    if token == "WRONG_SECRET_TOKEN":
        return generate_token(jwt_secret="my-secret-key")

    return token


@pytest.fixture
def expired_access_token() -> str:
    """
    Возвращает токен с истёкшим сроком действия.
    """
    expires_at = int(time.time()) - TOKEN_TTL
    issued_at = expires_at - TOKEN_TTL

    claims = generate_claims(iat=issued_at, exp=expires_at)

    return generate_token(claims)


@pytest.fixture
def mock_redis(mocker):
    return MockRedis(mocker)


@pytest.fixture
def mock_message():
    return MockMessage(tg_chat_id=random.randint(1, 2**32 - 1))


@pytest.fixture
def mock_llm_request_task(mocker):
    return MockLLMRequestTask(mocker)


@pytest.fixture
def mock_openrouter_client():
    with respx.mock() as mock_router:
        yield MockOpenRouterClient(mock_router)
