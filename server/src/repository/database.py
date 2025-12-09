from sqlalchemy.ext.asyncio import (
    AsyncEngine as SQLAlchemyAsyncEngine,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession as SQLAlchemyAsyncSession,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine as create_sqlmodel_async_engine,
)
from sqlalchemy.pool import Pool as SQLAlchemyPool
from sqlalchemy.pool import QueuePool as SQLAlchemyQueuePool

from src.config.manager import settings


class AsyncDatabase:
    def __init__(self):
        self.postgres_uri: str = settings.DATABASE_URI
        self.async_engine: SQLAlchemyAsyncEngine = create_sqlmodel_async_engine(
            url=self.postgres_uri,
            echo=settings.IS_DB_ECHO_LOG,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_POOL_OVERFLOW,
            poolclass=SQLAlchemyQueuePool,
        )
        self.async_session: SQLAlchemyAsyncSession = SQLAlchemyAsyncSession(
            bind=self.async_engine
        )
        self.pool: SQLAlchemyPool = self.async_engine.pool


async_db: AsyncDatabase = AsyncDatabase()
