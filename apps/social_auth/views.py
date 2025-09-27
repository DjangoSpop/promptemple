from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from .oauth_handlers import get_oauth_handler
from .serializers import (
    SocialAuthSerializer,
    SocialLoginResponseSerializer,
    SocialUserProfileSerializer
)
from apps.users.views import safe_jwt_token_generation, GamificationService, AnalyticsService

User = get_user_model()
logger = logging.getLogger(__name__)


class SocialAuthInitiateView(APIView):
    """
    Initiate social authentication flow

    Returns the OAuth provider's authorization URL for the frontend to redirect to
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, provider):
        """Get OAuth authorization URL"""
        try:
            # Validate provider
            if provider not in ['google', 'github']:
                return Response({
                    'error': 'Unsupported provider',
                    'message': f'Provider "{provider}" is not supported'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get OAuth handler
            oauth_handler = get_oauth_handler(provider)

            # Generate state for CSRF protection
            state = oauth_handler.generate_state()

            # Get redirect URI from query params or use default
            redirect_uri = request.GET.get('redirect_uri', f'http://localhost:3000/auth/callback/{provider}')

            # Get authorization URL
            auth_url = oauth_handler.get_auth_url(redirect_uri, state)

            # Store state in session for verification (optional - frontend can handle this)
            request.session[f'{provider}_oauth_state'] = state

            return Response({
                'auth_url': auth_url,
                'state': state,
                'provider': provider,
                'message': f'Redirect user to {provider.title()} for authorization'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Social auth initiation failed for {provider}: {e}")
            return Response({
                'error': 'Failed to initiate authentication',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SocialAuthCallbackView(APIView):
    """
    Handle OAuth callback and complete social authentication

    Processes the authorization code from the OAuth provider and returns JWT tokens
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle OAuth callback"""
        try:
            # Validate request data
            serializer = SocialAuthSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            code = serializer.validated_data['code']
            provider = serializer.validated_data['provider']
            state = serializer.validated_data.get('state')

            # Optional: Verify state parameter
            if state:
                stored_state = request.session.get(f'{provider}_oauth_state')
                if stored_state and stored_state != state:
                    return Response({
                        'error': 'Invalid state parameter',
                        'message': 'Possible CSRF attack detected'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Get OAuth handler
            oauth_handler = get_oauth_handler(provider)

            # Get redirect URI from request
            redirect_uri = request.data.get('redirect_uri', f'http://localhost:3000/auth/callback/{provider}')

            # Exchange code for access token
            token_data = oauth_handler.exchange_code_for_token(code, redirect_uri)
            access_token = token_data['access_token']

            # Get user info from provider
            user_info = oauth_handler.get_user_info(access_token)

            # Create or update user
            user, is_new_user = oauth_handler.create_or_update_user(user_info)

            # Generate JWT tokens
            tokens = safe_jwt_token_generation(user)

            # Prepare response data
            response_data = {
                'message': 'Social authentication successful',
                'user': SocialUserProfileSerializer(user, context={'request': request}).data,
                'tokens': tokens,
                'is_new_user': is_new_user,
                'provider': provider
            }

            # Update daily streak (non-blocking)
            try:
                streak = GamificationService.update_daily_streak(user)
                response_data['daily_streak'] = streak
            except Exception as e:
                logger.warning(f"Daily streak update failed for user {user.id}: {e}")
                response_data['daily_streak'] = 0

            # Track authentication analytics (non-blocking)
            try:
                AnalyticsService.track_event(
                    user=user,
                    event_name='social_authentication',
                    category='authentication',
                    properties={
                        'provider': provider,
                        'is_new_user': is_new_user,
                        'user_id': str(user.id),
                        'daily_streak': response_data.get('daily_streak', 0)
                    }
                )
            except Exception as e:
                logger.warning(f"Analytics tracking failed for user {user.id}: {e}")

            # Award welcome bonus for new users (non-blocking)
            if is_new_user:
                try:
                    GamificationService.award_credits(
                        user=user,
                        amount=50,
                        reason=f"Welcome bonus for {provider.title()} signup!",
                        transaction_type='bonus'
                    )
                except Exception as e:
                    logger.warning(f"Welcome bonus failed for user {user.id}: {e}")

            # Clean up session state
            if f'{provider}_oauth_state' in request.session:
                del request.session[f'{provider}_oauth_state']

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Social auth callback failed: {e}")
            return Response({
                'error': 'Social authentication failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SocialAuthProviderInfoView(APIView):
    """
    Get information about available social authentication providers
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Get provider information"""
        providers = []

        # Check Google configuration
        google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        google_app = google_config.get('APP', {})
        if google_app.get('client_id'):
            providers.append({
                'name': 'google',
                'display_name': 'Google',
                'enabled': True,
                'initiate_url': '/api/v2/auth/social/google/initiate/',
                'callback_url': '/api/v2/auth/social/callback/',
                'scopes': google_config.get('SCOPE', ['profile', 'email'])
            })

        # Check GitHub configuration
        github_config = settings.SOCIALACCOUNT_PROVIDERS.get('github', {})
        github_app = github_config.get('APP', {})
        if github_app.get('client_id'):
            providers.append({
                'name': 'github',
                'display_name': 'GitHub',
                'enabled': True,
                'initiate_url': '/api/v2/auth/social/github/initiate/',
                'callback_url': '/api/v2/auth/social/callback/',
                'scopes': github_config.get('SCOPE', ['user:email', 'read:user'])
            })

        return Response({
            'providers': providers,
            'callback_url': '/api/v2/auth/social/callback/',
            'frontend_callback_urls': {
                'google': 'http://localhost:3000/auth/callback/google',
                'github': 'http://localhost:3000/auth/callback/github'
            }
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unlink_social_account(request):
    """
    Unlink social account from user
    """
    try:
        user = request.user

        # Check if user has a password set (not a social-only account)
        if not user.has_usable_password():
            return Response({
                'error': 'Cannot unlink social account',
                'message': 'You must set a password before unlinking your social account'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Clear social authentication fields
        provider = user.provider_name
        user.provider_id = None
        user.provider_name = None
        user.social_avatar_url = None
        user.save()

        # Track unlinking event
        try:
            AnalyticsService.track_event(
                user=user,
                event_name='social_account_unlinked',
                category='authentication',
                properties={
                    'provider': provider,
                    'user_id': str(user.id)
                }
            )
        except Exception as e:
            logger.warning(f"Analytics tracking failed for user {user.id}: {e}")

        return Response({
            'message': f'{provider.title()} account unlinked successfully',
            'user': SocialUserProfileSerializer(user, context={'request': request}).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Social account unlinking failed: {e}")
        return Response({
            'error': 'Failed to unlink social account',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def link_social_account(request):
    """
    Link social account to existing user

    This endpoint allows users to link additional social providers to their account
    """
    try:
        # Validate request data
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        provider = serializer.validated_data['provider']
        user = request.user

        # Check if user already has a social account linked
        if user.provider_name and user.provider_name != provider:
            return Response({
                'error': 'Social account already linked',
                'message': f'User already has {user.provider_name.title()} account linked'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get OAuth handler
        oauth_handler = get_oauth_handler(provider)

        # Get redirect URI from request
        redirect_uri = request.data.get('redirect_uri', f'http://localhost:3000/auth/link/{provider}')

        # Exchange code for access token
        token_data = oauth_handler.exchange_code_for_token(code, redirect_uri)
        access_token = token_data['access_token']

        # Get user info from provider
        user_info = oauth_handler.get_user_info(access_token)

        # Check if this social account is already linked to another user
        if provider == 'google':
            provider_id = user_info['sub']
        elif provider == 'github':
            provider_id = str(user_info['id'])

        existing_user = User.objects.filter(
            provider_id=provider_id,
            provider_name=provider
        ).exclude(id=user.id).first()

        if existing_user:
            return Response({
                'error': 'Social account already linked',
                'message': f'This {provider.title()} account is already linked to another user'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Link the social account
        user.provider_id = provider_id
        user.provider_name = provider
        if user_info.get('picture' if provider == 'google' else 'avatar_url'):
            user.social_avatar_url = user_info.get('picture' if provider == 'google' else 'avatar_url')
        user.save()

        # Track linking event
        try:
            AnalyticsService.track_event(
                user=user,
                event_name='social_account_linked',
                category='authentication',
                properties={
                    'provider': provider,
                    'user_id': str(user.id)
                }
            )
        except Exception as e:
            logger.warning(f"Analytics tracking failed for user {user.id}: {e}")

        return Response({
            'message': f'{provider.title()} account linked successfully',
            'user': SocialUserProfileSerializer(user, context={'request': request}).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Social account linking failed: {e}")
        return Response({
            'error': 'Failed to link social account',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)