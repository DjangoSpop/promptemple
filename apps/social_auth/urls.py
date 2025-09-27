from django.urls import path
from . import views

urlpatterns = [
    # Social authentication endpoints
    path('social/providers/', views.SocialAuthProviderInfoView.as_view(), name='social-providers'),
    path('social/<str:provider>/initiate/', views.SocialAuthInitiateView.as_view(), name='social-initiate'),
    path('social/callback/', views.SocialAuthCallbackView.as_view(), name='social-callback'),

    # Account management
    path('social/unlink/', views.unlink_social_account, name='social-unlink'),
    path('social/link/', views.link_social_account, name='social-link'),
]