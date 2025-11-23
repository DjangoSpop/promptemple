# Heroku Deployment Guide - Prompt Temple Backend

Complete deployment guide for Django + DRF + LangChain backend on Heroku (single dyno, 500MB limit).

## Prerequisites

- Heroku CLI installed
- Git repository initialized
- Python 3.11+ application
- Redis add-on (hobby-dev tier)

---

## Quick Start

```bash
# Login to Heroku
heroku login

# Create Heroku app
heroku create prompt-temple-backend

# Add Redis add-on
heroku addons:create heroku-redis:hobby-dev

# Set buildpack
heroku buildpacks:set heroku/python
```

---

## Environment Variables

### Required Configuration

```bash
# Django core settings
heroku config:set DJANGO_SETTINGS_MODULE=promptcraft.settings.production
heroku config:set SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
heroku config:set DEBUG=False

# Allowed hosts and CORS
heroku config:set ALLOWED_HOSTS="prompt-temple-backend.herokuapp.com,www.prompt-temple.com"
heroku config:set CORS_ALLOWED_ORIGINS="https://www.prompt-temple.com"

# Database (Heroku provides DATABASE_URL automatically)
# REDIS_URL is auto-set by heroku-redis addon

# LangChain/LangSmith (optional - set if you have keys)
heroku config:set LANGCHAIN_TRACING_V2=true
heroku config:set LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
heroku config:set LANGCHAIN_API_KEY=your_langsmith_api_key
heroku config:set LANGSMITH_PROJECT=prompt-temple

# AI providers
heroku config:set DEEPSEEK_API_KEY=your_deepseek_key
heroku config:set OPENAI_API_KEY=your_openai_key  # optional fallback

# Feature flags
heroku config:set FEATURE_RAG=false  # Keep disabled for 500MB limit
```

### Get Current Redis URL

```bash
heroku config:get REDIS_URL
```

---

## Procfile Configuration

Create or verify `Procfile` in project root:

```
web: gunicorn promptcraft.wsgi --log-file - --workers 2 --threads 2 --timeout 30
release: python manage.py migrate --noinput
```

**Notes:**
- `release` phase runs migrations automatically on deploy
- 2 workers × 2 threads = 4 concurrent requests (optimal for hobby dyno)
- 30s timeout prevents long-running requests from blocking

---

## Runtime Configuration

Create `runtime.txt` in project root:

```
python-3.11.9
```

---

## Requirements Management

Ensure `requirements.txt` is lean (under 500MB slug size):

```bash
# Core dependencies only
Django==4.2.7
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
django-redis==5.4.0
django-cors-headers==4.3.1
channels==4.0.0
channels-redis==4.1.0
celery==5.3.4
langchain==0.1.0
langchain-community==0.0.10
openai==1.10.0
```

**Optimization Tips:**
- Remove unused packages
- Use `pipdeptree` to find bloated dependencies
- Consider moving heavy ML libs (numpy, scipy) behind feature flags

---

## Database Migration

```bash
# Run migrations manually (first time)
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# Seed sample prompts
heroku run python manage.py seed_prompts_small
```

---

## Production Settings

Create `promptcraft/settings/production.py`:

```python
from .settings import *
import os
import dj_database_url

DEBUG = False

# Security
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES['default'] = dj_database_url.config(conn_max_age=600)

# Redis
REDIS_URL = os.environ.get('REDIS_URL')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
```

---

## Deploy Steps

### 1. Initial Deployment

```bash
# Add Heroku remote (if not done)
heroku git:remote -a prompt-temple-backend

# Ensure all files are committed
git add .
git commit -m "Prepare for Heroku deployment"

# Deploy
git push heroku main

# Check logs
heroku logs --tail
```

### 2. Verify Deployment

```bash
# Check app status
heroku ps

# Test health endpoint
curl https://prompt-temple-backend.herokuapp.com/health/

# Test Redis health
curl https://prompt-temple-backend.herokuapp.com/health/redis/

# Open app
heroku open
```

### 3. Run Migrations & Seed Data

```bash
# Migrations should run automatically via release phase
# If needed, run manually:
heroku run python manage.py migrate

# Seed prompts
heroku run python manage.py seed_prompts_small

# Verify data
heroku run python manage.py shell
>>> from apps.prompt_history.models import PromptHistory
>>> PromptHistory.objects.count()
```

---

## Health Checks

### 1. Basic Health

```bash
curl https://prompt-temple-backend.herokuapp.com/health/
```

**Expected Response:**
```json
{
  "status": "ok"
}
```

### 2. Redis Health

```bash
curl https://prompt-temple-backend.herokuapp.com/health/redis/
```

**Expected Response:**
```json
{
  "ok": true
}
```

**Error Response (503):**
```json
{
  "ok": false,
  "error": "cache_unreachable"
}
```

### 3. API Root

```bash
curl https://prompt-temple-backend.herokuapp.com/api/
```

---

## Monitoring & Debugging

### View Logs

```bash
# Tail logs
heroku logs --tail

# Last 200 lines
heroku logs -n 200

# Filter by source
heroku logs --source app
```

