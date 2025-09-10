"""
Simplified views for basic functionality without advanced services
"""

import time
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.generic import View
from django.core.cache import cache

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def search_prompts_simple(request):
    """
    Simplified prompt search endpoint
    """
    start_time = time.time()
    
    try:
        # Parse request data
        data = request.data
        query = data.get('query', '').strip()
        max_results = min(data.get('max_results', 20), 50)
        
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simple search implementation using existing Template model
        from .models import Template
        
        results = Template.objects.filter(
            title__icontains=query,
            is_active=True,
            is_public=True
        ).select_related('category', 'author')[:max_results]
        
        # Format results
        formatted_results = []
        for template in results:
            formatted_results.append({
                'id': str(template.id),
                'title': template.title,
                'description': template.description,
                'category': template.category.name if template.category else None,
                'usage_count': template.usage_count,
                'average_rating': template.average_rating,
                'created_at': template.created_at.isoformat()
            })
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return Response({
            'results': formatted_results,
            'total_results': len(formatted_results),
            'query': query,
            'response_time_ms': response_time_ms,
            'message': 'Using simplified search - install Redis and run migrations for full functionality'
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return Response(
            {
                'error': 'Search failed',
                'details': str(e),
                'response_time_ms': response_time_ms
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def process_intent_simple(request):
    """
    Simplified intent processing
    """
    start_time = time.time()
    
    try:
        data = request.data
        query = data.get('query', '').strip()
        
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simple keyword-based intent classification
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['write', 'create', 'draft']):
            intent_category = 'content_creation'
        elif any(word in query_lower for word in ['email', 'message', 'communication']):
            intent_category = 'communication'
        elif any(word in query_lower for word in ['business', 'professional']):
            intent_category = 'business'
        else:
            intent_category = 'general'
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return Response({
            'intent_category': intent_category,
            'confidence_score': 0.8,
            'query': query,
            'response_time_ms': response_time_ms,
            'message': 'Using simplified intent processing - install LangChain for advanced features'
        })
        
    except Exception as e:
        logger.error(f"Intent processing error: {e}")
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return Response(
            {
                'error': 'Intent processing failed',
                'details': str(e),
                'response_time_ms': response_time_ms
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_featured_templates_simple(request):
    """
    Get featured templates using existing models
    """
    start_time = time.time()
    
    try:
        from .models import Template
        
        featured_templates = Template.objects.filter(
            is_featured=True,
            is_active=True,
            is_public=True
        ).select_related('category', 'author').order_by('-created_at')[:10]
        
        formatted_results = []
        for template in featured_templates:
            formatted_results.append({
                'id': str(template.id),
                'title': template.title,
                'description': template.description[:200],
                'category': template.category.name if template.category else None,
                'usage_count': template.usage_count,
                'average_rating': template.average_rating
            })
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return Response({
            'results': formatted_results,
            'total_results': len(formatted_results),
            'response_time_ms': response_time_ms
        })
        
    except Exception as e:
        logger.error(f"Featured templates error: {e}")
        return Response(
            {'error': 'Failed to fetch featured templates'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class SimpleHealthCheck(View):
    """
    Simple health check
    """
    
    def get(self, request):
        """Check basic system health"""
        try:
            # Test database connection
            from .models import Template
            template_count = Template.objects.count()
            
            # Test cache if available
            cache_working = False
            try:
                cache.set('health_check', 'ok', 10)
                cache_working = cache.get('health_check') == 'ok'
            except Exception:
                pass
            
            health_data = {
                'status': 'healthy',
                'database_connected': True,
                'template_count': template_count,
                'cache_working': cache_working,
                'timestamp': time.time(),
                'message': 'Basic system health check - run full setup for advanced features'
            }
            
            return JsonResponse(health_data)
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return JsonResponse({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def system_status(request):
    """
    Show current system status and available features
    """
    try:
        # Check what features are available
        features = {
            'basic_search': True,
            'intent_processing': True,
            'featured_templates': True,
        }
        
        # Check advanced features
        advanced_available = False
        try:
            from .search_services import search_service
            from .cache_services import multi_cache
            from .langchain_services import LangChainOptimizationService
            advanced_available = True
            features.update({
                'high_performance_search': True,
                'multi_level_caching': True,
                'langchain_integration': True,
                'websocket_chat': True,
                'performance_monitoring': True
            })
        except ImportError:
            features.update({
                'high_performance_search': False,
                'multi_level_caching': False,
                'langchain_integration': False,
                'websocket_chat': False,
                'performance_monitoring': False
            })
        
        # Database info
        from .models import Template, TemplateCategory
        db_info = {
            'templates_count': Template.objects.count(),
            'categories_count': TemplateCategory.objects.count(),
        }
        
        # Try to check prompt library
        try:
            from .models import PromptLibrary
            db_info['prompt_library_count'] = PromptLibrary.objects.count()
        except:
            db_info['prompt_library_count'] = 'Not available (run migrations)'
        
        return Response({
            'status': 'operational',
            'mode': 'advanced' if advanced_available else 'basic',
            'features': features,
            'database': db_info,
            'endpoints': {
                'search_prompts': '/api/templates/search/prompts/',
                'process_intent': '/api/templates/intent/process/',
                'featured_prompts': '/api/templates/prompts/featured/',
                'system_health': '/api/templates/health/websocket/',
                'this_status': '/api/templates/status/',
            },
            'setup_needed': [] if advanced_available else [
                'Install Redis: redis-server',
                'Install packages: pip install redis channels channels_redis django-redis langchain-community',
                'Run migrations: python manage.py makemigrations templates && python manage.py migrate',
                'Load sample data: python manage.py ingest_100k_prompts --file prompts.json'
            ],
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return Response(
            {'error': 'Status check failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )