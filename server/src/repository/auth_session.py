from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.auth_session import AuthSession
from src.repository.base import BaseRepository


class AuthSessionRepository(BaseRepository[AuthSession]):
    def __init__(self):
        super().__init__(AuthSession)

    async def get_active_by_jti(
        self, session: AsyncSession, jti: str
    ) -> AuthSession | None:
        stmt = select(AuthSession).where(
            AuthSession.refresh_token_jti == jti,
            AuthSession.is_active == True,  # noqa: E712
            AuthSession.expires_at > func.now(),
        )
        result = await session.exec(stmt)
        return result.one_or_none()

    async def revoke(self, session: AsyncSession, auth_session: AuthSession):
        auth_session.is_active = False
        auth_session.last_used_at = func.now()  # type: ignore
        await session.commit()

    async def touch(self, session: AsyncSession, auth_session: AuthSession):
        auth_session.last_used_at = func.now()  # type: ignore
        await session.commit()

    async def revoke_all(self, session, user_id: UUID):
        stmt = (
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,  # type: ignore
                AuthSession.is_active.is_(True),  # type: ignore
            )
            .values(is_active=False, refresh_token_jti=None)
        )
        await session.exec(stmt)
        await session.commit()

    async def count_active_sessions(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> int:
        query = select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.is_active.is_(True),  # type: ignore
            AuthSession.expires_at > datetime.now(timezone.utc),
        )
        stmt = select(func.count()).select_from(query.subquery())
        result = await session.exec(stmt)
        return result.one()

    async def revoke_oldest_sessions(
        self,
        session: AsyncSession,
        user_id: UUID,
        limit: int,
    ) -> None:
        stmt = (
            select(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.is_active.is_(True),  # type: ignore
            )
            .order_by(AuthSession.created_at.asc())  # type: ignore
            .limit(limit)
        )

        result = await session.exec(stmt)
        sessions = result.all()

        for auth_session in sessions:
            auth_session.is_active = False
            auth_session.refresh_token_jti = None

        await session.commit()

    async def revoke_by_device(
        self, session: AsyncSession, user_id: UUID, device_id: UUID
    ):
        stmt = (
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,  # type: ignore
                AuthSession.device_id == device_id,  # type: ignore
                AuthSession.is_active.is_(True),  # type: ignore
            )
            .values(is_active=False, refresh_token_jti=None)
        )
        await session.exec(stmt)
        await session.commit()


auth_session_repository = AuthSessionRepository()
