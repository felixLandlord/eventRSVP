from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.sql import select, update as sql_update, delete as sql_delete, func
from sqlalchemy.orm import selectinload
from backend.models.rsvp_model import RSVP
from backend.models.user_model import User
from backend.models.event_model import Event
from backend.models.ticket_model import Ticket
from backend.core.database import db
from backend.schemas.rsvp_schema import RSVPCreate, RSVPUpdate, RSVPStatus


class RSVPRepository:

    @staticmethod
    async def create(rsvp_data: RSVPCreate) -> RSVP:
        async with db as session:
            rsvp = RSVP(**rsvp_data.model_dump())
            session.add(rsvp)
            await db.commit_rollback()
            await session.refresh(rsvp)
            return rsvp

    @staticmethod
    async def get_by_id(rsvp_id: int) -> Optional[RSVP]:
        async with db as session:
            stmt = select(RSVP).where(RSVP.id == rsvp_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_by_user(user_id: int) -> List[RSVP]:
        async with db as session:
            stmt = (
                select(RSVP)
                .where(RSVP.user_id == user_id)
                .order_by(RSVP.created_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_by_event(event_id: int) -> List[RSVP]:
        async with db as session:
            stmt = (
                select(RSVP)
                .where(RSVP.event_id == event_id)
                .order_by(RSVP.created_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_by_user_and_event(user_id: int, event_id: int) -> Optional[RSVP]:
        async with db as session:
            stmt = select(RSVP).where(
                RSVP.user_id == user_id, RSVP.event_id == event_id
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def update(rsvp_id: int, rsvp_data: RSVPUpdate) -> Optional[RSVP]:
        async with db as session:
            stmt = select(RSVP).where(RSVP.id == rsvp_id)
            result = await session.execute(stmt)
            rsvp = result.scalars().first()

            if not rsvp:
                return None

            for field, value in rsvp_data.model_dump(exclude_unset=True).items():
                if hasattr(rsvp, field) and value is not None:
                    setattr(rsvp, field, value)

            rsvp.updated_at = datetime.now(timezone.utc)
            await db.commit_rollback()
            await session.refresh(rsvp)
            return rsvp

    @staticmethod
    async def delete(rsvp_id: int) -> bool:
        async with db as session:
            stmt = sql_delete(RSVP).where(RSVP.id == rsvp_id)
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def update_status(
        rsvp_id: int, status: RSVPStatus, checked_in_at: Optional[datetime] = None
    ) -> bool:
        async with db as session:
            update_values = {
                "status": status,
                "updated_at": datetime.now(timezone.utc),
            }
            if checked_in_at:
                update_values["checked_in_at"] = checked_in_at

            stmt = sql_update(RSVP).where(RSVP.id == rsvp_id).values(**update_values)
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def get_event_attendees_with_details(event_id: int) -> List[dict]:
        """Get attendees with user and ticket details"""
        async with db as session:
            stmt = (
                select(RSVP, User, Ticket)
                .join(User, RSVP.user_id == User.id)
                .join(Ticket, RSVP.ticket_id == Ticket.id)
                .where(RSVP.event_id == event_id)
                .order_by(RSVP.created_at.desc())
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [
                {"rsvp": row.RSVP, "user": row.User, "ticket": row.Ticket}
                for row in rows
            ]

    @staticmethod
    async def get_user_rsvps_with_details(user_id: int) -> List[dict]:
        """Get user RSVPs with event and ticket details"""
        async with db as session:
            stmt = (
                select(RSVP, Event, Ticket)
                .join(Event, RSVP.event_id == Event.id)
                .join(Ticket, RSVP.ticket_id == Ticket.id)
                .where(RSVP.user_id == user_id)
                .order_by(RSVP.created_at.desc())
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [
                {"rsvp": row.RSVP, "event": row.Event, "ticket": row.Ticket}
                for row in rows
            ]

    @staticmethod
    async def get_event_statistics(event_id: int) -> dict:
        """Get comprehensive event statistics"""
        async with db as session:
            total_stmt = select(func.count(RSVP.id)).where(
                RSVP.event_id == event_id, ~RSVP.is_deleted
            )
            total_result = await session.execute(total_stmt)
            total_rsvps = total_result.scalar() or 0

            status_stmt = (
                select(RSVP.status, func.count(RSVP.id).label("count"))
                .where(RSVP.event_id == event_id)
                .group_by(RSVP.status)
            )
            status_result = await session.execute(status_stmt)

            status_breakdown = {
                row._mapping["status"]: int(row._mapping["count"] or 0)
                for row in status_result.all()
            }

            checked_in_count = status_breakdown.get(RSVPStatus.ATTENDED, 0)
            confirmed_count = status_breakdown.get(RSVPStatus.CONFIRMED, 0)
            check_in_rate = (
                (checked_in_count / (confirmed_count + checked_in_count) * 100)
                if (confirmed_count + checked_in_count) > 0
                else 0
            )

            return {
                "total_rsvps": total_rsvps,
                "status_breakdown": status_breakdown,
                "confirmed": status_breakdown.get(RSVPStatus.CONFIRMED, 0),
                "attended": status_breakdown.get(RSVPStatus.ATTENDED, 0),
                "cancelled": status_breakdown.get(RSVPStatus.CANCELLED, 0),
                "no_show": status_breakdown.get(RSVPStatus.NO_SHOW, 0),
                "check_in_rate": round(check_in_rate, 2),
            }

    @staticmethod
    async def get_upcoming_user_events(user_id: int) -> List[dict]:
        """Get user's upcoming events they've RSVP'd to"""
        async with db as session:
            stmt = (
                select(RSVP, Event)
                .join(Event, RSVP.event_id == Event.id)
                .where(
                    RSVP.user_id == user_id,
                    RSVP.status.in_([RSVPStatus.CONFIRMED, RSVPStatus.PENDING]),
                    Event.start_date > datetime.now(timezone.utc),
                )
                .order_by(Event.start_date.asc())
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [{"rsvp": row.RSVP, "event": row.Event} for row in rows]

    @staticmethod
    async def get_past_user_events(user_id: int) -> List[dict]:
        """Get user's past events they've attended"""
        async with db as session:
            stmt = (
                select(RSVP, Event)
                .join(Event, RSVP.event_id == Event.id)
                .where(
                    RSVP.user_id == user_id,
                    Event.end_date < datetime.now(timezone.utc),
                )
                .order_by(Event.end_date.desc())
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [{"rsvp": row.RSVP, "event": row.Event} for row in rows]

    @staticmethod
    async def check_user_rsvp_exists(user_id: int, event_id: int) -> bool:
        """Check if user already has an active RSVP for the event"""
        async with db as session:
            stmt = select(func.count(RSVP.id)).where(
                RSVP.user_id == user_id,
                RSVP.event_id == event_id,
                RSVP.status != RSVPStatus.CANCELLED,
            )
            result = await session.execute(stmt)
            count = result.scalar() or 0
            return count > 0

    @staticmethod
    async def bulk_update_status(rsvp_ids: List[int], status: RSVPStatus) -> int:
        """Bulk update status for multiple RSVPs"""
        async with db as session:
            stmt = (
                sql_update(RSVP)
                .where(RSVP.id.in_(rsvp_ids))
                .values(status=status, updated_at=datetime.now(timezone.utc))
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount

    @staticmethod
    async def get_rsvps_by_qr_code(qr_code: str) -> Optional[RSVP]:
        """Find RSVP by QR code"""
        async with db as session:
            stmt = select(RSVP).where(RSVP.qr_code == qr_code)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_event_check_in_summary(event_id: int) -> dict:
        """Get check-in summary for an event"""
        async with db as session:
            stmt = select(
                func.count(RSVP.id)
                .filter(RSVP.status == RSVPStatus.CONFIRMED)
                .label("pending_checkin"),
                func.count(RSVP.id)
                .filter(RSVP.status == RSVPStatus.ATTENDED)
                .label("checked_in"),
                func.count(RSVP.id)
                .filter(RSVP.status == RSVPStatus.NO_SHOW)
                .label("no_show"),
                func.count(RSVP.id).label("total_rsvps"),
            ).where(RSVP.event_id == event_id)

            result = await session.execute(stmt)
            row = result.first()

            if not row:
                return {
                    "pending_checkin": 0,
                    "checked_in": 0,
                    "no_show": 0,
                    "total_rsvps": 0,
                    "checkin_percentage": 0,
                }

            return {
                "pending_checkin": row.pending_checkin or 0,
                "checked_in": row.checked_in or 0,
                "no_show": row.no_show or 0,
                "total_rsvps": row.total_rsvps or 0,
                "checkin_percentage": (
                    (row.checked_in / row.total_rsvps * 100)
                    if row.total_rsvps and row.total_rsvps > 0
                    else 0
                ),
            }
