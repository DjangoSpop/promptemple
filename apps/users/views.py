from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.users.serializers import (
    UserRegistrationSerializer, UserLoginSerializer, 
    UserProfileSerializer, UserUpdateSerializer, PasswordChangeSerializer
)

User = get_user_model()
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
        """
        Check if username is available for registration
    
        Query params:
        - username: The username to check
    
        Returns:
        - available: Boolean indicating if username is available
        """
        username = request.GET.get('username')
    
        if not username:
            return Response({
            'error': 'Username parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if username already exists (case-insensitive)
        is_available = not User.objects.filter(username__iexact=username).exists()
    
        return Response({
        'available': is_available,
        'username': username
    }, status=status.HTTP_200_OK)
# Create placeholder services to avoid import errors for now

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """
    Check if email is available for registration

    Query params:
    - email: The email to check

    Returns:
    - available: Boolean indicating if email is available
    """
    email = request.GET.get('email')

    if not email:
        return Response({
            'error': 'Email parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    # Check if email already exists (case-insensitive)
    is_available = not User.objects.filter(email__iexact=email).exists()

    return Response({
        'available': is_available,
        'email': email
    }, status=status.HTTP_200_OK)
class GamificationService:
    @staticmethod
    def award_credits(user, amount, reason, transaction_type):
        # Placeholder implementation
        user.credits += amount
        user.save()
        return amount
    
    @staticmethod
    def update_daily_streak(user):
        # Placeholder implementation
        today = timezone.now().date()
        if user.last_login_date != today:
            if user.last_login_date == today - timezone.timedelta(days=1):
                user.daily_streak += 1
            else:
                user.daily_streak = 1
            user.last_login_date = today
            user.save()
        return user.daily_streak

class AnalyticsService:
    @staticmethod
    def track_event(user, event_name, category, properties=None):
        # Placeholder implementation
        print(f"Analytics: {event_name} for user {user.username}")
        return True

User = get_user_model()


class UserRegistrationView(CreateAPIView):
    """
    User registration endpoint
    
    Creates new user account and returns JWT tokens
    """
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """Handle user registration"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Track registration analytics
        AnalyticsService.track_event(
            user=user,
            event_name='user_registered',
            category='authentication',
            properties={
                'registration_method': 'email',
                'user_id': str(user.id)
            }
        )
        
        # Award welcome bonus
        GamificationService.award_credits(
            user=user,
            amount=50,
            reason="Welcome bonus for new user!",
            transaction_type='bonus'
        )
        
        return Response({
            'message': 'User registered successfully',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    """
    Custom login view with additional features
    
    Supports:
    - Email or username login
    - Daily streak tracking
    - Login analytics
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Handle user login"""
        # First validate credentials
        login_serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        login_serializer.is_valid(raise_exception=True)
        
        user = login_serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Update daily streak
        streak = GamificationService.update_daily_streak(user)
        
        # Track login analytics
        AnalyticsService.track_event(
            user=user,
            event_name='user_login',
            category='authentication',
            properties={
                'login_method': 'password',
                'daily_streak': streak,
                'user_id': str(user.id)
            }
        )
        
        return Response({
            'message': 'Login successful',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'daily_streak': streak
        }, status=status.HTTP_200_OK)


class UserProfileView(RetrieveUpdateAPIView):
    """
    User profile view for retrieving and updating profile
    """
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get current user profile"""
        return self.request.user

    def get_serializer_class(self):
        """Use different serializer for updates"""
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserProfileSerializer
    
   

    def update(self, request, *args, **kwargs):
        """Handle profile updates"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Save updated profile
        user = serializer.save()
        
        # Track profile update
        AnalyticsService.track_event(
            user=user,
            event_name='profile_updated',
            category='user',
            properties={
                'fields_updated': list(request.data.keys()),
                'user_id': str(user.id)
            }
        )
        
        # Return full profile data
        profile_serializer = UserProfileSerializer(user)
        return Response(profile_serializer.data)


class PasswordChangeView(APIView):
    """
    Change user password
    """
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Handle password change"""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Update password
        user = serializer.save()
        
        # Track password change
        AnalyticsService.track_event(
            user=user,
            event_name='password_changed',
            category='security',
            properties={'user_id': str(user.id)}
        )
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout user by blacklisting refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Track logout
        AnalyticsService.track_event(
            user=request.user,
            event_name='user_logout',
            category='authentication',
            properties={'user_id': str(request.user.id)}
        )
        
        return Response({
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats_view(request):
    """
    Get user statistics and gamification data
    """
    user = request.user
    
    # Calculate level based on experience
    user.calculate_level()
    
    # Get basic stats (without UserAchievement for now)
    stats_data = {
        'user_id': str(user.id),
        'credits': user.credits,
        'level': user.level,
        'experience_points': user.experience_points,
        'daily_streak': user.daily_streak,
        'user_rank': user.user_rank,
        'templates_created': user.templates_created,
        'templates_completed': user.templates_completed,
        'total_prompts_generated': user.total_prompts_generated,
        'completion_rate': user.completion_rate,
        'recent_achievements': []  # Placeholder until achievements are implemented
    }
    
    return Response(stats_data)


# Add missing view classes for the URLs
class UserLogoutView(APIView):
    """
    Logout user endpoint
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        return logout_view(request)


class UserProfileUpdateView(RetrieveUpdateAPIView):
    """
    Update user profile endpoint
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


# Import TokenRefreshView from simplejwt
from rest_framework_simplejwt.views import TokenRefreshView