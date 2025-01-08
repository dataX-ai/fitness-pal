from django.utils import timezone
from django.db import models

def calculate_fitness_rating(user):
    """
    Calculates a fitness rating (0-100) for a given user based on their workout history.
    
    Parameters:
    - user: WhatsAppUser instance
    
    Returns:
    - int or None: Fitness rating between 0-100, or None if insufficient data
    """
    # Get all workout sessions ordered by date
    workout_sessions = user.workouts.all().order_by('created_at')
    total_sessions = workout_sessions.count()
    
    if total_sessions < 20:
        return None
        
    # Initialize rating components
    consistency_score = 0
    variety_score = 0
    intensity_score = 0
    
    # Calculate consistency score (40% of total)
    last_30_days = workout_sessions.filter(
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    consistency_score = min(40, (last_30_days / 20) * 40)
    
    # Calculate variety score (30% of total)
    unique_exercises = set()
    for session in workout_sessions:
        unique_exercises.update(session.exercises.values_list('name', flat=True))
    variety_score = min(30, (len(unique_exercises) / 15) * 30)
    
    # Calculate intensity score (30% of total)
    total_sets = 0
    total_exercises = 0
    for session in workout_sessions:
        exercises = session.exercises.all()
        total_exercises += exercises.count()
        total_sets += exercises.aggregate(total=models.Sum('sets'))['total'] or 0
    
    if total_exercises > 0:
        avg_sets_per_exercise = total_sets / total_exercises
        intensity_score = min(30, (avg_sets_per_exercise / 4) * 30)
    
    # Calculate final rating
    fitness_rating = round(consistency_score + variety_score + intensity_score)
    
    return min(100, fitness_rating)

def get_rating_description(rating):
    """
    Returns a descriptive text based on the fitness rating.
    
    Parameters:
    - rating: int or None
    
    Returns:
    - str: Description of the rating
    """
    if rating is None:
        return "Insufficient data - complete more workouts to get a rating"
    
    if rating >= 90:
        return "Excellent fitness dedication! You're among our top performers."
    elif rating >= 70:
        return "Good fitness routine! You're maintaining a solid workout schedule."
    elif rating >= 50:
        return "Average commitment. There's room for improvement in consistency or variety."
    else:
        return "Getting started! Focus on building a regular workout routine."
    

# # Example usage
# def get_user_fitness_summary(user_id):
#     user = WhatsAppUser.objects.get(id=user_id)
#     rating = calculate_fitness_rating(user)
#     description = get_rating_description(rating)
    
#     return {
#         'rating': rating,
#         'description': description,
#         'total_workouts': user.workouts.count()
#     }