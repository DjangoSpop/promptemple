# ❌ ERROR: invalid_client - IMMEDIATE FIX GUIDE

## The Problem
Google is rejecting your OAuth credentials with `invalid_client: Unauthorized`. This means:
- Your Client ID or Client Secret is incorrect, OR
- The credentials don't match each other, OR
- The OAuth app configuration is incomplete

## ✅ IMMEDIATE FIX - Follow These Steps EXACTLY:

### Step 1: Go to Google Cloud Console
1. Open: https://console.cloud.google.com/apis/credentials
2. **Sign in with the Google account that owns the project**
3. Select your project from the dropdown (top left)

### Step 2: Find Your OAuth Client
1. Look for "OAuth 2.0 Client IDs" section
2. Find the client with ID starting with: `367664891760-g0phqsut6h3jm0bq1...`
3. Click on the **name** (not the client ID) to open details

### Step 3: Verify/Reset Credentials

#### Option A: Verify Existing Credentials (Try This First)
1. In the OAuth client details page, you should see:
   - **Client ID**: `367664891760-g0phqsut6h3jm0bq12sorj1e1nlkuf7u` (example)
   - **Client Secret**: (hidden, but visible)
2. Compare the **Client ID** with your .env file
3. If they DON'T match exactly → Copy the correct one from console

#### Option B: Reset Secret (If Step A Doesn't Work)
1. In the OAuth client details, find "RESET SECRET" button
2. Click "RESET SECRET" 
3. **⚠️ IMPORTANT**: Copy the new secret IMMEDIATELY (shown only once)
4. Keep this tab open until you update your .env

### Step 4: Configure Redirect URIs
In the same OAuth client details page:

1. Scroll to "Authorized redirect URIs"
2. Click "ADD URI"
3. Paste EXACTLY (no trailing slash):
   ```
   http://localhost:3000/auth/callback/google
   ```
4. Also add this for backend:
   ```
   http://127.0.0.1:8000/api/v2/auth/social/callback/
   ```
5. Click "SAVE" at the bottom

### Step 5: Update Your .env File
Open your `.env` file and update these lines:

```env
# Update with EXACT values from Google Console
GOOGLE_OAUTH2_CLIENT_ID=your-client-id-from-console
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret-from-console
FRONTEND_URL=http://localhost:3000
```

**Example:**
```env
GOOGLE_OAUTH2_CLIENT_ID=367664891760-g0phqsut6h3jm0bq12sorj1e1nlkuf7u.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-abc123xyz789_example_secret
FRONTEND_URL=http://localhost:3000
```

### Step 6: Verify OAuth Consent Screen
1. In Google Console, go to: **APIs & Services > OAuth consent screen**
2. Verify:
   - ✅ User Type is set (Internal or External)
   - ✅ App name is filled
   - ✅ Support email is set
   - ✅ Status shows "Testing" or "Published"

3. If status is "Testing":
   - Scroll down to "Test users"
   - Click "ADD USERS"
   - Add your Google email that you'll use to test
   - Click "SAVE"

### Step 7: Restart Backend
```powershell
# Stop the current server (Ctrl+C)
# Then restart:
cd "c:\Users\ahmed el bahi\MyPromptApp\my_prmpt_bakend"
.\venv\Scripts\activate
python manage.py runserver
```

### Step 8: Test Again
```powershell
# Run the diagnostic
python diagnose_google_oauth.py
```

Expected output should show:
```
✅ GOOD NEWS: Credentials are VALID!
```

### Step 9: Clear Browser & Test OAuth Flow
1. Clear browser cache (or use Incognito)
2. Go to your frontend: http://localhost:3000
3. Click "Login with Google"
4. Authorize
5. Should redirect back and login successfully!

---

## 🔍 Still Not Working?

### Double-Check These Common Mistakes:

1. **Wrong Project**: Make sure you're looking at the correct Google Cloud Project
2. **Copy-Paste Error**: Extra spaces or line breaks in credentials
3. **Old Secret**: Using an old secret after resetting
4. **Wrong Account**: Using a Google account not added as test user
5. **Cache**: Old credentials cached in backend (restart server!)

### Debug Commands:

```powershell
# Check what the backend is using:
cd "c:\Users\ahmed el bahi\MyPromptApp\my_prmpt_bakend"
.\venv\Scripts\python.exe -c "from decouple import config; print('ID:', config('GOOGLE_OAUTH2_CLIENT_ID')[:50]); print('Secret:', config('GOOGLE_OAUTH2_CLIENT_SECRET')[:20] + '...')"
```

### Manual Verification:
1. Open .env file in notepad
2. Copy Client ID from there
3. Open Google Console
4. Compare character-by-character
5. They must match EXACTLY

---

## 📧 Need More Help?

If still failing, provide:
1. Screenshot of Google OAuth client details (hide the secret!)
2. First 30 chars of Client ID from .env
3. Backend logs when attempting OAuth

---

## ⚡ Quick Commands

```powershell
# Check credentials
python diagnose_google_oauth.py

# Test configuration
python test_social_auth_fix.py

# Restart backend
python manage.py runserver

# Check .env
Get-Content .env | Select-String "GOOGLE"
```
