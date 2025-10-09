from typing import Optional
from backend.repository.feedback_repository import FeedbackRepository
from backend.repository.rsvp_repository import RSVPRepository
from backend.schemas.feedback_schema import FeedbackCreate
from backend.graphql_api.types import EventFeedbackSummaryType
from backend.database import get_db
from backend.exceptions import ValidationError

class FeedbackService:
    @staticmethod
    async def submit_feedback(feedback_data: FeedbackCreate, user_id: int) -> str:
        async with get_db() as db:
            # Verify user attended event
            rsvp_repo = RSVPRepository(db)
            rsvp = await rsvp_repo.get_rsvp(feedback_data.event_id, user_id)
            if not rsvp or not rsvp.attended:
                raise ValidationError("User must have attended the event to submit feedback")

            # Create feedback
            feedback_repo = FeedbackRepository(db)
            await feedback_repo.create(feedback_data, user_id)
            return "Feedback submitted successfully"

    @staticmethod
    async def get_event_feedback(event_id: int) -> EventFeedbackSummaryType:
        async with get_db() as db:
            feedback_repo = FeedbackRepository(db)
            
            # Get summary statistics
            stats = await feedback_repo.get_summary_stats(event_id)
            
            # Get recent comments (paginated, limit to 10)
            comments = await feedback_repo.get_by_event(event_id, limit=10)
            
            return EventFeedbackSummaryType(
                average_rating=stats['average_rating'],
                total_ratings=stats['total_ratings'],
                total_comments=stats['total_comments'],
                comments=comments
            )