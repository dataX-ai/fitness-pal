from typing import Optional
from django.db.models import Q
from ..models import BodyHistory, WhatsAppUser

class BodyHistoryDAO:
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Lightly Active (1-3 days/week)'),
        ('moderate', 'Moderately Active (3-5 days/week)'),
        ('very', 'Very Active (6-7 days/week)'),
        ('extra', 'Extra Active (very active & physical job)'),
    ]

    BODY_COMPOSITION_CHOICES = [
        ('calorie_deficit', 'Calorie Deficit'),
        ('calorie_maintenance', 'Calorie Maintenance'),
        ('calorie_surplus', 'Calorie Surplus'),
    ]

    GOAL_CHOICES = [
        ('lean', 'Lean'),
        ('athletic', 'Athletic'),
        ('bulk', 'Bulk'),
    ]

    @staticmethod
    def get_latest_entry(user: WhatsAppUser) -> Optional[BodyHistory]:
        """Get user's most recent body history entry"""
        return BodyHistory.objects.filter(user=user).order_by('-created_at').first()

    @staticmethod
    def create_entry(user: WhatsAppUser, **kwargs) -> BodyHistory:
        """Create a new body history entry, copying values from the latest entry"""
        latest = BodyHistoryDAO.get_latest_entry(user)
        
        # If there's a latest entry, copy its values
        if latest:
            new_data = {
                'height': latest.height,
                'weight': latest.weight,
                'activity': latest.activity,
                'body_fat': latest.body_fat,
                'bmi': latest.bmi,
                'maintenance_calories': latest.maintenance_calories,
                'body_composition': latest.body_composition,
                'goal': latest.goal
            }
            # Update with any new values passed in
            new_data.update(kwargs)
            return BodyHistory.objects.create(user=user, **new_data)
        
        # If no previous entry, just create with provided kwargs
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