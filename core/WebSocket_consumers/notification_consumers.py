import json
from channels.generic.websocket import AsyncWebsocketConsumer
from ..models import Notification


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

    # Marks a notification in the Live WebSocket as read if the user reading the notification is the recipient
    async def mark_notification_as_read(self, unique_identifier):
        # Find the notification by its unique identifier and mark it as read
        try:
            notification_id = int(unique_identifier)
            notification = Notification.objects.get(id=notification_id)
            if notification.recipient == self.scope["user"] and not notification.is_read:
                notification.is_read = True
                notification.save()
        except (ValueError, Notification.DoesNotExist):
            pass

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

        # Mark the notification as read if the recipient is the current user
        await self.mark_notification_as_read(unique_identifier)

    # Removes a specific notification from the user's WebSocket
    async def remove_notification(self, event):
        unique_identifier = event["unique_identifier"]

        # # Send removal instruction to the user's WebSocket
        await self.send(text_data=json.dumps({
            "type": "remove_notification",
            "unique_identifier": unique_identifier,
        }))
