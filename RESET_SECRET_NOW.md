# 🚨 IMMEDIATE FIX REQUIRED - Client Secret Invalid

## The Problem
Your Google OAuth Client Secret is **INCORRECT**. Google is returning `401 Unauthorized` which means the secret doesn't match the Client ID.

## ✅ FIX IT NOW - 5 Minutes

### Step 1: Open Google Console
```
https://console.cloud.google.com/apis/credentials
```
- Sign in with your Google account
- Select your project

### Step 2: Reset the Client Secret

1. Find "OAuth 2.0 Client IDs" section
2. Look for client starting with: `367664891760-g0phqsut6h3jm0bq12sorj1e1nlkuf7u`
3. Click on the **client name** (not the ID itself)
4. In the details page, find and click: **"RESET SECRET"** button
5. Confirm the reset
6. **IMMEDIATELY COPY** the new secret (shown only once!)

### Step 3: Update .env

Open `.env` file and replace the secret:

```env
GOOGLE_OAUTH2_CLIENT_SECRET=YOUR_NEW_SECRET_HERE
```

**Example:**
```env
GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-AbC123XyZ789NewSecretHere
```

### Step 4: Add Redirect URIs (While You're There)

In the same OAuth client details:

1. Scroll to "Authorized redirect URIs"
2. Make sure these are added:
   ```
   http://localhost:3000/auth/callback/google
   http://127.0.0.1:8000/api/v2/auth/social/callback/
   ```
3. Click **SAVE**

### Step 5: Check OAuth Consent Screen

1. Go to: **OAuth consent screen** (left menu)
2. Verify:
   - App name is set
   - Support email is set
   - Status is "Testing" or "In production"
3. If status is "Testing":
   - Scroll to "Test users"
   - Click "ADD USERS"
   - Add your Google email address
   - Save

### Step 6: Restart Backend

```powershell
# Stop current server (Ctrl+C)
# Then:
cd "c:\Users\ahmed el bahi\MyPromptApp\my_prmpt_bakend"
.\venv\Scripts\activate
python manage.py runserver
```

### Step 7: Test Credentials

```powershell
python test_google_direct.py
```

**Expected output:**
```
✅ CREDENTIALS ARE VALID!
The 'invalid_grant' error is EXPECTED
```

### Step 8: Try OAuth Flow

1. Clear browser cache (or use Incognito)
2. Go to: http://localhost:3000
3. Click "Login with Google"
4. Should work now! ✅

---

## Why This Happened

Possible reasons:
1. Secret was never set correctly
2. Secret was reset in console but not updated in .env
3. Copy-paste error when setting up initially
4. Using credentials from wrong Google project

---

## Still Getting 401?

If still failing after reset:

### Check 1: Correct Project?
- Make sure you're in the right Google Cloud Project
- Client ID should start with: `367664891760-g0phqsut6h3jm0bq12sorj1e1nlkuf7u`

### Check 2: Client Not Disabled?
- In OAuth clients list, check if client shows as "Active"
- If disabled, enable it

### Check 3: No Typos?
- Open .env in text editor
- Verify no extra spaces before/after the secret
- Verify secret is on one line (no line breaks)

### Check 4: Backend Restarted?
- Old credentials might be cached
- Must fully stop and restart the server

---

## Quick Verification Commands

```powershell
# Check what backend is using
cd "c:\Users\ahmed el bahi\MyPromptApp\my_prmpt_bakend"
.\venv\Scripts\python.exe -c "from decouple import config; secret = config('GOOGLE_OAUTH2_CLIENT_SECRET'); print(f'Secret length: {len(secret)} chars'); print(f'First 10: {secret[:10]}'); print(f'Last 10: {secret[-10:]}')"

# Test credentials
python test_google_direct.py

# Full test
python test_social_auth_fix.py
```

---

## ⚡ After Fixing

Once you see "✅ CREDENTIALS ARE VALID!" you're good to go!

The OAuth flow should work perfectly after that.
