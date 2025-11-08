"""
Enhanced Base Settings for PromptCraft
Professional Production-Ready Configuration

Author: GitHub Copilot
Date: November 2024
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Initialize logger for configuration tracking
logger = logging.getLogger(__name__)

# Try to import decouple with enhanced fallback
try:
    from decouple import config, Csv
    logger.info("Using python-decouple for configuration")
except ImportError:
    logger.warning("python-decouple not available, using environment variables directly")
    
    def config(key: str, default=None, cast=None):
        """Enhanced config function with type casting"""
        value = os.environ.get(key, default)
        if cast and value is not None:
            if cast == bool:
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif cast == Csv:
                return [item.strip() for item in str(value).split(',') if item.strip()]
            elif cast == int:
                return int(value)
            elif cast == float:
                return float(value)
            else:
                return cast(value)
        return value
    
    class Csv:
        @staticmethod
        def __call__(value):
            return [item.strip() for item in str(value).split(',') if item.strip()]

# =============================================================================
# CORE DJANGO SETTINGS
# =============================================================================

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security Settings
SECRET_KEY = config('SECRET_KEY', default="django-insecure-change-me-in-production")
DEBUG = config('DEBUG', default=True, cast=bool)

# Environment detection
ENVIRONMENT = config('DJANGO_ENVIRONMENT', default='development')
IS_PRODUCTION = ENVIRONMENT == 'production'
IS_DEVELOPMENT = ENVIRONMENT == 'development'
IS_TESTING = ENVIRONMENT == 'testing'

# Dynamic ALLOWED_HOSTS based on environment
if IS_PRODUCTION:
    ALLOWED_HOSTS = config(
        'ALLOWED_HOSTS',
        default='localhost,127.0.0.1,http://localhost:3000/',
        cast=Csv
    )
else:
    # Development: Allow common development hosts
    ALLOWED_HOSTS = [
        'localhost',
        'http://localhost:3000/',
        '127.0.0.1',
        '0.0.0.0',
        '10.0.2.2',  # Android AVD emulator
        '10.0.3.2',  # Alternative Android emulator
        '*',  # Allow all for development (not recommended for production)
    ]

# =============================================================================
# INSTALLED APPS CONFIGURATION
# =============================================================================

# Core Django applications
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for social auth
]

# Third-party applications with dynamic loading
THIRD_PARTY_APPS = []

def try_add_app(app_name: str, import_name: str = None) -> bool:
    """Safely add an app if it's installed"""
    try:
        if import_name:
            __import__(import_name)
        else:
            __import__(app_name.replace('.', '/'))
        THIRD_PARTY_APPS.append(app_name)
        logger.info(f"Added {app_name} to INSTALLED_APPS")
        return True
    except ImportError:
        logger.info(f"{app_name} not available, skipping")
        return False

# Essential third-party apps
try_add_app('rest_framework', 'rest_framework')
try_add_app('rest_framework_simplejwt', 'rest_framework_simplejwt')
try_add_app('corsheaders', 'corsheaders')
try_add_app('drf_spectacular', 'drf_spectacular')
try_add_app('channels', 'channels')
try_add_app('django_celery_beat', 'django_celery_beat')
try_add_app('django_celery_results', 'django_celery_results')

# Social authentication
try_add_app('allauth', 'allauth')
try_add_app('allauth.account', 'allauth.account')
try_add_app('allauth.socialaccount', 'allauth.socialaccount')
try_add_app('allauth.socialaccount.providers.google', 'allauth.socialaccount.providers.google')
try_add_app('allauth.socialaccount.providers.github', 'allauth.socialaccount.providers.github')
try_add_app('dj_rest_auth', 'dj_rest_auth')
try_add_app('dj_rest_auth.registration', 'dj_rest_auth.registration')

# Development tools (only in development)
if IS_DEVELOPMENT:
    try_add_app('debug_toolbar', 'debug_toolbar')

# JWT token blacklist (production only)
if IS_PRODUCTION:
    try_add_app('rest_framework_simplejwt.token_blacklist', 'rest_framework_simplejwt.token_blacklist')

# Local applications
LOCAL_APPS = []

