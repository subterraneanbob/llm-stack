from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UsersOrmRepo:
    """
    Репозиторий пользователей.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Получает пользователя, соответствующего указанному значению e-mail.

        Args:
            email (str): Значение e-mail.

        Returns:
            User | None: ORM-модель пользователя или None, если пользователь не найден.
        """
        statement = select(User).where(User.email == email)
        return await self._session.scalar(statement)

    async def get_user_by_id(self, id: int) -> User | None:
        """
        Получает пользователя по его уникальному идентификатору.

        Args:
            id (int): Уникальный идентификатор пользователя.

        Returns:
            User | None: ORM-модель пользователя или None, если пользователь не найден.

        """
        return await self._session.get(User, id)

    async def create(self, new_user: User):
        """
        Создаёт нового пользователя.

        Args:
            new_user (User): Данные нового пользователя.
        """
        self._session.add(new_user)
        await self._session.commit()
        await self._session.refresh(new_user)
