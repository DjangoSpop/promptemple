from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
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
    Supports both web app and Chrome extension authentication
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, provider):
        """
        Get OAuth authorization URL
        
        Query Parameters:
        - provider: 'google' or 'github'
        - redirect_uri: (optional) Custom redirect URI for extension/webapp
        - client_type: (optional) 'extension' or 'web' to help with URI resolution
        """
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

            # Determine redirect URI based on client type or explicit parameter
            from decouple import config as env_config
            from promptcraft.settings.production import is_valid_redirect_uri

            client_type = request.GET.get('client_type', 'web')  # 'web' or 'extension'
            explicit_redirect_uri = request.GET.get('redirect_uri')

            # Auto-detect extension client from redirect_uri (extension may not send client_type)
            if explicit_redirect_uri and 'chromiumapp.org' in explicit_redirect_uri:
                client_type = 'extension'
                logger.info(f"Auto-detected extension client from redirect_uri: {explicit_redirect_uri}")

            # If extension is requesting, use its chromiumapp.org redirect URI
            if client_type == 'extension':
                if explicit_redirect_uri:
                    # Use the provided extension redirect URI
                    redirect_uri = explicit_redirect_uri
                    logger.info(f"Extension auth initiated with redirect_uri: {redirect_uri}")
                else:
                    # Extension without explicit redirect URI - return error
                    return Response({
                        'error': 'Extension redirect_uri required',
                        'message': 'Chrome extension must provide ?redirect_uri=https://EXTENSION_ID.chromiumapp.org/ parameter'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Web app - use the frontend-provided redirect_uri if valid,
                # otherwise fall back to FRONTEND_URL. This avoids overriding
                # a valid URI that matches what's registered in Google/GitHub
                # OAuth console, preventing redirect_uri_mismatch errors.
                if explicit_redirect_uri and is_valid_redirect_uri(explicit_redirect_uri):
                    redirect_uri = explicit_redirect_uri
                    logger.info(f"Web auth: using frontend-provided redirect_uri: {redirect_uri}")
                else:
                    frontend_url = env_config('FRONTEND_URL', default='https://www.prompt-temple.com')
                    redirect_uri = f'{frontend_url}/auth/callback/{provider}'
                    if explicit_redirect_uri:
                        logger.info(f"Web auth: frontend redirect_uri '{explicit_redirect_uri}' invalid, using canonical '{redirect_uri}'")
                    else:
                        logger.info(f"Web auth: no redirect_uri provided, using canonical '{redirect_uri}'")
            
            # Validate redirect URI against whitelist
            if not is_valid_redirect_uri(redirect_uri):
                logger.warning(f"Invalid redirect_uri attempted: {redirect_uri} (client_type={client_type})")
                return Response({
                    'error': 'Invalid redirect_uri',
                    'message': f'The redirect_uri "{redirect_uri}" is not registered. '
                               f'For extensions, ensure the URI is registered in Google/GitHub OAuth console. '
                               f'For web, check FRONTEND_URL environment variable.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get authorization URL with validated redirect URI
            auth_url = oauth_handler.get_auth_url(redirect_uri, state)
            
            logger.info(f"Auth URL generated for {provider} (client_type={client_type}), redirect_uri={redirect_uri}")

            # Store state in session for verification (optional - frontend can handle this)
            request.session[f'{provider}_oauth_state'] = state
            request.session[f'{provider}_redirect_uri'] = redirect_uri  # Store for callback validation

            return Response({
                'auth_url': auth_url,
                'state': state,
                'redirect_uri': redirect_uri,
                'provider': provider,
                'client_type': client_type,
                'message': f'Redirect to {provider.title()} for authorization'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Social auth initiation failed for {provider}: {e}", exc_info=True)
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
            # Log incoming request data for debugging
            logger.info(f"Social auth callback received: provider={request.data.get('provider')}, has_code={bool(request.data.get('code'))}, has_state={bool(request.data.get('state'))}, redirect_uri={request.data.get('redirect_uri')}")
            
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
                    logger.warning(f"State mismatch for {provider}: expected={stored_state}, received={state}")
                    return Response({
                        'error': 'Invalid state parameter',
                        'message': 'Possible CSRF attack detected'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Get OAuth handler
            oauth_handler = get_oauth_handler(provider)

            # Get redirect URI - MUST match what was used in initiation
            from decouple import config as env_config
            from promptcraft.settings.production import is_valid_redirect_uri

            frontend_url = env_config('FRONTEND_URL', default='https://www.prompt-temple.com')

            # First try to get stored redirect_uri from session (set during initiation)
            redirect_uri = request.session.get(f'{provider}_redirect_uri')

            # If not in session, check request data (for stateless clients like extensions)
            if not redirect_uri:
                request_redirect_uri = request.data.get('redirect_uri')
                if request_redirect_uri and is_valid_redirect_uri(request_redirect_uri):
                    # Use the frontend-provided redirect_uri if it passes validation
                    redirect_uri = request_redirect_uri
                else:
                    # Fall back to canonical FRONTEND_URL
                    redirect_uri = f'{frontend_url}/auth/callback/{provider}'
            
            logger.info(f"Using redirect_uri for token exchange: {redirect_uri}")
            
            # Validate redirect URI
            if not is_valid_redirect_uri(redirect_uri):
                logger.error(f"Invalid redirect_uri in callback: {redirect_uri}")
                return Response({
                    'error': 'Invalid redirect_uri',
                    'message': f'The redirect_uri "{redirect_uri}" is not registered. '
                               f'Verify it matches the URI used during authentication initiation.',
                    'provider': provider,
                    'received_redirect_uri': redirect_uri
                }, status=status.HTTP_400_BAD_REQUEST)

            # Exchange code for access token
            try:
                token_data = oauth_handler.exchange_code_for_token(code, redirect_uri)
                logger.info(f"Successfully exchanged code for {provider} token")
            except ValidationError as ve:
                logger.error(f"Token exchange validation error for {provider}: {ve}")
                logger.error(f"Attempted redirect_uri: {redirect_uri}")
                return Response({
                    'error': 'OAuth token exchange failed',
                    'message': str(ve),
                    'provider': provider,
                    'redirect_uri_used': redirect_uri,
                    'help': f'Ensure the redirect_uri "{redirect_uri}" is registered in {provider.title()} OAuth Console'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            access_token = token_data['access_token']

            # Get user info from provider
            user_info = oauth_handler.get_user_info(access_token)

            # Create or update user
            user, is_new_user = oauth_handler.create_or_update_user(user_info)

            # Generate JWT tokens
            tokens = safe_jwt_token_generation(user)

            # Prepare response data with tokens at root level for easy frontend access
            response_data = {
                'message': 'Social authentication successful',
                'user': SocialUserProfileSerializer(user, context={'request': request}).data,
                'tokens': tokens,
                'access': tokens['access'],  # Add at root level for convenience
                'refresh': tokens['refresh'],  # Add at root level for convenience
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

            logger.info(f"Social auth successful for user {user.username} (id={user.id}), provider={provider}, is_new={is_new_user}")
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

        try:
            # Try to get configuration from settings first, fallback to environment
            from decouple import config as env_config
            
            # Check Google configuration
            google_client_id = None
            google_scopes = ['profile', 'email']
            
            if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS') and 'google' in settings.SOCIALACCOUNT_PROVIDERS:
                google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
                google_app = google_config.get('APP', {})
                google_client_id = google_app.get('client_id')
                google_scopes = google_config.get('SCOPE', google_scopes)
            else:
                google_client_id = env_config('GOOGLE_OAUTH2_CLIENT_ID', default='')
            
            if google_client_id:
                providers.append({
                    'name': 'google',
                    'display_name': 'Google',
                    'enabled': True,
                    'initiate_url': '/api/v2/auth/social/google/initiate/',
                    'callback_url': '/api/v2/auth/social/callback/',
                    'scopes': google_scopes
                })

            # Check GitHub configuration
            github_client_id = None
            github_scopes = ['user:email', 'read:user']
            
            if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS') and 'github' in settings.SOCIALACCOUNT_PROVIDERS:
                github_config = settings.SOCIALACCOUNT_PROVIDERS.get('github', {})
                github_app = github_config.get('APP', {})
                github_client_id = github_app.get('client_id')
                github_scopes = github_config.get('SCOPE', github_scopes)
            else:
                github_client_id = env_config('GITHUB_CLIENT_ID', default='')
            
            if github_client_id:
                providers.append({
                    'name': 'github',
                    'display_name': 'GitHub',
                    'enabled': True,
                    'initiate_url': '/api/v2/auth/social/github/initiate/',
                    'callback_url': '/api/v2/auth/social/callback/',
                    'scopes': github_scopes
                })

            # Get frontend URL from environment
            frontend_url = env_config('FRONTEND_URL', default='http://localhost:3000')
            
            return Response({
                'providers': providers,
                'callback_url': '/api/v2/auth/social/callback/',
                'frontend_callback_urls': {
                    'google': f'{frontend_url}/auth/callback/google',
                    'github': f'{frontend_url}/auth/callback/github'
                },
                'frontend_url': frontend_url
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Failed to get social auth providers: {e}")
            return Response({
                'error': 'Configuration error',
                'message': 'Social authentication is not properly configured',
                'providers': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        from decouple import config as env_config
        frontend_url = env_config('FRONTEND_URL', default='http://localhost:3000')
        redirect_uri = request.data.get('redirect_uri', f'{frontend_url}/auth/link/{provider}')

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