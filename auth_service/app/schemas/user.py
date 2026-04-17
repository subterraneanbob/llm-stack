from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    """
    Публичная схема пользователя, которая используется в ответах.
    """

    id: int = Field(description="Идентификатор пользователя")
    email: EmailStr = Field(description="e-mail пользователя")
    role: str = Field(description="Роль пользователя")

    model_config = {"from_attributes": True}
