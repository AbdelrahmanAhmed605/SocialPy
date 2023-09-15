from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException
from rest_framework.response import Response

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
        try:
            # Fetch all notifications for the user
            notifications = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
            return notifications
        except Exception as e:
            # Handle unexpected errors
            raise APIException()

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
        except APIException as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
