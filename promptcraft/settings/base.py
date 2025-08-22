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
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes', 'on')
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
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Basic development settings
SECRET_KEY = config('SECRET_KEY', default="django-insecure-=$&0cpo9(=xihchk^!6p&#um-7icn@#u4ut)04sqcxs6__i+gd")
DEBUG = config('DEBUG', default=True, cast=bool)

# Local development only - includes Android AVD support
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    '10.0.2.2',  # Android AVD emulator
    '0.0.0.0',   # Allow all interfaces for development
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

THIRD_PARTY_APPS = []

# Conditionally add third-party apps if they're installed
try:
    import debug_toolbar
    THIRD_PARTY_APPS.append('debug_toolbar')
except ImportError:
    pass

try:
    import rest_framework
    THIRD_PARTY_APPS.append('rest_framework')
except ImportError:
    pass

try:
    import rest_framework_simplejwt
    THIRD_PARTY_APPS.append('rest_framework_simplejwt')
except ImportError:
    pass

try:
    import corsheaders
    THIRD_PARTY_APPS.append('corsheaders')
except ImportError:
    pass

try:
    import drf_spectacular
    THIRD_PARTY_APPS.append('drf_spectacular')
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

# Base middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
]

# Add CORS middleware if installed
if 'corsheaders' in THIRD_PARTY_APPS:
    MIDDLEWARE.append("corsheaders.middleware.CorsMiddleware")

MIDDLEWARE.extend([
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
])

# Add debug toolbar middleware if installed
if 'debug_toolbar' in THIRD_PARTY_APPS:
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

# Add temporary auth-debug middleware in debug mode to inspect Authorization headers
if DEBUG:
    # Import here to avoid circular imports and only enable in debug
    MIDDLEWARE.append('apps.core.middleware.DebugAuthLoggingMiddleware')

ROOT_URLCONF = "promptcraft.urls"

# Templates configuration
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
            ],
        },
    },
]

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
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",    },
]

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Debug Toolbar Settings (only if installed)
if 'debug_toolbar' in THIRD_PARTY_APPS:
    INTERNAL_IPS = [
        '127.0.0.1', 
        'localhost',
        '10.0.2.2',  # Android AVD emulator
    ]

# CORS settings (only if installed)

    CORS_ALLOWED_ORIGINS = [
        'http://localhost:3000', 
        'http://127.0.0.1:3000', 
        'http://localhost', 
        'http://127.0.0.1',
        'http://10.0.2.2:8000',  # Android AVD emulator
        'http://10.0.2.2',  
        "http://127.0.0.1:3000",     # Android AVD emulator
    ]
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
    'x-request-id',          # ADD THIS
    'x-client-version',      # ADD THIS
]
    # Ensure both modern and legacy setting names are present so every
    # environment and any code referencing the older name works.
    CORS_ALLOW_ALL_ORIGINS = True  # Only for development
    CORS_ALLOW_HEADERS = ['*'] 

    # Backwards-compatible alias for older code that expects CORS_ALLOWED_HEADERS


# JWT Settings - Basic configuration
if 'rest_framework_simplejwt' in THIRD_PARTY_APPS:
    from datetime import timedelta
    
    SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Shorter for security
        'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
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


# REST Framework settings (only if installed)
if 'rest_framework' in THIRD_PARTY_APPS:
    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.AllowAny',  # Allow views to control their own permissions
        ],
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework_simplejwt.authentication.JWTAuthentication',
            'rest_framework.authentication.SessionAuthentication',
        ],
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 20,
    }
    
    # Add schema class if spectacular is available
    if 'drf_spectacular' in THIRD_PARTY_APPS:
        REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'