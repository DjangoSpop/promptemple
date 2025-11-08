"""
CORS Configuration for PromptCraft API
Handles cross-origin requests from frontend applications
"""

import os
from decouple import config

# Determine environment
DEBUG = config('DEBUG', default=True, cast=bool)
ENVIRONMENT = 'production' if not DEBUG else 'development'

# Development Origins
DEV_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:8000',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:3001',
    'http://127.0.0.1:8000',
    'http://10.0.2.2:8000',  # Android emulator
    'http://10.0.3.2:8000',  # Alternative Android emulator
]

# Production Origins
PROD_ORIGINS = [
    'https://www.prompt-temple.com',
    'https://prompt-temple.com',
    'https://app.prompt-temple.com',
]

# Allowed Headers
ALLOWED_HEADERS = [
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
    'x-client-version',
    'x-client-name',
    'x-request-id',
    'x-access-token',
]

# Allowed Methods
ALLOWED_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
    'HEAD',
]

# Exposed Headers
EXPOSED_HEADERS = [
    'Content-Type',
    'X-CSRFToken',
    'Authorization',
    'X-Total-Count',
    'X-Page-Count',
]

def get_cors_origins():
    """Get appropriate CORS origins based on environment"""
    if DEBUG:
        return DEV_ORIGINS
    return PROD_ORIGINS

def get_cors_config():
    """Get complete CORS configuration"""
    return {
        'allowed_origins': get_cors_origins(),
        'allowed_credentials': True,
        'allowed_headers': ALLOWED_HEADERS,
        'allowed_methods': ALLOWED_METHODS,
        'exposed_headers': EXPOSED_HEADERS,
        'max_age': 86400,  # 24 hours
        'allow_all_origins': DEBUG,  # Allow all in development
        'environment': ENVIRONMENT,
    }
