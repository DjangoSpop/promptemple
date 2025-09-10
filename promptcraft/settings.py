"""
Django settings for promptcraft project.
Basic configuration for development.
"""

import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from pathlib import Path

# Try to import decouple, fallback to os.environ if not available
try:
    from decouple import config, Csv
except ImportError:
    def config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            if cast == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            elif cast == Csv:
                return [item.strip() for item in value.split(',') if item.strip()]
            else:
                return cast(value)
        return value
    
    class Csv:
        @staticmethod
        def __call__(value):
            return [item.strip() for item in value.split(',') if item.strip()]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
APPEND_SLASH=False
# Basic development settings
SECRET_KEY = config('SECRET_KEY', default="django-insecure-=$&0cpo9(=xihchk^!6p&#um-7icn@#u4ut)04sqcxs6__i+gd")
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS configuration
if DEBUG:
    # Development - allow all hosts for mobile testing
    ALLOWED_HOSTS = ['*']
else:
    # Production - specific domains only
    ALLOWED_HOSTS = [
        'floating-chamber-26624-41879340871a.herokuapp.com',
        'www.prompt-temple.com',
        'prompt-temple.com',
    ]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # or BASE_DIR / 'templates' if using pathlib
        'APP_DIRS': True,  # This is crucial for admin and debug toolbar
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
# Application definition - only include apps that exist
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    # API framework
    'rest_framework',
    'rest_framework_simplejwt',
    # 'drf_spectacular',  # Commented out - not installed
    # CORS handling
    'corsheaders',
    # WebSocket support
    'channels',
    # Debug tools (only in development)
]

# Conditionally add development tools
if DEBUG:
    try:
        import debug_toolbar
        THIRD_PARTY_APPS.append('debug_toolbar')
    except ImportError:
        pass

LOCAL_APPS = [
    # Only add apps that actually exist
]

# Check which local apps exist and add them
apps_dir = BASE_DIR / 'apps'
if apps_dir.exists():
    for app_path in apps_dir.iterdir():
        if app_path.is_dir() and (app_path / '__init__.py').exists():
            LOCAL_APPS.append(f'apps.{app_path.name}')

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Must be early in the list
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Add debug toolbar middleware if installed and in debug mode
if DEBUG and 'debug_toolbar' in THIRD_PARTY_APPS:
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "promptcraft.urls"

# Ensure a proper DjangoTemplates backend is configured



WSGI_APPLICATION = "promptcraft.wsgi.application"
ASGI_APPLICATION = "promptcraft.asgi.application"

# Channels and WebSocket Configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config('REDIS_URL', default='redis://localhost:6379/0')],
            "symmetric_encryption_keys": [config('CHANNEL_LAYER_SECRET', default='secret-key')],
        },
    },
}

# Sentry Configuration for Error Monitoring
SENTRY_DSN = config('SENTRY_DSN', default=None)
if SENTRY_DSN:
    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(
                    transaction_capture=True,
                    middleware_spans=True,
                    signals_spans=False,
                    cache_spans=True,
                ),
                CeleryIntegration(
                    monitor_beat_tasks=True,
                    propagate_traces=True,
                ),
                RedisIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1 if not DEBUG else 1.0,
            send_default_pii=False,
            attach_stacktrace=True,
            environment='production' if not DEBUG else 'development',
            release=config('APP_VERSION', default='1.0.0'),
        )
    except Exception as e:
        print(f"Sentry initialization failed: {e}")

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Custom User Model
AUTH_USER_MODEL = 'apps.users.User'

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Debug Toolbar Settings (only if installed)
if 'debug_toolbar' in THIRD_PARTY_APPS:
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
        "10.0.2.2",  # Android emulator
    ]

# CORS settings for mobile development
if 'corsheaders' in THIRD_PARTY_APPS:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://10.0.2.2:8000",  # Android emulator
        "http://10.0.3.2:8000",  # Alternative Android emulator
        "https://YOUR-FRONTEND-DOMAIN",  # Production frontend domain
    ]
    CORS_ALLOW_CREDENTIALS = True
    # Allow all origins in development for mobile testing
    if DEBUG:
        CORS_ALLOW_ALL_ORIGINS = True
    
    # Allow custom headers from frontend
    CORS_ALLOWED_HEADERS = [
        'accept',
        'accept-encoding',
        'accept-language',
        'authorization',
        'cache-control',
        'content-type',
        'dnt',
        'origin',
        'pragma',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
        'x-client-version',  # Custom frontend header
        'x-client-name',     # Custom frontend header
        'x-request-id',      # Custom frontend header
    ]

# REST Framework settings (JWT-only authentication to avoid session dependency)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',  # Disabled to avoid session issues
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'chat_completions': '5/min',  # Conservative rate for SSE streaming
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # 'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # Commented out - not installed
}

# DRF Spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'PromptCraft API',
    'DESCRIPTION': 'API for PromptCraft application',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# JWT settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# Feature Flags
FEATURE_RAG = config('FEATURE_RAG', default=False, cast=bool)

