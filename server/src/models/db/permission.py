from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Literal
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .models import User


class PermissionAction(str, Enum):
    """Fine-grained permission actions"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT = "export"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"


class ResourceType(str, Enum):
    """Resources that can be protected"""

    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    DOCUMENT = "document"
    REPORT = "report"
    SETTINGS = "settings"
    AUDIT_LOG = "audit_log"


class Permission(SQLModel, table=True):
    """Permission database model"""

    __tablename__: Literal["permissions"] = "permissions"

    id: UUID = Field(default_factory=lambda: uuid4(), primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str | None = None
    action: PermissionAction
    resource: ResourceType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    role_permissions: List["RolePermission"] = Relationship(back_populates="permission")


class Role(SQLModel, table=True):
    """Role database model"""

    __tablename__: Literal["roles"] = "roles"

    id: UUID = Field(default_factory=lambda: uuid4(), primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str | None = None
    is_system: bool = Field(default=False, description="System roles cannot be deleted")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    role_permissions: List["RolePermission"] = Relationship(
        back_populates="role", cascade_delete=True
    )
    users: List["User"] = Relationship(back_populates="role")


class RolePermission(SQLModel, table=True):
    """Maps permissions to roles with optional scoping"""

    __tablename__: Literal["role_permissions"] = "role_permissions"

    id: UUID = Field(default_factory=lambda: uuid4(), primary_key=True)
    role_id: UUID = Field(foreign_key="roles.id", index=True)
    permission_id: UUID = Field(foreign_key="permissions.id", index=True)
    scope: str | None = Field(
        default=None, description="Optional scope like tenant_id or resource_id"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    role: Role = Relationship(back_populates="role_permissions")
    permission: Permission = Relationship(back_populates="role_permissions")
