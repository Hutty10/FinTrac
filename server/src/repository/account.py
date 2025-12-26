from typing import Any, Tuple
from uuid import UUID

from sqlalchemy.orm import contains_eager
from sqlmodel import func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.account import Account
from src.models.db.transaction import Transaction
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
            .where(self.model.id == account_id)  # type: ignore
            .values(balance=self.model.balance + change_amount)
        )
        await session.exec(statement)
        await session.commit()

    async def get_accounts_by_user_id(
        self, session: AsyncSession, user_id: UUID, page: int, page_size: int
    ) -> Tuple[list[Account], dict[str, Any]]:
        """Retrieve all accounts for a specific user."""

        offset = (page - 1) * page_size

        conditions = self.model.user_id == user_id

        count_query = select(func.count()).select_from(self.model).where(conditions)
        total_result = await session.exec(count_query)
        total_count = total_result.one()

        query = (
            select(self.model)
            .where(conditions)
            .offset(offset)
            .limit(page_size)
            .order_by(self.model.created_at.desc())  # type: ignore
        )

        result = await session.exec(query)
        accounts = list(result.all())

        meta = {
            "page": page,
            "page_size": page_size,
            "total_items": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
        }

        return accounts, meta

    async def delete_for_user(
        self, session: AsyncSession, user_id: UUID, account_id: UUID
    ) -> bool:
        """Delete an account for a specific user."""

        statement = (
            select(self.model)
            .where(self.model.id == account_id)
            .where(self.model.user_id == user_id)
        )
        result = await session.exec(statement)
        account = result.one_or_none()
        if account:
            await session.delete(account)
            await session.commit()
            return True
        return False

    async def get_transactions_for_account(
        self,
        session: AsyncSession,
        account_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[list[Transaction], dict[str, Any]]:
        """Retrieve all transactions for a specific account."""

        offset = (page - 1) * page_size

        # Count query with explicit join
        count_query = (
            select(func.count())
            .select_from(Transaction)
            .join(Account, Transaction.account_id == Account.id)  # type: ignore
            .where(
                (Transaction.account_id == account_id) & (Account.user_id == user_id)
            )
        )
        total_count = await session.scalar(count_query) or 0

        # Data query with explicit join AND eager loading of relationships
        query = (
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)  # type: ignore
            .options(
                contains_eager(Transaction.account).contains_eager(Account.currency)
            )
            .where(
                (Transaction.account_id == account_id) & (Account.user_id == user_id)
            )
            .order_by(
                Transaction.transaction_date.desc(),  # type: ignore
                Transaction.created_at.desc(),  # type: ignore
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await session.exec(query)
        transactions = result.all()

        meta = {
            "page": page,
            "page_size": page_size,
            "total_items": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
        }

        return list(transactions), meta
