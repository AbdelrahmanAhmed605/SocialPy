from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, APIException
from rest_framework.response import Response

# lets you directly manipulate database fields within database queries, leading to more efficient operations
from django.db.models import F
# Atomic transactions ensure that a series of database operations are completed together or not at all, maintaining data integrity.
from django.db import transaction

# Accessing Django Channels' channel layer for WebSocket integration
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.models import Post, Comment, Notification
from core.serializers import CommentSerializer, CommentSerializerMinimal
from core.Pagination_Classes.paginations import LargePagination
from .api_utility_functions import remove_notification


# Endpoint: /api/comment/post/{post_id}
# API view to create a comment on a specific post
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    content = request.data.get('content')

    if not content:
        return Response({"error": "Comment content is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Use an atomic transaction for creating the Comment instance, updating the comment counter,
        # creating a notification, and informing the WebSocket of the comment creation
        with transaction.atomic():
            # Create comment for the post
            comment = Comment.objects.create(user=request.user, post=post, content=content)
            serializer = CommentSerializerMinimal(comment)

            # Increment the counter for the comment count
            post.comment_count = F('comment_count') + 1
            post.save()  # Save the post to update the counter

            # Create a new_comment notification for the post author
            notification = Notification.objects.create(
                recipient=post.user,  # Author of the post
                sender=request.user,
                notification_type='new_comment',
                notification_post=post,
                notification_comment=comment
            )

            # Notify the post author via WebSocket about the new comment
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{post.user.id}",
                {
                    "type": "core.notification",
                    "unique_identifier": str(notification.id),
                    "notification_type": "new_comment",
                    "recipient": str(post.user.id),
                    "sender": str(request.user.id),
                    "message": f"{request.user.username} commented on your post",
                    "sender_profile_picture_url": request.user.profile_picture.url if request.user.profile_picture else None,
                    "post_media_url": post.media.url if post.media else None,
                }
            )
    except Exception as e:
        return Response({"error": "An error occurred while creating the comment"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


# Endpoint: /api/comment/{comment_id}/
# API view to delete a specific comment
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if the requesting user is the owner of the comment or the owner of the post
    if comment.user.id != request.user.id and comment.post.user.id != request.user.id:
        raise PermissionDenied("You don't have permission to delete this comment")

    try:
        # Use an atomic transaction for deleting the Comment instance, updating the comment counter,
        # deleting the comment notification, and informing the WebSocket of the deletion
        with transaction.atomic():
            # Decrement the counter for the comment count
            comment.post.comment_count = F('comment_count') - 1
            comment.post.save()  # Save the post to update the counter

            # Fetch the associated 'new_comment' notification
            notification = Notification.objects.filter(
                notification_comment_id=comment.id
            ).first()

            # Delete the comment
            comment.delete()

            # Check if the notification exists
            if notification:
                notification_id = str(notification.id)  # Store the ID for WebSocket use
                notification.delete()

                # Remove the notification for the post author via WebSocket
                remove_notification(comment.post.user.id, notification_id)
    except Exception as e:
        return Response({"error": "An error occurred while deleting the comment"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Comment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# Endpoint: /api/comments/post/{post_id}/?page={}&page_size={}
# API view to view all the comments for a specific post
class PostCommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    pagination_class = LargePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        try:
            post = Post.objects.only('id').get(id=post_id)
        except Post.DoesNotExist:
            raise APIException(detail={"error": "Post not found"}, code=status.HTTP_404_NOT_FOUND)

        try:
            # Access comments for the specified post using the related_name
            comments = post.post_comments.all()
            return comments
        except Exception as e:
            # Handle other unexpected errors
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