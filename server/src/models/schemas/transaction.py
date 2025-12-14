from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from src.models.db.transaction import TransactionType
from src.models.schemas.base import BaseSchemaModel


class RecurringTransactionCreate(BaseSchemaModel):
    """Schema for creating a recurring transaction"""

    interval: str = Field(
        ...,
        max_length=50,
        description="Recurrence interval (daily, weekly, monthly, yearly)",
    )
    is_active: bool = Field(
        default=True, description="Whether this recurring transaction is active"
    )


class RecurringTransactionRead(BaseSchemaModel):
    """Schema for reading a recurring transaction"""

    # id: UUID = Field(..., description="The unique recurring transaction ID")
    # transaction_id: UUID = Field(..., description="The ID of the associated transaction")
    interval: str = Field(
        ..., description="Recurrence interval (daily, weekly, monthly, yearly)"
    )
    next_occurrence: datetime = Field(..., description="Date of the next occurrence")
    is_active: bool = Field(
        ..., description="Whether this recurring transaction is active"
    )
    # created_at: datetime = Field(..., description="When the recurring transaction was created")
    # updated_at: datetime = Field(..., description="When the recurring transaction was last updated")

    class Config:
        from_attributes = True


class RecurringTransactionUpdate(BaseSchemaModel):
    """Schema for updating a recurring transaction"""

    interval: str | None = Field(
        default=None,
        max_length=50,
        description="Recurrence interval (daily, weekly, monthly, yearly)",
    )
    is_active: bool | None = Field(
        default=None, description="Whether this recurring transaction is active"
    )

    class Config:
        from_attributes = True


class TransactionCreate(BaseSchemaModel):
    """Schema for creating a new transaction"""

    account_id: UUID = Field(
        ..., description="The ID of the account for this transaction"
    )
    category_id: UUID | None = Field(
        default=None,
        description="The ID of the category (required for Income/Expense, optional for Transfer)",
    )
    currency_id: UUID = Field(
        ..., description="The ID of the currency for this transaction"
    )
    to_account_id: UUID | None = Field(
        default=None,
        description="The destination account ID (required for Transfer, optional otherwise)",
    )
    amount: float = Field(
        ..., gt=0, description="The transaction amount (must be positive)"
    )
    type: TransactionType = Field(
        ..., description="The type of transaction (Income, Expense, Transfer)"
    )
    description: str | None = Field(
        default=None,
        max_length=255,
        description="Optional description of the transaction",
    )
    reference_number: str | None = Field(
        default=None,
        max_length=100,
        description="Optional reference number (useful for linking transfers)",
    )
    transaction_date: datetime | None = Field(
        default=None,
        description="The date of the transaction. Defaults to current datetime if not provided",
    )
    recurring: RecurringTransactionCreate | None = Field(
        default=None,
        description="Optional recurring transaction details. If provided, creates a recurring pattern for this transaction",
    )

    @field_validator("category_id", mode="before")
    @classmethod
    def validate_category_for_transfer(cls, v, info):
        """Category is required for Income/Expense, must be null for Transfer"""
        if info.data.get("type") in [TransactionType.INCOME, TransactionType.EXPENSE]:
            if v is None:
                raise ValueError(
                    "category_id is required for Income and Expense transactions"
                )
        elif info.data.get("type") == TransactionType.TRANSFER:
            if v is not None:
                raise ValueError("category_id must be null for Transfer transactions")
        return v

    @field_validator("to_account_id", mode="before")
    @classmethod
    def validate_to_account_for_transfer(cls, v, info):
        """to_account_id is required for Transfer, must be null otherwise"""
        if info.data.get("type") == TransactionType.TRANSFER:
            if v is None:
                raise ValueError("to_account_id is required for Transfer transactions")
        else:
            if v is not None:
                raise ValueError(
                    "to_account_id must be null for Income and Expense transactions"
                )
        return v

    @field_validator("to_account_id", mode="before")
    @classmethod
    def validate_accounts_not_same(cls, v, info):
        """Account and to_account must be different for transfers"""
        if (
            info.data.get("type") == TransactionType.TRANSFER
            and v is not None
            and v == info.data.get("account_id")
        ):
            raise ValueError(
                "Cannot transfer to the same account. Account and to_account_id must be different"
            )
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "category_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "currency_id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
                "amount": 150.50,
                "type": "Expense",
                "description": "Grocery shopping",
                "transaction_date": "2025-12-13T10:30:00",
            }
        }


