import requests
import secrets
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework.exceptions import ValidationError
from .serializers import GoogleUserInfoSerializer, GitHubUserInfoSerializer, GitHubEmailSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseOAuthHandler:
    """
    Base class for OAuth handlers
    """

    def __init__(self):
        self.provider_name = None
        self.client_id = None
        self.client_secret = None
        self.token_url = None
        self.user_info_url = None

    def generate_state(self):
        """Generate secure state parameter for CSRF protection"""
        return secrets.token_urlsafe(32)

    def exchange_code_for_token(self, code, redirect_uri=None):
        """Exchange authorization code for access token"""
        raise NotImplementedError("Subclasses must implement this method")

    def get_user_info(self, access_token):
        """Get user information from provider"""
        raise NotImplementedError("Subclasses must implement this method")

    def create_or_update_user(self, user_data):
        """Create or update user based on social provider data"""
        raise NotImplementedError("Subclasses must implement this method")


class GoogleOAuthHandler(BaseOAuthHandler):
    """
    Google OAuth2 handler
    """

    def __init__(self):
        super().__init__()
        self.provider_name = 'google'
        
        # Try to get from settings.SOCIALACCOUNT_PROVIDERS first, fallback to environment variables
        try:
            if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS') and 'google' in settings.SOCIALACCOUNT_PROVIDERS:
                google_config = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']
                self.client_id = google_config['client_id']
                self.client_secret = google_config['secret']
            else:
                raise AttributeError("SOCIALACCOUNT_PROVIDERS not configured")
        except (AttributeError, KeyError):
            # Fallback to environment variables
            from decouple import config
            self.client_id = config('GOOGLE_OAUTH2_CLIENT_ID', default='')
            self.client_secret = config('GOOGLE_OAUTH2_CLIENT_SECRET', default='')
        
        if not self.client_id or not self.client_secret:
            raise ValidationError("Google OAuth credentials not configured")
        
        self.token_url = 'https://oauth2.googleapis.com/token'
        self.user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'

    def get_auth_url(self, redirect_uri, state):
        """Get Google OAuth authorization URL"""
        scope = 'openid email profile'
        return (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={self.client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}&"
            f"response_type=code&"
            f"state={state}&"
            f"access_type=online"
        )

    def exchange_code_for_token(self, code, redirect_uri=None):
        """Exchange authorization code for access token"""
        try:
            # Use provided redirect_uri or fall back to default
            if not redirect_uri:
                redirect_uri = 'http://localhost:3000/auth/callback/google'
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri,
            }

            logger.info(f"Exchanging Google code for token with redirect_uri: {redirect_uri}")
            response = requests.post(self.token_url, data=data, timeout=10)
            response.raise_for_status()

            token_data = response.json()
            if 'access_token' not in token_data:
                raise ValidationError("Failed to obtain access token from Google")

            return token_data

        except requests.RequestException as e:
            logger.error(f"Google token exchange failed: {e}")
            logger.error(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
            logger.error(f"Response body: {getattr(e.response, 'text', 'N/A')}")
            logger.error(f"Request data used: client_id={self.client_id[:10]}..., redirect_uri={redirect_uri}, code_length={len(code)}")
            raise ValidationError(f"Failed to exchange code for token: {str(e)}")

    def get_user_info(self, access_token):
        """Get user information from Google"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(self.user_info_url, headers=headers, timeout=10)
            response.raise_for_status()

            user_data = response.json()
            serializer = GoogleUserInfoSerializer(data=user_data)
            serializer.is_valid(raise_exception=True)

            return serializer.validated_data

        except requests.RequestException as e:
            logger.error(f"Google user info fetch failed: {e}")
            raise ValidationError("Failed to fetch user information from Google")

    def create_or_update_user(self, user_data):
        """Create or update user based on Google data"""
        try:
            email = user_data['email']
            google_id = user_data['sub']

            # Try to find existing user by email or Google ID
            user = None
            is_new_user = False

            # First check if user exists with this Google ID
            try:
                user = User.objects.get(provider_id=google_id, provider_name='google')
            except User.DoesNotExist:
                # Check if user exists with this email
                try:
                    user = User.objects.get(email=email)
                    # Link the Google account to existing user
                    user.provider_id = google_id
                    user.provider_name = 'google'
                    if user_data.get('picture'):
                        user.social_avatar_url = user_data['picture']
                except User.DoesNotExist:
                    # Create new user
                    is_new_user = True
                    username = self._generate_username(email, user_data.get('given_name', ''))

                    user = User.objects.create(
                        username=username,
                        email=email,
                        first_name=user_data.get('given_name', ''),
                        last_name=user_data.get('family_name', ''),
                        provider_id=google_id,
                        provider_name='google',
                        social_avatar_url=user_data.get('picture', ''),
                        password=make_password(None),  # Unusable password
                        is_active=True,
                    )

            # Update user info from Google (for existing users)
            if not is_new_user:
                if user_data.get('given_name') and not user.first_name:
                    user.first_name = user_data['given_name']
                if user_data.get('family_name') and not user.last_name:
                    user.last_name = user_data['family_name']
                if user_data.get('picture'):
                    user.social_avatar_url = user_data['picture']

            user.save()
            return user, is_new_user

        except Exception as e:
            logger.error(f"User creation/update failed for Google: {e}")
            raise ValidationError("Failed to create or update user")

    def _generate_username(self, email, first_name):
        """Generate unique username"""
        base_username = first_name.lower() if first_name else email.split('@')[0]
        base_username = ''.join(c for c in base_username if c.isalnum() or c in '_-')

        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username


class GitHubOAuthHandler(BaseOAuthHandler):
    """
    GitHub OAuth2 handler
    """

    def __init__(self):
        super().__init__()
        self.provider_name = 'github'
        
        # Try to get from settings.SOCIALACCOUNT_PROVIDERS first, fallback to environment variables
        try:
            if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS') and 'github' in settings.SOCIALACCOUNT_PROVIDERS:
                github_config = settings.SOCIALACCOUNT_PROVIDERS['github']['APP']
                self.client_id = github_config['client_id']
                self.client_secret = github_config['secret']
            else:
                raise AttributeError("SOCIALACCOUNT_PROVIDERS not configured")
        except (AttributeError, KeyError):
            # Fallback to environment variables
            from decouple import config
            self.client_id = config('GITHUB_CLIENT_ID', default='')
            self.client_secret = config('GITHUB_CLIENT_SECRET', default='')
        
        if not self.client_id or not self.client_secret:
            raise ValidationError("GitHub OAuth credentials not configured")
        
        self.token_url = 'https://github.com/login/oauth/access_token'
        self.user_info_url = 'https://api.github.com/user'
        self.user_emails_url = 'https://api.github.com/user/emails'

    def get_auth_url(self, redirect_uri, state):
        """Get GitHub OAuth authorization URL"""
        scope = 'user:email'
        return (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={self.client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}&"
            f"state={state}"
        )

    def exchange_code_for_token(self, code, redirect_uri=None):
        """Exchange authorization code for access token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
            }

            headers = {'Accept': 'application/json'}
            response = requests.post(self.token_url, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            token_data = response.json()
            if 'access_token' not in token_data:
                raise ValidationError("Failed to obtain access token from GitHub")

            return token_data

        except requests.RequestException as e:
            logger.error(f"GitHub token exchange failed: {e}")
            raise ValidationError("Failed to exchange code for token")

    def get_user_info(self, access_token):
        """Get user information from GitHub"""
        try:
            headers = {'Authorization': f'token {access_token}'}

            # Get user info
            response = requests.get(self.user_info_url, headers=headers, timeout=10)
            response.raise_for_status()
            user_data = response.json()

            # Get user emails if email is not public
            if not user_data.get('email'):
                email_response = requests.get(self.user_emails_url, headers=headers, timeout=10)
                email_response.raise_for_status()
                emails = email_response.json()

                # Find primary or verified email
                primary_email = None
                for email_info in emails:
                    email_serializer = GitHubEmailSerializer(data=email_info)
                    if email_serializer.is_valid():
                        if email_serializer.validated_data['primary']:
                            primary_email = email_serializer.validated_data['email']
                            break
                        elif email_serializer.validated_data['verified'] and not primary_email:
                            primary_email = email_serializer.validated_data['email']

                if primary_email:
                    user_data['email'] = primary_email

            # Validate user data
            serializer = GitHubUserInfoSerializer(data=user_data)
            serializer.is_valid(raise_exception=True)

            return serializer.validated_data

        except requests.RequestException as e:
            logger.error(f"GitHub user info fetch failed: {e}")
            raise ValidationError("Failed to fetch user information from GitHub")

    def create_or_update_user(self, user_data):
        """Create or update user based on GitHub data"""
        try:
            email = user_data.get('email')
            github_id = str(user_data['id'])
            github_username = user_data['login']

            if not email:
                raise ValidationError("Email is required but not provided by GitHub")

            # Try to find existing user by email or GitHub ID
            user = None
            is_new_user = False

            # First check if user exists with this GitHub ID
            try:
                user = User.objects.get(provider_id=github_id, provider_name='github')
            except User.DoesNotExist:
                # Check if user exists with this email
                try:
                    user = User.objects.get(email=email)
                    # Link the GitHub account to existing user
                    user.provider_id = github_id
                    user.provider_name = 'github'
                    if user_data.get('avatar_url'):
                        user.social_avatar_url = user_data['avatar_url']
                except User.DoesNotExist:
                    # Create new user
                    is_new_user = True
                    username = self._generate_username(github_username, email)

                    # Parse name if available
                    full_name = user_data.get('name', '')
                    first_name, last_name = self._parse_name(full_name)

                    user = User.objects.create(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        provider_id=github_id,
                        provider_name='github',
                        social_avatar_url=user_data.get('avatar_url', ''),
                        password=make_password(None),  # Unusable password
                        is_active=True,
                    )

            # Update user info from GitHub (for existing users)
            if not is_new_user:
                if user_data.get('name') and not (user.first_name and user.last_name):
                    first_name, last_name = self._parse_name(user_data['name'])
                    if not user.first_name:
                        user.first_name = first_name
                    if not user.last_name:
                        user.last_name = last_name
                if user_data.get('avatar_url'):
                    user.social_avatar_url = user_data['avatar_url']

            user.save()
            return user, is_new_user

        except Exception as e:
            logger.error(f"User creation/update failed for GitHub: {e}")
            raise ValidationError("Failed to create or update user")

    def _generate_username(self, github_username, email):
        """Generate unique username"""
        # Try GitHub username first
        base_username = github_username.lower()
        base_username = ''.join(c for c in base_username if c.isalnum() or c in '_-')

        if not base_username:
            base_username = email.split('@')[0]
            base_username = ''.join(c for c in base_username if c.isalnum() or c in '_-')

        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

    def _parse_name(self, full_name):
        """Parse full name into first and last name"""
        if not full_name:
            return '', ''

        name_parts = full_name.strip().split()
        if len(name_parts) == 1:
            return name_parts[0], ''
        elif len(name_parts) >= 2:
            return name_parts[0], ' '.join(name_parts[1:])

        return '', ''


def get_oauth_handler(provider):
    """Factory function to get OAuth handler"""
    handlers = {
        'google': GoogleOAuthHandler,
        'github': GitHubOAuthHandler,
    }

    if provider not in handlers:
        raise ValidationError(f"Unsupported OAuth provider: {provider}")

    return handlers[provider]()