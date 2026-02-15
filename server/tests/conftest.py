"""
Pytest configuration and shared fixtures for all tests.
This module provides database, session, and application fixtures
for testing the FinTrac application.
"""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

import src.models.db.models  # noqa: F401
from src.models.db.account import Account, AccountType
from src.models.db.currency import Currency
from src.models.db.permission import Role
from src.models.db.user import User

# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async_session = AsyncSession(bind=db_engine, expire_on_commit=False)

    yield async_session

    await async_session.close()


@pytest.fixture
async def db_session_with_data(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session with pre-populated test data."""
    # Create roles
    user_role = Role(id=uuid4(), name="user", description="Standard user role")
    admin_role = Role(id=uuid4(), name="admin", description="Admin role")

    db_session.add(user_role)
    db_session.add(admin_role)
    await db_session.commit()

    # Create currency
    usd = Currency(
        id=uuid4(),
        code="USD",
        name="US Dollar",
        symbol="$",
        exchange_rate_to_usd=1.0,
    )
    db_session.add(usd)
    await db_session.commit()

    yield db_session


# ============================================================================
# USER AND AUTHENTICATION FIXTURES
# ============================================================================


@pytest.fixture
def test_user_data() -> dict:
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "password": "SecurePassword123!",
        "phone_number": "+1234567890",
    }


@pytest.fixture
def test_user_data_2() -> dict:
    """Provide a second test user data."""
    return {
        "email": "test2@example.com",
        "username": "testuser2",
        "first_name": "Test2",
        "last_name": "User2",
        "password": "SecurePassword456!",
        "phone_number": "+1987654321",
    }


@pytest.fixture
async def test_user(db_session_with_data: AsyncSession, test_user_data: dict) -> User:
    """Create a test user in the database."""
    role = (
        await db_session_with_data.exec(
            __import__("sqlmodel").select(Role).where(Role.name == "user")
        )
    ).first()

    user = User(
        id=uuid4(),
        email=test_user_data["email"],
        username=test_user_data["username"],
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
        hashed_password="hashed_password_here",  # In real tests, use proper hashing
        role_id=role.id,
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )

    db_session_with_data.add(user)
    await db_session_with_data.commit()
    await db_session_with_data.refresh(user)

    return user


@pytest.fixture
async def test_account(db_session_with_data: AsyncSession, test_user: User) -> Account:
    """Create a test account for the test user."""
    currency = (
        await db_session_with_data.exec(__import__("sqlmodel").select(Currency))
    ).first()

    account = Account(
        id=uuid4(),
        user_id=test_user.id,
        currency_id=currency.id,
        name="Test Checking Account",
        account_type=AccountType.BANK.value,
        balance=1000.0,
    )

    db_session_with_data.add(account)
    await db_session_with_data.commit()
    await db_session_with_data.refresh(account)

    return account


# ============================================================================
# REQUEST AND RESPONSE FIXTURES
# ============================================================================


@pytest.fixture
def valid_registration_payload(test_user_data: dict) -> dict:
    """Provide valid user registration payload."""
    return {
        "email": test_user_data["email"],
        "username": test_user_data["username"],
        "first_name": test_user_data["first_name"],
        "last_name": test_user_data["last_name"],
        "password": test_user_data["password"],
        "confirm_password": test_user_data["password"],
        "phone_number": test_user_data["phone_number"],
        "accept_terms": True,
        "prefered_locale": "en",
        "theme": "light",
        "accepted_terms": [],
        "device": {
            "device_id": "test-device-id",
            "device_name": "Test Device",
            "platform": "test",
            "os_version": "1.0",
            "app_version": "1.0.0",
        },
    }


@pytest.fixture
def invalid_email_payload(test_user_data: dict) -> dict:
    """Provide invalid email registration payload."""
    return {
        "email": "not-an-email",
        "username": test_user_data["username"],
        "first_name": test_user_data["first_name"],
        "last_name": test_user_data["last_name"],
        "password": test_user_data["password"],
        "confirm_password": test_user_data["password"],
    }


@pytest.fixture
def mismatched_password_payload(test_user_data: dict) -> dict:
    """Provide payload with mismatched passwords."""
    return {
        "email": test_user_data["email"],
        "username": test_user_data["username"],
        "first_name": test_user_data["first_name"],
        "last_name": test_user_data["last_name"],
        "password": test_user_data["password"],
        "confirm_password": "DifferentPassword123!",
        "prefered_locale": "en",
        "theme": "light",
        "accept_terms": True,
        "accepted_terms": [],
        "device": {
            "device_id": "test-device-id",
            "device_name": "Test Device",
            "platform": "test",
            "os_version": "1.0",
            "app_version": "1.0.0",
        },
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


@pytest.fixture
def async_test_helper():
    """Provide async test helper functions."""

    async def run_async(coro):
        """Run an async function."""
        return await coro

    return run_async
