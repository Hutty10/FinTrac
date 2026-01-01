import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Request

from src.config.manager import settings
from src.core.securities.jwt import jwt_manager
from src.core.utils.exceptions.base import BaseAppException
from src.models.db.user import User

logger = logging.getLogger(__name__)


def check_deleted_user(user: User) -> None:
    """Check if user account is deleted and calculate recovery time"""
    if user.is_deleted and user.deleted_at:
        deletion_time = user.deleted_at
        recovery_time = deletion_time + timedelta(days=settings.ACCOUNT_DELETION_DAYS)
        current_time = datetime.now(timezone.utc)

        remaining_time = recovery_time - current_time

        # If account deletion period has expired
        if remaining_time.total_seconds() <= 0:
            raise BaseAppException(
                message="User account permanently deleted",
                status_code=403,
            )

        # Convert to human-readable format
        days_remaining = remaining_time.days
        hours_remaining = remaining_time.seconds // 3600
        minutes_remaining = (remaining_time.seconds % 3600) // 60

        raise BaseAppException(
            message=(
                f"User account deleted. You can recover your account in "
                f"{days_remaining}d {hours_remaining}h {minutes_remaining}m"
                "reach out to customer support to recover ur account"
            ),
            status_code=403,
        )


async def extract_user_id(request: Request) -> UUID | None:
    """
    Extract user ID from request Authorization header.
    """
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1]
            payload = await jwt_manager.verify_token(token=token, token_type="access")
            user_id_str = payload.get("user_id")
            if user_id_str:
                return UUID(user_id_str)

        return None
    except Exception as exc:
        logger.warning(f"Failed to extract user_id: {exc}")
        return None


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def extract_email(request: Request) -> str | None:
    try:
        if request.method not in {"POST", "PUT", "PATCH"}:
            return None

        body = await request.body()
        if not body:
            return None

        data = json.loads(body)

        return data.get("email")

    except Exception:
        return None

async def extract_username(request: Request) -> str | None:
    try:
        if request.method not in {"POST", "PUT", "PATCH"}:
            return None

        body = await request.body()
        if not body:
            return None

        data = json.loads(body)

        return data.get("username")

    except Exception:
        return None
