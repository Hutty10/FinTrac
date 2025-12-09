from src.models.db.permission import PermissionAction, ResourceType, Role


class PermissionChecker:
    """Utility for checking permissions"""

    @staticmethod
    async def has_permission(
        user_role: Role,
        action: PermissionAction,
        resource: ResourceType,
        scope: str | None = None,
    ) -> bool:
        """Check if role has specific permission"""
        for role_perm in user_role.role_permissions:
            perm = role_perm.permission
            if perm.action == action and perm.resource == resource:
                # If scope is required, check it matches
                if scope and role_perm.scope and role_perm.scope != scope:
                    continue
                return True
        return False

    @staticmethod
    async def get_permissions(user_role: Role) -> set[tuple[PermissionAction, ResourceType]]:
        """Get all permissions for a role"""
        return {
            (rp.permission.action, rp.permission.resource)
            for rp in user_role.role_permissions
        }
