from rest_framework import serializers
from .models import Hashtag, Post, Comment, Message, Notification
from django.contrib.auth import get_user_model


# Get the User model configured for this Django project
User = get_user_model()


# Serializers to convert Django model instances into Python data types and vice versa (deserialization)
# Python data will be rendered into JSON for use in API responses (serialization)
# JSON data will be converted to python data from API requests to be saved in Django model instances. (deserialization)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    # Exclude the password field from the API response
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('password')  # Remove the password field from the serialized data
        return data


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    # Custom field for the user representation of the author of the post
    user = serializers.SerializerMethodField()

    # Function to customize the representation of the author of the post
    def get_user(self, post):
        user = post.user  # Get the user associated with the post
        if user:
            return {
                'user_id': user.id,
                'username': user.username,
                'profile_picture': user.profile_picture.url if user.profile_picture else None
            }
        return None

    # Custom field to indicate if the requesting user has liked the post
    liked_by_user = serializers.SerializerMethodField()

    # Function that checks if a requesting user liked the post that is being retrieved
    # This will be used on the front end to provide indication to users if they liked a post or not
    def get_liked_by_user(self, post):
        if 'request' in self.context:
            user = self.context['request'].user
            if user.is_authenticated:
                return post.likes.filter(id=user.id).exists()
        return False

    class Meta:
        model = Post
        fields = ['id', 'user', 'content', 'media', 'visibility', 'hashtags', 'created_at', 'updated_at', 'like_count', 'comment_count', 'liked_by_user']


class PostSerializerMinimal(PostSerializer):
    class Meta:
        model = Post
        fields = ['media']


class CommentSerializer(serializers.ModelSerializer):
    # Custom field to indicate whether the requesting user can edit the comment
    can_edit = serializers.SerializerMethodField()
    # Custom field to indicate whether the requesting user can delete the comment
    can_delete = serializers.SerializerMethodField()

    def get_can_delete(self, comment):
        if 'request' in self.context:
            # Check if the requesting user is the owner of the comment or the owner of the post
            user = self.context['request'].user
            if user.is_authenticated:
                return comment.user == user or comment.post.user == user
        return False

    def get_can_edit(self, comment):
        if 'request' in self.context:
            # Check if the requesting user is the owner of the comment
            user = self.context['request'].user
            if user.is_authenticated:
                return comment.user == user
        return False

    # Custom field for the user representation with only 'username' and 'profile_picture'
    user = serializers.SerializerMethodField()

    # Function to customize the representation of the user field
    def get_user(self, post):
        user = post.user  # Get the user associated with the post
        if user:
            return {
                'username': user.username,
                'profile_picture': user.profile_picture.url if user.profile_picture else None
            }
        return None

    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'content', 'created_at', 'can_edit', 'can_delete']


class FollowSerializer(serializers.ModelSerializer):
    # Custom field to indicate the follow status of the requesting user to the viewed users
    requesting_user_follow_status = serializers.SerializerMethodField()

    # Function to get the follow status of the requesting user to the viewed user
    def get_requesting_user_follow_status(self, following_user):
        if 'request' in self.context:
            requesting_user = self.context['request'].user
            # Check if there is an authenticated requesting user
            if requesting_user.is_authenticated:
                if requesting_user == following_user:
                    return "self"
                follow_instance = requesting_user.following.filter(following=following_user).first()
                if follow_instance:
                    return follow_instance.follow_status  # return the follow status
        # If the requesting user is not authenticated, or we do not follow the user
        return False

    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture', 'requesting_user_follow_status']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
