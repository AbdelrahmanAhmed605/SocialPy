import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ..models import Notification, User


# WebSocket consumer for handling real-time notifications.
class NotificationConsumer(AsyncWebsocketConsumer):

    # Retrieve a notification from the database by its ID
    # wrapped with @database_sync_to_async to allow database access in an asynchronous context.
    @database_sync_to_async
    def get_notification(self, notification_id):
        try:
            return Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            return None

    # Establishes a WebSocket connection for the user's notifications.
    async def connect(self):
        # Get the receiver of the WebSocket Notifications from the url
        user = self.scope["url_route"]["kwargs"]["user_id"]

        # Store the authenticated user's id to be used in the mark_notification_as_read function
        self.auth_userId = user

        # Create a notification group for the user and add it to the channel layer
        self.notification_group = f"notifications_{user}"
        await self.channel_layer.group_add(
            self.notification_group,
            self.channel_name
        )

        await self.accept()

    # Disconnects the user from the WebSocket notification group.
    async def disconnect(self, close_code):
        if hasattr(self, 'notification_group'):
            await self.channel_layer.group_discard(
                self.notification_group,
                self.channel_name
            )

    # Marks a notification in the Live WebSocket as read if the user reading the notification is the recipient
    async def mark_notification_as_read(self, unique_identifier):
        try:
            # Find the notification by its unique identifier
            notification_id = int(unique_identifier)
            notification = await self.get_notification(notification_id)
            if notification:
                # Find the recipient of the notification
                recipient_id = notification.recipient_id
                # Check the notification recipient matches the current authenticated user and the notification is unread
                if recipient_id == self.auth_userId and not notification.is_read:
                    notification.is_read = True
                    await notification.save()
        except ValueError:
            pass

    # Sends a new notification message to the connected user.
    async def core_notification(self, event):
        unique_identifier = event["unique_identifier"]  # notification's id
        message = event["message"]  # notification message
        notification_type = event["notification_type"]  # type of notification
        recipient = event["recipient"]  # recipient of notification
        sender = event["sender"]  # sender of notification (user who committed action)

        # user profile picture associated with the notification (ex: user who liked your post)
        sender_profile_picture_url = event["sender_profile_picture_url"]
        # post media associated with the notification
        post_media_url = event.get("post_media_url")  # Use .get() to handle the possibility of missing key

        # Send notification data to the user
        await self.send(text_data=json.dumps({
            "type": "core.notification",
            "unique_identifier": unique_identifier,
            "notification_type": notification_type,
            "recipient": recipient,
            "sender": sender,
            "message": message,
            "sender_profile_picture_url": sender_profile_picture_url,
            "post_media_url": post_media_url,
        }))

        # Mark the notification as read if the recipient is the current user
        await self.mark_notification_as_read(unique_identifier)

    # Function to send follow request action (accept or decline) updates to frontend
    async def notification_follow_request_action(self, event):
        action = event["action"]  # 'accept' or 'decline'
        unique_identifier = event["unique_identifier"]

        # Send update to the connected frontend clients
        await self.send(text_data=json.dumps({
            "type": "notification_follow_request_action",
            "action": action,
            "unique_identifier": unique_identifier,
        }))

    # Removes a specific notification from the user's WebSocket
    async def remove_notification(self, event):
        unique_identifier = event["unique_identifier"]

        # Send removal instruction to the user's WebSocket
        await self.send(text_data=json.dumps({
            "type": "remove.notification",
            "unique_identifier": unique_identifier,
        }))
