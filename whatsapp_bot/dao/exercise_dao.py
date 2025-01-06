from django.db import transaction
from django.db.models import QuerySet, Sum, Case, When, IntegerField, Count
from django.utils import timezone
from datetime import timedelta
from ..models import Exercise, WorkoutSession, RawMessage, WhatsAppUser
from ..services.logger_service import get_logger
from typing import List, Dict, Optional
import pandas as pd
from django.db.models.functions import TruncDate, ExtractWeekDay

logger = get_logger(__name__)

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

    @staticmethod
    def get_user_workouts(user: WhatsAppUser, limit: int = None) -> List[WorkoutSession]:
        """Get all workouts for a user"""
        query = WorkoutSession.objects.filter(user=user).order_by('-created_at')
        if limit:
            query = query[:limit]
        return list(query)

    @staticmethod
    def get_total_workout_duration(user: WhatsAppUser) -> int:
        """Get total workout duration in minutes"""
        result = WorkoutSession.objects.filter(
            user=user,
            duration_minutes__isnull=False
        ).aggregate(total=Sum('duration_minutes'))
        return result['total'] or 0

    @staticmethod
    def get_weekly_workout_stats(user: WhatsAppUser) -> dict:
        """Get workout statistics for the last week"""
        week_ago = timezone.now() - timedelta(days=7)
        workouts = WorkoutSession.objects.filter(
            user=user,
            created_at__gte=week_ago,
            duration_minutes__isnull=False
        )
        total_minutes = workouts.aggregate(total=Sum('duration_minutes'))['total'] or 0
        return {
            'total_minutes': total_minutes,
            'total_workouts': workouts.count()
        }

    @staticmethod
    def get_average_weekly_duration(user: WhatsAppUser, weeks: int = 4) -> float:
        """Calculate average weekly workout duration over the specified number of weeks"""
        start_date = timezone.now() - timedelta(weeks=weeks)
        total_minutes = WorkoutSession.objects.filter(
            user=user,
            created_at__gte=start_date,
            duration_minutes__isnull=False
        ).aggregate(total=Sum('duration_minutes'))['total'] or 0
        
        return total_minutes / weeks if total_minutes > 0 else 0

    @staticmethod
    def get_user_workout_stats(users: List[WhatsAppUser] = None) -> pd.DataFrame:
        """
        Get comprehensive workout duration statistics for users
        Args:
            users: List of WhatsAppUser instances. If None or empty, stats for all users will be returned
        Returns:
            DataFrame with columns: 
            - user_id: User identifier
            - all_time_duration: Total workout duration in minutes
            - last_week_duration: Workout duration in the last 7 days
            - distinct_workout_days: Number of unique days with workouts
        """

        week_ago = timezone.now() - timedelta(days=7)
        
        # Base query
        base_query = WorkoutSession.objects.filter(duration_minutes__isnull=False)
        
        # Add user filter only if specific users are requested
        if users:
            base_query = base_query.filter(user__in=users)
        
        # Get both all-time and weekly stats in a single query per user
        stats = base_query.values('user_id').annotate(
            all_time_duration=Sum('duration_minutes'),
            last_week_duration=Sum(
                Case(
                    When(created_at__gte=week_ago, then='duration_minutes'),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            # Count distinct dates for all time
            distinct_workout_days=Count(
                TruncDate('created_at'),
                distinct=True
            )
        )
        logger.info(f"Stats: {stats}")
        # Convert queryset to DataFrame
        return pd.DataFrame.from_records(stats)

    @staticmethod
    def mark_messages_as_processed(session: WorkoutSession, raw_messages: QuerySet[RawMessage], session_time: int, calories_burnt: int) -> None:
        """
        Update the processed_messages and duration for a workout session
        Args:
            session: WorkoutSession instance
            raw_messages: QuerySet of RawMessage instances that were processed
            session_time: Duration of the session in minutes
            calories_burnt: Calories burnt during the session
        """
        try:
            session.processed_messages.set(raw_messages)
            session.duration_minutes = session_time
            session.calories_burnt = calories_burnt
            session.save()
            logger.info(f"Updated processed messages and duration for session {session.id}")
        except Exception as e:
            logger.error(f"Failed to update processed messages for session {session.id}: {str(e)}")
            raise

    @staticmethod
    def get_current_week_streak(user: WhatsAppUser) -> Optional[Dict[str, any]]:
        """
        Get workout streak details for the current calendar week (Monday to Sunday)
        Returns a dictionary containing:
        - days: List of day statuses with completion and dates
        - total_sessions: Total number of workout sessions this week
        - streak_days: Number of days with at least one workout this week
        """
        
        # Get the current date
        today = timezone.now().date()
        
        # Calculate the start (Monday) and end (Sunday) of the current week
        monday = today - timezone.timedelta(days=today.weekday())
        
        # Query workouts for the current week and group by day
        weekly_workouts = (
            WorkoutSession.objects
            .filter(
                user=user,
                created_at__date__gte=monday,
                created_at__date__lte=monday + timezone.timedelta(days=6),
                duration_minutes__isnull=False
            )
            .annotate(
                weekday=ExtractWeekDay('created_at')
            )
            .values('weekday')
            .annotate(
                session_count=Count('id')
            )
        )

        # Convert to a set of days with workouts (0 = Monday, 6 = Sunday)
        days_with_workouts = {
            # PostgreSQL's week days are 1-7 where 1 is Sunday, 
            # so we need to convert to 0-6 where 0 is Monday
            (workout['weekday'] - 2) % 7 
            for workout in weekly_workouts
        }

        # Create the days array with status for each day
        days = []
        day_ids = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        day_letters = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
        
        for i in range(7):
            current_date = monday + timezone.timedelta(days=i)
            days.append({
                'id': day_ids[i],
                'day': day_letters[i],
                'completed': i in days_with_workouts,
                'date': current_date.day,
                'full_date': current_date.isoformat()  # Include full date for reference
            })

        # Get total sessions this week
        total_sessions = sum(workout['session_count'] for workout in weekly_workouts)

        return {
            'days': days,
            'total_sessions': total_sessions,
            'streak_days': len(days_with_workouts),
            'week_range': {
                'start': monday.isoformat(),
                'end': (monday + timezone.timedelta(days=6)).isoformat()
            }
        }

# -----------------------------------------------------------------------------------------------------------------------------------

class ExerciseDAO:
    @staticmethod
    def replace_session_exercises(session: WorkoutSession, exercises_data: List[Dict]) -> List[Exercise]:
        """
        Replace all exercises for a workout session with new ones using bulk create
        Args:
            session: WorkoutSession instance
            exercises_data: List of dicts containing Exercise model fields
                          Each dict should contain: name, weights, weight_unit, sets, reps
                          Optional fields: workout_machine
        Returns:
            List of created Exercise instances
        """
        # Prepare exercise objects outside transaction (in-memory operation)
        exercise_objects = []
        for exercise_data in exercises_data:
            try:
                exercise = Exercise(
                    workout_session=session,
                    **exercise_data  # Data should exactly match Exercise model fields
                )
                exercise_objects.append(exercise)
            except Exception as e:
                logger.error(f"Failed to prepare exercise record: {str(e)}")
                continue
        
        if not exercise_objects:
            logger.warning("No valid exercise records to create")
            return []
        
        try:
            # Only use transaction for actual database operations
            with transaction.atomic():
                # First delete old records, then bulk create new ones
                delete_count = Exercise.objects.filter(workout_session=session).delete()[0]
                logger.info(f"Deleted {delete_count} existing exercise records")
                
                created_exercises = Exercise.objects.bulk_create(exercise_objects)
                logger.info(f"Bulk created {len(created_exercises)} exercise records")
                return created_exercises
                
        except Exception as e:
            logger.error(f"Failed to replace exercises for session {session.id}: {str(e)}")
            raise