#!/usr/bin/env python
"""
Debug the exact authentication flow in the ChatCompletionsProxyView
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from apps.chat.views import ChatCompletionsProxyView

# Test token
test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3MzU2ODI4LCJpYXQiOjE3NTcyNzA0MjgsImp0aSI6ImJjMTUzY2Q0MmY3ZjRjMDI5MTRiOWYyMTNmYjA4NjYzIiwidXNlcl9pZCI6IjFhMDA1YTViLTdlYTgtNDMzZC04ZGRmLWU2NzY2ODlmMTFkZSJ9.6usiGIA65JxRzio8MltXe8nT1OWsWeukEa_qmYX8kAw"

def debug_view_authentication():
    """Debug authentication in the actual view"""
    print("=== View Authentication Debug ===")
    
    # Create a mock request
    factory = APIRequestFactory()
    request = factory.post(
        '/api/v2/chat/completions/',
        data={"messages": [{"role": "user", "content": "Hello"}]},
        format='json',
        HTTP_AUTHORIZATION=f'Bearer {test_token}'
    )
    
    print(f"Request Authorization Header: {request.META.get('HTTP_AUTHORIZATION', 'NOT SET')}")
    
    # Try to authenticate the request manually
    jwt_auth = JWTAuthentication()
    print("\n--- Manual JWT Authentication ---")
    try:
        user, validated_token = jwt_auth.authenticate(request)
        print(f"✓ Authentication successful: User={user}, Token={validated_token}")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
    
    # Test the view directly
    print("\n--- View Processing ---")
    view = ChatCompletionsProxyView()
    view.request = request
    view.format_kwarg = None
    
    # Manually run the permission check
    print("Checking permissions...")
    for permission_class in view.permission_classes:
        permission = permission_class()
        has_permission = permission.has_permission(request, view)
        print(f"Permission {permission_class.__name__}: {has_permission}")
        
        if not has_permission:
            print(f"Permission denied by {permission_class.__name__}")
            print(f"Request user: {getattr(request, 'user', 'NOT SET')}")
            print(f"User authenticated: {getattr(getattr(request, 'user', None), 'is_authenticated', 'N/A')}")
    
    # Check if user is set on request
    print(f"\nRequest user before auth: {getattr(request, 'user', 'NOT SET')}")
    
    # Run authentication on the view
    try:
        user, auth = view.perform_authentication(request)
        print(f"View authentication result: User={user}, Auth={auth}")
        request.user = user
    except Exception as e:
        print(f"View authentication error: {e}")
    
    print(f"Request user after auth: {getattr(request, 'user', 'NOT SET')}")

if __name__ == "__main__":
    debug_view_authentication()