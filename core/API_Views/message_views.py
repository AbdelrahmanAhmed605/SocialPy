from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.models import Message, User
from core.serializers import MessageSerializer, UserSerializer


# Endpoint: api/messages/send/{receiver_id}
# API view to send a message to a user
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, receiver_id):
    sender = request.user
    content = request.data.get('content')

    # Ensures there is content within the message
    if not content:
        return Response({"error": "Message content is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Ensures the receiving user exists
    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return Response({"error": "Receiver not found"}, status=status.HTTP_404_NOT_FOUND)

    # Ensures the user is not sending a message to themselves
    if sender == receiver:
        return Response({"error": "Cannot send message to yourself"}, status=status.HTTP_400_BAD_REQUEST)

    # Creates the message
    message = Message(sender=sender, receiver=receiver, content=content, is_delivered=True)
    message.save()

    # Create a unique room group name using both sender and receiver IDs
    room_group_name = f"group_{min(sender.id, receiver.id)}_{max(sender.id, receiver.id)}"

    # Notify WebSocket group about the new message
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            "type": "chat.message",
            "content": content
        }
    )

    serializer = MessageSerializer(message)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


# Endpoint: api/messages/delete/{message_id}
# API view to unsend a message to a user
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    # Ensures the message being deleted exists
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({"error": "Message not found"}, status=status.HTTP_404_NOT_FOUND)

    # Checks to see if the message being deleted was sent by the requesting user
    if message.sender != request.user:
        raise PermissionDenied("You don't have permission to delete this message")

    message.delete()
    return Response({"message": "Message deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# Endpoint: /api/messages/conversation/{user_id}
# API view to get message conversation between 2 users
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation(request, user_id):
    # Obtain the user the request user has the conversation with
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "Receiver not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get all messages between the requesting user and the receiver
    # The Q object helps build complex queries using logical operators to filter database records based on multiple conditions
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
    ).order_by('-timestamp')

    # If the user accessing the conversation is the receiver, then set the unread messages to be seen
    messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    serializer = MessageSerializer(messages, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


# Endpoint: /api/messages/conversation-partners
# API view to get a list of all the user's we have had conversations with or apply a search query to narrow the search
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_and_search_conversation_partners(request):
    username = request.query_params.get('username')  # Get the username from the search query if applied

    # Get all unique users that the requesting user has had conversations with
    conversation_partners = User.objects.filter(
        Q(received_messages__sender=request.user) | Q(sent_messages__receiver=request.user)
    ).distinct()

    # Exclude the requesting user itself from the list
    conversation_partners = conversation_partners.exclude(id=request.user.id)

    # Check if a search query was applied to view for specific users
    if username:
        # Filter conversation partners by username query
        conversation_partners = conversation_partners.filter(username__icontains=username)

    serializer = UserSerializer(conversation_partners, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)
