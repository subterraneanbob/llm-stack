from fastapi import HTTPException


class BaseHTTPException(HTTPException):
    """
    Базовый класс для ошибок при работе приложения, которые нужно возвращать клиенту.
    """

    status_code = 400
    error_code = "APP_ERROR"
    message = "Application error"
    headers = {}

    def __init__(
        self,
        *,
        message: str | None = None,
        headers: dict | None = None,
        meta: dict | None = None,
    ):
        self.meta = meta or {}

        if message is not None:
            self.message = message

        if headers:
            self.headers |= headers

        super().__init__(
            status_code=self.status_code,
            detail={
                "error_code": self.error_code,
                "message": self.message,
                "meta": self.meta,
            },
            headers=self.headers,
        )


class BaseAuthError(BaseHTTPException):
    """
    Базовый класс для ошибок аутентификации.
    """

    status_code = 401
    headers = {"www-authenticate": "Bearer"}


class UserAlreadyExistsError(BaseHTTPException):
    """
    Ошибка при регистрации: пользователь уже существует.
    """

    status_code = 409
    error_code = "USER_ALREADY_EXISTS"
    message = "User with this identifier already exists."


class InvalidCredentialsError(BaseAuthError):
    """
    Ошибка авторизации: неверный e-mail или пароль.
    """

    error_code = "INVALID_CREDENTIALS"
    message = "Incorrect email or password."


class InvalidTokenError(BaseAuthError):
    """
    Ошибка авторизации: предоставлен некорректный токен доступа.
    """

    error_code = "INVALID_TOKEN"
    message = "The provided token is malformed or invalid."


class TokenExpiredError(BaseAuthError):
    """
    Ошибка авторизации: истёк срок действия токена доступа.
    """

    error_code = "TOKEN_EXPIRED"
    message = "The access token has expired."


class UserNotFoundError(BaseHTTPException):
    """
    Ошибка авторизации: пользователь с указанным идентификатором не найден.
    """

    status_code = 404
    error_code = "USER_NOT_FOUND"
    message = "Requested user was not found."


class PermissionDeniedError(BaseHTTPException):
    """
    Ошибка авторизации: действие запрещено.
    """

    status_code = 403
    error_code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action."
