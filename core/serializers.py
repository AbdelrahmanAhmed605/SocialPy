from rest_framework import serializers
from .models import User, Post, Comment, Follow, Message


# Serializers to convert Django model instances into Python data types and vice versa (deserialization)
# Python data will be rendered into JSON for use in API responses (serialization)
# JSON data will be converted to python data from API requests to be saved in Django model instances. (deserialization)

class UserSerializer(serializers.ModelSerializer):
    # Create new fields containing the number of followers, following, and posts for a user
    num_followers = serializers.SerializerMethodField()
    num_following = serializers.SerializerMethodField()
    num_posts = serializers.SerializerMethodField()

    # Function to count the number of followers for a specific user
    # followers is a related_name field in the Follow model for the User field foreign key
    def get_num_followers(self, obj):
        return obj.followers.count()

    # Function to count the number of following for a specific user
    # following is a related_name field in the Follow model for the User field foreign key
    def get_num_following(self, obj):
        return obj.following.count()

    # Function to count the number of posts for a specific user
    # user_posts is a related_name field in the Post model for the User field foreign key
    def get_num_posts(self, obj):
        return obj.user_posts.count()

    class Meta:
        model = User
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    # Create new fields containing the number of likes and comments for a post
    num_likes = serializers.SerializerMethodField()
    num_comments = serializers.SerializerMethodField()

    # Function to count the number of likes for a specific post
    def get_num_likes(self, obj):
        return obj.likes.count()

    # Function to count the number of comments for a specific post
    # post_comments is the related_name field in the Comment model for the Post field foreign key
    def get_num_comments(self, obj):
        return obj.post_comments.count()

    class Meta:
        model = Post
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
