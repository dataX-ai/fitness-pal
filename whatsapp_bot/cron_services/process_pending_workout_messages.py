from django.utils import timezone
from django.db.models import Count, Q, F
from ..models import WorkoutSession, Exercise
from ..services.logger_service import get_logger
from ..ai_services.nlp_processor import extract_workout_details
from django.db import transaction
from ..dao.exercise_dao import ExerciseDAO, WorkoutSessionDAO
import pandas as pd
import os
import math
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from ..utils.config import EXERCISE_LIST_DF, EXERCISE_LEVEL_JSON, EXERCISE_LEVEL_INTENSITY_MAPPING
from ..utils.conversion import lbs_to_kg

logger = get_logger(__name__)

exercise_metrics = {}
for _, row in EXERCISE_LIST_DF.iterrows():
    exercise_name = row['Exercise Name']
    avg_rep = row['Avg Rep']
    avg_break = row['Avg Break']
    cal_per_rep = row['calories_spent_per_rep_per_kg']
    exercise_metrics[exercise_name] = [avg_rep, avg_break, cal_per_rep]


def process_session_wrapper(session_data: Dict):
    """Wrapper function to handle individual session processing"""
    try:
        session = WorkoutSession.objects.get(id=session_data['id'])
        process_session(session)
        return True
    except Exception as e:
        logger.error(f"Failed to process session {session_data['id']}: {str(e)}")
        return False

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
            raw_count=Count('raw_messages', distinct=True),
            processed_count=Count('processed_messages', distinct=True)
        ).filter(
            Q(raw_count__gt=0) & Q(raw_count__gt=F('processed_count'))  # Compare counts at DB level
        ).values('id', 'raw_count', 'processed_count')
        
        session_count = len(pending_sessions)

        if session_count > 0:
            logger.info(f"Found {session_count} sessions with pending messages to process")
            
            # Process sessions in parallel using ThreadPoolExecutor
            max_workers = min(session_count, 4)  # Limit max workers to 4 or session count
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all sessions for processing
                results = list(executor.map(process_session_wrapper, pending_sessions))
                
                # Count successful processes
                successful = sum(1 for result in results if result)
                logger.info(f"Successfully processed {successful} out of {session_count} sessions")
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

        session_time = 0
        temp_session_time = []
        calories_burnt = 0

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

                        exercise_time += (exercise_metrics[exercise['exercise_name']][0] * int(exercise['reps'])  + exercise_metrics[exercise['exercise_name']][1]*(int(exercise['sets'])-1) + 120)/60
                        session_time += exercise_time
                        calories_burnt += exercise_metrics[exercise['exercise_name']][2] * int(exercise['reps']) * int(exercise['sets'])  * (int(exercise['weight']['value']) if exercise['weight']['unit'].lower() in ['kg', 'kgs', 'kilograms', 'kilos', 'kilogram', 'kilo'] else int(lbs_to_kg(exercise['weight']['value'])))
                        intensity += get_exercise_intensity(exercise)
                        temp_session_time.append({exercise['exercise_name']: {"time": exercise_time, "intensity": get_exercise_intensity(exercise), "calories": exercise_metrics[exercise['exercise_name']][2] * int(exercise['reps']) * int(exercise['sets'])  * (int(exercise['weight']['value']) if exercise['weight']['unit'].lower() in ['kg', 'kgs', 'kilograms', 'kilos', 'kilogram', 'kilo'] else int(lbs_to_kg(exercise['weight']['value'])))}})
                        logger.info(f"Session Time Now with {exercise['exercise_name']}: {temp_session_time}")
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
                        raw_messages=raw_messages,
                        session_time=math.ceil(session_time),
                        calories_burnt=math.ceil(calories_burnt)
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

def get_exercise_intensity(exercise: Dict):
    try:
        weight = exercise['weight']['value']
        rep = exercise['reps']
        set = exercise['sets']

        if exercise['weight']['unit'].lower() in ['kg', 'kgs', 'kilograms', 'kilos', 'kilogram', 'kilo']:
            weight = int(lbs_to_kg(weight))

        if weight < EXERCISE_LEVEL_JSON[exercise['exercise_name']]['exercise_weights']['level1']['max']:
            return ((rep*set)**1.5)*(EXERCISE_LEVEL_INTENSITY_MAPPING['level1'])
        elif weight>= EXERCISE_LEVEL_JSON[exercise['exercise_name']]['exercise_weights']['level2']['min'] and weight < EXERCISE_LEVEL_JSON[exercise['exercise_name']]['exercise_weights']['level2']['max']:
            return ((rep*set)**1.5)*(EXERCISE_LEVEL_INTENSITY_MAPPING['level2'])
        else:
            return ((rep*set)**1.5)*(EXERCISE_LEVEL_INTENSITY_MAPPING['level3'])
    except Exception as e:
        logger.error(f"Error getting exercise intensity: {str(e)}")
        return 0
