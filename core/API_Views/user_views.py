from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser

from django.db import transaction
from django.core.files.storage import default_storage

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.models import User, Post, Follow, Notification
from core.serializers import UserSerializer, PostSerializer, FollowSerializer
from core.Custom_Permission_Classes.checkOwner import IsOwnerOrReadOnly
from .api_utility_functions import get_pagination_indeces, update_follow_counters, notify_user


# Endpoint: List Users: GET /api/users/
# Endpoint: Create User: POST /api/users/
# Custom view for listing and creating users
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()  # Retrieves all the users from the database
    serializer_class = UserSerializer  # Specifies serializer class to use for serializing and deserializing user data
    permission_classes = [AllowAny]  # Allow anyone to view the list and create new users
    parser_classes = [MultiPartParser]

    # Overriding create method to perform custom logic
    def create(self, request, *args, **kwargs):
        # Serializes incoming data and ensures the data is valid
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check for duplicate username and email before creating the user
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")

        # Remove additional fields added by default serializer
        additional_fields = ['is_superuser', 'is_staff', 'is_active', 'groups', 'user_permissions']
        for field in additional_fields:
            serializer.validated_data.pop(field, None)

        # Obtain the password from the validated data to be hashed
        password = serializer.validated_data['password']
        # Create the user instance using all fields from request data
        user = User(**serializer.validated_data)
        user.set_password(password)  # Hash the password
        user.save()

        # Save the serializer after creating the user
        serializer.instance = user
        headers = self.get_success_headers(serializer.data)

        # Generate or get the token for the user
        token = Token.objects.create(user=user)

        # Add the token data to the response
        response_data = serializer.data
        response_data['token'] = token.key

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


# Endpoint: Retrieve User: GET /api/users/{user_id}/
# Endpoint: Update User: PATCH /api/users/{user_id}/ (PATCH not PUT since we allow partial updates)
# Endpoint: Delete User: DELETE /api/users/{user_id}/
# Custom view for retrieving, updating, and deleting a user
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated,
                          IsOwnerOrReadOnly]  # Allow only authenticated users to make changes to their own account
    parser_classes = [MultiPartParser]

    # Overriding perform_update method to perform custom logic
    def perform_update(self, serializer):
        instance = serializer.instance

        # .get() used to return None instead of a KeyError if username/email are not present (since it is partial data)
        new_username = serializer.validated_data.get('username')
        new_email = serializer.validated_data.get('email')

        # Check for duplicate username and email before updating the user
        if new_username and User.objects.exclude(pk=instance.pk).filter(username=new_username).exists():
            raise ValidationError("Username already exists.")
        if new_email and User.objects.exclude(pk=instance.pk).filter(email=new_email).exists():
            raise ValidationError("Email already exists.")

        new_profile_picture = serializer.validated_data.get('profile_picture')

        # Delete the old profile picture from the AWS S3 bucket if the user is updating it
        if new_profile_picture and instance.profile_picture:
            default_storage.delete(instance.profile_picture.name)

        # Perform the update
        serializer.save(partial=True)

    # Custom logic for deleting a post
    def perform_destroy(self, instance):
        # Delete the profile picture associated with the user from the AWS S3 Bucket
        default_storage.delete(instance.profile_picture.name)
        instance.delete()


# Endpoint: /api/login/
# API view to allow users to log in and get authentication token
@api_view(['POST'])
@permission_classes([AllowAny])  # Allow any user to access this view
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    # Find a user with the provided username and use Django's built-in AbstractUser check_password method to see if the
    # provided password matches the hashed password store in the database for the specific user
    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            # Create or get existing token for the user
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)


# Endpoint: /api/logout/
# API view to allow users to log out and delete their authentication token
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    # Delete the user's authentication token
    request.user.auth_token.delete()
    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


# Endpoint: /api/feed/?page={}&page_size={}
# API view to get posts from the users that the current user follows
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_feed(request):
    # Obtains all the users the requesting user is following
    following_users = User.objects.filter(follower__follower=request.user, follower__follow_status='accepted')

    # Set a default page size of 20 returned datasets per page
    default_page_size = 20
    # Utility function to get current page number and page size from the request's query parameters and calculate the pagination slicing indeces
    start_index, end_index, validation_response = get_pagination_indeces(request, default_page_size)
    if validation_response:
        return validation_response

    # fetch the posts from the users in following_users
    feed_posts = Post.objects.filter(user__in=following_users)[start_index:end_index]

    # The context is used to pass the request to the PostSerializer to perform custom logic
    serializer = PostSerializer(feed_posts, many=True, context={'request': request})

    return Response(serializer.data, status=status.HTTP_200_OK)


