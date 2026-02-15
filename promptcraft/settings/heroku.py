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
    'api.prompt-temple.com',
    'localhost',
    '127.0.0.1',
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
# CACHING - Use Redis if available, otherwise in-memory
# ============================================
REDIS_URL = os.environ.get('REDIS_URL', None)

if REDIS_URL:
    import ssl
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
                }
            },
            'KEY_PREFIX': 'promptcraft',
            'TIMEOUT': 300,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    # No Redis addon — use Django's built-in LocMemCache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'promptcraft-cache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

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

# SSL/TLS Settings for Custom Domain
SECURE_SSL_HOST = None  # Allow all HTTPS hosts in ALLOWED_HOSTS
SECURE_REDIRECT_EXEMPT = []  # No exemptions from SSL redirect

# Cookie Settings for Custom Domain
SESSION_COOKIE_DOMAIN = None  # Allow cookies across subdomains
SESSION_COOKIE_SAMESITE = 'Lax'  # Balance security and functionality
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'https://www.prompt-temple.com',
    'https://prompt-temple.com',
    'https://api.prompt-temple.com',
    'https://prompt-temple-2777469a4e35.herokuapp.com',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'chrome-extension://bcopclpofnaghlkpeilijadlbnnfabpp',
]

# ============================================
# CORS SETTINGS
# ============================================
CORS_ALLOWED_ORIGINS = [
    'https://www.prompt-temple.com',
    'https://prompt-temple.com',
    'https://api.prompt-temple.com',
    'https://prompt-temple-2777469a4e35.herokuapp.com',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'chrome-extension://bcopclpofnaghlkpeilijadlbnnfabpp',
]

# Allow credentials for authentication
CORS_ALLOW_CREDENTIALS = True

# Allow custom headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-client-version',
    'x-request-id',
    'x-operation-id',
    'x-timestamp',
    'x-correlation-id',
    'cache-control',
    'pragma',
]

# Expose headers to the frontend
CORS_EXPOSE_HEADERS = [
    'x-request-id',
    'x-correlation-id',
    'x-client-version',
    'x-ratelimit-limit',
    'x-ratelimit-remaining',
    'x-ratelimit-reset',
    'content-type',
    'content-length',
]

# Allowed HTTP methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Preflight request cache duration (24 hours)
CORS_PREFLIGHT_MAX_AGE = 86400

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
# FRONTEND URL
# ============================================
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# ============================================
# SOCIAL AUTH CONFIGURATION (Google OAuth)
# ============================================
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'APP': {
            'client_id': config('GOOGLE_OAUTH2_CLIENT_ID', default=''),
            'secret': config('GOOGLE_OAUTH2_CLIENT_SECRET', default=''),
        },
    },
}

SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'

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
