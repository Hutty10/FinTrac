import threading
from datetime import datetime
from typing import Callable

from asgiref.sync import async_to_sync
from celery import shared_task

# from src.config.celery import celery_app
from src.core.utils.mail import create_message, mail


class EmailThread(threading.Thread):
    def __init__(self, func: Callable, *args, **kwargs) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.exception = None
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self) -> None:
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.exception = e
            raise


@shared_task
def send_verification_email_task(
    recipient_email: str, recipient_name: str, code: str, expiry: int
) -> None:
    message = create_message(
        recipients=[recipient_email],
        subject="Verify Your Email Address",
        body={
            "user_name": recipient_name,
            "otp_code": code,
            "expiry_minutes": str(expiry),
            "current_year": str(datetime.now().year),
            "support_url": "https://fintrac.app/support",
            "privacy_url": "https://fintrac.app/privacy",
            "terms_url": "https://fintrac.app/terms",
        },
    )

    async_to_sync(mail.send_message)(message, template_name="verification_email.html")


@shared_task
def send_password_reset_email_task(
    recipient_email: str, recipient_name: str, code: str, expiry: int
) -> None:
    message = create_message(
        recipients=[recipient_email],
        subject="Password Reset Request",
        body={
            "user_name": recipient_name,
            "otp_code": code,
            "expiry_minutes": str(expiry),
            "user_email": recipient_email,
            "request_time": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "ip_address": "Lagos, Nigeria",
            "current_year": str(datetime.now().year),
            "support_url": "https://fintrac.app/support",
            "security_url": "https://fintrac.app/security",
            "privacy_url": "https://fintrac.app/privacy",
        },
    )

    async_to_sync(mail.send_message)(message, template_name="password_reset_email.html")
