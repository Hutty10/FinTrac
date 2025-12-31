from celery import shared_task

from src.config.manager import settings
from src.models.db.user import User


@shared_task(bind=True, name="check_and_delete_expired_users")
def check_and_delete_expired_users(self) -> dict:
    """Check all soft-deleted users and permanently delete if 30 days have passed"""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlmodel import select

    try:
        # Synchronous database setup for Celery (use sync driver for SQLModel)
        sync_database_url = settings.DATABASE_URI.replace("asyncpg", "psycopg2")
        engine = create_engine(sync_database_url, echo=False)

        with Session(engine) as session:
            # Find all deleted users whose deletion period has expired
            deletion_deadline = datetime.now(timezone.utc) - timedelta(days=30)

            expired_users = session.execute(
                select(User).where(
                    User.is_deleted == True,  # noqa: E712
                    User.deleted_at <= deletion_deadline,  # type: ignore
                )
            ).all()

            deleted_count = 0
            skipped_count = 0
            errors = []

            for user in expired_users:
                try:
                    session.delete(user)
                    deleted_count += 1
                except Exception as e:
                    skipped_count += 1
                    errors.append(f"Failed to delete user {user.id}: {str(e)}")

            # Commit all deletions at once
            if deleted_count > 0:
                session.commit()

            return {
                "status": "success",
                "deleted_count": deleted_count,
                "skipped_count": skipped_count,
                "errors": errors,
                "message": f"Deleted {deleted_count} expired user accounts",
            }
    except Exception as exc:
        # Retry task up to 3 times with exponential backoff
        raise self.retry(exc=exc, countdown=60, max_retries=3)
