"""
Enhanced Production Settings for PromptCraft
Enterprise-Grade Configuration with Advanced Security and Monitoring

Author: GitHub Copilot
Date: November 2024
"""

from .enhanced_base import *
import sys
import os

# =============================================================================
# PRODUCTION ENVIRONMENT OVERRIDES
# =============================================================================

# Force production mode
DEBUG = False
ENVIRONMENT = 'production'
IS_PRODUCTION = True
IS_DEVELOPMENT = False

# Enhanced secret key validation
SECRET_KEY = config('SECRET_KEY')
if not SECRET_KEY or SECRET_KEY == "django-insecure-change-me-in-production":
    raise ValueError("SECRET_KEY must be set to a secure value in production")

# Strict allowed hosts
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv
)

# Additional production hosts
PRODUCTION_HOSTS = config('PRODUCTION_HOSTS', default='', cast=Csv)
if PRODUCTION_HOSTS:
    ALLOWED_HOSTS.extend(PRODUCTION_HOSTS)

# Railway-specific hosts
RAILWAY_HOSTS = config('RAILWAY_HOSTS', default='*.railway.app,*.railway.dev', cast=Csv)
ALLOWED_HOSTS.extend(RAILWAY_HOSTS)

# =============================================================================
# ENHANCED DATABASE CONFIGURATION
# =============================================================================

# Production database with connection pooling
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True,
                ssl_require=config('DB_SSL_REQUIRE', default=True, cast=bool),
            )
        }
        
        # Add connection pooling if available
        try:
            import psycopg2.pool
            DATABASES['default']['OPTIONS'] = {
                'MAX_CONNS': config('DB_MAX_CONNECTIONS', default=20, cast=int),
                'OPTIONS': {
                    'MAX_CONNS': config('DB_MAX_CONNECTIONS', default=20, cast=int),
                }
            }
        except ImportError:
            pass
            
        logger.info("Production database configured with connection pooling")
    except ImportError:
        logger.error("dj_database_url required for production DATABASE_URL")
        sys.exit(1)
else:
    # Manual PostgreSQL configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'OPTIONS': {
                'connect_timeout': 60,
                'sslmode': config('DB_SSLMODE', default='require'),
                'options': '-c default_transaction_isolation=read_committed'
            },
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
    }

# Database backup settings
DATABASE_BACKUP = {
    'ENABLED': config('DB_BACKUP_ENABLED', default=True, cast=bool),
    'RETENTION_DAYS': config('DB_BACKUP_RETENTION', default=30, cast=int),
    'S3_BUCKET': config('DB_BACKUP_S3_BUCKET', default=''),
}

# =============================================================================
# ENHANCED CACHE CONFIGURATION
# =============================================================================

REDIS_URL = config('REDIS_URL')
if not REDIS_URL:
    logger.error("REDIS_URL is required for production")
    sys.exit(1)

try:
    import redis
    import django_redis
    
    # Test Redis connection
    redis_client = redis.Redis.from_url(REDIS_URL)
    redis_client.ping()
    
    # Production Redis configuration with clustering support
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f"{REDIS_URL}/1",
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 100,
                    'retry_on_timeout': True,
                    'health_check_interval': 30,
                },
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'IGNORE_EXCEPTIONS': True,
            },
            'KEY_PREFIX': 'promptcraft_prod',
            'TIMEOUT': 300,
            'VERSION': 1,
        },
        'sessions': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f"{REDIS_URL}/2",
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
            },
            'KEY_PREFIX': 'session_prod',
            'TIMEOUT': 86400,
        },
        'rate_limit': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f"{REDIS_URL}/3",
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'rate_limit',
            'TIMEOUT': 3600,
        }
    }
    
    logger.info("Production Redis cache configured with clustering support")
    
except (ImportError, Exception) as e:
    logger.error(f"Redis configuration failed: {e}")
    sys.exit(1)

# =============================================================================
# ENHANCED SECURITY CONFIGURATION
# =============================================================================

# HTTPS enforcement
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS settings
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Cookie security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Content Security Policy
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net']
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com']
CSP_FONT_SRC = ["'self'", 'https://fonts.gstatic.com']
CSP_IMG_SRC = ["'self'", 'data:', 'https:']
CSP_CONNECT_SRC = ["'self'", 'https://api.deepseek.com', 'https://api.openai.com']

# =============================================================================
# ENHANCED CORS CONFIGURATION
# =============================================================================

# Production CORS - strict origins only
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://prompt-temple.com,https://www.prompt-temple.com,https://api.prompt-temple.com',
    cast=Csv
)

# No wildcard origins in production
CORS_ALLOW_ALL_ORIGINS = False

# Enhanced CORS headers
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
    'x-api-key',
    'cache-control',
    'pragma',
]

CORS_EXPOSE_HEADERS = [
    'x-request-id',
    'x-correlation-id',
    'x-client-version',
    'x-ratelimit-limit',
    'x-ratelimit-remaining',
    'x-ratelimit-reset',
    'x-response-time',
]

