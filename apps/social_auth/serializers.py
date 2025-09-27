from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import uuid
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class SocialAuthSerializer(serializers.Serializer):
    """
    Serializer for social authentication callback
    """
    code = serializers.CharField(
        help_text="Authorization code from OAuth provider"
    )
    state = serializers.CharField(
        required=False,
        help_text="State parameter for CSRF protection"
    )
    provider = serializers.ChoiceField(
        choices=['google', 'github'],
        help_text="Social authentication provider"
    )


class SocialUserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for social user profile data
    """
    avatar_url = serializers.SerializerMethodField()
    social_avatar_url = serializers.URLField(read_only=True)
    provider_name = serializers.CharField(read_only=True)
    provider_id = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'avatar_url', 'social_avatar_url', 'bio',
            'provider_name', 'provider_id', 'date_joined', 'last_login',
            'credits', 'level', 'experience_points', 'daily_streak',
            'user_rank', 'is_premium', 'premium_expires_at',
            'theme_preference', 'language_preference',
            'ai_assistance_enabled', 'analytics_enabled',
            'templates_created', 'templates_completed', 'total_prompts_generated',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'credits', 'level',
            'experience_points', 'daily_streak', 'user_rank', 'is_premium',
            'premium_expires_at', 'templates_created', 'templates_completed',
            'total_prompts_generated', 'created_at', 'updated_at',
            'provider_name', 'provider_id', 'social_avatar_url'
        ]

    def get_avatar_url(self, obj):
        """Get avatar URL - prefer uploaded avatar over social avatar"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        elif obj.social_avatar_url:
            return obj.social_avatar_url
        return None


class SocialLoginResponseSerializer(serializers.Serializer):
    """
    Serializer for social login response
    """
    message = serializers.CharField()
    user = SocialUserProfileSerializer()
    tokens = serializers.DictField()
    is_new_user = serializers.BooleanField()
    provider = serializers.CharField()
    daily_streak = serializers.IntegerField(required=False)


class GoogleUserInfoSerializer(serializers.Serializer):
    """
    Serializer for Google user info response
    """
    sub = serializers.CharField()  # Google user ID
    email = serializers.EmailField()
    given_name = serializers.CharField(required=False)
    family_name = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    picture = serializers.URLField(required=False)
    email_verified = serializers.BooleanField(required=False)


class GitHubUserInfoSerializer(serializers.Serializer):
    """
    Serializer for GitHub user info response
    """
    id = serializers.IntegerField()  # GitHub user ID
    login = serializers.CharField()  # GitHub username
    email = serializers.EmailField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    avatar_url = serializers.URLField(required=False)


class GitHubEmailSerializer(serializers.Serializer):
    """
    Serializer for GitHub email response
    """
    email = serializers.EmailField()
    primary = serializers.BooleanField()
    verified = serializers.BooleanField()