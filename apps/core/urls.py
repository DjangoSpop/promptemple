from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    # Core endpoints
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    path('config/', views.AppConfigurationView.as_view(), name='app-config'),
    path('notifications/', views.NotificationView.as_view(), name='notifications'),
    
    # Include router URLs
    path('', include(router.urls)),
]