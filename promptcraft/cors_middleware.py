"""
Custom CORS Middleware for PromptCraft API
Ensures proper handling of preflight requests and CORS headers
"""

import json
from django.http import HttpResponse
from django.conf import settings


class CorsMiddleware:
    """
    Custom CORS middleware to ensure proper handling of:
    - Preflight OPTIONS requests
    - CORS headers on all responses
    - Credentials with CORS
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight requests
        if request.method == 'OPTIONS':
            return self.handle_preflight(request)

        # Process the request
        response = self.get_response(request)

        # Add CORS headers to response
        return self.add_cors_headers(request, response)

    def get_allowed_origins(self):
        """Get list of allowed origins"""
        if getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False):
            return ['*']

        return getattr(settings, 'CORS_ALLOWED_ORIGINS', [
            'http://localhost:3000',
            'http://localhost:3001',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:3001',
        ])

    def is_origin_allowed(self, origin):
        """Check if origin is in allowed list"""
        allowed = self.get_allowed_origins()

        if allowed == ['*']:
            return True

        return origin in allowed

    def handle_preflight(self, request):
        """Handle OPTIONS preflight requests"""
        origin = request.META.get('HTTP_ORIGIN', '')

        if not self.is_origin_allowed(origin):
            return HttpResponse(status=403)

        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = ', '.join(
            getattr(settings, 'CORS_ALLOW_METHODS', [
                'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'
            ])
        )
        response['Access-Control-Allow-Headers'] = ', '.join(
            getattr(settings, 'CORS_ALLOWED_HEADERS', [
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
            ])
        )

        if getattr(settings, 'CORS_ALLOW_CREDENTIALS', True):
            response['Access-Control-Allow-Credentials'] = 'true'

        response['Access-Control-Max-Age'] = '86400'

        return response

    def add_cors_headers(self, request, response):
        """Add CORS headers to response"""
        origin = request.META.get('HTTP_ORIGIN', '')

        if not self.is_origin_allowed(origin):
            return response

        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = ', '.join(
            getattr(settings, 'CORS_ALLOW_METHODS', [
                'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'
            ])
        )

        if getattr(settings, 'CORS_ALLOW_CREDENTIALS', True):
            response['Access-Control-Allow-Credentials'] = 'true'

        # Expose custom headers
        exposed_headers = getattr(settings, 'CORS_EXPOSE_HEADERS', [
            'Content-Type',
            'X-CSRFToken',
        ])
        if exposed_headers:
            response['Access-Control-Expose-Headers'] = ', '.join(exposed_headers)

        return response
