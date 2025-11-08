"""
MVP Auth API URLs - Clean professional endpoints for production use

Provides essential authentication functionality:
- User registration and login
- JWT token management  
- Profile management
- Password operations
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import mvp_views

app_name = 'mvp_auth'

urlpatterns = [
    # Core authentication
    path('register/', mvp_views.MVPUserRegistrationView.as_view(), name='register'),
    path('login/', mvp_views.MVPUserLoginView.as_view(), name='login'), 
    path('logout/', mvp_views.MVPUserLogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    
    # User validation
    path('check-username/', mvp_views.check_username_availability, name='check-username'),
    path('check-email/', mvp_views.check_email_availability, name='check-email'),
    
    # Profile management
    path('profile/', mvp_views.MVPUserProfileView.as_view(), name='profile'),
    path('change-password/', mvp_views.MVPPasswordChangeView.as_view(), name='change-password'),
]