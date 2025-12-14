from uuid import UUID

from sqlmodel import update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.account import Account
from src.repository.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    """Repository class for account-related operations"""

    def __init__(self):
        super().__init__(Account)

    async def update_balance(
        self, session: AsyncSession, account_id: UUID, change_amount: float
    ) -> None:
        """Atomically updates the balance of an account by the given amount."""      

        statement = (
            update(self.model)
            .where(self.model.id == account_id) # type: ignore
            .values(balance=self.model.balance + change_amount)
        )
        await session.exec(statement)
        await session.commit()
