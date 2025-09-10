"""
Enhanced WSGI configuration with Sentry integration and performance monitoring
Production-ready setup with comprehensive error handling
"""

import os
import logging
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings")

# Configure logging
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'wsgi.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Sentry before Django setup
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware
    
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(
                    transaction_capture=True,
                    middleware_spans=True,
                    signals_spans=False,
                    cache_spans=True,
                ),
            ],
            traces_sample_rate=0.1,
            send_default_pii=False,
            attach_stacktrace=True,
            environment=os.environ.get('ENVIRONMENT', 'production'),
            release=os.environ.get('APP_VERSION', '1.0.0'),
        )
        logger.info("Sentry initialized for WSGI application")
        SENTRY_ENABLED = True
    else:
        SENTRY_ENABLED = False
        logger.info("Sentry DSN not provided - error monitoring disabled")
        
except ImportError:
    SENTRY_ENABLED = False
    logger.warning("Sentry not available - install sentry-sdk for error monitoring")

# Get Django WSGI application
django_application = get_wsgi_application()

# Wrap with Sentry middleware if available
if SENTRY_ENABLED:
    try:
        application = SentryWsgiMiddleware(django_application)
        logger.info("WSGI application wrapped with Sentry middleware")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry WSGI middleware: {e}")
        application = django_application
else:
    application = django_application

# Performance monitoring middleware
class PerformanceMiddleware:
    """Simple performance monitoring for WSGI requests"""
    
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        import time
        
        start_time = time.time()
        
        def custom_start_response(status, response_headers, exc_info=None):
            # Add performance headers
            elapsed = time.time() - start_time
            response_headers.append(('X-Response-Time', f'{elapsed:.3f}s'))
            response_headers.append(('X-Server', 'PromptCraft-WSGI'))
            
            # Log slow requests
            if elapsed > 2.0:  # Log requests taking more than 2 seconds
                method = environ.get('REQUEST_METHOD', 'GET')
                path = environ.get('PATH_INFO', '/')
                logger.warning(f"Slow request: {method} {path} took {elapsed:.3f}s")
            
            return start_response(status, response_headers, exc_info)
        
        return self.app(environ, custom_start_response)

# Wrap application with performance monitoring
application = PerformanceMiddleware(application)

logger.info("WSGI application initialized successfully")
logger.info(f"Sentry enabled: {SENTRY_ENABLED}")
logger.info("Performance monitoring enabled")
