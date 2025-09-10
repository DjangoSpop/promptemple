import logging
import json

logger = logging.getLogger('core.auth_debug')


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
