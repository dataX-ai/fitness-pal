from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta
from ..models import WorkoutSession, WhatsAppUser
from ..services.logger_service import get_logger
from ..services.twilio_services import send_whatsapp_message

logger = get_logger(__name__)

def get_week_date_range():
    """Get the date range for the previous week (Monday to Sunday)"""
    today = timezone.now().date()
    # Get previous week's Monday and Sunday
    start_of_week = today - timedelta(days=today.weekday() + 7)
    end_of_week = start_of_week + timedelta(days=6)
    return (
        timezone.make_aware(timezone.datetime.combine(start_of_week, timezone.datetime.min.time())),
        timezone.make_aware(timezone.datetime.combine(end_of_week, timezone.datetime.max.time()))
    )

def format_weekly_summary(user, sessions):
    """Format the weekly workout summary for a user"""
    # Calculate weekly stats
    total_workouts = len(sessions)
    total_duration = sum(s.duration_minutes or 0 for s in sessions)
    unique_days = len(set(s.created_at.date() for s in sessions))
    
    # Get most common activity type
    activity_types = [s.activity_type for s in sessions if s.activity_type]
    # most_common_activity = max(set(activity_types), key=activity_types.count) if activity_types else None
    
    # Count total exercises
    total_exercises = sum(s.exercises.count() for s in sessions)
    
    message_parts = [
        "📊 *Your Weekly Workout Summary* 🏋️‍♂️\n",
        f"Week of {sessions[0].created_at.strftime('%B %d')} - {sessions[-1].created_at.strftime('%B %d')}\n",
        f"*Weekly Stats:*",
        f"• Workout Days: {unique_days}/7",
        f"• Total Workouts: {total_workouts}",
        f"• Total Exercises: {total_exercises}",
        f"• Total Time: {total_duration} minutes"
    ]
    
    # if most_common_activity:
    #     message_parts.append(f"• Favorite Activity: {most_common_activity}")
    
    message_parts.append("\n*Daily Breakdown:*")
    
    # Group sessions by day
    current_date = None
    for session in sessions:
        session_date = session.created_at.date()
        if session_date != current_date:
            current_date = session_date
            message_parts.append(f"\n{session_date.strftime('%A, %B %d')}:")
        
        # time_str = session.created_at.strftime("%I:%M %p")
        # workout_info = [f"• {time_str}"]
        # if session.activity_type:
            # workout_info.append(f" - {session.activity_type}")
        # if session.duration_minutes:
        #     workout_info.append(f" ({session.duration_minutes} mins)")
        
        # message_parts.append("".join(workout_info))
        
        # Add exercise summary if exists
        if session.exercises.exists():
            for exercise in session.exercises.all():
                message_parts.append(
                    f"  - {exercise.name}: {exercise.sets}x{exercise.reps} @ "
                    f"{exercise.weights}{exercise.weight_unit or 'kg'}"
                )
    
    # Add motivational message based on performance
    if unique_days >= 5:
        message_parts.append("\n🌟 Outstanding week! Keep up the amazing work! 💪")
    elif unique_days >= 3:
        message_parts.append("\n💪 Solid effort this week! Let's push even harder next week! 🎯")
    else:
        message_parts.append("\n🎯 Every workout counts! Let's aim for more sessions next week! 💪")
    
    return "\n".join(message_parts)

def send_eow_workout_summaries():
    """Send end-of-week workout summaries to users"""
    try:
        start_date, end_date = get_week_date_range()
        
        # Get all users who had workouts in the past week
        users_with_workouts = WhatsAppUser.objects.filter(
            workouts__created_at__range=(start_date, end_date)
        ).distinct()
        
        if not users_with_workouts.exists():
            logger.info("No users had workouts in the past week")
            return
        
        for user in users_with_workouts:
            try:
                # Get all sessions for this user in the date range
                user_sessions = WorkoutSession.objects.filter(
                    user=user,
                    created_at__range=(start_date, end_date)
                ).prefetch_related(
                    'exercises'
                ).order_by('created_at')
                
                if user_sessions.exists():
                    message = format_weekly_summary(user, user_sessions)
                    send_whatsapp_message(
                        to_number=user.phone_number,
                        message=message
                    )
                    logger.info(f"Sent weekly summary to user {user.id}")
                
            except Exception as e:
                logger.error(f"Failed to send weekly summary to user {user.id}: {str(e)}")
        
        logger.info("Completed sending end-of-week workout summaries")
        
    except Exception as e:
        logger.error(f"Error in send_eow_workout_summaries: {str(e)}")
        raise