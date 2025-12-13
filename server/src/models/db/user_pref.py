# from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func

# if TYPE_CHECKING:
#     from .currency import Currency
#     from .user import User


class ThemeEnum(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class UserPreference(SQLModel, table=True):
    __tablename__: str = "user_preferences"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    locale: str = Field(default="en_US", nullable=False, max_length=10)
    theme: ThemeEnum = Field(default=ThemeEnum.LIGHT, nullable=False, max_length=20)
    default_currency_id: UUID = Field(
        foreign_key="currencies.id",
        index=True,
        nullable=False,
    )
    notifications_enabled: bool = Field(default=True, nullable=False)
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

    user: "User" = Relationship(back_populates="preferences")  # type: ignore # noqa: F821
    currency: "Currency" = Relationship(back_populates="user_preferences")  # type: ignore # noqa: F821
