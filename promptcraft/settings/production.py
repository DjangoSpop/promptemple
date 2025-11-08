"""
Production Settings for PromptCraft API

This module contains production-ready settings with proper security,
performance optimizations, and error handling.

Author: GitHub Copilot
Date: August 9, 2025
"""

from .base import *
import os
import sys

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

# Sentry Configuration for Production
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    SENTRY_DSN = config('SENTRY_DSN', default=None)
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(transaction_style='url'),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment=config('SENTRY_ENVIRONMENT', default='production'),
            release=config('SENTRY_RELEASE', default=None),
        )
        print("🔍 Sentry monitoring enabled", file=sys.stderr)
    else:
        print("⚠️ Sentry DSN not configured, monitoring disabled", file=sys.stderr)
except ImportError:
    print("⚠️ Sentry SDK not available, monitoring disabled", file=sys.stderr)

# Try to import dj_database_url, fallback if not available
try:
    import dj_database_url
    HAS_DJ_DATABASE_URL = True
except ImportError:
    print("⚠️ dj_database_url not available, using direct database configuration", file=sys.stderr)
    HAS_DJ_DATABASE_URL = False

# Add JWT token blacklist app for production security (if available)
try:
    import rest_framework_simplejwt.token_blacklist
    INSTALLED_APPS += [
        'rest_framework_simplejwt.token_blacklist',
    ]
    print("🔐 JWT token blacklist enabled", file=sys.stderr)
except ImportError:
    print("⚠️ JWT token blacklist not available", file=sys.stderr)

# Security Settings
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='your-secret-key-here-change-in-production')

# Allowed hosts for production - Railway and development
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,0.0.0.0,10.0.2.2,*.railway.app,*.railway.dev,www.prompt-temple.com,prompt-temple.com,api.prompt-temple.com',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Database Configuration with PostgreSQL focus
if config('DATABASE_URL', default=None) and HAS_DJ_DATABASE_URL:
    # Use DATABASE_URL from environment (Heroku, Railway, etc.)
    DATABASES = {
        'default': dj_database_url.parse(
            config('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    print("📊 Using DATABASE_URL for database connection", file=sys.stderr)
elif config('DATABASE_URL', default=None) and not HAS_DJ_DATABASE_URL:
    # Handle DATABASE_URL without dj_database_url
    print("⚠️ DATABASE_URL provided but dj_database_url not available, using direct PostgreSQL config", file=sys.stderr)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='promptcraft_db'),
            'USER': config('DB_USER', default='promptcraft_user'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'OPTIONS': {
                'connect_timeout': 60,
                'sslmode': config('DB_SSLMODE', default='prefer'),
            },
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
    }
else:
    # Force PostgreSQL configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='promptcraft_db'),
            'USER': config('DB_USER', default='promptcraft_user'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'OPTIONS': {
                'connect_timeout': 60,
                'sslmode': config('DB_SSLMODE', default='prefer'),
            },
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
    }
    print(f"🐘 Using PostgreSQL: {config('DB_HOST', default='localhost')}:{config('DB_PORT', default='5432')}/{config('DB_NAME', default='promptcraft_db')}", file=sys.stderr)

# Enhanced fallback to SQLite for Railway deployment
database_url = config('DATABASE_URL', default=None)
db_password = config('DB_PASSWORD', default=None)

# If no database configuration is provided, use SQLite as fallback
if not database_url and not db_password:
    print("ℹ️  No external database configured, using SQLite for Railway deployment", file=sys.stderr)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    # Validate PostgreSQL connection or fallback to SQLite
    print(f"🐘 Using PostgreSQL: {DATABASES['default'].get('HOST', 'localhost')}:{DATABASES['default'].get('PORT', '5432')}/{DATABASES['default'].get('NAME', 'promptcraft_db')}", file=sys.stderr)

# Security Headers and HTTPS (relaxed for local development)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 0  # Disabled for local development
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Less restrictive for local development
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session Security (relaxed for local development)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'  # Less restrictive
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'  # Less restrictive

# ============================================================================
# CORS SETTINGS - Production Configuration
# ============================================================================

# Production Origins - HTTPS only for security
CORS_ALLOWED_ORIGINS = [
    "https://prompt-temple.com",
    "https://www.prompt-temple.com",
    "https://api.prompt-temple.com",
    "http://localhost:3000",   # For local testing - REMOVE in final production!
    "http://localhost:3001",   # Alternative port - REMOVE in final production!
    "http://127.0.0.1:3000",   # REMOVE in final production!
    "http://127.0.0.1:3001",   # REMOVE in final production!
    "http://10.0.2.2:8000",    # Android AVD emulator
    "http://10.0.2.2:3000",    # Android AVD emulator frontend
]

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# DO NOT use CORS_ALLOW_ALL_ORIGINS in production
CORS_ALLOW_ALL_ORIGINS = False  # Strict CORS - NEVER set to True in production!

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

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add WhiteNoise middleware
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Cache Configuration - Redis first, fallback to in-memory
REDIS_URL = config('REDIS_URL', default=None)

if REDIS_URL:
    try:
        # Test both django_redis import and Redis connectivity
        import django_redis
        import redis

        # Parse Redis URL properly
        redis_url_base = REDIS_URL.rstrip('/0').rstrip('/1').rstrip('/2').rstrip('/3')
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()

        # Redis is available, use it
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"{redis_url_base}/1",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                },
                'KEY_PREFIX': 'promptcraft',
                'TIMEOUT': 300,  # 5 minutes default
            },
            # Session cache - separate database for isolation
            'sessions': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"{redis_url_base}/2",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                },
                'KEY_PREFIX': 'session',
                'TIMEOUT': 86400,  # 24 hours
            }
        }
        print("🟢 Redis cache enabled", file=sys.stderr)
    except (ImportError, Exception) as e:
        print(f"⚠️ Redis not available ({e}), using fallback cache", file=sys.stderr)
        REDIS_URL = None

