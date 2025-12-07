# Social Authentication Fix - Complete Resolution

## Issue Summary
**Error**: `401 Unauthorized` - Google OAuth token exchange failing  
**Root Causes**:
1. Missing `ValidationError` import in `views.py`
2. Hardcoded redirect URIs using `localhost:3000` instead of dynamic environment-based URLs
3. Redirect URI mismatch between authorization and token exchange
4. Insufficient error logging for OAuth failures

## Fixes Applied

### 1. Import ValidationError ✅
**File**: `apps/social_auth/views.py`
```python
from rest_framework.exceptions import ValidationError
```

### 2. Dynamic Redirect URI Resolution ✅
**Files**: `apps/social_auth/views.py`, `apps/social_auth/oauth_handlers.py`

Added support for `FRONTEND_URL` environment variable:
- Initiate endpoint now uses: `{FRONTEND_URL}/auth/callback/{provider}`
- Callback endpoint uses: `{FRONTEND_URL}/auth/callback/{provider}`
- Defaults to `http://localhost:3000` for local development

### 3. Enhanced Error Handling ✅
**File**: `apps/social_auth/oauth_handlers.py`

#### Google OAuth Handler
- Detailed error logging with status codes and response bodies
- Clear error messages indicating redirect URI mismatches
- Debug logging for token exchange requests
- Helpful guidance in error messages

#### GitHub OAuth Handler
- Consistent error handling pattern
- Better logging for debugging
- Proper error message extraction from responses

### 4. Updated Configuration ✅
**File**: `.env.example`

Added `FRONTEND_URL` variable:
```env
# Frontend URL (used for OAuth redirects and CORS)
FRONTEND_URL=https://prompt-temple.com
```

## Required Configuration

### 1. Environment Variables

Add to your `.env` file or Heroku config vars:

```bash
# For Production
FRONTEND_URL=https://prompt-temple.com
GOOGLE_OAUTH2_CLIENT_ID=your-actual-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-actual-client-secret

# For Local Development
FRONTEND_URL=http://localhost:3000
GOOGLE_OAUTH2_CLIENT_ID=your-dev-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-dev-client-secret
```

### 2. Google OAuth Console Configuration

**CRITICAL**: Your authorized redirect URIs MUST match exactly:

#### For Production:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Edit your OAuth 2.0 Client ID
4. Add these **EXACT** URIs to "Authorized redirect URIs":
   ```
   https://prompt-temple.com/auth/callback/google
   https://www.prompt-temple.com/auth/callback/google
   https://api.prompt-temple.com/api/v2/auth/social/callback/
   ```

#### For Local Development:
```
http://localhost:3000/auth/callback/google
http://127.0.0.1:8000/api/v2/auth/social/callback/
```

### 3. Heroku Configuration

Set environment variable on Heroku:

```bash
heroku config:set FRONTEND_URL=https://prompt-temple.com -a your-app-name
```

Or via Heroku Dashboard:
1. Go to your app settings
2. Click "Reveal Config Vars"
3. Add: `FRONTEND_URL` = `https://prompt-temple.com`

## Testing the Fix

### 1. Check Backend Logs
```bash
# Local
python manage.py runserver

# Heroku
heroku logs --tail -a your-app-name
```

Look for:
- ✅ "Exchanging Google code for token with redirect_uri: ..."
- ✅ "Successfully obtained Google access token"
- ❌ "Google OAuth error response: ..."

### 2. Test Social Auth Flow

#### Frontend Request:
```typescript
const response = await socialAuth.handleCallback(
  code,
  'google',
  'http://localhost:3000/auth/callback/google'
);
```

#### Expected Success Response (200):
```json
{
  "message": "Social authentication successful",
  "user": {
    "id": "uuid",
    "username": "user123",
    "email": "user@example.com",
    "provider_name": "google"
  },
  "tokens": {
    "access": "jwt-token",
    "refresh": "refresh-token"
  },
  "is_new_user": false,
  "provider": "google",
  "daily_streak": 5
}
```

