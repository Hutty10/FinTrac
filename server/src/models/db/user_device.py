from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func


class PlatformEnum(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"
    OTHER = "other"


class UserDevice(SQLModel, table=True):
    __tablename__: Literal["user_devices"] = "user_devices"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)

    device_id: str = Field(index=True)
    device_name: str | None = None
    platform: PlatformEnum
    os_version: str | None = None
    app_version: str | None = None

    ip_address: str | None = None
    user_agent: str | None = None

    is_trusted: bool = Field(default=False)
    last_login_at: datetime | None = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),
    )
    last_ip_address: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": func.now()},
    )

    user: "User" = Relationship(  # type: ignore # noqa: F821
        back_populates="user_devices",
        sa_relationship_kwargs={"uselist": False, "lazy": "selectin"},
    )
    auth_sessions: list["AuthSession"] = Relationship(  # type: ignore # noqa: F821
        back_populates="device",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