# Endpoint: /api/user/profile/{user_id}/?page={}&page_size={}
# API view to get a users profile and its information
@api_view(['GET'])
def user_profile(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    default_page_size = 20
    start_index, end_index, validation_response = get_pagination_indeces(request, default_page_size)
    if validation_response:
        return validation_response

    follow_status = False  # Keeps track of the requesting user's follow relationship to the user they are viewing
    can_view = True  # Keeps track of whether the requesting user can view this user's profile or not

    if request.user.is_authenticated:
        follow_instance = request.user.following.filter(following=user).first()
        if follow_instance:
            follow_status = follow_instance.follow_status
        elif request.user.id == user_id:
            follow_status = "self"

    if user.profile_privacy == 'private' and (follow_status is False or follow_status == 'pending'):
        can_view = False

    users_posts = Post.objects.filter(user=user)[start_index:end_index]
    serializer = PostSerializer(users_posts, many=True, context={'request': request})

    response_data = {
        'username': user.username,
        'profile_picture': user.profile_picture.url if user.profile_picture else None,
        'bio': user.bio,
        'contact_information': user.contact_information,
        'follow_status': follow_status,
        'can_view': can_view,
        'posts': serializer.data if can_view else None,
        'num_followers': user.num_followers,
        'num_following': user.num_following,
        'num_posts': user.num_posts,
    }

    return Response(response_data, status=status.HTTP_200_OK)


# Endpoint: /api/user/change_profile_privacy/
# API view to change a user's profile privacy setting
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_profile_privacy(request):
    new_privacy = request.data.get('profile_privacy')
    if new_privacy not in ['public', 'private']:
        return Response({'error': 'Invalid profile_privacy value'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    old_privacy = user.profile_privacy

    # Update the user's profile privacy
    user.profile_privacy = new_privacy
    user.save()

    # Update visibility of the user's posts
    if new_privacy != old_privacy:
        user.user_posts.filter(visibility=old_privacy).update(visibility=new_privacy)

    # If user changes profile to public, accept all pending follow requests
    if new_privacy == 'public':
        pending_follow_requests = Follow.objects.filter(following=user, follow_status='pending')
        for follow_request in pending_follow_requests:
            try:
                with transaction.atomic():
                    follow_request.follow_status = 'accepted'
                    follow_request.save()

                    # Update the num_followers and num_following counters for the users
                    update_follow_counters(follow_request.following, follow_request.follower)

                    # Get the original follow_request notification to update it based on the selected user action
                    notification = Notification.objects.get(recipient=follow_request.following,
                                                            sender=follow_request.follower,
                                                            notification_type='follow_request')

                    # Update the original "follow_request" notification to "new_follower"
                    notification.notification_type = 'new_follower'
                    notification.save()

                    # Notify user that changed their profile privacy to public of their new followers
                    notify_user(follow_request.following, follow_request.follower, 'new_follower', "started following you")
                    # Notify the users who had the pending follow requests that their follow request was accepted
                    notify_user(follow_request.follower, follow_request.following, 'follow_accept', "accepted your follow request")

                    # Notify the user who accepted the request via WebSocket (to apply necessary changes to their front-end)
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{follow_request.following.id}",
                        {
                            "type": "notification_follow_request_action",
                            "action": "accept",
                            "unique_identifier": str(notification.id),
                        }
                    )
            except Exception as e:
                # Log the exception, but continue processing other follow requests
                print(f"Error processing follow request: {e}")
                continue  # Move to the next follow request

    return Response({'success': 'Profile privacy updated successfully'}, status=status.HTTP_200_OK)


# Endpoint: /api/search/users/?username={}&page={}&page_size={}
# API view to search for users
@api_view(['GET'])
def search_users(request):
    username = request.query_params.get('username')  # Get the search query from query parameters

    if not username:
        return Response([], status=status.HTTP_200_OK)

    # Set a default page size of 5 returned datasets per page
    default_page_size = 5
    start_index, end_index, validation_response = get_pagination_indeces(request, default_page_size)
    if validation_response:
        return validation_response

    # Search for users based on username
    matched_users = User.objects.filter(username__icontains=username)[start_index:end_index].only('username', 'profile_picture')

    serializer = FollowSerializer(matched_users, many=True, context={'request': request})

    return Response(serializer.data, status=status.HTTP_200_OK)
