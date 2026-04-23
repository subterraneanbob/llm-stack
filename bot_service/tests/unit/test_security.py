import pytest

from app.core.jwt import decode_and_validate
from app.core.errors import InvalidTokenError, TokenExpiredError


def test_decode_and_validate(access_token_with_claims):
    # Проверяем, что токен корретно проверяется, и что можно получить поля из токена
    access_token, claims = access_token_with_claims
    payload = decode_and_validate(access_token)

    assert payload.get("sub")
    assert payload.get("sub") == claims.get("sub")
    assert payload == claims


def test_expired_token(expired_access_token):
    # "Просроченный" токен вызывают ошибку
    with pytest.raises(TokenExpiredError):
        decode_and_validate(expired_access_token)


def test_invalid_token(invalid_access_token):
    # Неверные значения токена вызывают ошибку
    with pytest.raises(InvalidTokenError):
        decode_and_validate(invalid_access_token)
