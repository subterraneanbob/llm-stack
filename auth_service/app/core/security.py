import logging
import time
from datetime import timedelta
from typing import Any
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

token_ttl = timedelta(minutes=settings.access_token_expire_minutes)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Подавляем предупреждение passlib при использовании bcrypt >= 4.1.1:
# AttributeError: module 'bcrypt' has no attribute '__about__'
# https://github.com/pyca/bcrypt/issues/684
logging.getLogger("passlib").setLevel(logging.ERROR)


def _now_seconds() -> int:
    """
    Возвращает целое число секунд, которое прошло с момента начала эпохи (Epoch).

    Returns:
        int: Целое число секунд с начала эпохи.
    """
    return int(time.time())


def hash_password(plain_text_password: str) -> str:
    """
    Преобразует пароль в открытом виде в безопасный хеш для хранения и последующей проверки.

    Args:
        plain_test_password (str): Пароль в открытом виде.

    Returns:
        str: Хеш пароля вместе с солью.
    """
    return pwd_context.hash(plain_text_password)


def verify_password(plain_text_password: str, hashed_password: str | None) -> bool:
    """
    Проверяет, что предоставленный в открытом виде пароль соответствует хешу.

    Args:
        plain_text_password (str): Пароль в открытом виде
        hashed_password (str | None): Хеш пароля. Если указать значение None,
            то функция всегда возвращает False.

    Returns:
        bool: True, если пароль соответствует хешу, иначе False.
    """
    return pwd_context.verify(plain_text_password, hashed_password)


def create_access_token(subject: str, role: str) -> str:
    """
    Генерирует токен доступа в формате JWT. Секретный ключ для подписи токена,
    алгоритм формирования подписи токена и время жизни токена берутся из настроек.

    Args:
        subject (str): Субъект, которому принадлежит токен (например, идентификатор пользователя).
        role (str): Роль субъекта (например, роль пользователя - `admin`).

    Returns:
        str: Токен доступа в виде JWT строки.
    """
    issued_at = _now_seconds()
    expires_at = issued_at + int(token_ttl.total_seconds())

    claims = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": issued_at,
        "exp": expires_at,
    }

    return jwt.encode(claims, settings.jwt_secret, settings.jwt_alg)


def decode_token(token: str) -> dict[str, Any]:
    """
    Проверяет JWT токен и возвращает словарь полей, содержащихся в токене, если проверка успешна.
    Секретный ключ для проверки токена и алгоритм формирования подписи токена берутся из настроек.

    Args:
        token (str): JWT токен.

    Returns:
        dict[str, Any]: Словарь полей, указанных в токене.
    """
    return jwt.decode(token, settings.jwt_secret, settings.jwt_alg)
