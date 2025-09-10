"""
URL patterns for Templates API with high-performance search and WebSocket integration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.templates.views import (
    TemplateCategoryViewSet, TemplateViewSet,
)

# Try to import high-performance endpoints, fallback to simple ones
# Always import system_status from simple_views
from apps.templates.simple_views import system_status

try:
    from apps.templates.views import (
        search_prompts, process_intent, get_featured_prompts_library,
        get_similar_prompts, get_performance_metrics, WebSocketHealthCheck
    )
    ADVANCED_FEATURES = True
except ImportError:
    from apps.templates.simple_views import (
        search_prompts_simple as search_prompts,
        process_intent_simple as process_intent, 
        get_featured_templates_simple as get_featured_prompts_library,
        SimpleHealthCheck as WebSocketHealthCheck
    )
    # Create dummy functions for missing endpoints
    def get_similar_prompts(request, prompt_id):
        from rest_framework.response import Response
        return Response({'error': 'Feature not available - install advanced components'}, status=503)
    
    def get_performance_metrics(request):
        from rest_framework.response import Response
        return Response({'error': 'Feature not available - install advanced components'}, status=503)
    
    ADVANCED_FEATURES = False

# Create router and register viewsets
router = DefaultRouter()
router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'template-categories', TemplateCategoryViewSet, basename='category')

app_name = 'templates_api'

urlpatterns = [
    # Router URLs - existing template functionality
    path('', include(router.urls)),
    
    # High-performance search endpoints for 100K prompt library
    # Note: Will use simplified versions if advanced components not installed
    path('search/prompts/', search_prompts, name='search-prompts'),
    path('intent/process/', process_intent, name='process-intent'),
    path('prompts/featured/', get_featured_prompts_library, name='featured-prompts'),
    path('prompts/<str:prompt_id>/similar/', get_similar_prompts, name='similar-prompts'),
    
    # Performance and health monitoring  
    path('metrics/performance/', get_performance_metrics, name='performance-metrics'),
    path('health/websocket/', WebSocketHealthCheck.as_view(), name='websocket-health'),
    
    # System status endpoint - always available
    path('status/', system_status, name='system-status'),
    
    # Legacy search endpoints (commented for reference)
    # path('search/', search_templates, name='search'),
    # path('autocomplete/', autocomplete_search, name='autocomplete'),
    # path('copy/', copy_template_content, name='copy-template'),
    # path('user/stats/', user_usage_stats, name='user-stats'),
    # path('freemium/', freemium_info, name='freemium-info'),
]