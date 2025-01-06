from django.urls import path
from . import views

app_name = 'whatsapp_bot'

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
    path('payments/dodo/', views.create_payment, name='create_payment'),
    path('payments/dodo/webhook/', views.dodo_webhook, name='dodo_webhook'),
    path('health/', views.health_check, name='health_check'),
    path('workout-info/', views.fetch_workout_info, name='fetch_workout_info'),
    path('v1/dashboard/user-info/', views.get_user_dashboard_info, name='get_user_dashboard_info'),
]