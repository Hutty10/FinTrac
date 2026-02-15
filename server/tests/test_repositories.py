"""
Unit tests for repository layer.
Tests database operations without hitting the service layer.
"""

from uuid import uuid4

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.account import Account, AccountType
from src.models.db.currency import Currency
from src.models.db.permission import Role
from src.models.db.transaction import Transaction, TransactionType
from src.models.db.user import User
from src.repository.account import AccountRepository
from src.repository.transaction import TransactionRepository
from src.repository.user import UserRepository


class TestUserRepository:
    """Test cases for UserRepository."""

    @pytest.fixture
    def user_repo(self):
        """Create a UserRepository instance."""
        return UserRepository()

    @pytest.mark.asyncio
    async def test_get_by_email_found(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        user_repo: UserRepository,
    ):
        """Test retrieving a user by email when user exists."""
        user = await user_repo.get_by_email(db_session_with_data, test_user.email)

        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(
        self, db_session_with_data: AsyncSession, user_repo: UserRepository
    ):
        """Test retrieving a user by email when user doesn't exist."""
        user = await user_repo.get_by_email(
            db_session_with_data, "nonexistent@example.com"
        )

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_username_found(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        user_repo: UserRepository,
    ):
        """Test retrieving a user by username when user exists."""
        if test_user.username:
            user = await user_repo.get_by_username(
                db_session_with_data, test_user.username
            )
            assert user is not None
            assert user.username == test_user.username
            assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(
        self, db_session_with_data: AsyncSession, user_repo: UserRepository
    ):
        """Test retrieving a user by username when user doesn't exist."""
        user = await user_repo.get_by_username(db_session_with_data, "nonexistent_user")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_role_id_success(
        self, db_session_with_data: AsyncSession, user_repo: UserRepository
    ):
        """Test retrieving user role ID."""
        role_id = await user_repo.get_user_role_id(db_session_with_data)

        assert role_id is not None
        # Verify the role exists
        role = await db_session_with_data.get(Role, role_id)
        assert role is not None
        assert role.name == "user"

    @pytest.mark.asyncio
    async def test_update_last_login(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        user_repo: UserRepository,
    ):
        """Test updating user's last login timestamp."""

        old_last_login = test_user.last_login
        await user_repo.update_last_login(db_session_with_data, test_user)

        # Refresh to get updated data
        await db_session_with_data.refresh(test_user)
        assert test_user.last_login is not None
        assert test_user.last_login > old_last_login if old_last_login else True

    @pytest.mark.asyncio
    async def test_create_user(
        self, db_session_with_data: AsyncSession, test_user_data: dict
    ):
        """Test creating a new user."""
        role = (
            await db_session_with_data.exec(select(Role).where(Role.name == "user"))
        ).first()

        if role is not None:
            new_user = User(
                id=uuid4(),
                email="newuser@example.com",
                username="newuser",
                first_name="New",
                last_name="User",
                hashed_password="hashed_password",
                role_id=role.id,
                is_active=True,
                is_verified=False,
                is_deleted=False,
            )

            db_session_with_data.add(new_user)
            await db_session_with_data.commit()
            await db_session_with_data.refresh(new_user)

            # Verify user was created
            user = await db_session_with_data.get(User, new_user.id)
            assert user is not None
            assert user.email == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_get_by_id(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        user_repo: UserRepository,
    ):
        """Test retrieving a user by ID."""
        user = await db_session_with_data.get(User, test_user.id)

        assert user is not None
        assert user.id == test_user.id