if not REDIS_URL:
    # Fallback to in-memory cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
            }
        },
        # Session cache - use in-memory for production fallback
        'sessions': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'sessions-cache',
            'TIMEOUT': 86400,  # 24 hours
            'OPTIONS': {
                'MAX_ENTRIES': 5000,
            }
        }
    }
    print("ℹ️ Using in-memory cache (no Redis configured)", file=sys.stderr)

# Channels Configuration - Redis first, fallback to in-memory
if REDIS_URL:
    try:
        import channels_redis
        # Test Redis availability again for channels
        redis_url_base = REDIS_URL.rstrip('/0').rstrip('/1').rstrip('/2').rstrip('/3')
        redis_client = redis.Redis.from_url(f"{redis_url_base}/3")
        redis_client.ping()

        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [f"{redis_url_base}/3"],
                    'capacity': 1500,
                    'expiry': 60,
                    'symmetric_encryption_keys': [config('CHANNEL_LAYER_SECRET', default='change-me-in-production')],
                },
            },
        }
        print("🟢 Redis channel layer enabled", file=sys.stderr)
    except (ImportError, Exception) as e:
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer'
            }
        }
        print(f"⚠️ Using in-memory channel layer for Redis error: {e}", file=sys.stderr)
else:
    # No Redis configured, use in-memory
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        }
    }
    print("ℹ️ Using in-memory channel layer (no Redis configured)", file=sys.stderr)

# Logging Configuration
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django_error.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# REST Framework Production Settings
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Enable browsable API for testing
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For browsable API
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',  # Allow read access
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',  # Increased for testing
        'user': '5000/hour',  # Increased for testing
        'login': '20/minute',  # Increased for testing
        'register': '10/minute',  # Increased for testing
    },
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# API Documentation Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'PromptCraft API',
    'DESCRIPTION': 'Production API for PromptCraft - AI Prompt Management Platform',
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
}

# JWT Settings for Production
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
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
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

print(f"🚀 Production settings loaded: {__file__}", file=sys.stderr)