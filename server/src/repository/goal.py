from typing import Any, Tuple
from uuid import UUID

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.goal import Goal
from src.repository.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    def __init__(self):
        super().__init__(Goal)

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        page: int | None,
        page_size: int | None,
    ) -> Tuple[list[Goal], dict[str, Any]]:
        query = select(Goal).where(Goal.user_id == user_id)
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(total_query)
        total = total_result.scalar_one()

        if page and page_size:
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

        result = await session.exec(query)
        goals = result.all()

        metadata = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        }

        return list(goals), metadata
