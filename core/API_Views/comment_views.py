from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.models import Post, Comment, Notification
from core.serializers import CommentSerializer


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

    comment = Comment.objects.create(user=request.user, post=post, content=content)
    serializer = CommentSerializer(comment)

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
            "type": "notification",
            "unique_identifier": str(notification.id),
            "notification_type": "new_comment",
            "recipient": str(post.user.id),
            "sender": str(request.user.id),
            "message": f"{request.user.username} commented on your post",
            "sender_profile_picture_url": request.user.profile_picture.url if request.user.profile_picture else None,
            "post_media_url": post.media.url if post.media else None,
        }
    )

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
    if comment.user != request.user and comment.post.user != request.user:
        raise PermissionDenied("You don't have permission to delete this comment")

    comment.delete()

    # Fetch the associated 'new_comment' notification
    notification = Notification.objects.filter(
        recipient=comment.post.user,
        sender=request.user,
        notification_type='new_comment',
        notification_post=comment.post
    ).first()

    # Check if the notification exists
    if notification:
        notification_id = str(notification.id)  # Store the ID for WebSocket use
        notification.delete()

        # Remove the notification for the post author via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{comment.post.user.id}",
            {
                "type": "remove_notification",
                "unique_identifier": notification_id
            }
        )

    return Response({"message": "Comment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# Endpoint: /api/comments/post/{post_id}/?page={}&page_size={}
# API view to view all the comments for a specific post
@api_view(['GET'])
def get_post_comments(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get the current page number from the request's query parameters
    page_number = int(request.query_params.get('page', 1))  # Defaults to the first page

    # Get the page size from the request's query parameters
    page_size = int(request.query_params.get('page_size', 20))  # Default page size is 20

    # Calculate the starting and ending index for slicing
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size

    # Access comments for the specified post using the related_name
    comments = post.post_comments[start_index:end_index]
    serializer = CommentSerializer(comments, many=True, context={'request': request})

    return Response(serializer.data, status=status.HTTP_200_OK)
