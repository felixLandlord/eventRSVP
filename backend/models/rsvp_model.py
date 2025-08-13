from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base_model import Base, TimestampMixin


from backend.schemas.rsvp_schema import RSVPStatus


if TYPE_CHECKING:
    from backend.models.event_model import Event
    from backend.models.ticket_model import Ticket


class RSVP(Base, TimestampMixin):
    __tablename__ = "rsvps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[RSVPStatus] = mapped_column(
        Enum(RSVPStatus, name="rsvp_status"),
        default=RSVPStatus.PENDING,
        nullable=False,
    )
    qr_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="rsvps")
    ticket: Mapped["Ticket"] = relationship(back_populates="rsvps")
