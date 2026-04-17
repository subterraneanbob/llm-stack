from typing import AsyncGenerator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.repositories.users import UsersOrmRepo
from app.usecases.auth import AuthUseCase
from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security import decode_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


def get_users_repo(db: AsyncSession = Depends(get_db)) -> UsersOrmRepo:
    return UsersOrmRepo(db)


def get_auth_usecase(
    users_repo: UsersOrmRepo = Depends(get_users_repo),
) -> AuthUseCase:
    return AuthUseCase(users_repo)


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    Получает идентификатор текущего пользователя из токена доступа.

    Args:
        token (str, optional): JWT токен, который предоставлен клиентом.

    Raises:
        TokenExpiredError: Если истёк срок действия токена доступа.
        InvalidTokenError: Если из токена доступа не удалось получить идентификатор пользователя.

    Returns:
        int: Уникальный идентификатор пользователя.
    """

    try:
        payload = decode_token(token)

        token_type = payload.get("type")
        subject = payload.get("sub")

        if token_type != "access" or not subject:
            raise InvalidTokenError

        return int(subject)

    except ExpiredSignatureError as ex:
        raise TokenExpiredError from ex
    except (JWTError, ValueError) as ex:
        raise InvalidTokenError from ex
