from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.models.db.account import AccountType
from src.models.schemas.base import BaseSchemaModel


class AccountCreate(BaseSchemaModel):
    """Schema for creating a new account"""

    name: str = Field(..., max_length=20, description="The name of the account")
    account_type: AccountType = Field(
        ..., description="The type of account (Cash, Bank, Card)"
    )
    balance: float = Field(
        default=0.0,
        ge=0,
        description="The initial balance of the account (must be non-negative)",
    )
    currency_code: str | None = Field(
        ...,
        description="The code of the currency for this account",
        max_length=3,
        min_length=3,
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Checking Account",
                "account_type": "Bank",
                "balance": 1000.00,
                "currency_code": "NGN",
            }
        }


class AccountReadMini(BaseSchemaModel):
    """Minimal schema for reading/returning an account"""

    id: UUID = Field(..., description="The unique account ID")
    name: str = Field(..., description="The name of the account")
    account_type: AccountType = Field(..., description="The type of account")
    balance: float = Field(..., description="The current balance of the account")
    currency_code: str = Field(
        ..., description="The code of the currency for this account"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Checking Account",
                "account_type": "Bank",
                "balance": 1000.00,
                "currency_id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
            }
        }


class AccountRead(BaseSchemaModel):
    """Schema for reading/returning an account"""

    id: UUID = Field(..., description="The unique account ID")
    user_id: UUID = Field(..., description="The ID of the user who owns this account")
    name: str = Field(..., description="The name of the account")
    account_type: AccountType = Field(..., description="The type of account")
    balance: float = Field(..., description="The current balance of the account")
    currency_code: str = Field(
        ..., description="The code of the currency for this account"
    )
    is_active: bool = Field(..., description="Whether this account is active")
    created_at: datetime = Field(..., description="When the account was created")
    updated_at: datetime = Field(..., description="When the account was last updated")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660f9511-f30c-52e5-b827-557766551111",
                "name": "Checking Account",
                "account_type": "Bank",
                "balance": 1000.00,
                "currency_id": "NGN",
                "is_active": True,
                "created_at": "2025-12-13T10:30:00",
                "updated_at": "2025-12-13T10:30:00",
            }
        }


class AccountUpdate(BaseSchemaModel):
    """Schema for updating an account"""

    name: str | None = Field(
        default=None, max_length=20, description="The name of the account"
    )
    account_type: AccountType | None = Field(
        default=None, description="The type of account (Cash, Bank, Card)"
    )
    balance: float | None = Field(
        default=None,
        ge=0,
        description="The balance of the account (must be non-negative)",
    )
    currency_code: str | None = Field(
        default=None, description="The code of the currency for this account"
    )
    is_active: bool | None = Field(
        default=None, description="Whether this account is active"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Updated Checking Account",
                "balance": 1500.00,
                "is_active": True,
            }
        }
