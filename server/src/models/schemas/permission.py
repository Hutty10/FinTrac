from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import Field

from src.models.db.permission import PermissionAction, ResourceType
from src.models.schemas.base import BaseSchemaModel


class PermissionRead(BaseSchemaModel):
    """Permission response"""

    id: UUID
    name: str
    description: str | None
    action: PermissionAction
    resource: ResourceType
    created_at: datetime
    updated_at: datetime


class RolePermissionRead(BaseSchemaModel):
    """Role-permission response"""

    id: UUID
    role_id: UUID
    permission_id: UUID
    scope: str | None
    permission: PermissionRead
    created_at: datetime


class RoleRead(BaseSchemaModel):
    """Role response with permissions"""

    id: UUID
    name: str
    description: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime
    role_permissions: List[RolePermissionRead]


class RoleCreate(BaseSchemaModel):
    """Create role request"""

    name: str
    description: str | None = None
    permissions: List[str] = Field(default_factory=list, description="Permission IDs")


class RoleUpdate(BaseSchemaModel):
    """Update role request"""

    name: str | None = None
    description: str | None = None
    permissions: List[str] | None = None
