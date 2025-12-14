from datetime import datetime, timedelta, timezone
from uuid import UUID

from dateutil.relativedelta import relativedelta
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.utils.exceptions.base import BaseAppException
from src.models.db.account import AccountType
from src.models.db.recurring_transaction import RecurringTransaction
from src.models.db.transaction import Transaction, TransactionType
from src.models.schemas.response import ResponseModel
from src.models.schemas.transaction import (
    RecurringTransactionRead,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from src.repository.account import AccountRepository
from src.repository.recurring_transaction import RecurringTransactionRepository
from src.repository.streak import StreakRepository
from src.repository.transaction import TransactionRepository
from src.service.base import BaseService


class TransactionService(BaseService[Transaction, TransactionRepository]):
    def __init__(self):
        self.repository = TransactionRepository()
        self.account_repo = AccountRepository()
        self.streak_repo = StreakRepository()
        self.recurring_repo = RecurringTransactionRepository()
        super().__init__(self.repository)

    def _calculate_next_occurrence(
        self, start_date: datetime, interval: str
    ) -> datetime:
        """
        Calculates the next occurrence date based on the interval.
        Uses relativedelta for reliable month/year arithmetic.
        """
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)

        interval = interval.lower()

        if interval == "daily":
            next_date = start_date + timedelta(days=1)
        elif interval == "weekly":
            next_date = start_date + timedelta(weeks=1)
        elif interval == "monthly":
            next_date = start_date + relativedelta(months=1)
        elif interval == "yearly":
            next_date = start_date + relativedelta(years=1)
        else:
            raise BaseAppException(
                message=f"Invalid recurrence interval: {interval}",
                status_code=400,
            )

        return next_date

    async def create_transaction(
        self, session: AsyncSession, user_id: UUID, transaction_data: TransactionCreate
    ) -> ResponseModel[TransactionRead]:
        """Create a new transaction, update account balances, set up recurrence, and update streak."""

        now_aware = datetime.now(timezone.utc)
        transaction_date = transaction_data.transaction_date or now_aware
        if transaction_date.tzinfo is None:
            transaction_date = transaction_date.replace(tzinfo=timezone.utc)

        transaction_data.transaction_date = transaction_date

        account = await self.account_repo.get_by_id(
            session, transaction_data.account_id
        )
        if not account or account.user_id != user_id:
            raise BaseAppException(
                message="Source account not found or access denied",
                status_code=404,
            )

        to_account = None
        if account.account_type != AccountType.CASH:
            transaction_data.currency_id = account.currency_id
        elif not transaction_data.currency_id:
            raise BaseAppException(
                message="currency_id is required for Cash accounts",
                status_code=400,
            )

        if transaction_data.type == TransactionType.TRANSFER:
            if not transaction_data.to_account_id:
                raise BaseAppException(
                    message="to_account_id is required for Transfer transactions",
                    status_code=400,
                )
            to_account = await self.account_repo.get_by_id(
                session, transaction_data.to_account_id
            )
            if not to_account or to_account.user_id != user_id:
                raise BaseAppException(
                    message="Destination account not found or access denied",
                    status_code=404,
                )
            if account.currency_id != to_account.currency_id:
                raise BaseAppException(
                    message="Transfer accounts must have the same currency",
                    status_code=400,
                )
            transaction_data.currency_id = account.currency_id

        new_transaction = Transaction.model_validate(transaction_data)
        created_transaction = await self.repository.create(session, new_transaction)

        amount = transaction_data.amount

        if transaction_data.type == TransactionType.INCOME:
            await self.account_repo.update_balance(
                session, account_id=account.id, change_amount=amount
            )

        elif transaction_data.type == TransactionType.EXPENSE:
            await self.account_repo.update_balance(
                session, account_id=account.id, change_amount=-amount
            )

        elif transaction_data.type == TransactionType.TRANSFER and to_account:
            await self.account_repo.update_balance(
                session, account_id=account.id, change_amount=-amount
            )
            await self.account_repo.update_balance(
                session, account_id=to_account.id, change_amount=amount
            )

        recurring_transaction = None
        if transaction_data.recurring:
            next_date = self._calculate_next_occurrence(
                start_date=created_transaction.transaction_date,
                interval=transaction_data.recurring.interval,
            )

            recurring_transaction = RecurringTransaction(
                transaction_id=created_transaction.id,
                interval=transaction_data.recurring.interval,
                next_occurrence=next_date,
                is_active=transaction_data.recurring.is_active,
            )

            await self.recurring_repo.create(session, recurring_transaction)

        await self.streak_repo.increment_streak(session, user_id)

        # Reload transaction with recurring data if it exists
        created_transaction = await self.repository.get_by_id(
            session, created_transaction.id
        )

        data = TransactionRead.model_validate(
            {
                **created_transaction.model_dump(),  # type: ignore
                "recurring_transaction": RecurringTransactionRead.model_validate(
                    recurring_transaction
                )
                if recurring_transaction
                else None,
            }
        )

        return ResponseModel(
            message="Transaction created successfully"
            + (" and scheduled for recurrence" if transaction_data.recurring else ""),
            data=data,
        )

    async def get_all_transactions(
        self, session: AsyncSession, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> ResponseModel[list[TransactionRead]]:
        """Retrieve all transactions for the current user"""
        transactions, meta = await self.repository.get_by_user_id(
            session, user_id, page, page_size
        )
        transaction_reads = [TransactionRead.model_validate(tx) for tx in transactions]
        return ResponseModel(
            message="All transactions retrieved successfully",
            data=transaction_reads,
            meta=meta,
        )

    # async def get_all_recurring_transactions(
    #     self, session: AsyncSession, user_id: UUID, page: int = 1, page_size: int = 20
    # ) -> ResponseModel[list[RecurringTransactionRead]]:
    #     """Retrieve all recurring transactions for the current user"""
    #     transactions, meta = await self.repository.get_recurring_by_user_id(
    #         session, user_id, page, page_size
    #     )
    #     transaction_reads = [
    #         RecurringTransactionRead.model_validate(tx) for tx in transactions
    #     ]
    #     return ResponseModel(
    #         message="All recurring transactions retrieved successfully",
    #         data=transaction_reads,
    #         meta=meta,
    #     )

    async def get_transaction_by_id(
        self, session: AsyncSession, user_id: UUID, transaction_id: UUID
    ) -> ResponseModel[TransactionRead]:
        """Retrieve a transaction by its ID"""
        transaction = await self.repository.get_by_id(session, transaction_id)
        if not transaction:
            raise BaseAppException(
                message="Transaction not found",
                status_code=404,
            )
        account = await self.account_repo.get_by_id(session, transaction.account_id)
        if not account or account.user_id != user_id:
            raise BaseAppException(
                message="Access denied to this transaction",
                status_code=403,
            )
        return ResponseModel(
            message="Transaction retrieved successfully",
            data=TransactionRead.model_validate(transaction),
        )

    async def update_transaction(
        self,
        session: AsyncSession,
        user_id: UUID,
        transaction_id: UUID,
        transaction_data: TransactionUpdate,
    ) -> ResponseModel[TransactionRead]:
        """Update an existing transaction"""
        transaction = await self.repository.get_by_id(session, transaction_id)
        if not transaction:
            raise BaseAppException(
                message="Transaction not found",
                status_code=404,
            )
        account = await self.account_repo.get_by_id(session, transaction.account_id)
        if not account or account.user_id != user_id:
            raise BaseAppException(
                message="Access denied to this transaction",
                status_code=403,
            )

        # Update transaction fields
        update_data = transaction_data.model_dump(
            exclude={"recurring"}, exclude_unset=True
        )
        updated_transaction = await self.repository.update(
            session, transaction_id, update_data
        )

        # Update recurring transaction if provided
        if transaction_data.recurring:
            recurring_transaction = await self.recurring_repo.get_by_transaction_id(
                session, transaction_id
            )

            if not recurring_transaction:
                # Create new recurring transaction if it doesn't exist
                next_date = self._calculate_next_occurrence(
                    start_date=updated_transaction.transaction_date,  # type: ignore
                    interval=transaction_data.recurring.interval or "monthly",
                )
                recurring_transaction = RecurringTransaction(
                    transaction_id=transaction_id,
                    interval=transaction_data.recurring.interval or "monthly",
                    next_occurrence=next_date,
                    is_active=transaction_data.recurring.is_active
                    if transaction_data.recurring.is_active is not None
                    else True,
                )
                await self.recurring_repo.create(session, recurring_transaction)
            else:
                # Update existing recurring transaction
                update_data = transaction_data.recurring.model_dump(exclude_unset=True)

                # Recalculate next_occurrence if interval changed
                if transaction_data.recurring.interval:
                    update_data["next_occurrence"] = self._calculate_next_occurrence(
                        start_date=updated_transaction.transaction_date,  # type: ignore
                        interval=transaction_data.recurring.interval,
                    )

                await self.recurring_repo.update(
                    session,
                    recurring_transaction.id,
                    update_data,
                )

        # Reload transaction to get updated recurring data
        updated_transaction = await self.repository.get_by_id(session, transaction_id)

        return ResponseModel(
            message="Transaction updated successfully",
            data=TransactionRead.model_validate(updated_transaction),
        )

    async def delete_transaction(
        self, session: AsyncSession, user_id: UUID, transaction_id: UUID
    ) -> ResponseModel[None]:
        """Delete a transaction by its ID"""
        transaction = await self.repository.get_by_id(session, transaction_id)
        if not transaction:
            raise BaseAppException(
                message="Transaction not found",
                status_code=404,
            )
        account = await self.account_repo.get_by_id(session, transaction.account_id)
        if not account or account.user_id != user_id:
            raise BaseAppException(
                message="Access denied to this transaction",
                status_code=403,
            )
        await self.repository.delete(session, transaction_id)
        return ResponseModel(
            message="Transaction deleted successfully",
            data=None,
        )


transaction_service = TransactionService()
