from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.sql import select, update as sql_update, delete as sql_delete, func
from backend.schemas.event_schema import (
    EventCreate,
    EventUpdate,
    EventStatus,
    EventCategory,
)
from backend.schemas.rsvp_schema import RSVPStatus
from backend.core.database import db
from backend.models.event_model import Event
from backend.models.rsvp_model import RSVP


class EventRepository:

    @staticmethod
    async def create(event_data: EventCreate) -> Event:
        async with db as session:
            event = Event(**event_data.model_dump())
            session.add(event)
            await db.commit_rollback()
            await session.refresh(event)
            return event

    @staticmethod
    async def get_by_id(event_id: int) -> Optional[Event]:
        async with db as session:
            stmt = select(Event).where(Event.id == event_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_all(
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
        status: EventStatus = EventStatus.PUBLISHED,
    ) -> List[Event]:
        async with db as session:
            stmt = select(Event).where(Event.status == status, ~Event.is_deleted)

            # Filter by category
            if category:
                try:
                    category_enum = EventCategory(category.lower())
                    stmt = stmt.where(Event.category == category_enum)
                except ValueError:
                    pass  # Ignore invalid category

            # Search filter
            if search:
                search_term = f"%{search.lower()}%"
                stmt = stmt.where(
                    Event.title.ilike(search_term)
                    | Event.description.ilike(search_term)
                    | Event.location.ilike(search_term)
                )

            stmt = stmt.order_by(Event.start_date.asc()).offset(skip).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_by_organizer(organizer_id: int) -> List[Event]:
        async with db as session:
            stmt = (
                select(Event)
                .where(Event.organizer_id == organizer_id)
                .order_by(Event.created_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def update(event_id: int, event_data: EventUpdate) -> Optional[Event]:
        async with db as session:
            stmt = select(Event).where(Event.id == event_id)
            result = await session.execute(stmt)
            event = result.scalars().first()

            if not event:
                return None

            for field, value in event_data.model_dump(exclude_unset=True).items():
                if hasattr(event, field) and value is not None:
                    setattr(event, field, value)

            event.updated_at = datetime.now(timezone.utc)
            await db.commit_rollback()
            await session.refresh(event)
            return event

    @staticmethod
    async def delete(event_id: int) -> bool:
        async with db as session:
            stmt = sql_delete(Event).where(Event.id == event_id)
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def update_status(event_id: int, status: EventStatus) -> bool:
        async with db as session:
            stmt = (
                sql_update(Event)
                .where(Event.id == event_id)
                .values(status=status, updated_at=datetime.now(timezone.utc))
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def update_cover_image(event_id: int, image_url: str) -> bool:
        async with db as session:
            stmt = (
                sql_update(Event)
                .where(Event.id == event_id)
                .values(cover_image=image_url, updated_at=datetime.now(timezone.utc))
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def get_attendee_count(event_id: int) -> int:
        async with db as session:
            stmt = select(func.count(RSVP.id)).where(
                RSVP.event_id == event_id,
                RSVP.status.in_([RSVPStatus.CONFIRMED, RSVPStatus.ATTENDED]),
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    @staticmethod
    async def get_upcoming_events(limit: int = 10) -> List[Event]:
        async with db as session:
            stmt = (
                select(Event)
                .where(
                    Event.start_date > datetime.now(timezone.utc),
                    Event.status == EventStatus.PUBLISHED,
                )
                .order_by(Event.start_date.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_events_by_date_range(
        start_date: datetime, end_date: datetime
    ) -> List[Event]:
        async with db as session:
            stmt = (
                select(Event)
                .where(
                    Event.start_date >= start_date,
                    Event.start_date <= end_date,
                    Event.status == EventStatus.PUBLISHED,
                )
                .order_by(Event.start_date.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_popular_events(limit: int = 10) -> List[Event]:
        async with db as session:
            stmt = (
                select(Event, func.count(RSVP.id).label("rsvp_count"))
                .join(RSVP, Event.id == RSVP.event_id, isouter=True)
                .where(
                    Event.status == EventStatus.PUBLISHED,
                    Event.start_date > datetime.now(timezone.utc),
                )
                .group_by(Event.id)
                .order_by(func.count(RSVP.id).desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]

    @staticmethod
    async def search_events(query: str, limit: int = 20) -> List[Event]:
        async with db as session:
            search_term = f"%{query.lower()}%"
            stmt = (
                select(Event)
                .where(
                    Event.status == EventStatus.PUBLISHED,
                    Event.title.ilike(search_term)
                    | Event.description.ilike(search_term)
                    | Event.location.ilike(search_term),
                )
                .order_by(Event.start_date.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
