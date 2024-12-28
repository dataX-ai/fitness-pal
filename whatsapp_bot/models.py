from django.db import models
from django.utils import timezone

class RawMessage(models.Model):
    phone_number = models.CharField(max_length=50)
    message = models.TextField()
    incoming = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number}: {self.message[:50]}..."

class WhatsAppUser(models.Model):
    phone_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50, null=True, blank=True)

    # metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_interaction = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate BMI if height and weight are available
        if self.height and self.weight and self.height > 0:
            height_in_meters = self.height / 100
            self.bmi = round(self.weight / (height_in_meters * height_in_meters), 2)
        
        #TODO: Calculate Body Fat Percentage
        #TODO: Calculate Maintenance Calories
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

class BodyHistory(models.Model):
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Lightly active (1-3 days/week)'),
        ('moderate', 'Moderately active (3-5 days/week)'),
        ('very', 'Very active (6-7 days/week)'),
        ('extra', 'Extra active (very active & physical job)')
    ]

    GOAL_CHOICES = [
        ('lose', 'Lose Weight'),
        ('maintain', 'Maintain Weight'),
        ('gain', 'Gain Weight'),
        ('muscle', 'Build Muscle'),
        ('strength', 'Increase Strength')
    ]

    BODY_COMPOSITION_CHOICES = [
        ('calorie_deficit', 'Calorie Deficit'),
        ('body_recomposition', 'Maintain Calorie'),
        ('calorie_surplus', 'Calorie Surplus')
    ]
    user = models.ForeignKey(WhatsAppUser, on_delete=models.CASCADE, related_name='body_history')
    height = models.FloatField(help_text="Height in centimeters", null=True, blank=True)
    weight = models.FloatField(help_text="Weight in kilograms", null=True, blank=True)
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, null=True, blank=True)
    activity = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, null=True, blank=True)
    photo_link = models.URLField(max_length=500, null=True, blank=True)
    dream_photo_link = models.URLField(max_length=500, null=True, blank=True)
    body_fat = models.FloatField(help_text="Manually entered body fat percentage", null=True, blank=True)
    bmi = models.FloatField(help_text="Body Mass Index", null=True, blank=True)
    maintenance_calories = models.IntegerField(help_text="Daily maintenance calories", null=True, blank=True)
    body_composition = models.CharField(max_length=20, choices=BODY_COMPOSITION_CHOICES, null=True, blank=True)

class WorkoutSession(models.Model):
    user = models.ForeignKey(WhatsAppUser, on_delete=models.CASCADE, related_name='workouts')
    activity_type = models.CharField(max_length=100, null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    raw_messages = models.ManyToManyField(RawMessage, related_name='workout_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone_number} - {self.activity_type} ({self.created_at})"

class Exercise(models.Model):
    workout_session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='exercises')
    raw_message = models.ForeignKey(RawMessage, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=100)
    weights = models.IntegerField()
    sets = models.IntegerField()
    reps = models.IntegerField()

    def __str__(self):
        return f"{self.name} - {self.sets}x{self.reps}"

class ProgressPhoto(models.Model):
    user = models.ForeignKey(WhatsAppUser, on_delete=models.CASCADE, related_name='photos')
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    media_id = models.CharField(max_length=255)  # Twilio's MediaSid
    
    def __str__(self):
        return f"{self.user.phone_number} - Photo at {self.created_at}"
