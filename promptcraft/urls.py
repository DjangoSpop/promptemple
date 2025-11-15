"""
URL configuration for promptcraft project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView, 
    SpectacularRedocView, 
    SpectacularSwaggerView
)
from django.views.generic import TemplateView
from apps.core.views import HealthCheckView, health_simple
from apps.core.socketio_views import SocketIOCompatibilityView, WebSocketInfoView
from django.http import JsonResponse


def trigger_error(request):
    division_by_zero = 1 / 0


def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Welcome to PromptCraft API',
        'version': '2.0.0',
        'api_versions': {
            'v1': 'Legacy API endpoints',
            'v2': 'Current API endpoints (recommended)'
        },
        'endpoints': {
            'health': '/health/',
            'api_docs': '/api/schema/swagger-ui/',
            'mvp_auth': '/api/mvp/auth/',
            'mvp_templates': '/api/mvp/templates/',
            'templates': '/api/v2/templates/',
            'categories': '/api/v2/template-categories/',
            'auth': '/api/v2/auth/',
            'billing': '/api/v2/billing/',
            'orchestrator': '/api/v2/orchestrator/',
            'analytics': '/api/v2/analytics/',
            'core': '/api/v2/core/',
            'research': '/api/v2/research/',
        },
        'template_endpoints': {
            'list': '/api/v2/templates/',
            'featured': '/api/v2/templates/featured/',
            'trending': '/api/v2/templates/trending/',
            'categories': '/api/v2/template-categories/',
        },
        'orchestrator_endpoints': {
            'intent_detection': '/api/v2/orchestrator/intent/',
            'prompt_assessment': '/api/v2/orchestrator/assess/',
            'template_rendering': '/api/v2/orchestrator/render/',
            'library_search': '/api/v2/orchestrator/search/',
            'get_template': '/api/v2/orchestrator/template/',
        },
        'billing_endpoints': {
            'plans': '/api/v2/billing/plans/',
            'entitlements': '/api/v2/billing/me/entitlements/',
            'checkout': '/api/v2/billing/checkout/',
            'portal': '/api/v2/billing/portal/',
        },
        'analytics_endpoints': {
            'dashboard': '/api/v2/analytics/dashboard/',
            'user_insights': '/api/v2/analytics/user-insights/',
            'template_analytics': '/api/v2/analytics/template-analytics/',
            'track': '/api/v2/analytics/track/',
        },
        'core_endpoints': {
            'config': '/api/v2/core/config/',
            'health': '/api/v2/core/health/',
        },
        'research_endpoints': {
            'jobs': '/api/v2/research/jobs/',
            'quick': '/api/v2/research/quick/',
            'intent_fast': '/api/v2/research/intent_fast/',
            'batch': '/api/v2/research/batch/',
            'health': '/api/v2/research/health/',
            'stats': '/api/v2/research/stats/',
            'stream': '/api/v2/research/jobs/{job_id}/stream/',
            'cards_stream': '/api/v2/research/jobs/{job_id}/cards/stream/',
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
     path('sentry-debug/', trigger_error),
    # Health check endpoint (simple, no DB dependencies for Railway)
    path('health/', health_simple, name='health-check'),
    
    # MVP UI - Full-stack Django interface for API testing
    path('mvp-ui/', include('apps.mvp_ui.urls', namespace='mvp_ui')),
    
    # Socket.IO compatibility endpoints (to handle frontend Socket.IO requests gracefully)
    path('socket.io/', SocketIOCompatibilityView.as_view(), name='socketio-compatibility'),
    path('ws/info/', WebSocketInfoView.as_view(), name='websocket-info'),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # API Documentation URLs (temporarily disabled)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # MVP API - Professional clean endpoints for production
    path('api/mvp/auth/', include(('apps.users.mvp_urls', 'mvp_auth'), namespace='mvp_auth')),
    path('api/mvp/templates/', include(('apps.templates.mvp_urls', 'mvp_templates'), namespace='mvp_templates')),
    
    # API v2 URLs (current version)
    path('api/v2/', include(('apps.templates.urls', 'templates_api_v2'), namespace='templates_api_v2')),
    path('api/v2/auth/', include(('apps.users.urls', 'users_v2'), namespace='users_v2')),
    path('api/v2/ai/', include(('apps.ai_services.urls', 'ai_services_v2'), namespace='ai_services_v2')),
    path('api/v2/chat/', include(('apps.chat.urls', 'chat_v2'), namespace='chat_v2')),
    path('api/v2/gamification/', include(('apps.gamification.urls', 'gamification_v2'), namespace='gamification_v2')),
    path('api/v2/analytics/', include(('apps.analytics.urls', 'analytics_v2'), namespace='analytics_v2')),
    path('api/v2/core/', include(('apps.core.urls', 'core_v2'), namespace='core_v2')),
    path('api/v2/billing/', include(('apps.billing.urls', 'billing_v2'), namespace='billing_v2')),
    path('api/v2/orchestrator/', include(('apps.orchestrator.urls', 'orchestrator_v2'), namespace='orchestrator_v2')),
    path('', include(('research_agent.urls', 'research_agent'), namespace='research_agent')),
    
    # API v1 URLs (legacy support)
    path('api/v1/', include(('apps.templates.urls', 'templates_api_v1'), namespace='templates_api_v1')),
    path('api/v1/auth/', include(('apps.users.urls', 'users_v1'), namespace='users_v1')),
    path('api/v1/ai/', include(('apps.ai_services.urls', 'ai_services_v1'), namespace='ai_services_v1')),
    path('api/v1/gamification/', include(('apps.gamification.urls', 'gamification_v1'), namespace='gamification_v1')),
    path('api/v1/analytics/', include(('apps.analytics.urls', 'analytics_v1'), namespace='analytics_v1')),
    path('api/v1/core/', include(('apps.core.urls', 'core_v1'), namespace='core_v1')),
    path('api/v1/billing/', include(('apps.billing.urls', 'billing_v1'), namespace='billing_v1')),
    path('api/v1/orchestrator/', include(('apps.orchestrator.urls', 'orchestrator_v1'), namespace='orchestrator_v1')),
    
    # Web interface - Testing Dashboard (place this LAST, before debug toolbar)
    path('', include('apps.core.urls')),
]

# Add debug toolbar URLs in development
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Add REST framework URLs if installed
if 'rest_framework' in settings.INSTALLED_APPS:
    urlpatterns.append(
        path('api-auth/', include('rest_framework.urls')),
    )

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

