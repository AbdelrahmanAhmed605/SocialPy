# core/message_urls.py
from django.urls import path
from core.API_Views import notification_views

urlpatterns = [
    # Endpoint: GET /api/notifications
    path('api/notifications', notification_views.get_notifications, name='get-notifications'),
]
