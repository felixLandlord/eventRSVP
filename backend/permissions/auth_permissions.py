from strawberry.permission import BasePermission
from strawberry.types import Info
from backend.schemas.user_schema import UserRole
from backend.core.logger import get_logger

logger = get_logger("permissions")


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source, info: Info, **kwargs) -> bool:
        authenticated = info.context.get("current_user") is not None
        if not authenticated:
            logger.warning("Permission denied: User not authenticated")
        return authenticated


class IsAdmin(BasePermission):
    message = "User is not an admin"

    def has_permission(self, source, info: Info, **kwargs) -> bool:
        user = info.context.get("current_user")
        is_admin = user is not None and user.role == UserRole.ADMIN
        if not is_admin:
            logger.warning(
                f"Permission denied: User {user.id if user else 'None'} is not admin"
            )
        return is_admin


class IsOrganizer(BasePermission):
    message = "User is not an organizer"

    def has_permission(self, source, info: Info, **kwargs) -> bool:
        user = info.context.get("current_user")
        is_organizer = user is not None and user.role == UserRole.ORGANIZER
        if not is_organizer:
            logger.warning(
                f"Permission denied: User {user.id if user else 'None'} is not organizer"
            )
        return is_organizer
