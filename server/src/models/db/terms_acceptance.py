# from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel

# if TYPE_CHECKING:
#     from .user import User


class TermsAcceptance(SQLModel, table=True):
    __tablename__: str = "terms_acceptances"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    terms_version: str = Field(nullable=False, max_length=20)
    accepted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
    ip_address: str | None = Field(default=None, nullable=True, max_length=45)
    device_info: str | None = Field(default=None, nullable=True, max_length=255)

    user: "User" = Relationship(back_populates="terms_acceptances")  # type: ignore # noqa: F821