# Automatically discover local apps
apps_dir = BASE_DIR / 'apps'
if apps_dir.exists():
    for app_path in apps_dir.iterdir():
        if app_path.is_dir() and (app_path / '__init__.py').exists():
            app_name = f'apps.{app_path.name}'
            LOCAL_APPS.append(app_name)
            logger.info(f"Discovered local app: {app_name}")

# Add research agent
LOCAL_APPS.append('research_agent')

# Combine all apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static file serving
]

# Add CORS middleware if available
if 'corsheaders' in THIRD_PARTY_APPS:
    MIDDLEWARE.append('corsheaders.middleware.CorsMiddleware')

MIDDLEWARE.extend([
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
])

# Custom middleware
MIDDLEWARE.extend([
    'apps.core.middleware.RequestLoggingMiddleware',
    'apps.core.middleware.PerformanceMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
])

# Development middleware
if IS_DEVELOPMENT and 'debug_toolbar' in THIRD_PARTY_APPS:
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

# =============================================================================
# URL AND TEMPLATE CONFIGURATION
# =============================================================================

ROOT_URLCONF = 'promptcraft.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
            ],
        },
    },
]

# =============================================================================
# WSGI/ASGI CONFIGURATION
# =============================================================================

WSGI_APPLICATION = 'promptcraft.wsgi.application'
ASGI_APPLICATION = 'promptcraft.asgi.application'

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Default to SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Override with environment-specific database configuration if provided
database_url = config('DATABASE_URL', default=None)
if database_url:
    try:
        import dj_database_url
        DATABASES['default'] = dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
        logger.info("Using DATABASE_URL for database connection")
    except ImportError:
        logger.warning("dj_database_url not available, using default database configuration")

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

if 'allauth' in THIRD_PARTY_APPS:
    AUTHENTICATION_BACKENDS.append('allauth.account.auth_backends.AuthenticationBackend')

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# =============================================================================
# STATIC AND MEDIA FILES
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Static file storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Cache configuration with Redis fallback
REDIS_URL = config('REDIS_URL', default=None)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'default-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sessions-cache',
        'TIMEOUT': 86400,
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
        }
    }
}

if REDIS_URL:
    try:
        import redis
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()
        
        # Redis is available
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"{REDIS_URL}/1",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'CONNECTION_POOL_KWARGS': {
                        'max_connections': 50,
                        'retry_on_timeout': True,
                    },
                },
                'KEY_PREFIX': 'promptcraft',
                'TIMEOUT': 300,
            },
            'sessions': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"{REDIS_URL}/2",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                },
                'KEY_PREFIX': 'session',
                'TIMEOUT': 86400,
            }
        }
        logger.info("Redis cache enabled")
    except (ImportError, Exception) as e:
        logger.warning(f"Redis not available ({e}), using local memory cache")

# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = IS_PRODUCTION
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = False

# =============================================================================
# CHANNELS CONFIGURATION
# =============================================================================

if 'channels' in THIRD_PARTY_APPS:
    if REDIS_URL:
        try:
            import channels_redis
            CHANNEL_LAYERS = {
                'default': {
                    'BACKEND': 'channels_redis.core.RedisChannelLayer',
                    'CONFIG': {
                        'hosts': [f"{REDIS_URL}/3"],
                        'capacity': 1500,
                        'expiry': 60,
                        'symmetric_encryption_keys': [
                            config('CHANNEL_LAYER_SECRET', default='change-me-in-production')
                        ],
                    },
                },
            }
            logger.info("Redis channel layer enabled")
        except ImportError:
            CHANNEL_LAYERS = {
                'default': {
                    'BACKEND': 'channels.layers.InMemoryChannelLayer'
                }
            }
            logger.info("Using in-memory channel layer")
    else:
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer'
            }
        }

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

if REDIS_URL:
    CELERY_BROKER_URL = f"{REDIS_URL}/4"
    CELERY_RESULT_BACKEND = f"{REDIS_URL}/4"
else:
    CELERY_BROKER_URL = 'redis://localhost:6379/4'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/4'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

