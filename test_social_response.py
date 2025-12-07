"""
Test social auth response structure
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.social_auth.serializers import SocialUserProfileSerializer
from apps.users.views import safe_jwt_token_generation
import json

User = get_user_model()

print("="*70)
print("🔍 Testing Social Auth Response Structure")
print("="*70)

# Get a test user (or create one)
try:
    user = User.objects.filter(provider_name='google').first()
    if not user:
        user = User.objects.first()
    
    if not user:
        print("\n❌ No users found in database")
        exit(1)
    
    print(f"\n✅ Using test user: {user.username} ({user.email})")
    
    # Generate tokens
    tokens = safe_jwt_token_generation(user)
    print(f"\n📋 Tokens generated:")
    print(f"   Access: {tokens['access'][:50]}...")
    print(f"   Refresh: {tokens['refresh'][:50]}...")
    
    # Serialize user profile
    from django.test import RequestFactory
    factory = RequestFactory()
    request = factory.get('/')
    
    serializer = SocialUserProfileSerializer(user, context={'request': request})
    user_data = serializer.data
    
    print(f"\n👤 User Profile Data:")
    print(json.dumps(user_data, indent=2, default=str))
    
    # Build complete response
    response_data = {
        'message': 'Social authentication successful',
        'user': user_data,
        'tokens': tokens,
        'access': tokens['access'],
        'refresh': tokens['refresh'],
        'is_new_user': False,
        'provider': user.provider_name or 'google'
    }
    
    print(f"\n📦 Complete Social Auth Response Structure:")
    print(json.dumps({
        'message': response_data['message'],
        'access': response_data['access'][:50] + '...',
        'refresh': response_data['refresh'][:50] + '...',
        'tokens': {
            'access': response_data['tokens']['access'][:50] + '...',
            'refresh': response_data['tokens']['refresh'][:50] + '...'
        },
        'is_new_user': response_data['is_new_user'],
        'provider': response_data['provider'],
        'user': {
            'id': user_data['id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'provider_name': user_data.get('provider_name'),
            'social_avatar_url': user_data.get('social_avatar_url'),
            'credits': user_data.get('credits'),
            'level': user_data.get('level'),
            'daily_streak': user_data.get('daily_streak'),
            '... and more': '(full profile data included)'
        }
    }, indent=2, default=str))
    
    print("\n" + "="*70)
    print("✅ Frontend should:")
    print("="*70)
    print("1. Extract tokens from response:")
    print("   const { access, refresh, user } = response.data")
    print("\n2. Store tokens:")
    print("   localStorage.setItem('access_token', access)")
    print("   localStorage.setItem('refresh_token', refresh)")
    print("\n3. Store user profile:")
    print("   localStorage.setItem('user', JSON.stringify(user))")
    print("\n4. Set auth state:")
    print("   setUser(user)")
    print("   setIsAuthenticated(true)")
    print("\n5. Include token in subsequent requests:")
    print("   headers: { Authorization: `Bearer ${access}` }")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
