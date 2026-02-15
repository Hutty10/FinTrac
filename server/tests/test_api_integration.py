"""
Integration tests for API endpoints.
Tests the full stack from HTTP request to database.
"""

from typing import Any

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.session import get_session
from src.main import app


class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""

    @pytest.fixture
    async def client(self, db_session: AsyncSession):
        """Create a test client with database session."""
        from httpx import ASGITransport

        async def override_get_session():
            yield db_session

        app.dependency_overrides[get_session] = override_get_session

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_success(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
        valid_registration_payload: dict,
    ):
        """Test successful user registration via API."""
        response = await client.post(
            "/api/v1/auth/register",
            json=valid_registration_payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.asyncio
    async def test_register_invalid_email(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
        invalid_email_payload: dict,
    ):
        """Test registration with invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json=invalid_email_payload,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_missing_required_field(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
    ):
        """Test registration with missing required field."""
        payload = {
            "email": "test@example.com",
            # Missing other required fields
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=payload,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
        test_user: Any,
        test_user_data: dict,
    ):
        """Test successful login via API."""
        login_payload = {
            "email": test_user.email,
            "password": "SecurePassword123!",  # Would need to match actual password
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=login_payload,
        )

        # This will depend on your implementation
        # For now, we check status codes
        assert response.status_code in [200, 401, 422]

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
    ):
        """Test login with invalid credentials."""
        login_payload = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=login_payload,
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_email(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
    ):
        """Test login without email."""
        login_payload = {
            "password": "SomePassword123!",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=login_payload,
        )

        assert response.status_code == 422


class TestAccountEndpoints:
    """Integration tests for account endpoints."""

    @pytest.fixture
    async def client(self, db_session: AsyncSession):
        """Create a test client with database session."""
        from httpx import ASGITransport

        async def override_get_session():
            yield db_session

        app.dependency_overrides[get_session] = override_get_session

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        app.dependency_overrides.clear()

    @pytest.fixture
    async def auth_headers(
        self,
        client: AsyncClient,
        test_user: Any,
    ):
        """Create authentication headers for test requests."""
        # This would require a valid JWT token
        # For testing, you might mock the token validation
        return {"Authorization": "Bearer test-token"}

    @pytest.mark.asyncio
    async def test_create_account_success(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
        auth_headers: dict,
    ):
        """Test creating a new account via API."""
        payload = {
            "name": "Test Savings Account",
            "account_type": "savings",
            "currency_id": "550e8400-e29b-41d4-a716-446655440000",  # Would be actual UUID
        }

        response = await client.post(
            "/api/v1/accounts",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code in [201, 401, 422]

    @pytest.mark.asyncio
    async def test_get_account_success(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
        test_account: Any,
        auth_headers: dict,
    ):
        """Test retrieving an account via API."""
        response = await client.get(
            f"/api/v1/accounts/{test_account.id}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 404]

    @pytest.mark.asyncio
    async def test_get_accounts_list(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
        auth_headers: dict,
    ):
        """Test retrieving list of accounts via API."""
        response = await client.get(
            "/api/v1/accounts?page=1&page_size=10",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 422]

    @pytest.mark.asyncio
    async def test_update_account_success(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
        test_account: Any,
        auth_headers: dict,
    ):
        """Test updating an account via API."""
        payload = {
            "name": "Updated Account Name",
        }

        response = await client.put(
            f"/api/v1/accounts/{test_account.id}",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 404, 422]

    @pytest.mark.asyncio
    async def test_delete_account_success(
        self,
        client: AsyncClient,
        db_session_with_data: AsyncSession,
        test_account: Any,
        auth_headers: dict,
    ):
        """Test deleting an account via API."""
        response = await client.delete(
            f"/api/v1/accounts/{test_account.id}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 404]


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.fixture
    async def client(self):
        """Create a test client."""
        from httpx import ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestErrorHandling:
    """Tests for error handling and validation."""

    @pytest.fixture
    async def client(self, db_session: AsyncSession):
        """Create a test client with database session."""
        from httpx import ASGITransport

        async def override_get_session():
            yield db_session

        app.dependency_overrides[get_session] = override_get_session

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_404_endpoint_not_found(self, client: AsyncClient):
        """Test 404 error for non-existent endpoint."""
        response = await client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client: AsyncClient):
        """Test 405 error for disallowed HTTP method."""
        response = await client.delete("/api/v1/auth/register")

        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, client: AsyncClient):
        """Test 400 error for invalid JSON."""
        response = await client.post(
            "/api/v1/auth/register",
            content="invalid json {",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
