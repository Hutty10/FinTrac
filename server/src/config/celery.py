import logging

from celery import Celery
from celery.schedules import crontab

from src.config.manager import settings

logger = logging.getLogger(__name__)


def celery_config() -> Celery:
    celery_app = Celery(
        "FinTrac",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_BACKEND_URL,
    )

    celery_app.autodiscover_tasks(
        ["src.core.tasks.email_tasks", "src.core.tasks.cron_tasks"], force=True
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        result_expires=3600,
    )

    celery_app.autodiscover_tasks(
        ["src.core.tasks.email_tasks", "src.core.tasks.cron_tasks"], force=True
    )

    celery_app.conf.beat_schedule = {
        "check-and-delete-expired-users": {
            "task": "src.core.tasks.cron_tasks.check_and_delete_expired_users",
            "schedule": crontab(hour=2, minute=0),
        },
    }
    return celery_app


celery_app = celery_config()

logger.info("Celery app initialized")
logger.info(
    f"Registered tasks: {[k for k in celery_app.tasks.keys() if not k.startswith('celery.')]}"
)
