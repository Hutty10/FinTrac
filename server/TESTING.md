# FinTrac Testing Guide

## Overview

This document provides comprehensive documentation for the FinTrac test suite. The test suite is production-ready and includes unit tests, integration tests, security tests, and performance tests.

## Test Structure

```
tests/
├── __init__.py                          # Test package initialization
├── conftest.py                          # Pytest configuration and shared fixtures
├── test_repositories.py                 # Repository layer unit tests
├── test_services.py                     # Service layer unit tests
├── test_api_integration.py              # API endpoint integration tests
├── test_security_and_edge_cases.py     # Security and edge case tests
├── test_utils.py                        # Test utilities and helpers
└── pytest.ini                           # Pytest configuration
```

## Setup

### Installation

1. **Install test dependencies**:

```bash
uv sync --group dev
# or
pip install -r requirements-dev.txt
```

2. **Verify pytest installation**:

```bash
pytest --version
```

### Configuration

Tests are configured via `pytest.ini`:

- Auto-discovery of test files (`test_*.py`)
- Async test support via `pytest-asyncio`
- Coverage reporting via `pytest-cov`
- Parallel execution via `pytest-xdist`

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_repositories.py
```

### Run Specific Test Class

```bash
pytest tests/test_repositories.py::TestUserRepository
```

### Run Specific Test

```bash
pytest tests/test_repositories.py::TestUserRepository::test_get_by_email_found
```

### Run Tests by Marker

```bash
# Run only integration tests
pytest -m integration

# Run unit tests
pytest -m unit

# Run security tests
pytest -m security

# Skip slow tests
pytest -m "not slow"
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Parallel Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run with 4 workers
pytest -n 4
```

### Verbose Output

```bash
# Verbose output with print statements
pytest -v -s

# Show local variables in tracebacks
pytest -l

# Show slowest 10 tests
pytest --durations=10
```

## Test Categories

### 1. Repository Tests (`test_repositories.py`)

Tests for data access layer operations.

**Coverage**:

- User repository CRUD operations
- Account repository operations
- Transaction repository queries
- Pagination and filtering
- Soft deletes

**Example**:

```bash
pytest tests/test_repositories.py -v
```

### 2. Service Tests (`test_services.py`)

Tests for business logic layer.

**Coverage**:

- User registration and validation
- Authentication logic
- Account management
- Authorization checks
- Input validation

**Example**:

```bash
pytest tests/test_services.py::TestAuthService -v
```

### 3. API Integration Tests (`test_api_integration.py`)

Tests for HTTP endpoints and request/response handling.

**Coverage**:

- Authentication endpoints
- Account endpoints
- Error handling
- Validation errors
- Authorization

**Example**:

```bash
pytest tests/test_api_integration.py::TestAuthEndpoints -v
```

### 4. Security & Edge Cases (`test_security_and_edge_cases.py`)

Tests for security vulnerabilities and edge cases.

**Coverage**:

- SQL injection protection
- Data privacy
- Concurrency issues
- Input validation
- XSS protection

**Example**:

```bash
pytest tests/test_security_and_edge_cases.py -m security -v
```

## Fixtures

### Database Fixtures

```python
@pytest.mark.asyncio
async def test_something(db_session: AsyncSession):
    """Test with clean database session"""
    pass

@pytest.mark.asyncio
async def test_with_data(db_session_with_data: AsyncSession):
    """Test with pre-populated database"""
    pass
```

### User Fixtures

```python
@pytest.mark.asyncio
async def test_user_operations(test_user: User):
    """Test with pre-created user"""
    assert test_user.email == "test@example.com"

@pytest.mark.asyncio
async def test_account_operations(test_account: Account):
    """Test with pre-created account"""
    assert test_account.balance == 1000.0
```

### Data Fixtures

```python
def test_with_user_data(test_user_data: dict):
    """Test with user data dictionary"""
    assert test_user_data["email"] == "test@example.com"

def test_with_registration_payload(valid_registration_payload: dict):
    """Test with valid registration payload"""
    pass
```

### Helper Fixtures

```python
@pytest.mark.asyncio
async def test_with_helpers(async_helper, mock_data_generator, assertion_helpers):
    """Test with utility helpers"""
    user_data = mock_data_generator.generate_user_data()
    transaction = await async_helper.create_test_transaction(...)
    assertion_helpers.assert_response_success(response)
```

## Common Test Patterns

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_operation(db_session: AsyncSession):
    result = await some_async_function(db_session)
    assert result is not None
```

### Testing Exceptions

```python
@pytest.mark.asyncio
async def test_exception_handling(db_session: AsyncSession):
    with pytest.raises(BaseAppException) as exc_info:
        await function_that_raises(db_session)

    assert exc_info.value.status_code == 400
    assert "expected message" in str(exc_info.value)
```

### Testing Pagination

```python
@pytest.mark.asyncio
async def test_pagination(db_session: AsyncSession, repo):
    items, meta = await repo.get_paginated(db_session, page=1, page_size=10)

    assert meta["page"] == 1
    assert meta["page_size"] == 10
    assert meta["total_items"] >= 0
    assert meta["total_pages"] >= 0
```

### Testing Authorization

```python
@pytest.mark.asyncio
async def test_authorization(db_session: AsyncSession, service, test_user, other_user):
    # User should access own data
    result = await service.get_item(db_session, item_id, test_user.id)
    assert result is not None

    # User should NOT access other's data
    with pytest.raises(BaseAppException) as exc_info:
        await service.get_item(db_session, item_id, other_user.id)

    assert exc_info.value.status_code == 403
```

