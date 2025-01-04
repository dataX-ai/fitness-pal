from django.db import models

class WhatsAppUser(models.Model):
    phone_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    paid = models.BooleanField(default=False)

    # metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_interaction = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

class RawMessage(models.Model):
    user = models.ForeignKey(WhatsAppUser, on_delete=models.CASCADE, related_name='raw_messages')
    message = models.TextField()
    incoming = models.BooleanField(default=True)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone_number}: {self.message[:50]}..."

class BodyHistory(models.Model):
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Lightly Active (1-3 days/week)'),
        ('moderate', 'Moderately Active (3-5 days/week)'),
        ('very', 'Very Active (6-7 days/week)'),
        ('extra', 'Extra Active (very active & physical job)'),
    ]

    BODY_COMPOSITION_CHOICES = [
        ('calorie_deficit', 'Calorie Deficit'),
        ('calorie_maintenance', 'Calorie Maintenance'),
        ('calorie_surplus', 'Calorie Surplus'),
    ]

    GOAL_CHOICES = [
        ('lean', 'Lean (Slim and Defined)'),
        ('athletic', 'Athletic ( Muscular and Balanced)'),
        ('bulk', 'Bulk (Large and Powerful)'),
    ]

    user = models.ForeignKey(WhatsAppUser, on_delete=models.CASCADE)
    height = models.FloatField(null=True, blank=True)  # in cm
    weight = models.FloatField(null=True, blank=True)  # in kg
    activity = models.CharField(max_length=50, choices=ACTIVITY_CHOICES, null=True, blank=True)
    body_fat = models.FloatField(null=True, blank=True)  # in percentage
    bmi = models.FloatField(null=True, blank=True)
    maintenance_calories = models.IntegerField(null=True, blank=True)
    body_composition = models.CharField(max_length=50, choices=BODY_COMPOSITION_CHOICES, null=True, blank=True)
    photo_link = models.URLField(null=True, blank=True)
    dream_photo_link = models.URLField(null=True, blank=True)
    goal = models.CharField(max_length=50, choices=GOAL_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only for new instances
            latest = BodyHistory.objects.filter(user=self.user).order_by('-created_at').first()
            if latest:
                # List of fields to copy if they're null
                fields_to_copy = [
                    'height', 'weight', 'activity', 'body_fat', 'bmi',
                    'maintenance_calories', 'body_composition', 'goal'
                ]
                
                for field in fields_to_copy:
                    current_value = getattr(self, field)
                    if current_value is None:
                        setattr(self, field, getattr(latest, field))
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user}'s body history at {self.created_at}"

class WorkoutSession(models.Model):
    user = models.ForeignKey(WhatsAppUser, on_delete=models.CASCADE, related_name='workouts')
    activity_type = models.CharField(max_length=100, null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    raw_messages = models.ManyToManyField(RawMessage, related_name='raw_workout_sessions')
    processed_messages = models.ManyToManyField(RawMessage, related_name='processed_workout_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone_number} - {self.activity_type} ({self.created_at})"

class Exercise(models.Model):
    workout_session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=100)
    weights = models.IntegerField()
    weight_unit = models.CharField(max_length=50, null=True, blank=True)
    sets = models.IntegerField()
    reps = models.IntegerField()
    workout_machine = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.sets}x{self.reps}"

class ProgressPhoto(models.Model):
    user = models.ForeignKey(WhatsAppUser, on_delete=models.CASCADE, related_name='photos')
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    media_id = models.CharField(max_length=255)  # Twilio's MediaSid
    
    def __str__(self):
        return f"{self.user.phone_number} - Photo at {self.created_at}"

class PaymentHistory(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    PERIOD_INTERVAL_CHOICES = [
        ('Year', 'Year'),
        ('Month', 'Month'),
        ('Week', 'Week'),
        ('Day', 'Day'),
    ]

    # User and basic info
    user = models.ForeignKey(WhatsAppUser, on_delete=models.CASCADE, related_name='payments')
    subscription_id = models.CharField(max_length=255)
    customer_id = models.CharField(max_length=255, null=True, blank=True)
    product_id = models.CharField(max_length=255, null=True, blank=True)
    business_id = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255)

    # Amount and currency
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, null=True, blank=True)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_time = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)
    
    # Subscription details
    trial_period_days = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    
    # Intervals
    subscription_period_interval = models.CharField(
        max_length=10, 
        choices=PERIOD_INTERVAL_CHOICES,
        null=True, blank=True
    )
    payment_frequency_interval = models.CharField(
        max_length=10, 
        choices=PERIOD_INTERVAL_CHOICES,
        null=True, blank=True
    )
    subscription_period_count = models.IntegerField(null=True, blank=True)
    payment_frequency_count = models.IntegerField(null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Payment histories"

    def __str__(self):
        return f"{self.user.phone_number} - {self.subscription_id} ({self.status})"
