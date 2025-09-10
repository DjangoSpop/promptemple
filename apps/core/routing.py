"""
Core WebSocket routing
"""

from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    # Root WebSocket endpoint
    path('', consumers.RootWebSocketConsumer.as_asgi()),
    re_path(r'^$', consumers.RootWebSocketConsumer.as_asgi()),
    
    # Health check endpoint
    path('health/', consumers.HealthCheckConsumer.as_asgi()),
    path('ws/health/', consumers.HealthCheckConsumer.as_asgi()),
]