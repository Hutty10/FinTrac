from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.recurring_transaction import RecurringTransaction
from src.repository.base import BaseRepository


class RecurringTransactionRepository(BaseRepository[RecurringTransaction]):
    def __init__(self):
        super().__init__(RecurringTransaction)

    async def get_by_transaction_id(
        self, session: AsyncSession, transaction_id: UUID
    ) -> RecurringTransaction | None:
        """Get a recurring transaction by its associated transaction ID"""
        query = select(self.model).where(self.model.transaction_id == transaction_id)
        result = await session.exec(query)
        return result.first()
