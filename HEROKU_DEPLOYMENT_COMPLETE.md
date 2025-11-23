# Heroku Deployment Guide - PromptCraft Backend

## 🚀 Quick Deployment Checklist

### Prerequisites
- [ ] Heroku account created
- [ ] Heroku CLI installed
- [ ] Git repository initialized
- [ ] Google OAuth Console configured with production redirect URI
- [ ] Environment variables ready

### OAuth Configuration (CRITICAL)
**Before deploying, update Google OAuth Console:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services > Credentials**
4. Find OAuth 2.0 Client ID: `367664891760-g0phqsut6h3jm0bq12sorj1e1nlkuf7u.apps.googleusercontent.com`
5. Click **Edit**
6. Under **Authorized redirect URIs**, add:
   - `https://www.prompt-temple.com/auth/callback/google`
   - `https://prompt-temple.com/auth/callback/google`
   - `https://your-app-name.herokuapp.com/auth/callback/google` (if using Heroku subdomain)
   - Keep `http://localhost:3000/auth/callback/google` for local development
7. Click **Save**

---

## 📦 Step 1: Install Heroku CLI

```powershell
# Windows (using Chocolatey)
choco install heroku-cli

# Or download from: https://devcenter.heroku.com/articles/heroku-cli
```

---

## 🔐 Step 2: Login to Heroku

```powershell
heroku login
```

---

## 🏗️ Step 3: Create Heroku App

```powershell
# Create new app (replace with your desired name)
heroku create prompt-temple-backend

# Or use existing app
heroku git:remote -a your-existing-app-name
```

---

## 🗄️ Step 4: Add PostgreSQL Database

```powershell
# Add Heroku Postgres (Essential Plan or higher for production)
heroku addons:create heroku-postgresql:essential-0

# Check database URL
heroku config:get DATABASE_URL
```

---

## 💾 Step 5: Add Redis (Optional but Recommended)

```powershell
# Add Heroku Redis
heroku addons:create heroku-redis:mini

# Check Redis URL
heroku config:get REDIS_URL
```

---

## ⚙️ Step 6: Configure Environment Variables

```powershell
# Django Configuration
heroku config:set DJANGO_ENVIRONMENT=heroku
heroku config:set SECRET_KEY="your-super-secret-production-key-here"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=".herokuapp.com,www.prompt-temple.com,prompt-temple.com"

# Frontend Configuration
heroku config:set FRONTEND_URL=https://www.prompt-temple.com

# Google OAuth (USE PRODUCTION REDIRECT URI)
heroku config:set GOOGLE_OAUTH2_CLIENT_ID=367664891760-g0phqsut6h3jm0bq12sorj1e1nlkuf7u.apps.googleusercontent.com
heroku config:set GOOGLE_OAUTH2_CLIENT_SECRET=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
heroku config:set SOCIAL_AUTH_GOOGLE_REDIRECT_URI=https://www.prompt-temple.com/auth/callback/google

# GitHub OAuth
heroku config:set GITHUB_CLIENT_ID=Ov23liEYkjrWCP9zoHNF
heroku config:set GITHUB_CLIENT_SECRET=ecad6c4f421187b2f6b8a032df90647d463271d8
heroku config:set SOCIAL_AUTH_GITHUB_REDIRECT_URI=https://www.prompt-temple.com/auth/callback/github

# AI API Keys
heroku config:set DEEPSEEK_API_KEY=sk-fad996d33334443dab24fcd669653814
heroku config:set DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
heroku config:set TAVILY_API_KEY=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

# Z.AI Configuration
heroku config:set ZAI_API_TOKEN=20b0829bcb234d0b8c073245bad18bc0.5epWW9GwBy5T9l2N
heroku config:set ZAI_API_BASE=https://api.z.ai/api/paas/v4
heroku config:set ZAI_DEFAULT_MODEL=glm-4-32b-0414-128k

# Optional: Add your OpenAI/Anthropic keys if needed
# heroku config:set OPENAI_API_KEY=your-openai-key
# heroku config:set ANTHROPIC_API_KEY=your-anthropic-key

# Verify configuration
heroku config
```

---

## 📝 Step 7: Prepare for Deployment

```powershell
# Ensure all files are committed
git add .
git commit -m "Prepare for Heroku deployment with OAuth configuration"

# Push to Heroku
git push heroku main

# Or if your branch is named 'master'
git push heroku master
```

---

## 🔄 Step 8: Run Database Migrations

```powershell
# Run migrations
heroku run python manage.py migrate

# Create superuser (optional)
heroku run python manage.py createsuperuser

# Collect static files (already handled by WhiteNoise, but can run manually)
heroku run python manage.py collectstatic --noinput
```

---

## 🚀 Step 9: Open Your App

```powershell
# Open in browser
heroku open

# Check logs
heroku logs --tail

# Check app status
heroku ps
```

---

## 🔍 Step 10: Verify Deployment

### Health Check
```powershell
curl https://your-app-name.herokuapp.com/health/
```

### Test OAuth Flow
1. Go to your frontend: `https://www.prompt-temple.com`
2. Click "Sign in with Google"
3. Authorize the app
4. Should redirect back with JWT tokens

### Check API Documentation
```
https://your-app-name.herokuapp.com/api/schema/swagger-ui/
```

---

## 🐛 Troubleshooting

### View Logs
```powershell
# View real-time logs
heroku logs --tail

# View last 1000 lines
heroku logs -n 1000

# Filter by source
heroku logs --source app
heroku logs --source heroku
```

### Common Issues

#### 1. OAuth 401 Error
**Symptom:** "Failed to exchange code for token"
**Solution:** 
- Verify redirect URI in Google OAuth Console matches exactly
- Check `SOCIAL_AUTH_GOOGLE_REDIRECT_URI` environment variable
- Ensure production URL uses HTTPS

