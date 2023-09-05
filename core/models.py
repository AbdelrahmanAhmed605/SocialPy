# Import necessary modules
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


# Generate a unique identifier for user profile picture files (to avoid files with the same names being saved to the S3 Bucket)
def user_profile_picture_upload(instance, filename):
    unique_identifier = uuid.uuid4().hex
    # Construct the path including the unique identifier
    return f'profiles/{unique_identifier}/{filename}'

# Define a custom User model that extends AbstractUser
class User(AbstractUser):
    email = models.EmailField(max_length=255, unique=True,
                              error_messages={'unique': ("That email has already been used.")})
    username = models.CharField(max_length=255, unique=True,
                                error_messages={'unique': ("A user with that username already exists.")})
    # Additional fields for user profiles
    profile_picture = models.ImageField(upload_to=user_profile_picture_upload, null=True, blank=True)  # Profile picture for the user
    bio = models.TextField(max_length=300, blank=True)  # Short bio or description for the user
    profile_privacy = models.CharField(max_length=10, choices=[('public', 'Public'), ('private', 'Private')], default='public')  # Privacy setting for user profile
    num_followers = models.PositiveIntegerField(default=0)  # counter to keep track of users num of followers
    num_following = models.PositiveIntegerField(default=0)  # counter to keep track of num of users a user is following
    num_posts = models.PositiveIntegerField(default=0)  # counter to keep track of num of posts made by the user

    def __str__(self):
        return self.username


# Model to represent hashtags on posts
class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]


# Generate a unique identifier for media files (to avoid media files with the same names being saved to the S3 Bucket)
def post_media_upload(instance, filename):
    unique_identifier = uuid.uuid4().hex
    # Construct the path including the unique identifier
    return f'posts/{unique_identifier}/{filename}'

# Model to represent user posts
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_posts')  # ForeignKey user who made the post
    content = models.TextField(max_length=1000)  # Text content of the post
    media = models.ImageField(upload_to=post_media_upload, null=False, blank=False)
    visibility = models.CharField(max_length=10, choices=[('public', 'Public'), ('private', 'Private')], default='public')  # Visibility setting for the post
    hashtags = models.ManyToManyField(Hashtag, blank=True)  # Hashtags or tags associated with the post
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts')
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['visibility']),
        ]
        ordering = ['-created_at']  # Sort posts by created_at in descending order


# Model to represent user comments on posts
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ForeignKey User who made the comment
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments')  # ForeignKey Post of the post being commented on
    content = models.TextField(max_length=500)  # Text content of the comment
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.post}"

    class Meta:
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']


# Model to represent user follows (followers and following)
class Follow(models.Model):
    FOLLOW_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
    ]

    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')  # ForeignKey User that is following another User
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')  # ForeignKey User that is being followed by another User
    follow_status = models.CharField(max_length=10, choices=FOLLOW_STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('follower', 'following')  # Ensure unique follower-following pairs
        indexes = [
            models.Index(fields=['follower', 'following', 'follow_status']),  # Combined index
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# Model to represent direct messages between users
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')  # ForeignKey User that sent the message
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')  # ForeignKey User that received the message
    content = models.TextField(max_length=1000)  # Text content of the message
    created_at = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)  # Track if the message has been delivered
    is_read = models.BooleanField(default=False)  # Track if the message has been read

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username} - {self.created_at}"

    class Meta:
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['receiver']),
        ]
        ordering = ['-created_at']


# Model to represent the notifications a user will receive
class Notification(models.Model):
    TYPE_CHOICES = (
        ('follow_request', 'Follow Request'),
        ('follow_accept', 'Follow Request Accepted'),
        ('new_follower', 'New Follower'),
        ('new_comment', 'New Comment'),
        ('new_like', 'New Like'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    notification_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    notification_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.notification_type} notification for {self.recipient}'

    class Meta:
        indexes = [
            models.Index(fields=['recipient']),  # Index for recipient field
            models.Index(fields=['sender', 'notification_type']),  # Composite index
        ]