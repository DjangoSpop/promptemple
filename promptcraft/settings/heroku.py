# promptcraft/settings/heroku.py
# Heroku-optimized production settings
# Minimal footprint for MVP deployment under 500MB

from .production import *
import dj_database_url
import os

# ============================================
# ENVIRONMENT
# ============================================
DEBUG = False
ENVIRONMENT = 'heroku'

# ============================================
# ALLOWED HOSTS
# ============================================
ALLOWED_HOSTS = [
    '.herokuapp.com',
    'www.prompt-temple.com',
    'prompt-temple.com',
]

# ============================================
# DATABASE - Heroku Postgres
# ============================================
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True
    )
}

# ============================================
# CACHING - Redis (without Celery)
# ============================================
import ssl

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Configure SSL context for Heroku Redis (self-signed cert)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'ssl_cert_reqs': ssl.CERT_NONE,
            }
        },
        'KEY_PREFIX': 'promptcraft',
        'TIMEOUT': 300,
    }
}

# ============================================
# SESSION CONFIGURATION
# ============================================
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ============================================
# STATIC FILES - WhiteNoise
# ============================================
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_DIRS = []  # No additional static directories
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# WhiteNoise Configuration
WHITENOISE_MANIFEST_STRICT = False  # Don't fail on missing files
WHITENOISE_ALLOW_ALL_ORIGINS = True

# ============================================
# MEDIA FILES
# ============================================
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# ============================================
# REMOVE UNUSED APPS FOR MVP
# ============================================
# Remove research_agent, channels, celery
INSTALLED_APPS = [
    app for app in INSTALLED_APPS 
    if not any(x in app for x in ['research_agent', 'channels', 'django_celery'])
]

# ============================================
# MIDDLEWARE - Add WhiteNoise
# ============================================
# Insert WhiteNoise middleware right after SecurityMiddleware
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    security_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
    MIDDLEWARE.insert(security_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# ============================================
# DISABLE FEATURES NOT NEEDED FOR MVP
# ============================================
FEATURE_RAG = False  # No vector search/RAG
ENABLE_AI_FALLBACK = True
CHAT_TRANSPORT = 'sse'  # Server-Sent Events (not WebSockets)

# ============================================
# CELERY - Run synchronously (no workers)
# ============================================
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ============================================
# SECURITY SETTINGS
# ============================================
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================
# CORS SETTINGS
# ============================================
CORS_ALLOWED_ORIGINS = [
    'https://www.prompt-temple.com',
    'https://prompt-temple.com',
]

# Allow credentials for authentication
CORS_ALLOW_CREDENTIALS = True

# ============================================
# LOGGING
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================
# REST FRAMEWORK - Production throttling
# ============================================
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'chat_completions': '5/min',
        'research': '100/hour',
        'research_auth': '500/hour',
    },
}

# ============================================
# AI SERVICES - Lightweight configuration
# ============================================
LANGCHAIN_SETTINGS = {
    'DEEPSEEK_API_KEY': config('DEEPSEEK_API_KEY', default=''),
    'DEEPSEEK_BASE_URL': config('DEEPSEEK_BASE_URL', default='https://api.deepseek.com'),
    'DEEPSEEK_DEFAULT_MODEL': config('DEEPSEEK_DEFAULT_MODEL', default='deepseek-chat'),
    'OPENAI_API_KEY': config('OPENAI_API_KEY', default=None),
    'ANTHROPIC_API_KEY': config('ANTHROPIC_API_KEY', default=None),
    'AI_PROVIDER_PRIORITY': ['deepseek', 'openai', 'anthropic'],
    'ENABLE_AI_FALLBACK': True,
    'AI_REQUEST_TIMEOUT': 30,
    'AI_MAX_RETRIES': 3,
    'AI_RATE_LIMIT_PER_MINUTE': 60,
}

# ============================================
# DEPLOYMENT INFO
# ============================================
print("=" * 60)
print("🚀 HEROKU DEPLOYMENT CONFIGURATION LOADED")
print("=" * 60)
print(f"Environment: {ENVIRONMENT}")
print(f"Debug: {DEBUG}")
print(f"Database: Heroku Postgres")
print(f"Cache: Redis (without Celery)")
print(f"Static: WhiteNoise")
print(f"Chat: SSE (not WebSockets)")
print(f"RAG: Disabled")
print(f"Celery: Synchronous execution")
print(f"Apps: {len(INSTALLED_APPS)} installed")
print("=" * 60)
