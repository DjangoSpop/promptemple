from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

User = get_user_model()


class AnalyticsDashboardView(APIView):
    """
    Analytics dashboard with key metrics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return dashboard analytics"""
        user = request.user
        
        # Placeholder data - replace with real analytics later
        return Response({
            'user_stats': {
                'templates_created': 0,
                'templates_used': 0,
                'credits_earned': user.credits if hasattr(user, 'credits') else 0,
                'current_streak': 0
            },
            'recent_activity': [],
            'top_templates': [],
            'usage_trends': {
                'daily': [],
                'weekly': [],
                'monthly': []
            }
        })


class UserInsightsView(APIView):
    """
    User-specific insights and analytics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return user insights"""
        user = request.user
        
        return Response({
            'productivity_score': 75,
            'favorite_categories': [],
            'peak_usage_hours': [],
            'improvement_suggestions': [
                "Try creating templates for your most common prompts",
                "Explore new template categories to expand your creativity"
            ],
            'achievements_progress': [],
            'comparison_metrics': {
                'vs_last_week': 0,
                'vs_average_user': 0
            }
        })


class TemplateAnalyticsView(APIView):
    """
    Template usage and performance analytics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return template analytics"""
        return Response({
            'popular_templates': [],
            'category_usage': [],
            'performance_metrics': {
                'most_used': [],
                'highest_rated': [],
                'trending': []
            },
            'user_template_stats': {
                'created': 0,
                'published': 0,
                'total_uses': 0,
                'average_rating': 0
            }
        })


class ABTestView(APIView):
    """
    A/B testing analytics and management
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return A/B test results"""
        return Response({
            'active_tests': [],
            'user_segments': [],
            'test_results': []
        })


class RecommendationView(APIView):
    """
    AI-powered recommendations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return personalized recommendations"""
        return Response({
            'recommended_templates': [],
            'suggested_categories': [],
            'trending_prompts': [],
            'personalization_score': 0.75
        })


class AnalyticsTrackView(APIView):
    """
    Track user analytics events - allows anonymous tracking
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Track an analytics event"""
        event_type = request.data.get('event_type')
        event_data = request.data.get('data', {})
        user_id = None
        
        # If user is authenticated, include their ID
        if request.user and request.user.is_authenticated:
            user_id = request.user.id
        
        # Placeholder for analytics tracking logic
        # In a real implementation, you would save this to a database
        # or send it to an analytics service like Google Analytics, Mixpanel, etc.
        
        # Log the analytics event for debugging
        print(f"Analytics Event: {event_type} from user {user_id} with data: {event_data}")
        
        return Response({
            'status': 'success',
            'message': 'Event tracked successfully',
            'event_type': event_type,
            'user_id': user_id,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_201_CREATED)

# NOTE:
# - `track/` accepts anonymous events (AllowAny) so the frontend can record
#   usage before login or for anonymous users.
# - Other analytics endpoints (dashboard, user-insights, etc.) require
#   authentication (IsAuthenticated) and expect a valid JWT or session cookie.
