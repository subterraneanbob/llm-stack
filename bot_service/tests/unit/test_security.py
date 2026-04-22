import pytest

from app.core.jwt import decode_and_validate
from app.core.errors import InvalidTokenError, TokenExpiredError


def test_decode_and_validate(access_token):
    # Проверяем, что можно получить поля из токена
    claims = decode_and_validate(access_token)

    assert claims.get("sub")
    assert claims.get("exp")


def test_expired_token(expired_access_token):
    # "Просроченный" токен вызывают ошибку
    with pytest.raises(TokenExpiredError):
        decode_and_validate(expired_access_token)


@pytest.mark.parametrize(
    "wannabe_access_token", ["", "definitely-an-access-token", "abcdef123456"]
)
def test_invalid_token(wannabe_access_token):
    # Неверные значения токена вызывают ошибку
    with pytest.raises(InvalidTokenError):
        decode_and_validate(wannabe_access_token)
