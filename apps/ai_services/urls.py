from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import agent_views

router = DefaultRouter()

urlpatterns = [
    # AI service endpoints
    path('providers/', views.AIProviderListView.as_view(), name='ai-providers'),
    path('models/', views.AIModelListView.as_view(), name='ai-models'),
    path('generate/', views.AIGenerateView.as_view(), name='ai-generate'),
    path('usage/', views.AIUsageView.as_view(), name='ai-usage'),
    path('quotas/', views.AIQuotaView.as_view(), name='ai-quotas'),
    path('suggestions/', views.ai_suggestions, name='ai-suggestions'),
    
    # DeepSeek specific endpoints
    path('deepseek/chat/', views.deepseek_chat, name='deepseek-chat'),
    path('deepseek/test/', views.deepseek_test, name='deepseek-test'),
    # Streaming proxy for DeepSeek (SSE-like single-event streaming fallback)
    path('deepseek/stream/', views.DeepSeekStreamView.as_view(), name='deepseek-stream'),
    
    # RAG Agent endpoints
    path('agent/optimize/', agent_views.optimize_prompt, name='agent-optimize'),
    path('agent/stats/', agent_views.agent_stats, name='agent-stats'),
    # RAG retrieval and answer endpoints
    path('rag/retrieve/', agent_views.rag_retrieve, name='rag-retrieve'),
    path('rag/answer/', agent_views.rag_answer, name='rag-answer'),
    
    # Include router URLs
    path('', include(router.urls)),
]