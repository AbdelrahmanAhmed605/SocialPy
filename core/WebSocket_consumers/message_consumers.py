import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ..models import Message, User


# WebSocket consumer to handle live messaging between users
class MessageConsumer(AsyncWebsocketConsumer):

    # Retrieve a user from the database by their authentication token.
    # wrapped with @database_sync_to_async to allow database access in an asynchronous context.
    @database_sync_to_async
    def get_user_by_token(self, token):
        try:
            return User.objects.get(auth_token=token)
        except User.DoesNotExist:
            return None

    # Retrieve a message from the database by its ID
    @database_sync_to_async
    def get_message(self, message_id):
        try:
            return Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return None

    # Initiates a WebSocket connection for live messaging.
    async def connect(self):
        # Get headers from the connection's scope
        headers = dict(self.scope["headers"])

        # If user is not authenticated, send an authentication required message and close the connection
        if b"authorization" not in headers:
            await self.accept()
            await self.send(text_data=json.dumps({
                "type": "authentication_required",
                "message": "Authentication is required to access notifications."
            }))
            await self.close()
            return

        # Extract the token from the Authorization header and get the sender user associated with the token
        token = headers[b"authorization"].decode("utf-8").split()[1]
        sender = await self.get_user_by_token(token)
        if sender is None:
            await self.close()
            return
        sender_id = int(sender.id)

        # Store the authenticated user's id to be used in the mark_message_as_read function
        self.auth_user = sender

        # Extract receiver ID from the WebSocket URL parameter
        receiver_id = int(self.scope['url_route']['kwargs']['receiver_id'])

        # Create a unique room group name using both sender and receiver IDs
        self.room_group_name = f"group_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"

        # Join the conversation group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

    # Handles disconnection from the messaging session.
    async def disconnect(self, close_code):
        if hasattr(self, 'notification_group'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Marks a message in the Live WebSocket conversation as read if the user reading the message is the receiver
    async def mark_message_as_read(self, unique_identifier):
        # Find the message by its unique identifier and mark it as read
        try:
            message_id = int(unique_identifier)
            message = await self.get_message(message_id)

            # Check the receiver of the notification is the authenticated user and the message is not read
            if message.receiver == self.auth_user and not message.is_read:
                message.is_read = True
                message.save()
        except (ValueError, Message.DoesNotExist):
            pass

    # Receives incoming messages from the WebSocket connection and relays the messages to other users in the same chat group.
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        content = text_data_json["content"]
        unique_identifier = text_data_json["unique_identifier"]

        # Update is_read status for the received message
        await self.mark_message_as_read(unique_identifier)

        # Send the received message to chat room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "content": content,
                "unique_identifier": unique_identifier,
            }
        )

    # Relays messages to users in the chat group and sends the message to the original consumer (WebSocket connection).
    async def chat_message(self, event):
        content = event["content"]
        unique_identifier = event["unique_identifier"]

        await self.send(text_data=json.dumps({
            "type": "message",
            "content": content,
            "unique_identifier": unique_identifier,
        }))

    # Send a WebSocket message to the client indicating that a message should be removed
    async def remove_message(self, event):
        unique_identifier = event["unique_identifier"]

        await self.send(text_data=json.dumps({
            "type": "remove_message",
            "unique_identifier": unique_identifier,
        }))
