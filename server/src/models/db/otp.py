# from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel

# if TYPE_CHECKING:
#     from .user import User


class OTPType(str, Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    TWO_FACTOR = "two_factor"


class OTP(SQLModel, table=True):
    __tablename__: str = "otps"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    code: str = Field(nullable=False, max_length=6, min_length=6)
    type: OTPType = Field(nullable=False)
    is_used: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
    expires_at: datetime = Field(nullable=False, sa_type=DateTime(timezone=True))

    user: "User" = Relationship(back_populates="otps")  # type: ignore # noqa: F821

    def is_expired(self) -> bool:
        print("now:", datetime.now(timezone.utc))
        return datetime.now(timezone.utc) > self.expires_at
