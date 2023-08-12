from django.db import transaction, DatabaseError, IntegrityError

from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User, Follow, Notification
from .serializers import FollowSerializer


# Endpoint: /api/follow/user/{user_id}
# API view to allow a requesting user to follow another user
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    # Look for the user we are attempting to follow
    try:
        following_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    follower_user = request.user

    # Check if user already follows this user
    if Follow.objects.filter(follower=follower_user, following=following_user, follow_status='accepted').exists():
        return Response({"error": "You are already following this user"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the following_user is private
    if following_user.profile_privacy == 'private':
        # Create the follow request with a 'pending' status
        Follow.objects.create(follower=follower_user, following=following_user, follow_status='pending')

        # Create a follow_request notification
        Notification.objects.create(
            recipient=following_user,
            sender=follower_user,
            notification_type='follow_request'
        )

        return Response({"message": "Follow request sent"}, status=status.HTTP_201_CREATED)
    else:
        # Create the follow relationship immediately for public users
        Follow.objects.create(follower=follower_user, following=following_user, follow_status='accepted')

        # Create a new_follower notification
        Notification.objects.create(
            recipient=following_user,
            sender=follower_user,
            notification_type='new_follower'
        )

        return Response({"message": "You are now following this user"}, status=status.HTTP_201_CREATED)


# Endpoint: /api/accept/follow/user/{user_id}
# API view to allow a private user to accept a follow request
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_follow_request(request, follower_id):
    try:
        follower_user = User.objects.get(id=follower_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        follow = Follow.objects.get(follower=follower_user, following=request.user, follow_status='pending')
    except Follow.DoesNotExist:
        return Response({"error": "No pending follow request found from this user"}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get('action')  # 'accept' or 'decline'

    if action == 'accept':
        follow.follow_status = 'accepted'
        follow.save()
        return Response({"message": "Follow request accepted"}, status=status.HTTP_200_OK)
    elif action == 'decline':
        follow.delete()
        return Response({"message": "Follow request declined"}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)


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

    try:
        # Use a transaction to handle both unfollowing and deleting the associated notification
        with transaction.atomic():
            # Remove the follow relationship
            follow.delete()

            # Delete the associated notification
            Notification.objects.filter(sender=follower_user, recipient=following_user).delete()
    except (DatabaseError, IntegrityError):
        return Response({"error": "An error occurred while unfollowing the user"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "You have unfollowed this user"}, status=status.HTTP_200_OK)


# Endpoint: /api/follower_list/{user_id}
# API view to view a user's follower list
# Note: we don't have to check if requesting user has access to this list since the user_profile
#       API view in the user_views already checks for this access
@api_view(['GET'])
def get_followers(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get a list of all the user's followers
    followers = Follow.objects.filter(following=user).select_related('follower')
    follower_users = [follow.follower for follow in followers]

    serializer = FollowSerializer(follower_users, many=True, context={'request': request})

    return Response(serializer.data, status=status.HTTP_200_OK)


# Endpoint: /api/following_list/{user_id}
# API view to view a user's following list
@api_view(['GET'])
def get_following(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get a list of all the user's that they follow
    followings = Follow.objects.filter(follower=user).select_related('following')
    following_users = [following.following for following in followings]

    serializer = FollowSerializer(following_users, many=True, context={'request': request})

    return Response(serializer.data, status=status.HTTP_200_OK)
