# 🚀 Heroku Deployment Quick Start

## ✅ Pre-Flight Checklist

All deployment files are ready:
- ✅ `requirements-heroku.txt` - Optimized dependencies (~185MB)
- ✅ `.slugignore` - Excludes large files
- ✅ `Procfile` - Gunicorn configuration
- ✅ `runtime.txt` - Python 3.11.9
- ✅ `promptcraft/settings/heroku.py` - Production settings
- ✅ `.gitignore` - Updated for large datasets

**Estimated Slug Size:** ~185MB (✅ Under 500MB limit)

---

## 🚀 Deploy to Heroku (5 Minutes)

### 1. Login to Heroku
```bash
heroku login
```

### 2. Create App
```bash
# Choose one:
heroku create prompt-temple-mvp  # Custom name
# OR
heroku create  # Auto-generate name
```

### 3. Add Addons
```bash
# PostgreSQL database (required)
heroku addons:create heroku-postgresql:mini

# Redis for caching (optional but recommended)
heroku addons:create heroku-redis:mini
```

### 4. Set Environment Variables
```bash
# Core settings
heroku config:set DJANGO_SETTINGS_MODULE=promptcraft.settings.heroku
heroku config:set DJANGO_ENVIRONMENT=heroku
heroku config:set SECRET_KEY="$(openssl rand -base64 32)"
heroku config:set DEBUG=False

# AI Services
heroku config:set DEEPSEEK_API_KEY="sk-fad996d33334443dab24fcd669653814"
heroku config:set DEEPSEEK_BASE_URL="https://api.deepseek.com"

# Google OAuth
heroku config:set GOOGLE_OAUTH2_CLIENT_ID="1088607409316-tshcdh28ka5v0gpjnp8j040gm6lcar2h.apps.googleusercontent.com"
heroku config:set GOOGLE_OAUTH2_CLIENT_SECRET="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"

# GitHub OAuth
heroku config:set GITHUB_CLIENT_ID="Ov23liEYkjrWCP9zoHNF"
heroku config:set GITHUB_CLIENT_SECRET="ecad6c4f421187b2f6b8a032df90647d463271d8"

# Stripe (update with your keys)
heroku config:set STRIPE_SECRET_KEY="your-stripe-secret-key"

# Sentry (optional)
heroku config:set SENTRY_DSN="your-sentry-dsn"
```

### 5. Rename Requirements File
```bash
# Windows PowerShell
Move-Item requirements.txt requirements-old.txt -Force
Move-Item requirements-heroku.txt requirements.txt -Force

# Linux/Mac
mv requirements.txt requirements-old.txt
mv requirements-heroku.txt requirements.txt
```

### 6. Commit and Deploy
```bash
git add .
git commit -m "Heroku optimization: Deploy under 500MB"
git push heroku main
```

### 7. Run Migrations and Seed
```bash
# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# Seed templates (using existing seed command)
heroku run python manage.py seed_templates
```

### 8. Open Your App
```bash
heroku open
```

---

## 🔍 Quick Verification

```bash
# Check dyno status
heroku ps

# View logs
heroku logs --tail

# Check slug size (should be ~185MB)
heroku releases:info

# Test API
curl https://your-app.herokuapp.com/api/v2/health/
```

---

## ⚡ One-Command Deploy (Windows PowerShell)

```powershell
# Set variables
$APP_NAME = "prompt-temple-mvp"
$SECRET_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})

# Create and configure
heroku create $APP_NAME
heroku addons:create heroku-postgresql:mini -a $APP_NAME
heroku addons:create heroku-redis:mini -a $APP_NAME
heroku config:set DJANGO_SETTINGS_MODULE=promptcraft.settings.heroku -a $APP_NAME
heroku config:set SECRET_KEY=$SECRET_KEY -a $APP_NAME
heroku config:set DEEPSEEK_API_KEY="sk-fad996d33334443dab24fcd669653814" -a $APP_NAME

# Deploy
Move-Item requirements.txt requirements-old.txt -Force
Move-Item requirements-heroku.txt requirements.txt -Force
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Setup
heroku run python manage.py migrate -a $APP_NAME
heroku run python manage.py seed_templates -a $APP_NAME

# Open
heroku open -a $APP_NAME
```

---

## 🐛 Common Issues

### Issue: Slug too large
**Solution:** Already handled! Using optimized requirements (~185MB)

### Issue: Database error
```bash
heroku pg:reset DATABASE
heroku run python manage.py migrate
```

### Issue: Static files not loading
```bash
heroku run python manage.py collectstatic --noinput
```

### Issue: App crashed (H10)
```bash
heroku logs --tail
# Check Procfile uses: gunicorn promptcraft.wsgi --bind 0.0.0.0:$PORT
```

---

## 📊 What Was Optimized

| Removed | Size Saved |
|---------|-----------|
| ML packages (torch, transformers) | ~1.6GB |
| Data science (pandas, numpy, scipy) | ~750MB |
| Vector DBs (chromadb, faiss) | ~300MB |
| Celery + Channels | ~130MB |
| **Total Savings** | **~2.8GB** |

**Final Size:** ~185MB ✅

---

## 🎯 Production Checklist

- [x] Optimized requirements (~185MB)
- [x] .slugignore configured
- [x] Procfile using Gunicorn
- [x] Settings configured for Heroku
- [x] PostgreSQL addon
- [x] Redis addon (optional)
- [ ] Environment variables set
- [ ] SECRET_KEY generated
- [ ] OAuth redirect URIs updated
- [ ] Deployed to Heroku
- [ ] Migrations run
- [ ] Templates seeded
- [ ] Custom domain (optional)

---

## 🔗 Useful Commands

```bash
# View config
heroku config

# Database info
heroku pg:info

# Connect to database
heroku pg:psql

# View Redis info
heroku redis:info

# Restart app
heroku restart

# Scale dynos
heroku ps:scale web=1

# View releases
heroku releases

# Rollback
heroku rollback v123
```

---

**Ready to deploy!** Follow steps 1-8 above. 🚀
