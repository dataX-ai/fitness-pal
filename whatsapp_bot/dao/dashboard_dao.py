from django.db.models import Q
from datetime import datetime, timedelta
from ..models import WhatsAppUser, DashboardDetails
from ..dao.user_dao import UserDAO
from django.db import transaction
from ..services.logger_service import get_logger

logger = get_logger(__name__)

class DashboardDAO:
    @staticmethod
    def get_user_dashboard_data(user_id) -> DashboardDetails:
        """
        Fetch all necessary data for the user dashboard from the database
        """
        try:
            # Get user
            user = UserDAO.get_user_by_id(user_id);
            dashboard_details = DashboardDetails.objects.get(user=user)
            return dashboard_details
        except WhatsAppUser.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {str(e)}")
            return None

    @staticmethod
    def bulk_update_dashboard_details(records_to_update):
        """
        Bulk update existing dashboard details records
        Args:
            records_to_update: List of DashboardDetails objects to update
        """
        try:
            if records_to_update:
                DashboardDetails.objects.bulk_update(
                    records_to_update,
                    fields=['all_time_duration', 'last_week_duration', 'avg_week_duration',
                           'initial_weight', 'current_weight', 'goal_weight']
                )
                logger.info(f"Bulk updated {len(records_to_update)} dashboard records")
        except Exception as e:
            logger.error(f"Error in bulk updating dashboard details: {str(e)}")
            raise

    @staticmethod
    def bulk_create_dashboard_details(records_to_create):
        """
        Bulk create new dashboard details records
        Args:
            records_to_create: List of DashboardDetails objects to create
        """
        try:
            if records_to_create:
                DashboardDetails.objects.bulk_create(records_to_create)
                logger.info(f"Bulk created {len(records_to_create)} dashboard records")
        except Exception as e:
            logger.error(f"Error in bulk creating dashboard details: {str(e)}")
            raise