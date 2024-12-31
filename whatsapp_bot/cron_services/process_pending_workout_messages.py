from django.utils import timezone
from django.db.models import Count, Q, F
from ..models import WorkoutSession, Exercise
from ..services.logger_service import get_logger
from ..ai_services.nlp_processor import extract_workout_details
from django.db import transaction
from ..dao.exercise_dao import ExerciseDAO, WorkoutSessionDAO

logger = get_logger(__name__)

def process_pending_workout_messages():
    """
    Find workout sessions with pending messages to process using optimized database queries
    """
    try:
        # Calculate the timestamp for 8 hours ago
        eight_hours_ago = timezone.now() - timezone.timedelta(hours=8)
        
        # Use annotations to count relationships at the database level
        pending_sessions = WorkoutSession.objects.filter(
            created_at__gte=eight_hours_ago
        ).annotate(
            raw_count=Count('raw_messages'),
            processed_count=Count('processed_messages')
        ).filter(
            Q(raw_count__gt=0) & Q(raw_count__gt=F('processed_count'))  # Compare counts at DB level
        ).values('id', 'raw_count', 'processed_count')
        
        session_count = len(pending_sessions)
        
        if session_count > 0:
            logger.info(f"Found {session_count} sessions with pending messages to process")
            # Process each session
            for session_data in pending_sessions:
                try:
                    session = WorkoutSession.objects.get(id=session_data['id'])
                    process_session(session)
                except Exception as e:
                    logger.error(f"Failed to process session {session_data['id']}: {str(e)}")
                    continue
        else:
            logger.info("No sessions found with pending messages")
        
        return f"Found {session_count} sessions with pending messages"
        
    except Exception as e:
        logger.error(f"Failed to process pending workout messages: {str(e)}")
        raise

def process_session(session: WorkoutSession):
    """
    Process a single workout session by:
    1. Concatenating ALL raw messages
    2. Extracting workout details using NLP
    3. Creating Exercise records from the extracted data
    """
    try:
        # Get all raw messages for this session
        raw_messages = session.raw_messages.all()
        
        # Concatenate messages with newlines
        message_blob = '\n'.join(msg.message for msg in raw_messages)
        
        if not message_blob.strip():
            logger.warning(f"No message content found for session {session.id}")
            return
        
        # Extract workout details using NLP
        logger.info(f"Processing message blob for session {session.id}")
        logger.info(f"Input message blob: {message_blob}")
        
        workout_details = extract_workout_details(message_blob)
        logger.info(f"Extracted workout details: {workout_details}")
        
        # Process exercises from the workout details
        if 'exercises' in workout_details:
            try:
                # Transform the NLP output to match Exercise model fields
                exercise_records = []
                for exercise in workout_details['exercises']:
                    try:
                        exercise_record = {
                            'name': exercise['exercise_name'],
                            'weights': exercise['weight']['value'],
                            'weight_unit': exercise['weight']['unit'],
                            'sets': exercise['sets'],
                            'reps': int(exercise['reps'])
                        }
                        exercise_records.append(exercise_record)
                    except (KeyError, ValueError) as e:
                        logger.error(f"Failed to transform exercise data: {str(e)}")
                        continue
                
                # Replace exercises using ExerciseDAO
                created_exercises = ExerciseDAO.replace_session_exercises(
                    session=session,
                    exercises_data=exercise_records
                )
                
                # If exercises were created successfully, mark messages as processed
                if created_exercises:
                    WorkoutSessionDAO.mark_messages_as_processed(
                        session=session,
                        raw_messages=raw_messages
                    )
                
                logger.info(f"Successfully processed {len(created_exercises)} exercises for session {session.id}")
            except Exception as e:
                logger.error(f"Failed to process exercises for session {session.id}: {str(e)}")
                raise
        else:
            logger.warning(f"No exercises found in workout details for session {session.id}")
            
    except Exception as e:
        logger.error(f"Error processing session {session.id}: {str(e)}")
        raise
