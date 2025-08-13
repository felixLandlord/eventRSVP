from typing import List
from datetime import datetime, timezone

from backend.schemas.rsvp_schema import RSVPCreate, RSVPStatus
from backend.repository.rsvp_repository import RSVPRepository
from backend.repository.event_repository import EventRepository
from backend.repository.ticket_repository import TicketRepository
from backend.graphql_api.types import RSVPType, RSVPInput
from backend.services.qr_service import QRGenerator
from backend.services.email_service import EmailService


class RSVPService:

    @staticmethod
    async def create_rsvp(rsvp_data: RSVPInput, user_id: int) -> RSVPType:
        # Verify event and ticket exist
        event = await EventRepository.get_by_id(rsvp_data.event_id)
        if not event:
            raise ValueError("Event not found!")

        ticket = await TicketRepository.get_by_id(rsvp_data.ticket_id)
        if not ticket or ticket.event_id != rsvp_data.event_id:
            raise ValueError("Invalid ticket!")

        # Check if user already has RSVP for this event
        existing_rsvp = await RSVPRepository.get_by_user_and_event(
            user_id, rsvp_data.event_id
        )
        if existing_rsvp:
            raise ValueError("You have already RSVP'd to this event!")

        if ticket.quantity_sold >= ticket.quantity_total:
            raise ValueError("This ticket type is sold out!")

        qr_code = QRGenerator.generate_rsvp_qr(user_id, rsvp_data.event_id)

        rsvp = RSVPCreate(
            event_id=rsvp_data.event_id,
            user_id=user_id,
            ticket_id=rsvp_data.ticket_id,
            status=RSVPStatus.CONFIRMED,
            qr_code=qr_code,
        )

        created_rsvp = await RSVPRepository.create(rsvp)

        await TicketRepository.increment_sold_count(rsvp_data.ticket_id)

        await EmailService.send_rsvp_confirmation(user_id, rsvp_data.event_id)

        return RSVPType(
            id=created_rsvp.id,
            event_id=created_rsvp.event_id,
            user_id=created_rsvp.user_id,
            ticket_id=created_rsvp.ticket_id,
            status=created_rsvp.status,
            qr_code=created_rsvp.qr_code,
            checked_in_at=created_rsvp.checked_in_at,
            created_at=created_rsvp.created_at,
        )

    @staticmethod
    async def check_in_attendee(rsvp_id: int, organizer_id: int) -> str:
        rsvp = await RSVPRepository.get_by_id(rsvp_id)
        if not rsvp:
            raise ValueError("RSVP not found!")

        event = await EventRepository.get_by_id(rsvp.event_id)
        if not event or event.organizer_id != organizer_id:
            raise ValueError("Unauthorized to check in attendees for this event!")

        if rsvp.status == RSVPStatus.ATTENDED:
            raise ValueError("Attendee already checked in!")

        await RSVPRepository.update_status(
            rsvp_id, RSVPStatus.ATTENDED, datetime.now(timezone.utc)
        )

        return "Attendee checked in successfully!"

    @staticmethod
    async def cancel_rsvp(rsvp_id: int, user_id: int) -> str:
        rsvp = await RSVPRepository.get_by_id(rsvp_id)
        if not rsvp or rsvp.user_id != user_id:
            raise ValueError("RSVP not found or unauthorized!")

        if rsvp.status == RSVPStatus.ATTENDED:
            raise ValueError("Cannot cancel RSVP after attending event!")

        await RSVPRepository.update_status(rsvp_id, RSVPStatus.CANCELLED)

        await TicketRepository.decrement_sold_count(rsvp.ticket_id)

        return "RSVP cancelled successfully!"

    @staticmethod
    async def get_user_rsvps(user_id: int) -> List[RSVPType]:
        rsvps = await RSVPRepository.get_by_user(user_id)

        return [
            RSVPType(
                id=rsvp.id,
                event_id=rsvp.event_id,
                user_id=rsvp.user_id,
                ticket_id=rsvp.ticket_id,
                status=rsvp.status,
                qr_code=rsvp.qr_code,
                checked_in_at=rsvp.checked_in_at,
                created_at=rsvp.created_at,
            )
            for rsvp in rsvps
        ]

    @staticmethod
    async def get_event_attendees(event_id: int, organizer_id: int) -> List[RSVPType]:
        event = await EventRepository.get_by_id(event_id)
        if not event or event.organizer_id != organizer_id:
            raise ValueError("Unauthorized to view attendees for this event!")

        rsvps = await RSVPRepository.get_by_event(event_id)

        return [
            RSVPType(
                id=rsvp.id,
                event_id=rsvp.event_id,
                user_id=rsvp.user_id,
                ticket_id=rsvp.ticket_id,
                status=rsvp.status,
                qr_code=rsvp.qr_code,
                checked_in_at=rsvp.checked_in_at,
                created_at=rsvp.created_at,
            )
            for rsvp in rsvps
        ]
