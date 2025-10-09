from pydantic import BaseModel, validator, constr
from typing import Optional

class FeedbackCreate(BaseModel):
    event_id: int
    rating: int
    comment: Optional[str] = None

    @validator('rating')
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

    @validator('comment')
    def validate_comment(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError('Comment must be less than 1000 characters')
            if len(v.strip()) == 0:
                return None
        return v

    class Config:
        orm_mode = True