"""
Google OAuth Diagnostic Tool
Tests the actual OAuth credentials with Google
"""
import requests
import sys

def test_google_oauth_credentials():
    """Test if Google OAuth credentials are valid"""
    
    print("\n" + "=" * 70)
    print("🔍 GOOGLE OAUTH CREDENTIALS DIAGNOSTIC")
    print("=" * 70)
    
    # Load credentials from environment
    from decouple import config
    
    client_id = config('GOOGLE_OAUTH2_CLIENT_ID', default='')
    client_secret = config('GOOGLE_OAUTH2_CLIENT_SECRET', default='')
    frontend_url = config('FRONTEND_URL', default='http://localhost:3000')
    redirect_uri = f'{frontend_url}/auth/callback/google'
    
    print(f"\n📋 Configuration:")
    print(f"   Client ID: {client_id[:30]}...")
    print(f"   Client Secret: {'✅ SET (' + str(len(client_secret)) + ' chars)' if client_secret else '❌ NOT SET'}")
    print(f"   Redirect URI: {redirect_uri}")
    
    # Check if credentials are set
    if not client_id or not client_secret:
        print("\n❌ ERROR: Google OAuth credentials not configured!")
        print("\n📝 Fix:")
        print("   1. Go to https://console.cloud.google.com/")
        print("   2. Select your project")
        print("   3. Go to APIs & Services > Credentials")
        print("   4. Find your OAuth 2.0 Client ID")
        print("   5. Copy Client ID and Client Secret to your .env file:")
        print("      GOOGLE_OAUTH2_CLIENT_ID=your-client-id")
        print("      GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret")
        return
    
    # Test 1: Verify Client ID format
    print(f"\n1️⃣ Client ID Format Check:")
    if client_id.endswith('.apps.googleusercontent.com'):
        print("   ✅ Client ID format looks correct")
    else:
        print("   ⚠️  Client ID doesn't end with .apps.googleusercontent.com")
        print("      This might be okay, but double-check it's correct")
    
    # Test 2: Check redirect URI registration
    print(f"\n2️⃣ Redirect URI Registration Check:")
    print(f"   ⚠️  Cannot automatically verify - you must check manually")
    print(f"\n   📋 Steps to verify:")
    print(f"   1. Go to: https://console.cloud.google.com/apis/credentials")
    print(f"   2. Click on your OAuth 2.0 Client ID: {client_id[:30]}...")
    print(f"   3. Under 'Authorized redirect URIs', ensure EXACTLY this URI is listed:")
    print(f"      {redirect_uri}")
    print(f"   4. If not, click 'ADD URI' and paste: {redirect_uri}")
    print(f"   5. Click 'SAVE'")
    print(f"   6. ⚠️  IMPORTANT: Wait 5-10 minutes for changes to propagate")
    
    # Test 3: Common issues
    print(f"\n3️⃣ Common Issues:")
    print(f"   ❌ Trailing slashes: {redirect_uri}/ ≠ {redirect_uri}")
    print(f"   ❌ HTTP vs HTTPS: http:// ≠ https://")
    print(f"   ❌ localhost vs 127.0.0.1: localhost ≠ 127.0.0.1")
    print(f"   ❌ Port numbers: :3000 ≠ :3001")
    print(f"   ✅ Must match EXACTLY character-by-character")
    
    # Test 4: Attempt a test token request (will fail but shows the error)
    print(f"\n4️⃣ Test Token Exchange (with dummy code):")
    try:
        test_code = "test_code_will_fail"
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': test_code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri,
            },
            timeout=10
        )
        
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text[:200]}")
        
        if response.status_code == 400:
            error_data = response.json()
            error_type = error_data.get('error', '')
            
            if error_type == 'invalid_grant':
                print(f"\n   ✅ GOOD NEWS: Credentials are VALID!")
                print(f"      The 'invalid_grant' error is expected (we used a dummy code)")
                print(f"      This confirms your Client ID and Secret are correct.")
                print(f"\n   ⚠️  However, your OAuth flow is still failing...")
                print(f"      Most likely cause: Redirect URI mismatch")
                print(f"\n   🔧 Next steps:")
                print(f"      1. Verify redirect URI in Google Console (see above)")
                print(f"      2. Make sure it's EXACTLY: {redirect_uri}")
                print(f"      3. Wait 5-10 minutes after making changes")
                print(f"      4. Clear your browser cache")
                print(f"      5. Try the OAuth flow again")
                
            elif error_type == 'invalid_client':
                print(f"\n   ❌ INVALID CREDENTIALS!")
                print(f"      Your Client ID or Client Secret is incorrect.")
                print(f"\n   🔧 Fix:")
                print(f"      1. Go to Google Cloud Console")
                print(f"      2. APIs & Services > Credentials")
                print(f"      3. Find your OAuth 2.0 Client ID")
                print(f"      4. Click 'RESET SECRET' to generate a new secret")
                print(f"      5. Copy the NEW credentials to your .env file")
                print(f"      6. Restart your backend server")
                
        elif response.status_code == 401:
            print(f"\n   ❌ UNAUTHORIZED!")
            print(f"      Your credentials are invalid or the OAuth app is disabled.")
            print(f"\n   🔧 Fix:")
            print(f"      1. Verify Client ID and Secret in .env match Google Console")
            print(f"      2. Ensure OAuth consent screen is configured")
            print(f"      3. Check that OAuth app is not suspended")
            
    except Exception as e:
        print(f"   ⚠️  Could not test credentials: {e}")
    
    # Summary
    print(f"\n" + "=" * 70)
    print(f"📊 SUMMARY")
    print(f"=" * 70)
    print(f"\nIf you're still getting 'invalid_client' error:")
    print(f"\n1️⃣ VERIFY CREDENTIALS:")
    print(f"   • Go to Google Cloud Console")
    print(f"   • Copy Client ID from console")
    print(f"   • Compare with your .env file")
    print(f"   • They must match EXACTLY")
    print(f"\n2️⃣ RESET SECRET (if needed):")
    print(f"   • In Google Console, click 'RESET SECRET'")
    print(f"   • Copy the NEW secret immediately")
    print(f"   • Update .env file")
    print(f"   • Restart backend")
    print(f"\n3️⃣ CHECK REDIRECT URI:")
    print(f"   • Must be EXACTLY: {redirect_uri}")
    print(f"   • No trailing slash")
    print(f"   • Correct port number")
    print(f"   • Wait 5-10 minutes after changes")
    print(f"\n4️⃣ OAUTH CONSENT SCREEN:")
    print(f"   • Must be configured in Google Console")
    print(f"   • Must have at least one test user (if in testing mode)")
    print(f"   • Status should be 'Testing' or 'Published'")
    print(f"\n" + "=" * 70)

if __name__ == "__main__":
    test_google_oauth_credentials()
