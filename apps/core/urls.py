from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

app_name = 'core'

urlpatterns = [
    # Web interface pages
    path('', views.home, name='home'),
    path('api-tester/', views.api_tester, name='api-tester'),
    
    # Authentication page
    path('auth/', views.auth_page, name='auth-page'),
    
    # AI Services Testing Dashboard
    path('ai-test/', views.ai_dashboard, name='ai-dashboard'),
    path('ai-test/research/', views.research_agent_test, name='research-agent-test'),
    path('ai-test/research-pro/', views.research_agent_pro_test, name='research-agent-pro-test'),
    path('ai-test/optimizer/', views.prompt_optimizer_test, name='prompt-optimizer-test'),
    path('ai-test/rag-retrieve/', views.rag_retrieve_test, name='rag-retrieve-test'),
    path('ai-test/rag-answer/', views.rag_answer_test, name='rag-answer-test'),
    path('ai-test/deepseek/', views.deepseek_stream_test, name='deepseek-stream-test'),
    
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
    
    # Testing endpoints
    path('api/v2/status/', views.system_status, name='system-status'),
    path('api/v2/cors-test/', views.cors_test, name='cors-test'),
    
    # Include router URLs
    path('', include(router.urls)),
]