class TestAccountRepository:
    """Test cases for AccountRepository."""

    @pytest.fixture
    def account_repo(self):
        """Create an AccountRepository instance."""
        return AccountRepository()

    @pytest.mark.asyncio
    async def test_get_accounts_by_user_id(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        test_account: Account,
        account_repo: AccountRepository,
    ):
        """Test retrieving accounts for a specific user."""
        accounts, meta = await account_repo.get_accounts_by_user_id(
            db_session_with_data, test_user.id, page=1, page_size=10
        )

        assert len(accounts) == 1
        assert accounts[0].id == test_account.id
        assert meta["total_items"] == 1
        assert meta["page"] == 1
        assert meta["page_size"] == 10

    @pytest.mark.asyncio
    async def test_get_accounts_by_user_id_pagination(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        account_repo: AccountRepository,
    ):
        """Test pagination in get_accounts_by_user_id."""
        currency = (await db_session_with_data.exec(select(Currency))).first()

        # Create multiple accounts
        if currency:
            for i in range(15):
                account = Account(
                    id=uuid4(),
                    user_id=test_user.id,
                    currency_id=currency.id,
                    name=f"Account {i}",
                    account_type=AccountType.BANK.value,
                    balance=1000.0 + i,
                )
                db_session_with_data.add(account)
            await db_session_with_data.commit()

            # Test first page
            accounts_page_1, meta_page_1 = await account_repo.get_accounts_by_user_id(
                db_session_with_data, test_user.id, page=1, page_size=10
            )

            assert len(accounts_page_1) >= 10
            assert meta_page_1["total_items"] >= 15
            assert meta_page_1["total_pages"] >= 2

    @pytest.mark.asyncio
    async def test_delete_for_user_success(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        test_account: Account,
        account_repo: AccountRepository,
    ):
        """Test deleting an account for a user."""
        result = await account_repo.delete_for_user(
            db_session_with_data, test_user.id, test_account.id
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_for_user_not_found(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        account_repo: AccountRepository,
    ):
        """Test deleting a non-existent account."""
        result = await account_repo.delete_for_user(
            db_session_with_data, test_user.id, uuid4()
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_for_user_wrong_owner(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        test_account: Account,
        test_user_data_2: dict,
        account_repo: AccountRepository,
    ):
        """Test that user cannot delete another user's account."""
        role = (
            await db_session_with_data.exec(select(Role).where(Role.name == "user"))
        ).first()

        if role is not None:
            other_user = User(
                id=uuid4(),
                email=test_user_data_2["email"],
                username=test_user_data_2["username"],
                first_name=test_user_data_2["first_name"],
                last_name=test_user_data_2["last_name"],
                hashed_password="hashed_password",
                role_id=role.id,
                is_active=True,
                is_verified=True,
                is_deleted=False,
            )
            db_session_with_data.add(other_user)
            await db_session_with_data.commit()

            result = await account_repo.delete_for_user(
                db_session_with_data, other_user.id, test_account.id
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_update_balance(
        self,
        db_session_with_data: AsyncSession,
        test_account: Account,
        account_repo: AccountRepository,
    ):
        """Test updating account balance."""
        original_balance = test_account.balance
        change_amount = 100.0

        await account_repo.update_balance(
            db_session_with_data, test_account.id, change_amount
        )

        # Refresh and verify
        await db_session_with_data.refresh(test_account)
        assert test_account.balance == original_balance + change_amount

    @pytest.mark.asyncio
    async def test_update_balance_negative(
        self,
        db_session_with_data: AsyncSession,
        test_account: Account,
        account_repo: AccountRepository,
    ):
        """Test updating account balance with negative amount."""
        original_balance = test_account.balance
        change_amount = -50.0

        await account_repo.update_balance(
            db_session_with_data, test_account.id, change_amount
        )

        await db_session_with_data.refresh(test_account)
        assert test_account.balance == original_balance + change_amount


class TestTransactionRepository:
    """Test cases for TransactionRepository."""

    @pytest.fixture
    def transaction_repo(self):
        """Create a TransactionRepository instance."""
        return TransactionRepository()

    @pytest.mark.asyncio
    async def test_get_by_account_id(
        self,
        db_session_with_data: AsyncSession,
        test_account: Account,
        transaction_repo: TransactionRepository,
    ):
        """Test retrieving transactions for an account."""
        from datetime import datetime, timezone

        # Create a transaction
        currency = (await db_session_with_data.exec(select(Currency))).first()

        if currency is not None:
            transaction = Transaction(
                id=uuid4(),
                account_id=test_account.id,
                currency_id=currency.id,
                amount=100.0,
                type=TransactionType.INCOME,
                description="Test transaction",
                category_id=None,
                to_account_id=None,
                transaction_date=datetime.now(timezone.utc),
            )
            db_session_with_data.add(transaction)
            await db_session_with_data.commit()

            # Retrieve transactions
            transactions, meta = await transaction_repo.get_by_account_id(
                db_session_with_data, test_account.id, page=1, page_size=10
            )

            assert len(transactions) >= 1
            assert transactions[0].id == transaction.id
            assert transactions[0].amount == 100.0
