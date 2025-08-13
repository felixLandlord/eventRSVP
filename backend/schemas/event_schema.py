from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EventCategory(str, Enum):
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    MEETUP = "meetup"
    WEBINAR = "webinar"
    NETWORKING = "networking"
    SOCIAL = "social"
    SPORTS = "sports"
    OTHER = "other"


class EventBase(BaseModel):
    title: str
    description: str
    category: EventCategory = EventCategory.OTHER
    location: str
    venue_address: Optional[str] = None
    start_date: datetime
    end_date: datetime
    timezone: str = "UTC"
    max_attendees: Optional[int] = None
    is_free: bool = True
    cover_image: Optional[str] = None
    status: EventStatus = EventStatus.DRAFT


class EventCreate(EventBase):
    organizer_id: int


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[EventCategory] = None
    location: Optional[str] = None
    venue_address: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: Optional[str] = None
    max_attendees: Optional[int] = None
    is_free: Optional[bool] = None
    cover_image: Optional[str] = None
    status: Optional[EventStatus] = None


class EventRead(EventBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
