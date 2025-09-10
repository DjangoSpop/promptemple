from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
import platform
import sys
import logging

logger = logging.getLogger(__name__)


def health_simple(request):
    """Simple health check - no DB, no session, minimal dependencies"""
    return JsonResponse({"status": "ok"}, status=200)


class HealthCheckView(APIView):
    """
    Comprehensive health check endpoint for monitoring service status
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Return comprehensive health status"""
        try:
            # Simple health response without external dependencies
            health_data = {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'app': 'PromptCraft',
                'version': getattr(settings, 'VERSION', '1.0.0'),
                'python_version': sys.version.split()[0],
                'platform': platform.system()
            }
            
            return Response(health_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return Response({
                'status': 'error',
                'timestamp': timezone.now().isoformat(),
                'error': str(e),
                'message': 'Health check system failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def rag_status(request):
    """RAG service status endpoint - no auth required"""
    try:
        from apps.templates.rag.services import langchain_status
        return Response(langchain_status())
    except ImportError:
        return Response({
            "feature_enabled": False,
            "service_ready": False,
            "error": "RAG module not available",
            "strategy": None,
            "available_factories": []
        })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def app_config(request):
    """Public app configuration endpoint - no auth, no session, no DB"""
    return Response({
        'env': getattr(settings, 'ENV_NAME', 'development'),
        'features': {
            'rag': getattr(settings, 'FEATURE_RAG', False),
            'ai_integration': True,
            'template_library': True,
        },
        'app_name': 'PromptCraft',
        'version': getattr(settings, 'VERSION', '1.0.0'),
    })


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
            'env': getattr(settings, 'ENV_NAME', 'development'),
            'features': {
                'rag': getattr(settings, 'FEATURE_RAG', False),
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
