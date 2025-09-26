"""
WebSocket routing for AI services - real-time AI processing and streaming
"""

from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # AI Processing WebSocket for real-time AI operations
    path('ws/ai/process/<str:session_id>/', consumers.AIProcessingConsumer.as_asgi()),
    
    # Streaming AI responses for long-form content generation
    path('ws/ai/stream/<str:session_id>/', consumers.AIStreamingConsumer.as_asgi()),
    
    # Real-time search with AI enhancement
    path('ws/search/<str:session_id>/', consumers.SearchConsumer.as_asgi()),
    
    # AI Assistant interactive WebSocket
    path('ws/assistant/<str:assistant_id>/<str:session_id>/', consumers.AssistantConsumer.as_asgi()),

    # AI analytics and insights WebSocket
    path('ws/analytics/<str:session_id>/', consumers.AnalyticsConsumer.as_asgi()),
]