class TransactionRead(BaseSchemaModel):
    """Schema for reading/returning a transaction"""

    id: UUID = Field(..., description="The unique transaction ID")
    account_id: UUID = Field(..., description="The account ID for this transaction")
    category_id: UUID | None = Field(
        default=None, description="The category ID (null for transfers)"
    )
    currency_id: UUID = Field(..., description="The currency ID for this transaction")
    to_account_id: UUID | None = Field(
        default=None, description="The destination account ID (for transfers only)"
    )
    amount: float = Field(..., description="The transaction amount")
    type: TransactionType = Field(..., description="The transaction type")
    description: str | None = Field(
        default=None, description="The transaction description"
    )
    reference_number: str | None = Field(
        default=None, description="The transaction reference number"
    )
    transaction_date: datetime = Field(..., description="The date of the transaction")
    created_at: datetime = Field(..., description="When the transaction was created")
    updated_at: datetime = Field(
        ..., description="When the transaction was last updated"
    )
    recurring_transaction: RecurringTransactionRead | None = Field(
        default=None,
        description="Recurring transaction details if this transaction is recurring",
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "account_id": "550e8400-e29b-41d4-a716-446655440001",
                "category_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "currency_id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
                "to_account_id": None,
                "amount": 150.50,
                "type": "Expense",
                "description": "Grocery shopping",
                "reference_number": None,
                "transaction_date": "2025-12-13T10:30:00",
                "created_at": "2025-12-13T10:30:00",
                "updated_at": "2025-12-13T10:30:00",
                "recurring_transaction": None,
            }
        }


class TransactionUpdate(BaseSchemaModel):
    """Schema for updating a transaction"""

    account_id: UUID | None = Field(
        default=None, description="The ID of the account for this transaction"
    )
    category_id: UUID | None = Field(
        default=None,
        description="The ID of the category (required for Income/Expense, optional for Transfer)",
    )
    currency_id: UUID | None = Field(
        default=None, description="The ID of the currency for this transaction"
    )
    to_account_id: UUID | None = Field(
        default=None,
        description="The destination account ID (required for Transfer, optional otherwise)",
    )
    amount: float | None = Field(
        default=None, gt=0, description="The transaction amount (must be positive)"
    )
    type: TransactionType | None = Field(
        default=None, description="The type of transaction (Income, Expense, Transfer)"
    )
    description: str | None = Field(
        default=None,
        max_length=255,
        description="Optional description of the transaction",
    )
    reference_number: str | None = Field(
        default=None,
        max_length=100,
        description="Optional reference number (useful for linking transfers)",
    )
    transaction_date: datetime | None = Field(
        default=None,
        description="The date of the transaction",
    )
    recurring: RecurringTransactionUpdate | None = Field(
        default=None,
        description="Optional recurring transaction details to update",
    )

    @field_validator("category_id", mode="before")
    @classmethod
    def validate_category_for_transaction(cls, v, info):
        """Category is required for Income/Expense, must be null for Transfer"""
        transaction_type = info.data.get("type")

        if transaction_type is None:
            return v

        if transaction_type == TransactionType.TRANSFER:
            if v is not None:
                raise ValueError("category_id must be null for Transfer transactions")
        elif transaction_type in [TransactionType.INCOME, TransactionType.EXPENSE]:
            if v is None:
                raise ValueError(
                    "category_id is required for Income and Expense transactions"
                )
        return v

    @field_validator("to_account_id", mode="before")
    @classmethod
    def validate_to_account_for_transfer(cls, v, info):
        """to_account_id is required for Transfer, must be null otherwise"""
        transaction_type = info.data.get("type")

        if transaction_type is None:
            return v

        if transaction_type == TransactionType.TRANSFER:
            if v is None:
                raise ValueError("to_account_id is required for Transfer transactions")
        else:
            if v is not None:
                raise ValueError(
                    "to_account_id must be null for Income and Expense transactions"
                )
        return v

    @field_validator("to_account_id", mode="before")
    @classmethod
    def validate_accounts_not_same(cls, v, info):
        """Account and to_account must be different for transfers"""
        if (
            info.data.get("type") == TransactionType.TRANSFER
            and v is not None
            and v == info.data.get("account_id")
        ):
            raise ValueError(
                "Cannot transfer to the same account. Account and to_account_id must be different"
            )
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "amount": 200.00,
                "description": "Updated grocery shopping amount",
                "recurring": {
                    "interval": "weekly",
                    "is_active": True,
                }
            }
        }