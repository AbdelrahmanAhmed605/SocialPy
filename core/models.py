# Import necessary modules
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator


# Define a custom User model that extends AbstractUser
class User(AbstractUser):
    # Additional fields for user profiles
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)  # Profile picture for the user
    bio = models.TextField(max_length=300, blank=True)  # Short bio or description for the user
    contact_information = models.CharField(max_length=100, blank=True)  # Contact information for the user
    profile_privacy = models.CharField(max_length=10, choices=[('public', 'Public'), ('private', 'Private')], default='public')  # Privacy setting for user profile

    def __str__(self):
        return self.username


# Model to represent hashtags on posts
class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# Model to represent user posts
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_posts')  # ForeignKey user who made the post
    content = models.TextField(max_length=1000)  # Text content of the post
    media = models.FileField(
        upload_to='posts/',
        null=False,
        blank=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi', 'mkv'])]
    )
    visibility = models.CharField(max_length=10, choices=[('public', 'Public'), ('private', 'Private')], default='public')  # Visibility setting for the post
    hashtags = models.ManyToManyField(Hashtag, blank=True)  # Hashtags or tags associated with the post
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts')

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

    class Meta:
        ordering = ['-created_at']  # Sort posts by created_at in descending order


# Model to represent user comments on posts
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ForeignKey User who made the comment
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments')  # ForeignKey Post of the post being commented on
    content = models.TextField(max_length=500)  # Text content of the comment
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.post}"


# Model to represent user follows (followers and following)
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')  # ForeignKey User that is following another User
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')  # ForeignKey User that is being followed by another User

    class Meta:
        unique_together = ('follower', 'following')  # Ensure unique follower-following pairs

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# Model to represent direct messages between users
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')  # ForeignKey User that sent the message
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')  # ForeignKey User that received the message
    content = models.TextField(max_length=1000)  # Text content of the message
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username} - {self.timestamp}"
