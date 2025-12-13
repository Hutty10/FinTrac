from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.manager import settings

# engine: AsyncEngine = create_async_engine(
#     settings.DATABASE_URI,
#     echo=settings.IS_DB_ECHO_LOG,
#     future=True,
#     # pool_size=settings.DB_POOL_SIZE,
#     # max_overflow=settings.DB_POOL_OVERFLOW,
# )

# async_session_maker = sessionmaker(
#     bind=engine,  # type: ignore
#     class_=AsyncSession,
#     expire_on_commit=False,
# )  # type: ignore


class AsyncDatabase:
    def __init__(self):
        self.postgres_uri = settings.DATABASE_URI
        self.async_engine = create_async_engine(
            self.postgres_uri,
            echo=settings.IS_DB_ECHO_LOG,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_POOL_OVERFLOW,
            future=True,
        )

        self.session_maker = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


async_db = AsyncDatabase()
