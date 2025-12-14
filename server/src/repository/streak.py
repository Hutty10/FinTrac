from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.streak import Streak
from src.repository.base import BaseRepository


class StreakRepository(BaseRepository[Streak]):
    def __init__(self):
        super().__init__(Streak)

    async def get_by_user_id(
        self, session: AsyncSession, user_id: UUID
    ) -> Streak | None:
        """Get a streak by user ID"""
        statement = select(self.model).where(self.model.user_id == user_id)
        result = await session.exec(statement)
        return result.first()

    async def increment_streak(self, session: AsyncSession, user_id: UUID) -> Streak:
        """
        Calculates and updates the user's streak based on the last active date.
        Returns the updated Streak object.
        """
        streak = await self.get_by_user_id(session, user_id)

        if not streak:
            new_streak = Streak(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_active_date=datetime.now(timezone.utc),
            )
            session.add(new_streak)
            await session.commit()
            await session.refresh(new_streak)
            return new_streak

        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)

        last_active = (
            streak.last_active_date.date() if streak.last_active_date else None
        )

        if last_active == today:
            return streak

        if last_active == yesterday:
            streak.current_streak += 1
            current_streak = streak.current_streak
            if current_streak > streak.longest_streak:
                streak.longest_streak = current_streak
                print("Longest streak updated")

            streak.last_active_date = datetime.now(timezone.utc)
            session.add(streak)
            print("Streak incremented")

        elif last_active is None or last_active < yesterday:
            streak.current_streak = 1
            streak.last_active_date = datetime.now(timezone.utc)
            session.add(streak)
            print("Streak reset to 1")

        await session.commit()
        await session.refresh(streak)

        return streak
