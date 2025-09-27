from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class SocialAuthException(Exception):
    """Base exception for social authentication errors"""
    pass


class OAuthProviderError(SocialAuthException):
    """Error from OAuth provider"""
    pass


class TokenExchangeError(OAuthProviderError):
    """Error during token exchange"""
    pass


class UserInfoError(OAuthProviderError):
    """Error fetching user info from provider"""
    pass


class UserCreationError(SocialAuthException):
    """Error creating or updating user"""
    pass


class StateValidationError(SocialAuthException):
    """Invalid state parameter"""
    pass


def social_auth_exception_handler(exc, context):
    """
    Custom exception handler for social authentication
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Add custom handling for social auth exceptions
    if isinstance(exc, SocialAuthException):
        custom_response_data = {
            'error': 'Social authentication error',
            'message': str(exc),
            'error_type': exc.__class__.__name__,
            'provider': getattr(exc, 'provider', None)
        }

        # Determine appropriate status code
        if isinstance(exc, StateValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, OAuthProviderError):
            status_code = status.HTTP_502_BAD_GATEWAY
        elif isinstance(exc, UserCreationError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        return Response(custom_response_data, status=status_code)

    # Return the default response for other exceptions
    return response


def handle_oauth_error(provider, error_type, error_message, details=None):
    """
    Standardized OAuth error handling
    """
    error_data = {
        'error': f'{provider.title()} authentication failed',
        'error_type': error_type,
        'message': error_message,
        'provider': provider,
    }

    if details:
        error_data['details'] = details

    logger.error(f"OAuth error for {provider}: {error_type} - {error_message}")

    return error_data


def handle_user_creation_error(provider, user_data, error):
    """
    Handle user creation/update errors
    """
    error_data = {
        'error': 'Failed to create or update user',
        'error_type': 'UserCreationError',
        'message': str(error),
        'provider': provider,
        'user_email': user_data.get('email', 'Unknown')
    }

    logger.error(f"User creation error for {provider}: {error}")

    return error_data