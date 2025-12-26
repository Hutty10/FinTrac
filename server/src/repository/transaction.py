from typing import Any, Tuple
from uuid import UUID

from sqlmodel import desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.account import Account
from src.models.db.transaction import Transaction
from src.repository.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self):
        super().__init__(Transaction)

    async def get_by_account_id(
        self,
        session: AsyncSession,
        account_id: UUID,
        page: int,
        page_size: int,
    ) -> Tuple[list[Transaction], dict[str, Any]]:
        """Get paginated transactions for a specific account"""

        offset = (page - 1) * page_size

        conditions = self.model.account_id == account_id

        count_query = select(func.count()).select_from(self.model).where(conditions)
        total_result = await session.exec(count_query)
        total_count = total_result.one()

        query = (
            select(self.model)
            .where(conditions)
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await session.exec(query)
        transactions = list(result.all())

        meta = {
            "page": page,
            "page_size": page_size,
            "total_items": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
        }

        return transactions, meta

    async def get_by_user_id(
        self, session: AsyncSession, user_id: UUID, page: int, page_size: int
    ) -> Tuple[list[Transaction], dict[str, Any]]:
        """Get paginated transactions for a specific user"""

        offset = (page - 1) * page_size

        join_condition = self.model.account_id == Account.id
        filter_condition = Account.user_id == user_id

        count_query = (
            select(func.count())
            .select_from(self.model)
            .join(Account, onclause=join_condition)  # type: ignore
            .where(filter_condition)
        )
        total_result = await session.exec(count_query)
        total_count = total_result.one()

        query = (
            select(self.model)
            .join(Account, onclause=join_condition)  # type: ignore
            .where(filter_condition)
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await session.exec(query)
        transactions = list(result.all())

        meta = {
            "page": page,
            "page_size": page_size,
            "total_items": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
        }

        return transactions, meta

    async def get_recurring_by_user_id(
        self, session: AsyncSession, user_id: UUID, page: int, page_size: int
    ) -> Tuple[list[Transaction], dict[str, Any]]:
        """Get all recurring transactions for a specific user"""
        offset = (page - 1) * page_size

        join_condition = self.model.account_id == Account.id
        filter_condition = Account.user_id == user_id

        count_query = (
            select(func.count())
            .select_from(self.model)
            .join(Account, onclause=join_condition)  # type: ignore
            .where(filter_condition)
        )
        total_result = await session.exec(count_query)
        total_count = total_result.one()

        query = (
            select(self.model)
            .join(Account, onclause=join_condition)  # type: ignore
            .where(filter_condition)
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await session.exec(query)
        transactions = list(result.all())

        meta = {
            "page": page,
            "page_size": page_size,
            "total_items": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
        }

        return transactions, meta
