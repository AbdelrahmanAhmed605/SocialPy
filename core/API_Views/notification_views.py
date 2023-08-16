from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Notification
from core.serializers import NotificationSerializer


# Endpoint: /api/notifications
# Get all of a user's notifications, separated into unread and read
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    user = request.user

    # Get the current page number from the request's query parameters
    page_number = int(request.query_params.get('page', 1))  # Defaults to the first page

    # Get the page size from the request's query parameters
    page_size = int(request.query_params.get('page_size', 20))  # Default page size is 20

    # Get the last unread page number from the session if available
    # This denotes the last page_number that contained unread notifications
    last_unread_page = request.session.get('last_unread_page', 0)

    # Calculate the starting and ending index for slicing
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size

    # Get paginated list of most recent unread notifications
    unread_notifications = Notification.objects.filter(recipient=user, is_read=False)[start_index:end_index]

    # Check if there are any unread notifications left, since we want to display all unread notifications
    # before we start displaying read notifications
    if not unread_notifications:
        # Calculate read_start_index based on last_unread_page
        read_start_index = start_index - (last_unread_page * page_size)
        read_end_index = read_start_index + page_size

        # Get paginated list of read notifications
        read_notifications = Notification.objects.filter(recipient=user, is_read=True)[read_start_index:read_end_index]

        read_serializer = NotificationSerializer(read_notifications, many=True)

        return Response({
            "read_notifications": read_serializer.data,
            "unread_notifications": []
        }, status=status.HTTP_200_OK)

    unread_serializer = NotificationSerializer(unread_notifications, many=True)

    # Mark unread notifications as read
    unread_notifications.update(is_read=True)

    # Update last_unread_page when there are unread notifications
    last_unread_page = page_number

    # Store the updated last_unread_page in the session
    request.session['last_unread_page'] = last_unread_page

    return Response({
        "read_notifications": [],
        "unread_notifications": unread_serializer.data
    }, status=status.HTTP_200_OK)
