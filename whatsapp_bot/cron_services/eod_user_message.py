from django.utils import timezone
from django.db.models import Prefetch
from ..models import WorkoutSession, Exercise, WhatsAppUser
from ..services.logger_service import get_logger
from ..services.twilio_services import send_whatsapp_message  # Assuming you have this

logger = get_logger(__name__)

def format_exercise_summary(exercise):
    """Format a single exercise into a readable string"""
    return f"• {exercise.name}: {exercise.sets}x{exercise.reps} @ {exercise.weights}{exercise.weight_unit or 'kg'}"

def format_workout_message(sessions):
    """Format all workout sessions into a nice message"""
    message_parts = ["🏋️‍♂️ *Your Workout Summary for Today* 💪\n"]
    
    for session in sessions:
        # Add session header with time and activity type
        time_str = session.created_at.strftime("%I:%M %p")
        message_parts.append(f"\n*Workout at {time_str}*")
        if session.activity_type:
            message_parts.append(f"Type: {session.activity_type}")
        
        # Add exercises
        if session.exercises.exists():
            message_parts.append("\nExercises:")
            for exercise in session.exercises.all():
                message_parts.append(format_exercise_summary(exercise))
        
        if session.duration_minutes:
            message_parts.append(f"\nDuration: {session.duration_minutes} minutes")
    
    message_parts.append("\nGreat job today! 💪 Keep pushing yourself! 🎯")
    return "\n".join(message_parts)

def send_eod_workout_summaries():
    """Send end-of-day workout summaries to users"""
    try:
        # Get today's date range
        today = timezone.now().date()
        start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))
        
        # Get all workout sessions for today with related exercises
        sessions = WorkoutSession.objects.filter(
            created_at__range=(start_of_day, end_of_day)
        ).prefetch_related(
            'exercises'
        ).select_related(
            'user'
        ).order_by('user_id', 'created_at')
        
        if not sessions.exists():
            logger.info("No workout sessions found for today")
            return
        
        # Group sessions by user
        current_user_id = None
        user_sessions = []
        
        for session in sessions:
            # If we encounter a new user, send the previous user's summary
            if current_user_id and current_user_id != session.user_id:
                try:
                    message = format_workout_message(user_sessions)
                    send_whatsapp_message(
                        to_number=user_sessions[0].user.phone_number,
                        message=message
                    )
                    # Mark all sessions as processed
                    WorkoutSession.objects.filter(
                        id__in=[s.id for s in user_sessions]
                    ).update(eod_summary_sent=True)
                    logger.info(f"Sent workout summary to user {current_user_id}")
                except Exception as e:
                    logger.error(f"Failed to send message to user {current_user_id}: {str(e)}")
                user_sessions = []
            
            current_user_id = session.user_id
            user_sessions.append(session)
        
        # Send summary for the last user
        if user_sessions:
            try:
                message = format_workout_message(user_sessions)
                send_whatsapp_message(
                    to_number=user_sessions[0].user.phone_number,
                    message=message
                )
                logger.info(f"Sent workout summary to user {current_user_id}")
            except Exception as e:
                logger.error(f"Failed to send message to last user {current_user_id}: {str(e)}")
        
        logger.info("Completed sending end-of-day workout summaries")
        
    except Exception as e:
        logger.error(f"Error in send_eod_workout_summaries: {str(e)}")
        raise