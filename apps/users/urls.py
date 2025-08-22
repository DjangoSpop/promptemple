from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Create router for ViewSets
router = DefaultRouter()

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.UserLogoutView.as_view(), name='user-logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('check-username/', views.check_username_availability, name='check-username'),
        path( 'auth/check-email/', views.check_email_availability, name='check-email'),
    # User profile endpoints
    
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', views.UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('change-password/', views.PasswordChangeView.as_view(), name='password-change'),
    path('stats/', views.user_stats_view, name='user-stats'),
    
    # Include router URLs
    path('', include(router.urls)),
]