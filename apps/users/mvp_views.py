"""
MVP User Views - Professional clean authentication API

Simplified, secure authentication endpoints for production MVP.
Focuses on essential functionality with proper error handling.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, 
    UserProfileSerializer, UserUpdateSerializer, PasswordChangeSerializer
)

logger = logging.getLogger(__name__)
User = get_user_model()


def safe_jwt_token_generation(user):
    """Generate JWT tokens with error handling"""
    try:
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    except Exception as e:
        logger.error(f"JWT token generation failed: {e}")
        raise Exception(f"Authentication token generation failed")


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """Check if username is available for registration"""
    username = request.GET.get('username')
    
    if not username:
        return Response({
            'error': 'Username parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(username) < 3:
        return Response({
            'available': False,
            'error': 'Username must be at least 3 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    is_available = not User.objects.filter(username__iexact=username).exists()
    
    return Response({
        'available': is_available,
        'username': username
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """Check if email is available for registration"""
    email = request.GET.get('email')
    
    if not email:
        return Response({
            'error': 'Email parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    is_available = not User.objects.filter(email__iexact=email).exists()
    
    return Response({
        'available': is_available,
        'email': email
    })


class MVPUserRegistrationView(CreateAPIView):
    """
    MVP User Registration
    
    Handles user registration with JWT token generation.
    Clean, minimal implementation for production.
    """
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """Handle user registration"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create user
            user = serializer.save()
            
            # Generate JWT tokens
            tokens = safe_jwt_token_generation(user)
            
            return Response({
                'message': 'Registration successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return Response({
                'error': 'Registration failed. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)


class MVPUserLoginView(APIView):
    """
    MVP User Login
    
    Handles user authentication with email or username.
    Returns JWT tokens on successful authentication.
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle user login"""
        try:
            serializer = UserLoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            user = serializer.validated_data['user']
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate JWT tokens
            tokens = safe_jwt_token_generation(user)
            
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'tokens': tokens
            })
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class MVPUserLogoutView(APIView):
    """
    MVP User Logout
    
    Blacklists the refresh token to log out the user.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Handle user logout"""
        try:
            refresh_token = request.data.get('refresh')
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout successful'
            })
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return Response({
                'error': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)


class MVPUserProfileView(RetrieveUpdateAPIView):
    """
    MVP User Profile
    
    Allows users to view and update their profile information.
    """
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return current user"""
        return self.request.user
    
    def get_serializer_class(self):
        """Use appropriate serializer for the action"""
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserProfileSerializer
    
    def update(self, request, *args, **kwargs):
        """Handle profile update"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            user = serializer.save()
            
            # Return updated profile
            profile_serializer = UserProfileSerializer(user)
            return Response({
                'message': 'Profile updated successfully',
                'user': profile_serializer.data
            })
            
        except Exception as e:
            logger.error(f"Profile update failed: {e}")
            return Response({
                'error': 'Profile update failed'
            }, status=status.HTTP_400_BAD_REQUEST)


class MVPPasswordChangeView(APIView):
    """
    MVP Password Change
    
    Allows authenticated users to change their password.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Handle password change"""
        try:
            serializer = PasswordChangeSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            
            # Update password
            serializer.save()
            
            return Response({
                'message': 'Password changed successfully'
            })
            
        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return Response({
                'error': 'Password change failed'
            }, status=status.HTTP_400_BAD_REQUEST)