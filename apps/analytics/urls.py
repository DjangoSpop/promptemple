from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    # Analytics endpoints
    path('dashboard/', views.AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
    path('user-insights/', views.UserInsightsView.as_view(), name='user-insights'),
    path('template-analytics/', views.TemplateAnalyticsView.as_view(), name='template-analytics'),
    path('ab-tests/', views.ABTestView.as_view(), name='ab-tests'),
    path('recommendations/', views.RecommendationView.as_view(), name='recommendations'),
    
    # Include router URLs
    path('', include(router.urls)),
]