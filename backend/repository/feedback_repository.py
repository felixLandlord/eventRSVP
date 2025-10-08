from typing import List, Dict, Optional
from sqlalchemy import func
from backend.models.feedback_model import FeedbackModel
from backend.schemas.feedback_schema import FeedbackCreate
from backend.database import get_db


class FeedbackRepository:
    @staticmethod
    async def create(feedback_data: FeedbackCreate) -> FeedbackModel:
        db = next(get_db())
        db_feedback = FeedbackModel(**feedback_data.dict())
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return db_feedback

    @staticmethod
    async def get_by_event(event_id: int) -> List[FeedbackModel]:
        db = next(get_db())
        return db.query(FeedbackModel).filter(FeedbackModel.event_id == event_id).all()

    @staticmethod
    async def get_by_user_and_event(user_id: int, event_id: int) -> Optional[FeedbackModel]:
        db = next(get_db())
        return db.query(FeedbackModel).filter(
            FeedbackModel.user_id == user_id,
            FeedbackModel.event_id == event_id
        ).first()

    @staticmethod
    async def get_event_feedback_metrics(event_id: int) -> Dict:
        db = next(get_db())
        result = db.query(
            func.avg(FeedbackModel.rating).label('average_rating'),
            func.count(FeedbackModel.id).label('total_feedback_count')
        ).filter(FeedbackModel.event_id == event_id).first()

        return {
            'average_rating': float(result.average_rating or 0),
            'total_feedback_count': result.total_feedback_count or 0
        }