if 'corsheaders' in THIRD_PARTY_APPS:
    if IS_PRODUCTION:
        CORS_ALLOWED_ORIGINS = config(
            'CORS_ALLOWED_ORIGINS',
            default='https://prompt-temple.com,https://www.prompt-temple.com,http://localhost:3000/',
            cast=Csv
        )
        CORS_ALLOW_ALL_ORIGINS = True
    else:
        # Development CORS settings
        CORS_ALLOWED_ORIGINS = [
            'http://localhost:3000',
            'http://localhost:3001',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:3001',
            'http://10.0.2.2:8000',  # Android emulator
            'http://10.0.2.2:3000',
        ]
        CORS_ALLOW_ALL_ORIGINS = IS_DEVELOPMENT
    
    CORS_ALLOW_CREDENTIALS = True
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
        'x-client-version',
        'x-request-id',
        'x-correlation-id',
        'cache-control',
        'pragma',
        
    ]
    
    CORS_EXPOSE_HEADERS = [
        'x-request-id',
        'x-correlation-id',
        'x-ratelimit-limit',
        'x-ratelimit-remaining',
        'x-ratelimit-reset',
    ]
    
    CORS_ALLOW_METHODS = [
        'DELETE',
        'GET',
        'OPTIONS',
        'PATCH',
        'POST',
        'PUT',
    ]
    
    CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours

# =============================================================================
# REST FRAMEWORK CONFIGURATION
# =============================================================================

if 'rest_framework' in THIRD_PARTY_APPS:
    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework_simplejwt.authentication.JWTAuthentication',
            'rest_framework.authentication.SessionAuthentication',
        ],
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
        ],
        'DEFAULT_PARSER_CLASSES': [
            'rest_framework.parsers.JSONParser',
            'rest_framework.parsers.FormParser',
            'rest_framework.parsers.MultiPartParser',
        ],
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '100/hour' if IS_PRODUCTION else '1000/hour',
            'user': '1000/hour' if IS_PRODUCTION else '5000/hour',
        },
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 25,
        'DEFAULT_FILTER_BACKENDS': [
            'django_filters.rest_framework.DjangoFilterBackend',
            'rest_framework.filters.SearchFilter',
            'rest_framework.filters.OrderingFilter',
        ],
    }
    
    # Add browsable API for development
    if IS_DEVELOPMENT:
        REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
            'rest_framework.renderers.BrowsableAPIRenderer'
        )
    
    # Add schema class if spectacular is available
    if 'drf_spectacular' in THIRD_PARTY_APPS:
        REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'

# =============================================================================
# JWT CONFIGURATION
# =============================================================================

if 'rest_framework_simplejwt' in THIRD_PARTY_APPS:
    from datetime import timedelta
    
    SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
        'REFRESH_TOKEN_LIFETIME': timedelta(days=7 if IS_PRODUCTION else 30),
        'ROTATE_REFRESH_TOKENS': True,
        'BLACKLIST_AFTER_ROTATION': IS_PRODUCTION,
        'UPDATE_LAST_LOGIN': True,
        
        'ALGORITHM': 'HS256',
        'SIGNING_KEY': SECRET_KEY,
        'VERIFYING_KEY': None,
        'AUDIENCE': None,
        'ISSUER': 'PromptCraft',
        'JWK_URL': None,
        'LEEWAY': 10,
        
        'AUTH_HEADER_TYPES': ('Bearer',),
        'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
        'USER_ID_FIELD': 'id',
        'USER_ID_CLAIM': 'user_id',
        'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
        
        'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
        'TOKEN_TYPE_CLAIM': 'token_type',
        'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
        
        'JTI_CLAIM': 'jti',
    }

# =============================================================================
# API DOCUMENTATION CONFIGURATION
# =============================================================================

if 'drf_spectacular' in THIRD_PARTY_APPS:
    SPECTACULAR_SETTINGS = {
        'TITLE': 'PromptCraft API',
        'DESCRIPTION': 'Professional AI Prompt Management Platform API',
        'VERSION': '2.0.0',
        'SERVE_INCLUDE_SCHEMA': False,
        'SCHEMA_PATH_PREFIX': '/api/',
        'COMPONENT_SPLIT_REQUEST': True,
        'SORT_OPERATIONS': True,
        'ENABLE_DJANGO_DEPLOY_CHECK': False,
        'DISABLE_ERRORS_AND_WARNINGS': IS_PRODUCTION,
        'SERVE_AUTHENTICATION': [
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ],
        'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
        'SWAGGER_UI_SETTINGS': {
            'deepLinking': True,
            'persistAuthorization': True,
            'displayOperationId': True,
            'displayRequestDuration': True,
            'filter': True,
            'tryItOutEnabled': not IS_PRODUCTION,
        },
        'REDOC_UI_SETTINGS': {
            'hideDownloadButton': IS_PRODUCTION,
        },
    }

