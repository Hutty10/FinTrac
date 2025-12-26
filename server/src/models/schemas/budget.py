from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.models.db.budget import BudgetFrequency
from src.models.schemas.base import BaseSchemaModel


class BudgetCreate(BaseSchemaModel):
    """Schema for creating a new budget"""

    category_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    frequency: BudgetFrequency
    start_date: datetime
    end_date: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "category_id": "b2557203-2c13-416c-bf8c-daa26705631e",
                "name": "Grocery Budget",
                "amount": 500.0,
                "frequency": "Weekly",
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-12-30T00:00:00Z",
            }
        }


class BudgetUpdate(BaseSchemaModel):
    """Schema for updating a budget"""

    name: str | None = Field(None, min_length=1, max_length=100)
    amount: float | None = Field(None, gt=0)
    frequency: BudgetFrequency | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Grocery Budget",
                "amount": 600.0,
                "frequency": "Monthly",
            }
        }


class BudgetRead(BaseSchemaModel):
    """Schema for reading/returning a budget"""

    id: UUID
    user_id: UUID
    category_id: UUID
    name: str
    amount: float
    frequency: BudgetFrequency
    start_date: datetime
    end_date: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "category_id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Grocery Budget",
                "amount": 500.0,
                "frequency": "Monthly",
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-012-30T00:00:00Z",
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-01T10:00:00Z",
            }
        }
