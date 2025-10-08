from typing import List
from datetime import datetime
from backend.repository.feedback_repository import FeedbackRepository
from backend.repository.event_repository import EventRepository
from backend.repository.rsvp_repository import RSVPRepository
from backend.schemas.feedback_schema import FeedbackCreate
from backend.graphql_api.types import FeedbackType, FeedbackInput
from backend.schemas.rsvp_schema import RSVPStatus


class FeedbackService:
    @staticmethod
    async def submit_feedback(event_id: int, feedback_data: FeedbackInput, user_id: int) -> FeedbackType:
        # Get event to check if it has ended
        event = await EventRepository.get_by_id(event_id)
        if not event:
            raise ValueError("Event not found")

        if event.end_date > datetime.now():
            raise ValueError("Cannot submit feedback before event ends")

        # Check if user attended the event
        rsvp = await RSVPRepository.get_by_user_and_event(user_id, event_id)
        if not rsvp or rsvp.status != RSVPStatus.CHECKED_IN:
            raise ValueError("Only checked-in attendees can submit feedback")

        # Check if user already submitted feedback
        existing_feedback = await FeedbackRepository.get_by_user_and_event(user_id, event_id)
        if existing_feedback:
            raise ValueError("You have already submitted feedback for this event")

        # Create feedback
        feedback_create = FeedbackCreate(
            event_id=event_id,
            user_id=user_id,
            rating=feedback_data.rating,
            comment=feedback_data.comment
        )
        feedback = await FeedbackRepository.create(feedback_create)

        return FeedbackType(
            id=feedback.id,
            event_id=feedback.event_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            comment=feedback.comment,
            created_at=feedback.created_at
        )

    @staticmethod
    async def get_event_feedback(event_id: int) -> List[FeedbackType]:
        feedbacks = await FeedbackRepository.get_by_event(event_id)
        return [
            FeedbackType(
                id=feedback.id,
                event_id=feedback.event_id,
                user_id=feedback.user_id,
                rating=feedback.rating,
                comment=feedback.comment,
                created_at=feedback.created_at
            )
            for feedback in feedbacks
        ]