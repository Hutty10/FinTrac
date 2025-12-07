import pydantic
from sqlalchemy.ext.asyncio import (
    async_sessionmaker as sqlalchemy_async_sessionmaker,
    AsyncEngine as SQLAlchemyAsyncEngine,
    AsyncSession as SQLAlchemyAsyncSession,
    create_async_engine as create_sqlmodel_async_engine,
)
from sqlalchemy.pool import Pool as SQLAlchemyPool, QueuePool as SQLAlchemyQueuePool

from app.config.manager import settings


class AsyncDatabase:
    def __init__(self):
        self.postgres_uri:  str = settings.DATABASE_URI
        self.async_engine: SQLAlchemyAsyncEngine = create_sqlmodel_async_engine(
            url=self.postgres_uri,
            echo=settings.IS_DB_ECHO_LOG,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_POOL_OVERFLOW,
            poolclass=SQLAlchemyQueuePool,
        )
        self.async_session: SQLAlchemyAsyncSession = SQLAlchemyAsyncSession(bind=self.async_engine)
        self.pool: SQLAlchemyPool = self.async_engine.pool




async_db: AsyncDatabase = AsyncDatabase()