from django.contrib import admin
from .models import WhatsAppUser, WorkoutSession, Exercise, ProgressPhoto

class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 1

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'duration_minutes', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__phone_number', 'activity_type', 'raw_message')
    inlines = [ExerciseInline]

@admin.register(WhatsAppUser)
class WhatsAppUserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'created_at', 'last_interaction')
    search_fields = ('phone_number',)

@admin.register(ProgressPhoto)
class ProgressPhotoAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'image_url')
    list_filter = ('created_at',)
    search_fields = ('user__phone_number',)
