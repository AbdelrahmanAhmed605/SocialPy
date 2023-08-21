from rest_framework import status
from rest_framework.response import Response

from django.db.models import F
from django.db import DatabaseError, IntegrityError

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.models import Notification


# Utility Function to calculate pagination indices for API views
def get_pagination_indeces(request, default_page_size):
    try:
        # Get the current page number from the request's query parameters
        page_number = int(request.query_params.get('page', 1))
        # Get the current page size from the request's query parameters
        page_size = int(request.query_params.get('page_size', default_page_size))
        if page_number <= 0 or page_size <= 0:
            return None, None, Response({"error": "Invalid page or page_size value"}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return None, None, Response({"error": "Invalid page or page_size value"}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate the slicing indeces from the page number and page size
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    return start_index, end_index, None

# Utility function to handle follow-related notifications
def notify_user(notification_recipient, notification_sender, notification_type, message):
    # Create a notification for the recipient of the notification action
    try:
        notification = Notification.objects.create(
            recipient=notification_recipient,
            sender=notification_sender,
            notification_type=notification_type
        )
    except (DatabaseError, IntegrityError):
        return Response({"error": "Error creating notification"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Notify the recipient via WebSocket about the new notification
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{notification_recipient.id}",
            {
                "type": "notification",
                "unique_identifier": str(notification.id),
                "notification_type": notification_type,
                "recipient": str(notification_recipient.id),
                "sender": str(notification_sender.id),
                "message": f"{notification_sender.username} {message}",
                "sender_profile_picture_url": notification_sender.profile_picture.url if notification_sender.profile_picture else None,
            }
        )
    except Exception as e:
        return Response({"error": "Error sending WebSocket notification"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Utility function to update follow counters
# following_user is the user being followed and follower_user is the user who is following
def update_follow_counters(following_user, follower_user):
    # Increment the num_followers counter for the user being followed (following_user) using Django F object
    following_user.num_followers = F('num_followers') + 1
    following_user.save()
    # Increment the num_following counter for the user attempting to follow (follower_user) using Django F object
    follower_user.num_following = F('num_following') + 1
    follower_user.save()

