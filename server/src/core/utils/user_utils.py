from datetime import datetime, timedelta, timezone

from src.config.manager import settings
from src.core.utils.exceptions.base import BaseAppException
from src.models.db.user import User


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
