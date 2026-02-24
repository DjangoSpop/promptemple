### Step 7.3: Gamification API Views


from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

from .models import Achievement, UserAchievement, DailyChallenge, UserDailyChallenge, CreditTransaction, UserLevel
from .serializers import (
    AchievementSerializer, UserAchievementSerializer, 
    DailyChallengeSerializer, CreditTransactionSerializer
)
from .services import GamificationService
from apps.analytics.services import AnalyticsService

class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for achievements
    
    Provides:
    - List all available achievements
    - User's achievement progress
    - Achievement claiming
    """
    
    queryset = Achievement.objects.filter(is_active=True)
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter achievements based on availability and visibility"""
        queryset = super().get_queryset()
        
        # Hide hidden achievements unless user has progress
        if not self.request.user.is_staff:
            # Show non-hidden achievements OR hidden achievements user has progress on
            queryset = queryset.filter(
                Q(is_hidden=False) |
                Q(user_unlocks__user=self.request.user, user_unlocks__progress_value__gt=0)
            ).distinct()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def user_progress(self, request):
        """Get user's achievement progress"""
        user_achievements = UserAchievement.objects.filter(
            user=request.user
        ).select_related('achievement').order_by('-updated_at')
        
        serializer = UserAchievementSerializer(user_achievements, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def claim_reward(self, request, pk=None):
        """Claim achievement reward"""
        achievement = self.get_object()
        
        try:
            reward_info = GamificationService.claim_achievement_reward(
                user=request.user,
                achievement_id=achievement.id
            )
            
            # Track analytics
            AnalyticsService.track_event(
                user=request.user,
                event_name='achievement_claimed',
                category='gamification',
                properties={
                    'achievement_id': str(achievement.id),
                    'achievement_name': achievement.name,
                    'credits_earned': reward_info['credits_earned'],
                    'experience_earned': reward_info['experience_earned']
                }
            )
            
            return Response({
                'message': 'Achievement reward claimed successfully',
                **reward_info
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class DailyChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for daily challenges
    """
    
    serializer_class = DailyChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get today's active challenges"""
        today = timezone.now().date()
        return DailyChallenge.objects.filter(
            date=today,
            is_active=True
        )
    
    def get_serializer_context(self):
        """Add request context for user progress"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CreditTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for credit transaction history
    """
    
    serializer_class = CreditTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get user's credit transactions"""
        return CreditTransaction.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats_view(request):
    """
    Get comprehensive user gamification statistics
    """
    stats = GamificationService.get_user_stats(request.user)
    
    # Track analytics
    AnalyticsService.track_event(
        user=request.user,
        event_name='gamification_stats_viewed',
        category='gamification',
        properties={
            'user_level': stats['level'],
            'user_credits': stats['credits'],
            'daily_streak': stats['daily_streak']
        }
    )
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_achievements_view(request):
    """
    Manually trigger achievement checking
    """
    unlocked_achievements = GamificationService.check_achievements(request.user)
    
    if unlocked_achievements:
        achievement_data = [
            {
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'credits_reward': ua.achievement.credits_reward,
                'experience_reward': ua.achievement.experience_reward,
                'rarity': ua.achievement.rarity
            }
            for ua in unlocked_achievements
        ]
        
        return Response({
            'message': f'Unlocked {len(unlocked_achievements)} new achievement(s)!',
            'new_achievements': achievement_data
        })
    
    return Response({
        'message': 'No new achievements unlocked',
        'new_achievements': []
    })


# Add these class-based views for the URL endpoints

class AchievementListView(APIView):
    """
    List all achievements
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get all achievements with user progress"""
        achievements = Achievement.objects.filter(is_active=True)
        if not request.user.is_staff:
            achievements = achievements.filter(is_hidden=False)
        
        serializer = AchievementSerializer(achievements, many=True)
        return Response(serializer.data)


class BadgeListView(APIView):
    """
    List user badges — derived from unlocked achievements (rarity: rare/epic/legendary).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Treat high-rarity unlocked achievements as badges
        badge_rarities = ('rare', 'epic', 'legendary')
        user_achievements = UserAchievement.objects.filter(
            user=request.user,
            is_unlocked=True,
            achievement__rarity__in=badge_rarities,
        ).select_related('achievement').order_by('-unlocked_at')

        badges = []
        for ua in user_achievements:
            a = ua.achievement
            badges.append({
                'id': str(a.id),
                'name': a.name,
                'description': a.description,
                'icon': a.icon,
                'rarity': a.rarity,
                'earned_at': ua.unlocked_at.isoformat() if ua.unlocked_at else None,
                'category': a.category,
            })

        recent = badges[:5]
        return Response({
            'badges': badges,
            'total_badges': len(badges),
            'recent_badges': recent,
        })


class LeaderboardView(APIView):
    """
    Leaderboard — top users by experience points from the User model.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        limit = int(request.query_params.get('limit', 50))

        def build_leaderboard(qs, requesting_user):
            entries = []
            for rank, user in enumerate(qs, start=1):
                entries.append({
                    'rank': rank,
                    'user_id': str(user.id),
                    'username': user.username,
                    'level': getattr(user, 'level', 1),
                    'experience_points': getattr(user, 'experience_points', 0),
                    'daily_streak': getattr(user, 'daily_streak', 0),
                    'is_current_user': user.id == requesting_user.id,
                })
            return entries

        # All-time: top by XP
        all_time_qs = User.objects.filter(
            is_active=True
        ).order_by('-experience_points')[:limit]
        all_time = build_leaderboard(all_time_qs, request.user)

        # Weekly: users active in last 7 days (last_login approximation)
        week_ago = timezone.now() - timezone.timedelta(days=7)
        weekly_qs = User.objects.filter(
            is_active=True,
            last_login__gte=week_ago,
        ).order_by('-experience_points')[:limit]
        weekly = build_leaderboard(weekly_qs, request.user)

        # User's own rank in all-time
        user_rank = 0
        for entry in all_time:
            if entry['is_current_user']:
                user_rank = entry['rank']
                break

        return Response({
            'weekly_leaders': weekly,
            'monthly_leaders': all_time,  # monthly approximation
            'all_time_leaders': all_time,
            'user_rank': user_rank,
            'current_user': {
                'level': getattr(request.user, 'level', 1),
                'experience_points': getattr(request.user, 'experience_points', 0),
                'rank': user_rank,
            },
        })


class DailyChallengeView(APIView):
    """
    Daily challenges view
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get today's challenges"""
        today = timezone.now().date()
        challenges = DailyChallenge.objects.filter(
            date=today,
            is_active=True
        )
        
        serializer = DailyChallengeSerializer(challenges, many=True)
        return Response(serializer.data)


class UserLevelView(APIView):
    """
    User level and experience — resolves against the UserLevel table.
    Falls back to 100-XP-per-level formula when the table is empty.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        experience = getattr(user, 'experience_points', 0)
        user_level_number = getattr(user, 'level', 1)

        # Try to resolve against the UserLevel ladder
        try:
            current_level_obj = UserLevel.objects.filter(
                experience_required__lte=experience
            ).order_by('-experience_required').first()

            next_level_obj = UserLevel.objects.filter(
                experience_required__gt=experience
            ).order_by('experience_required').first()

            if current_level_obj:
                level_number = current_level_obj.level
                level_name = current_level_obj.name
                current_xp_floor = current_level_obj.experience_required
                next_xp = next_level_obj.experience_required if next_level_obj else current_xp_floor + 500
                xp_in_level = experience - current_xp_floor
                xp_needed = next_xp - current_xp_floor
                progress_pct = round((xp_in_level / xp_needed) * 100, 1) if xp_needed > 0 else 100.0
                points_to_next = max(0, next_xp - experience)

                # Collect benefits from next level
                level_benefits = []
                if next_level_obj:
                    if getattr(next_level_obj, 'credits_reward', 0):
                        level_benefits.append(f"{next_level_obj.credits_reward} bonus credits")
                    if getattr(next_level_obj, 'title_reward', ''):
                        level_benefits.append(f'Title: "{next_level_obj.title_reward}"')
                    if getattr(next_level_obj, 'can_create_premium', False):
                        level_benefits.append("Unlock premium templates")
                    if getattr(next_level_obj, 'ai_requests_per_day', 0):
                        level_benefits.append(f"{next_level_obj.ai_requests_per_day} AI requests/day")

                return Response({
                    'current_level': level_number,
                    'level_name': level_name,
                    'experience_points': experience,
                    'current_level_progress': xp_in_level,
                    'next_level_requirement': next_xp,
                    'points_to_next_level': points_to_next,
                    'progress_percentage': progress_pct,
                    'level_benefits': level_benefits,
                    'perks': {
                        'max_templates': getattr(current_level_obj, 'max_templates', 10),
                        'ai_requests_per_day': getattr(current_level_obj, 'ai_requests_per_day', 5),
                        'can_create_premium': getattr(current_level_obj, 'can_create_premium', False),
                    },
                })
        except Exception:
            pass  # Fall through to formula-based fallback

        # Formula fallback (100 XP per level)
        level = max(1, user_level_number or (experience // 100 + 1))
        xp_floor = (level - 1) * 100
        next_level_xp = level * 100
        xp_in_level = experience - xp_floor
        return Response({
            'current_level': level,
            'level_name': f'Level {level}',
            'experience_points': experience,
            'current_level_progress': xp_in_level,
            'next_level_requirement': next_level_xp,
            'points_to_next_level': max(0, next_level_xp - experience),
            'progress_percentage': round((xp_in_level / 100) * 100, 1),
            'level_benefits': [],
            'perks': {'max_templates': 10, 'ai_requests_per_day': 5, 'can_create_premium': False},
        })


class StreakView(APIView):
    """
    User streak information
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user streak data"""
        user = request.user
        
        return Response({
            'current_streak': getattr(user, 'daily_streak', 0),
            'longest_streak': getattr(user, 'longest_streak', 0),
            'streak_freeze_available': False,
            'days_until_streak_reward': 7 - (getattr(user, 'daily_streak', 0) % 7)
        })