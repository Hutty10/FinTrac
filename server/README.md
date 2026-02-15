# FinTrac Server 💰

A comprehensive, production-ready financial tracking and management API built with FastAPI, SQLModel, and PostgreSQL. FinTrac provides a robust backend for personal finance management, featuring account management, transaction tracking, budgeting, and goal setting.

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.122.0+-green.svg)](https://fastapi.tiangolo.com)
[![SQLModel](https://img.shields.io/badge/SQLModel-0.0.27+-orange.svg)](https://sqlmodel.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Database Migrations](#-database-migrations)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Security](#-security)
- [Background Tasks](#-background-tasks)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Functionality

- 🔐 **Authentication & Authorization**
  - JWT-based authentication with access and refresh tokens
  - Role-based access control (RBAC)
  - Multi-device session management
  - Email verification and password reset
  - Secure password hashing with Argon2

- 💳 **Account Management**
  - Multiple account types (Cash, Bank, Card)
  - Multi-currency support with exchange rates
  - Account balance tracking and history
  - Soft delete with data retention

- 💸 **Transaction Management**
  - Income, expense, and transfer tracking
  - Transaction categorization
  - Recurring transactions
  - Transaction filtering and search
  - Bulk transaction operations

- 📊 **Budgeting**
  - Category-based budgets
  - Budget period management (monthly, quarterly, yearly)
  - Budget vs actual spending tracking
  - Budget alerts and notifications

- 🎯 **Goal Setting**
  - Savings goals with target amounts
  - Goal progress tracking
  - Deadline management
  - Goal achievement notifications

### Advanced Features

- 📈 **Analytics & Reporting**
  - Spending patterns analysis
  - Income vs expense reports
  - Category-wise breakdowns
  - Custom date range reports

- 🔔 **Notifications**
  - Email notifications for important events
  - Transaction alerts
  - Budget limit warnings
  - Goal milestone notifications

- 🔒 **Security Features**
  - Rate limiting to prevent abuse
  - Audit logging for all operations
  - Security event tracking
  - IP-based access control
  - Device fingerprinting

- 📱 **User Preferences**
  - Customizable themes (light/dark)
  - Multi-language support
  - Default currency settings
  - Notification preferences

---

## 🏗️ Architecture

FinTrac follows a clean, layered architecture:

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │
│   ┌─────────────────────────────────┐   │
│   │   Routers (Auth, Accounts, etc) │   │
│   └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Service Layer                    │
│   ┌─────────────────────────────────┐   │
│   │   Business Logic & Validation   │   │
│   └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Repository Layer                   │
│   ┌─────────────────────────────────┐   │
│   │   Data Access & ORM Operations  │   │
│   └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Database Layer                   │
│   ┌─────────────────────────────────┐   │
│   │    PostgreSQL + SQLModel        │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Design Patterns

- **Repository Pattern**: Abstracts data access logic
- **Service Layer Pattern**: Encapsulates business logic
- **Dependency Injection**: Decouples components
- **Factory Pattern**: For creating complex objects
- **Singleton Pattern**: For configuration management

---

## 🛠️ Tech Stack

### Core Framework

- **FastAPI** 0.122.0+ - Modern, fast web framework
- **SQLModel** 0.0.27+ - SQL databases in Python with type hints
- **Pydantic** 2.12+ - Data validation using Python type hints

### Database

- **PostgreSQL** - Primary database
- **asyncpg** 0.31.0+ - Async PostgreSQL driver
- **Alembic** 1.17.2+ - Database migrations

### Caching & Task Queue

- **Redis** - Caching and session storage
- **Celery** 5.6.0+ - Distributed task queue

### Security

- **pwdlib[argon2]** 0.3.0+ - Password hashing
- **PyJWT** 2.10.1+ - JSON Web Token implementation

### Email

- **fastapi-mail** 1.6.0+ - Email sending

### Development Tools

- **pytest** 7.4.0+ - Testing framework
- **pytest-asyncio** 0.23.0+ - Async test support
- **pytest-cov** 4.1.0+ - Coverage reporting
- **pytest-xdist** 3.5.0+ - Parallel test execution
- **ruff** 0.14.8+ - Fast Python linter
- **httpx** - Async HTTP client for testing

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.14 or higher
- **PostgreSQL** 12 or higher
- **Redis** 6.0 or higher
- **Git** (for version control)

### Optional but Recommended

- **Docker** & **Docker Compose** (for containerized deployment)
- **Make** (for running Makefile commands)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Hutty10/FinTrac.git
cd FinTrac/server
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

### 4. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the server directory:

```bash
cp .env.example .env
```

Configure the following environment variables:

```env
# Environment
ENVIRONMENT=development  # development, staging, production

# Server Configuration
SERVER_HOST=localhost
SERVER_PORT=8000
SERVER_WORKERS=4

# Database Configuration
DB_POSTGRES_HOST=localhost
DB_POSTGRES_PORT=5432
DB_POSTGRES_NAME=fintrac
DB_POSTGRES_USERNAME=postgres
DB_POSTGRES_PASSWORD=your_password
DB_POSTGRES_SCHEMA=public
DB_MAX_POOL_CON=10
DB_POOL_SIZE=5
DB_POOL_OVERFLOW=10
DB_TIMEOUT=30

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_KEEPALIVE=true
REDIS_SOCKET_TIMEOUT=30
REDIS_SOCKET_CONNECT_TIMEOUT=30
REDIS_MAX_RETRIES=3
REDIS_RETRY_ON_TIMEOUT=true
REDIS_RETRY_DELAY=1
REDIS_CACHE_TTL=3600

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_FROM=noreply@fintrac.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=FinTrac
MAIL_TLS=true
MAIL_SSL=false

# Application URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Database Setup

Create the PostgreSQL database:

```bash
createdb fintrac
```

Or using psql:

```sql
CREATE DATABASE fintrac;
```

---

## 🏃 Running the Application

### Development Mode

```bash
# Using uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using fastapi CLI
fastapi dev

# Or using the Python module
python -m uvicorn src.main:app --reload
```

### Production Mode

```bash
# Using uvicorn with workers
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or using gunicorn with uvicorn workers
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker

```bash
# Build the image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Starting Background Workers

```bash
# Start Celery worker
celery -A src.config.celery worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A src.config.celery beat --loglevel=info
```

The application will be available at:

- API: http://localhost:8000
- API Documentation (Swagger UI): http://localhost:8000/docs
- API Documentation (ReDoc): http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

---

## 📚 API Documentation

Once the application is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Authentication

Most endpoints require authentication. To authenticate:

1. Register a new user via `/api/v1/auth/register`
2. Login via `/api/v1/auth/login` to get access token
3. Include the token in the Authorization header:
   ```
   Authorization: Bearer <your_access_token>
   ```

---

## 🗄️ Database Migrations

FinTrac uses Alembic for database migrations.

### Create a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade by one version
alembic upgrade +1

# Downgrade by one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Migration Best Practices

- Always review auto-generated migrations
- Test migrations on a development database first
- Create separate migrations for data and schema changes
- Include both upgrade and downgrade operations

---

## 🧪 Testing

FinTrac includes a comprehensive test suite with 55+ tests covering repositories, services, API endpoints, and security.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_repositories.py

# Run specific test class
pytest tests/test_repositories.py::TestUserRepository

# Run specific test
pytest tests/test_repositories.py::TestUserRepository::test_create_user

# Run tests in parallel (faster)
pytest -n auto

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x

# Run tests matching pattern
pytest -k "test_auth"
```

### Test Coverage

View HTML coverage report:

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Structure

```
tests/
├── conftest.py                          # Shared fixtures
├── test_repositories.py                 # Repository layer tests
├── test_services.py                     # Service layer tests
├── test_api_integration.py              # API endpoint tests
├── test_security_and_edge_cases.py      # Security tests
└── test_utils.py                        # Utility tests
```

### Writing Tests

Example test:

```python
import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

@pytest.mark.asyncio
async def test_create_account(
    db_session: AsyncSession,
    test_user: User,
):
    """Test account creation."""
    account_data = {
        "name": "Test Account",
        "account_type": "Bank",
        "currency_code": "USD",
        "balance": 1000.0
    }

    account = await account_service.create_account(
        db_session, test_user.id, account_data
    )

    assert account.name == "Test Account"
    assert account.balance == 1000.0
```

For more testing information, see [TESTING.md](TESTING.md) and [TEST_README.md](TEST_README.md).

---

## 📁 Project Structure

```
server/
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   └── env.py                    # Alembic configuration
├── src/                          # Source code
│   ├── api/                      # API layer
│   │   ├── dependencies/         # FastAPI dependencies
│   │   ├── routers_v1/           # API v1 endpoints
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── account.py       # Account management
│   │   │   ├── transaction.py   # Transaction endpoints
│   │   │   ├── budget.py        # Budget endpoints
│   │   │   ├── goal.py          # Goal endpoints
│   │   │   └── user.py          # User management
│   │   └── health.py            # Health check endpoint
│   ├── config/                   # Configuration
│   │   ├── settings/            # Environment settings
│   │   ├── celery.py            # Celery configuration
│   │   ├── lifespan.py          # App lifespan events
│   │   └── manager.py           # Settings manager
│   ├── core/                     # Core utilities
│   │   ├── middleware/          # Custom middleware
│   │   ├── securities/          # Security utilities
│   │   ├── tasks/               # Background tasks
│   │   ├── utils/               # Helper utilities
│   │   ├── cache_manager.py     # Redis cache manager
│   │   └── rate_limiter.py      # Rate limiting
│   ├── models/                   # Data models
│   │   ├── db/                  # Database models
│   │   │   ├── user.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── budget.py
│   │   │   ├── goal.py
│   │   │   ├── currency.py
│   │   │   ├── category.py
│   │   │   └── ...
│   │   └── schemas/             # Pydantic schemas
│   │       ├── auth.py
│   │       ├── account.py
│   │       ├── transaction.py
│   │       └── ...
│   ├── repository/               # Data access layer
│   │   ├── base.py              # Base repository
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── transaction.py
│   │   └── ...
│   ├── service/                  # Business logic layer
│   │   ├── base.py              # Base service
│   │   ├── auth.py
│   │   ├── account.py
│   │   ├── transaction.py
│   │   └── ...
│   └── main.py                   # Application entry point
├── tests/                        # Test suite
│   ├── conftest.py              # Test fixtures
│   ├── test_repositories.py
│   ├── test_services.py
│   ├── test_api_integration.py
│   └── ...
├── docker/                       # Docker configurations
│   └── app.Dockerfile
├── scripts/                      # Utility scripts
├── alembic.ini                   # Alembic config
├── docker-compose.yaml           # Docker compose config
├── pyproject.toml                # Project dependencies
├── pytest.ini                    # Pytest configuration
└── README.md                     # This file
```

---

## 🔌 API Endpoints

### Authentication (`/api/v1/auth`)

- `POST /register` - Register new user
- `POST /login` - User login
- `POST /logout` - User logout
- `POST /refresh` - Refresh access token
- `POST /verify-email` - Verify email address
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password

### Users (`/api/v1/users`)

- `GET /me` - Get current user profile
- `PUT /me` - Update user profile
- `POST /me/change-password` - Change password
- `GET /me/preferences` - Get user preferences
- `PUT /me/preferences` - Update preferences

### Accounts (`/api/v1/accounts`)

- `GET /` - List all accounts
- `POST /` - Create new account
- `GET /{account_id}` - Get account details
- `PUT /{account_id}` - Update account
- `DELETE /{account_id}` - Delete account
- `GET /{account_id}/transactions` - Get account transactions

### Transactions (`/api/v1/transactions`)

- `GET /` - List all transactions
- `POST /` - Create new transaction
- `GET /{transaction_id}` - Get transaction details
- `PUT /{transaction_id}` - Update transaction
- `DELETE /{transaction_id}` - Delete transaction
- `GET /recurring` - List recurring transactions
- `POST /recurring` - Create recurring transaction

### Budgets (`/api/v1/budgets`)

- `GET /` - List all budgets
- `POST /` - Create new budget
- `GET /{budget_id}` - Get budget details
- `PUT /{budget_id}` - Update budget
- `DELETE /{budget_id}` - Delete budget
- `GET /{budget_id}/progress` - Get budget progress

### Goals (`/api/v1/goals`)

- `GET /` - List all goals
- `POST /` - Create new goal
- `GET /{goal_id}` - Get goal details
- `PUT /{goal_id}` - Update goal
- `DELETE /{goal_id}` - Delete goal
- `POST /{goal_id}/contribute` - Add contribution to goal

### Health (`/health`)

- `GET /` - Basic health check
- `GET /ready` - Readiness check
- `GET /live` - Liveness check

---

## 🔒 Security

### Authentication & Authorization

- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: Argon2 algorithm for password security
- **Role-Based Access Control**: Fine-grained permissions
- **Session Management**: Multi-device session tracking

### API Security

- **Rate Limiting**: Prevents API abuse
- **CORS**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic schemas for request validation
- **SQL Injection Prevention**: Parameterized queries via SQLModel

### Data Security

- **Encryption**: Sensitive data encryption at rest
- **Audit Logging**: Track all important operations
- **Soft Deletes**: Data retention for compliance
- **Security Events**: Monitor suspicious activities

### Best Practices

- Use environment variables for secrets
- Enable HTTPS in production
- Regular security audits
- Keep dependencies updated
- Implement proper error handling (no sensitive data in errors)

---

## 📋 Background Tasks

FinTrac uses Celery for asynchronous task processing:

### Email Tasks

- Welcome emails for new users
- Password reset emails
- Transaction notifications
- Budget alert emails

### Scheduled Tasks (Cron)

- Daily budget checks
- Monthly report generation
- Currency exchange rate updates
- Cleanup of old sessions

### Task Monitoring

```bash
# Monitor Celery worker
celery -A src.config.celery inspect active

# Check registered tasks
celery -A src.config.celery inspect registered

# Monitor task queue
celery -A src.config.celery inspect stats
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Write tests** for new functionality
5. **Run tests**: `pytest`
6. **Run linter**: `ruff check src/`
7. **Commit changes**: `git commit -m 'Add amazing feature'`
8. **Push to branch**: `git push origin feature/amazing-feature`
9. **Open a Pull Request**

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and small
- Write meaningful commit messages

### Testing Requirements

- Maintain test coverage above 80%
- Write unit tests for new features
- Update integration tests as needed
- Ensure all tests pass before submitting PR

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Hutty10** - _Initial work_ - [GitHub](https://github.com/Hutty10)

---

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- SQLModel for bridging SQL and Pydantic
- The Python community for excellent libraries
- All contributors to this project

---

## 📞 Support

For support, please:

- Open an issue on GitHub
- Check the [documentation](TESTING.md)
- Contact the maintainers

---

## 🗺️ Roadmap

### Version 1.0

- ✅ Core authentication system
- ✅ Account management
- ✅ Transaction tracking
- ✅ Budget management
- ✅ Goal setting

### Version 1.1 (Planned)

- [ ] Mobile app support
- [ ] Bank integration APIs
- [ ] Advanced analytics dashboard
- [ ] Expense categorization AI
- [ ] Multi-user households
- [ ] Bill reminders

### Version 2.0 (Future)

- [ ] Investment tracking
- [ ] Tax reporting
- [ ] Financial advisor chatbot
- [ ] Cryptocurrency support
- [ ] Invoice generation

---

## 📊 Performance

- API Response Time: < 100ms (average)
- Database Query Time: < 50ms (average)
- Concurrent Users: 1000+ (tested)
- Uptime: 99.9% target

---

## 🌍 Internationalization

FinTrac supports multiple languages and locales:

- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Portuguese (pt)

Currency support includes 150+ currencies with real-time exchange rates.

---

**Made with ❤️ by the FinTrac Team**
