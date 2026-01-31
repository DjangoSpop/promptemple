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

# Import drf-spectacular decorators
try:
    from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
    from drf_spectacular.types import OpenApiTypes
    DRF_SPECTACULAR_AVAILABLE = True
except ImportError:
    # Fallback decorator that does nothing if drf-spectacular is not installed
    def extend_schema(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    DRF_SPECTACULAR_AVAILABLE = False

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
    Tests: Database, Redis, Celery, AI Services
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Return comprehensive health status with all service checks"""
        start_time = timezone.now()
        health_data = {
            'status': 'healthy',
            'timestamp': start_time.isoformat(),
            'app': 'PromptCraft',
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'python_version': sys.version.split()[0],
            'platform': platform.system(),
            'services': {}
        }

        try:
            # 1. Database Health Check
            from django.db import connection
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                health_data['services']['database'] = {
                    'status': 'healthy',
                    'type': settings.DATABASES['default']['ENGINE'].split('.')[-1]
                }
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                health_data['services']['database'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_data['status'] = 'degraded'

            # 2. Redis/Cache Health Check
            from django.core.cache import cache
            try:
                cache_key = '__health_check__'
                cache_value = 'ok'
                cache.set(cache_key, cache_value, 10)
                cached = cache.get(cache_key)

                if cached == cache_value:
                    health_data['services']['cache'] = {
                        'status': 'healthy',
                        'backend': settings.CACHES['default']['BACKEND'].split('.')[-1]
                    }
                else:
                    health_data['services']['cache'] = {
                        'status': 'degraded',
                        'message': 'Cache read/write mismatch'
                    }
                    health_data['status'] = 'degraded'
            except Exception as e:
                logger.error(f"Cache health check failed: {e}")
                health_data['services']['cache'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_data['status'] = 'degraded'

            # 3. Celery Health Check (if installed)
            try:
                from celery import current_app
                inspect = current_app.control.inspect()
                active_workers = inspect.active()

                if active_workers:
                    health_data['services']['celery'] = {
                        'status': 'healthy',
                        'workers': len(active_workers),
                        'worker_names': list(active_workers.keys())
                    }
                else:
                    health_data['services']['celery'] = {
                        'status': 'warning',
                        'message': 'No active workers'
                    }
            except ImportError:
                health_data['services']['celery'] = {
                    'status': 'not_installed',
                    'message': 'Celery not configured'
                }
            except Exception as e:
                logger.warning(f"Celery health check failed: {e}")
                health_data['services']['celery'] = {
                    'status': 'error',
                    'error': str(e)
                }

            # 4. DeepSeek AI Service Health Check
            deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
            api_key = deepseek_config.get('API_KEY', '')
            base_url = deepseek_config.get('BASE_URL', '')

            if api_key and base_url:
                health_data['services']['deepseek'] = {
                    'status': 'configured',
                    'base_url': base_url,
                    'model': deepseek_config.get('DEFAULT_MODEL', 'deepseek-chat'),
                    'api_key_present': bool(api_key)
                }
            else:
                health_data['services']['deepseek'] = {
                    'status': 'not_configured',
                    'message': 'DeepSeek API key or base URL missing'
                }

            # 5. WebSocket/Channels Health Check
            try:
                from channels.layers import get_channel_layer
                channel_layer = get_channel_layer()

                if channel_layer:
                    health_data['services']['channels'] = {
                        'status': 'configured',
                        'backend': channel_layer.__class__.__name__
                    }
                else:
                    health_data['services']['channels'] = {
                        'status': 'not_configured'
                    }
            except ImportError:
                health_data['services']['channels'] = {
                    'status': 'not_installed'
                }
            except Exception as e:
                health_data['services']['channels'] = {
                    'status': 'error',
                    'error': str(e)
                }

            # Calculate response time
            end_time = timezone.now()
            health_data['response_time_ms'] = int((end_time - start_time).total_seconds() * 1000)

            # Determine overall status code
            status_code = status.HTTP_200_OK if health_data['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE

            return Response(health_data, status=status_code)

        except Exception as e:
            logger.error(f"Health check system error: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'timestamp': timezone.now().isoformat(),
                'error': str(e),
                'message': 'Health check system failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    description="Get RAG service status",
    responses={200: dict},
    tags=["Core"]
)
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


@extend_schema(
    description="Get public app configuration",
    responses={200: dict},
    tags=["Core"]
)
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


@extend_schema(
    description="Get system status and configuration",
    responses={200: dict},
    tags=["Core"]
)
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


@extend_schema(
    description="Health check for Redis cache and channels",
    responses={200: dict, 503: dict},
    tags=["Core"]
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def redis_health(request):
    """Health check for Redis cache and channels. Returns 200 with ok true/false."""
    from django.core.cache import cache
    try:
        # Prefer direct ping when available
        ok = False
        try:
            # django-redis exposes .client.get_client() in many setups
            client = cache
            val = cache.get('__health_check__')
            cache.set('__health_check__', 'ok', 5)
            ok = cache.get('__health_check__') == 'ok'
        except Exception:
            # Fallback to simple get/set
            cache.set('__health_check__', 'ok', 5)
            ok = cache.get('__health_check__') == 'ok'

        if ok:
            return Response({'ok': True}, status=200)
        else:
            return Response({'ok': False, 'error': 'cache_unreachable'}, status=503)
    except Exception as e:
        return Response({'ok': False, 'error': str(e)}, status=503)


@extend_schema(
    description="Test CORS configuration",
    responses={200: dict},
    tags=["Core"]
)
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
