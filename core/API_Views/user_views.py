from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.authtoken.models import Token

from core.models import User, Post
from core.serializers import UserSerializer, PostSerializer


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


# Endpoint: /api/feed/?page={}&page_size={}
# API view to get posts from the users that the current user follows
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_feed(request):
    following_users = request.user.following.filter(follow_status='accepted')  # Obtains all the users the requesting user is following

    # Get the current page number from the request's query parameters
    page_number = int(request.query_params.get('page', 1))  # Defaults to the first page

    # Get the page size from the request's query parameters
    page_size = int(request.query_params.get('page_size', 20))  # Default page size is 20

    # Calculate the starting and ending index for slicing
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size

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
        # Get user by username
        user = User.objects.get(id=user_id)

        # Get the current page number from the request's query parameters
        page_number = int(request.query_params.get('page', 1))  # Defaults to the first page

        # Get the page size from the request's query parameters
        page_size = int(request.query_params.get('page_size', 20))  # Default page size is 20

        # Calculate the starting and ending index for slicing
        start_index = (page_number - 1) * page_size
        end_index = start_index + page_size

        # Check if there is a requesting user and get their follow status to the viewed user
        if request.user.is_authenticated:
            follow_instance = request.user.following.filter(id=user_id).first()
            if follow_instance:
                follow_status = follow_instance.follow_status
            else:
                follow_status = 'False'
        # The else means that there is no authenticated requesting user (not logged in or no account)
        else:
            follow_status = False

        # Check if the requesting user is attempting to view their own account
        if request.user == user:
            follow_status = None  # Indicate that the user is viewing their own account

        # Check if the requesting user is attempting to view a private user that they don't follow
        elif user.profile_privacy == 'private' and (follow_status is False or follow_status == 'pending'):
            response_data = {
                'username': user.username,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'bio': user.bio,
                'contact_information': user.contact_information,
                'follow_status': follow_status,
                'can_view': False,  # Indicate we cannot view the user's profile
                'posts': None,  # Indicate that the user has no access to posts
                'num_followers': user.num_followers,  # Use the counter field from the User model
                'num_following': user.num_following,  # Use the counter field from the User model
                'num_posts': user.num_posts,  # Use the counter field from the User model
            }
            return Response(response_data, status=status.HTTP_200_OK)

        # If we are in this section below, it means the above elif statement didn't run, meaning we are
        # attempting to view a user that is public or private, but we follow them

        # Get a paginated list of the user's posts for users the requesting user has access to
        users_posts = Post.objects.filter(user=user)[start_index:end_index]
        serializer = PostSerializer(users_posts, many=True)

        # Add the follow status and additional information to the response data
        response_data = {
            'username': user.username,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'bio': user.bio,
            'contact_information': user.contact_information,
            'follow_status': follow_status,
            'can_view': True,  # indicate we can view the user's profile
            'posts': serializer.data,
            'num_followers': user.num_followers,  # Use the counter field from the User model
            'num_following': user.num_following,  # Use the counter field from the User model
            'num_posts': user.num_posts,  # Use the counter field from the User model
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


# Endpoint: /api/search/users/?page={}&page_size={}
# API view to search for users
@api_view(['GET'])
def search_users(request):
    username = request.query_params.get('username')  # Get the search query from query parameters

    if not username:
        return Response({"error": "Please provide a username query parameter"}, status=status.HTTP_400_BAD_REQUEST)

    # Get the current page number from the request's query parameters
    page_number = int(request.query_params.get('page', 1))  # Defaults to the first page

    # Get the page size from the request's query parameters
    page_size = int(request.query_params.get('page_size', 5))  # Default page size is 5

    # Calculate the starting and ending index for slicing
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size

    # Search for users based on username
    matched_users = User.objects.filter(username__icontains=username)[start_index:end_index]

    serializer = UserSerializer(matched_users, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)
