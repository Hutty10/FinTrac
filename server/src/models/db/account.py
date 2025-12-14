# from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func

# if TYPE_CHECKING:
#     from .currency import Currency
#     from .transaction import Transaction
#     from .user import User


class AccountType(str, Enum):
    CASH = "Cash"
    BANK = "Bank"
    CARD = "Card"


class Account(SQLModel, table=True):
    __tablename__: str = "accounts"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    name: str = Field(index=True, nullable=False, max_length=20)
    account_type: str = Field(nullable=False, max_length=50)
    balance: float = Field(default=0.0, nullable=False)
    currency_id: UUID = Field(foreign_key="currencies.id", index=True, nullable=False)
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

    user: "User" = Relationship(back_populates="accounts")  # type: ignore # noqa: F821
    currency: "Currency" = Relationship(back_populates="accounts")  # type: ignore # noqa: F821
    transactions: List["Transaction"] = Relationship(  # type: ignore # noqa: F821
        back_populates="account",
        cascade_delete=True,
        sa_relationship_kwargs={"foreign_keys": "[Transaction.account_id]"},
    )
    outgoing_transfers: List["Transaction"] = Relationship(  # type: ignore # noqa: F821
        back_populates="to_account",
        sa_relationship_kwargs={"foreign_keys": "[Transaction.to_account_id]"},
    )
