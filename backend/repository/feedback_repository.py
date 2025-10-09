from typing import List, Optional, Dict
from sqlalchemy import func
from backend.models.feedback import Feedback
from backend.database import AsyncSession
from backend.schemas.feedback_schema import FeedbackCreate

class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, feedback_data: FeedbackCreate, user_id: int) -> Feedback:
        feedback = Feedback(
            event_id=feedback_data.event_id,
            user_id=user_id,
            rating=feedback_data.rating,
            comment=feedback_data.comment
        )
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback

    async def get_by_event(self, event_id: int, limit: int = 10, offset: int = 0) -> List[Feedback]:
        query = self.db.query(Feedback)\
            .filter(Feedback.event_id == event_id)\
            .order_by(Feedback.created_at.desc())\
            .limit(limit)\
            .offset(offset)
        result = await query.all()
        return result

    async def get_summary_stats(self, event_id: int) -> Dict:
        query = self.db.query(
            func.avg(Feedback.rating).label('average_rating'),
            func.count(Feedback.id).label('total_ratings'),
            func.count(Feedback.comment).label('total_comments')
        ).filter(Feedback.event_id == event_id)
        
        result = await query.first()
        return {
            'average_rating': float(result.average_rating) if result.average_rating else 0.0,
            'total_ratings': result.total_ratings,
            'total_comments': result.total_comments
        }