# LangChain and AI Search Configuration
LANGCHAIN_SETTINGS = {
    # DeepSeek API (Budget-friendly primary choice)
    'DEEPSEEK_API_KEY': config('DEEPSEEK_API_KEY', default='sk-fad996d33334443dab24fcd669653814'),
    'DEEPSEEK_BASE_URL': config('DEEPSEEK_BASE_URL', default='https://api.deepseek.com'),
    'DEEPSEEK_DEFAULT_MODEL': config('DEEPSEEK_DEFAULT_MODEL', default='deepseek-chat'),
    'DEEPSEEK_REASONER_MODEL': config('DEEPSEEK_REASONER_MODEL', default='deepseek-reasoner'),
    'DEEPSEEK_CODER_MODEL': config('DEEPSEEK_CODER_MODEL', default='deepseek-coder'),
    
    # OpenAI API (Fallback option)
    'OPENAI_API_KEY': config('OPENAI_API_KEY', default=None),
    'ANTHROPIC_API_KEY': config('ANTHROPIC_API_KEY', default=None),
    
    # Model preferences (DeepSeek first, then OpenAI)
    'AI_PROVIDER_PRIORITY': ['deepseek', 'openai', 'anthropic'],
    'ENABLE_AI_FALLBACK': config('ENABLE_AI_FALLBACK', default=True, cast=bool),
    
    # Search and embedding settings
    'EMBEDDING_MODEL': config('EMBEDDING_MODEL', default='all-MiniLM-L6-v2'),
    'SEARCH_INDEX_PATH': BASE_DIR / 'search_index',
    'SIMILARITY_THRESHOLD': float(config('SIMILARITY_THRESHOLD', default='0.7')),
    'MAX_SEARCH_RESULTS': int(config('MAX_SEARCH_RESULTS', default='10')),
    
    # Performance settings
    'AI_REQUEST_TIMEOUT': int(config('AI_REQUEST_TIMEOUT', default='30')),
    'AI_MAX_RETRIES': int(config('AI_MAX_RETRIES', default='3')),
    'AI_RATE_LIMIT_PER_MINUTE': int(config('AI_RATE_LIMIT_PER_MINUTE', default='60')),
}

# Session Configuration (using signed cookies to avoid cache dependency)
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG  # Only over HTTPS in production
SESSION_COOKIE_SAMESITE = 'Lax'
# No SESSION_CACHE_ALIAS needed for signed_cookies backend

# Cache Configuration (with sessions backend)
REDIS_URL = config('REDIS_URL', default=None)

if REDIS_URL:
    # Redis-based caching with separate sessions cache
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'default',
            'TIMEOUT': 300,  # 5 minutes default timeout
        },
        'sessions': {
            'BACKEND': 'django_redis.cache.RedisCache', 
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'sessions',
            'TIMEOUT': 86400,  # 24 hours for sessions
        }
    }
else:
    # Fallback to local memory cache for development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
        'sessions': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Celery Configuration for Background Tasks
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/2')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Search and AI specific settings
SEARCH_SETTINGS = {
    'ENABLE_VECTOR_SEARCH': config('ENABLE_VECTOR_SEARCH', default=True, cast=bool),
    'REINDEX_ON_STARTUP': config('REINDEX_ON_STARTUP', default=False, cast=bool),
    'BATCH_SIZE': int(config('SEARCH_BATCH_SIZE', default='100')),
    'UPDATE_FREQUENCY': int(config('INDEX_UPDATE_FREQUENCY', default='3600')),  # seconds
}

# ==================================================
# CHAT STREAMING & SSE CONFIGURATION
# ==================================================

# Chat Transport Mode (ws or sse)
CHAT_TRANSPORT = config('CHAT_TRANSPORT', default='sse')  # values: "sse" | "ws"

# External AI Provider Configuration (for SSE proxy)
ZAI_API_TOKEN = config('ZAI_API_TOKEN', default='')
ZAI_API_BASE = config('ZAI_API_BASE', default='https://api.z.ai/api/paas/v4')

# Security Headers for Proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SSE Response Headers
SSE_HEADERS = {
    'Cache-Control': 'no-cache',
    'X-Accel-Buffering': 'no',  # Nginx: prevent proxy buffering
    'X-Content-Type-Options': 'nosniff',
}

# Z.AI API Configuration
ZAI_CONFIG = {
    'API_TOKEN': config('ZAI_API_TOKEN', default=''),
    'BASE_URL': config('ZAI_API_BASE', default='https://api.z.ai/api/paas/v4'),
    'DEFAULT_MODEL': config('ZAI_DEFAULT_MODEL', default='glm-4-32b-0414-128k'),
    'MAX_TOKENS': int(config('ZAI_MAX_TOKENS', default='4096')),
    'TEMPERATURE': float(config('ZAI_TEMPERATURE', default='0.7')),
    'TIMEOUT': int(config('ZAI_TIMEOUT', default='30')),
}

# DeepSeek API Configuration (V3.1 compatible)
DEEPSEEK_CONFIG = {
    'API_KEY': config('DEEPSEEK_API_KEY', default='sk-fad996d33334443dab24fcd669653814'),
    'BASE_URL': config('DEEPSEEK_BASE_URL', default='https://api.deepseek.com'),
    'DEFAULT_MODEL': config('DEEPSEEK_DEFAULT_MODEL', default='deepseek-chat'),
    'REASONER_MODEL': config('DEEPSEEK_REASONER_MODEL', default='deepseek-reasoner'),
    'CODER_MODEL': config('DEEPSEEK_CODER_MODEL', default='deepseek-coder'),
    'MATH_MODEL': config('DEEPSEEK_MATH_MODEL', default='deepseek-math'),
    'MAX_TOKENS': int(config('DEEPSEEK_MAX_TOKENS', default='4096')),
    'TEMPERATURE': float(config('DEEPSEEK_TEMPERATURE', default='0.7')),
    'TIMEOUT': int(config('DEEPSEEK_TIMEOUT', default='30')),
}
