from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import agent_views
from . import askme_views

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
    
    # AI Assistant endpoints
    path('assistant/', views.AssistantListView.as_view(), name='assistant-list'),
    path('assistant/run/', views.AssistantRunView.as_view(), name='assistant-run'),
    path('assistant/threads/', views.AssistantThreadListView.as_view(), name='assistant-thread-list'),
    path('assistant/threads/<uuid:thread_id>/', views.AssistantThreadDetailView.as_view(), name='assistant-thread-detail'),

    # RAG Agent endpoints
    path('agent/optimize/', agent_views.optimize_prompt, name='agent-optimize'),
    path('agent/stats/', agent_views.agent_stats, name='agent-stats'),
    # RAG retrieval and answer endpoints
    path('rag/retrieve/', agent_views.rag_retrieve, name='rag-retrieve'),
    path('rag/answer/', agent_views.rag_answer, name='rag-answer'),

    # Ask-Me Prompt Builder endpoints
    path('askme/start/', askme_views.askme_start_api, name='askme-start'),
    path('askme/answer/', askme_views.askme_answer_api, name='askme-answer'),
    path('askme/finalize/', askme_views.askme_finalize_api, name='askme-finalize'),
    path('askme/stream/', askme_views.askme_stream_api, name='askme-stream'),

    # Ask-Me session management
    path('askme/sessions/', askme_views.askme_sessions_list, name='askme-sessions-list'),
    path('askme/sessions/<uuid:session_id>/', askme_views.askme_session_detail, name='askme-session-detail'),
    path('askme/sessions/<uuid:session_id>/delete/', askme_views.askme_session_delete, name='askme-session-delete'),

    # Debug endpoint
    path('askme/debug/', askme_views.askme_debug_test, name='askme-debug'),

    # Include router URLs
    path('', include(router.urls)),
]
