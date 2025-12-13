from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.currency import Currency
from src.repository.base import BaseRepository


class CurrencyRepository(BaseRepository[Currency]):
    def __init__(self):
        super().__init__(Currency)

    async def get_by_code(self, session: AsyncSession, code: str) -> Currency | None:
        """Get a currency by its code"""
        statement = select(self.model).where(self.model.code == code)
        result = await session.exec(statement)
        return result.first()
