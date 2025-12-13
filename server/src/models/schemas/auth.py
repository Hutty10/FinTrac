from pydantic import EmailStr, field_validator

from src.models.db.user_pref import ThemeEnum
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
    ip_address: str | None = None
    device_info: str | None = None

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

    @field_validator("accept_terms")
    def validate_accept_terms(cls, value):
        if not value:
            raise ValueError("Terms must be accepted to register")
        return value


class VerifyEmailSchema(BaseSchemaModel):
    email: EmailStr
    code: str


class ResendVerificationEmailSchema(BaseSchemaModel):
    email: EmailStr


class LoginSchema(BaseSchemaModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str

    @field_validator("email", "username", mode="before")
    def validate_email_or_username(cls, value, info):
        if not value and not info.data.get(
            "username" if info.field_name == "email" else "email"
        ):
            raise ValueError("Either email or username must be provided")
        return value


class RefreshTokenSchema(BaseSchemaModel):
    refresh_token: str
    rotate: bool = True


class TokenSchema(BaseSchemaModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


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