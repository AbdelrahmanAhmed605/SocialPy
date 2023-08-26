from rest_framework import serializers
from .models import User, Hashtag, Post, Comment, Follow, Message, Notification


# Serializers to convert Django model instances into Python data types and vice versa (deserialization)
# Python data will be rendered into JSON for use in API responses (serialization)
# JSON data will be converted to python data from API requests to be saved in Django model instances. (deserialization)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']  # Exclude the password field from the API response


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'content', 'created_at', 'updated_at', 'can_edit', 'can_delete']


class FollowSerializer(serializers.ModelSerializer):
    # Custom field to indicate the follow status of the requesting user to the viewed users
    requesting_user_follow_status = serializers.SerializerMethodField()

    # Function to get the follow status of the requesting user to the viewed user
    def get_requesting_user_follow_status(self, following_user):
        if 'request' in self.context:
            requesting_user = self.context['request'].user
            # Check if there is an authenticated requesting user
            if requesting_user.is_authenticated:
                follow_instance = requesting_user.following.filter(id=following_user.id).first()
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
