from typing import Generic
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, TypeVar, List
from sqlmodel import  select
from sqlalchemy.exc import SQLAlchemyError

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """Generic repository base class for common CRUD operations"""
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def create(self, obj_in: dict | T) -> T:
        """Create a new record"""
        try:
            if isinstance(obj_in, dict):
                db_obj = self.model(**obj_in)
            else:
                db_obj = obj_in
            
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error creating record: {str(e)}")
    
    async def get_by_id(self, obj_id: int|UUID) -> T|None:
        """Get a record by ID"""
        return await self.session.get(self.model, obj_id)
    
    async def get_all(self, skip: int|None = None, limit:int|None = None) -> List[T]:
        """Get all records with pagination"""
        statement = select(self.model)
        if skip is not None and limit is not None:
            statement = statement.offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
    
    async def update(self, obj_id: int|UUID, obj_in: dict) -> T|None:
        """Update a record by ID"""
        try:
            db_obj = await self.session.get(self.model, obj_id)
            if not db_obj:
                return None
            
            for key, value in obj_in.items():
                setattr(db_obj, key, value)
            
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error updating record: {str(e)}")
    
    async def delete(self, obj_id: int|UUID) -> bool:
        """Delete a record by ID"""
        try:
            db_obj = await self.session.get(self.model, obj_id)
            if not db_obj:
                return False
            
            await self.session.delete(db_obj)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error deleting record: {str(e)}")
    
    async def exists(self, obj_id: int|UUID) -> bool:
        """Check if a record exists"""
        return await self.session.get(self.model, obj_id) is not None
    
    async def count(self) -> int:
        """Count total records"""
        statement = select(self.model)
        result = await self.session.execute(statement)
        return len(result.all())