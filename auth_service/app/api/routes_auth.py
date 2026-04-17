from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_usecase, get_current_user_id
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.usecases.auth import AuthUseCase


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register(
    data: RegisterRequest, auth: AuthUseCase = Depends(get_auth_usecase)
):
    """
    Регистрирует нового пользователя.
    """
    return await auth.register(data.email, data.password.get_secret_value())


@router.post("/login", response_model=TokenResponse)
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    auth: AuthUseCase = Depends(get_auth_usecase),
):
    """
    Авторизует существующего пользователя.
    """
    token = await auth.login(data.username, data.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
async def me(
    user_id: int = Depends(get_current_user_id),
    auth: AuthUseCase = Depends(get_auth_usecase),
):
    """
    Получает профиль текущего пользователя.
    """
    return await auth.get_user_profile(user_id)
