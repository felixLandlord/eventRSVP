import strawberry
from typing import List, Optional
from datetime import datetime
from backend.models.event_model import EventStatus, EventCategory
from backend.schemas.ticket_schema import TicketType as TicketTypeEnum
from backend.schemas.rsvp_schema import RSVPStatus
from backend.schemas.user_schema import UserRole


@strawberry.type
class UserType:
    id: int
    name: str
    email: str
    role: UserRole
    avatar: Optional[str] = None
    created_at: datetime


@strawberry.type
class EventType:
    id: int
    title: str
    description: str
    category: EventCategory
    location: str
    venue_address: Optional[str]
    start_date: datetime
    end_date: datetime
    timezone: str
    max_attendees: Optional[int]
    is_free: bool
    cover_image: Optional[str]
    status: EventStatus
    organizer_id: int
    created_at: datetime
    attendee_count: Optional[int] = 0


@strawberry.type
class TicketType:
    id: int
    name: str
    description: Optional[str]
    price: float
    currency: str
    quantity_total: int
    quantity_sold: int
    ticket_type: TicketTypeEnum
    event_id: int


@strawberry.type
class RSVPType:
    id: int
    event_id: int
    user_id: int
    ticket_id: int
    status: RSVPStatus
    qr_code: Optional[str]
    checked_in_at: Optional[datetime]
    created_at: datetime


@strawberry.type
class AuthType:
    user: UserType
    access_token: str
    refresh_token: str


@strawberry.type
class EventAnalyticsType:
    total_events: int
    total_attendees: int
    revenue: float
    popular_categories: List[str]


@strawberry.type
class EventCheckInSummaryType:
    pending_checkin: int
    checked_in: int
    no_show: int
    total_rsvps: int
    checkin_percentage: float


# Input Types
@strawberry.input
class RegisterInput:
    name: str
    email: str
    password: str


@strawberry.input
class LoginInput:
    email: str
    password: str


@strawberry.input
class EventInput:
    title: str
    description: str
    category: EventCategory
    location: str
    venue_address: Optional[str] = None
    start_date: datetime
    end_date: datetime
    timezone: str = "UTC"
    max_attendees: Optional[int] = None
    is_free: bool = True

    @strawberry.field
    def validate_dates(self) -> None:
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")


@strawberry.input
class TicketInput:
    name: str
    description: Optional[str] = None
    price: float = 0.0
    currency: str = "USD"
    quantity_total: int
    ticket_type: TicketTypeEnum = TicketTypeEnum.FREE


@strawberry.input
class RSVPInput:
    event_id: int
    ticket_id: int


@strawberry.input
class VerifyEmailInput:
    email: str
    otp: str


@strawberry.input
class ForgotPasswordInput:
    email: str


@strawberry.input
class ResetPasswordInput:
    email: str
    otp: str
    new_password: str


@strawberry.input
class ChangePasswordInput:
    current_password: str
    new_password: str


@strawberry.input
class ResendOTPInput:
    email: str


# @strawberry.type
# class MessageResponse:
#     message: str
#     success: bool
