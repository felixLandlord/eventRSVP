# from __future__ import annotations
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Integer, Float, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base_model import Base, TimestampMixin
from backend.schemas.ticket_schema import TicketType

if TYPE_CHECKING:
    from backend.models.event_model import Event
    from backend.models.rsvp_model import RSVP


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    quantity_total: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ticket_type: Mapped[TicketType] = mapped_column(
        Enum(TicketType, name="ticket_type"),
        default=TicketType.FREE,
        nullable=False,
    )
    sale_start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sale_end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="tickets")
    rsvps: Mapped[List["RSVP"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )
