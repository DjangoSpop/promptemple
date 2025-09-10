#!/usr/bin/env python
"""
Debug JWT Authentication Issues
Test JWT token validation and decode the authentication problem
"""
import os
import sys
import django
import jwt
from datetime import datetime, timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

# Test token from the failed request
test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3MzU2ODI4LCJpYXQiOjE3NTcyNzA0MjgsImp0aSI6ImJjMTUzY2Q0MmY3ZjRjMDI5MTRiOWYyMTNmYjA4NjYzIiwidXNlcl9pZCI6IjFhMDA1YTViLTdlYTgtNDMzZC04ZGRmLWU2NzY2ODlmMTFkZSJ9.6usiGIA65JxRzio8MltXe8nT1OWsWeukEa_qmYX8kAw"

def debug_jwt_authentication():
    """Debug JWT authentication step by step"""
    print("=== JWT Authentication Debug ===")
    print(f"Test Token: {test_token[:50]}...")
    print()
    
    # 1. Check JWT secret key configuration
    try:
        secret_key = settings.SECRET_KEY
        print(f"✓ Django SECRET_KEY configured: {secret_key[:20]}...")
    except Exception as e:
        print(f"✗ Django SECRET_KEY error: {e}")
        return
    
    # 2. Check SimpleJWT configuration
    print("\n--- SimpleJWT Configuration ---")
    jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
    print(f"Access Token Lifetime: {jwt_settings.get('ACCESS_TOKEN_LIFETIME', 'Not set')}")
    print(f"Refresh Token Lifetime: {jwt_settings.get('REFRESH_TOKEN_LIFETIME', 'Not set')}")
    print(f"Rotate Refresh Tokens: {jwt_settings.get('ROTATE_REFRESH_TOKENS', 'Not set')}")
    
    # 3. Try to decode the token manually
    print("\n--- Manual Token Decoding ---")
    try:
        # Decode without verification first to see the payload
        decoded_payload = jwt.decode(test_token, options={"verify_signature": False})
        print(f"✓ Token payload decoded: {decoded_payload}")
        
        # Check token expiration
        exp_timestamp = decoded_payload.get('exp')
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            print(f"Token expires: {exp_datetime}")
            print(f"Current time: {now}")
            if exp_datetime < now:
                print("✗ TOKEN IS EXPIRED!")
            else:
                print("✓ Token is not expired")
        
        # Check user ID
        user_id = decoded_payload.get('user_id')
        print(f"User ID in token: {user_id}")
        
    except jwt.DecodeError as e:
        print(f"✗ JWT decode error: {e}")
        return
    except Exception as e:
        print(f"✗ Unexpected decode error: {e}")
        return
    
    # 4. Try to decode with signature verification
    print("\n--- Signature Verification ---")
    try:
        decoded_verified = jwt.decode(
            test_token, 
            secret_key, 
            algorithms=["HS256"]
        )
        print(f"✓ Token signature verified: {decoded_verified}")
    except jwt.ExpiredSignatureError:
        print("✗ Token signature expired")
    except jwt.InvalidSignatureError:
        print("✗ Token signature invalid")
    except Exception as e:
        print(f"✗ Signature verification error: {e}")
    
    # 5. Try SimpleJWT validation
    print("\n--- SimpleJWT Validation ---")
    try:
        access_token = AccessToken(test_token)
        print(f"✓ SimpleJWT validation passed")
        print(f"Token payload: {access_token.payload}")
        
        # Try to get the user
        user_id = access_token.payload.get('user_id')
        if user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                print(f"✓ User found: {user}")
            except User.DoesNotExist:
                print(f"✗ User with ID {user_id} does not exist")
        
    except TokenError as e:
        print(f"✗ SimpleJWT validation failed: {e}")
    except Exception as e:
        print(f"✗ Unexpected SimpleJWT error: {e}")
    
    # 6. Check REST framework authentication classes
    print("\n--- REST Framework Configuration ---")
    rest_framework_config = getattr(settings, 'REST_FRAMEWORK', {})
    auth_classes = rest_framework_config.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    print(f"Authentication classes: {auth_classes}")
    
    permission_classes = rest_framework_config.get('DEFAULT_PERMISSION_CLASSES', [])
    print(f"Permission classes: {permission_classes}")
    
    # 7. Check if the user model exists and is configured correctly
    print("\n--- User Model Check ---")
    try:
        User = get_user_model()
        print(f"✓ User model: {User}")
        print(f"✓ User model path: {User._meta.app_label}.{User._meta.model_name}")
        
        # Check if users exist
        user_count = User.objects.count()
        print(f"✓ Total users in database: {user_count}")
        
    except Exception as e:
        print(f"✗ User model error: {e}")

if __name__ == "__main__":
    debug_jwt_authentication()