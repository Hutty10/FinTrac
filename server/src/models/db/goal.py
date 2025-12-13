# from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func

# if TYPE_CHECKING:
#     from .currency import Currency
#     from .user import User


class GoalStatus(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Goal(SQLModel, table=True):
    __tablename__: str = "goals"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    currency_id: UUID = Field(foreign_key="currencies.id", index=True, nullable=False)
    name: str = Field(index=True, nullable=False, max_length=100)
    target_amount: float = Field(nullable=False)
    current_amount: float = Field(default=0.0, nullable=False)
    due_date: datetime | None = Field(default=None, nullable=True)
    status: GoalStatus = Field(default=GoalStatus.ACTIVE, nullable=False, max_length=20)
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

    user: "User" = Relationship(back_populates="goals")  # type: ignore # noqa: F821
    currency: "Currency" = Relationship(back_populates="goals")  # type: ignore # noqa: F821