#### 2. Database Connection Error
**Symptom:** "No DATABASE_URL set"
**Solution:**
```powershell
heroku addons:create heroku-postgresql:essential-0
heroku config:get DATABASE_URL
```

#### 3. Static Files Not Loading
**Symptom:** CSS/JS files return 404
**Solution:**
```powershell
heroku run python manage.py collectstatic --noinput
# WhiteNoise should handle this automatically
```

#### 4. Application Error (H10)
**Symptom:** "Application crashed"
**Solution:**
```powershell
# Check logs
heroku logs --tail

# Restart dynos
heroku restart

# Check dyno status
heroku ps
```

#### 5. CORS Errors
**Symptom:** Frontend can't access API
**Solution:**
- Verify `ALLOWED_HOSTS` includes your domain
- Check `CORS_ALLOWED_ORIGINS` in settings
- Ensure `CSRF_TRUSTED_ORIGINS` includes your frontend URL

---

## 🔧 Configuration Files

### Current Setup
- **Procfile:** Gunicorn web server (2 workers, 120s timeout)
- **runtime.txt:** Python 3.11.9
- **Settings:** `promptcraft/settings/heroku.py`
- **Database:** PostgreSQL (via DATABASE_URL)
- **Cache:** Redis (optional, falls back to in-memory)
- **Static Files:** WhiteNoise (no S3 needed)
- **Features:** No Celery, No Channels, No RAG (MVP)

---

## 📊 Scaling

### Scale Dynos
```powershell
# Scale web dynos
heroku ps:scale web=1

# For higher traffic
heroku ps:scale web=2

# Check current scaling
heroku ps
```

### Upgrade Database
```powershell
# Upgrade to Standard plan
heroku addons:upgrade postgresql:standard-0

# Check database size
heroku pg:info
```

---

## 🔒 Security Checklist

- [x] `DEBUG=False` in production
- [x] Strong `SECRET_KEY` set
- [x] `SECURE_SSL_REDIRECT=True`
- [x] `SESSION_COOKIE_SECURE=True`
- [x] `CSRF_COOKIE_SECURE=True`
- [x] HSTS headers enabled
- [x] XSS protection enabled
- [x] Content type sniffing blocked
- [x] OAuth redirect URIs whitelisted
- [x] CORS properly configured
- [x] CSRF trusted origins set

---

## 🌐 Custom Domain Setup

### Add Custom Domain
```powershell
# Add domain to Heroku
heroku domains:add www.prompt-temple.com
heroku domains:add prompt-temple.com

# Get DNS target
heroku domains
```

### Configure DNS
Add CNAME records in your DNS provider:
```
www.prompt-temple.com  →  your-app-name.herokuapp.com
prompt-temple.com      →  your-app-name.herokuapp.com
```

### Enable SSL
```powershell
# Heroku provides free SSL with custom domains
heroku certs:auto:enable
```

---

## 📈 Monitoring

### View Metrics
```powershell
# Open metrics dashboard
heroku open --admin

# View app performance
heroku apps:info
```

### Set Up Alerts
- Configure dyno alerts in Heroku Dashboard
- Monitor response times
- Track error rates

---

## 🔄 Continuous Deployment

### Automatic Deployments from GitHub
1. Go to Heroku Dashboard
2. Select your app
3. Go to **Deploy** tab
4. Connect to GitHub
5. Enable **Automatic Deploys** from `main` branch
6. Enable **Wait for CI to pass** (optional)

---

## 🎯 Post-Deployment Tasks

1. **Test all endpoints:**
   - Registration: `/api/v2/auth/registration/`
   - Login: `/api/v2/auth/login/`
   - Google OAuth: `/api/v2/auth/social/callback/`
   - Templates: `/api/v2/templates/`
   - Prompt History: `/api/v2/history/`

2. **Update frontend environment variables:**
   ```env
   NEXT_PUBLIC_API_URL=https://your-app-name.herokuapp.com
   NEXT_PUBLIC_OAUTH_REDIRECT_URI=https://www.prompt-temple.com/auth/callback/google
   ```

3. **Test OAuth flow end-to-end**

4. **Monitor logs for first 24 hours**

5. **Set up error monitoring (Sentry):**
   ```powershell
   heroku config:set SENTRY_DSN=your-sentry-dsn
   ```

---

## 💡 Tips for Success

1. **Always use HTTPS in production** - OAuth requires secure connections
2. **Match redirect URIs exactly** - Including protocol, domain, port, path
3. **Keep development and production configs separate** - Use environment variables
4. **Monitor logs regularly** - Catch issues early
5. **Scale gradually** - Start with 1 dyno, scale as needed
6. **Use Redis for caching** - Improves performance significantly
7. **Enable database backups** - Essential for production

---

## 🆘 Support Resources

- [Heroku Documentation](https://devcenter.heroku.com/)
- [Django on Heroku](https://devcenter.heroku.com/articles/django-app-configuration)
- [Heroku Postgres](https://devcenter.heroku.com/categories/heroku-postgres)
- [Heroku Redis](https://devcenter.heroku.com/articles/heroku-redis)

---

## ✅ Deployment Complete!

Your PromptCraft backend is now live on Heroku with:
- ✅ PostgreSQL database
- ✅ Redis caching
- ✅ Google OAuth configured
- ✅ WhiteNoise static files
- ✅ Gunicorn production server
- ✅ HTTPS/SSL enabled
- ✅ CORS configured
- ✅ Security headers set

**Next Steps:**
1. Update frontend to use production API URL
2. Test all features end-to-end
3. Monitor logs and performance
4. Set up custom domain (optional)
5. Configure automated backups
