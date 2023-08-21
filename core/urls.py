# core/urls.py
from django.urls import path, include

urlpatterns = [
    # Include the URLs for comment-related API views
    path('', include('core.API_URLs.comment_urls')),

    # Include the URLs for follow-related API views
    path('', include('core.API_URLs.follow_urls')),

    # Include the URLs for message-related API views
    path('', include('core.API_URLs.message_urls')),

    # Include the URLs for notification-related API views
    path('', include('core.API_URLs.notification_urls')),

    # Include the URLs for post-related API views
    path('', include('core.API_URLs.post_urls')),

    # Include the URLs for user-related API views
    path('', include('core.API_URLs.user_urls')),
]
