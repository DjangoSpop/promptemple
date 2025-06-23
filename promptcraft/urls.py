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

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API URLs
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/templates/', include('apps.templates.urls')),
    path('api/v1/ai/', include('apps.ai_services.urls')),
    path('api/v1/gamification/', include('apps.gamification.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/core/', include('apps.core.urls')),
    
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