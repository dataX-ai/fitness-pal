from typing import Optional
from django.db.models import Q
from ..models import BodyHistory, WhatsAppUser

class BodyHistoryDAO:
    @staticmethod
    def get_latest_entry(user: WhatsAppUser) -> Optional[BodyHistory]:
        """Get user's most recent body history entry"""
        return BodyHistory.objects.filter(user=user).order_by('-created_at').first()

    @staticmethod
    def create_entry(user: WhatsAppUser, **kwargs) -> BodyHistory:
        """Create a new body history entry"""
        return BodyHistory.objects.create(user=user, **kwargs)

    @staticmethod
    def has_activity(user: WhatsAppUser) -> bool:
        """Check if user has activity level set"""
        latest = BodyHistoryDAO.get_latest_entry(user)
        return bool(latest and latest.activity)

    @staticmethod
    def has_measurements(user: WhatsAppUser) -> bool:
        """Check if user has height and weight set"""
        latest = BodyHistoryDAO.get_latest_entry(user)
        return bool(latest and latest.height and latest.weight)

    @staticmethod
    def get_latest_metrics(user: WhatsAppUser) -> dict:
        """Get user's latest metrics as a dictionary"""
        latest = BodyHistoryDAO.get_latest_entry(user)
        if not latest:
            return {}
        
        return {
            'height': latest.height,
            'weight': latest.weight,
            'activity': latest.activity,
            'body_fat': latest.body_fat,
            'bmi': latest.bmi,
            'maintenance_calories': latest.maintenance_calories,
            'body_composition': latest.body_composition
        } 