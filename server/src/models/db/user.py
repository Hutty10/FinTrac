from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .permission import Role


class User(SQLModel, table=True):
    __tablename__: str = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: EmailStr = Field(index=True, unique=True, nullable=False)
    Username: str | None = Field(
        default=None, index=True, unique=True, nullable=True, max_length=50
    )
    first_name: str | None = Field(default=None, nullable=True)
    last_name: str | None = Field(default=None, nullable=True)
    hashed_password: str = Field(nullable=False)
    role_id: UUID = Field(foreign_key="roles.id", index=True)
    is_active: bool = Field(default=True, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_login: datetime | None = None

    role: "Role" = Relationship(back_populates="users")
