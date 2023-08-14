import json
from channels.generic.websocket import AsyncWebsocketConsumer


# WebSocket consumer for handling real-time notifications.
class NotificationConsumer(AsyncWebsocketConsumer):

    # Establishes a WebSocket connection for the user's notifications.
    async def connect(self):
        user = self.scope["user"]

        # If the user is not authenticated, send an authentication required message and close the connection
        if user.is_anonymous:
            await self.send(text_data=json.dumps({
                "type": "authentication_required",
                "message": "Authentication is required to access notifications."
            }))
            await self.close()
            return

        self.notification_group = f"notifications_{user.id}"

        # Add the user to the notification group
        await self.channel_layer.group_add(
            self.notification_group,
            self.channel_name
        )

        await self.accept()

    # Disconnects the user from the WebSocket notification group.
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.notification_group,
            self.channel_name
        )

    # Sends a new notification message to the connected user.
    async def notify_notification(self, event):
        unique_identifier = event["unique_identifier"]  # notification's id
        message = event["message"]  # notification message

        # user profile picture associated with the notification (ex: user who liked your post)
        sender_profile_picture_url = event["sender_profile_picture_url"]
        # post media associated with the notification
        post_media_url = event.get("post_media_url")  # Use .get() to handle the possibility of missing key

        # Send notification data to the user
        await self.send(text_data=json.dumps({
            "type": "notification",
            "unique_identifier": unique_identifier,
            "message": message,
            "sender_profile_picture_url": sender_profile_picture_url,
            "post_media_url": post_media_url,
        }))

    # Removes a specific notification from the user's WebSocket
    async def remove_notification(self, event):
        unique_identifier = event["unique_identifier"]

        # # Send removal instruction to the user's WebSocket
        await self.send(text_data=json.dumps({
            "type": "remove_notification",
            "unique_identifier": unique_identifier,
        }))
