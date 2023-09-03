# core/post_urls.py
from django.urls import path
from core.API_Views import post_views

urlpatterns = [
    # Endpoint: List Posts: GET /api/posts/
    # Endpoint: Create Post: POST /api/posts/
    path('api/posts/', post_views.PostListCreateView.as_view(), name='post-list-create'),

    # Endpoint: Retrieve Post: GET /api/posts/{post_id}/
    # Endpoint: Update Post: PATCH /api/posts/{post_id}/
    # Endpoint: Delete Post: DELETE /api/posts/{post_id}/
    path('api/posts/<int:pk>/', post_views.PostDetailAPIView.as_view(), name='post-detail'),

    # Endpoint: POST /api/post/{post_id}/like/
    path('api/post/<int:post_id>/like/', post_views.like_post, name='like-post'),

    # Endpoint: POST /api/post/{post_id}/unlike/
    path('api/post/<int:post_id>/unlike/', post_views.unlike_post, name='unlike-post'),

    # Endpoint: GET /api/hashtags/?hashtag={}&page={}&page_size={}
    path('api/hashtags/', post_views.SuggestHashtagsView.as_view(), name='suggest-hashtags'),

    # Endpoint: GET /api/hashtag/posts/?hashtag={}&page={}&page_size={}
    path('api/hashtag/<int:hashtag_id>/posts/', post_views.SearchHashtagPostsView.as_view(), name='search-hashtag-posts'),

    # Endpoint: GET /api/explore/posts/?page={}&page_size={}
    path('api/explore/posts/', post_views.ExplorePageView.as_view(), name='explore-page'),

    # Endpoint: GET /api/post/{post_id}/likers/?page={}&page_size={}
    path('api/post/<int:post_id>/likers/', post_views.PostLikersView.as_view(), name='post-likers'),
]
