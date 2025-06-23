"""
Testing settings for the promptcraft project.
"""

from .base import *

# Set DEBUG to False to ensure tests run with production-like settings
DEBUG = False

# Use SQLite for testing by default
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Using in-memory database for faster tests
    }
}

# Faster password hashing for testing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable middleware that we don't need for testing
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m.lower()]

# Disable CORS checks during testing
CORS_ORIGIN_ALLOW_ALL = True

# Turn off debug-toolbar for testing
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')
if 'debug_toolbar.middleware.DebugToolbarMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')

# Use a dummy cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Email settings for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Celery settings for testing
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously in tests
