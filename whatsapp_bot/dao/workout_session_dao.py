from typing import Optional
from django.utils import timezone
from datetime import timedelta
from ..models import WorkoutSession, WhatsAppUser, RawMessage

class WorkoutSessionDAO:

    @staticmethod
    def get_active_session(user: WhatsAppUser) -> Optional[WorkoutSession]:
        six_hours_ago = timezone.now() - timedelta(hours=6)
        return WorkoutSession.objects.filter(
            user=user,
            created_at__gte=six_hours_ago
        ).order_by('-created_at').first()

    @staticmethod
    def create_session(user: WhatsAppUser, activity_type: str = None, duration_minutes: int = None) -> WorkoutSession:
        return WorkoutSession.objects.create(
            user=user,
            activity_type=activity_type,
            duration_minutes=duration_minutes
        )

    @staticmethod
    def add_raw_message(session: WorkoutSession, raw_message: RawMessage) -> None:
        session.raw_messages.add(raw_message)