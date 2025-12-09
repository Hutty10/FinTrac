import logging
import pathlib
from typing import Any

from pydantic_settings import BaseSettings

# import decouple
# import pydantic

ROOT_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent.parent.parent.resolve()


class BackendBaseSettings(BaseSettings):  # type: ignore[misc]
    TITLE: str = "FinTrac Server Application"
    VERSION: str = "0.1.0"
    TIMEZONE: str = "UTC"
    DESCRIPTION: str | None = None
    DEBUG: bool = False

    SERVER_HOST: str
    SERVER_PORT: int = 8000
    SERVER_WORKERS: int
    API_PREFIX: str = "/api"
    DOCS_URL: str = "/docs"
    OPENAPI_URL: str = "/openapi.json"
    REDOC_URL: str = "/redoc"
    OPENAPI_PREFIX: str = ""

    DB_POSTGRES_HOST: str
    DB_MAX_POOL_CON: int
    DB_POSTGRES_NAME: str
    DB_POSTGRES_PASSWORD: str
    DB_POOL_SIZE: int
    DB_POOL_OVERFLOW: int
    DB_POSTGRES_PORT: int
    DB_POSTGRES_SCHEMA: str
    DB_TIMEOUT: int
    DB_POSTGRES_USERNAME: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_MAX_CONNECTIONS: int
    REDIS_SOCKET_KEEPALIVE: bool
    REDIS_SOCKET_TIMEOUT: int
    REDIS_SOCKET_CONNECT_TIMEOUT: int
    REDIS_MAX_RETRIES: int
    REDIS_RETRY_ON_TIMEOUT: bool
    REDIS_RETRY_DELAY: int
    REDIS_CACHE_TTL: int

    CELERY_BROKER_URL: str
    CELERY_BACKEND_URL: str

    IS_DB_ECHO_LOG: bool
    IS_DB_FORCE_ROLLBACK: bool
    IS_DB_EXPIRE_ON_COMMIT: bool

    SECRET_KEY: str
    API_TOKEN: str
    AUTH_TOKEN: str
    JWT_TOKEN_PREFIX: str
    JWT_SECRET_KEY: str

    JWT_ACCESS_TOKEN_EXPIRATION_TIME_IN_SECONDS: int
    JWT_REFRESH_TOKEN_EXPIRATION_TIME_IN_SECONDS: int

    IS_ALLOWED_CREDENTIALS: bool
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",  # React default port
        "http://0.0.0.0:3000",
        "http://127.0.0.1:3000",  # React docker port
        "http://127.0.0.1:3001",
        "http://localhost:5173",  # Qwik default port
        "http://0.0.0.0:5173",
        "http://127.0.0.1:5173",  # Qwik docker port
        "http://127.0.0.1:5174",
    ]
    ALLOWED_METHODS: list[str] = ["*"]
    ALLOWED_HEADERS: list[str] = ["*"]

    LOGGING_LEVEL: int = logging.INFO
    LOGGERS: tuple[str, str] = ("uvicorn.asgi", "uvicorn.access")

    HASHING_ALGORITHM_LAYER_1: str
    HASHING_ALGORITHM_LAYER_2: str
    HASHING_SALT: str
    JWT_ALGORITHM: str

    model_config = {
        "validate_assignment": True,
        "env_file": f"{str(ROOT_DIR)}/.env",
        "case_sensitive": True,
        "extra": "ignore",
    }

    @property
    def DATABASE_URI(self) -> str:
        """
        Set the asynchronous database URI for SQLAlchemy Async Engine.
        """
        return "{schema}://{username}:{password}@{host}:{port}/{database}".format(
            schema=self.DB_POSTGRES_SCHEMA,
            username=self.DB_POSTGRES_USERNAME,
            password=self.DB_POSTGRES_PASSWORD,
            host=self.DB_POSTGRES_HOST,
            port=self.DB_POSTGRES_PORT,
            database=self.DB_POSTGRES_NAME,
        )

    @property
    def set_backend_app_attributes(self) -> dict[str, Any]:
        """
        Set all `FastAPI` class' attributes with the custom values defined in `BackendBaseSettings`.
        """
        return {
            "title": self.TITLE,
            "version": self.VERSION,
            "debug": self.DEBUG,
            "description": self.DESCRIPTION,
            "docs_url": self.DOCS_URL,
            "openapi_url": self.OPENAPI_URL,
            "redoc_url": self.REDOC_URL,
            "openapi_prefix": self.OPENAPI_PREFIX,
            "api_prefix": self.API_PREFIX,
        }
