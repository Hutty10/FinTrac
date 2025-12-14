# from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, Relationship, SQLModel

# if TYPE_CHECKING:
#     from .user import User


class AuditLog(SQLModel, table=True):
    __tablename__: str = "audit_logs"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    action: str = Field(nullable=False, max_length=100)
    entity: str = Field(nullable=False, max_length=100)
    entity_id: UUID | None = Field(default=None, nullable=True)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )
    details: str | None = Field(default=None, nullable=True)
    status_code: int = Field(nullable=False, ge=100, le=511)

    user: "User" = Relationship(back_populates="audit_logs")  # type: ignore # noqa: F821