# =============================================================================
# SOCIAL AUTHENTICATION CONFIGURATION
# =============================================================================

if 'allauth' in THIRD_PARTY_APPS:
    SITE_ID = 1
    
    # Allauth settings
    ACCOUNT_AUTHENTICATION_METHOD = 'email'
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_EMAIL_VERIFICATION = 'none'  # Simplified for development
    ACCOUNT_UNIQUE_EMAIL = True
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
    ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
    
    # Social account settings
    SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
    SOCIALACCOUNT_EMAIL_REQUIRED = True
    SOCIALACCOUNT_AUTO_SIGNUP = True
    SOCIALACCOUNT_QUERY_EMAIL = True
    SOCIALACCOUNT_STORE_TOKENS = True
    
    # Social providers
    SOCIALACCOUNT_PROVIDERS = {
        'google': {
            'SCOPE': ['profile', 'email'],
            'AUTH_PARAMS': {'access_type': 'online'},
            'OAUTH_PKCE_ENABLED': True,
            'FETCH_USERINFO': True,
            'APP': {
                'client_id': config('GOOGLE_OAUTH2_CLIENT_ID', default=''),
                'secret': config('GOOGLE_OAUTH2_CLIENT_SECRET', default=''),
            }
        },
        'github': {
            'SCOPE': ['user:email', 'read:user'],
            'VERIFIED_EMAIL': True,
            'APP': {
                'client_id': config('GITHUB_CLIENT_ID', default=''),
                'secret': config('GITHUB_CLIENT_SECRET', default=''),
            }
        }
    }

# =============================================================================
# AI SERVICES CONFIGURATION
# =============================================================================

# DeepSeek API Configuration
DEEPSEEK_CONFIG = {
    'API_KEY': config('DEEPSEEK_API_KEY', default=''),
    'BASE_URL': config('DEEPSEEK_BASE_URL', default='https://api.deepseek.com'),
    'DEFAULT_MODEL': config('DEEPSEEK_DEFAULT_MODEL', default='deepseek-chat'),
    'REASONER_MODEL': config('DEEPSEEK_REASONER_MODEL', default='deepseek-reasoner'),
    'CODER_MODEL': config('DEEPSEEK_CODER_MODEL', default='deepseek-coder'),
    'MATH_MODEL': config('DEEPSEEK_MATH_MODEL', default='deepseek-math'),
    'MAX_TOKENS': config('DEEPSEEK_MAX_TOKENS', default=4096, cast=int),
    'TEMPERATURE': config('DEEPSEEK_TEMPERATURE', default=0.7, cast=float),
    'TIMEOUT': config('DEEPSEEK_TIMEOUT', default=30, cast=int),
}

# OpenAI Configuration (fallback)
OPENAI_CONFIG = {
    'API_KEY': config('OPENAI_API_KEY', default=''),
    'DEFAULT_MODEL': config('OPENAI_DEFAULT_MODEL', default='gpt-4'),
    'MAX_TOKENS': config('OPENAI_MAX_TOKENS', default=4096, cast=int),
    'TEMPERATURE': config('OPENAI_TEMPERATURE', default=0.7, cast=float),
    'TIMEOUT': config('OPENAI_TIMEOUT', default=30, cast=int),
}

