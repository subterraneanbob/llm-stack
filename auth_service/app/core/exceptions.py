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
        self.headers = headers or {}

        if message is not None:
            self.message = message

        super().__init__(
            status_code=self.status_code, detail=self.message, headers=self.headers
        )


class UserAlreadyExistsError(BaseHTTPException):
    """
    Ошибка при регистрации: пользователь уже существует.
    """

    status_code = 409
    error_code = "USER_ALREADY_EXISTS"
    message = "User with this identifier already exists."


class InvalidCredentialsError(BaseHTTPException):
    """
    Ошибка авторизации: неверный e-mail или пароль.
    """

    status_code = 401
    code = "INVALID_CREDENTIALS"
    message = "Incorrect email or password."
    headers = {"WWW-Authenticate": "Bearer"}


class InvalidTokenError(BaseHTTPException):
    """
    Ошибка авторизации: предоставлен некорректный токен доступа.
    """

    status_code = 401
    code = "INVALID_TOKEN"
    message = "The provided token is malformed or invalid."
    headers = {"WWW-Authenticate": "Bearer"}


class TokenExpiredError(BaseHTTPException):
    """
    Ошибка авторизации: истёк срок действия токена доступа.
    """

    status_code = 401
    code = "TOKEN_EXPIRED"
    message = "The access token has expired."
    headers = {"WWW-Authenticate": "Bearer"}


class UserNotFoundError(BaseHTTPException):
    """
    Ошибка авторизации: пользователь с указанным идентификатором не найден.
    """

    status_code = 404
    code = "USER_NOT_FOUND"
    message = "Requested user was not found."


class PermissionDeniedError(BaseHTTPException):
    """
    Ошибка авторизации: действие запрещено.
    """

    status_code = 403
    code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action."
