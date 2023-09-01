from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Q object helps build complex queries using logical operators to filter database records based on multiple conditions
from django.db.models import Q
# lets you directly manipulate database fields within database queries, leading to more efficient operations
from django.db.models import F
# Atomic transactions ensure that a series of database operations are completed together or not at all, maintaining data integrity.
from django.db import transaction, DatabaseError, IntegrityError

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.models import User, Follow, Notification
from core.serializers import FollowSerializer
from .api_utility_functions import get_pagination_indeces, notify_user, update_follow_counters, send_follow_request_notification


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
    if Follow.objects.filter(follower=follower_user, following=following_user, follow_status='accepted').exists():
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
        follower_user = User.objects.get(id=follower_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Set the following user as the request user (user who is accepting/declining the follow_request)
    following_user = request.user

    # Find the Follow model instance for the pending follow request
    try:
        follow = Follow.objects.get(follower=follower_user, following=following_user, follow_status='pending')
    except Follow.DoesNotExist:
        return Response({"error": "No pending follow request found from this user"}, status=status.HTTP_404_NOT_FOUND)

    # Get the requesting users deciding action on the follow request (accept or decline)
    action = request.data.get('action')
    # Get the original follow_request notification to update it based on the selected user action
    original_notification = Notification.objects.get(recipient=following_user, sender=follower_user, notification_type='follow_request')

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

                    # Create a notification to the user who created the follow request informing them it was accepted
                    notify_user(follower_user, following_user, 'follow_accept', "accepted your follow request")
                    websocket_action = 'accept'
                else:  # 'decline' action
                    # Delete the Follow instance if the user declined the follow request
                    follow.delete()
                    # Update the original "follow_request" notification to "follow_decline"
                    original_notification.notification_type = 'follow_decline'
                    websocket_action = 'decline'

                # Save the original notification with the new appropriate notification type
                original_notification.save()

                # Notify the user who accepted/decline the follow request via WebSocket (to apply necessary changes to their front-end)
                send_follow_request_notification(original_notification, following_user, websocket_action)
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
        following_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Set the follower user as the request user (user who is attempting to unfollow another user)
    follower_user = request.user

    # Check if requesting user is currently following this user
    follow = Follow.objects.filter(follower=follower_user, following=following_user).first()
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
                Q(sender=follower_user, recipient=following_user, notification_type='follow_request') |
                Q(sender=follower_user, recipient=following_user, notification_type='new_follower')
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


# Endpoint: /api/follower_list/{user_id}/?page={}&page_size={}
# API view to view a user's follower list
# Note: we don't have to check if requesting user has access to this list since the user_profile
#       API view in the user_views already checks for this access
@api_view(['GET'])
def get_followers(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Set a default page size of 20 returned datasets per page
    default_page_size = 20
    # Utility function to get current page number and page size from the request's query parameters and calculate the pagination slicing indeces
    start_index, end_index, validation_response = get_pagination_indeces(request, default_page_size)
    if validation_response:
        return validation_response

    try:
        # Get a paginated list of the user's followers
        follower_users = User.objects.filter(following__following=user, following__follow_status='accepted')[start_index:end_index]

        serializer = FollowSerializer(follower_users, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    except DatabaseError:
        return Response({"error": "An error occurred while retrieving follower data"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"error": "An unexpected error occurred: " + str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Endpoint: /api/following_list/{user_id}/?page={}&page_size={}
# API view to view a user's following list
@api_view(['GET'])
def get_following(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get the pagination slicing indeces
    default_page_size = 20
    start_index, end_index, validation_response = get_pagination_indeces(request, default_page_size)
    if validation_response:
        return validation_response

    try:
        # Get a paginated list of the user's that the requesting user follows
        following_users = User.objects.filter(follower__follower=user, follower__follow_status='accepted')[start_index:end_index]

        serializer = FollowSerializer(following_users, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    except DatabaseError:
        return Response({"error": "An error occurred while retrieving following data"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"error": "An unexpected error occurred: " + str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
