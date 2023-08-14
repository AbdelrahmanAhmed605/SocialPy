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

    # Separate unread and read notifications
    unread_notifications = Notification.objects.filter(recipient=user, is_read=False).order_by('-created_at')
    read_notifications = Notification.objects.filter(recipient=user, is_read=True).order_by('-created_at')

    # Mark unread notifications as read
    unread_notifications.update(is_read=True)

    unread_serializer = NotificationSerializer(unread_notifications, many=True)
    read_serializer = NotificationSerializer(read_notifications, many=True)

    return Response({
        "unread_notifications": unread_serializer.data,
        "read_notifications": read_serializer.data
    }, status=status.HTTP_200_OK)
