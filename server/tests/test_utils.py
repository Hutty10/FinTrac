"""
Test utilities and helper functions for the test suite.
"""

from uuid import UUID

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.account import Account
from src.models.db.currency import Currency
from src.models.db.transaction import Transaction
from src.models.db.user import User


class AsyncTestHelper:
    """Helper class for async testing utilities."""

    @staticmethod
    async def create_test_transaction(
        session: AsyncSession,
        account: Account,
        currency: Currency,
        amount: float = 100.0,
        description: str = "Test transaction",
        transaction_type: str = "income",
    ) -> Transaction:
        """Create a test transaction."""
        from datetime import datetime, timezone
        from uuid import uuid4

        from src.models.db.transaction import TransactionType

        tx_type = (
            TransactionType.INCOME
            if transaction_type.lower() == "income"
            else TransactionType.EXPENSE
        )

        transaction = Transaction(
            id=uuid4(),
            account_id=account.id,
            currency_id=currency.id,
            amount=amount,
            type=tx_type,
            description=description,
            category_id=None,
            to_account_id=None,
            transaction_date=datetime.now(timezone.utc),
        )

        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)

        return transaction

    @staticmethod
    async def create_multiple_transactions(
        session: AsyncSession,
        account: Account,
        currency: Currency,
        count: int = 5,
    ) -> list[Transaction]:
        """Create multiple test transactions."""
        transactions = []

        for i in range(count):
            transaction = await AsyncTestHelper.create_test_transaction(
                session,
                account,
                currency,
                amount=100.0 + (i * 10),
                description=f"Test transaction {i + 1}",
            )
            transactions.append(transaction)

        return transactions

    @staticmethod
    async def verify_account_balance(
        session: AsyncSession,
        account: Account,
        expected_balance: float,
    ) -> bool:
        """Verify account balance matches expected value."""
        await session.refresh(account)
        return (
            abs(account.balance - expected_balance) < 0.01
        )  # Allow for floating point errors


class MockDataGenerator:
    """Generate mock data for testing."""

    @staticmethod
    def generate_user_data(
        email: str = "test@example.com",
        username: str = "testuser",
        first_name: str = "Test",
        last_name: str = "User",
        password: str = "SecurePassword123!",
    ) -> dict:
        """Generate test user data."""
        return {
            "email": email,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
            "phone_number": "+1234567890",
        }

    @staticmethod
    def generate_account_data(
        name: str = "Test Account",
        account_type: str = "checking",
        balance: float = 1000.0,
    ) -> dict:
        """Generate test account data."""
        return {
            "name": name,
            "account_type": account_type,
            "balance": balance,
        }

    @staticmethod
    def generate_transaction_data(
        amount: float = 100.0,
        transaction_type: str = "income",
        description: str = "Test transaction",
    ) -> dict:
        """Generate test transaction data."""
        return {
            "amount": amount,
            "transaction_type": transaction_type,
            "description": description,
        }

    @staticmethod
    def generate_budget_data(
        name: str = "Test Budget",
        limit: float = 500.0,
    ) -> dict:
        """Generate test budget data."""
        return {
            "name": name,
            "limit": limit,
        }


class AssertionHelpers:
    """Custom assertion helpers for common test scenarios."""

    @staticmethod
    def assert_response_success(response: dict, status_code: int = 200) -> None:
        """Assert that API response indicates success."""
        assert response.get("status") == "success"
        assert response.get("code") == status_code

    @staticmethod
    def assert_response_error(response: dict, status_code: int = 400) -> None:
        """Assert that API response indicates an error."""
        assert response.get("status") == "error"
        assert response.get("code") == status_code

    @staticmethod
    def assert_paginated_response(
        response: dict,
        page: int = 1,
        page_size: int = 10,
        min_items: int = 0,
    ) -> None:
        """Assert that response contains valid pagination metadata."""
        data = response.get("data", {})
        assert data.get("page") == page
        assert data.get("page_size") == page_size
        assert len(data.get("items", [])) >= min_items
        assert "total_items" in data
        assert "total_pages" in data

    @staticmethod
    def assert_user_object(user: dict, email: str, username: str) -> None:
        """Assert that user object has expected properties."""
        assert user.get("email") == email
        assert user.get("username") == username
        assert "id" in user
        assert "created_at" in user

    @staticmethod
    def assert_account_object(account: dict, name: str) -> None:
        """Assert that account object has expected properties."""
        assert account.get("name") == name
        assert "id" in account
        assert "balance" in account
        assert "account_type" in account


class TestDataManager:
    """Manages test data lifecycle."""

    def __init__(self):
        """Initialize test data manager."""
        self.created_users: list[UUID] = []
        self.created_accounts: list[UUID] = []
        self.created_transactions: list[UUID] = []

    async def cleanup(self, session: AsyncSession) -> None:
        """Clean up all created test data."""

        from src.models.db.account import Account
        from src.models.db.transaction import Transaction

        # Delete transactions
        for tx_id in self.created_transactions:
            tx = await session.get(Transaction, tx_id)
            if tx:
                await session.delete(tx)

        # Delete accounts
        for acc_id in self.created_accounts:
            acc = await session.get(Account, acc_id)
            if acc:
                await session.delete(acc)

        # Delete users
        for user_id in self.created_users:
            user = await session.get(User, user_id)
            if user:
                await session.delete(user)

        await session.commit()

    def track_user(self, user_id: UUID) -> None:
        """Track created user ID."""
        self.created_users.append(user_id)

    def track_account(self, account_id: UUID) -> None:
        """Track created account ID."""
        self.created_accounts.append(account_id)

    def track_transaction(self, transaction_id: UUID) -> None:
        """Track created transaction ID."""
        self.created_transactions.append(transaction_id)


class PerformanceAssertions:
    """Performance-related assertion helpers."""

    @staticmethod
    def assert_response_time(
        elapsed_time: float,
        max_milliseconds: float = 1000,
    ) -> None:
        """Assert that operation completed within expected time."""
        elapsed_ms = elapsed_time * 1000
        assert elapsed_ms <= max_milliseconds, (
            f"Operation took {elapsed_ms}ms, expected <= {max_milliseconds}ms"
        )

    @staticmethod
    def assert_query_count(
        query_count: int,
        expected_count: int,
        tolerance: int = 1,
    ) -> None:
        """Assert that number of queries is as expected."""
        assert abs(query_count - expected_count) <= tolerance, (
            f"Expected ~{expected_count} queries, got {query_count}"
        )


@pytest.fixture
def async_helper():
    """Provide async test helper."""
    return AsyncTestHelper()


@pytest.fixture
def mock_data_generator():
    """Provide mock data generator."""
    return MockDataGenerator()


@pytest.fixture
def assertion_helpers():
    """Provide assertion helpers."""
    return AssertionHelpers()


@pytest.fixture
def test_data_manager():
    """Provide test data manager."""
    return TestDataManager()


@pytest.fixture
def performance_assertions():
    """Provide performance assertions."""
    return PerformanceAssertions()
