from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Import directly from views.py to avoid circular import with views/ directory
from apps.analytics.views import (
    AnalyticsDashboardView,
    UserInsightsView,
    TemplateAnalyticsView,
    ABTestView,
    RecommendationView,
    AnalyticsTrackView
)

router = DefaultRouter()

urlpatterns = [
    # Analytics endpoints
    path('dashboard/', AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
    path('user-insights/', UserInsightsView.as_view(), name='user-insights'),
    path('template-analytics/', TemplateAnalyticsView.as_view(), name='template-analytics'),
    path('ab-tests/', ABTestView.as_view(), name='ab-tests'),
    path('recommendations/', RecommendationView.as_view(), name='recommendations'),
    path('track/', AnalyticsTrackView.as_view(), name='analytics-track'),
    
    # Include router URLs
    path('', include(router.urls)),
]