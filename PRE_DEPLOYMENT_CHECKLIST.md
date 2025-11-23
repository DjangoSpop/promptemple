# Pre-Deployment Checklist

## ✅ Code Ready
- [x] All endpoints implemented and tested
- [x] OAuth handlers fixed (no hardcoded redirect URIs)
- [x] Registration endpoint supports dual password formats
- [x] Prompt history v2 API complete with CRUD + enhance
- [x] LangChain/LangSmith telemetry integrated
- [x] CORS configured for production
- [x] Error logging enhanced for debugging

## ✅ Configuration Files
- [x] `Procfile` - Gunicorn web server configured
- [x] `runtime.txt` - Python 3.11.9 specified
- [x] `requirements.txt` - All dependencies listed (optimized for Heroku)
- [x] `.gitignore` - Excludes sensitive files
- [x] `promptcraft/settings/heroku.py` - Production settings ready

## ✅ Environment Variables
- [x] `.env` file configured for development
- [x] `.env.template` created with all variables documented
- [x] Development OAuth redirect URI: `http://localhost:3000/auth/callback/google`
- [ ] **TODO:** Production OAuth redirect URI to be set on Heroku

## ⚠️ CRITICAL: Google OAuth Console Setup
**MUST DO BEFORE DEPLOYMENT:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Credentials**
3. Find OAuth Client ID: `367664891760-g0phqsut6h3jm0bq12sorj1e1nlkuf7u.apps.googleusercontent.com`
4. Click **Edit**
5. Under **Authorized redirect URIs**, ensure these are added:
   - `http://localhost:3000/auth/callback/google` ✅ (development)
   - `https://www.prompt-temple.com/auth/callback/google` ⚠️ (production - ADD THIS)
   - `https://prompt-temple.com/auth/callback/google` ⚠️ (production no-www - ADD THIS)
   - `https://YOUR-APP-NAME.herokuapp.com/auth/callback/google` ⚠️ (Heroku subdomain - ADD THIS)
6. Click **Save**

**Why this is critical:**
- OAuth will fail with 401 error if redirect URI is not whitelisted
- Google requires exact match (protocol, domain, port, path)
- Must be configured BEFORE testing OAuth in production

## 🚀 Deployment Steps

### Option 1: Automated (Recommended)
```powershell
.\deploy_heroku.ps1
```
- Interactive script
- Guides through all steps
- Configures environment variables
- Deploys code
- Runs migrations

### Option 2: Manual
```powershell
# 1. Login to Heroku
heroku login

# 2. Create app or connect to existing
heroku create YOUR-APP-NAME
# or
heroku git:remote -a YOUR-EXISTING-APP

# 3. Add PostgreSQL
heroku addons:create heroku-postgresql:essential-0

# 4. Add Redis (optional)
heroku addons:create heroku-redis:mini

# 5. Set environment variables (see HEROKU_DEPLOYMENT_COMPLETE.md)
heroku config:set DJANGO_ENVIRONMENT=heroku
heroku config:set SECRET_KEY="your-secret-key"
# ... (see .env.template for all variables)

# 6. Deploy
git push heroku main

# 7. Run migrations
heroku run python manage.py migrate

# 8. Create superuser
heroku run python manage.py createsuperuser

# 9. Open app
heroku open
```

## 📋 Post-Deployment Verification

### 1. Health Check
```bash
curl https://YOUR-APP-NAME.herokuapp.com/health/
```
Expected: `{"status": "ok"}`

### 2. API Root
```bash
curl https://YOUR-APP-NAME.herokuapp.com/api/
```
Expected: JSON with all endpoint information

### 3. Registration Test
```bash
curl -X POST https://YOUR-APP-NAME.herokuapp.com/api/v2/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password1": "SecurePass123!",
    "password2": "SecurePass123!"
  }'
```
Expected: User created with JWT tokens

### 4. OAuth Flow Test
1. Go to frontend: `https://www.prompt-temple.com`
2. Click "Sign in with Google"
3. Authorize the app
4. Should redirect back with JWT tokens
5. Check backend logs: `heroku logs --tail`

### 5. API Documentation
Visit: `https://YOUR-APP-NAME.herokuapp.com/api/schema/swagger-ui/`

## 🔍 Monitoring

### View Logs
```powershell
# Real-time logs
heroku logs --tail

# Last 1000 lines
heroku logs -n 1000

# Filter by source
heroku logs --source app
```

### Check Dyno Status
```powershell
heroku ps
```

### Database Info
```powershell
heroku pg:info
```

### Redis Info
```powershell
heroku redis:info
```

## 🐛 Common Issues & Solutions

