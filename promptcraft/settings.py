"""
Django settings for promptcraft project.
Basic configuration for development.
"""

import os
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
    'drf_spectacular',
    # CORS handling
    'corsheaders',
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

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
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
