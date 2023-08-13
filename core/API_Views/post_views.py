from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import Post, Comment, Notification
from core.serializers import PostSerializer


# Endpoint: List Posts: GET /api/posts/
# Endpoint: Create Post: POST /api/posts/
# Custom view for listing and creating posts
class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can create posts

    def perform_create(self, serializer):
        hashtag_names = serializer.validated_data.pop('hashtags', [])  # Extract hashtag names from validated data

        # create_hashtags is a function in the serializer that either creates or retrieves corresponding hashtags
        hashtags = serializer.create_hashtags(hashtag_names)

        instance = serializer.save(user=self.request.user)  # Set the user of the post
        instance.hashtags.set(hashtags)  # Set hashtags after the instance is saved


# Endpoint: Retrieve Post: GET /api/posts/{post_id}/
# Endpoint: Update Post: PATCH /api/posts/{post_id}/ (PATCH not PUT since we allow partial updates)
# Endpoint: Delete Post: DELETE /api/posts/{post_id}/
# Custom view for retrieving, updating, and deleting a post
class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    # Override the serializer context to include the request object
    # This is done due to custom logic in the PostSerializer that requires the request data (get_liked_by_user function)
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    # Custom logic for updating a post
    def perform_update(self, serializer):
        post = serializer.instance  # Get the existing post instance
        if post.user != self.request.user:
            raise PermissionDenied("You don't have permission to update this post.")

        # Save the updated post
        serializer.save(partial=True)

    # Custom logic for deleting a post
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You don't have permission to delete this post.")

        # Delete the associated comments first
        comments = Comment.objects.filter(post=instance)
        comments.delete()

        instance.delete()


# Endpoint: /api/post/{post_id}/like/
# API view to allow users to like a specific post
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.user in post.likes.all():
        return Response({"error": "You already liked this post"}, status=status.HTTP_400_BAD_REQUEST)

    post.likes.add(request.user)

    # Create a notification for the liked post
    Notification.objects.create(
        recipient=post.user,
        sender=request.user,
        notification_type='new_like',
        notification_post=post
    )

    return Response({"message": "Post liked successfully"}, status=status.HTTP_200_OK)


# Endpoint: /api/post/{post_id}/unlike/
# API view to allow users to remove their like from a specific post
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlike_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.user not in post.likes.all():
        return Response({"error": "You haven't liked this post"}, status=status.HTTP_400_BAD_REQUEST)

    # Remove the like
    post.likes.remove(request.user)

    # Delete the corresponding 'new_like' notification
    Notification.objects.filter(
        recipient=post.user,
        sender=request.user,
        notification_type='new_like',
        notification_post=post
    ).delete()

    return Response({"message": "Post unliked successfully"}, status=status.HTTP_200_OK)


# Endpoint: /api/hashtag/posts
# API view to allow users to search for posts by a specific hashtag
@api_view(['GET'])
def search_hashtags(request):
    hashtag = request.query_params.get('hashtag')  # Get the search query from query parameters

    if not hashtag:
        return Response({"error": "Please provide a hashtag query parameter"}, status=status.HTTP_400_BAD_REQUEST)

    # Search for posts with the specified hashtag and a public visibility
    matched_posts = Post.objects.filter(hashtags__name=hashtag, visibility='public')

    serializer = PostSerializer(matched_posts, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


# Endpoint: /api/explore/posts
# API view to allow users to have an explore page (see posts created by public accounts)
@api_view(['GET'])
def explore_page(request):
    # If the user is authenticated, then show posts of public users they do not follow
    if request.user.is_authenticated:
        following_users = request.user.following.all()
        explore_posts = Post.objects.filter(visibility='public').exclude(user__in=following_users)
        serializer = PostSerializer(explore_posts, many=True, context={'request': request})

    else:
        # If the user is not authenticated, then show posts of public users
        explore_posts = Post.objects.filter(visibility='public')
        serializer = PostSerializer(explore_posts, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)
