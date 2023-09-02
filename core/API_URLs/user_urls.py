# core/user_urls.py
from django.urls import path
from core.API_Views import user_views

urlpatterns = [
    # Endpoint: List Users: GET /api/users/
    # Endpoint: Create User: POST /api/users/
    path('api/users/', user_views.UserListCreateView.as_view(), name='user-list-create'),

    # Endpoint: Retrieve User: GET /api/users/{user_id}/
    # Endpoint: Update User: PATCH /api/users/{user_id}/
    # Endpoint: Delete User: DELETE /api/users/{user_id}/
    path('api/users/<int:pk>/', user_views.UserDetailView.as_view(), name='user-detail'),

    # Endpoint: POST /api/login/
    path('api/login/', user_views.user_login, name='user-login'),

    # Endpoint: POST /api/logout/
    path('api/logout/', user_views.user_logout, name='user-logout'),

    # Endpoint: GET /api/feed/?page={}&page_size={}
    path('api/feed/', user_views.UserFeedView.as_view(), name='user-feed'),

    # Endpoint: GET /api/user/profile/{user_id}/?page={}&page_size={}
    path('api/user/profile/<int:user_id>/', user_views.user_profile, name='user-profile'),

    # Endpoint: POST /api/user/change_profile_privacy/
    path('api/user/change_profile_privacy/', user_views.change_profile_privacy, name='change-profile-privacy'),

    # Endpoint: GET /api/search/users/?page={}&page_size={}
    path('api/search/users/', user_views.SearchUsersView.as_view(), name='search-users'),
]
