from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Post, Comment, Notification
from .serializers import CommentSerializer


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

    # Create a notification for the post author
    Notification.objects.create(
        recipient=post.user,  # Author of the post
        sender=request.user,
        notification_type='new_comment',
        notification_post=post,
        notification_comment=comment
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
    return Response({"message": "Comment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# Endpoint: /api/comments/post/{post_id}/
# API view to view all the comments for a specific post
@api_view(['GET'])
def get_post_comments(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    comments = post.post_comments.all()  # Access comments using the related_name
    serializer = CommentSerializer(comments, many=True, context={'request': request})

    return Response(serializer.data, status=status.HTTP_200_OK)
