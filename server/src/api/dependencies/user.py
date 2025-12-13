from typing import Any
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.session import get_session
from src.core.securities.jwt import jwt_manager
from src.core.utils.exceptions.base import BaseAppException
from src.models.db.user import User
from src.repository.user import user_repository


class TokenBearer(HTTPBearer):
    def __init__(self, token_type: str, auto_error: bool = True) -> None:
        super().__init__(auto_error=auto_error)
        self.token_type = token_type

    async def __call__(self, request: Request) -> dict[str, Any]:
        creds: HTTPAuthorizationCredentials | None = await super().__call__(request)
        if not creds:
            raise BaseAppException(message="Not authenticated.", status_code=401)
        if creds and creds.scheme != "Bearer":
            raise BaseAppException(
                message="Invalid authentication scheme.", status_code=401
            )

        token: str = creds.credentials
        token_data = await jwt_manager.verify_token(
            token=token, token_type=self.token_type
        )

        return token_data


class AccessTokenBearer(TokenBearer):
    def __init__(self, auto_error=True) -> None:
        super().__init__("access", auto_error)


async def get_current_active_user(
    token: dict[str, Any] = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
) -> User:
    user_id: UUID | None = token.get("user_id")
    if not user_id:
        raise BaseAppException(message="Invalid token payload", status_code=401)
    user: User | None = await user_repository.get_by_id(session, user_id)
    if not user:
        raise BaseAppException(
            message="User not found",
            status_code=401,
        )
    if not user.is_active:
        raise BaseAppException(message="User not active", status_code=403)
    return user
