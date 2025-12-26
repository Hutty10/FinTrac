from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.user_pref import UserPreference
from src.repository.base import BaseRepository


class UserPrefRepository(BaseRepository[UserPreference]):
    def __init__(self):
        super().__init__(UserPreference)

    async def get_by_user_id(
        self, session: AsyncSession, user_id: UUID
    ) -> UserPreference | None:
        """Retrieve user preferences by user ID."""
        statement = select(self.model).where(self.model.user_id == user_id)
        result = await session.exec(statement)
        return result.first()
