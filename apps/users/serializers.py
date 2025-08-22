from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
import re

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    
    Handles user creation with password confirmation
    and input validation
    """
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text="Confirm your password"
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'bio',
            'theme_preference', 'language_preference'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate_username(self, value):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, hyphens, and underscores."
            )
        if len(value) < 3:
            raise serializers.ValidationError(
                "Username must be at least 3 characters long."
            )
        return value
    
    def validate_email(self, value):
        """Validate email format and uniqueness"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value
    
    def validate(self, attrs):
        """Validate password confirmation and strength"""
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': "Passwords do not match."
            })
        
        # Validate password strength using Django's validators
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create new user with hashed password"""
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    
    Supports login with username or email
    """
    
    username = serializers.CharField(
        help_text="Username or email address"
    )
    password = serializers.CharField(
        write_only=True,
        help_text="User password"
    )
    
    def validate(self, attrs):
        """Authenticate user with username/email and password"""
        username_or_email = attrs.get('username')
        password = attrs.get('password')
        
        if not username_or_email or not password:
            raise serializers.ValidationError(
                "Username/email and password are required."
            )
        
        user = None
        
        # First try to authenticate with the input as-is (username)
        user = authenticate(
            username=username_or_email,
            password=password
        )
        
        # If authentication failed and input looks like email, try to find user by email
        if not user and '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                # Try to authenticate with the found username
                user = authenticate(
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                pass
        
        if not user:
            raise serializers.ValidationError(
                "Invalid credentials. Please check your username/email and password."
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                "User account is disabled."
            )
        
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile display
    
    Read-only serializer for showing user information
    """
    
    completion_rate = serializers.ReadOnlyField()
    avatar_url = serializers.SerializerMethodField()
    rank_info = serializers.SerializerMethodField()
    next_level_xp = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'avatar_url', 'bio', 'date_joined', 'last_login',
            'credits', 'level', 'experience_points', 'daily_streak',
            'user_rank', 'rank_info', 'next_level_xp', 'is_premium',
            'premium_expires_at', 'theme_preference', 'language_preference',
            'ai_assistance_enabled', 'analytics_enabled',
            'templates_created', 'templates_completed', 'total_prompts_generated',
            'completion_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'credits', 'level',
            'experience_points', 'daily_streak', 'user_rank', 'is_premium',
            'premium_expires_at', 'templates_created', 'templates_completed',
            'total_prompts_generated', 'created_at', 'updated_at'
        ]
    
    def get_avatar_url(self, obj):
        """Get avatar URL or default"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def get_rank_info(self, obj):
        """Get detailed rank information"""
        return {
            'current_rank': obj.user_rank,
            'level': obj.level,
            'next_rank': self._get_next_rank(obj.level)
        }
    
    def get_next_level_xp(self, obj):
        """Calculate XP needed for next level"""
        current_level_xp = (obj.level - 1) * 100
        next_level_xp = obj.level * 100
        return next_level_xp - obj.experience_points
    
    def _get_next_rank(self, level):
        """Get next rank title based on level"""
        rank_titles = {
            1: 'Prompt Novice',
            5: 'Template Explorer',
            10: 'AI Apprentice',
            20: 'Prompt Craftsman',
            35: 'Template Master',
            50: 'AI Virtuoso',
            75: 'Prompt Legend',
            100: 'Template Grandmaster'
        }
        
        for required_level in sorted(rank_titles.keys()):
            if level < required_level:
                return rank_titles[required_level]
        return 'Template Grandmaster'


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    
    Allows users to update their profile information
    """
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'bio', 'avatar',
            'theme_preference', 'language_preference',
            'ai_assistance_enabled', 'analytics_enabled'
        ]
    
    def validate_bio(self, value):
        """Validate bio length"""
        if len(value) > 500:
            raise serializers.ValidationError(
                "Bio cannot be longer than 500 characters."
            )
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password
    
    Requires current password and validates new password
    """
    
    current_password = serializers.CharField(
        write_only=True,
        help_text="Current password"
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="New password (minimum 8 characters)"
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        help_text="Confirm new password"
    )
    
    def validate_current_password(self, value):
        """Verify current password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Current password is incorrect."
            )
        return value
    
    def validate(self, attrs):
        """Validate new password confirmation and strength"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': "New passwords do not match."
            })
        
        # Validate password strength
        try:
            validate_password(new_password, self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        return attrs
    
    def save(self):
        """Update user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for user statistics and gamification data
    
    Provides comprehensive user performance metrics
    """
    
    completion_rate = serializers.ReadOnlyField()
    level_progress = serializers.SerializerMethodField()
    streak_info = serializers.SerializerMethodField()
    credit_history = serializers.SerializerMethodField()
    achievements_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'level', 'experience_points', 'credits',
            'daily_streak', 'user_rank', 'templates_created',
            'templates_completed', 'total_prompts_generated',
            'completion_rate', 'level_progress', 'streak_info',
            'credit_history', 'achievements_summary'
        ]
        read_only_fields = [
            'id', 'username', 'level', 'experience_points', 'credits',
            'daily_streak', 'user_rank', 'templates_created',
            'templates_completed', 'total_prompts_generated',
            'completion_rate', 'level_progress', 'streak_info',
            'credit_history', 'achievements_summary'
        ]
    
    def get_level_progress(self, obj):
        """Calculate level progress information"""
        current_level_xp = (obj.level - 1) * 100
        next_level_xp = obj.level * 100
        progress_xp = obj.experience_points - current_level_xp
        needed_xp = next_level_xp - obj.experience_points
        
        return {
            'current_level': obj.level,
            'current_xp': obj.experience_points,
            'level_start_xp': current_level_xp,
            'next_level_xp': next_level_xp,
            'progress_xp': progress_xp,
            'needed_xp': max(0, needed_xp),
            'progress_percentage': min(100, (progress_xp / 100) * 100)
        }
    
    def get_streak_info(self, obj):
        """Get streak information"""
        return {
            'current_streak': obj.daily_streak,
            'last_login': obj.last_login_date,
            'streak_status': 'active' if obj.daily_streak > 0 else 'broken'
        }
    
    def get_credit_history(self, obj):
        """Get recent credit transactions"""
        # This would typically fetch from a CreditTransaction model
        # For now, return basic info
        return {
            'current_balance': obj.credits,
            'total_earned': obj.credits + 100,  # Placeholder
            'total_spent': 100  # Placeholder
        }
    
    def get_achievements_summary(self, obj):
        """Get achievements summary"""
        # This would typically fetch from UserAchievement model
        # For now, return placeholder data
        return {
            'total_achievements': 0,
            'recent_count': 0,
            'points_from_achievements': 0
        }


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for references in other models
    
    Used when you need basic user info in other serializers
    """
    
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'avatar_url', 'level', 'user_rank'
        ]
        read_only_fields = [
            'id', 'username', 'first_name', 'last_name',
            'avatar_url', 'level', 'user_rank'
        ]
    
    def get_avatar_url(self, obj):
        """Get avatar URL or default"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer for user preferences only
    
    Lightweight serializer for preference updates
    """
    
    class Meta:
        model = User
        fields = [
            'theme_preference', 'language_preference',
            'ai_assistance_enabled', 'analytics_enabled'
        ]


class UserSearchSerializer(serializers.ModelSerializer):
    """
    Serializer for user search results
    
    Used in collaboration features and user lookup
    """
    
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'avatar_url', 'user_rank', 'level', 'is_premium'
        ]
        read_only_fields = [
            'id', 'username', 'first_name', 'last_name',
            'avatar_url', 'user_rank', 'level', 'is_premium'
        ]
    
    def get_avatar_url(self, obj):
        """Get avatar URL or default"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None