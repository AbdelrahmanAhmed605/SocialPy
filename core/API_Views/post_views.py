from rest_framework import generics, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

# Q object helps build complex queries using logical operators to filter database records based on multiple conditions
from django.db.models import Q
# lets you directly manipulate database fields within database queries, leading to more efficient operations
from django.db.models import F
# Atomic transactions ensure that a series of database operations are completed together or not at all, maintaining data integrity.
from django.db import transaction, DatabaseError
# Managing file uploads and storage
from django.core.files.storage import default_storage

# Accessing Django Channels' channel layer for WebSocket integration
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.models import Post, Notification, Hashtag
from core.serializers import PostSerializer, PostSerializerMinimal,HashtagSerializer, FollowSerializer
from .api_utility_functions import create_hashtags
from core.Pagination_Classes.paginations import LargePagination, SmallPagination


# Endpoint: List Posts: GET /api/posts/
# Endpoint: Create Post: POST /api/posts/
# Custom view for listing and creating posts
class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all()  # Retrieves all the users from the database
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can create posts
    parser_classes = [MultiPartParser]
    pagination_class = LargePagination

    # Set the user field of the serializer to the authenticated user
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # Custom logic for creating a post
    def create(self, request, *args, **kwargs):
        hashtag_names = []
        index = 0
        while f'hashtags_{index}' in request.data:
            hashtag_name = request.data[f'hashtags_{index}']
            hashtag_names.append(hashtag_name)
            index += 1

        # Remove empty hashtags from the data and strip whitespaces from non-empty hashtags
        cleaned_hashtags = [tag.strip() for tag in hashtag_names if tag.strip()]
        # create_hashtags is a utility function that retrieves or creates provided hashtags (to ensure no duplicate hashtags are made)
        hashtag_ids = create_hashtags(cleaned_hashtags)

        request.data.setlist('hashtags', hashtag_ids)

        # Check the requesting user's profile_privacy
        user_profile_privacy = request.user.profile_privacy
        # Set the visibility based on user's profile_privacy (it is already set to public by default)
        if user_profile_privacy == 'private':
            request.data['visibility'] = 'private'

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Increment the num_posts counter for the user using the Django F object
        request.user.num_posts = F('num_posts') + 1
        request.user.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# Endpoint: Retrieve Post: GET /api/posts/{post_id}/
