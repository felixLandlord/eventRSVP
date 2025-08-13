# from __future__ import annotations
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base_model import Base, TimestampMixin


from backend.schemas.event_schema import EventCategory, EventStatus

if TYPE_CHECKING:
    from backend.models.rsvp_model import RSVP
    from backend.models.ticket_model import Ticket


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[EventCategory] = mapped_column(
        Enum(EventCategory, name="event_category"),
        default=EventCategory.OTHER,
        nullable=False,
    )
    location: Mapped[str] = mapped_column(String, nullable=False)
    venue_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String, default="UTC", nullable=False)
    max_attendees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    cover_image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status"),
        default=EventStatus.DRAFT,
        nullable=False,
    )
    organizer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    tickets: Mapped[List["Ticket"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    rsvps: Mapped[List["RSVP"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
