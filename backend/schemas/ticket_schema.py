from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class TicketType(str, Enum):
    FREE = "free"
    PAID = "paid"
    VIP = "vip"
    EARLY_BIRD = "early_bird"


class TicketBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = 0.0
    currency: str = "USD"
    quantity_total: int
    quantity_sold: int = 0
    ticket_type: TicketType = TicketType.FREE
    sale_start_date: Optional[datetime] = None
    sale_end_date: Optional[datetime] = None


class TicketCreate(TicketBase):
    event_id: int


class TicketUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    quantity_total: Optional[int] = None
    quantity_sold: Optional[int] = None
    ticket_type: Optional[TicketType] = None
    sale_start_date: Optional[datetime] = None
    sale_end_date: Optional[datetime] = None


class TicketRead(TicketBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
