from django.utils import timezone
from datetime import datetime
import pytz
from ..models import WhatsAppUser
from ..dao.raw_message_dao import RawMessageDAO
from ..utils.config import MAX_FREE_MESSAGES_PER_DAY

class SubscriptionCheck:
    IST_TIMEZONE = pytz.timezone('Asia/Kolkata')

    @staticmethod
    def can_send_message(user: WhatsAppUser) -> bool:
        """
        Check if a user can send more messages based on their subscription status
        and daily message limit.
        Args:
            user: The WhatsAppUser object
        Returns:
            bool: True if user can send more messages, False otherwise
        """
        # Paid users have no restrictions
        if user.paid:
            return True
        # For non-paid users, check message count for current day in IST
        ist_now = timezone.now().astimezone(SubscriptionCheck.IST_TIMEZONE)
        start_of_day = ist_now.replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = RawMessageDAO.count_messages_since(user, start_of_day)
        
        return messages_today < MAX_FREE_MESSAGES_PER_DAY

    @staticmethod
    def get_remaining_messages(user: WhatsAppUser) -> int:
        """
        Get the number of remaining messages a user can send today.
        Args:
            user: The WhatsAppUser object
        Returns:
            int: Number of remaining messages. -1 for paid users (unlimited)
        """
        if user.paid:
            return -1  # Unlimited messages
        ist_now = timezone.now().astimezone(SubscriptionCheck.IST_TIMEZONE)
        start_of_day = ist_now.replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = RawMessageDAO.count_messages_since(user, start_of_day)
        return max(0, MAX_FREE_MESSAGES_PER_DAY - messages_today)
