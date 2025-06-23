from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Achievement, UserAchievement, DailyChallenge, UserDailyChallenge, CreditTransaction

User = get_user_model()


class AchievementSerializer(serializers.ModelSerializer):
    """
    Serializer for Achievement model
    """
    user_progress = serializers.SerializerMethodField()
    is_unlocked = serializers.SerializerMethodField()
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description', 'category', 'requirement_type',
            'requirement_value', 'credits_reward', 'experience_reward',
            'rarity', 'icon', 'is_hidden', 'user_progress', 'is_unlocked'
        ]
    
    def get_user_progress(self, obj):
        """Get user's progress for this achievement"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        try:
            user_achievement = UserAchievement.objects.get(
                user=request.user,
                achievement=obj
            )
            return user_achievement.progress_value
        except UserAchievement.DoesNotExist:
            return 0
    
    def get_is_unlocked(self, obj):
        """Check if user has unlocked this achievement"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        try:
            user_achievement = UserAchievement.objects.get(
                user=request.user,
                achievement=obj
            )
            return user_achievement.is_unlocked
        except UserAchievement.DoesNotExist:
            return False


class UserAchievementSerializer(serializers.ModelSerializer):
    """
    Serializer for UserAchievement model
    """
    achievement = AchievementSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement', 'progress_value', 'is_unlocked',
            'unlocked_at', 'progress_percentage', 'created_at', 'updated_at'
        ]
    
    def get_progress_percentage(self, obj):
        """Calculate progress percentage"""
        if obj.achievement.requirement_value == 0:
            return 100.0 if obj.is_unlocked else 0.0
        
        percentage = (obj.progress_value / obj.achievement.requirement_value) * 100
        return min(100.0, percentage)


class DailyChallengeSerializer(serializers.ModelSerializer):
    """
    Serializer for DailyChallenge model
    """
    user_progress = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyChallenge
        fields = [
            'id', 'title', 'description', 'challenge_type', 'target_value',
            'credits_reward', 'experience_reward', 'date', 'difficulty',
            'user_progress', 'is_completed'
        ]
    
    def get_user_progress(self, obj):
        """Get user's progress for this challenge"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        try:
            user_challenge = UserDailyChallenge.objects.get(
                user=request.user,
                challenge=obj
            )
            return user_challenge.progress_value
        except UserDailyChallenge.DoesNotExist:
            return 0
    
    def get_is_completed(self, obj):
        """Check if user has completed this challenge"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        try:
            user_challenge = UserDailyChallenge.objects.get(
                user=request.user,
                challenge=obj
            )
            return user_challenge.is_completed
        except UserDailyChallenge.DoesNotExist:
            return False


class UserDailyChallengeSerializer(serializers.ModelSerializer):
    """
    Serializer for UserDailyChallenge model
    """
    challenge = DailyChallengeSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UserDailyChallenge
        fields = [
            'id', 'challenge', 'progress_value', 'is_completed',
            'completed_at', 'progress_percentage', 'created_at', 'updated_at'
        ]
    
    def get_progress_percentage(self, obj):
        """Calculate progress percentage"""
        if obj.challenge.target_value == 0:
            return 100.0 if obj.is_completed else 0.0
        
        percentage = (obj.progress_value / obj.challenge.target_value) * 100
        return min(100.0, percentage)


class CreditTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for CreditTransaction model
    """
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    
    class Meta:
        model = CreditTransaction
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'amount', 'balance_after', 'description', 'reference_id',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for gamification contexts
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id', 'username', 'email']
