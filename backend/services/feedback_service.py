from datetime import datetime
from typing import Optional, List
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from models.feedback_model import FeedbackModel
from models.event_model import EventModel
from models.rsvp_model import RSVPModel
from graphql_api.types import FeedbackType, EventFeedbackSummaryType, FeedbackInput
from exceptions import ValidationError, PermissionError

class FeedbackService:
    def __init__(self, db_session):
        self.db_session = db_session

    async def submit_feedback(self, feedback_data: FeedbackInput, user_id: int) -> FeedbackType:
        """
        Submit feedback for an event.
        Validates eligibility and prevents duplicate submissions.
        """
        # Validate feedback eligibility
        if not await self.validate_feedback_eligibility(feedback_data.event_id, user_id):
            raise PermissionError("User is not eligible to submit feedback for this event")

        # Validate rating range
        if not 1 <= feedback_data.rating <= 5:
            raise ValidationError("Rating must be between 1 and 5")

        try:
            feedback = FeedbackModel(
                event_id=feedback_data.event_id,
                user_id=user_id,
                rating=feedback_data.rating,
                comment=feedback_data.comment
            )
            self.db_session.add(feedback)
            await self.db_session.commit()
            await self.db_session.refresh(feedback)
            
            return FeedbackType(
                id=feedback.id,
                event_id=feedback.event_id,
                user_id=feedback.user_id,
                rating=feedback.rating,
                comment=feedback.comment,
                created_at=feedback.created_at
            )
        except IntegrityError:
            await self.db_session.rollback()
            raise ValidationError("Feedback has already been submitted for this event")

    async def get_event_feedback(self, event_id: int) -> EventFeedbackSummaryType:
        """
        Retrieve feedback summary and details for an event.
        """
        # Calculate average rating and count
        feedback_stats = await self.db_session.query(
            func.avg(FeedbackModel.rating).label('average_rating'),
            func.count(FeedbackModel.id).label('feedback_count')
        ).filter(FeedbackModel.event_id == event_id).first()

        # Get all feedback comments
        feedbacks = await self.db_session.query(FeedbackModel).filter(
            FeedbackModel.event_id == event_id
        ).order_by(FeedbackModel.created_at.desc()).all()

        feedback_list = [
            FeedbackType(
                id=f.id,
                event_id=f.event_id,
                user_id=f.user_id,
                rating=f.rating,
                comment=f.comment,
                created_at=f.created_at
            ) for f in feedbacks
        ]

        return EventFeedbackSummaryType(
            average_rating=float(feedback_stats.average_rating or 0),
            feedback_count=feedback_stats.feedback_count,
            comments=feedback_list
        )

    async def validate_feedback_eligibility(self, event_id: int, user_id: int) -> bool:
        """
        Validate if a user is eligible to submit feedback for an event.
        Checks if:
        1. User has a valid RSVP for the event
        2. Event has ended
        """
        # Check if event exists and has ended
        event = await self.db_session.query(EventModel).filter(
            EventModel.id == event_id
        ).first()
        
        if not event:
            raise ValidationError("Event not found")
            
        if event.end_date > datetime.utcnow():
            raise ValidationError("Cannot submit feedback before event has ended")

        # Check if user has valid RSVP
        rsvp = await self.db_session.query(RSVPModel).filter(
            RSVPModel.event_id == event_id,
            RSVPModel.user_id == user_id,
            RSVPModel.status == 'confirmed'
        ).first()

        if not rsvp:
            return False

        return True