# Endpoint: Update Post: PATCH /api/posts/{post_id}/ (PATCH not PUT since we allow partial updates)
# Endpoint: Delete Post: DELETE /api/posts/{post_id}/
# Custom view for retrieving, updating, and deleting a post
class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    # Override the serializer context to include the request object
    # This is done due to custom logic in the PostSerializer that requires the request data (get_liked_by_user function)
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    # Modify the "hashtags" field when retrieving a post to show the actual hashtag names instead of the primary key id
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Modify the 'hashtags' data in the serialized representation
        modified_data = serializer.data.copy()
        modified_data['hashtags'] = [hashtag.name for hashtag in instance.hashtags.all()]

        return Response(modified_data)

    # Custom logic for updating a post
    def update(self, request, *args, **kwargs):
        instance = self.get_object()  # Get the existing post instance

        # Ensure that the author of the post is the one updating it
        if instance.user != self.request.user:
            raise PermissionDenied("You don't have permission to update this post.")

        old_media = instance.media
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        hashtag_names = []
        index = 0
        while f'hashtags_{index}' in request.data:
            hashtag_name = request.data[f'hashtags_{index}']
            hashtag_names.append(hashtag_name)
            index += 1

        if hashtag_names:
            cleaned_hashtags = [tag.strip() for tag in hashtag_names]
            hashtag_ids = create_hashtags(cleaned_hashtags)
            # Update the post instance with the processed list of hashtags
            instance.hashtags.set(hashtag_ids)

        # Delete the old media from the AWS S3 bucket if the user is updating it
        new_media = serializer.validated_data.get('media')
        if new_media and old_media:
            default_storage.delete(old_media.name)

        self.perform_update(serializer)

        return Response(serializer.data)

    # Custom logic for deleting a post
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You don't have permission to delete this post.")

        default_storage.delete(instance.media.name)

        instance.delete()

        # Decrement the num_posts counter for the user using F object
        self.request.user.num_posts = F('num_posts') - 1
        self.request.user.save()  # Save the user object with the updated counter


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

    try:
        # Use an atomic transaction for adding the users like to the post instance, updating the like counter,
        # creating the like notification, and informing the WebSocket of the like
        with transaction.atomic():
            # Create the like relationship between the requesting user and the post
            post.likes.add(request.user)

            # Increment the counter for the like count
            post.like_count = F('like_count') + 1
            post.save()  # Save the post to update the counter

            # Create a new_like notification for the post author
            notification = Notification.objects.create(
                recipient=post.user,
                sender=request.user,
                notification_type='new_like',
                notification_post=post
            )

            # Notify the post author via WebSocket about the new like
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{post.user.id}",
                {
                    "type": "core.notification",
                    "unique_identifier": str(notification.id),
                    "notification_type": "new_like",
                    "recipient": str(post.user.id),
                    "sender": str(request.user.id),
                    "message": f"{request.user.username} liked your post",
                    "sender_profile_picture_url": request.user.profile_picture.url if request.user.profile_picture else None,
                    "post_media_url": post.media.url if post.media else None,
                }
            )
    except Exception as e:
        return Response({"error": "An error occurred while liking the post"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Post liked successfully"}, status=status.HTTP_200_OK)


# Endpoint: /api/post/{post_id}/unlike/
# API view to allow users to remove their like from a specific post
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlike_post(request, post_id):
    try:
        post = Post.objects.only('id', 'likes', 'user__id').get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.user not in post.likes.all():
        return Response({"error": "You haven't liked this post"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Use an atomic transaction for removing the users like from the post instance, updating the like counter,
        # deleting the like notification, and informing the WebSocket of the unlike
        with transaction.atomic():
            # Remove the like
            post.likes.remove(request.user)

            # Decrement the counter for the like count
            post.like_count = F('like_count') - 1
            post.save()  # Save the post to update the counter

            # Find the corresponding 'new_like' notification
            notification = Notification.objects.filter(
                recipient_id=post.user_id,
                sender=request.user,
                notification_type='new_like',
                notification_post_id=post.id
            ).first()

            # Check if the notification exists
            if notification:
                notification_id = str(notification.id)  # Store the ID for WebSocket use
                notification.delete()  # Delete the notification

                # Remove the notification for the post author via WebSocket
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"notifications_{post.user_id}",
                    {
                        "type": "remove_notification",
                        "unique_identifier": notification_id
                    }
                )
    except Exception as e:
        return Response({"error": "An error occurred while liking the post"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Post unliked successfully"}, status=status.HTTP_200_OK)


# Endpoint: /api/hashtags/?hashtag={}&page={}
# API view to allow users to find hashtag names that are similar to the one in the search query
class SuggestHashtagsView(generics.ListAPIView):
    serializer_class = HashtagSerializer
    pagination_class = SmallPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        hashtag = self.request.query_params.get('hashtag')  # Get the search query from query parameters

        if not hashtag:
            return Hashtag.objects.none()

        try:
            # Search for hashtag names that are similar to the provided search query
            suggested_hashtags = Hashtag.objects.filter(name__icontains=hashtag)
            return suggested_hashtags
        except DatabaseError as e:
            # Handle database-related errors
            return Response({"error": f"Database error: {str(e)}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # Handle other unexpected errors
            return Response({"error": "An unexpected error occurred: " + str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Endpoint: /api/hashtag/{hashtag_id}/posts/?page={}
# API view to allow users to search for posts by a specific hashtag
class SearchHashtagPostsView(generics.ListAPIView):
    serializer_class = PostSerializerMinimal
    pagination_class = LargePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        hashtag_id = self.kwargs['hashtag_id']
        try:
            hashtag = Hashtag.objects.get(id=hashtag_id)
        except Hashtag.DoesNotExist:
            return Response({"error": "Hashtag not found"}, status=status.HTTP_404_NOT_FOUND)

        # Search for paginated posts with the specified hashtag and a public visibility
        matched_posts = Post.objects.filter(hashtags=hashtag, visibility='public').only('id', 'media')

        return matched_posts

# Endpoint: /api/explore/posts/?page={}
# API view to allow users view their explore page (posts created by public accounts the requesting user does not follow)
class ExplorePageView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = LargePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # user__follower__follower=self.request.user excludes posts made by authors the requesting user is following
        explore_posts = Post.objects.filter(visibility='public').exclude(
            Q(user__follower__follower=self.request.user) | Q(user=self.request.user)
        )
        return explore_posts

# Endpoint: /api/post/{post_id}/likers/?page={}
# API view to get a list of all the users who liked a post
class PostLikersView(generics.ListAPIView):
    serializer_class = FollowSerializer
    pagination_class = LargePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            post = Post.objects.get(id=self.kwargs['post_id'])
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        users = post.likes.only('id', 'username', 'profile_picture')

        return users
