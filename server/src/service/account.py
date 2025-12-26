from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.utils.exceptions.base import BaseAppException
from src.models.db.account import Account
from src.models.schemas.account import AccountCreate, AccountRead, AccountUpdate
from src.models.schemas.response import ResponseModel
from src.models.schemas.transaction import TransactionRead
from src.repository.account import AccountRepository
from src.repository.currency import CurrencyRepository
from src.repository.recurring_transaction import RecurringTransactionRepository
from src.repository.transaction import TransactionRepository
from src.repository.user_pref import UserPrefRepository
from src.service.base import BaseService


class AccountService(BaseService[Account, AccountRepository]):
    """Service for managing accounts"""

    def __init__(self):
        repo = AccountRepository()
        self.user_pref_repo = UserPrefRepository()
        self.currency_repo = CurrencyRepository()
        self.transaction_repo = TransactionRepository()
        self.recurring_transaction_repo = RecurringTransactionRepository()
        super().__init__(repo)

    async def create_account(
        self,
        session: AsyncSession,
        user_id: UUID,
        account_data: AccountCreate,
    ) -> ResponseModel[AccountRead]:
        """Create a new account.

        Args:
            account_data (AccountCreate): The data for the new account.
        Returns:
            Account: The created account instance.
        """
        account_dict = account_data.model_dump()
        if not account_data.currency_code:
            user_pref = await self.user_pref_repo.get_by_user_id(session, user_id)
            if not user_pref or not user_pref.default_currency_id:
                raise BaseAppException(
                    "Currency symbol must be provided if no default is set.",
                    status_code=400,
                )
            account_dict["currency_id"] = user_pref.default_currency_id

        else:
            currency = await self.currency_repo.get_by_code(
                session, account_data.currency_code.upper()
            )
            if not currency:
                raise BaseAppException(
                    f"Currency with code '{account_data.currency_code}' not found.",
                    status_code=404,
                )
            account_dict["currency_id"] = currency.id

        account_dict["user_id"] = user_id
        new_account = await self.repository.create(session, account_dict)
        return ResponseModel(
            message="Account created successfully.",
            data=AccountRead.model_validate(new_account),
        )

    async def get_account_by_id(
        self,
        session: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> ResponseModel[AccountRead]:
        """Retrieve an account by its ID.

        Args:
            account_id (UUID): The ID of the account to retrieve.
        Returns:
            Account | None: The account instance if found, else None.
        """
        account = await self.repository.get_by_id(session, account_id)
        if not account or account.user_id != user_id:
            raise BaseAppException("Account not found.", status_code=404)
        currency_code = account.currency.code
        account_read = AccountRead.model_validate(
            {**account.__dict__, "currency_code": currency_code}
        )
        return ResponseModel(
            message="Account retrieved successfully.",
            data=account_read,
        )

    async def get_all_accounts(
        self, session: AsyncSession, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> ResponseModel[list[AccountRead]]:
        """Retrieve all accounts for a user.

        Args:
            user_id (UUID): The ID of the user whose accounts to retrieve.
        Returns:
            list[Account]: A list of account instances.
        """
        accounts, meta = await self.repository.get_accounts_by_user_id(
            session, user_id, page, page_size
        )
        account_reads = [
            AccountRead.model_validate(
                {**account.__dict__, "currency_code": account.currency.code}
            )
            for account in accounts
        ]
        return ResponseModel(
            message="Accounts retrieved successfully.",
            data=account_reads,
            meta=meta,
        )

    async def get_transactions_for_account(
        self,
        session: AsyncSession,
        account_id: UUID,
        user_id: UUID,
        page: int,
        page_size: int,
    ) -> ResponseModel[list[TransactionRead]]:
        transactions, meta = await self.repository.get_transactions_for_account(
            session, account_id, user_id, page, page_size
        )
        transaction_reads = [
            TransactionRead.model_validate(
                {
                    **transaction.__dict__,
                    "currency_code": transaction.account.currency.code,
                }
            )
            for transaction in transactions
        ]
        return ResponseModel(
            message="Transactions retrieved successfully.",
            data=transaction_reads,
            meta=meta,
        )

    async def update_account(
        self,
        session: AsyncSession,
        user_id: UUID,
        account_id: UUID,
        account_data: AccountUpdate,
    ) -> ResponseModel[AccountRead]:
        """Update an existing account.

        Args:
            account_id (UUID): The ID of the account to update.
            account_data (AccountUpdate): The updated account data.
        Returns:
            Account: The updated account instance.
        """
        existing_account = await self.repository.get_by_id(session, account_id)
        if not existing_account or existing_account.user_id != user_id:
            raise BaseAppException("Account not found.", status_code=404)

        account_data_dict = account_data.model_dump(exclude_unset=True)
        if account_data.currency_code:
            currency = await self.currency_repo.get_by_code(
                session, account_data.currency_code.upper()
            )
            if not currency:
                raise BaseAppException(
                    f"Currency with code '{account_data.currency_code}' not found.",
                    status_code=404,
                )
            account_data_dict["currency_id"] = currency.id
            account_data_dict.pop("currency_code", None)
            print("Account data after currency update:", account_data_dict)

        updated_account = await self.repository.update(
            session, account_id, account_data_dict
        )
        if not updated_account:
            raise BaseAppException("Failed to update account.", status_code=500)
        currency_code = updated_account.currency.code
        return ResponseModel(
            message="Account updated successfully.",
            data=AccountRead.model_validate(
                {**updated_account.__dict__, "currency_code": currency_code}
            ),
        )

    async def delete_account(
        self,
        session: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> ResponseModel[None]:
        """Delete an account and handle related data adjustments.

        Args:
            account_id (UUID): The ID of the account to delete.
        Returns:
            ResponseModel: A response indicating the result of the deletion.
        Raises:
            BaseAppException: If the account does not exist.
        """
        # Fetch the account to ensure it exists
        account = await self.repository.delete_for_user(session, user_id, account_id)
        if not account:
            raise BaseAppException("Account not found.", status_code=404)
        return ResponseModel(message="Account deleted successfully.", data=None)


account_service = AccountService()
