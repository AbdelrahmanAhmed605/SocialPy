from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Q object helps build complex queries using logical operators to filter database records based on multiple conditions
from django.db.models import Q, Max
# Atomic transactions ensure that a series of database operations are completed together or not at all, maintaining data integrity.
from django.db import transaction
from django.core.exceptions import PermissionDenied

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.models import Message, User
from core.serializers import MessageSerializer, UserSerializer
from .api_utility_functions import get_pagination_indeces


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

    # Create a unique room group name using both sender and receiver IDs
    room_group_name = f"group_{min(sender.id, receiver.id)}_{max(sender.id, receiver.id)}"

    try:
        # Use an atomic transaction for creating the Message instance, and informing the WebSocket of the new message
        with transaction.atomic():
            # Creates the message
            message = Message(sender=sender, receiver=receiver, content=content, is_delivered=True)
            message.save()

            # Notify WebSocket group about the new message
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    "type": "message",
                    "content": content,
                    "unique_identifier": str(message.id)  # Use message's ID as unique_identifier
                }
            )
    except Exception as e:
        return Response({"error": "An error occurred while sending the message"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    # Store the unique_identifier before deleting the message
    unique_identifier = str(message.id)

    # Determine the appropriate room_group_name based on sender and receiver IDs
    room_group_name = f"group_{min(message.sender.id, message.receiver.id)}_{max(message.sender.id, message.receiver.id)}"

    try:
        # Use an atomic transaction for deleting the Message instance, and informing the WebSocket of the deletion
        with transaction.atomic():
            # Delete the message
            message.delete()

            # Notify WebSocket consumer to remove the message from UI
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    "type": "remove_message",
                    "unique_identifier": unique_identifier,
                }
            )
    except Exception as e:
        return Response({"error": "An error occurred while unsending the message"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Message deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# Endpoint: /api/messages/conversation/{user_id}/?page={}&page_size={}
# API view to get message conversation between 2 users
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation(request, user_id):
    # Obtain the user the requesting user has the conversation with
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Set a default page size of 20 returned datasets per page
    default_page_size = 20
    # Utility function to get current page number and page size from the request's query parameters and calculate the pagination slicing indeces
    start_index, end_index, validation_response = get_pagination_indeces(request, default_page_size)
    if validation_response:
        return validation_response

    # Get paginated list of read messages between the requesting user and the receiver
    read_messages = Message.objects.filter(
        Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user), is_read=True
    )[start_index:end_index]

    # Get all unread messages between the requesting user and the receiver
    unread_messages = Message.objects.filter(
        Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user), is_read=False
    )

    read_serializer = MessageSerializer(read_messages, many=True)
    unread_serializer = MessageSerializer(unread_messages, many=True)

    # If the user accessing the conversation is the receiver, then set the unread messages to be seen
    unread_messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    return Response({
        "read_messages": read_serializer.data,
        "unread_messages": unread_serializer.data
    }, status=status.HTTP_200_OK)


# Endpoint: /api/messages/conversation-partners/?username={}&page={}&page_size={}
# API view to get a list of all the user's we have had conversations with or apply a search query to narrow the search
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_and_search_conversation_partners(request):
    username = request.query_params.get('username')  # Get the username from the search query if applied

    # Get the pagination slicing indeces
    default_page_size = 20
    start_index, end_index, validation_response = get_pagination_indeces(request, default_page_size)
    if validation_response:
        return validation_response

    # Check if a search query was applied to view for specific users
    # last_interaction annotated field used to order the Users by their most recent interaction with the requesting user
    if username:
        # Filter conversation partners by username query
        conversation_partners = User.objects.filter(
            Q(received_messages__sender=request.user) | Q(sent_messages__receiver=request.user),
            username__icontains=username
        ).annotate(
            last_interaction=Max('received_messages__created_at', 'sent_messages__created_at')
        ).distinct().exclude(id=request.user.id).order_by('-last_interaction')[start_index:end_index]

    else:
        # Get a paginated list of unique users that the requesting user has had conversations with
        conversation_partners = User.objects.filter(
            Q(received_messages__sender=request.user) | Q(sent_messages__receiver=request.user)
        ).annotate(
            last_interaction=Max('received_messages__created_at', 'sent_messages__created_at')
        ).distinct().exclude(id=request.user.id).order_by('-last_interaction')[start_index:end_index]

    serializer = UserSerializer(conversation_partners, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)
