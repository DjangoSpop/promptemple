import requests
import secrets
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import models
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
        # Use v3 endpoint which properly returns 'sub' field
        self.user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'

    def get_auth_url(self, redirect_uri, state):
        """Get Google OAuth authorization URL"""
        from urllib.parse import quote, urlencode
        # Include openid scope to ensure we get the 'sub' field
        scope = 'openid email profile'
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'response_type': 'code',
            'state': state,
            'access_type': 'online',
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    def exchange_code_for_token(self, code, redirect_uri=None):
        """Exchange authorization code for access token"""
        try:
            # Use provided redirect_uri or fall back to environment-based default
            if not redirect_uri:
                from decouple import config
                frontend_url = config('FRONTEND_URL', default='http://localhost:3000')
                redirect_uri = f'{frontend_url}/auth/callback/google'
            
            # Validate the redirect_uri format matches what was used in authorization
            if not redirect_uri:
                raise ValidationError("redirect_uri is required for token exchange")
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri,
            }

            logger.info(f"Exchanging Google code for token with redirect_uri: {redirect_uri}")
            logger.debug(f"Token exchange request data: client_id={self.client_id[:20]}..., code_length={len(code)}, redirect_uri={redirect_uri}")
            
            response = requests.post(self.token_url, data=data, timeout=10)
            
            # Log response for debugging
            logger.debug(f"Google token exchange response status: {response.status_code}")
            
            if response.status_code != 200:
                error_body = response.text
                logger.error(f"Google OAuth error response: {error_body}")
                logger.error(f"Used redirect_uri: {redirect_uri}")
                logger.error(f"Client ID (first 20 chars): {self.client_id[:20]}...")
                
                # Parse error message if available
                try:
                    error_data = response.json()
                    error_desc = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                    
                    # Check if it's a redirect_uri_mismatch error (common with extensions)
                    if 'redirect_uri_mismatch' in error_desc.lower() or error_desc == 'redirect_uri_mismatch':
                        raise ValidationError(
                            f"OAuth redirect_uri mismatch. The redirect_uri '{redirect_uri}' "
                            f"does not match one registered in Google Console. "
                            f"For Chrome extensions, ensure the extension ID's chromiumapp.org URI is registered. "
                            f"For web apps, ensure {redirect_uri} is registered in the OAuth app settings."
                        )
                    else:
                        raise ValidationError(
                            f"Google OAuth failed: {error_desc}. "
                            f"Ensure the redirect_uri '{redirect_uri}' is registered in your Google OAuth Console."
                        )
                except ValidationError:
                    raise
                except:
                    raise ValidationError(
                        f"Google OAuth failed with status {response.status_code}. "
                        f"Verify that redirect_uri '{redirect_uri}' matches exactly what's registered in Google Console."
                    )
            
            response.raise_for_status()
            token_data = response.json()
            
            if 'access_token' not in token_data:
                logger.error(f"No access_token in response: {token_data}")
                raise ValidationError("Failed to obtain access token from Google")

            logger.info("Successfully obtained Google access token")
            return token_data

        except requests.RequestException as e:
            logger.error(f"Google token exchange failed: {e}")
            logger.error(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
            logger.error(f"Response body: {getattr(e.response, 'text', 'N/A')}")
            logger.error(f"Request data - client_id={self.client_id[:10]}..., redirect_uri={redirect_uri}, code_length={len(code)}")
            
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_msg = f"{e.response.status_code} {e.response.reason} for url: {e.response.url}"
            
            raise ValidationError(f"Failed to exchange code for token: {error_msg}")

    def get_user_info(self, access_token):
        """Get user information from Google"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            logger.info(f"Fetching user info from: {self.user_info_url}")
            response = requests.get(self.user_info_url, headers=headers, timeout=10)
            response.raise_for_status()

            user_data = response.json()
            logger.info(f"Google user info response: {user_data}")
            
            # Validate the response
            serializer = GoogleUserInfoSerializer(data=user_data)
            if not serializer.is_valid():
                logger.error(f"Google user info validation failed: {serializer.errors}")
                logger.error(f"Received data: {user_data}")
            serializer.is_valid(raise_exception=True)

            return serializer.validated_data

        except requests.RequestException as e:
            logger.error(f"Google user info fetch failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
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
            user = User.objects.filter(provider_id=google_id, provider_name='google').first()
            
            if not user:
                # Check if user exists with this email (prioritize Google-linked accounts)
                user = User.objects.filter(email=email).order_by(
                    # Prioritize existing Google users, then any user
                    models.Case(
                        models.When(provider_name='google', then=0),
                        default=1
                    )
                ).first()
                
                if user:
                    # Link the Google account to existing user
                    logger.info(f"Linking Google account to existing user: {user.username}")
                    user.provider_id = google_id
                    user.provider_name = 'google'
                    if user_data.get('picture'):
                        user.social_avatar_url = user_data['picture']
                else:
                    # Create new user
                    is_new_user = True
                    username = self._generate_username(email, user_data.get('given_name', ''))
                    logger.info(f"Creating new user with username: {username}")

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
            # Log full stack trace for debugging
            logger.exception(f"User creation/update failed for Google: {e}")
            # Propagate the original exception message to help frontend debugging
            raise ValidationError(f"Failed to create or update user: {str(e)}")

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
            
            # GitHub doesn't strictly require redirect_uri in token exchange,
            # but include it for consistency if provided
            if redirect_uri:
                data['redirect_uri'] = redirect_uri

            headers = {'Accept': 'application/json'}
            logger.info(f"Exchanging GitHub code for token{' with redirect_uri: ' + redirect_uri if redirect_uri else ''}")
            
            response = requests.post(self.token_url, data=data, headers=headers, timeout=10)
            
            if response.status_code != 200:
                error_body = response.text
                logger.error(f"GitHub OAuth error response: {error_body}")
                try:
                    error_data = response.json()
                    error_desc = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                    raise ValidationError(f"GitHub OAuth failed: {error_desc}")
                except:
                    raise ValidationError(f"GitHub OAuth failed with status {response.status_code}")
            
            response.raise_for_status()
            token_data = response.json()
            
            if 'access_token' not in token_data:
                logger.error(f"No access_token in GitHub response: {token_data}")
                raise ValidationError("Failed to obtain access token from GitHub")

            logger.info("Successfully obtained GitHub access token")
            return token_data

        except requests.RequestException as e:
            logger.error(f"GitHub token exchange failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            raise ValidationError(f"Failed to exchange code for token: {str(e)}")

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
            user = User.objects.filter(provider_id=github_id, provider_name='github').first()
            
            if not user:
                # Check if user exists with this email (prioritize GitHub-linked accounts)
                user = User.objects.filter(email=email).order_by(
                    models.Case(
                        models.When(provider_name='github', then=0),
                        default=1
                    )
                ).first()
                
                if user:
                    # Link the GitHub account to existing user
                    logger.info(f"Linking GitHub account to existing user: {user.username}")
                    user.provider_id = github_id
                    user.provider_name = 'github'
                    if user_data.get('avatar_url'):
                        user.social_avatar_url = user_data['avatar_url']
                else:
                    # Create new user
                    is_new_user = True
                    username = self._generate_username(github_username, email)
                    logger.info(f"Creating new user with username: {username}")

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
            # Log full stack trace for debugging
            logger.exception(f"User creation/update failed for GitHub: {e}")
            # Propagate the original exception message to help frontend debugging
            raise ValidationError(f"Failed to create or update user: {str(e)}")

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