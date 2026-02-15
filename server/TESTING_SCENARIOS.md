"""
Common test scenarios and examples.
This file serves as a reference for frequently tested scenarios.
"""

# ==============================================================================

# USER REGISTRATION SCENARIOS

# ==============================================================================

"""
Test successful user registration:
pytest tests/test_services.py::TestAuthService::test_register_user_success -v

Test duplicate email detection:
pytest tests/test_services.py::TestAuthService::test_register_user_email_already_exists -v

Test duplicate username detection:
pytest tests/test_services.py::TestAuthService::test_register_user_username_already_exists -v

Test weak password rejection:
pytest tests/test_services.py::TestAuthService::test_register_user_weak_password -v

Test terms acceptance validation:
pytest tests/test_services.py::TestAuthService::test_register_user_terms_not_accepted -v

Test all registration scenarios:
pytest tests/test_services.py::TestAuthService -v
"""

# ==============================================================================

# ACCOUNT MANAGEMENT SCENARIOS

# ==============================================================================

"""
Test account creation:
pytest tests/test_services.py::TestAccountService::test_create_account_success -v

Test retrieving account:
pytest tests/test_services.py::TestAccountService::test_get_account_by_id_success -v

Test unauthorized access prevention:
pytest tests/test_services.py::TestAccountService::test_get_account_unauthorized -v

Test account update:
pytest tests/test_services.py::TestAccountService::test_update_account_success -v

Test account deletion:
pytest tests/test_services.py::TestAccountService::test_delete_account_success -v

Test paginated account list:
pytest tests/test_repositories.py::TestAccountRepository::test_get_accounts_by_user_id_pagination -v

Test all account scenarios:
pytest tests/test_services.py::TestAccountService -v
"""

# ==============================================================================

# AUTHORIZATION & SECURITY SCENARIOS

# ==============================================================================

"""
Test user cannot access other user's account:
pytest tests/test_services.py::TestAccountService::test_get_account_unauthorized -v

Test deleted users cannot login:
pytest tests/test_security_and_edge_cases.py::TestSecurityAndValidation::test_deleted_users_cannot_login -v

Test SQL injection protection:
pytest tests/test_security_and_edge_cases.py::TestSecurityAndValidation::test_sql_injection_protection -v

Test password not exposed in responses:
pytest tests/test_security_and_edge_cases.py::TestSecurityAndValidation::test_password_not_returned_in_responses -v

Test unverified user restrictions:
pytest tests/test_security_and_edge_cases.py::TestSecurityAndValidation::test_unverified_user_restrictions -v

Test all security scenarios:
pytest tests/test_security_and_edge_cases.py::TestSecurityAndValidation -v
"""

# ==============================================================================

# DATA INTEGRITY SCENARIOS

# ==============================================================================

"""
Test concurrent balance updates maintain consistency:
pytest tests/test_security_and_edge_cases.py::TestConcurrency::test_concurrent_balance_updates -v

Test concurrent user creation handles duplicates:
pytest tests/test_security_and_edge_cases.py::TestConcurrency::test_concurrent_user_creation -v

Test foreign key relationships:
pytest tests/test_security_and_edge_cases.py::TestDataIntegrity::test_foreign_key_integrity -v

Test soft deletes work correctly:
pytest tests/test_repositories.py::TestAccountRepository::test_delete_for_user_success -v

Test all data integrity scenarios:
pytest tests/test_security_and_edge_cases.py::TestDataIntegrity -v
"""

# ==============================================================================

# API ENDPOINT SCENARIOS

# ==============================================================================

"""
Test user registration endpoint:
pytest tests/test_api_integration.py::TestAuthEndpoints::test_register_success -v

Test login endpoint:
pytest tests/test_api_integration.py::TestAuthEndpoints::test_login_success -v

Test account creation endpoint:
pytest tests/test_api_integration.py::TestAccountEndpoints::test_create_account_success -v

Test account retrieval endpoint:
pytest tests/test_api_integration.py::TestAccountEndpoints::test_get_account_success -v

Test health check endpoint:
pytest tests/test_api_integration.py::TestHealthEndpoint::test_health_check -v

Test error handling:
pytest tests/test_api_integration.py::TestErrorHandling -v

Test all API scenarios:
pytest tests/test_api_integration.py -v
"""

# ==============================================================================

# INPUT VALIDATION SCENARIOS

# ==============================================================================

"""
Test email validation:
pytest tests/test_security_and_edge_cases.py::TestInputValidation::test_email_validation_strict -v

Test username validation:
pytest tests/test_security_and_edge_cases.py::TestInputValidation::test_username_validation -v

Test password validation requirements:
pytest tests/test_security_and_edge_cases.py::TestInputValidation::test_password_validation_requirements -v

Test XSS protection:
pytest tests/test_security_and_edge_cases.py::TestInputValidation::test_xss_protection_in_strings -v

Test all input validation:
pytest tests/test_security_and_edge_cases.py::TestInputValidation -v
"""

# ==============================================================================

# COMMON TEST COMMANDS

# ==============================================================================

