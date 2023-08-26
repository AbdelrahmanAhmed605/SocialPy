from django.urls import re_path

from core.WebSocket_consumers.message_consumers import MessageConsumer
from core.WebSocket_consumers.notification_consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/messages/(?P<receiver_id>\d+)/$", MessageConsumer.as_asgi()),
    re_path(r"ws/notifications/(?P<user_id>\d+)/$", NotificationConsumer.as_asgi()),
]
