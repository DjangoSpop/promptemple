"""
WebSocket URL routing for real-time prompt optimization chat
"""

from django.urls import re_path, path
from . import consumers
from .chat_consumer import ChatConsumer
from .enhanced_consumer import EnhancedChatConsumer

websocket_urlpatterns = [
    # Enhanced Chat WebSocket with RAG agent support (primary)
    path('ws/chat/<str:session_id>/', EnhancedChatConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<session_id>[a-zA-Z0-9_-]+)/$', EnhancedChatConsumer.as_asgi()),
    
    # Standard Chat WebSocket (fallback)
    path('ws/chat-basic/<str:session_id>/', ChatConsumer.as_asgi()),
    re_path(r'ws/chat-basic/(?P<session_id>[a-zA-Z0-9_-]+)/$', ChatConsumer.as_asgi()),
    
    # Legacy prompt optimization chat
    path('ws/prompt-chat/<str:session_id>/', consumers.PromptChatConsumer.as_asgi()),
    re_path(r'ws/prompt-chat/(?P<session_id>[a-zA-Z0-9_-]+)/$', consumers.PromptChatConsumer.as_asgi()),
    
    # Socket.IO compatibility endpoints
    path('socket.io/', consumers.SocketIOCompatibilityConsumer.as_asgi()),
    re_path(r'socket\.io/.*', consumers.SocketIOCompatibilityConsumer.as_asgi()),
]