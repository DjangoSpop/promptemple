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

try:
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

    # Import routing configurations with error handling
    websocket_urlpatterns = []

    try:
        from apps.core import routing as core_routing
        websocket_urlpatterns.extend(core_routing.websocket_urlpatterns)
        logger.info("Loaded core WebSocket patterns")
    except (ImportError, AttributeError) as e:
        logger.info(f"Core routing not available: {e}")

    try:
        from apps.templates import routing as template_routing
        websocket_urlpatterns.extend(template_routing.websocket_urlpatterns)
        logger.info("Loaded template WebSocket patterns")
    except (ImportError, AttributeError) as e:
        logger.info(f"Template routing not available: {e}")

    try:
        from apps.ai_services import routing as ai_routing
        websocket_urlpatterns.extend(ai_routing.websocket_urlpatterns)
        logger.info("Loaded AI services WebSocket patterns")
    except (ImportError, AttributeError) as e:
        logger.info(f"AI services routing not available: {e}")

    # Create ASGI application with WebSocket support
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

    logger.info(f"ASGI application initialized with {len(websocket_urlpatterns)} WebSocket patterns")

except ImportError as e:
    # Fallback to HTTP-only application if channels is not available
    logger.warning(f"Channels not available, using HTTP-only ASGI: {e}")
    application = django_asgi_app
