from django.db import transaction
from django.db.models import QuerySet, Sum, Case, When, IntegerField, Count
from django.utils import timezone
from datetime import timedelta, datetime
from ..models import Exercise, WorkoutSession, RawMessage, WhatsAppUser
from ..services.logger_service import get_logger
from typing import List, Dict, Optional
import pandas as pd
from django.db.models.functions import TruncDate, ExtractWeekDay
from django.db import models
from ..utils.config import EXERCISE_LIST_DF, MUSCLE_GROUP_MERGING_MAP

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

    @staticmethod
    def get_workout_sessions_by_date_range(user: WhatsAppUser, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """
        Get workout sessions for a user within a specified date range, returning intensity and calories as date-keyed dictionaries
        
        Args:
            user: WhatsAppUser instance
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive). If None, uses current date
            
        Returns:
            Dictionary containing:
            - intensity: Dict with dates as keys and intensity values
            - calories_burnt: Dict with dates as keys and calorie values
        """
        try:
            # Start with base query for the user
            query = WorkoutSession.objects.filter(user=user)
            
            # Add date filters if provided
            if start_date:
                query = query.filter(created_at__gte=start_date)
            if end_date:
                query = query.filter(created_at__lte=end_date)
            else:
                query = query.filter(created_at__lte=timezone.now())
                
            # Select only the required fields and order by date
            sessions = query.values('intensity', 'calories_burnt', 'created_at').order_by('-created_at')
            
            # Initialize result dictionaries
            intensity_dict = {}
            calories_dict = {}
            
            # Process each session and build the dictionaries
            for session in sessions:
                # Convert datetime to date string in ISO format (YYYY-MM-DD)
                date_str = session['created_at'].date().isoformat()
                
                # Add intensity if it exists (default to empty string if None)
                intensity_dict[date_str] = session['intensity'] if session['intensity'] is not None else ''
                
                # Add calories if they exist (default to 0 if None)
                calories_dict[date_str] = session['calories_burnt'] if session['calories_burnt'] is not None else 0
            
            return {
                'intensity': intensity_dict,
                'calories_burnt': calories_dict
            }
            
        except Exception as e:
            logger.error(f"Failed to get workout sessions for user {user.id}: {str(e)}")
            return {
                'intensity': {},
                'calories_burnt': {}
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

    @staticmethod
    def get_volume_by_muscle_group(user: Optional[WhatsAppUser] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Get the percentage distribution of volume (sets × reps) grouped by muscle group for a user's workout sessions within a time window
        Args:
            user: Optional WhatsAppUser instance. If provided, only analyzes that user's sessions
            start_date: Optional start date for the time window (inclusive). If None, includes from the beginning
            end_date: Optional end date for the time window (inclusive). If None, includes up to now
        Returns:
            Dictionary with muscle_group as key and percentage of total volume as value
        """
        try:
            # Start with base query
            query = Exercise.objects.filter(muscle_group__isnull=False)
            
            # Apply filters based on parameters
            if user:
                query = query.filter(workout_session__user=user)
            if start_date:
                query = query.filter(workout_session__created_at__gte=start_date)
            if end_date:
                query = query.filter(workout_session__created_at__lte=end_date)
            
            # Get volume by muscle group
            volume_by_muscle = query.values('muscle_group').annotate(
                total_volume=Sum(
                    models.F('sets') * models.F('reps'),
                    output_field=models.IntegerField()
                )
            )
            
            # Initialize merged volumes dictionary
            merged_volumes = {}
            
            # Process each muscle group and merge according to mapping
            for item in volume_by_muscle:
                muscle_group = str(item['muscle_group']).lower()
                volume = item['total_volume']
                
                # If muscle group needs to be merged, use the mapped name
                if muscle_group in MUSCLE_GROUP_MERGING_MAP:
                    merged_name = MUSCLE_GROUP_MERGING_MAP[muscle_group]
                    merged_volumes[merged_name] = merged_volumes.get(merged_name, 0) + volume
                else:
                    # Keep original name for unmapped muscle groups
                    merged_volumes[muscle_group] = merged_volumes.get(muscle_group, 0) + volume
            
            # Calculate total volume for percentage calculation
            total_volume = sum(merged_volumes.values())
            
            # Convert absolute values to percentages
            if total_volume > 0:
                percentage_volumes = {
                    muscle: (volume / total_volume) * 100
                    for muscle, volume in merged_volumes.items()
                }
            else:
                percentage_volumes = None
            
            return percentage_volumes

        except Exception as e:
            error_msg = f"Failed to get volume by muscle group"
            if user:
                error_msg += f" for user {user.id}"
            if start_date or end_date:
                error_msg += f" (time window: {start_date} to {end_date})"
            logger.error(f"{error_msg}: {str(e)}")
            return {}

    @staticmethod
    def update_empty_muscle_groups(session: Optional[WorkoutSession] = None) -> int:
        """
        Update exercises with empty muscle groups using the EXERCISE_LIST_DF.
        For exercises not found in the dataframe, sets muscle group as 'Unknown'.
        
        Args:
            session: Optional WorkoutSession instance. If provided, only updates exercises in that session.
                    If None, updates all exercises in the database.
        Returns:
            Number of exercises updated
        """
        logger.warning(f"Method Disabled: This is a Debug Method for modifying database")
        return -1

        logger.warning(f"Updating empty muscle groups for session {session.id if session else 'all'}")
        try:
            # Create a name to muscle group mapping from the dataframe
            exercise_muscle_map = dict(zip(
                EXERCISE_LIST_DF['Exercise Name'].str.lower(),
                EXERCISE_LIST_DF['Muscle Group']
            ))
            
            # Start with exercises that have null muscle groups
            query = Exercise.objects.filter(muscle_group__isnull=True)
            if session:
                query = query.filter(workout_session=session)
            
            # Update count
            updates = 0
            
            # Process in chunks to avoid memory issues with large datasets
            for exercise in query:
                # Look up muscle group, defaulting to 'Unknown' if not found
                muscle_group = exercise_muscle_map.get(
                    exercise.name.lower(),
                    'Unknown'
                )
                
                exercise.muscle_group = muscle_group
                exercise.save()
                updates += 1
            
            logger.info(f"Updated muscle groups for {updates} exercises")
            return updates
            
        except Exception as e:
            logger.error(f"Failed to update empty muscle groups: {str(e)}")
            return 

