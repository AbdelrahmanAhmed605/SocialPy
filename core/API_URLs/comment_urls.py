# core/comment_urls.py
from django.urls import path
from core.API_Views import comment_views

urlpatterns = [
    # Endpoint: POST /api/comment/post/{post_id}
    path('api/comment/post/<int:post_id>/', comment_views.create_comment, name='create-comment'),

    # Endpoint: DELETE /api/comment/{comment_id}/
    path('api/comment/<int:comment_id>/', comment_views.delete_comment, name='delete-comment'),

    # Endpoint: GET /api/comments/post/{post_id}/?page={}&page_size={}
    path('api/comments/post/<int:post_id>/', comment_views.PostCommentListView.as_view(), name='get-post-comments'),
]