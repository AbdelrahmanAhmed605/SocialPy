from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from core.models import Notification
from core.serializers import NotificationSerializer
from core.Pagination_Classes.paginations import LargePagination


# Endpoint: /api/notifications/?page={}
# API view to get a users notifications
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = LargePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Fetch all notifications for the user
        notifications = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
        return notifications
