from ..models import RawMessage, WhatsAppUser
from django.utils import timezone
from datetime import datetime

class RawMessageDAO:
    @staticmethod
    def create_raw_message(user: WhatsAppUser, message: str, incoming: bool) -> RawMessage:
        return RawMessage.objects.create(user=user, message=message, incoming=incoming)

    @staticmethod
    def count_messages_since(user: WhatsAppUser, since_datetime: datetime) -> int:
        """
        Count messages sent by a user since a given datetime
        
        Args:
            phone_number: The user's phone number
            since_datetime: Datetime to count messages from
            
        Returns:
            int: Number of messages sent since the given datetime
        """
        return RawMessage.objects.filter(
            user=user,
            incoming=True,
            created_at__gte=since_datetime
        ).count()

