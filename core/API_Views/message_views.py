from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Q object helps build complex queries using logical operators to filter database records based on multiple conditions
from django.db.models import Q, Max, Case, When, F, DateTimeField
# Atomic transactions ensure that a series of database operations are completed together or not at all, maintaining data integrity.
from django.db import transaction
from django.core.exceptions import PermissionDenied
# Get the User model configured for this Django project
from django.contrib.auth import get_user_model

# Accessing Django Channels' channel layer for WebSocket integration
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.models import Message
from core.serializers import MessageSerializer, UserSerializer, FollowSerializerMinimal
from core.Pagination_Classes.paginations import LargePagination


# Get the User model configured for this Django project
User = get_user_model()


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
            # Create the message
            message = Message.objects.create(sender=sender, receiver=receiver, content=content, is_delivered=True)

            # Notify WebSocket group about the new message
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    "type": "chat.message",
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


# Endpoint: /api/messages/conversation/{user_id}/?page={}
# API view to get message conversation between 2 users
class ConversationListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    pagination_class = LargePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']

        try:
            user = User.objects.only('id').get(id=user_id)
        except User.DoesNotExist:
            raise APIException(detail={"error": "User not found"}, code=status.HTTP_404_NOT_FOUND)

        try:
            # Fetch all messages between the requesting user and the receiver
            messages = Message.objects.filter(
                Q(sender_id=self.request.user.id, receiver_id=user.id) | Q(sender_id=user.id, receiver_id=self.request.user.id)
            )

            # Update unread messages sent by `user` since the `requesting user` has viewed them after calling this API
            Message.objects.filter(sender_id=user.id, receiver_id=self.request.user.id, is_read=False).update(is_read=True)

            return messages
        except Exception as e:
            # Handle unexpected errors
            raise APIException(detail={"error": "An unexpected error occurred: " + str(e)},
                               code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_most_recent_sender_status(self, queryset):
        # Get the most recent message in the conversation
        most_recent_message = queryset.first()

        # Determine the status of the most recent message for the sender
        # (so the sender of the last message can see if their message was sent or is still delivered)
        most_recent_sender_status = None
        if most_recent_message and most_recent_message.sender.id == self.request.user.id:
            most_recent_sender_status = {
                "id": most_recent_message.id,
                "is_read": most_recent_message.is_read
            }

        return most_recent_sender_status

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
        except APIException as e:
            # Re-raise the APIException with the appropriate error message
            raise e

        # Get the messages between the 2 users
        messages = queryset
        # Paginate the messages to only fetch paginated data from the database
        paginated_messages = self.paginate_queryset(messages)

        serializer = self.get_serializer(paginated_messages, many=True)

        most_recent_sender_status = self.get_most_recent_sender_status(messages)

        # Return the paginated data along with the status of the most recent message for the sender of the last message
        response_data = {
            "most_recent_sender_status": most_recent_sender_status,
            "messages": serializer.data
        }

        return self.get_paginated_response(response_data)

# Endpoint: /api/messages/conversation-partners/?username={}&page={}
# API view to get a list of all the user's we have had conversations with or apply a search query to narrow the search
class ConversationPartnerListView(generics.ListAPIView):
    serializer_class = FollowSerializerMinimal
    pagination_class = LargePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        username = self.request.query_params.get('username')  # Get the username from the search query if applied

        try:
            # Get all users that sent a message to the requesting user or received a message from the requesting user
            # last_interaction annotated field used to order the Users by their most recent interaction with the requesting user
            conversation_partners = User.objects.only('id', 'username', 'profile_picture').filter(
                Q(received_messages__sender_id=self.request.user.id) | Q(sent_messages__receiver_id=self.request.user.id)
            ).annotate(
                last_received=Max('received_messages__created_at'),
                last_sent=Max('sent_messages__created_at')
            ).annotate(
                last_interaction=Case(
                    When(last_received__gt=F('last_sent'), then=F('last_received')),
                    default=F('last_sent'),
                    output_field=DateTimeField()
                )
            ).distinct().exclude(id=self.request.user.id).order_by('-last_interaction')

            # Check if a search query was applied to view for specific users from the result query
            if username:
                # Filter conversation partners by username query
                conversation_partners = conversation_partners.filter(username__icontains=username)

            return conversation_partners
        except Exception as e:
            # Handle unexpected errors
            raise APIException(detail={"error": "An unexpected error occurred: " + str(e)},
                               code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
        except APIException as e:
            # Re-raise the APIException with the appropriate error message
            raise e

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)