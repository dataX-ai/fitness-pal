from django.contrib import admin
from .models import WhatsAppUser, RawMessage, BodyHistory, WorkoutSession, Exercise, ProgressPhoto

@admin.register(WhatsAppUser)
class WhatsAppUserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'name', 'created_at', 'last_interaction')
    search_fields = ('phone_number', 'name')

@admin.register(RawMessage)
class RawMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'incoming', 'created_at')
    list_filter = ('incoming', 'created_at')
    search_fields = ('user__phone_number', 'message')

@admin.register(BodyHistory)
class BodyHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'height', 'weight', 'activity', 'created_at')
    list_filter = ('activity', 'created_at')
    search_fields = ('user__phone_number', 'user__name')

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'duration_minutes', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__phone_number', 'user__name', 'activity_type')

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'workout_session', 'weights', 'sets', 'reps')
    list_filter = ('workout_session__created_at',)
    search_fields = ('name', 'workout_session__user__phone_number')

@admin.register(ProgressPhoto)
class ProgressPhotoAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'media_id')
    list_filter = ('created_at',)
    search_fields = ('user__phone_number', 'user__name')