CORS_ALLOW_CREDENTIALS = True
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours

# =============================================================================
# ENHANCED REST FRAMEWORK CONFIGURATION
# =============================================================================

REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': config('THROTTLE_ANON', default='100/hour'),
        'user': config('THROTTLE_USER', default='1000/hour'),
        'login': config('THROTTLE_LOGIN', default='10/minute'),
        'register': config('THROTTLE_REGISTER', default='5/minute'),
        'chat_completions': config('THROTTLE_CHAT', default='5/minute'),
        'research': config('THROTTLE_RESEARCH', default='50/hour'),
    },
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'DEFAULT_VERSION': '2.0',
    'ALLOWED_VERSIONS': ['1.0', '2.0'],
    'VERSION_PARAM': 'version',
})

# =============================================================================
# ENHANCED JWT CONFIGURATION
# =============================================================================

SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_LIFETIME', default=15, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_LIFETIME', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ISSUER': config('JWT_ISSUER', default='PromptCraft'),
    'AUDIENCE': config('JWT_AUDIENCE', default='promptcraft-api'),
})

# Add JWT token blacklist
if 'rest_framework_simplejwt.token_blacklist' not in INSTALLED_APPS:
    INSTALLED_APPS.append('rest_framework_simplejwt.token_blacklist')

# =============================================================================
# ENHANCED LOGGING CONFIGURATION
# =============================================================================

# Create production logs directory
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} [{process:d}:{thread:d}] {pathname}:{lineno} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "{levelname}", "timestamp": "{asctime}", "logger": "{name}", "process": {process}, "thread": {thread}, "pathname": "{pathname}", "lineno": {lineno}, "message": "{message}"}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'stream': sys.stdout,
        },
        'app_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'performance.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'app_file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'security_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'promptcraft': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'promptcraft.performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'research_agent': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# SENTRY CONFIGURATION
# =============================================================================

SENTRY_DSN = config('SENTRY_DSN', default=None)
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_logging = LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(
                    transaction_style='url',
                    middleware_spans=True,
                    signals_spans=False,
                    cache_spans=True,
                ),
                CeleryIntegration(
                    monitor_beat_tasks=True,
                    propagate_traces=True,
                ),
                RedisIntegration(),
                sentry_logging,
            ],
            traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float),
            send_default_pii=False,
            attach_stacktrace=True,
            environment=config('SENTRY_ENVIRONMENT', default='production'),
            release=config('SENTRY_RELEASE', default='1.0.0'),
            before_send=lambda event, hint: event if event.get('level') != 'info' else None,
        )
        
        logger.info("Sentry error monitoring enabled")
    except ImportError:
        logger.warning("Sentry SDK not available")

# =============================================================================
# STATIC AND MEDIA FILES CONFIGURATION
# =============================================================================

# Static files with WhiteNoise
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# WhiteNoise configuration
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False
WHITENOISE_MAX_AGE = 31536000  # 1 year

# Media files - consider using S3 in production
MEDIA_ROOT = BASE_DIR / 'media'

# AWS S3 Configuration (optional)
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')

if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_STORAGE_BUCKET_NAME:
    try:
        import storages
        DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
        AWS_S3_FILE_OVERWRITE = False
        AWS_DEFAULT_ACL = None
        AWS_S3_OBJECT_PARAMETERS = {
            'CacheControl': 'max-age=86400',
        }
        logger.info("AWS S3 storage configured for media files")
    except ImportError:
        logger.warning("django-storages not available, using local media storage")

# =============================================================================
# CELERY PRODUCTION CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = f"{REDIS_URL}/4"
CELERY_RESULT_BACKEND = f"{REDIS_URL}/4"

# Enhanced Celery configuration
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Task routing
CELERY_TASK_ROUTES = {
    'research_agent.*': {'queue': 'research'},
    'apps.ai_services.*': {'queue': 'ai'},
    'apps.analytics.*': {'queue': 'analytics'},
    '*': {'queue': 'default'},
}

# Task limits
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 200000  # 200MB

# Task monitoring
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_SEND_EVENTS = True
CELERY_WORKER_SEND_TASK_EVENTS = True

# Beat schedule
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-tokens': {
        'task': 'apps.users.tasks.cleanup_expired_tokens',
        'schedule': 3600.0,  # Every hour
    },
    'update-analytics': {
        'task': 'apps.analytics.tasks.update_daily_analytics',
        'schedule': 86400.0,  # Daily
    },
}

# =============================================================================
# CHANNELS PRODUCTION CONFIGURATION
# =============================================================================

if 'channels' in INSTALLED_APPS:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [f"{REDIS_URL}/5"],
                'capacity': 5000,
                'expiry': 300,  # 5 minutes
                'group_expiry': 86400,  # 24 hours
                'symmetric_encryption_keys': [
                    config('CHANNEL_LAYER_SECRET')
                ],
            },
        },
    }

# =============================================================================
# API RATE LIMITING
# =============================================================================

