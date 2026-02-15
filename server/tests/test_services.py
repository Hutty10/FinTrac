"""
Unit tests for service layer.
Tests business logic without hitting the database directly.
"""

from uuid import uuid4

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.utils.exceptions.base import BaseAppException
from src.models.db.account import Account, AccountType
from src.models.db.permission import Role
from src.models.db.user import User
from src.models.schemas.auth import RegisterUserSchema
from src.service.account import AccountService
from src.service.auth import AuthService


class TestAuthService:
    """Test cases for AuthService."""

    @pytest.fixture
    def auth_service(self):
        """Create an AuthService instance."""
        return AuthService()

    @pytest.mark.asyncio
    async def test_register_user_success(
        self,
        db_session_with_data: AsyncSession,
        auth_service: AuthService,
        valid_registration_payload: dict,
    ):
        """Test successful user registration."""
        # Register a new user
        register_data = RegisterUserSchema(**valid_registration_payload)
        response = await auth_service.register_user(db_session_with_data, register_data)

        assert response is not None
        # Verify user was created
        user = await auth_service.repository.get_by_email(
            db_session_with_data, valid_registration_payload["email"]
        )
        assert user is not None
        assert user.email == valid_registration_payload["email"]

    @pytest.mark.asyncio
    async def test_register_user_email_already_exists(
        self,
        db_session_with_data: AsyncSession,
        auth_service: AuthService,
        test_user: User,
        valid_registration_payload: dict,
    ):
        """Test registration fails when email already exists."""
        valid_registration_payload["email"] = test_user.email

        register_data = RegisterUserSchema(**valid_registration_payload)

        with pytest.raises(BaseAppException) as exc_info:
            await auth_service.register_user(db_session_with_data, register_data)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_register_user_username_already_exists(
        self,
        db_session_with_data: AsyncSession,
        auth_service: AuthService,
        test_user: User,
        valid_registration_payload: dict,
    ):
        """Test registration fails when username already exists."""
        valid_registration_payload["username"] = test_user.username

        register_data = RegisterUserSchema(**valid_registration_payload)

        with pytest.raises(BaseAppException) as exc_info:
            await auth_service.register_user(db_session_with_data, register_data)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_register_user_terms_not_accepted(
        self,
        db_session_with_data: AsyncSession,
        auth_service: AuthService,
        valid_registration_payload: dict,
    ):
        """Test registration fails when terms are not accepted."""
        valid_registration_payload["accept_terms"] = False

        register_data = RegisterUserSchema(**valid_registration_payload)

        with pytest.raises(BaseAppException) as exc_info:
            await auth_service.register_user(db_session_with_data, register_data)

        assert exc_info.value.status_code == 400
        assert "Terms" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_register_user_weak_password(
        self,
        db_session_with_data: AsyncSession,
        auth_service: AuthService,
        valid_registration_payload: dict,
    ):
        """Test registration with weak password."""
        valid_registration_payload["password"] = "weak"
        valid_registration_payload["confirm_password"] = "weak"

        register_data = RegisterUserSchema(**valid_registration_payload)

        with pytest.raises(BaseAppException):
            await auth_service.register_user(db_session_with_data, register_data)

    @pytest.mark.asyncio
    async def test_register_user_password_mismatch(
        self,
        db_session_with_data: AsyncSession,
        auth_service: AuthService,
        mismatched_password_payload: dict,
    ):
        """Test registration with mismatched passwords."""
        mismatched_password_payload["accept_terms"] = True

        register_data = RegisterUserSchema(**mismatched_password_payload)

        with pytest.raises(BaseAppException) as exc_info:
            await auth_service.register_user(db_session_with_data, register_data)

        assert "password" in exc_info.value.message.lower()


class TestAccountService:
    """Test cases for AccountService."""

    @pytest.fixture
    def account_service(self):
        """Create an AccountService instance."""
        return AccountService()

    @pytest.mark.asyncio
    async def test_create_account_success(
        self,
        db_session_with_data: AsyncSession,
        account_service: AccountService,
        test_user: User,
    ):
        """Test successful account creation."""
        account_data = {
            "name": "New Savings Account",
            "account_type": AccountType.BANK,
            "currency_code": "USD",
            "balance": 500.0,
        }

        # Create account
        from src.models.schemas.account import AccountCreate

        create_data = AccountCreate(**account_data)

        result = await account_service.create_account(
            db_session_with_data, test_user.id, create_data
        )

        assert result is not None
        assert result.data is not None
        assert result.data.name == "New Savings Account"
        assert result.data.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_account_by_id_success(
        self,
        db_session_with_data: AsyncSession,
        account_service: AccountService,
        test_user: User,
        test_account: Account,
    ):
        """Test retrieving an account by ID."""
        response = await account_service.get_account_by_id(
            db_session_with_data, test_user.id, test_account.id
        )

        assert response is not None
        assert response.data is not None
        assert response.data.id == test_account.id
        assert response.data.name == test_account.name

    @pytest.mark.asyncio
    async def test_get_account_unauthorized(
        self,
        db_session_with_data: AsyncSession,
        account_service: AccountService,
        test_user: User,
        test_account: Account,
        test_user_data_2: dict,
    ):
        """Test that user cannot access another user's account."""
        # Create another user
        role = (
            await db_session_with_data.exec(
                __import__("sqlmodel").select(Role).where(Role.name == "user")
            )
        ).first()

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

        with pytest.raises(BaseAppException) as exc_info:
            await account_service.get_account_by_id(
                db_session_with_data, other_user.id, test_account.id
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_account_success(
        self,
        db_session_with_data: AsyncSession,
        account_service: AccountService,
        test_user: User,
        test_account: Account,
    ):
        """Test updating an account."""
        from src.models.schemas.account import AccountUpdate

        update_data = AccountUpdate(name="Updated Account Name")

        result = await account_service.update_account(
            db_session_with_data, test_user.id, test_account.id, update_data
        )

        assert result is not None
        assert result.data is not None
        assert result.data.name == "Updated Account Name"

    @pytest.mark.asyncio
    async def test_delete_account_success(
        self,
        db_session_with_data: AsyncSession,
        account_service: AccountService,
        test_user: User,
        test_account: Account,
    ):
        """Test deleting an account."""
        result = await account_service.delete_account(
            db_session_with_data, test_user.id, test_account.id
        )

        assert result is not None
        assert result.message == "Account deleted successfully."

    @pytest.mark.asyncio
    async def test_get_user_accounts_success(
        self,
        db_session_with_data: AsyncSession,
        account_service: AccountService,
        test_user: User,
        test_account: Account,
    ):
        """Test retrieving all accounts for a user."""
        response = await account_service.get_all_accounts(
            db_session_with_data, test_user.id, page=1, page_size=10
        )

        assert response is not None
        assert response.data is not None
        assert len(response.data) >= 1
        assert any(acc.id == test_account.id for acc in response.data)
        if response.meta:
            assert response.meta.get("total_items", 0) >= 1
            assert response.meta.get("page", 1) == 1
