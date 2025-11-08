"""
Enhanced Middleware Collection for PromptCraft
Provides comprehensive security, monitoring, and performance features

Author: GitHub Copilot  
Date: November 2024
"""

import logging
import json
import time
import uuid
from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger('core.auth_debug')
security_logger = logging.getLogger('promptcraft.security')
performance_logger = logging.getLogger('promptcraft.performance')


class DebugAuthLoggingMiddleware:
    """
    Temporary middleware for debugging: logs masked Authorization header and remote IP.
    Also logs registration/login responses to debug token issues.

    Only intended for short-term debugging in development or local production testing.
    Do NOT enable in public production environments.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            auth = request.META.get('HTTP_AUTHORIZATION')
            remote = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR')
            path = request.path
            method = request.method

            if auth:
                # Mask token except last 8 chars
                masked = auth[:7] + '...' + auth[-8:] if len(auth) > 15 else '***masked***'
            else:
                masked = None

            logger.info(f"AuthDebug: {method} {path} from {remote} Authorization={masked}")
            
            # Log request body for auth endpoints (mask passwords)
            if any(endpoint in path for endpoint in ['/auth/register/', '/auth/login/']):
                if request.body:
                    try:
                        body = json.loads(request.body.decode('utf-8'))
                        safe_body = {k: ('***' if 'password' in k.lower() else v) for k, v in body.items()}
                        logger.info(f"AuthDebug Request Body: {safe_body}")
                    except:
                        logger.info(f"AuthDebug Request Body: Non-JSON or empty")
                        
        except Exception as e:
            logger.exception(f"DebugAuthLoggingMiddleware failed: {e}")

        response = self.get_response(request)
        
        # Log response for auth endpoints
        try:
            if any(endpoint in request.path for endpoint in ['/auth/register/', '/auth/login/']):
                logger.info(f"AuthDebug Response: {request.method} {request.path} -> {response.status_code}")
                if hasattr(response, 'content') and response.content:
                    try:
                        content = json.loads(response.content.decode('utf-8'))
                        # Check if tokens are present
                        if 'tokens' in content:
                            tokens = content['tokens']
                            safe_content = content.copy()
                            safe_content['tokens'] = {
                                'access': 'PRESENT' if 'access' in tokens and tokens['access'] else 'MISSING',
                                'refresh': 'PRESENT' if 'refresh' in tokens and tokens['refresh'] else 'MISSING'
                            }
                            logger.info(f"AuthDebug Response Content: {safe_content}")
                        else:
                            logger.info(f"AuthDebug Response Content: {content}")
                    except Exception as e:
                        logger.info(f"AuthDebug Response parsing failed: {e}")
        except Exception as e:
            logger.exception(f"Response logging failed: {e}")

        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add comprehensive security headers to all responses"""
    
    def process_response(self, request, response):
        # Content Security Policy
        if hasattr(settings, 'CSP_DEFAULT_SRC'):
            csp_policy = []
            csp_policy.append(f"default-src {' '.join(settings.CSP_DEFAULT_SRC)}")
            
            if hasattr(settings, 'CSP_SCRIPT_SRC'):
                csp_policy.append(f"script-src {' '.join(settings.CSP_SCRIPT_SRC)}")
            
            if hasattr(settings, 'CSP_STYLE_SRC'):
                csp_policy.append(f"style-src {' '.join(settings.CSP_STYLE_SRC)}")
            
            if hasattr(settings, 'CSP_IMG_SRC'):
                csp_policy.append(f"img-src {' '.join(settings.CSP_IMG_SRC)}")
            
            if hasattr(settings, 'CSP_CONNECT_SRC'):
                csp_policy.append(f"connect-src {' '.join(settings.CSP_CONNECT_SRC)}")
            
            response['Content-Security-Policy'] = '; '.join(csp_policy)
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = getattr(settings, 'X_FRAME_OPTIONS', 'DENY')
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = getattr(settings, 'SECURE_REFERRER_POLICY', 'strict-origin-when-cross-origin')
        
        # Remove server information
        response['Server'] = 'PromptCraft'
        
        # Add request ID if not present
        if not response.get('X-Request-ID'):
            response['X-Request-ID'] = getattr(request, 'request_id', str(uuid.uuid4()))
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all requests with security and performance information"""
    
    def process_request(self, request):
        # Generate unique request ID
        request.request_id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # Log security-relevant information
        security_info = {
            'request_id': request.request_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'content_type': request.META.get('CONTENT_TYPE', ''),
        }
        
        # Check for suspicious patterns
        if self.is_suspicious_request(request):
            security_logger.warning(f"Suspicious request detected: {security_info}")
        else:
            logger.info(f"Request: {request.method} {request.path} from {security_info['remote_addr']}")
        
        return None
    
    def process_response(self, request, response):
        # Calculate response time
        if hasattr(request, 'start_time'):
            response_time = time.time() - request.start_time
            response['X-Response-Time'] = f"{response_time:.3f}s"
            
            # Log slow requests
            slow_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 2.0)
            if response_time > slow_threshold:
                logger.warning(f"Slow request: {request.method} {request.path} took {response_time:.3f}s")
        
        # Log response information
        logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
        
        return response
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_suspicious_request(self, request):
        """Detect potentially suspicious requests"""
        suspicious_patterns = [
            'admin/login',
            'wp-admin',
            'phpMyAdmin',
            '.php',
            '../',
            'union select',
            '<script',
            'javascript:',
        ]
        
        path_lower = request.path.lower()
        query_lower = request.META.get('QUERY_STRING', '').lower()
        
        for pattern in suspicious_patterns:
            if pattern in path_lower or pattern in query_lower:
                return True
        
        return False


class PerformanceMiddleware(MiddlewareMixin):
    """Monitor and optimize performance"""
    
    def process_request(self, request):
        request.performance_start = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'performance_start'):
            duration = time.time() - request.performance_start
            
            # Add performance headers
            response['X-Processing-Time'] = f"{duration:.3f}"
            
            # Log performance metrics
            perf_info = {
                'path': request.path,
                'method': request.method,
                'duration': duration,
                'status_code': response.status_code,
                'content_length': len(response.content),
            }
            
            # Log as JSON for easier parsing
            performance_logger.info(
                f"PERF: {request.method} {request.path} "
                f"{response.status_code} {duration:.3f}s {len(response.content)}b"
            )
            
            # Alert on very slow requests
            if duration > getattr(settings, 'SLOW_REQUEST_THRESHOLD', 2.0):
                logger.warning(f"Very slow request: {perf_info}")
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Advanced rate limiting middleware"""
    
    def process_request(self, request):
        if not getattr(settings, 'RATE_LIMIT_SETTINGS', {}).get('ENABLE_RATE_LIMITING', False):
            return None
        
        client_ip = self.get_client_ip(request)
        path = request.path
        
        # Check for custom rate limits
        custom_rates = getattr(settings, 'RATE_LIMIT_SETTINGS', {}).get('CUSTOM_RATES', {})
        
        for pattern, rate_limit in custom_rates.items():
            if pattern in path:
                if self.is_rate_limited(client_ip, pattern, rate_limit):
                    security_logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
                    return HttpResponse(
                        'Rate limit exceeded',
                        status=429,
                        headers={
                            'Retry-After': '60',
                            'X-RateLimit-Limit': rate_limit,
                        }
                    )
        
        # General rate limiting
        if self.is_rate_limited(client_ip, 'general', '1000/hour'):
            security_logger.warning(f"General rate limit exceeded for {client_ip}")
            return HttpResponse(
                'Rate limit exceeded',
                status=429,
                headers={'Retry-After': '60'}
            )
        
        return None
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, client_ip, endpoint, rate_limit):
        """Check if client is rate limited"""
        try:
            # Parse rate limit (e.g., "10/minute", "100/hour")
            count, period = rate_limit.split('/')
            count = int(count)
            
            # Convert period to seconds
            if period == 'second':
                seconds = 1
            elif period == 'minute':
                seconds = 60
            elif period == 'hour':
                seconds = 3600
            elif period == 'day':
                seconds = 86400
            else:
                seconds = 3600  # Default to hour
            
            # Create cache key
            cache_key = f"rate_limit:{client_ip}:{endpoint}"
            
            # Get current count
            current_count = cache.get(cache_key, 0)
            
            if current_count >= count:
                return True
            
            # Increment counter
            cache.set(cache_key, current_count + 1, seconds)
            return False
            
        except (ValueError, TypeError):
            logger.error(f"Invalid rate limit format: {rate_limit}")
            return False


class MaintenanceMiddleware(MiddlewareMixin):
    """Handle maintenance mode"""
    
    def process_request(self, request):
        if getattr(settings, 'FEATURE_FLAGS', {}).get('MAINTENANCE_MODE', False):
            # Allow admin and health check endpoints during maintenance
            allowed_paths = [
                '/admin/',
                '/api/health/',
                '/api/v1/core/health/',
            ]
            
            if not any(request.path.startswith(path) for path in allowed_paths):
                return HttpResponse(
                    'Service temporarily unavailable. Please try again later.',
                    status=503,
                    headers={'Retry-After': '3600'}  # 1 hour
                )
        
        return None
