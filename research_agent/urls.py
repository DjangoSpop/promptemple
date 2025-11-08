"""
URL routing for research agent API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ResearchJobViewSet,
    stream_job_progress,
    stream_cards,
    system_health,
    system_stats,
    quick_research,
    intent_fast,
    batch_research,
    start_job,
    job_status,
    stream_answer
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'jobs', ResearchJobViewSet, basename='research-job')

app_name = 'research_agent'

urlpatterns = [
    # RESTful API endpoints (v2)
    path('api/v2/research/', include([
        path('', include(router.urls)),

        # Quick access endpoints
        path('quick/', quick_research, name='quick-research'),
        path('intent_fast/', intent_fast, name='intent-fast'),
        path('batch/', batch_research, name='batch-research'),

        # Streaming endpoints
        path('jobs/<uuid:job_id>/stream/', stream_job_progress, name='stream-job-progress'),
        path('jobs/<uuid:job_id>/cards/stream/', stream_cards, name='stream-cards'),

        # System endpoints
        path('health/', system_health, name='system-health'),
        path('stats/', system_stats, name='system-stats'),
    ])),

    # v1 API endpoints for compatibility  
    path('api/v1/intent_fast/', intent_fast, name='v1-intent-fast'),
    path('api/v1/intent/', quick_research, name='v1-intent'),
    
    # Legacy API endpoints (v1 compatibility)
    path('api/v2/research/jobs/', start_job, name='legacy-start-job'),
    path('api/v2/research/jobs/<uuid:job_id>/', job_status, name='legacy-job-status'),
    path('api/v2/research/jobs/<uuid:job_id>/stream/', stream_answer, name='legacy-stream-answer'),
]

# URL patterns for testing and documentation
test_patterns = [
    # Test endpoints (only available in DEBUG mode)
    path('api/v2/research/test/', include([
        path('ping/', lambda request: JsonResponse({"status": "ok"}), name='test-ping'),
    ])),
]

# Add test patterns in debug mode
from django.conf import settings
if settings.DEBUG:
    from django.http import JsonResponse
    urlpatterns.extend(test_patterns)