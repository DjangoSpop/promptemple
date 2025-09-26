"""
ASGI config for promptcraft project with WebSocket support.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import logging
from django.core.asgi import get_asgi_application

# Set Django settings before importing channels
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings.production")

# Initialize Django ASGI application early to ensure settings are loaded
django_asgi_app = get_asgi_application()

# Import channels components after Django is set up
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.middleware import BaseMiddleware

# Set up logging
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    """Custom middleware for logging WebSocket connections"""
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            logger.info(f"WebSocket connection from {scope.get('client', 'unknown')}")
        return await super().__call__(scope, receive, send)

# Import routing configurations
try:
    from apps.core import routing as core_routing
    core_websocket_patterns = core_routing.websocket_urlpatterns
except ImportError:
    logger.warning("Core routing not found, creating empty WebSocket patterns")
    core_websocket_patterns = []

try:
    from apps.templates import routing as template_routing
    template_websocket_patterns = template_routing.websocket_urlpatterns
except ImportError:
    logger.warning("Template routing not found, creating empty WebSocket patterns")
    template_websocket_patterns = []

try:
    from apps.ai_services import routing as ai_routing
    ai_websocket_patterns = ai_routing.websocket_urlpatterns
except ImportError:
    logger.warning("AI services routing not found")
    ai_websocket_patterns = []

# Combine all WebSocket URL patterns - core patterns first for root path handling
websocket_urlpatterns = core_websocket_patterns + template_websocket_patterns + ai_websocket_patterns

application = ProtocolTypeRouter({
    # HTTP requests are handled by Django
    "http": django_asgi_app,
    
    # WebSocket connections are handled by Channels
    "websocket": AllowedHostsOriginValidator(
        LoggingMiddleware(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
})
