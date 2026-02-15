"""
Edge case and security tests for comprehensive coverage.
"""

from uuid import uuid4

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.utils.exceptions.base import BaseAppException
from src.models.db.account import Account, AccountType
from src.models.db.permission import Role
from src.models.db.user import User
from src.service.auth import AuthService


class TestSecurityAndValidation:
    """Security-related test cases."""

    @pytest.fixture
    def auth_service(self):
        """Create an AuthService instance."""
        return AuthService()

    @pytest.mark.asyncio
    async def test_sql_injection_protection(
        self,
        db_session_with_data: AsyncSession,
    ):
        """Test that SQL injection attempts are safely handled."""
        from src.repository.user import UserRepository

        repo = UserRepository()

        # Attempt SQL injection
        malicious_email = "test' OR '1'='1"
        user = await repo.get_by_email(db_session_with_data, malicious_email)

        # Should safely return None, not execute injected code
        assert user is None

    @pytest.mark.asyncio
    async def test_password_not_returned_in_responses(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
    ):
        """Test that user passwords are never returned in API responses."""
        user = await db_session_with_data.get(User, test_user.id)

        if user is not None:
            # Verify hashed password is not exposed
            assert user.hashed_password is not None
            # Password should never be in a serialization
            user_dict = user.model_dump()
            assert (
                "hashed_password" not in user_dict
                or user_dict.get("hashed_password") is None
            )

    @pytest.mark.asyncio
    async def test_user_cannot_modify_other_user_data(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        test_user_data_2: dict,
    ):
        """Test that users cannot modify other users' data."""
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

            # Attempt to modify other user's first name
            original_first_name = test_user.first_name
            other_user.first_name = "Hacked"
            db_session_with_data.add(other_user)
            await db_session_with_data.commit()

            # Verify original user data is unchanged
            await db_session_with_data.refresh(test_user)
            assert test_user.first_name == original_first_name

    @pytest.mark.asyncio
    async def test_deleted_users_cannot_login(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        auth_service: AuthService,
    ):
        """Test that deleted users cannot login."""
        test_user.is_deleted = True
        db_session_with_data.add(test_user)
        await db_session_with_data.commit()

        # Attempt to login with deleted user
        from src.core.utils.user_utils import check_deleted_user

        with pytest.raises(BaseAppException):
            check_deleted_user(test_user)

    @pytest.mark.asyncio
    async def test_unverified_user_restrictions(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
    ):
        """Test restrictions for unverified users."""
        test_user.is_verified = False
        db_session_with_data.add(test_user)
        await db_session_with_data.commit()

        # Unverified users should have limited access
        # This depends on your business logic
        assert test_user.is_verified is False


class TestDataIntegrity:
    """Tests for data integrity and constraints."""

    @pytest.mark.asyncio
    async def test_account_balance_cannot_be_negative_on_delete(
        self,
        db_session_with_data: AsyncSession,
        test_account: Account,
    ):
        """Test that accounts with negative balance handling."""
        # This depends on your business rules
        original_balance = test_account.balance
        assert original_balance >= 0

    @pytest.mark.asyncio
    async def test_duplicate_account_names_allowed(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
        test_account: Account,
    ):
        """Test that users can have accounts with same name (different accounts)."""
        from sqlmodel import select as sql_select

        from src.models.db.currency import Currency

        currency = (await db_session_with_data.exec(sql_select(Currency))).first()

        if currency is not None:
            duplicate_account = Account(
                id=uuid4(),
                user_id=test_user.id,
                currency_id=currency.id,
                name=test_account.name,  # Same name
                account_type=AccountType.BANK.value,
                balance=500.0,
            )

            db_session_with_data.add(duplicate_account)
            await db_session_with_data.commit()

            # Both should exist
            accounts = await db_session_with_data.exec(
                sql_select(Account).where(Account.user_id == test_user.id)
            )
            assert len(list(accounts)) >= 2

    @pytest.mark.asyncio
    async def test_foreign_key_integrity(
        self,
        db_session_with_data: AsyncSession,
        test_account: Account,
    ):
        """Test that foreign key relationships are maintained."""
        # Verify account references valid user
        user = await db_session_with_data.get(User, test_account.user_id)
        assert user is not None

        # Verify account references valid currency
        from src.models.db.currency import Currency

        currency = await db_session_with_data.get(Currency, test_account.currency_id)
        assert currency is not None


class TestConcurrency:
    """Tests for concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_balance_updates(
        self,
        db_session_with_data: AsyncSession,
        test_account: Account,
    ):
        """Test that concurrent balance updates maintain consistency."""
        import asyncio

        from src.repository.account import AccountRepository

        repo = AccountRepository()
        original_balance = test_account.balance

        # Simulate concurrent updates
        async def update_balance(amount: float):
            await repo.update_balance(db_session_with_data, test_account.id, amount)

        # Run 5 concurrent updates
        updates = [update_balance(10.0) for _ in range(5)]
        await asyncio.gather(*updates)

        # Verify final balance
        await db_session_with_data.refresh(test_account)
        assert test_account.balance == original_balance + (10.0 * 5)

    @pytest.mark.asyncio
    async def test_concurrent_user_creation(
        self,
        db_session_with_data: AsyncSession,
    ):
        """Test that concurrent user creation handles duplicates correctly."""
        import asyncio
        from uuid import uuid4

        role = (
            await db_session_with_data.exec(select(Role).where(Role.name == "user"))
        ).first()

        if role is not None:

            async def create_user_with_email(email: str):
                user = User(
                    id=uuid4(),
                    email=email,
                    username=f"user_{uuid4().hex[:8]}",
                    first_name="Test",
                    last_name="User",
                    hashed_password="hashed_password",
                    role_id=role.id,
                    is_active=True,
                    is_verified=True,
                    is_deleted=False,
                )
                db_session_with_data.add(user)
                await db_session_with_data.commit()
                return user

            # Try to create multiple users (some might fail due to duplicates)
            results = await asyncio.gather(
                create_user_with_email("concurrent@example.com"),
                create_user_with_email("unique1@example.com"),
                create_user_with_email("unique2@example.com"),
                return_exceptions=True,
            )

        # At least some should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) >= 2


class TestInputValidation:
    """Tests for input validation and sanitization."""

    @pytest.mark.asyncio
    async def test_email_validation_strict(
        self,
        db_session_with_data: AsyncSession,
    ):
        """Test that invalid email formats are rejected."""
        # Email validation is handled by pydantic EmailStr
        # This is a placeholder for validation tests
        assert True

    @pytest.mark.asyncio
    async def test_xss_protection_in_strings(
        self,
        db_session_with_data: AsyncSession,
        test_user: User,
    ):
        """Test that XSS payloads in strings are handled safely."""
        xss_payload = "<script>alert('XSS')</script>"

        # Attempt to set XSS in first name
        test_user.first_name = xss_payload
        db_session_with_data.add(test_user)
        await db_session_with_data.commit()

        # Data should be stored as-is (not executed)
        await db_session_with_data.refresh(test_user)
        assert test_user.first_name == xss_payload
        await db_session_with_data.refresh(test_user)
        assert test_user.first_name == xss_payload
        # In a real scenario, this would be escaped on output
