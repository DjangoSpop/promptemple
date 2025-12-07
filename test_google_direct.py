"""
Direct Google OAuth Test
Makes a real call to Google to test credentials
"""
import requests
from decouple import config

def test_direct_google_call():
    print("\n" + "="*60)
    print("🧪 DIRECT GOOGLE OAUTH API TEST")
    print("="*60)
    
    client_id = config('GOOGLE_OAUTH2_CLIENT_ID')
    client_secret = config('GOOGLE_OAUTH2_CLIENT_SECRET')
    redirect_uri = 'http://localhost:3000/auth/callback/google'
    
    print(f"\nTesting with:")
    print(f"  Client ID: {client_id[:40]}...")
    print(f"  Secret: {client_secret[:15]}...")
    print(f"  Redirect: {redirect_uri}")
    
    # Test with a dummy authorization code (will fail, but error tells us if creds are valid)
    print(f"\n📡 Sending request to Google...")
    
    try:
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': 'dummy_code_for_testing',
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        print(f"\n📊 Response:")
        print(f"  Status: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        print(f"  Body: {response.text}")
        
        if response.status_code == 400:
            data = response.json()
            error = data.get('error', '')
            
            if error == 'invalid_grant':
                print(f"\n✅ CREDENTIALS ARE VALID!")
                print(f"   The 'invalid_grant' error is EXPECTED (we used dummy code)")
                print(f"   This means your Client ID and Secret are CORRECT.")
                print(f"\n   ✅ Your issue is NOT with credentials!")
                print(f"   ⚠️  Likely issue: Authorization code being reused or expired")
                print(f"\n   🔧 Next steps:")
                print(f"      1. Make sure redirect URI is registered: {redirect_uri}")
                print(f"      2. Try the OAuth flow again (fresh authorization)")
                print(f"      3. Check that you're added as a test user in Google Console")
                
            elif error == 'invalid_client':
                print(f"\n❌ INVALID CREDENTIALS!")
                print(f"   Your Client ID and/or Secret are WRONG.")
                print(f"\n   🔧 FIX:")
                print(f"      1. Go to: https://console.cloud.google.com/apis/credentials")
                print(f"      2. Find OAuth client: {client_id[:40]}...")
                print(f"      3. Click 'RESET SECRET'")
                print(f"      4. Copy the NEW secret")
                print(f"      5. Update .env with new secret")
                print(f"      6. Restart backend server")
                
            elif error == 'redirect_uri_mismatch':
                print(f"\n❌ REDIRECT URI NOT REGISTERED!")
                print(f"   The redirect URI is not in your Google Console.")
                print(f"\n   🔧 FIX:")
                print(f"      1. Go to: https://console.cloud.google.com/apis/credentials")
                print(f"      2. Click on your OAuth client")
                print(f"      3. Add EXACTLY this URI: {redirect_uri}")
                print(f"      4. Save and wait 5 minutes")
            else:
                print(f"\n⚠️  Unknown error: {error}")
                print(f"   Description: {data.get('error_description', 'N/A')}")
                
        elif response.status_code == 401:
            print(f"\n❌ 401 UNAUTHORIZED")
            print(f"   This usually means:")
            print(f"   1. Client Secret is incorrect")
            print(f"   2. OAuth client is disabled")
            print(f"   3. Project billing is disabled")
            print(f"\n   🔧 FIX:")
            print(f"      1. Verify Client Secret in .env")
            print(f"      2. Check OAuth client status in Google Console")
            print(f"      3. Ensure project is active")
        else:
            print(f"\n⚠️  Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error making request: {e}")
    
    print(f"\n" + "="*60)

if __name__ == "__main__":
    test_direct_google_call()