# Custom rate limiting per endpoint
RATE_LIMIT_SETTINGS = {
    'ENABLE_RATE_LIMITING': True,
    'RATE_LIMIT_BACKEND': 'django_redis.cache.RedisCache',
    'RATE_LIMIT_CACHE_ALIAS': 'rate_limit',
    'CUSTOM_RATES': {
        '/api/v1/auth/login/': '10/minute',
        '/api/v1/auth/register/': '5/minute',
        '/api/v1/chat/completions/': '5/minute',
        '/api/v1/research/': '10/hour',
        '/api/v1/templates/': '100/hour',
    }
}

# =============================================================================
# MONITORING AND HEALTH CHECKS
# =============================================================================

HEALTH_CHECK_SETTINGS = {
    'DATABASE_CHECK': True,
    'REDIS_CHECK': True,
    'CELERY_CHECK': True,
    'EXTERNAL_API_CHECK': False,  # Disable to avoid API quota usage
}

# Performance monitoring
PERFORMANCE_MONITORING = {
    'SLOW_QUERY_THRESHOLD': config('SLOW_QUERY_THRESHOLD', default=1.0, cast=float),
    'SLOW_REQUEST_THRESHOLD': config('SLOW_REQUEST_THRESHOLD', default=2.0, cast=float),
    'MEMORY_THRESHOLD': config('MEMORY_THRESHOLD', default=85, cast=int),
}

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend'
)

# SMTP Configuration
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@prompt-temple.com')

# =============================================================================
# BACKUP AND DISASTER RECOVERY
# =============================================================================

BACKUP_SETTINGS = {
    'ENABLED': config('BACKUP_ENABLED', default=True, cast=bool),
    'DATABASE_BACKUP_RETENTION': config('DB_BACKUP_RETENTION_DAYS', default=30, cast=int),
    'MEDIA_BACKUP_RETENTION': config('MEDIA_BACKUP_RETENTION_DAYS', default=90, cast=int),
    'S3_BACKUP_BUCKET': config('S3_BACKUP_BUCKET', default=''),
}

# =============================================================================
# FEATURE FLAGS OVERRIDE
# =============================================================================

FEATURE_FLAGS.update({
    'MAINTENANCE_MODE': config('MAINTENANCE_MODE', default=False, cast=bool),
    'NEW_USER_REGISTRATION': config('ALLOW_NEW_REGISTRATIONS', default=True, cast=bool),
    'SOCIAL_AUTH_ENABLED': config('ENABLE_SOCIAL_AUTH', default=True, cast=bool),
    'WEBSOCKETS_ENABLED': config('ENABLE_WEBSOCKETS', default=True, cast=bool),
    'RATE_LIMITING_ENABLED': config('ENABLE_RATE_LIMITING', default=True, cast=bool),
})

# =============================================================================
# PRODUCTION VALIDATION
# =============================================================================

def validate_production_settings():
    """Validate critical production settings"""
    errors = []
    warnings = []
    
    # Critical validations
    if SECRET_KEY == "django-insecure-change-me-in-production":
        errors.append("SECRET_KEY must be changed from default value")
    
    if DEBUG:
        errors.append("DEBUG must be False in production")
    
    if not DATABASE_URL and not all([
        config('DB_NAME', default=None),
        config('DB_USER', default=None),
        config('DB_PASSWORD', default=None)
    ]):
        errors.append("Database configuration is incomplete")
    
    if not REDIS_URL:
        errors.append("REDIS_URL is required for production")
    
    # Warning validations
    if not SENTRY_DSN:
        warnings.append("Sentry DSN not configured - error monitoring disabled")
    
    if not EMAIL_HOST_USER:
        warnings.append("Email configuration incomplete - notifications disabled")
    
    if not AWS_ACCESS_KEY_ID:
        warnings.append("AWS S3 not configured - using local file storage")
    
    # Log results
    for error in errors:
        logger.error(f"PRODUCTION ERROR: {error}")
    
    for warning in warnings:
        logger.warning(f"PRODUCTION WARNING: {warning}")
    
    if errors:
        logger.error("Production validation failed - fix errors before deployment")
        sys.exit(1)
    
    logger.info("Production settings validation passed")

# Run production validation
validate_production_settings()

# Log production configuration summary
logger.info("="*60)
logger.info("PRODUCTION CONFIGURATION LOADED")
logger.info("="*60)
logger.info(f"Environment: {ENVIRONMENT}")
logger.info(f"Debug: {DEBUG}")
logger.info(f"Allowed Hosts: {len(ALLOWED_HOSTS)} configured")
logger.info(f"Database: {DATABASES['default']['ENGINE']}")
logger.info(f"Cache: Redis with {len(CACHES)} backends")
logger.info(f"Security: HTTPS={SECURE_SSL_REDIRECT}, HSTS={SECURE_HSTS_SECONDS}s")
logger.info(f"Monitoring: Sentry={'enabled' if SENTRY_DSN else 'disabled'}")
logger.info(f"Features: {sum(1 for v in FEATURE_FLAGS.values() if v)}/{len(FEATURE_FLAGS)} enabled")
logger.info("="*60)