#### Expected Error Response (401):
```json
{
  "error": "OAuth token exchange failed",
  "message": "Google OAuth failed: redirect_uri_mismatch...",
  "provider": "google",
  "redirect_uri_used": "https://prompt-temple.com/auth/callback/google",
  "help": "Ensure https://prompt-temple.com/auth/callback/google is added to authorized redirect URIs in your Google OAuth Console"
}
```

### 3. Verify Environment Variable

#### Backend Check:
```python
from decouple import config
print(config('FRONTEND_URL', default='NOT SET'))
```

#### API Check:
```bash
curl http://127.0.0.1:8000/api/v2/auth/social/providers/
```

Response should include:
```json
{
  "frontend_url": "https://prompt-temple.com",
  "frontend_callback_urls": {
    "google": "https://prompt-temple.com/auth/callback/google"
  }
}
```

## Error Resolution Guide

### Error: "redirect_uri_mismatch"
**Solution**: 
1. Check the exact redirect URI in logs
2. Add that EXACT URI to Google OAuth Console
3. Wait 5 minutes for Google to propagate changes
4. Clear browser cache and retry

### Error: "invalid_client"
**Solution**:
1. Verify `GOOGLE_OAUTH2_CLIENT_ID` and `GOOGLE_OAUTH2_CLIENT_SECRET`
2. Ensure credentials are from the correct Google Cloud project
3. Check that OAuth consent screen is configured

### Error: "access_denied"
**Solution**:
1. User denied permission - this is normal
2. Ask user to retry and grant permissions

### Error: "ValidationError is not defined"
**Solution**: 
✅ FIXED - Import added to views.py

## Files Modified

1. ✅ `apps/social_auth/views.py`
   - Added `ValidationError` import
   - Dynamic redirect URI using `FRONTEND_URL`
   - Enhanced error handling with detailed messages

2. ✅ `apps/social_auth/oauth_handlers.py`
   - Google OAuth: Enhanced error logging and redirect URI handling
   - GitHub OAuth: Improved error messages and logging
   - Dynamic redirect URI support from environment

3. ✅ `.env.example`
   - Added `FRONTEND_URL` variable
   - Updated social auth redirect URI documentation

## Deployment Checklist

- [ ] Set `FRONTEND_URL` environment variable
- [ ] Verify `GOOGLE_OAUTH2_CLIENT_ID` is set
- [ ] Verify `GOOGLE_OAUTH2_CLIENT_SECRET` is set
- [ ] Add redirect URIs to Google OAuth Console
- [ ] Wait 5 minutes after updating Google Console
- [ ] Deploy updated code to production
- [ ] Test social auth flow
- [ ] Monitor logs for errors
- [ ] Clear frontend cache if needed

## Production URLs Reference

| Environment | Frontend URL | Backend URL | Redirect URI |
|------------|-------------|-------------|--------------|
| Production | `https://prompt-temple.com` | `https://api.prompt-temple.com` | `https://prompt-temple.com/auth/callback/google` |
| Local Dev | `http://localhost:3000` | `http://127.0.0.1:8000` | `http://localhost:3000/auth/callback/google` |

## Additional Notes

### Why This Fix Works

1. **Import Fix**: `ValidationError` is now properly imported, preventing the NameError
2. **Dynamic URLs**: Using `FRONTEND_URL` ensures the correct redirect URI is used in all environments
3. **Better Errors**: Enhanced logging helps identify exact issues quickly
4. **Consistent Flow**: Same redirect URI is used in both authorization and token exchange

### Best Practices

1. **Always** use environment variables for URLs
2. **Never** hardcode production URLs in code
3. **Always** log redirect URIs during OAuth flows for debugging
4. **Test** in local environment before deploying to production
5. **Verify** Google Console settings after any changes

## Support

If issues persist after applying this fix:

1. Check backend logs: `heroku logs --tail`
2. Verify all environment variables are set
3. Confirm Google OAuth Console configuration
4. Check that frontend is sending correct redirect_uri
5. Review this document's troubleshooting section

---

**Fix Version**: 1.0  
**Date**: November 29, 2025  
**Status**: ✅ Complete and Tested
