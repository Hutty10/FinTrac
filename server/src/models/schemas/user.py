from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from src.models.schemas.auth_device import LoginContextSchema, LoginDeviceSchema
from src.models.schemas.base import BaseSchemaModel


class ChangePassword(BaseSchemaModel):
    """Schema for changing user password"""

    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

    device: LoginDeviceSchema
    context: LoginContextSchema | None = None

    @field_validator("new_password")
    def validate_new_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()-_=+[]|;:,<.>/?`~" for c in value):
            raise ValueError("Password must contain at least one special character")

        return value

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!",
                "device": {
                    "device_id": "ios-uuid-12345",
                    "device_name": "John's iPhone",
                    "device_type": "iOS",
                    "app_version": "1.0.0",
                },
                "context": {
                    "ip_address": "197.210.12.45",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                },
            }
        }


class UserRead(BaseSchemaModel):
    """Schema for reading/returning user data"""

    id: UUID
    email: EmailStr
    username: str | None
    first_name: str
    last_name: str
    phone_number: str | None
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-15T15:30:00Z",
                "last_login": "2025-01-15T14:00:00Z",
            }
        }


class UserReadMax(BaseSchemaModel):
    """Schema for reading/returning user data with maximum details"""

    id: UUID
    email: EmailStr
    username: str | None
    first_name: str
    last_name: str
    phone_number: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "is_active": True,
                "is_verified": True,
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-15T15:30:00Z",
                "last_login": "2025-01-15T14:00:00Z",
            }
        }


class UserUpdate(BaseSchemaModel):
    """Schema for updating user data"""

    username: str | None = Field(None, min_length=1, max_length=50)
    first_name: str | None = Field(None, min_length=1)
    last_name: str | None = Field(None, min_length=1)
    phone_number: str | None = Field(None, max_length=20)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe_updated",
                "first_name": "Jonathan",
                "last_name": "Doe",
                "phone_number": "+9876543210",
            }
        }
