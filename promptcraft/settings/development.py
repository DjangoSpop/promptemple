from .base import *

DEBUG = False
ALLOWED_HOSTS = ['www.prompt-temple.com', 'https://floating-chamber-26624-41879340871a.herokuapp.com/','prompt-temple.com']

# Database for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config('DB_NAME', default='promptcraft_db'),
        "USER": config('DB_USER', default='promptcraft_user'),
        "PASSWORD": config('DB_PASSWORD', default='fuckthat'),
        "HOST": config('DB_HOST', default='localhost'),
        "PORT": config('DB_PORT', default='5432'),
        "OPTIONS": {
            "connect_timeout": 20,
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
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
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
 'www.prompt-temple.com', 
 'https://floating-chamber-26624-41879340871a.herokuapp.com/',
 'prompt-temple.com'
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only in development

# Debug toolbar
if DEBUG and 'debug_toolbar' not in INSTALLED_APPS:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# Add drf-spectacular to installed apps
if 'drf_spectacular' not in INSTALLED_APPS:
    INSTALLED_APPS += ['drf_spectacular']