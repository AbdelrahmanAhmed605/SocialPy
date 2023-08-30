from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Notification
from core.serializers import NotificationSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    user = request.user

    # Get the current page number from the request's query parameters
    page_number = int(request.query_params.get('page', 1))  # Defaults to the first page
    # Get the page size from the request's query parameters
    page_size = int(request.query_params.get('page_size', 20))  # Default page size is 20

    # To seamlessly transition from unread to read notifications in infinite scrolling,
    # we use last_unread_page as a reference to switch to the first page of read notifications.
    last_unread_page = request.session.get('last_unread_page', 0)

    # Initialize the start and end index for fetching unread notifications.
    # This is fixed because the data is being updated; as the user keeps calling the API,
    # the first set of notifications are not the same since some get marked as read.
    start_index = 0
    end_index = 20

    # Get IDs of paginated unread notifications
    unread_notification_ids = (
        Notification.objects.filter(recipient=user, is_read=False)
        .values_list('id', flat=True)[start_index:end_index]
    )
    # Convert unread notification IDs to a list to prevent database changes affecting the original queryset.
    # This is needed because later operations update the notifications' read status and change the queryset
    unread_notification_ids_list = list(unread_notification_ids)

    if not unread_notification_ids_list:
        # Calculate start and end indices for read notifications.
        start_index = (page_number - 1) * page_size
        ''' # To begin displaying read notifications after scrolling through unread ones, we use the equation 
        `start_index - (last_unread_page * page_size)` to reset the pagination of read notifications since we want
        to start from page 1 but the query parameter is not at page 1.
        For page refreshes, the page number is reset to 1. If all notifications are read, then we can use start_index 
        to track the current read page. max() guarantees consistent handling for both scenarios.
        '''
        read_start_index = max(start_index, start_index - (last_unread_page * page_size))
        read_end_index = read_start_index + page_size

        # Fetch paginated read notifications
        read_notifications = Notification.objects.filter(recipient=user, is_read=True)[read_start_index:read_end_index]
        read_serializer = NotificationSerializer(read_notifications, many=True)

        return Response({
            "unread_notifications": [],
            "read_notifications": read_serializer.data
        }, status=status.HTTP_200_OK)

    # Mark unread notifications as read using a single update query
    Notification.objects.filter(id__in=unread_notification_ids_list).update(is_read=True)

    # Fetch serialized unread notifications
    unread_notifications = Notification.objects.filter(id__in=unread_notification_ids_list)
    unread_serializer = NotificationSerializer(unread_notifications, many=True)

    # Update last_unread_page with the current page number for future reference
    last_unread_page = page_number
    request.session['last_unread_page'] = last_unread_page

    return Response({
        "unread_notifications": unread_serializer.data,
        "read_notifications": []
    }, status=status.HTTP_200_OK)
