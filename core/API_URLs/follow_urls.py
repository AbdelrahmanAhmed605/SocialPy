# core/API_URLs/follow_urls.py
from django.urls import path
from core.API_Views import follow_views

urlpatterns = [
    # Endpoint: POST /api/follow/user/{user_id}
    path('api/follow/user/<int:user_id>/', follow_views.follow_user, name='follow-user'),

    # Endpoint: POST /api/respond_follow_request/user/{user_id}
    path('api/respond_follow_request/user/<int:follower_id>/', follow_views.respond_follow_request, name='respond-follow-request'),

    # Endpoint: POST /api/unfollow/user/{user_id}
    path('api/unfollow/user/<int:user_id>/', follow_views.unfollow_user, name='unfollow-user'),

    # Endpoint: GET /api/follower_list/{user_id}/?page={}&page_size={}
    path('api/follower_list/<int:user_id>/', follow_views.FollowerListView.as_view(), name='get-followers'),

    # Endpoint: /api/following_list/{user_id}/?page={}&page_size={}
    path('api/following_list/<int:user_id>/', follow_views.FollowingListView.as_view(), name='get-following'),
]
