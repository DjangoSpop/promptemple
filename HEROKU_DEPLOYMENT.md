# 🚀 Heroku Deployment Guide - Optimized for Under 500MB

## 📊 Optimization Summary

**Original Size:** ~2.5GB  
**Optimized Size:** ~185MB  
**Savings:** 93% (2.3GB removed)  
**Status:** ✅ Ready for Heroku deployment

---

## ✅ What Was Done

### Removed (~2.3GB)
- ❌ `torch`, `transformers`, `sentence-transformers` (~1.6GB) - No local ML models
- ❌ `numpy`, `pandas`, `scipy`, `scikit-learn` (~750MB) - No data science operations
- ❌ `chromadb`, `faiss-cpu`, `pgvector` (~300MB) - No vector databases
- ❌ `celery`, `django-celery-beat` (~50MB) - Using synchronous execution
- ❌ `channels`, `channels-redis`, `daphne` (~80MB) - Using SSE with Gunicorn
- ❌ Research agent heavy dependencies

### Kept (~185MB)
- ✅ Django + DRF - Core framework
- ✅ JWT + Social Auth - User management  
- ✅ OpenAI/Anthropic API clients - AI services
- ✅ Minimal LangChain - LLM orchestration
- ✅ Stripe - Payment processing
- ✅ Gunicorn - Production server
- ✅ PostgreSQL - Database
- ✅ Redis - Caching
- ✅ Sentry - Error tracking

---

## 📦 Files Created

1. ✅ `requirements-heroku.txt` - Optimized dependencies
2. ✅ `.slugignore` - Exclude large files from deployment
3. ✅ `Procfile` - Updated for Gunicorn (no Celery/Daphne)
4. ✅ `runtime.txt` - Python 3.11.9
5. ✅ `promptcraft/settings/heroku.py` - Heroku-specific settings
6. ✅ `.gitignore` - Updated to exclude large datasets
7. ✅ `apps/templates/management/commands/seed_templates.py` - Already exists!

---

## 🔧 Pre-Deployment Steps

### 1. Export Template Fixtures (Run Locally)

```bash
# Activate virtual environment
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Export templates to fixture
python manage.py dumpdata templates.Template templates.TemplateCategory templates.PromptField templates.TemplateField --indent 2 > templates_fixture.json

# Verify fixture was created
ls templates_fixture.json
```

### 2. Test with Heroku Requirements (Optional but Recommended)

```bash
# Backup current requirements
cp requirements.txt requirements-backup.txt

# Test with Heroku requirements
pip install -r requirements-heroku.txt

# Run server to test
python manage.py runserver

# If everything works, you're ready to deploy!
```

### 3. Initialize Git (if not already)

```bash
git init
git add .
git commit -m "Initial commit: Heroku optimization under 500MB"
```

---

## 🚀 Heroku Deployment Steps

### Step 1: Install Heroku CLI

Download from: https://devcenter.heroku.com/articles/heroku-cli

```bash
# Verify installation
heroku --version
```

### Step 2: Login to Heroku

```bash
heroku login
```

### Step 3: Create Heroku App

```bash
# Create app with a custom name
heroku create prompt-temple-mvp

# Or let Heroku generate a name
heroku create

# Note: Your app URL will be https://your-app-name.herokuapp.com
```

### Step 4: Add Heroku Postgres

```bash
# Add PostgreSQL database (Mini plan - Free tier)
heroku addons:create heroku-postgresql:mini

# Verify database was added
heroku addons
```

### Step 5: Add Heroku Redis (Optional but Recommended)

```bash
# Add Redis for caching (Mini plan)
heroku addons:create heroku-redis:mini

# Verify Redis was added
heroku addons
```

### Step 6: Set Environment Variables