# Research Agent Configuration
RESEARCH_CONFIG = {
    'EMBED_MODEL': config('RESEARCH_EMBED_MODEL', default='sentence-transformers/all-MiniLM-L6-v2'),
    'SEARCH_PROVIDER': config('RESEARCH_SEARCH_PROVIDER', default='tavily'),
    'SEARCH_TOP_K': config('RESEARCH_SEARCH_TOP_K', default=8, cast=int),
    'FETCH_TIMEOUT_S': config('RESEARCH_FETCH_TIMEOUT_S', default=15, cast=int),
    'MAX_PAGES': config('RESEARCH_MAX_PAGES', default=12, cast=int),
    'MAX_TOKENS_PER_CHUNK': config('RESEARCH_MAX_TOKENS_PER_CHUNK', default=800, cast=int),
    'CHUNK_OVERLAP_TOKENS': config('RESEARCH_CHUNK_OVERLAP_TOKENS', default=120, cast=int),
    'ANSWER_MODEL': config('RESEARCH_ANSWER_MODEL', default='deepseek-chat'),
    'RATE_LIMIT_DEMO': config('RESEARCH_RATE_LIMIT_DEMO', default='10/5m'),
}

# Tavily API Key
TAVILY_API_KEY = config('TAVILY_API_KEY', default='')

# =============================================================================
# CHAT AND STREAMING CONFIGURATION
# =============================================================================

CHAT_TRANSPORT = config('CHAT_TRANSPORT', default='sse')  # 'sse' or 'ws'

SSE_HEADERS = {
    'Cache-Control': 'no-cache',
    'X-Accel-Buffering': 'no',
    'X-Content-Type-Options': 'nosniff',
}

# WebSocket settings
WEBSOCKET_SETTINGS = {
    'WEBSOCKET_URL': config('WEBSOCKET_URL', default='ws://localhost:8000'),
    'WEBSOCKET_TIMEOUT': config('WEBSOCKET_TIMEOUT', default=86400, cast=int),
    'WEBSOCKET_CONNECT_TIMEOUT': config('WEBSOCKET_CONNECT_TIMEOUT', default=10, cast=int),
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Create logs directory
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {name} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "{levelname}", "time": "{asctime}", "name": "{name}", "message": "{message}"}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'promptcraft': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY' if IS_PRODUCTION else 'SAMEORIGIN'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# HTTPS settings (production only)
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Cookie security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Strict'

# =============================================================================
# PERFORMANCE CONFIGURATION
# =============================================================================

# Database optimization
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# File upload settings
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Feature flags
FEATURE_FLAGS = {
    'RAG_ENABLED': config('FEATURE_RAG', default=False, cast=bool),
    'SOCIAL_AUTH_ENABLED': 'allauth' in THIRD_PARTY_APPS,
    'WEBSOCKETS_ENABLED': 'channels' in THIRD_PARTY_APPS,
    'CELERY_ENABLED': 'django_celery_beat' in THIRD_PARTY_APPS,
    'DEBUG_TOOLBAR_ENABLED': 'debug_toolbar' in THIRD_PARTY_APPS and IS_DEVELOPMENT,
}

# =============================================================================
# DEBUG TOOLBAR CONFIGURATION
# =============================================================================

if IS_DEVELOPMENT and 'debug_toolbar' in THIRD_PARTY_APPS:
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
        '10.0.2.2',  # Android emulator
    ]
    
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'SHOW_COLLAPSED': True,
        'INTERCEPT_REDIRECTS': False,
    }

# =============================================================================
# CUSTOM SETTINGS VALIDATION
# =============================================================================

def validate_settings():
    """Validate critical settings and log warnings"""
    warnings = []
    
    if SECRET_KEY == "django-insecure-change-me-in-production":
        warnings.append("SECRET_KEY is using default value - change in production!")
    
    if IS_PRODUCTION and DEBUG:
        warnings.append("DEBUG is True in production environment!")
    
    if IS_PRODUCTION and not REDIS_URL:
        warnings.append("Redis not configured for production - using local memory cache")
    
    if not DEEPSEEK_CONFIG['API_KEY'] and not OPENAI_CONFIG['API_KEY']:
        warnings.append("No AI API keys configured - AI features will not work")
    
    for warning in warnings:
        logger.warning(warning)

# Run settings validation
validate_settings()

# Log configuration summary
logger.info(f"Settings loaded for environment: {ENVIRONMENT}")
logger.info(f"Debug mode: {DEBUG}")
logger.info(f"Database engine: {DATABASES['default']['ENGINE']}")
logger.info(f"Cache backend: {CACHES['default']['BACKEND']}")
logger.info(f"Installed apps: {len(INSTALLED_APPS)}")
logger.info(f"Feature flags: {FEATURE_FLAGS}")