### Testing Soft Deletes

```python
@pytest.mark.asyncio
async def test_soft_delete(db_session: AsyncSession, repo, item):
    # Delete item
    result = await repo.delete(db_session, item.id)
    assert result is True

    # Item should be marked as deleted
    await db_session.refresh(item)
    assert item.is_deleted is True

    # Item should not appear in normal queries
    items = await repo.get_all(db_session)
    assert item not in items
```

## Test Utilities

### Mock Data Generator

```python
def test_with_generated_data(mock_data_generator):
    user_data = mock_data_generator.generate_user_data(
        email="custom@example.com"
    )
    account_data = mock_data_generator.generate_account_data(balance=5000.0)
    transaction_data = mock_data_generator.generate_transaction_data(amount=250.0)
```

### Assertion Helpers

```python
def test_with_helpers(assertion_helpers):
    response = {"status": "success", "code": 200}
    assertion_helpers.assert_response_success(response)

    paginated = {"data": {"page": 1, "page_size": 10, "items": [], "total_items": 0}}
    assertion_helpers.assert_paginated_response(paginated)
```

### Async Test Helper

```python
@pytest.mark.asyncio
async def test_with_async_helper(db_session: AsyncSession, async_helper, test_account, currency):
    transaction = await async_helper.create_test_transaction(
        db_session, test_account, currency
    )

    transactions = await async_helper.create_multiple_transactions(
        db_session, test_account, currency, count=5
    )

    is_valid = await async_helper.verify_account_balance(
        db_session, test_account, 1000.0
    )
```

## Best Practices

### 1. Test Isolation

- Each test should be independent
- Use fixtures to set up clean state
- Clean up created data in teardown

```python
@pytest.fixture
async def isolated_user(db_session: AsyncSession):
    user = User(...)
    db_session.add(user)
    await db_session.commit()
    yield user
    # Cleanup
    await db_session.delete(user)
    await db_session.commit()
```

### 2. Clear Test Names

- Use descriptive names that explain what is being tested
- Follow `test_<what>_<condition>_<expected_result>` pattern

```python
# Good
async def test_get_account_with_valid_id_returns_account(...)

# Bad
async def test_account(...)
```

### 3. Arrange-Act-Assert Pattern

```python
@pytest.mark.asyncio
async def test_user_email_update(db_session: AsyncSession, test_user):
    # Arrange
    new_email = "newemail@example.com"

    # Act
    test_user.email = new_email
    db_session.add(test_user)
    await db_session.commit()

    # Assert
    await db_session.refresh(test_user)
    assert test_user.email == new_email
```

### 4. Test Both Happy and Sad Paths

```python
@pytest.mark.asyncio
async def test_get_user_happy_path(repo, test_user):
    user = await repo.get_by_id(user.id)
    assert user is not None

@pytest.mark.asyncio
async def test_get_user_sad_path(repo):
    user = await repo.get_by_id(uuid4())
    assert user is None
```

### 5. Use Test Markers

```python
@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.integration
async def test_complex_workflow(...):
    pass

# Run with: pytest -m "integration and slow"
```

## Debugging Tests

### Print Debug Info

```bash
pytest -v -s tests/test_file.py::test_name
```

### Drop into Debugger

```python
import pdb; pdb.set_trace()  # For sync code
import ipdb; ipdb.set_trace()  # For async code
```

### Show Local Variables

```bash
pytest -l tests/test_file.py
```

### Verbose Output with Full Traceback

```bash
pytest -vv --tb=long tests/test_file.py
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src
      - run: coverage report
```

## Performance Testing

### Run with Timing

```bash
pytest --durations=10 tests/
```

### Profile Slow Tests

```bash
pytest --durations=0 tests/
```

### Performance Assertions

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_query_performance(db_session: AsyncSession, performance_assertions):
    import time

    start = time.time()
    users = await repo.get_all_users(db_session)
    elapsed = time.time() - start

    performance_assertions.assert_response_time(elapsed, max_milliseconds=500)
```

## Coverage Goals

- **Overall Coverage**: Aim for 80%+ coverage
- **Critical Paths**: 100% coverage for auth, payments, data operations
- **Excluded**: Migrations, config files, third-party integrations

### View Coverage Report

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Troubleshooting

### Tests Fail with "No module named 'src'"

**Solution**: Ensure you're running from project root and `src` is in PYTHONPATH:

```bash
cd /path/to/server
export PYTHONPATH=$PWD:$PYTHONPATH
pytest
```

### Async Tests Timeout

**Solution**: Increase timeout in `pytest.ini`:

```ini
asyncio_mode = auto
[tool:pytest]
asyncio_default_fixture_scope = function
timeout = 30
```

### Database Locked Error

**Solution**: Use in-memory SQLite for tests (already configured in `conftest.py`)

### Session Scope Issues

**Solution**: Ensure fixtures use appropriate scope:

- `function` - Fresh for each test (default)
- `session` - Shared across all tests (use sparingly)

## Contributing Tests

When adding new features:

1. Write tests first (TDD)
2. Cover happy path and error cases
3. Add appropriate markers
4. Update this documentation
5. Ensure coverage doesn't decrease
6. Run full test suite before submitting PR

```bash
# Before submitting
pytest --cov=src --cov-report=term-missing
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/testing/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
