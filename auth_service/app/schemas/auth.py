from pydantic import BaseModel, EmailStr, Field, SecretStr


class RegisterRequest(BaseModel):
    """
    Запрос регистрации нового пользователя.
    """

    email: EmailStr = Field(description="E-mail нового пользователя")
    password: SecretStr = Field(
        min_length=6,
        max_length=64,
        description="Пароль нового пользователя в открытом виде",
    )


class TokenResponse(BaseModel):
    """
    Ответ при успешной аутентификации пользователя.
    """

    access_token: str = Field(description="Токен доступа в формате JWT")
    token_type: str = "bearer"
