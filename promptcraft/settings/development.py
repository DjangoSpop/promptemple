from .base import *
import sys
import os
from pathlib import Path

DEBUG = True  # Enable debug for development
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    '10.0.2.2',  # Android AVD emulator
    '0.0.0.0',
    '*',  # Allow all hosts in development
]

# Database for development with fallback to SQLite
# Try PostgreSQL first, fallback to SQLite if PostgreSQL is not available
USE_POSTGRES = config('USE_POSTGRES', default=True, cast=bool)

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

# REST Framework configuration for development
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Development-friendly: allow any and disable mandatory authentication to
    # make local frontend integration easier. Do NOT use in production.
    # In development we still want to be able to test authenticated endpoints
    # so enable JWT and session authentication. Keep AllowAny as the default
    # permission class but individual views may set IsAuthenticated as needed.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
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

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://10.0.2.2:8000",
    "http://0.0.0.0",# Android AVD accessing Django
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  # Allow all origins in development
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
    'x-client-version',  # Allow frontend client version header
    'x-request-id',      # Allow frontend request ID header
]

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

print(f"Using settings: {__file__}", file=sys.stderr)