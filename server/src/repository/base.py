import logging
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError, SQLAlchemyError
from sqlmodel import SQLModel, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.utils.exceptions.base import BaseAppException

T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)


class UniqueConstraintError(BaseAppException):
    """Raised when unique constraint is violated"""

    def __init__(
        self,
        message: str = "A record with this value already exists",
        errors: dict[str, str] | None = None,
    ):
        super().__init__(message=message, status_code=409, errors=errors)


class ForeignKeyError(BaseAppException):
    """Raised when foreign key constraint is violated"""

    def __init__(
        self,
        message: str = "Referenced record does not exist",
        errors: dict[str, str] | None = None,
    ):
        super().__init__(message=message, status_code=400, errors=errors)


class DataValidationError(BaseAppException):
    """Raised when data validation fails"""

    def __init__(
        self,
        message: str = "Invalid data provided",
        errors: dict[str, str] | None = None,
    ):
        super().__init__(message=message, status_code=400, errors=errors)


class RepositoryError(BaseAppException):
    """Base repository exception"""

    def __init__(
        self, message: str = "Database error", errors: dict[str, str] | None = None
    ):
        super().__init__(message=message, status_code=500, errors=errors)


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
            await session.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")

            # Check for specific constraint violations
            if "unique constraint" in str(e.orig).lower():
                raise UniqueConstraintError(
                    "A record with this value already exists"
                ) from e
            elif "foreign key constraint" in str(e.orig).lower():
                raise ForeignKeyError("Referenced record does not exist") from e
            elif "not null constraint" in str(e.orig).lower():
                raise DataValidationError("Required field is missing") from e
            else:
                logger.error(f"Unknown integrity error: {e.orig}")
                raise RepositoryError("Integrity constraint violated: ") from e

        except DataError as e:
            await session.rollback()
            logger.error(f"Data error creating {self.model.__name__}: {e}")
            raise DataValidationError(f"Invalid data type provided: {str(e)}") from e

        except ProgrammingError as e:
            await session.rollback()
            logger.error(f"Programming error creating {self.model.__name__}: {e}")
            raise RepositoryError(f"Database programming error: {str(e)}") from e

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}") from e

        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error creating {self.model.__name__}: {e}")
            raise RepositoryError(f"Unexpected error: {str(e)}") from e

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

            await session.flush()
            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            await session.rollback()
            if "unique constraint" in str(e.orig).lower():
                raise UniqueConstraintError(
                    "A record with this value already exists"
                ) from e
            raise RepositoryError(f"Integrity error: {str(e.orig)}") from e
        except SQLAlchemyError as e:
            await session.rollback()
            raise RepositoryError(f"Error updating record: {str(e)}") from e

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
            raise RepositoryError(f"Error deleting record: {str(e)}") from e

    async def exists(self, session: AsyncSession, obj_id: int | UUID) -> bool:
        """Check if a record exists"""
        return await session.get(self.model, obj_id) is not None

    async def count(self, session: AsyncSession) -> int:
        """Count total records"""
        statement = select(func.count(self.model.id))  # type: ignore
        result = await session.execute(statement)
        return result.scalar_one() or 0

    async def save(self, session: AsyncSession, db_obj: T) -> T:
        """Save changes to an existing record"""
        try:
            session.add(db_obj)
            await session.flush()
            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            await session.rollback()
            if "unique constraint" in str(e.orig).lower():
                raise UniqueConstraintError(
                    "A record with this value already exists"
                ) from e
            raise RepositoryError(f"Integrity error: {str(e.orig)}") from e
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error saving {self.model.__name__}: {e}")
            raise RepositoryError(f"Error saving record: {str(e)}") from e
