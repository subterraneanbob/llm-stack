from typing import Any, NamedTuple, Type
import uuid

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.exceptions import BaseHTTPException
from app.db.base import Base
from app.main import app


class TestAuthClient:
    """
    Клиент для API авторизации.
    """

    def __init__(self, client: AsyncClient):
        self.client = client

    async def register(self, email: str, password: str) -> Response:
        return await self.client.post(
            "/auth/register", json={"email": email, "password": password}
        )

    async def login(self, email: str, password: str) -> Response:
        return await self.client.post(
            "/auth/login", data={"username": email, "password": password}
        )

    async def me(self, access_token: str | None) -> Response:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        return await self.client.get("/auth/me", headers=headers)


class TestAuthHelper:
    """
    Вспомогательный класс - вызывает методы авторизации и проверяет, что действие успешно.
    """

    def __init__(self, auth_client: TestAuthClient):
        self.api = auth_client

    async def create_user(self, email: str, password: str) -> dict[str, Any]:
        response = await self.api.register(email, password)
        assert response.status_code == 201
        return response.json()

    async def login_user(self, email: str, password: str) -> str:
        response = await self.api.login(email, password)
        assert response.status_code == 200
        match response.json():
            case {"access_token": access_token, "token_type": "bearer"}:
                return access_token
            case _:
                pytest.fail("Unexpected login response received.")

    async def get_user_profile(self, access_token: str) -> dict[str, Any]:
        response = await self.api.me(access_token)
        assert response.status_code == 200
        return response.json()


class UserCredentials(NamedTuple):
    email: str
    password: str


@pytest.fixture(scope="function")
async def test_db():
    """
    Создаёт базу данных в памяти и подменяет ею обычную базу.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """
    Создаёт HTTP-клиент для тестирования приложения.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def auth_helper(client) -> TestAuthHelper:
    """
    Создаёт вспомогательный класс для вызова методов авторизации.
    """
    auth_client = TestAuthClient(client)
    return TestAuthHelper(auth_client)


@pytest.fixture
def user_credentials() -> UserCredentials:
    """
    Генерирует случайные e-mail и пароль.
    """
    unique_id = uuid.uuid4().hex
    return UserCredentials(
        email=f"user_{unique_id}@example.com",
        password=f"P@ssw0rd!_{unique_id}",
    )


@pytest.fixture
async def existing_api_user(auth_helper, user_credentials) -> UserCredentials:
    """
    Создаёт нового пользователя со случайными e-mail и паролем.
    """
    await auth_helper.create_user(user_credentials.email, user_credentials.password)
    return user_credentials


def verify_api_error(
    response: Response,
    http_error: Type[BaseHTTPException],
):
    """
    Проверяет, что HTTP-ответ является ошибкой с определёнными:
     - HTTP-кодом возврата
     - кодом ошибки
     - сообщением
     - HTTP-заголовками (если указаны)

    Args:
        response (Response): Полученный HTTP-ответ.
        http_error (Type[BaseHTTPException]): Ошибка, которая формируется в приложении
            и возвращается клиенту.
    """
    detail = response.json().get("detail")

    if not detail:
        pytest.fail("Response body does not indicate error.")

    assert response.status_code == http_error.status_code
    assert detail.get("error_code") == http_error.error_code
    assert detail.get("message") == http_error.message

    # Проверяем, что нужные HTTP заголовки содержатся в ответе.
    if http_error.headers:
        assert http_error.headers.items() <= response.headers.items()
