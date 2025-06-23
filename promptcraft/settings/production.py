
from .base import *

DEBUG = False
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='www.prompt-temple.com', 
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Production database
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

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True