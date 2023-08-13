from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from core.WebSocket_consumers.message_consumers import MessageConsumer

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        # Define the WebSocket route with a dynamic parameter 'receiver_id'
        # This route is for WebSocket connections to initiate live messaging sessions
        path("ws/messages/<int:receiver_id>/", MessageConsumer.as_asgi()),
    ]),
})
