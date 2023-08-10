from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.authtoken.models import Token

from .models import User, Post
from .serializers import UserSerializer, PostSerializer


# Endpoint: List Users: GET /api/users/
# Endpoint: Create User: POST /api/users/
# Custom view for listing and creating users
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()  # Retrieves all the users from the database
    serializer_class = UserSerializer  # Specifies serializer class to use for serializing and deserializing user data
    permission_classes = [AllowAny]  # Allow anyone to view the list and create new users

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

        # Save the new user to the database
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Get the user instance after creation
        user = serializer.instance

        # Generate or get the token for the user
        token, _ = Token.objects.get_or_create(user=user)

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
    permission_classes = [IsAuthenticated]  # Allow only authenticated users to make changes to their account

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

        # Perform the update
        serializer.save(partial=True)


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


# Endpoint: /api/feed/
# API view to get posts from the users that the current user follows
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_feed(request):
    following_users = request.user.following.all()  # Obtains all the users the requesting user is following
    feed_posts = Post.objects.filter(user__in=following_users)  # fetches all posts from the users in following_users

    # The context is used to pass the request to the PostSerializer to perform custom logic
    serializer = PostSerializer(feed_posts, many=True, context={'request': request})

    return Response(serializer.data, status=status.HTTP_200_OK)


# Endpoint: /api/user/profile/{user_id}/
# API view to get a users profile and its information
@api_view(['GET'])
def user_profile(request, user_id):
    try:
        # Get user by username
        user = User.objects.get(id=user_id)

        # Use functions in the UserSerializer to get the users number of posts, followers, and following
        num_followers = user.num_followers()
        num_following = user.num_following()
        num_posts = user.num_posts()

        # Check if the requesting user is following the viewed user
        if request.user.is_authenticated:
            is_following = user.followers.filter(id=request.user.id).exists()
        else:
            is_following = False

        # Check if the requesting user is attempting to view their own account
        if request.user == user:
            is_following = None  # Indicate that the user is viewing their own account

        # Check if the requesting user is attempting to view a private user that they don't follow
        elif user.profile_privacy == 'private' and not is_following:
            response_data = {
                'username': user.username,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'bio': user.bio,
                'contact_information': user.contact_information,
                'is_following': False,
                'posts': None,  # Indicate that the user has no access to posts
                'num_followers': num_followers,
                'num_following': num_following,
                'num_posts': num_posts,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        # Get user's posts for users the requesting user has access to
        users_posts = Post.objects.filter(user=user)
        serializer = PostSerializer(users_posts, many=True)

        # Add the follow status and additional information to the response data
        response_data = {
            'username': user.username,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'bio': user.bio,
            'contact_information': user.contact_information,
            'is_following': is_following,
            'posts': serializer.data,
            'num_followers': num_followers,
            'num_following': num_following,
            'num_posts': num_posts,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


# Endpoint: /api/users/change_profile_privacy/
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
        if new_privacy == 'private':
            user.posts.filter(visibility='public').update(visibility='private')
        else:
            user.posts.filter(visibility='private').update(visibility='public')

    return Response({'success': 'Profile privacy updated successfully'}, status=status.HTTP_200_OK)


# Endpoint: /api/search/users/
@api_view(['GET'])
def search_users(request):
    search_query = request.query_params.get('q', '')  # Get the search query from query parameters

    # Search for users based on username or email
    matched_users = User.objects.filter(username__icontains=search_query)

    serializer = UserSerializer(matched_users, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)
