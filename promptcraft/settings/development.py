from .base import *
import sys
import os
from pathlib import Path

# Import config function (should be available from base settings)
try:
    from decouple import config
except ImportError:
    # Fallback config function if decouple not available
    def config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            if cast == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return cast(value)
        return value

# Ensure SECRET_KEY is properly set
SECRET_KEY = config('SECRET_KEY', default='dev-key-change-in-production-123456789')
if SECRET_KEY == 'dev-key-change-in-production-123456':
    print("⚠️ WARNING: Using default SECRET_KEY. Set SECRET_KEY environment variable for security!", file=sys.stderr)

DEBUG = True  # Enable debug for development
ALLOWED_HOSTS = [
    'localhost',
    'localhost:3000',  # Allow localhost with port
    '127.0.0.1', 
    '10.0.2.2',  # Android AVD emulator
    '0.0.0.0',
    '*',  # Allow all hosts in development
]

# Database for development with fallback to SQLite
# Default to SQLite for easier development setup
USE_POSTGRES = config('USE_POSTGRES', default=False, cast=bool)

if USE_POSTGRES:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config('DB_NAME', default='promptcraft_db'),
            "USER": config('DB_USER', default='promptcraft_user'),
            "PASSWORD": config('DB_PASSWORD', default='fuckthat'),
            "HOST": config('DB_HOST', default='localhost'),
            "PORT": config('DB_PORT', default='5432'),
            "OPTIONS": {
                "connect_timeout": 10,
            }
        }
    }
else:
    # SQLite fallback for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }

# Auto-fallback mechanism - if PostgreSQL connection fails, switch to SQLite
try:
    import psycopg2
    from django.db import connections
    from django.db.utils import OperationalError
    
    if USE_POSTGRES:
        # Test PostgreSQL connection
        try:
            test_conn = psycopg2.connect(
                host=config('DB_HOST', default='localhost'),
                port=config('DB_PORT', default='5432'),
                user=config('DB_USER', default='promptcraft_user'),
                password=config('DB_PASSWORD', default='fuckthat'),
                database=config('DB_NAME', default='promptcraft_db'),
                connect_timeout=5
            )
            test_conn.close()
            print("✅ PostgreSQL connection successful", file=sys.stderr)
        except (psycopg2.OperationalError, Exception) as e:
            print(f"⚠️ PostgreSQL connection failed: {e}", file=sys.stderr)
            print("🔄 Falling back to SQLite for development", file=sys.stderr)
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                    'OPTIONS': {
                        'timeout': 20,
                    }
                }
            }
except ImportError:
    print("⚠️ psycopg2 not available, using SQLite", file=sys.stderr)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }

# REST Framework configuration for development - OVERRIDE base settings
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Development-friendly: Allow any for easier testing
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',  # MVP: Auth required for writes
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',  # Higher limit for development
        'user': '5000/hour',  # Higher limit for development
        'chat_completions': '100/min',  # Higher limit for development
    },
}

# Spectacular settings for API documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'PromptCraft API',
    'DESCRIPTION': 'Comprehensive API documentation for PromptCraft - AI Prompt Management Platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'ENABLE_DJANGO_DEPLOY_CHECK': False,
    'DISABLE_ERRORS_AND_WARNINGS': True,
    'SERVE_AUTHENTICATION': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'displayRequestDuration': True,
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'expandResponses': 'all',
        'pathInMiddlePanel': True,
    },
}

# ============================================================================
# CORS SETTINGS - Development Configuration
# ============================================================================

# Development Origins - Allow localhost and Android AVD
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",  # Alternative frontend port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://10.0.2.2:8000",   # Android AVD accessing Django
    "http://10.0.2.2:3000",   # Android AVD accessing frontend
    "http://0.0.0.0",
]

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = False  # DEVELOPMENT ONLY - Set to True in production if needed!

# Restrict origins for MVP security (even in development)
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

# Custom headers that the frontend sends
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    # ===== Custom Frontend Headers =====
    'x-client-version',     # Frontend version tracking
    'x-request-id',         # Request tracing and debugging
    'x-operation-id',       # Operation correlation
    'x-timestamp',          # Request timestamp
    'x-correlation-id',     # Distributed tracing
    'cache-control',        # Cache directives
    'pragma',               # Legacy cache control
    # ===================================
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

# Preflight request cache duration (in seconds) - 24 hours
CORS_PREFLIGHT_MAX_AGE = 86400

# Debug toolbar
if DEBUG and 'debug_toolbar' not in INSTALLED_APPS:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# Add drf-spectacular to installed apps
if 'drf_spectacular' not in INSTALLED_APPS:
    INSTALLED_APPS += ['drf_spectacular']

# JWT Settings for development
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # Long lifetime for development
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 10,  # 10 seconds leeway for clock skew
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Additional debug settings for Android AVD
if DEBUG:
    INTERNAL_IPS = [
        '127.0.0.1',
        '10.0.2.2',  # Android AVD
    ]

# Override cache configuration for development (fallback to memory cache if Redis unavailable)
try:
    import redis
    redis_url = config('REDIS_URL', default='redis://localhost:6379')
    redis_client = redis.Redis.from_url(redis_url + '/0')
    redis_client.ping()
    # Redis is available, use it
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url + '/1',
            'KEY_PREFIX': 'promptcraft',
            'TIMEOUT': 300,
        },
        # Sessions cache for backward compatibility
        'sessions': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url + '/2',
            'KEY_PREFIX': 'sessions',
            'TIMEOUT': 86400,  # 24 hours
        }
    }
    
    # Override channel layers for development with Redis
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [redis_url + '/3'],
                'symmetric_encryption_keys': [config('CHANNEL_LAYER_SECRET', default='secret-key')],
            },
        },
    }
    print("✅ Redis available for caching and WebSockets", file=sys.stderr)
except (ImportError, redis.ConnectionError, Exception) as e:
    print(f"⚠️ Redis not available ({e}), using in-memory cache and channels", file=sys.stderr)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'dev-cache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 500,
            }
        },
        # Session cache for development (backward compatibility)
        'sessions': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'dev-sessions',
            'TIMEOUT': 86400,  # 24 hours
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
            }
        }
    }
    
    # In-memory channel layer for development
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        }
    }

# Override session configuration for development (use cache with proper fallback)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 86400  # 24 hours for development convenience
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Allow HTTP in development
SESSION_COOKIE_SAMESITE = 'Lax'

# Enable RAG feature for development since dependencies are compatible
FEATURE_RAG = config('FEATURE_RAG', default=True, cast=bool)

# ==================================================
# CELERY CONFIGURATION
# ==================================================

# Use Redis as the Celery broker and result backend
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/4')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/5')

# Celery task configuration
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Task execution configuration
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

# Worker configuration for Windows
CELERY_WORKER_POOL = 'threads'  # Use threads instead of prefork on Windows
CELERY_WORKER_CONCURRENCY = 2
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Task time limits
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 600       # 10 minutes

# ==================================================
# SOCIAL AUTH CONFIGURATION
# ==================================================

# Social account providers configuration
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
    },
    'github': {
        'SCOPE': [
            'user:email',
        ],
    },
}

# Social account settings
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'  # For development

# Result backend configuration
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Beat schedule configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

print(f"Using settings: {__file__}", file=sys.stderr)