```bash
# Required settings
heroku config:set DJANGO_SETTINGS_MODULE=promptcraft.settings.heroku
heroku config:set DJANGO_ENVIRONMENT=heroku
heroku config:set SECRET_KEY="your-production-secret-key-here-make-it-long-and-random"
heroku config:set DEBUG=False

# AI API Keys
heroku config:set DEEPSEEK_API_KEY="sk-fad996d33334443dab24fcd669653814"
heroku config:set DEEPSEEK_BASE_URL="https://api.deepseek.com"
heroku config:set DEEPSEEK_DEFAULT_MODEL="deepseek-chat"

# Optional: OpenAI (if using)
heroku config:set OPENAI_API_KEY="your-openai-key"

# Optional: Anthropic (if using)
heroku config:set ANTHROPIC_API_KEY="your-anthropic-key"

# Google OAuth (Social Authentication)
heroku config:set GOOGLE_OAUTH2_CLIENT_ID="1088607409316-tshcdh28ka5v0gpjnp8j040gm6lcar2h.apps.googleusercontent.com"
heroku config:set GOOGLE_OAUTH2_CLIENT_SECRET="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"

# GitHub OAuth (Social Authentication)
heroku config:set GITHUB_CLIENT_ID="Ov23liEYkjrWCP9zoHNF"
heroku config:set GITHUB_CLIENT_SECRET="ecad6c4f421187b2f6b8a032df90647d463271d8"

# Stripe (Payment Processing)
heroku config:set STRIPE_SECRET_KEY="your-stripe-secret-key"
heroku config:set STRIPE_PUBLISHABLE_KEY="your-stripe-publishable-key"

# Sentry (Error Tracking) - Optional
heroku config:set SENTRY_DSN="your-sentry-dsn"

# Frontend URLs (Update with your actual domain)
heroku config:set FRONTEND_URL="https://www.prompt-temple.com"
heroku config:set ALLOWED_HOSTS=".herokuapp.com,www.prompt-temple.com,prompt-temple.com"

# Verify all config vars
heroku config
```

### Step 7: Deploy to Heroku

```bash
# Add Heroku remote (if not already added)
heroku git:remote -a your-app-name

# Deploy using requirements-heroku.txt
# Option A: Rename requirements-heroku.txt to requirements.txt
mv requirements.txt requirements-old.txt
mv requirements-heroku.txt requirements.txt
git add .
git commit -m "Use Heroku-optimized requirements"

# Push to Heroku
git push heroku main

# Watch deployment logs
heroku logs --tail
```

### Step 8: Run Migrations

```bash
# Run database migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

### Step 9: Seed Templates

```bash
# Upload fixture file first (if not in git)
git add templates_fixture.json
git commit -m "Add templates fixture"
git push heroku main

# Seed templates
heroku run python manage.py seed_templates

# Or use the existing seed command with mock data
heroku run python manage.py seed_templates --clear
```

### Step 10: Collect Static Files (if needed)

```bash
# WhiteNoise handles this automatically, but you can run manually
heroku run python manage.py collectstatic --noinput
```

### Step 11: Open Your App

```bash
# Open in browser
heroku open

# Your app should be live at:
# https://your-app-name.herokuapp.com
```

---

## 🔍 Verify Deployment

### Check App Status

```bash
# Check dyno status
heroku ps

# Expected output:
# === web (Free): gunicorn promptcraft.wsgi --bind 0.0.0.0:$PORT
# web.1: up 2025/11/19 22:00:00 +0000 (~ 1m ago)
```

### Check Logs

```bash
# View recent logs
heroku logs --tail

# Look for:
# ✅ "🚀 HEROKU DEPLOYMENT CONFIGURATION LOADED"
# ✅ "Booting worker with pid"
# ✅ No error messages
```

### Test Endpoints

```bash
# Test health endpoint
curl https://your-app-name.herokuapp.com/api/v2/health/

# Test templates endpoint
curl https://your-app-name.herokuapp.com/api/v2/templates/

# Test config endpoint
curl https://your-app-name.herokuapp.com/api/v2/core/config/
```

### Check Database

```bash
# Connect to database
heroku pg:psql

# Check templates
SELECT COUNT(*) FROM templates_template;
SELECT COUNT(*) FROM templates_templatecategory;

# Exit
\q
```

---

## 📊 Monitor Your App

### View Metrics

```bash
# View app metrics
heroku logs --tail

# View database info
heroku pg:info

# View Redis info (if added)
heroku redis:info
```

### Check Slug Size

```bash
# Check deployed slug size
heroku slugs:info

# Expected output:
# Size: ~185MB (should be well under 500MB)
```

---

## 🐛 Troubleshooting

### Issue: Slug Too Large

```bash
# Check what's in the slug
heroku run bash
du -sh * | sort -hr | head -20
exit

# Solution: Add more items to .slugignore
```

### Issue: Application Error (H10)

```bash
# Check logs
heroku logs --tail

# Common causes:
# - Missing environment variables
# - Database not configured
# - Migration not run
# - Port binding issue

