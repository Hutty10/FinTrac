# from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func

# if TYPE_CHECKING:
#     from .account import Account
#     from .goal import Goal
#     from .subscription import Subscription
#     from .transaction import Transaction
#     from .user_pref import UserPreference


class Currency(SQLModel, table=True):
    __tablename__: str = "currencies"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    code: str = Field(index=True, unique=True, nullable=False, max_length=3)
    name: str = Field(nullable=False, max_length=100)
    symbol: str = Field(nullable=False, max_length=10)
    exchange_rate_to_usd: float = Field(nullable=False)
    decimal_places: int = Field(default=2, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
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

    accounts: List["Account"] = Relationship(back_populates="currency")  # type: ignore # noqa: F821
    goals: List["Goal"] = Relationship(back_populates="currency")  # type: ignore # noqa: F821
    subscriptions: List["Subscription"] = Relationship(back_populates="currency")  # type: ignore # noqa: F821
    transactions: List["Transaction"] = Relationship(back_populates="currency")  # type: ignore # noqa: F821
    user_preferences: List["UserPreference"] = Relationship(back_populates="currency")  # type: ignore # noqa: F821
