from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class FeedbackBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    event_id: int
    user_id: int


class FeedbackRead(FeedbackBase):
    id: int
    event_id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class FeedbackUpdate(FeedbackBase):
    @validator('rating')
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v