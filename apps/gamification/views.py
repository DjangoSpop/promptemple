### Step 7.3: Gamification API Views


from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

from .models import Achievement, UserAchievement, DailyChallenge, UserDailyChallenge, CreditTransaction
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
    List user badges
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's badges"""
        # Placeholder - implement badge system later
        return Response({
            'badges': [],
            'total_badges': 0,
            'recent_badges': []
        })


class LeaderboardView(APIView):
    """
    Leaderboard view
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get leaderboard data"""
        # Placeholder - implement leaderboard later
        return Response({
            'weekly_leaders': [],
            'monthly_leaders': [],
            'all_time_leaders': [],
            'user_rank': 0
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
    User level and experience view
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user level information"""
        user = request.user
        
        # Calculate level based on experience (placeholder logic)
        experience = getattr(user, 'experience_points', 0)
        level = max(1, experience // 100)  # 100 XP per level
        next_level_xp = (level * 100) + 100
        current_level_xp = experience - (level - 1) * 100
        
        return Response({
            'current_level': level,
            'experience_points': experience,
            'current_level_progress': current_level_xp,
            'next_level_requirement': next_level_xp,
            'progress_percentage': (current_level_xp / 100) * 100
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