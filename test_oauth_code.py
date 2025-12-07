"""Test OAuth flow with actual authorization code"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from apps.social_auth.oauth_handlers import GoogleOAuthHandler
import traceback

code = "4/0ATX87lPwJfdZCGB6iv6hybtqnwqvpbrVyMToz7w1i4ROTdUpbtpiUNSchajWv03ISOmRKQ"
redirect_uri = "http://localhost:3000/auth/callback/google"

print("="*70)
print("🧪 Testing OAuth Flow with Real Authorization Code")
print("="*70)

try:
    handler = GoogleOAuthHandler()
    print(f"\n✅ Handler initialized")
    print(f"   Client ID: {handler.client_id[:40]}...")
    
    print(f"\n1️⃣ Exchanging code for token...")
    token_data = handler.exchange_code_for_token(code, redirect_uri)
    print(f"   ✅ Got access token: {token_data['access_token'][:20]}...")
    
    print(f"\n2️⃣ Fetching user info...")
    user_info = handler.get_user_info(token_data['access_token'])
    print(f"   ✅ User info: {user_info}")
    
    print(f"\n3️⃣ Creating/updating user...")
    user, is_new = handler.create_or_update_user(user_info)
    print(f"   ✅ User created/updated!")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Is new: {is_new}")
    print(f"   Provider: {user.provider_name}")
    print(f"   Provider ID: {user.provider_id}")
    
    print(f"\n" + "="*70)
    print("✅ OAUTH FLOW SUCCESSFUL!")
    print("="*70)
    
except Exception as e:
    print(f"\n" + "="*70)
    print("❌ ERROR IN OAUTH FLOW")
    print("="*70)
    print(f"\nError: {e}")
    print(f"\nFull traceback:")
    traceback.print_exc()
    print("="*70)
