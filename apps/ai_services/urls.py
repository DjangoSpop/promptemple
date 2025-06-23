from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    # AI service endpoints
    path('providers/', views.AIProviderListView.as_view(), name='ai-providers'),
    path('models/', views.AIModelListView.as_view(), name='ai-models'),
    path('generate/', views.AIGenerateView.as_view(), name='ai-generate'),
    path('usage/', views.AIUsageView.as_view(), name='ai-usage'),
    path('quotas/', views.AIQuotaView.as_view(), name='ai-quotas'),
    
    # Include router URLs
    path('', include(router.urls)),
]