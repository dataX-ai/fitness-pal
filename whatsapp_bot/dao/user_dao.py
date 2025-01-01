from typing import Optional, List, Tuple
from django.db.models import Q
from ..models import WhatsAppUser, BodyHistory

class UserDAO:
    @staticmethod
    def get_or_create_user(phone_number: str) -> Tuple[WhatsAppUser, bool]:
        """Get or create a WhatsAppUser"""
        user, created = WhatsAppUser.objects.get_or_create(
            phone_number=phone_number
        )
        return user, created

    @staticmethod
    def get_user_by_phone(phone_number: str) -> Optional[WhatsAppUser]:
        """Get user by phone number"""
        try:
            return WhatsAppUser.objects.get(phone_number=phone_number)
        except WhatsAppUser.DoesNotExist:
            return None

    @staticmethod
    def update_user_details(phone_number: str, **kwargs) -> Optional[WhatsAppUser]:
        """
        Update user details
        Args:
            phone_number: User's phone number
            **kwargs: Fields to update (name, height, weight, etc.)
        """
        try:
            user = WhatsAppUser.objects.get(phone_number=phone_number)
            for key, value in kwargs.items():
                setattr(user, key, value)
            user.save()
            return user
        except WhatsAppUser.DoesNotExist:
            return None

    @staticmethod
    def create_body_history(user: WhatsAppUser, **kwargs) -> BodyHistory:
        """
        Create a new body history entry
        Args:
            user: WhatsAppUser instance
            **kwargs: Body metrics (height, weight, body_fat, etc.)
        """
        return BodyHistory.objects.create(user=user, **kwargs)

    @staticmethod
    def get_latest_body_history(user: WhatsAppUser) -> Optional[BodyHistory]:
        """Get user's most recent body history entry"""
        return BodyHistory.objects.filter(user=user).order_by('-created_at').first()

    @staticmethod
    def get_body_history(user: WhatsAppUser, limit: int = 10) -> List[BodyHistory]:
        """
        Get user's body history
        Args:
            user: WhatsAppUser instance
            limit: Number of entries to return
        """
        return list(BodyHistory.objects.filter(user=user).order_by('-created_at')[:limit])

    @staticmethod
    def search_users(query: str) -> List[WhatsAppUser]:
        """
        Search users by name or phone number
        Args:
            query: Search term
        """
        return list(WhatsAppUser.objects.filter(
            Q(name__icontains=query) | Q(phone_number__icontains=query)
        ))

    @staticmethod
    def delete_user(phone_number: str) -> bool:
        """
        Delete user by phone number
        Returns: True if user was deleted, False if not found
        """
        try:
            user = WhatsAppUser.objects.get(phone_number=phone_number)
            user.delete()
            return True
        except WhatsAppUser.DoesNotExist:
            return False

    @staticmethod
    def get_all_users(limit: int = 100, offset: int = 0) -> List[WhatsAppUser]:
        """
        Get all users with pagination
        Args:
            limit: Number of users to return
            offset: Number of users to skip
        """
        return list(WhatsAppUser.objects.all().order_by('-created_at')[offset:offset + limit])

    @staticmethod
    def get_active_users(days: int = 30) -> List[WhatsAppUser]:
        """
        Get users active within the last X days
        Args:
            days: Number of days to look back
        """
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return list(WhatsAppUser.objects.filter(last_interaction__gte=cutoff))

    @staticmethod
    def has_name(phone_number: str) -> bool:
        """Check if user has a name set"""
        try:
            user = WhatsAppUser.objects.get(phone_number=phone_number)
            return bool(user.name)
        except WhatsAppUser.DoesNotExist:
            return False

    @staticmethod
    def update_paid_status(user: WhatsAppUser, paid: bool = True) -> WhatsAppUser:
        """Update user's paid status"""
        user.paid = paid
        user.save()
        return user
