from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Q object helps build complex queries using logical operators to filter database records based on multiple conditions
from django.db.models import Q
# lets you directly manipulate database fields within database queries, leading to more efficient operations
from django.db.models import F
# Atomic transactions ensure that a series of database operations are completed together or not at all, maintaining data integrity.
from django.db import transaction, DatabaseError, IntegrityError
# Get the User model configured for this Django project
from django.contrib.auth import get_user_model

# Accessing Django Channels' channel layer for WebSocket integration
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.models import Follow, Notification
from core.serializers import FollowSerializer
from .api_utility_functions import notify_user, update_follow_counters, accept_follow_request_notification, remove_notification
from core.Pagination_Classes.paginations import LargePagination


# Get the User model configured for this Django project
User = get_user_model()


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

    # Set the following user as the request user (user who is attempting to follow another user)
    follower_user = request.user

    # Check if user already follows this user
    if Follow.objects.filter(follower_id=follower_user.id, following_id=following_user.id, follow_status='accepted').exists():
        return Response({"error": "You are already following this user"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            # Determine the status of the follow request based on the profile privacy of the user we're attempting to follow
            # If the user is public, then the follow is accepted. If the user is private then the status is pending
            follow_status = 'accepted' if following_user.profile_privacy == 'public' else 'pending'

            # Create the follow instance with the appropriate status
            follow = Follow.objects.create(
                follower=follower_user,
                following=following_user,
                follow_status=follow_status
            )

            # If the user is public, then the follow is immediately created
            if following_user.profile_privacy == 'public':
                # Update the num_followers and num_following counters for the users
                update_follow_counters(following_user, follower_user)
                # Create a new_follower notification for the user being followed and also notify them via WebSocket
                notify_user(following_user, follower_user, 'new_follower', "started following you")
            # If the user is private, a follow request is made and must be accepted before the requesting user can follow them
            else:
                # Create a follow_request notification for the user being followed and also notify them via WebSocket
                notify_user(following_user, follower_user, 'follow_request', "sent you a follow request")
    except Exception as e:
        return Response({"error": "An error occurred while processing the follow request"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(
        {"message": "Follow request sent" if follow_status == 'pending' else "You are now following this user"},
        status=status.HTTP_201_CREATED)


# Endpoint: /api/respond_follow_request/user/{user_id}
# API view to allow a private user to accept a follow request
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_follow_request(request, follower_id):
    try:
        follower_user = User.objects.only('id').get(id=follower_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Set the following user as the request user (user who is accepting/declining the follow_request)
    following_user = request.user

    # Find the Follow model instance for the pending follow request
    try:
        follow = Follow.objects.get(follower_id=follower_user.id, following_id=following_user.id, follow_status='pending')
    except Follow.DoesNotExist:
        return Response({"error": "No pending follow request found from this user"}, status=status.HTTP_404_NOT_FOUND)

    # Get the requesting users deciding action on the follow request (accept or decline)
    action = request.data.get('action')
    # Get the original follow_request notification to update it based on the selected user action
    original_notification = Notification.objects.get(recipient_id=following_user.id, sender_id=follower_user.id, notification_type='follow_request')

    if action in ['accept', 'decline']:
        try:
            with transaction.atomic():
                if action == 'accept':
                    # Update the follow status of the Follow instance between the 2 users
                    follow.follow_status = 'accepted'
                    follow.save()

                    # Update the num_followers and num_following counters for the users
                    update_follow_counters(following_user, follower_user)

                    # Update the original "follow_request" notification to "new_follower"
                    original_notification.notification_type = 'new_follower'
                    # Save the original notification with the new appropriate notification type
                    original_notification.save()

                    # Create a notification to the user who created the follow request informing them it was accepted
                    notify_user(follower_user, following_user, 'follow_accept', "accepted your follow request")

                    # Notify the user who accepted the follow request via WebSocket (to apply necessary changes to their front-end)
                    accept_follow_request_notification(original_notification, following_user, 'accept')
                else:  # 'decline' action
                    # Delete the Follow instance if the user declined the follow request
                    follow.delete()

                    notification_id = str(original_notification.id)  # Store the ID for WebSocket use

                    # Delete the original "follow_request" notification
                    original_notification.delete()

                    # Remove the notification for the use who declined the request via WebSocket
                    remove_notification(following_user.id, notification_id)
        except Exception as e:
            return Response({"error": "An error occurred while processing the response to the follow request"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": f"Follow request {action}ed"}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)


# Endpoint: /api/unfollow/user/{user_id}
# API view to allow a requesting user to unfollow another user
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unfollow_user(request, user_id):
    try:
        following_user = User.objects.only('id').get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Set the follower user as the request user (user who is attempting to unfollow another user)
    follower_user = request.user

    # Check if requesting user is currently following this user
    follow = Follow.objects.filter(follower_id=follower_user.id, following_id=following_user.id).first()
    if not follow:
        return Response({"error": "You are not following this user"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Use a transaction to handle unfollowing, updating the counters, and deleting the associated notification
        with transaction.atomic():
            # Check that the requesting user is following the user they are attempting to unfollow
            # Since if the requesting user is canceling a pending follow request, no follow counts need to be changed
            if follow.follow_status == "accepted":
                # Decrement the num_followers counter for the user being unfollowed using F object
                following_user.num_followers = F('num_followers') - 1
                following_user.save()
                # Decrement the num_following counter for the user who is unfollowing using F object
                follower_user.num_following = F('num_following') - 1
                follower_user.save()

            # Remove the follow relationship
            follow.delete()

            # Fetch the associated "follow_request" or "new_follower" notification
            notification = Notification.objects.filter(
                Q(sender_id=follower_user.id, recipient_id=following_user.id, notification_type='follow_request') |
                Q(sender_id=follower_user.id, recipient_id=following_user.id, notification_type='new_follower')
            ).first()

            # Check if the notification exists
            if notification:
                notification_id = str(notification.id)  # Store the ID for WebSocket use

                # Delete the associated notification
                notification.delete()

                # Remove the notification for the recipient user via WebSocket
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"notifications_{following_user.id}",
                    {
                        "type": "remove_notification",
                        "unique_identifier": notification_id,
                    }
                )
    except (DatabaseError, IntegrityError):
        return Response({"error": "An error occurred while unfollowing the user"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "You have unfollowed this user"}, status=status.HTTP_200_OK)


# Endpoint: /api/follower_list/{user_id}/?page={}
# API view to view a user's follower list
class FollowerListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    pagination_class = LargePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        try:
            user = User.objects.only('id').get(id=user_id)
        except User.DoesNotExist:
            raise APIException(detail={"error": "User not found"}, code=status.HTTP_404_NOT_FOUND)

        try:
            # Get a queryset of the user's followers
            followers = User.objects.filter(following__following_id=user.id, following__follow_status='accepted')
            return followers
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


# Endpoint: /api/following_list/{user_id}/?page={}
# API view to view a user's following list
class FollowingListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    pagination_class = LargePagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        try:
            user = User.objects.only('id').get(id=user_id)
        except User.DoesNotExist:
            raise APIException(detail={"error": "User not found"}, code=status.HTTP_404_NOT_FOUND)

        try:
            # Get a queryset of the users that the requesting user follows
            following_users = User.objects.filter(follower__follower_id=user.id, follower__follow_status='accepted')
            return following_users
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