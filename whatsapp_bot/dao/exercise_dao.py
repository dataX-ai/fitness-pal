from django.db import transaction
from django.db.models import QuerySet
from ..models import Exercise, WorkoutSession, RawMessage
from ..services.logger_service import get_logger
from typing import List, Dict

logger = get_logger(__name__)

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


class WorkoutSessionDAO:
    @staticmethod
    def mark_messages_as_processed(session: WorkoutSession, raw_messages: QuerySet[RawMessage]) -> None:
        """
        Update the processed_messages for a workout session
        Args:
            session: WorkoutSession instance
            raw_messages: QuerySet of RawMessage instances that were processed
        """
        try:
            session.processed_messages.set(raw_messages)
            logger.info(f"Updated processed messages for session {session.id}")
        except Exception as e:
            logger.error(f"Failed to update processed messages for session {session.id}: {str(e)}")
            raise