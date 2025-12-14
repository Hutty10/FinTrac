# from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel, func

# if TYPE_CHECKING:
#     from .transaction import Transaction


class RecurringTransaction(SQLModel, table=True):
    __tablename__: str = "recurring_transactions"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    transaction_id: UUID = Field(
        foreign_key="transactions.id", index=True, nullable=False, unique=True
    )
    interval: str = Field(nullable=False, max_length=50)
    next_occurrence: datetime = Field(
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
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

    transaction: "Transaction" = Relationship(  # type: ignore # noqa: F821
        back_populates="recurring_transaction",
        sa_relationship_kwargs={"uselist": False},
    )
