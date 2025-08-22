from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import connection
from django.conf import settings
from django.utils import timezone
from .health_checks import api_health_check
import platform
import sys
import logging

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Comprehensive health check endpoint for monitoring service status
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Return comprehensive health status"""
        try:
            # Use our comprehensive health check
            health_data = api_health_check()
            
            # Add additional system info
            health_data.update({
                'python_version': sys.version,
                'platform': platform.platform(),
                'django_version': getattr(settings, 'VERSION', '1.0.0')
            })
            
            # Determine response status
            if health_data['status'] == 'healthy':
                response_status = status.HTTP_200_OK
            else:
                response_status = status.HTTP_503_SERVICE_UNAVAILABLE
            
            return Response(health_data, status=response_status)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return Response({
                'status': 'error',
                'timestamp': timezone.now().isoformat(),
                'error': str(e),
                'message': 'Health check system failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AppConfigurationView(APIView):
    """
    App configuration endpoint
    """
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated access to app config
    
    def get(self, request):
        """Return app configuration"""
        return Response({
            'app_name': 'PromptCraft',
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'features': {
                'ai_integration': True,
                'template_library': True,
                'user_analytics': True,
                'gamification': True
            },
            'limits': {
                'max_templates_per_user': 100,
                'max_prompt_length': 5000,
                'daily_api_calls': 1000
            }
        })


class NotificationView(APIView):
    """
    User notifications endpoint
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user notifications"""
        # Placeholder implementation
        return Response({
            'notifications': [],
            'unread_count': 0
        })
    
    def post(self, request):
        """Mark notification as read"""
        return Response({'message': 'Notification marked as read'})
