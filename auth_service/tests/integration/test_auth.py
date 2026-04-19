import pytest

from conftest import verify_api_error
from app.core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


@pytest.mark.anyio
async def test_auth_flow(auth_helper, user_credentials):
    # Генерируем новые e-mail и пароль
    email = user_credentials.email
    password = user_credentials.password

    # Регистрация нового пользователя
    registered_user = await auth_helper.create_user(email, password)
    registered_user_id = registered_user.get("id")

    assert registered_user.get("id")
    assert registered_user.get("email") == email
    assert registered_user.get("role") == "user"

    # Логин
    access_token = await auth_helper.login_user(email, password)

    assert access_token

    # Получение профиля пользователя
    user_profile = await auth_helper.get_user_profile(access_token)

    assert user_profile.get("id") == registered_user_id
    assert user_profile.get("email") == email
    assert user_profile.get("role") == "user"


@pytest.mark.anyio
async def test_registration_conflict(auth_helper, existing_api_user):
    # Повторная регистрация с уже существующим e-mail
    response = await auth_helper.api.register(
        existing_api_user.email, existing_api_user.password
    )
    verify_api_error(response, UserAlreadyExistsError)


@pytest.mark.anyio
async def test_login_non_existing_email(auth_helper, user_credentials):
    # Используем e-mail сразу, без регистрации
    response = await auth_helper.api.login(
        user_credentials.email, user_credentials.password
    )
    verify_api_error(response, UserNotFoundError)


@pytest.mark.anyio
async def test_login_invalid_password(auth_helper, existing_api_user):
    # Логин с неверным паролем
    invalid_password = existing_api_user.password + "'; DROP TABLE users; --"
    response = await auth_helper.api.login(existing_api_user.email, invalid_password)
    verify_api_error(response, InvalidCredentialsError)


@pytest.mark.anyio
async def test_me_invalid_token(auth_helper, existing_api_user):
    # Запрос профиля с неверным токеном доступа
    response = await auth_helper.api.me("invalid-access-token")
    verify_api_error(response, InvalidTokenError)


@pytest.mark.anyio
async def test_me_no_token(auth_helper, existing_api_user):
    # Запрос профиля без токена доступа
    response = await auth_helper.api.me(None)

    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"
