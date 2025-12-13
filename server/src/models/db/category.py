# from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func

# if TYPE_CHECKING:
#     from .budget import Budget
#     from .transaction import Transaction
#     from .user import User


class CategoryType(str, Enum):
    INCOME = "Income"
    EXPENSE = "Expense"


class Category(SQLModel, table=True):
    __tablename__: str = "categories"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID | None = Field(foreign_key="users.id", index=True, nullable=True)
    name: str = Field(index=True, nullable=False, max_length=50)
    type: CategoryType = Field(nullable=False, max_length=20)
    icon: str = Field(default=None, nullable=True, max_length=100)
    color: str = Field(default=None, nullable=True, max_length=20)
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

    user: Optional["User"] = Relationship(back_populates="categories")  # type: ignore # noqa: F821
    budgets: List["Budget"] = Relationship(back_populates="category")  # type: ignore # noqa: F821
    transactions: List["Transaction"] = Relationship(back_populates="category")  # type: ignore # noqa: F821