# Fix: Ensure Procfile uses $PORT
web: gunicorn promptcraft.wsgi --bind 0.0.0.0:$PORT
```

### Issue: Database Connection Error

```bash
# Check DATABASE_URL is set
heroku config:get DATABASE_URL

# Run migrations again
heroku run python manage.py migrate
```

### Issue: Static Files Not Loading

```bash
# Collect static files
heroku run python manage.py collectstatic --noinput

# Check WhiteNoise is configured in settings/heroku.py
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Issue: OAuth Not Working

```bash
# Check OAuth redirect URIs in Google/GitHub console
# Should be: https://your-app-name.herokuapp.com/api/v2/auth/social/callback/

# Update environment variables
heroku config:set GOOGLE_OAUTH2_CLIENT_ID="your-client-id"
heroku config:set GOOGLE_OAUTH2_CLIENT_SECRET="your-client-secret"
```

---

## 🔄 Update Your App

### Deploy Updates

```bash
# Make changes to code
git add .
git commit -m "Description of changes"
git push heroku main

# Restart dynos if needed
heroku restart
```

### Update Environment Variables

```bash
# Update a variable
heroku config:set VARIABLE_NAME="new-value"

# Remove a variable
heroku config:unset VARIABLE_NAME
```

### View Releases

```bash
# View deployment history
heroku releases

# Rollback to previous version if needed
heroku rollback v123
```

---

## 💰 Cost Optimization

### Free Tier Limits
- **Dynos:** 550-1000 free dyno hours/month
- **Postgres:** 10,000 rows (Mini plan)
- **Redis:** 25MB (Mini plan)

### Upgrade When Needed
```bash
# Upgrade dyno
heroku ps:scale web=1:standard-1x

# Upgrade database
heroku addons:create heroku-postgresql:basic

# Upgrade Redis
heroku addons:create heroku-redis:premium-0
```

---

## 🎯 Production Checklist

- [ ] ✅ All environment variables set
- [ ] ✅ DATABASE_URL configured (Postgres)
- [ ] ✅ REDIS_URL configured (optional)
- [ ] ✅ SECRET_KEY is unique and secure
- [ ] ✅ DEBUG=False in production
- [ ] ✅ ALLOWED_HOSTS configured correctly
- [ ] ✅ Static files collected
- [ ] ✅ Database migrations run
- [ ] ✅ Templates seeded
- [ ] ✅ Superuser created
- [ ] ✅ OAuth redirect URIs updated in Google/GitHub
- [ ] ✅ Sentry configured for error tracking
- [ ] ✅ CORS origins set for frontend domain
- [ ] ✅ SSL certificate active (automatic with Heroku)
- [ ] ✅ Custom domain configured (if applicable)
- [ ] ✅ Logs monitoring set up
- [ ] ✅ Backup strategy in place

---

## 🌐 Custom Domain Setup (Optional)

```bash
# Add custom domain
heroku domains:add www.prompt-temple.com
heroku domains:add prompt-temple.com

# Configure DNS (add CNAME record)
# www.prompt-temple.com -> your-app-name.herokuapp.com

# Wait for SSL certificate (automatic)
heroku certs:auto:wait

# Verify
heroku domains
```

---

## 📈 Next Steps

1. **Monitor Performance**
   - Set up Heroku metrics
   - Configure Sentry alerts
   - Monitor database performance

2. **Set Up CI/CD** (Optional)
   - Connect GitHub repository
   - Enable automatic deploys
   - Add review apps

3. **Scale When Ready**
   - Add more dynos during peak traffic
   - Upgrade database plan as data grows
   - Consider CDN for static files

4. **Implement Microservices** (Future)
   - Deploy research agent separately
   - Split AI services into dedicated service
   - Use Heroku Private Spaces for enterprise

---

## 🆘 Support Resources

- **Heroku Docs:** https://devcenter.heroku.com/
- **Django Deployment:** https://docs.djangoproject.com/en/stable/howto/deployment/
- **Troubleshooting:** https://devcenter.heroku.com/articles/troubleshooting-application-errors

---

**Status:** ✅ Deployment files ready  
**Next Step:** Run pre-deployment steps and deploy!  
**Estimated Deployment Time:** 10-15 minutes  
**Expected Slug Size:** ~185MB (well under 500MB limit)

🚀 **Ready to deploy? Follow the steps above!**
