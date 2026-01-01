from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, DateTime, Field, Relationship, SQLModel


class SecurityEventTypeEnum(str, Enum):
    LOGIN_FAILURE = "login_failure"
    PASSWORD_CHANGE = "password_change"
    MFA_DISABLED = "mfa_disabled"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    NEW_DEVICE_LOGIN = "new_device_login"
    SESSION_INVALIDATED = "session_invalidated"
    LOGOUT_ALL_DEVICE = "logout_all_device"


class SecurityEvent(SQLModel, table=True):
    __tablename__: Literal["security_events"] = "security_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)

    event_type: SecurityEventTypeEnum
    ip_address: str | None = None
    user_agent: str | None = None
    meta: dict | None = Field(
        default=None,
        sa_column=Column(JSON),
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )

    user: "User" = Relationship(  # type: ignore # noqa: F821
        back_populates="security_events",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
