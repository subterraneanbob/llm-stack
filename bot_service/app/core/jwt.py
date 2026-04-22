from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.core.errors import InvalidTokenError, TokenExpiredError


def decode_and_validate(token: str) -> dict[str, Any]:
    """
    Проверяет JWT токен и возвращает словарь полей, содержащихся в токене, если проверка успешна.
    Секретный ключ для проверки токена и алгоритм формирования подписи токена берутся из настроек.

    Args:
        token (str): JWT токен.

    Returns:
        dict[str, Any]: Словарь полей, указанных в токене.
    """

    try:
        return jwt.decode(
            token, settings.jwt_secret, settings.jwt_alg, options={"require_exp": True}
        )
    except ExpiredSignatureError as ex:
        raise TokenExpiredError("Access token is expired.") from ex
    except (JWTError, ValueError) as ex:
        raise InvalidTokenError("Access token is invalid.") from ex
