from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import UUID, uuid4

import jwt
from fastapi import status

from src.config.manager import settings
from src.core.cache_manager import cache_manager
from src.core.utils.exceptions.base import BaseAppException


class JWTManager:
    """Production-ready JWT manager for FastAPI applications."""

    def __init__(self):
        """
        Initialize JWT manager.
        Raises:
            ValueError: If secret key is not set or too short
        """
        if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
            raise ValueError("Secret key must be at least 32 characters long")

        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = (
            settings.JWT_ACCESS_TOKEN_EXPIRATION_TIME_IN_SECONDS // 60
        )
        self.refresh_token_expire_days = (
            settings.JWT_REFRESH_TOKEN_EXPIRATION_TIME_IN_SECONDS // (60 * 60 * 24)
        )

    async def _create_token(
        self,
        user_id: UUID,
        expires_delta: timedelta,
        token_type: str,
        additional_claims: Dict[str, Any] | None = None,
    ) -> str:
        """Create a JWT token."""
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "token_type": token_type,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": uuid4().hex,
            "user_id": str(user_id),
        }

        if additional_claims:
            payload.update(additional_claims)

        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def create_access_token(
        self, user_id: UUID, additional_claims: Dict[str, Any] | None = None
    ) -> str:
        """Create an access token."""
        return await self._create_token(
            user_id=user_id,
            expires_delta=timedelta(minutes=self.access_token_expire_minutes),
            token_type="access",
            additional_claims=additional_claims,
        )

    async def create_refresh_token(
        self, user_id: UUID, additional_claims: Dict[str, Any] | None = None
    ) -> str:
        """Create a refresh token."""
        return await self._create_token(
            user_id=user_id,
            expires_delta=timedelta(days=self.refresh_token_expire_days),
            token_type="refresh",
            additional_claims=additional_claims,
        )

    async def create_token_pair(
        self, user_id: UUID, additional_claims: Dict[str, Any] | None = None
    ) -> Dict[str, str]:
        """Create both access and refresh tokens."""
        return {
            "access_token": await self.create_access_token(
                user_id, additional_claims=additional_claims
            ),
            "refresh_token": await self.create_refresh_token(
                user_id, additional_claims=additional_claims
            ),
            "token_type": "bearer",
        }

    async def verify_token(
        self, token: str, token_type: str = "access"
    ) -> Dict[str, Any]:
        """
        Verify and decode a token.

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify token type
            if payload.get("token_type") != token_type:
                raise BaseAppException(
                    message="Invalid token type",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    errors={"token_type": "Token type does not match"},
                )
            if token_type == "refresh":
                jti = payload.get("jti")
                if jti and await self._is_token_blacklisted(jti):
                    raise BaseAppException(
                        message="Token has been revoked",
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        errors={"token": "Token has been revoked"},
                    )

            return payload

        except jwt.ExpiredSignatureError:
            raise BaseAppException(
                message="Token has expired",
                status_code=status.HTTP_401_UNAUTHORIZED,
                errors={"token": "Token has expired"},
            )
        except jwt.InvalidTokenError:
            raise BaseAppException(
                message="Invalid token",
                status_code=status.HTTP_401_UNAUTHORIZED,
                errors={"token": "Invalid token"},
            )

    async def blacklist_refresh_token(self, refresh_token: str) -> bool:
        """
        Blacklist a refresh token (useful for logout).

        Args:
            refresh_token: The refresh token to blacklist

        Returns:
            True if successfully blacklisted

        Raises:
            BaseAppException: If token is invalid
        """
        try:
            payload = jwt.decode(
                refresh_token, self.secret_key, algorithms=[self.algorithm]
            )

            if payload.get("token_type") != "refresh":
                raise BaseAppException(
                    message="Invalid token type",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    errors={"token_type": "Token type does not match"},
                )

            jti = payload.get("jti")
            if not jti:
                raise BaseAppException(
                    message="Invalid token",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    errors={"token": "Token missing jti claim"},
                )

            # Calculate TTL (time until token expiration)
            exp = payload.get("exp")
            if exp:
                ttl = int(exp - datetime.now(timezone.utc).timestamp())
                if ttl > 0:
                    # Store in Redis with TTL matching token expiration
                    cache_key = cache_manager.cache_key("blacklist", "token", jti)
                    await cache_manager.set(cache_key, "blacklisted", ttl=ttl)

            return True

        except jwt.InvalidTokenError:
            raise BaseAppException(
                message="Invalid token",
                status_code=status.HTTP_401_UNAUTHORIZED,
                errors={"token": "Invalid token"},
            )

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """
        Async version to check if a token JTI is blacklisted.

        Args:
            jti: The token's JTI claim

        Returns:
            True if token is blacklisted, False otherwise
        """
        cache_key = cache_manager.cache_key("blacklist", "token", jti)
        exists = await cache_manager.exists(cache_key)
        return exists > 0

    async def refresh_access_token(
        self, refresh_token: str, rotate: bool = False
    ) -> Dict[str, str]:
        """Generate a new access token from a valid refresh token."""
        payload = await self.verify_token(refresh_token, token_type="refresh")
        user_id = UUID(payload.get("user_id"))
        additional_claims = {
            k: v
            for k, v in payload.items()
            if k not in {"exp", "iat", "jti", "user_id", "token_type"}
        }

        new_access_token: str = await self.create_access_token(
            user_id, additional_claims=additional_claims
        )
        if rotate:
            refresh_token = await self.create_refresh_token(
                user_id, additional_claims=additional_claims
            )

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


jwt_manager = JWTManager()
