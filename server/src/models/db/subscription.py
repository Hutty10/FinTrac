# from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func

# if TYPE_CHECKING:
#     from .currency import Currency
#     from .user import User


class BillingCycle(str, Enum):
    MONTHLY = "Monthly"
    YEARLY = "Yearly"
    ONE_TIME = "One-Time"


class Subscription(SQLModel, table=True):
    __tablename__: str = "subscriptions"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    name: str = Field(index=True, nullable=False, max_length=100)
    price: float = Field(nullable=False)
    currency_id: UUID = Field(foreign_key="currencies.id", index=True, nullable=False)
    billing_cycle: BillingCycle = Field(nullable=False, max_length=20)
    start_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    end_date: datetime | None = Field(default=None, nullable=True)
    next_billing_date: datetime | None = Field(default=None, nullable=True)
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

    user: "User" = Relationship(back_populates="subscriptions")  # type: ignore # noqa: F821
    currency: "Currency" = Relationship(back_populates="subscriptions")  # type: ignore # noqa: F821
