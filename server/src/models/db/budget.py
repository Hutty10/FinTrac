# from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func

# if TYPE_CHECKING:
#     from .category import Category
#     from .user import User


class BudgetFrequency(str, Enum):
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"


class Budget(SQLModel, table=True):
    __tablename__: str = "budgets"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    category_id: UUID = Field(foreign_key="categories.id", index=True, nullable=False)
    name: str = Field(index=True, nullable=False, max_length=100)
    amount: float = Field(nullable=False)
    frequency: BudgetFrequency = Field(nullable=False, max_length=20)
    start_date: datetime = Field(
        ...,
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
    end_date: datetime = Field(
        ...,
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
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

    user: "User" = Relationship(back_populates="budgets")  # type: ignore # noqa: F821
    category: "Category" = Relationship(back_populates="budgets")  # type: ignore # noqa: F821
