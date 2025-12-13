# from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

# if TYPE_CHECKING:
#     from .user import User


class AnalyticsEvent(SQLModel, table=True):
    __tablename__: str = "analytics_events"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID | None = Field(foreign_key="users.id", index=True, nullable=True)
    event_name: str = Field(nullable=False, max_length=100)
    event_data: str | None = Field(default=None, nullable=True)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Optional["User"] = Relationship(back_populates="analytics_events")  # type: ignore # noqa: F821
