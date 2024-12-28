from django.urls import path
from . import views

app_name = 'whatsapp_bot'

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
] 