"""
RUN ALL TESTS:
pytest

RUN WITH VERBOSE OUTPUT:
pytest -v

RUN WITH PRINT STATEMENTS:
pytest -v -s

RUN WITH LOCAL VARIABLES IN TRACEBACK:
pytest -l

RUN IN PARALLEL (4 workers):
pytest -n 4

RUN IN PARALLEL (auto-detect workers):
pytest -n auto

RUN WITH COVERAGE:
pytest --cov=src --cov-report=html --cov-report=term-missing

GENERATE COVERAGE HTML REPORT:
pytest --cov=src --cov-report=html
open htmlcov/index.html

RUN SPECIFIC TEST FILE:
pytest tests/test_repositories.py -v

RUN SPECIFIC TEST CLASS:
pytest tests/test_repositories.py::TestUserRepository -v

RUN SPECIFIC TEST:
pytest tests/test_repositories.py::TestUserRepository::test_get_by_email_found -v

RUN BY KEYWORD:
pytest -k "test_register" -v

RUN BY MARKER:
pytest -m security -v
pytest -m "not slow" -v
pytest -m "integration and not slow" -v

SHOW SLOWEST 10 TESTS:
pytest --durations=10

SHOW ALL TEST MARKERS:
pytest --markers

SHOW TEST COLLECTION WITHOUT RUNNING:
pytest --collect-only

DEBUG MODE (with pdb):
pytest -v -s --tb=short

CLEAN TEST CACHE:
rm -rf .pytest_cache
rm -rf .coverage
rm -rf htmlcov
"""

# ==============================================================================

# PYTEST MARKERS

# ==============================================================================

"""
AVAILABLE MARKERS:
@pytest.mark.asyncio - Async tests
@pytest.mark.slow - Slow tests (exclude with -m "not slow")
@pytest.mark.integration - Integration tests
@pytest.mark.unit - Unit tests
@pytest.mark.security - Security tests
@pytest.mark.performance - Performance tests
@pytest.mark.database - Database tests
@pytest.mark.api - API tests

USAGE EXAMPLES:
Run only security tests:
pytest -m security

    Run unit tests only:
        pytest -m unit

    Run integration tests:
        pytest -m integration

    Skip slow tests:
        pytest -m "not slow"

    Run security AND integration tests:
        pytest -m "security and integration"

    Run NOT slow tests:
        pytest -m "not slow"

"""

# ==============================================================================

# FIXTURE USAGE EXAMPLES

# ==============================================================================

"""
AVAILABLE FIXTURES:

Database Fixtures: - db_session: Fresh database session for each test - db_session_with_data: Database with pre-populated data - db_engine: SQLAlchemy engine for tests

User & Account Fixtures: - test_user: Pre-created test user - test_user_data: User data dictionary - test_user_data_2: Second test user data - test_account: Pre-created test account

Data Fixtures: - valid_registration_payload: Valid registration data - invalid_email_payload: Invalid email for testing - mismatched_password_payload: Mismatched passwords

Helper Fixtures: - async_helper: AsyncTestHelper utilities - mock_data_generator: MockDataGenerator instance - assertion_helpers: AssertionHelpers instance - test_data_manager: TestDataManager instance - performance_assertions: PerformanceAssertions instance

USAGE IN TESTS:
@pytest.mark.asyncio
async def test_something(db_session, test_user, assertion_helpers):
result = await some_function(db_session, test_user.id)
assertion_helpers.assert_response_success(result)
"""

# ==============================================================================

# TROUBLESHOOTING COMMON ISSUES

# ==============================================================================

"""
ISSUE: "No module named 'src'"
SOLUTION:
cd /path/to/server
export PYTHONPATH=$PWD:$PYTHONPATH
pytest

ISSUE: Tests timeout
SOLUTION:
pytest --timeout=60

ISSUE: Database locked error
SOLUTION:
Already using in-memory SQLite (no file locking)
Check if other pytest processes are running:
ps aux | grep pytest

ISSUE: Async test not running
SOLUTION:
Add @pytest.mark.asyncio decorator
Install: pip install pytest-asyncio
Check pytest.ini has: asyncio_mode = auto

ISSUE: Tests fail with "fixture not found"
SOLUTION:
Ensure conftest.py is in tests/ directory
Check spelling of fixture name matches exactly

ISSUE: Coverage report shows 0%
SOLUTION:
pytest --cov=src --cov-report=html
Make sure pytest-cov is installed

ISSUE: Tests pass locally but fail in CI
SOLUTION:
Check for timezone issues: use timezone.utc
Check for environment variables
Check for database connection issues
Run tests in same order as CI
"""

# ==============================================================================

# PERFORMANCE TESTING

# ==============================================================================

"""
RUN TESTS AND SHOW TIMING:
pytest --durations=10

PROFILE A TEST:
pytest -v -s tests/test_file.py::test_name

MEASURE TEST EXECUTION TIME:
pytest --durations=0

PERFORMANCE ASSERTION EXAMPLE:
@pytest.mark.performance
@pytest.mark.asyncio
async def test_query_speed(db_session, performance_assertions):
import time
start = time.time()
users = await repo.get_all(db_session)
elapsed = time.time() - start

        performance_assertions.assert_response_time(
            elapsed,
            max_milliseconds=500
        )

"""

# ==============================================================================

# CONTINUOUS INTEGRATION

# ==============================================================================

"""
FOR GITHUB ACTIONS:
pytest --cov=src --cov-report=xml

FOR GITLAB CI:
pytest --cov=src --cov-report=term --cov-report=html

FOR JENKINS:
pytest --junit-xml=test-results.xml --cov=src

FOR COVERAGE.IO:
pytest --cov=src --cov-report=xml
(use codecov/codecov-action)
"""
