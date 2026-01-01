from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel


class AuthSession(SQLModel, table=True):
    __tablename__: Literal["auth_sessions"] = "auth_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    device_id: UUID = Field(foreign_key="user_devices.id", nullable=False)

    refresh_token_jti: str | None = None

    is_active: bool = Field(default=True)

    expires_at: datetime = Field(
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
    last_used_at: datetime | None = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )

    user: "User" = Relationship(  # type: ignore # noqa: F821
        back_populates="auth_sessions",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    device: "UserDevice" = Relationship(  # type: ignore # noqa: F821
        back_populates="auth_sessions",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
