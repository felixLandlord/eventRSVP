from typing import List, Optional
from backend.repository.event_repository import EventRepository
from backend.repository.ticket_repository import TicketRepository
from backend.repository.rsvp_repository import RSVPRepository
from backend.graphql_api.types import EventType, EventInput

from backend.schemas.event_schema import EventCreate, EventUpdate
from backend.schemas.ticket_schema import TicketCreate  # , TicketInput


class EventService:

    @staticmethod
    async def create_event(
        event_data: EventInput, organizer_id: int
    ) -> Optional[EventType]:
        event = EventCreate(
            title=event_data.title,
            description=event_data.description,
            category=event_data.category,
            location=event_data.location,
            venue_address=event_data.venue_address,
            start_date=event_data.start_date,
            end_date=event_data.end_date,
            timezone=event_data.timezone,
            max_attendees=event_data.max_attendees,
            is_free=event_data.is_free,
            organizer_id=organizer_id,
        )

        created_event = await EventRepository.create(event)

        # Create default free ticket if event is free
        if event_data.is_free:
            default_ticket = TicketCreate(
                name="General Admission",
                description="Free admission to the event",
                price=0.0,
                quantity_total=event_data.max_attendees or 1000,
                event_id=created_event.id,
            )
            await TicketRepository.create(default_ticket)

        return await EventService.get_event_by_id(created_event.id)

    @staticmethod
    async def get_all_events(
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[EventType]:
        events = await EventRepository.get_all(
            skip=skip, limit=limit, category=category, search=search
        )

        result = []
        for event in events:
            attendee_count = await EventRepository.get_attendee_count(event.id)
            event_type = EventType(
                id=event.id,
                title=event.title,
                description=event.description,
                category=event.category,
                location=event.location,
                venue_address=event.venue_address,
                start_date=event.start_date,
                end_date=event.end_date,
                timezone=event.timezone,
                max_attendees=event.max_attendees,
                is_free=event.is_free,
                cover_image=event.cover_image,
                status=event.status,
                organizer_id=event.organizer_id,
                created_at=event.created_at,
                attendee_count=attendee_count,
            )
            result.append(event_type)

        return result

    @staticmethod
    async def get_event_by_id(event_id: int) -> Optional[EventType]:
        event = await EventRepository.get_by_id(event_id)
        if not event:
            return None

        attendee_count = await EventRepository.get_attendee_count(event_id)

        return EventType(
            id=event.id,
            title=event.title,
            description=event.description,
            category=event.category,
            location=event.location,
            venue_address=event.venue_address,
            start_date=event.start_date,
            end_date=event.end_date,
            timezone=event.timezone,
            max_attendees=event.max_attendees,
            is_free=event.is_free,
            cover_image=event.cover_image,
            status=event.status,
            organizer_id=event.organizer_id,
            created_at=event.created_at,
            attendee_count=attendee_count,
        )

    @staticmethod
    async def update_event(event_id: int, event_data: EventInput, user_id: int) -> str:
        event = await EventRepository.get_by_id(event_id)
        if not event or event.organizer_id != user_id:
            raise ValueError("Event not found or unauthorized!")

        updated_event = EventUpdate(
            title=event_data.title,
            description=event_data.description,
            category=event_data.category,
            location=event_data.location,
            venue_address=event_data.venue_address,
            start_date=event_data.start_date,
            end_date=event_data.end_date,
            timezone=event_data.timezone,
            max_attendees=event_data.max_attendees,
            is_free=event_data.is_free,
        )

        await EventRepository.update(event_id, updated_event)
        return f"Event {event_id} updated successfully!"

    @staticmethod
    async def delete_event(event_id: int, user_id: int) -> str:
        event = await EventRepository.get_by_id(event_id)
        if not event or event.organizer_id != user_id:
            raise ValueError("Event not found or unauthorized!")

        await EventRepository.delete(event_id)
        return f"Event {event_id} deleted successfully!"

    @staticmethod
    async def get_user_events(user_id: int) -> List[EventType]:
        events = await EventRepository.get_by_organizer(user_id)

        result = []
        for event in events:
            attendee_count = await EventRepository.get_attendee_count(event.id)
            event_type = EventType(
                id=event.id,
                title=event.title,
                description=event.description,
                category=event.category,
                location=event.location,
                venue_address=event.venue_address,
                start_date=event.start_date,
                end_date=event.end_date,
                timezone=event.timezone,
                max_attendees=event.max_attendees,
                is_free=event.is_free,
                cover_image=event.cover_image,
                status=event.status,
                organizer_id=event.organizer_id,
                created_at=event.created_at,
                attendee_count=attendee_count,
            )
            result.append(event_type)

        return result

    @staticmethod
    async def get_event_analytics(event_id: int, organizer_id: int) -> dict:
        event = await EventRepository.get_by_id(event_id)
        if not event or event.organizer_id != organizer_id:
            raise ValueError("Event not found or unauthorized!")

        total_rsvps = await RSVPRepository.get_event_check_in_summary(event_id)
        return total_rsvps
