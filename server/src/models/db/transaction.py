# from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func

# if TYPE_CHECKING:
#     from .account import Account
#     from .category import Category
#     from .currency import Currency
#     from .recurring_transaction import RecurringTransaction


class TransactionType(str, Enum):
    INCOME = "Income"
    EXPENSE = "Expense"
    TRANSFER = "Transfer"


class Transaction(SQLModel, table=True):
    __tablename__: str = "transactions"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    account_id: UUID = Field(foreign_key="accounts.id", index=True, nullable=False)
    category_id: UUID | None = Field(
        foreign_key="categories.id", index=True, nullable=True
    )
    currency_id: UUID | None = Field(
        foreign_key="currencies.id", index=True, nullable=True
    )
    to_account_id: UUID | None = Field(
        foreign_key="accounts.id", index=True, nullable=True
    )
    amount: float = Field(nullable=False)
    type: TransactionType = Field(nullable=False, max_length=20)
    description: str | None = Field(default=None, nullable=True, max_length=255)
    reference_number: str | None = Field(default=None, nullable=True, max_length=100)
    transaction_date: datetime = Field(
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

    currency: "Currency" = Relationship(back_populates="transactions")  # type: ignore # noqa: F821
    account: "Account" = Relationship(  # type: ignore # noqa: F821
        back_populates="transactions",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.account_id]"},
    )
    to_account: "Account" = Relationship(  # type: ignore # noqa: F821
        back_populates="outgoing_transfers",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.to_account_id]"},
    )
    recurring_transaction: Optional["RecurringTransaction"] = Relationship(  # type: ignore # noqa: F821
        back_populates="transaction",
        cascade_delete=True,
        sa_relationship_kwargs={"uselist": False, "lazy": "selectin"},
    )
    category: "Category" = Relationship(back_populates="transactions")  # type: ignore # noqa: F821
