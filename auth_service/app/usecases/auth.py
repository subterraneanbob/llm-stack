from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.users import UsersOrmRepo


class AuthUseCase:
    """
    Бизнес-логика регистрации и авторизации пользователей.
    """

    def __init__(self, users_repo: UsersOrmRepo):
        self._users_repo = users_repo

    async def register(self, email: str, plain_text_password: str) -> User:
        """
        Регистрирует нового пользователя.

        Args:
            email (str): E-mail пользователя.
            plain_text_password (str): Пароль пользователя в открытом виде.

        Raises:
            UserAlreadyExistsError: Если пользователь с указанным e-mail уже существует.

        Returns:
            User: Профиль нового пользователя.
        """
        existing_user = await self._users_repo.get_user_by_email(email)

        if existing_user:
            raise UserAlreadyExistsError(meta={"email": email})

        new_user = User(
            email=email,
            password_hash=hash_password(plain_text_password),
            role="user",
        )

        await self._users_repo.create(new_user)

        return new_user

    async def login(self, email: str, plain_text_password: str) -> str:
        """
        Авторизует существующего пользователя и создаёт токен доступа.

        Args:
            email (str): e-mail пользователя.
            plain_text_password (str): Пароль пользователя в открытом виде.

        Raises:
            UserNotFoundError: Если пользователь с указанным e-mail не существует.
            InvalidCredentialsError: Если указан неверный пароль.

        Returns:
            str: Токен доступа в виде строки.
        """
        existing_user = await self._users_repo.get_user_by_email(email)

        if not existing_user:
            raise UserNotFoundError(meta={"email": email})

        if not verify_password(plain_text_password, existing_user.password_hash):
            raise InvalidCredentialsError

        return create_access_token(
            subject=str(existing_user.id), role=existing_user.role
        )

    async def get_user_profile(self, user_id: int) -> User:
        """
        Получает профиль существующего пользователя.

        Args:
            user_id (int): Уникальный идентификатор пользователя.

        Raises:
            UserNotFoundError: Если пользователь с указанным идентификатором не найден.

        Returns:
            User: Профиль пользователя.
        """
        user = await self._users_repo.get_user_by_id(user_id)

        if not user:
            raise UserNotFoundError(meta={"user_id": user_id})

        return user
