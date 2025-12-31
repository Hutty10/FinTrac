# from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, computed_field

from src.models.db.goal import GoalStatus
from src.models.schemas.base import BaseSchemaModel


class GoalCreate(BaseSchemaModel):
    """Schema for creating a new goal"""

    currency_code: str | None = Field(None, min_length=3, max_length=3)
    name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    due_date: datetime | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "currency_code": "NGN",
                "name": "Emergency Fund",
                "target_amount": 10000.0,
                "due_date": "2025-12-31T23:59:59Z",
            }
        }


class GoalUpdate(BaseSchemaModel):
    """Schema for updating a goal"""

    name: str | None = Field(None, min_length=1, max_length=100)
    target_amount: float | None = Field(None, gt=0)
    current_amount: float | None = Field(None, ge=0)
    due_date: datetime | None = None
    status: GoalStatus | None = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Emergency Fund",
                "target_amount": 15000.0,
                "current_amount": 5000.0,
                "status": "Active",
            }
        }


class GoalRead(BaseSchemaModel):
    """Schema for reading/returning a goal"""

    id: UUID
    currency_code: str
    name: str
    target_amount: float
    current_amount: float
    due_date: datetime | None
    status: GoalStatus
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def percentage_completed(self) -> float:
        """Calculate the percentage of the goal completed."""
        if self.target_amount == 0:
            return 0.0
        return (self.current_amount / self.target_amount) * 100

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "currency_code": "NGN",
                "name": "Emergency Fund",
                "target_amount": 10000.0,
                "current_amount": 5000.0,
                "due_date": "2025-12-31T23:59:59Z",
                "status": "Active",
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-15T15:30:00Z",
                "percentage_completed": 50.0,
            }
        }


class GoalReadMax(BaseSchemaModel):
    """Schema for reading/returning a goal"""

    id: UUID
    user_id: UUID
    currency_code: str
    name: str
    target_amount: float
    current_amount: float
    due_date: datetime | None
    status: GoalStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "currency_id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Emergency Fund",
                "target_amount": 10000.0,
                "current_amount": 5000.0,
                "due_date": "2025-12-31T23:59:59Z",
                "status": "Active",
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-15T15:30:00Z",
            }
        }
