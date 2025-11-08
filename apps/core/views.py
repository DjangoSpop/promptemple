from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render
import platform
import sys
import logging

logger = logging.getLogger(__name__)


def home(request):
    """Home page with API testing dashboard"""
    context = {
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'cors_allow_all': getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False),
        'cors_allowed_origins': getattr(settings, 'CORS_ALLOWED_ORIGINS', []),
    }
    return render(request, 'core/home.html', context)


def api_tester(request):
    """Interactive API testing interface"""
    context = {
        'api_base_url': f"http://{request.get_host()}",
        'endpoints': [
            {
                'name': 'Templates List',
                'url': '/api/v2/templates/',
                'method': 'GET',
                'description': 'Get all templates with pagination and ordering'
            },
            {
                'name': 'Template Categories',
                'url': '/api/v2/template-categories/',
                'method': 'GET',
                'description': 'Get all template categories'
            },
            {
                'name': 'User Login',
                'url': '/api/v2/auth/login/',
                'method': 'POST',
                'description': 'Login with email and password',
                'sample_body': '{"email": "test@example.com", "password": "password123"}'
            },
            {
                'name': 'User Registration',
                'url': '/api/v2/auth/registration/',
                'method': 'POST',
                'description': 'Register a new user',
                'sample_body': '{"email": "test@example.com", "username": "testuser", "password1": "password123", "password2": "password123"}'
            },
            {
                'name': 'System Status',
                'url': '/api/v2/status/',
                'method': 'GET',
                'description': 'Check system health and configuration'
            },
        ]
    }
    return render(request, 'core/api_tester.html', context)


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


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def system_status(request):
    """System status endpoint for health checks"""
    return Response({
        'status': 'operational',
        'debug': settings.DEBUG,
        'environment': 'development' if settings.DEBUG else 'production',
        'cors_configured': 'corsheaders' in settings.INSTALLED_APPS,
        'cors_allow_all': getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False),
        'allowed_origins': getattr(settings, 'CORS_ALLOWED_ORIGINS', []),
        'python_version': sys.version,
        'settings_module': 'promptcraft.settings',
    })


@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([permissions.AllowAny])
def cors_test(request):
    """Test CORS configuration"""
    response_data = {
        'method': request.method,
        'origin': request.META.get('HTTP_ORIGIN', 'No origin header'),
        'referer': request.META.get('HTTP_REFERER', 'No referer'),
        'cors_test': 'SUCCESS',
        'headers_received': {
            'Content-Type': request.META.get('CONTENT_TYPE', 'Not set'),
            'Authorization': 'Present' if request.META.get('HTTP_AUTHORIZATION') else 'Not present',
        }
    }
    
    if request.method == 'POST':
        response_data['body'] = request.data if hasattr(request, 'data') else 'No body'
    
    return Response(response_data)


def auth_page(request):
    """Authentication page for sign-in and sign-up with JWT token management"""
    return render(request, 'ai_services/auth.html')


def ai_dashboard(request):
    """AI Services Testing Dashboard - Main interface for testing all AI endpoints"""
    context = {
        'api_base_url': f"http://{request.get_host()}",
        'user': request.user,
        'debug': settings.DEBUG,
        'ai_endpoints': [
            {
                'name': 'Prompt Optimizer',
                'endpoint': '/api/ai/agent/optimize/',
                'method': 'POST',
                'requires_auth': True,
                'description': 'RAG-powered prompt optimization with vector search',
                'test_page': '/ai-test/optimizer/',
            },
            {
                'name': 'RAG Retrieval',
                'endpoint': '/api/ai/rag/retrieve/',
                'method': 'POST',
                'requires_auth': True,
                'description': 'Vector similarity search with document retrieval',
                'test_page': '/ai-test/rag-retrieve/',
            },
            {
                'name': 'RAG Answer',
                'endpoint': '/api/ai/rag/answer/',
                'method': 'POST',
                'requires_auth': True,
                'description': 'RAG-powered Q&A with context',
                'test_page': '/ai-test/rag-answer/',
            },
            {
                'name': 'Research Agent (Tavily)',
                'endpoint': '/api/ai/assistant/run/',
                'method': 'POST',
                'requires_auth': True,
                'description': 'Tavily-powered web research assistant',
                'test_page': '/ai-test/research/',
            },
            {
                'name': 'DeepSeek Stream',
                'endpoint': '/api/ai/deepseek/stream/',
                'method': 'POST',
                'requires_auth': True,
                'description': 'SSE streaming chat with DeepSeek',
                'test_page': '/ai-test/deepseek/',
            },
            {
                'name': 'Research Agent Pro',
                'endpoint': '/api/v2/research/quick/',
                'method': 'POST',
                'requires_auth': False,
                'description': 'Full research pipeline: Search → Fetch → Chunk → Embed → Retrieve → Synthesize',
                'test_page': '/ai-test/research-pro/',
            },
        ],
    }
    return render(request, 'ai_services/dashboard.html', context)


def research_agent_test(request):
    """Test page for Tavily Research Agent with SSE streaming"""
    context = {
        'api_base_url': f"http://{request.get_host()}",
        'endpoint': '/api/ai/assistant/run/',
        'user': request.user,
        'requires_auth': True,
    }
    return render(request, 'ai_services/research_agent.html', context)


def prompt_optimizer_test(request):
    """Test page for RAG-powered prompt optimizer"""
    context = {
        'api_base_url': f"http://{request.get_host()}",
        'endpoint': '/api/ai/agent/optimize/',
        'user': request.user,
        'requires_auth': True,
        'sample_prompts': [
            "Write a blog post about AI",
            "Create a product description for a smart watch",
            "Generate a social media caption",
        ],
    }
    return render(request, 'ai_services/prompt_optimizer.html', context)


def rag_retrieve_test(request):
    """Test page for RAG vector retrieval"""
    context = {
        'api_base_url': f"http://{request.get_host()}",
        'endpoint': '/api/ai/rag/retrieve/',
        'user': request.user,
        'requires_auth': True,
    }
    return render(request, 'ai_services/rag_retrieve.html', context)


def rag_answer_test(request):
    """Test page for RAG-powered Q&A"""
    context = {
        'api_base_url': f"http://{request.get_host()}",
        'endpoint': '/api/ai/rag/answer/',
        'user': request.user,
        'requires_auth': True,
    }
    return render(request, 'ai_services/rag_answer.html', context)


def deepseek_stream_test(request):
    """Test page for DeepSeek SSE streaming"""
    context = {
        'api_base_url': f"http://{request.get_host()}",
        'endpoint': '/api/ai/deepseek/stream/',
        'user': request.user,
        'requires_auth': True,
    }
    return render(request, 'ai_services/deepseek_stream.html', context)


def research_agent_pro_test(request):
    """Test page for Professional Research Agent with full pipeline"""
    context = {
        'api_base_url': f"http://{request.get_host()}",
        'user': request.user,
    }
    return render(request, 'ai_services/research_agent_pro.html', context)
