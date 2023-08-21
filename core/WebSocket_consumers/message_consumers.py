import json
from channels.generic.websocket import AsyncWebsocketConsumer
from ..models import Message


# WebSocket consumer to handle live messaging between users
class MessageConsumer(AsyncWebsocketConsumer):

    # Initiates a WebSocket connection for live messaging.
    async def connect(self):
        # Extract sender and receiver IDs from the user and URL parameter
        sender = self.scope["user"]
        sender_id = sender.id

        receiver_id = self.scope['url_route']['kwargs']['receiver_id']

        # Create a unique room group name using both sender and receiver IDs
        self.room_group_name = f"group_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"

        # Join the conversation group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

    # Handles disconnection from the messaging session.
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Marks a message in the Live WebSocket conversation as read if the user reading the message is the receiver
    async def mark_message_as_read(self, unique_identifier):
        # Find the message by its unique identifier and mark it as read
        try:
            message_id = int(unique_identifier)
            message = Message.objects.get(id=message_id)
            if message.receiver == self.scope["user"] and not message.is_read:
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
                "type": "message",
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