### Check Dyno Status

```bash
heroku ps
heroku ps:scale web=1
```

### Run Commands

```bash
# Django shell
heroku run python manage.py shell

# Database shell
heroku run python manage.py dbshell

# Custom management commands
heroku run python manage.py seed_prompts_small
```

### Restart Dyno

```bash
heroku ps:restart
```

---

## Performance Optimization

### 1. Slug Size Management

```bash
# Check slug size
heroku builds:info

# Remove unnecessary files via .slugignore
echo "*.md" >> .slugignore
echo "docs/" >> .slugignore
echo "tests/" >> .slugignore
```

### 2. Memory Optimization

Monitor memory usage:

```bash
heroku logs --dyno=web.1 | grep "Memory"
```

**Tips:**
- Use gunicorn with 2 workers max
- Disable heavyweight features (RAG, large embeddings)
- Lazy-load AI models
- Use Redis for caching

### 3. Response Time Optimization

- Enable Redis caching for frequently accessed data
- Use database indexes (already added to PromptHistory)
- Implement pagination (DRF default: 20 items/page)
- Cache API responses with `@cache_page(300)`

---

## Troubleshooting

### Redis Connection Errors

```bash
# Verify Redis add-on
heroku addons:info heroku-redis

# Get Redis credentials
heroku config:get REDIS_URL

# Test connection
heroku run python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

### Migration Errors

```bash
# Check migration status
heroku run python manage.py showmigrations

# Force migrate
heroku run python manage.py migrate --run-syncdb

# Rollback specific migration
heroku run python manage.py migrate prompt_history 0001
```

### 500 Internal Server Errors

```bash
# Enable debug temporarily (NOT for production use!)
heroku config:set DEBUG=True
heroku restart
# Check error details
curl https://prompt-temple-backend.herokuapp.com/api/v2/history/
# Disable debug
heroku config:unset DEBUG
```

### Memory Errors (R14)

```bash
# Check memory usage
heroku logs --ps web | grep "R14"

# Reduce workers
# Update Procfile: web: gunicorn promptcraft.wsgi --workers 1 --threads 4
git add Procfile
git commit -m "Reduce workers for memory"
git push heroku main
```

---

## CI/CD Setup (Optional)

### GitHub Actions Deployment

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Heroku

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: akhileshns/heroku-deploy@v3.12.14
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "prompt-temple-backend"
          heroku_email: "your@email.com"
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale to 2 dynos (requires paid plan)
heroku ps:scale web=2

# Scale down
heroku ps:scale web=1
```

### Vertical Scaling

```bash
# Upgrade dyno type
heroku ps:type performance-m

# Check current type
heroku ps
```

---

## Backup & Recovery

### Database Backups

```bash
# Create manual backup
heroku pg:backups:capture

# List backups
heroku pg:backups

# Download backup
heroku pg:backups:download

# Restore backup
heroku pg:backups:restore
```

### Configuration Backup

```bash
# Export all config vars
heroku config -s > .env.heroku.backup

# Restore config vars
cat .env.heroku.backup | xargs heroku config:set
```

---

## Cost Optimization

### Hobby Dyno Plan ($7/month)
- 1 dyno, 512MB RAM
- No SSL required (Heroku provides)
- No auto-sleep (unlike free tier)

### Redis Addon ($0-15/month)
- hobby-dev: Free, 25MB
- mini: $3/month, 100MB
- hobby: $15/month, 1GB

### Cost Estimate:
- Hobby dyno: $7/month
- Redis hobby-dev: $0/month
- Total: **$7/month**

---

## Production Checklist

- [ ] `DEBUG=False` in production settings
- [ ] `SECRET_KEY` set to random secure value
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] `CORS_ALLOWED_ORIGINS` includes frontend domain
- [ ] Redis addon provisioned and `REDIS_URL` set
- [ ] Migrations applied: `heroku run python manage.py migrate`
- [ ] Sample data seeded: `heroku run python manage.py seed_prompts_small`
- [ ] Health checks pass: `/health/` and `/health/redis/`
- [ ] SSL certificate active (automatic on Heroku)
- [ ] Logging configured and monitored
- [ ] LangSmith tracing configured (if using AI features)
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured (Heroku Dashboard or Sentry)

---

## Support & Resources

- Heroku Dev Center: https://devcenter.heroku.com/
- Django Deployment: https://docs.djangoproject.com/en/4.2/howto/deployment/
- Heroku Redis: https://devcenter.heroku.com/articles/heroku-redis
- LangSmith Docs: https://docs.smith.langchain.com/

---

## Quick Reference Commands

```bash
# Deploy
git push heroku main

# Logs
heroku logs --tail

# Restart
heroku ps:restart

# Migrations
heroku run python manage.py migrate

# Shell
heroku run python manage.py shell

# Config
heroku config
heroku config:set KEY=value

# Health
curl https://prompt-temple-backend.herokuapp.com/health/
curl https://prompt-temple-backend.herokuapp.com/health/redis/
```
