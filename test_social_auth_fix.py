"""
Test script to verify social authentication fixes
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from decouple import config
from apps.social_auth.oauth_handlers import GoogleOAuthHandler, GitHubOAuthHandler

def test_configuration():
    """Test that OAuth configuration is correct"""
    print("=" * 60)
    print("🔍 Testing Social Auth Configuration")
    print("=" * 60)
    
    # Test environment variables
    print("\n1️⃣ Environment Variables:")
    frontend_url = config('FRONTEND_URL', default='NOT SET')
    google_client_id = config('GOOGLE_OAUTH2_CLIENT_ID', default='NOT SET')
    google_client_secret = config('GOOGLE_OAUTH2_CLIENT_SECRET', default='NOT SET')
    
    print(f"   FRONTEND_URL: {frontend_url}")
    print(f"   GOOGLE_OAUTH2_CLIENT_ID: {google_client_id[:20] + '...' if len(google_client_id) > 20 else google_client_id}")
    print(f"   GOOGLE_OAUTH2_CLIENT_SECRET: {'✅ SET' if google_client_secret != 'NOT SET' else '❌ NOT SET'}")
    
    # Test OAuth handlers
    print("\n2️⃣ OAuth Handler Initialization:")
    try:
        google_handler = GoogleOAuthHandler()
        print(f"   ✅ Google OAuth Handler initialized")
        print(f"      Client ID (first 20): {google_handler.client_id[:20]}...")
        print(f"      Token URL: {google_handler.token_url}")
        
        # Test redirect URI generation
        redirect_uri = f'{frontend_url}/auth/callback/google'
        print(f"      Redirect URI: {redirect_uri}")
        
    except Exception as e:
        print(f"   ❌ Google OAuth Handler failed: {e}")
    
    try:
        github_handler = GitHubOAuthHandler()
        print(f"   ✅ GitHub OAuth Handler initialized")
        print(f"      Client ID (first 20): {github_handler.client_id[:20]}...")
    except Exception as e:
        print(f"   ⚠️  GitHub OAuth Handler failed: {e}")
    
    # Test imports
    print("\n3️⃣ Import Verification:")
    try:
        from rest_framework.exceptions import ValidationError
        print("   ✅ ValidationError imported successfully")
    except ImportError as e:
        print(f"   ❌ ValidationError import failed: {e}")
    
    try:
        from apps.social_auth.views import SocialAuthCallbackView
        print("   ✅ SocialAuthCallbackView imported successfully")
    except ImportError as e:
        print(f"   ❌ SocialAuthCallbackView import failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    
    issues = []
    if frontend_url == 'NOT SET':
        issues.append("FRONTEND_URL not set")
    if google_client_id == 'NOT SET':
        issues.append("GOOGLE_OAUTH2_CLIENT_ID not set")
    if google_client_secret == 'NOT SET':
        issues.append("GOOGLE_OAUTH2_CLIENT_SECRET not set")
    
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 Add missing variables to your .env file")
    else:
        print("✅ All configuration checks passed!")
        print("\n📝 Next Steps:")
        print("   1. Ensure redirect URI is added to Google OAuth Console:")
        print(f"      {frontend_url}/auth/callback/google")
        print("   2. Start the backend server: python manage.py runserver")
        print("   3. Test the social auth flow from frontend")
    
    print("=" * 60)

if __name__ == "__main__":
    test_configuration()
