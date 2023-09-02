from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Notification
from core.serializers import NotificationSerializer
from .api_utility_functions import get_pagination_indeces


# Endpoint: /api/notifications/?page={}&page_size={}
# API view to get a users notifications
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    user = request.user

    # Set a default page size of 20 returned datasets per page
    default_page_size = 20
    # Utility function to get current page number and page size from the request's query parameters and calculate the pagination slicing indeces
    start_index, end_index, validation_response = get_pagination_indeces(request, default_page_size)
    if validation_response:
        return validation_response

    # Fetch all notifications for the user
    notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[start_index: end_index]

    # Serialize all notifications
    serializer = NotificationSerializer(notifications, many=True)

    return Response({
        "notifications": serializer.data,
    }, status=status.HTTP_200_OK)
