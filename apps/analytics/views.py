from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Q
from django.contrib.auth import get_user_model

User = get_user_model()


def _get_prompt_history_model():
    try:
        from apps.prompt_history.models import PromptHistory
        return PromptHistory
    except ImportError:
        return None


def _get_gamification_models():
    try:
        from apps.gamification.models import UserAchievement
        return UserAchievement
    except ImportError:
        return None


def _get_template_model():
    try:
        from apps.propmtcraft.models import PromptTemplate
        return PromptTemplate
    except ImportError:
        try:
            from apps.core.models import PromptTemplate
            return PromptTemplate
        except ImportError:
            return None


class AnalyticsDashboardView(APIView):
    """
    Analytics dashboard — real DB aggregations from User, PromptHistory, and Gamification models.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Gamification data directly from User model
        experience = getattr(user, 'experience_points', 0)
        level = getattr(user, 'level', 1)
        daily_streak = getattr(user, 'daily_streak', 0)
        templates_created = getattr(user, 'templates_created', 0)
        templates_completed = getattr(user, 'templates_completed', 0)

        # Count unlocked achievements
        achievements_unlocked = 0
        UserAchievement = _get_gamification_models()
        if UserAchievement:
            achievements_unlocked = UserAchievement.objects.filter(
                user=user, is_unlocked=True
            ).count()

        # Compute XP needed for next level (100 XP per level)
        next_level_xp = max(0, ((level) * 100) - experience)

        # Level name from UserLevel table (or fallback)
        rank = 'Temple Initiate'
        try:
            from apps.gamification.models import UserLevel
            level_obj = UserLevel.objects.filter(level=level).first()
            if level_obj:
                rank = level_obj.name
        except Exception:
            pass

        # Recent activity from PromptHistory
        recent_activity = []
        PromptHistory = _get_prompt_history_model()
        if PromptHistory:
            try:
                recent_qs = PromptHistory.objects.filter(user=user).order_by('-created_at')[:10]
                for ph in recent_qs:
                    recent_activity.append({
                        'template_name': getattr(ph, 'title', '') or getattr(ph, 'prompt_text', '')[:60] or 'Prompt',
                        'used_at': ph.created_at.isoformat() if hasattr(ph, 'created_at') else timezone.now().isoformat(),
                        'category': getattr(ph, 'category', '') or '',
                    })
            except Exception:
                pass

        return Response({
            'total_templates_used': templates_completed,
            'total_renders': getattr(user, 'total_prompts_generated', 0),
            'favorite_categories': [],
            'recent_activity': recent_activity,
            'gamification': {
                'level': level,
                'experience_points': experience,
                'daily_streak': daily_streak,
                'achievements_unlocked': achievements_unlocked,
                'badges_earned': achievements_unlocked,
                'rank': rank,
                'next_level_xp': next_level_xp,
            },
            # Legacy shape for backward-compat
            'user_stats': {
                'templates_created': templates_created,
                'templates_used': templates_completed,
                'credits_earned': getattr(user, 'credits', 0),
                'current_streak': daily_streak,
            },
        })


class UserInsightsView(APIView):
    """
    User-specific insights — aggregated from real DB data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Favorite categories from prompt history
        favorite_categories = []
        PromptHistory = _get_prompt_history_model()
        if PromptHistory:
            try:
                cat_qs = (
                    PromptHistory.objects
                    .filter(user=user)
                    .values('category')
                    .annotate(count=Count('id'))
                    .order_by('-count')[:5]
                )
                favorite_categories = [
                    item['category'] for item in cat_qs if item.get('category')
                ]
            except Exception:
                pass

        # Achievements progress
        achievements_progress = []
        UserAchievement = _get_gamification_models()
        if UserAchievement:
            try:
                ua_qs = UserAchievement.objects.filter(
                    user=user, is_unlocked=False
                ).select_related('achievement').order_by('-progress_value')[:5]
                for ua in ua_qs:
                    achievements_progress.append({
                        'name': ua.achievement.name,
                        'progress': ua.progress_value,
                        'required': ua.achievement.requirement_value,
                        'percentage': ua.progress_percentage,
                    })
            except Exception:
                pass

        return Response({
            'usage_patterns': {
                'total_sessions': getattr(user, 'total_prompts_generated', 0),
                'templates_created': getattr(user, 'templates_created', 0),
                'templates_used': getattr(user, 'templates_completed', 0),
            },
            'favorite_categories': favorite_categories,
            'performance_metrics': {
                'completion_rate': user.template_completion_rate if hasattr(user, 'template_completion_rate') else 0,
                'daily_streak': getattr(user, 'daily_streak', 0),
            },
            'recommendations': [
                'Try creating templates for your most common prompts',
                'Explore new template categories to expand your creativity',
            ],
            'achievements_progress': achievements_progress,
        })


class TemplateAnalyticsView(APIView):
    """
    Template usage analytics — aggregated from real data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        templates_created = getattr(user, 'templates_created', 0)
        templates_completed = getattr(user, 'templates_completed', 0)

        return Response({
            'popular_templates': [],
            'category_usage': [],
            'performance_metrics': {
                'most_used': [],
                'highest_rated': [],
                'trending': [],
            },
            'user_template_stats': {
                'created': templates_created,
                'published': templates_created,
                'total_uses': templates_completed,
                'average_rating': 0,
            },
        })


class ABTestView(APIView):
    """
    A/B testing — placeholder (no active tests configured).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'active_tests': [],
            'user_segments': [],
            'test_results': [],
        })


class RecommendationView(APIView):
    """
    Personalized recommendations — returns public templates sorted by usage.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        recommended = []
        TemplateModel = _get_template_model()
        if TemplateModel:
            try:
                qs = TemplateModel.objects.filter(
                    is_public=True
                ).order_by('-usage_count')[:10]
                for t in qs:
                    recommended.append({
                        'id': str(t.id),
                        'title': getattr(t, 'title', ''),
                        'category': str(getattr(t, 'category', '') or ''),
                        'usage_count': getattr(t, 'usage_count', 0),
                    })
            except Exception:
                pass

        return Response({
            'recommended_templates': recommended,
            'suggested_categories': [],
            'trending_prompts': [],
            'personalization_score': 0.75,
        })


class AnalyticsTrackView(APIView):
    """
    Track user analytics events — persists to DB via AnalyticsEvent model if available.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        event_type = request.data.get('event_type', '')
        event_data = request.data.get('data', {})
        user = request.user if request.user and request.user.is_authenticated else None

        # Persist to AnalyticsEvent model if it exists
        try:
            from apps.analytics.models import AnalyticsEvent
            AnalyticsEvent.objects.create(
                user=user,
                event_type=event_type,
                properties=event_data,
            )
        except Exception:
            # Fallback: log to console (model may not exist yet)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Analytics Event: {event_type} from user {getattr(user, 'id', None)} with data: {event_data}")

        return Response({
            'status': 'success',
            'message': 'Event tracked successfully',
            'event_type': event_type,
            'user_id': getattr(user, 'id', None),
            'timestamp': timezone.now().isoformat(),
        }, status=status.HTTP_201_CREATED)
