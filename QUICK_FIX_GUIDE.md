# 🚀 Quick Fix Deployment Guide

## ✅ What Was Fixed

1. **Missing Import** - Added `ValidationError` to views.py
2. **Hardcoded URLs** - Now uses `FRONTEND_URL` environment variable
3. **Poor Error Logging** - Enhanced error messages for debugging
4. **Redirect URI Handling** - Dynamic resolution based on environment

## 🔧 Quick Setup (Local Development)

```bash
# 1. Ensure FRONTEND_URL is in .env
echo "FRONTEND_URL=http://localhost:3000" >> .env

# 2. Restart backend
python manage.py runserver

# 3. Test the fix
python test_social_auth_fix.py
```

## 🌐 Production Deployment (Heroku)

```bash
# Set environment variable
heroku config:set FRONTEND_URL=https://prompt-temple.com -a your-app-name

# Deploy the fix
git add .
git commit -m "Fix: Social auth ValidationError and redirect URI handling"
git push heroku main

# Verify configuration
heroku run python test_social_auth_fix.py -a your-app-name
```

## 🔍 Google OAuth Console Setup

**CRITICAL**: Add these EXACT redirect URIs to your Google OAuth Console:

### For Local Development:
```
http://localhost:3000/auth/callback/google
```

### For Production:
```
https://prompt-temple.com/auth/callback/google
https://www.prompt-temple.com/auth/callback/google
```

### Steps:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. APIs & Services > Credentials
3. Click your OAuth 2.0 Client ID
4. Add redirect URIs to "Authorized redirect URIs"
5. Click Save
6. **Wait 5 minutes** for changes to propagate

## 🧪 Testing the Fix

### Test 1: Configuration Check
```bash
python test_social_auth_fix.py
```

**Expected Output**: ✅ All configuration checks passed!

### Test 2: Backend API
```bash
curl http://127.0.0.1:8000/api/v2/auth/social/providers/
```

**Expected**: Should show `frontend_url` and correct redirect URIs

### Test 3: Full Flow
1. Open frontend: `http://localhost:3000`
2. Click "Login with Google"
3. Authorize in Google
4. Should redirect back and login successfully

## 🐛 Troubleshooting

### Error: "ValidationError is not defined"
✅ **FIXED** - Import added to views.py

### Error: "redirect_uri_mismatch"
1. Check exact redirect URI in backend logs
2. Add that EXACT URI to Google Console
3. Wait 5 minutes
4. Clear browser cache and retry

### Error: "invalid_client"
1. Verify `GOOGLE_OAUTH2_CLIENT_ID` in .env
2. Verify `GOOGLE_OAUTH2_CLIENT_SECRET` in .env
3. Check credentials are from correct Google project

### Backend not picking up changes
```bash
# Restart the server
# Press Ctrl+C then:
python manage.py runserver
```

## 📋 Files Changed

- ✅ `apps/social_auth/views.py` - Added ValidationError import & dynamic URLs
- ✅ `apps/social_auth/oauth_handlers.py` - Enhanced error handling & logging
- ✅ `.env.example` - Added FRONTEND_URL documentation
- ✅ `SOCIAL_AUTH_FIX.md` - Complete documentation
- ✅ `test_social_auth_fix.py` - Verification script

## 🎯 Ready to Deploy

Your backend is now ready! Make sure to:

- [ ] Set `FRONTEND_URL` in your environment
- [ ] Add redirect URIs to Google OAuth Console
- [ ] Wait 5 minutes after updating Google Console
- [ ] Deploy the changes
- [ ] Test the authentication flow

## 📞 Support

If you encounter issues:

1. Run: `python test_social_auth_fix.py`
2. Check backend logs for detailed error messages
3. Verify Google OAuth Console configuration
4. Review `SOCIAL_AUTH_FIX.md` for detailed troubleshooting

---

**Status**: ✅ Ready for Production  
**Date**: November 29, 2025