### Issue 1: OAuth 401 Error
**Symptom:** "Failed to exchange code for token"
**Solution:** 
- Verify redirect URI in Google OAuth Console
- Check `SOCIAL_AUTH_GOOGLE_REDIRECT_URI` config var
- Ensure production URL uses HTTPS

```powershell
heroku config:get SOCIAL_AUTH_GOOGLE_REDIRECT_URI
# Should be: https://www.prompt-temple.com/auth/callback/google
```

### Issue 2: Database Connection Error
**Symptom:** "No DATABASE_URL set"
**Solution:**
```powershell
heroku addons:create heroku-postgresql:essential-0
heroku config:get DATABASE_URL
```

### Issue 3: Static Files 404
**Symptom:** CSS/JS files not loading
**Solution:**
```powershell
heroku run python manage.py collectstatic --noinput
# WhiteNoise should handle this automatically
```

### Issue 4: Application Crash (H10)
**Symptom:** "Application error"
**Solution:**
```powershell
heroku logs --tail
heroku restart
heroku ps:scale web=1
```

### Issue 5: CORS Errors
**Symptom:** Frontend can't access API
**Solution:**
```powershell
heroku config:set ALLOWED_HOSTS=".herokuapp.com,www.prompt-temple.com,prompt-temple.com"
heroku config:set CORS_ALLOWED_ORIGINS="https://www.prompt-temple.com,https://prompt-temple.com"
```

## 📊 Performance Checklist

- [ ] Database connection pooling enabled (conn_max_age=600)
- [ ] Redis caching configured
- [ ] Static files compressed (WhiteNoise)
- [ ] HTTPS/SSL enabled
- [ ] Gunicorn workers set (2 workers for hobby/basic dyno)
- [ ] Request timeout set (120s)
- [ ] Throttling configured in REST_FRAMEWORK

## 🔒 Security Checklist

- [x] `DEBUG=False` in production
- [x] Strong `SECRET_KEY` set
- [x] `SECURE_SSL_REDIRECT=True`
- [x] `SESSION_COOKIE_SECURE=True`
- [x] `CSRF_COOKIE_SECURE=True`
- [x] HSTS headers enabled (1 year)
- [x] XSS protection enabled
- [x] Content type sniffing blocked
- [x] Frame options set to DENY
- [ ] OAuth redirect URIs whitelisted in Google Console
- [x] CORS properly configured (production domains only)
- [x] CSRF trusted origins set

## 📁 Files Created/Modified

### New Files
- `HEROKU_DEPLOYMENT_COMPLETE.md` - Comprehensive deployment guide
- `deploy_heroku.ps1` - Automated deployment script
- `.env.template` - Environment variables template
- `PRE_DEPLOYMENT_CHECKLIST.md` - This file

### Modified Files
- `.env` - Updated with localhost redirect URI for development
- `apps/social_auth/oauth_handlers.py` - Fixed hardcoded redirect_uri
- `apps/social_auth/views.py` - Enhanced logging
- `apps/users/serializers.py` - Dual password field support
- `apps/users/urls.py` - Added /registration/ alias

### Existing Files (Ready for Deployment)
- `Procfile` - Gunicorn configuration
- `runtime.txt` - Python 3.11.9
- `requirements.txt` - Optimized dependencies
- `promptcraft/settings/heroku.py` - Production settings
- `.gitignore` - Excludes .env and sensitive files

## 🎯 Next Steps

1. [ ] **CRITICAL:** Update Google OAuth Console with production redirect URIs
2. [ ] Run deployment script: `.\deploy_heroku.ps1`
3. [ ] Verify health check endpoint
4. [ ] Test registration endpoint
5. [ ] Test OAuth flow end-to-end
6. [ ] Monitor logs for first 24 hours
7. [ ] Set up custom domain (optional)
8. [ ] Configure automated backups
9. [ ] Set up error monitoring (Sentry)
10. [ ] Update frontend environment variables

## 📞 Support Resources

- **Heroku Documentation:** https://devcenter.heroku.com/
- **Django on Heroku:** https://devcenter.heroku.com/articles/django-app-configuration
- **Heroku Postgres:** https://devcenter.heroku.com/categories/heroku-postgres
- **Heroku Redis:** https://devcenter.heroku.com/articles/heroku-redis
- **Google OAuth Setup:** https://developers.google.com/identity/protocols/oauth2

## ✅ Ready to Deploy!

All code is ready for production deployment. The only remaining step is to update the Google OAuth Console with production redirect URIs, then run the deployment script.

**Estimated deployment time:** 10-15 minutes
**Estimated total setup time:** 30 minutes (including OAuth setup)

Good luck! 🚀
