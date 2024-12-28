from django.urls import path
from .views import chat, clear_chat

app_name = 'AIChat_app'

urlpatterns = [
    path('chat/', chat, name='chat'),
    path('clear_chat/', clear_chat, name='clear_chat'),
]