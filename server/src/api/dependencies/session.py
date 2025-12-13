from typing import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from src.repository.database import async_db


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_db.session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
