from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    # Simple health endpoint (minimal dependencies)
    path('health/', views.health_simple, name='health-simple'),
    # Comprehensive health endpoint  
    path('health/detailed/', views.HealthCheckView.as_view(), name='health-detailed'),
    # App configuration endpoints
    path('config/', views.app_config, name='app-config-simple'),
    path('configuration/', views.AppConfigurationView.as_view(), name='app-configuration'),
    # RAG status endpoint
    path('rag/status/', views.rag_status, name='rag-status'),
    path('notifications/', views.NotificationView.as_view(), name='notifications'),
    
    # Include router URLs
    path('', include(router.urls)),
]