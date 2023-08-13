import json
from channels.generic.websocket import AsyncWebsocketConsumer


# WebSocket consumer to handle live messaging between users
class MessageConsumer(AsyncWebsocketConsumer):

    # Initiates a WebSocket connection for live messaging.
    async def connect(self):
        user = self.scope["user"]
        receiver_id = self.scope['url_route']['kwargs']['receiver_id']

        # Construct unique identifier for the messaging session.
        self.room_name = f"user_{receiver_id}"
        self.room_group_name = f"group_{self.room_name}"

        # Join the conversation group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

    # Handles disconnection from the messaging session.
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receives incoming messages from the WebSocket connection and relays the messages to other users in the same chat group.
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        content = text_data_json["content"]

        # Send the received message to chat room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "content": content
            }
        )

    # Relays messages to users in the chat group and sends the message to the original consumer (WebSocket connection).
    async def chat_message(self, event):
        content = event["content"]

        await self.send(text_data=json.dumps({
            "content": content
        }))
