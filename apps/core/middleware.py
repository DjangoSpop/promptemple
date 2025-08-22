import logging

logger = logging.getLogger('core.auth_debug')


class DebugAuthLoggingMiddleware:
    """
    Temporary middleware for debugging: logs masked Authorization header and remote IP.

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
        except Exception as e:
            logger.exception(f"DebugAuthLoggingMiddleware failed: {e}")

        return self.get_response(request)
