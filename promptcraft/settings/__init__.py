"""
Settings module initialization.
This file configures which settings file to use based on the environment.
"""

import os

# Try to import decouple, fallback to os.environ if not available
try:
    from decouple import config
except ImportError:
    def config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            if cast == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return cast(value)
        return value

# Set the environment variable to specify which settings module to use
# Valid options: development, production, testing
# Default to development for easier local setup
ENVIRONMENT = config('DJANGO_ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'testing':
    from .testing import *
else:
    from .development import *
