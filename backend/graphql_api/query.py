from typing import List, Optional
import strawberry

from backend.services.event_service import EventService
from backend.services.rsvp_service import RSVPService
from backend.graphql_api.types import (
    EventType,
    RSVPType,
    UserType,
    EventCheckInSummaryType,
)
from backend.permissions.auth_permissions import IsAuthenticated, IsOrganizer
from backend.core.limiter import limiter, RATE_LIMITS


@strawberry.type
class Query:

    @strawberry.field
    @limiter.limit(RATE_LIMITS["query_hello"])
    def hello(self) -> str:
        return "Welcome to Event Management Platform!"

    @strawberry.field(permission_classes=[IsAuthenticated])
    @limiter.limit(RATE_LIMITS["query_me"])
    async def me(self, info) -> UserType:
        if not info.context["current_user"]:
            raise ValueError("Not authenticated")
        return info.context["current_user"]

    @strawberry.field
    @limiter.limit(RATE_LIMITS["query_get_events"])
    async def get_events(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[EventType]:
        return await EventService.get_all_events(skip, limit, category, search)

    @strawberry.field
    @limiter.limit(RATE_LIMITS["query_get_event"])
    async def get_event(self, event_id: int) -> Optional[EventType]:
        return await EventService.get_event_by_id(event_id)

    @strawberry.field(permission_classes=[IsAuthenticated])
    @limiter.limit(RATE_LIMITS["query_get_my_events"])
    async def get_my_events(self, info) -> List[EventType]:
        user = info.context["current_user"]
        return await EventService.get_user_events(user.id)

    @strawberry.field(permission_classes=[IsAuthenticated])
    @limiter.limit(RATE_LIMITS["query_get_my_rsvps"])
    async def get_my_rsvps(self, info) -> List[RSVPType]:
        user = info.context["current_user"]
        return await RSVPService.get_user_rsvps(user.id)

    @strawberry.field(permission_classes=[IsAuthenticated])
    @limiter.limit(RATE_LIMITS["query_get_event_attendees"])
    async def get_event_attendees(self, info, event_id: int) -> List[RSVPType]:
        user = info.context["current_user"]
        return await RSVPService.get_event_attendees(event_id, user.id)

    @strawberry.field(permission_classes=[IsOrganizer])
    @limiter.limit(RATE_LIMITS["query_get_event_analytics"])
    async def get_event_analytics(self, info, event_id: int) -> EventCheckInSummaryType:
        user = info.context["current_user"]
        data = await EventService.get_event_analytics(event_id, user.id)
        return EventCheckInSummaryType(**data)
