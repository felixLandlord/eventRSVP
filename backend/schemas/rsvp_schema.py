from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class RSVPStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    ATTENDED = "attended"
    NO_SHOW = "no_show"


class RSVPBase(BaseModel):
    event_id: int
    user_id: int
    ticket_id: int
    status: RSVPStatus = RSVPStatus.PENDING
    qr_code: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    notes: Optional[str] = None


class RSVPCreate(RSVPBase):
    pass


class RSVPUpdate(BaseModel):
    status: Optional[RSVPStatus] = None
    qr_code: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    notes: Optional[str] = None


class RSVPRead(RSVPBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
