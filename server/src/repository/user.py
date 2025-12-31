from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.permission import Role
from src.models.db.user import User
from src.repository.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository class for user-related operations"""

    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        """Get a user by email"""
        statement = select(self.model).where(self.model.email == email)
        result = await session.exec(statement)
        return result.first()

    async def get_user_role_id(self, session: AsyncSession) -> UUID:
        """Get the user role ID"""

        statement = select(Role).where(Role.name == "user")
        result = await session.exec(statement)
        default_role = result.first()
        if not default_role:
            raise Exception("User role not found")
        return default_role.id

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> User | None:
        """Get a user by username"""
        statement = select(self.model).where(self.model.username == username)
        result = await session.exec(statement)
        return result.first()

    async def update_last_login(self, session: AsyncSession, user: User) -> None:
        """Update the last login timestamp for a user"""
        user.last_login = datetime.now(timezone.utc)
        session.add(user)
        await session.commit()
        await session.refresh(user)


user_repository = UserRepository()
