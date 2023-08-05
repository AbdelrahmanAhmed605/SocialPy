from rest_framework import serializers
from .models import User, Post, Comment, Follow, Message

# Serializers to convert Django model instances into Python data types and vice versa (deserialization)
# Python data will be rendered into JSON for use in API responses (serialization)
# JSON data will be converted to python data from API requests to be saved in Django model instances. (deserialization)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
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
