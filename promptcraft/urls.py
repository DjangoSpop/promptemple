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
from apps.core.views import HealthCheckView
from django.http import JsonResponse

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
            'templates': '/api/v2/templates/',
            'categories': '/api/v2/template-categories/',
            'auth': '/api/v2/auth/',
            'billing': '/api/v2/billing/',
            'orchestrator': '/api/v2/orchestrator/',
            'analytics': '/api/v2/analytics/',
            'core': '/api/v2/core/',
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
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health-check'),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # API Documentation URLs (temporarily disabled)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v2 URLs (current version)
    path('api/v2/', include('apps.templates.urls')),
    path('api/v2/auth/', include('apps.users.urls')),
    path('api/v2/ai/', include('apps.ai_services.urls')),
    path('api/v2/gamification/', include('apps.gamification.urls')),
    path('api/v2/analytics/', include('apps.analytics.urls')),
    path('api/v2/core/', include('apps.core.urls')),
    path('api/v2/billing/', include('apps.billing.urls')),
    path('api/v2/orchestrator/', include('apps.orchestrator.urls')),
    
    # API v1 URLs (legacy support)
    path('api/v1/', include('apps.templates.urls')),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/ai/', include('apps.ai_services.urls')),
    path('api/v1/gamification/', include('apps.gamification.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/core/', include('apps.core.urls')),
    path('api/v1/billing/', include('apps.billing.urls')),
    path('api/v1/orchestrator/', include('apps.orchestrator.urls')),
    
    # Coming Soon page
    path('', TemplateView.as_view(template_name='coming_soon.html'), name='coming_soon'),
]

# Add debug toolbar URLs in development
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Add REST framework URLs if installed
if 'rest_framework' in settings.INSTALLED_APPS:
    urlpatterns.append(
        path('api-auth/', include('rest_framework.urls')),
    )

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)