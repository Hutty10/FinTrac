from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, EmailStr, field_validator

from src.models.db.user_pref import ThemeEnum
from src.models.schemas.auth_device import LoginContextSchema, LoginDeviceSchema
from src.models.schemas.base import BaseSchemaModel
from src.models.schemas.terms import TermsAcceptanceItem


class RegisterUserSchema(BaseSchemaModel):
    email: EmailStr
    username: str | None = None
    first_name: str
    last_name: str
    password: str
    prefered_locale: str
    theme: ThemeEnum
    accept_terms: bool
    accepted_terms: list[TermsAcceptanceItem]

    device: LoginDeviceSchema
    context: LoginContextSchema | None = None

    @field_validator("password")
    def validate_password(cls, value):
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "password": "Password1!",
                "prefered_locale": "en-NG",
                "theme": "light",
                "accept_terms": True,
                "accepted_terms": [
                    {
                        "terms_id": "c8a6c9e4-6f5d-4c3b-9b6f-2c7a0e8b4f11",
                        "version": "v1.0",
                    }
                ],
                "device": {
                    "device_id": "android-uuid-98765",
                    "device_name": "Samsung S23",
                    "platform": "android",
                    "os_version": "14",
                    "app_version": "1.0.0",
                },
                "context": {
                    "ip_address": "197.210.12.45",
                    "user_agent": "okhttp/4.11.0",
                },
            }
        }
    )

    @field_validator("accept_terms")
    def validate_accept_terms(cls, value):
        if not value:
            raise ValueError("Terms must be accepted to register")
        return value


class VerifyEmailSchema(BaseSchemaModel):
    email: EmailStr
    code: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "john.doe@example.com", "code": "483920"}
        }
    )


class ResendVerificationEmailSchema(BaseSchemaModel):
    email: EmailStr

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "john.doe@example.com"}}
    )


class LoginSchema(BaseSchemaModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str

    device: LoginDeviceSchema
    context: LoginContextSchema | None = None

    @field_validator("email", "username", mode="before")
    def validate_email_or_username(cls, value, info):
        if not value and not info.data.get(
            "username" if info.field_name == "email" else "email"
        ):
            raise ValueError("Either email or username must be provided")
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "Password1!",
                "device": {
                    "device_id": "android-uuid-98765",
                    "device_name": "Samsung S23",
                    "platform": "android",
                    "os_version": "14",
                    "app_version": "1.0.0",
                },
                "context": {
                    "ip_address": "197.210.12.45",
                    "user_agent": "okhttp/4.11.0",
                },
            }
        }
    )


class RefreshTokenSchema(BaseSchemaModel):
    refresh_token: str
    rotate: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "rotate": True,
            }
        }
    )


class TokenSchema(BaseSchemaModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class LoginDeviceResponseSchema(BaseSchemaModel):
    id: UUID
    is_trusted: bool
    last_login_at: datetime | None


class LoginResponse(BaseSchemaModel):
    user_id: UUID
    tokens: TokenSchema
    device: LoginDeviceResponseSchema
    requires_device_verification: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "5c9c5f1d-3d59-4d6c-bf94-9c9c4f90c001",
                "tokens": {
                    "access_token": "access.jwt.token",
                    "refresh_token": "refresh.jwt.token",
                    "token_type": "bearer",
                },
                "device": {
                    "id": "e3a8b0e9-9f1a-4e6a-b71c-13a6e9b82f55",
                    "is_trusted": False,
                    "last_login_at": "2025-01-01T10:15:30Z",
                },
                "requires_device_verification": False,
            }
        }
    )


class ForgotPasswordSchema(BaseSchemaModel):
    email: EmailStr | None = None
    username: str | None = None

    @field_validator("email", "username", mode="before")
    def validate_email_or_username(cls, value, info):
        if not value and not info.data.get(
            "username" if info.field_name == "email" else "email"
        ):
            raise ValueError("Either email or username must be provided")
        return value


class VerifyPasswordResetSchema(BaseSchemaModel):
    email: EmailStr | None = None
    username: str | None = None
    code: str

    @field_validator("email", "username", mode="before")
    def validate_email_or_username(cls, value, info):
        if not value and not info.data.get(
            "username" if info.field_name == "email" else "email"
        ):
            raise ValueError("Either email or username must be provided")
        return value


class ResetPasswordSchema(BaseSchemaModel):
    email: EmailStr | None = None
    username: str | None = None
    token: str
    new_password: str

    device: LoginDeviceSchema
    context: LoginContextSchema | None = None

    @field_validator("email", "username", mode="before")
    def validate_email_or_username(cls, value, info):
        if not value and not info.data.get(
            "username" if info.field_name == "email" else "email"
        ):
            raise ValueError("Either email or username must be provided")
        return value

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


class LogoutSchema(BaseSchemaModel):
    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
    )
