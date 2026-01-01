from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.user_device import UserDevice
from src.repository.base import BaseRepository


class UserDeviceRepository(BaseRepository[UserDevice]):
    def __init__(self):
        super().__init__(UserDevice)

    async def get_by_device_id(
        self, session: AsyncSession, user_id: UUID, device_id: str
    ) -> UserDevice | None:
        statement = select(UserDevice).where(
            UserDevice.user_id == user_id,
            UserDevice.device_id == device_id,
        )
        result = await session.exec(statement)
        return result.first()
