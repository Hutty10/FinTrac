import logging
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """Generic repository base class for common CRUD operations"""

    def __init__(self, model: type[T]):
        self.model = model

    async def create(self, session: AsyncSession, obj_in: dict | T) -> T:
        """Create a new record"""
        try:
            if isinstance(obj_in, dict):
                db_obj = self.model(**obj_in)
            else:
                db_obj = obj_in
            session.add(db_obj)
            await session.flush()
            await session.commit()
            await session.refresh(db_obj)  # ✅ Add this line
            return db_obj
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise Exception(f"Error creating record: {str(e)}")

    async def get_by_id(self, session: AsyncSession, obj_id: int | UUID) -> T | None:
        """Get a record by ID"""
        return await session.get(self.model, obj_id)

    async def get_all(
        self, session: AsyncSession, skip: int | None = None, limit: int | None = None
    ) -> list[T]:
        """Get all records with pagination"""
        statement = select(self.model)
        if skip is not None and limit is not None:
            statement = statement.offset(skip).limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def update(
        self, session: AsyncSession, obj_id: int | UUID, obj_in: dict
    ) -> T | None:
        """Update a record by ID"""
        try:
            db_obj = await session.get(self.model, obj_id)
            if not db_obj:
                return None

            for key, value in obj_in.items():
                setattr(db_obj, key, value)

            # session.add(db_obj)
            await session.flush()
            await session.commit()
            # await session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await session.rollback()
            raise Exception(f"Error updating record: {str(e)}")

    async def delete(self, session: AsyncSession, obj_id: int | UUID) -> bool:
        """Delete a record by ID"""
        try:
            db_obj = await session.get(self.model, obj_id)
            if not db_obj:
                return False

            await session.delete(db_obj)
            await session.commit()
            return True
        except SQLAlchemyError as e:
            await session.rollback()
            raise Exception(f"Error deleting record: {str(e)}")

    async def exists(self, session: AsyncSession, obj_id: int | UUID) -> bool:
        """Check if a record exists"""
        return await session.get(self.model, obj_id) is not None

    async def count(self, session: AsyncSession) -> int:
        """Count total records"""
        statement = select(func(self.model))
        result = await session.execute(statement)
        return result.scalar_one() or 0
