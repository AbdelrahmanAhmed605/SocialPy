# core/message_urls.py
from django.urls import path
from core.API_Views import message_views

urlpatterns = [
    # Endpoint: POST api/messages/send/{receiver_id}
    path('api/messages/send/<int:receiver_id>/', message_views.send_message, name='send-message'),

    # Endpoint: DELETE api/messages/delete/{message_id}
    path('api/messages/delete/<int:message_id>/', message_views.delete_message, name='delete-message'),

    # Endpoint: GET /api/messages/conversation/{user_id}/?page={}&page_size={}
    path('api/messages/conversation/<int:user_id>/', message_views.ConversationListView.as_view(), name='get-conversation'),

    # Endpoint: GET /api/messages/conversation-partners/?username={}&page={}&page_size={}
    path('api/messages/conversation-partners/', message_views.ConversationPartnerListView.as_view(), name='get-conversation-partners'),
]
