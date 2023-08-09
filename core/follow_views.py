from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User, Follow
from .serializers import FollowSerializer


# Endpoint: /api/follow/user/{user_id}
# API view to allow a requesting user to follow another user
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    try:
        following_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    follower_user = request.user

    # Check if user already follows this user
    if Follow.objects.filter(follower=follower_user, following=following_user).exists():
        return Response({"error": "You are already following this user"}, status=status.HTTP_400_BAD_REQUEST)

    # Create the follow relationship
    Follow.objects.create(follower=request.user, following=following_user)

    return Response({"message": "You are now following this user"}, status=status.HTTP_201_CREATED)


# Endpoint: /api/unfollow/user/{user_id}
# API view to allow a requesting user to unfollow another user
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unfollow_user(request, user_id):
    try:
        following_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    follower_user = request.user

    # Check if user is currently following this user
    follow = Follow.objects.filter(follower=follower_user, following=following_user).first()
    if not follow:
        return Response({"error": "You are not following this user"}, status=status.HTTP_400_BAD_REQUEST)

    # Remove the follow relationship
    follow.delete()

    return Response({"message": "You have unfollowed this user"}, status=status.HTTP_200_OK)


# Endpoint: /api/follower_list/{user_id}
# API view to view a user's follower list
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_followers(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get a list of all the user's followers
    followers = Follow.objects.filter(following=user).select_related('follower')
    follower_users = [follow.follower for follow in followers]

    serializer = FollowSerializer(follower_users, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


# Endpoint: /api/following_list/{user_id}
# API view to view a user's following list
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get a list of all the user's that they follow
    followings = Follow.objects.filter(follower=user).select_related('following')
    following_users = [following.following for following in followings]

    serializer = FollowSerializer(following_users, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)
