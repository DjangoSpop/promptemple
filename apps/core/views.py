from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import connection
from django.conf import settings
from django.utils import timezone
import platform
import sys


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring service status
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Return health status"""
        try:
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            return Response({
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'version': getattr(settings, 'VERSION', '1.0.0'),
                'database': 'connected',
                'python_version': sys.version,
                'platform': platform.platform()
            })
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class AppConfigurationView(APIView):
    """
    App configuration endpoint
    """
    permission_classes = [permissions.IsAuthenticated]
    
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
