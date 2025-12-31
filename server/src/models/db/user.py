# from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

from pwdlib import PasswordHash
from pydantic import EmailStr
from sqlmodel import DateTime, Field, Relationship, SQLModel, func

from src.core.securities.jwt import jwt_manager

# if TYPE_CHECKING:
#     from .account import Account
#     from .analytics_event import AnalyticsEvent
#     from .audit_log import AuditLog
#     from .budget import Budget
#     from .category import Category
#     from .goal import Goal
#     from .otp import OTP
#     from .permission import Role
#     from .streak import Streak
#     from .subscription import Subscription
#     from .terms_acceptance import TermsAcceptance
#     from .user_pref import UserPreference


password_hash = PasswordHash.recommended()


class User(SQLModel, table=True):
    __tablename__: str = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: EmailStr = Field(index=True, unique=True, nullable=False)
    username: str | None = Field(
        default=None, index=True, unique=True, nullable=True, max_length=50
    )
    first_name: str = Field(default=None, nullable=False)
    last_name: str = Field(default=None, nullable=False)
    phone_number: str | None = Field(default=None, nullable=True)
    hashed_password: str = Field(nullable=False)
    role_id: UUID = Field(foreign_key="roles.id", index=True)
    is_active: bool = Field(default=True, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
    is_deleted: bool = Field(default=False, nullable=False)
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
    last_login: datetime | None = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),
    )
    deleted_at: datetime | None = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),
    )

    role: "Role" = Relationship(back_populates="users")  # type: ignore # noqa: F821
    preferences: List["UserPreference"] = Relationship(back_populates="user")  # type: ignore # noqa: F821
    accounts: List["Account"] = Relationship(back_populates="user", cascade_delete=True)  # type: ignore # noqa: F821
    analytics_events: List["AnalyticsEvent"] = Relationship(back_populates="user")  # type: ignore # noqa: F821
    audit_logs: List["AuditLog"] = Relationship(  # type: ignore # noqa: F821
        back_populates="user", cascade_delete=False
    )
    budgets: List["Budget"] = Relationship(back_populates="user", cascade_delete=True)  # type: ignore # noqa: F821
    categories: List["Category"] = Relationship(  # type: ignore # noqa: F821
        back_populates="user", cascade_delete=True
    )
    goals: List["Goal"] = Relationship(back_populates="user", cascade_delete=True)  # type: ignore # noqa: F821
    subscriptions: List["Subscription"] = Relationship(  # type: ignore # noqa: F821
        back_populates="user", cascade_delete=True
    )
    streak: "Streak" = Relationship(back_populates="user", cascade_delete=True)  # type: ignore # noqa: F821
    terms_acceptances: List["TermsAcceptance"] = Relationship(  # type: ignore # noqa: F821
        back_populates="user", cascade_delete=True
    )
    otps: List["OTP"] = Relationship(back_populates="user", cascade_delete=True)  # type: ignore # noqa: F821

    def set_password(self, password: str) -> None:
        self.hashed_password = password_hash.hash(password)

    def verify_password(self, password: str) -> bool:
        if not self.hashed_password:
            return False
        return password_hash.verify(password, self.hashed_password)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    async def tokens(self) -> dict[str, str]:
        return await jwt_manager.create_token_pair(user_id=self.id)
