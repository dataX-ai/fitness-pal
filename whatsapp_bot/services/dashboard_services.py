from ..dao.user_dao import UserDAO
from ..dao.exercise_dao import WorkoutSessionDAO
from ..dao.dashboard_dao import DashboardDAO
from django.utils import timezone
from ..services import logger_service
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any

logger = logger_service.get_logger()

def _fetch_dashboard_details(user_id) -> Optional[Dict[str, Any]]:
    """Helper function to fetch dashboard details"""
    try:
        dashboard_details = DashboardDAO.get_user_dashboard_data(user_id)
        if not dashboard_details:
            return None
            
        return {
            'fitness_score': dashboard_details.fitness_score,
            'fitness_score_change': dashboard_details.fitness_score_change,
            'initial_weight': dashboard_details.initial_weight,
            'current_weight': dashboard_details.current_weight,
            'goal_weight': dashboard_details.goal_weight,
            'all_time_duration': dashboard_details.all_time_duration,
            'last_week_duration': dashboard_details.last_week_duration,
            'avg_week_duration': dashboard_details.avg_week_duration,
            'achievements': dashboard_details.achievements
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard details: {str(e)}")
        return None

def _streak_stats(user) -> Optional[Dict[str, Any]]:
    """Helper function to fetch workout statistics"""
    try:
        streak_details = WorkoutSessionDAO.get_current_week_streak(user)
        return streak_details
    except Exception as e:
        logger.error(f"Error fetching streak stats: {str(e)}")
        return None

def get_dashboard_user_data(user_id):
    """
    Get formatted dashboard data for a user using parallel processing
    """
    try:
        user = UserDAO.get_user_by_id(user_id)
        if not user:
            return None

        # Use ThreadPoolExecutor to run the fetches in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            dashboard_future = executor.submit(_fetch_dashboard_details, user_id)
            streak_future = executor.submit(_streak_stats, user)

            # Wait for both tasks to complete
            dashboard_details = dashboard_future.result()
            streak_details = streak_future.result()

            if not dashboard_details:
                return None

            # Calculate statistics
            total_hours = dashboard_details['all_time_duration'] / 60 if dashboard_details['all_time_duration'] else 0
            last_week_hours = dashboard_details['last_week_duration'] / 60 if dashboard_details['last_week_duration'] else 0
            avg_week_hours = dashboard_details['avg_week_duration'] / 60 if dashboard_details['avg_week_duration'] else 0

            dashboard_data = {
                'name': user.name if user.name else "John Doe",
                'avatar': '👤',  # TODO: Implement avatar storage and retrieval
                'stats': {
                    'totalHours': round(total_hours, 1),
                    'weeklyAverage': round(avg_week_hours, 1),
                    'lastWeekHours': round(last_week_hours, 1),
                    'fitnessScore': dashboard_details['fitness_score'],
                    'fitnessScoreImprovement': dashboard_details['fitness_score_change'],
                    'weightLossProgress': {
                        'initial': dashboard_details['initial_weight'],
                        'current': dashboard_details['current_weight'],
                        'goal': dashboard_details['goal_weight'],
                        'unit': "kg",
                    },
                },
                'achievements': dashboard_details['achievements'],
                'streak': streak_details
            }
            return dashboard_data
    except Exception as e:
        logger.error(f"Error in get_dashboard_user_data: {str(e)}")
        return None
