# URGENT: Apply Settings Fix Before Testing

## 🚨 Critical Issue Fixed

**Problem**: CORS headers were not being returned despite correct configuration  
**Root Cause**: Django was loading the old `settings.py` file instead of the modular `settings/` package  
**Solution**: Updated `manage.py`, `asgi.py`, and `wsgi.py` to use environment-based settings module selection

## ✅ What Was Changed

### 1. `manage.py` ✅ DONE
- Now uses environment variable `DJANGO_ENVIRONMENT` to select settings module
- Default: `development` (uses `promptcraft.settings.development`)

### 2. `asgi.py` ✅ DONE  
- Updated from hardcoded `production` settings
- Now respects `DJANGO_ENVIRONMENT` variable
- Supports both development and production

### 3. `wsgi.py` ✅ DONE
- Updated from generic settings
- Now uses environment-specific settings module

## 🚀 How to Use (IMPORTANT!)

### On Windows PowerShell:

```powershell
# Development with runserver
$env:DJANGO_ENVIRONMENT="development"
python manage.py runserver 0.0.0.0:8000

# OR with Daphne (WebSocket support)
$env:DJANGO_ENVIRONMENT="development"
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

### On Linux/macOS:

```bash
# Development with runserver
export DJANGO_ENVIRONMENT=development
python manage.py runserver 0.0.0.0:8000

# OR with Daphne (WebSocket support)
export DJANGO_ENVIRONMENT=development
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

### Production:

```bash
# Using WSGI (Gunicorn)
export DJANGO_ENVIRONMENT=production
gunicorn promptcraft.wsgi:application --bind 0.0.0.0:8000

# Using ASGI (Daphne)
export DJANGO_ENVIRONMENT=production
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

## 🔍 Verify the Fix

### Step 1: Test CORS Headers

```bash
curl -X OPTIONS http://127.0.0.1:8000/api/v2/templates/ \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**Expected** (should show CORS headers):
```
< HTTP/1.1 200 OK
< Access-Control-Allow-Origin: http://localhost:3001
< Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD
< Access-Control-Allow-Headers: accept, accept-encoding, ... authorization ...
```

### Step 2: Run Verification Command

```bash
# Set environment first!
export DJANGO_ENVIRONMENT=development  # Linux/Mac
# OR: $env:DJANGO_ENVIRONMENT="development"  # Windows PowerShell

python manage.py verify_api --check-cors --verbose
```

**Expected** (all should show ✓ CORS enabled):
```
✓ Health check: HTTP 200 (CORS: http://localhost:3001)
✓ Core config: HTTP 200 (CORS: http://localhost:3001)
✓ Templates list: HTTP 200 (CORS: http://localhost:3001)
✓ AI Assistant: HTTP 200 (CORS: http://localhost:3001)
✓ Analytics dashboard: HTTP 200 (CORS: http://localhost:3001)
```

### Step 3: Test Frontend Integration

1. **Restart backend** with environment variable set:
   ```bash
   export DJANGO_ENVIRONMENT=development
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Start frontend** (in another terminal):
   ```bash
   cd ../my_prmpt_frontend
   npm start
   ```

3. **Open browser** to http://localhost:3001

4. **Check browser console** (F12):
   - Should see NO CORS errors
   - API calls should succeed
   - Network tab should show CORS headers

## 📋 Settings Module Resolution

When you start the server, Django will:

1. **Check `DJANGO_ENVIRONMENT` env variable**
   - If `development` → loads `promptcraft/settings/development.py`
   - If `production` → loads `promptcraft/settings/production.py`
   - If `testing` → loads `promptcraft/settings/testing.py`
   - Default: `development`

2. **Load base settings** from `promptcraft/settings/base.py`
   - Middleware configuration
   - INSTALLED_APPS
   - CORS setup

3. **Apply environment-specific overrides**
   - Development: DEBUG=True, CORS_ALLOW_ALL_ORIGINS=True
   - Production: DEBUG=False, specific CORS domains
   - Testing: Minimal configuration

## 📂 Project Structure After Fix

```
promptcraft/
├── __init__.py
├── manage.py              ← ✅ UPDATED
├── promptcraft/
│   ├── settings.py        ← OLD (no longer used)
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py        ← CORS middleware setup
│   │   ├── development.py ← DEBUG=True, CORS_ALLOW_ALL_ORIGINS=True
│   │   ├── production.py  ← DEBUG=False, specific domains
│   │   └── testing.py
│   ├── asgi.py            ← ✅ UPDATED
│   ├── wsgi.py            ← ✅ UPDATED
│   ├── urls.py
│   └── celery.py
└── apps/
    ├── core/
    ├── templates/
    ├── ai_services/
    ├── analytics/
    └── ...
```

## 🔧 Troubleshooting

### CORS Still Not Working?

**1. Check environment variable is set:**

```bash
# Linux/Mac
echo $DJANGO_ENVIRONMENT

# Windows PowerShell
echo $env:DJANGO_ENVIRONMENT

# Windows CMD
echo %DJANGO_ENVIRONMENT%
```

If empty, you didn't set it! Try again:
```bash
export DJANGO_ENVIRONMENT=development
python manage.py runserver
```

**2. Check which settings is loaded:**

```bash
python manage.py shell
```

```python
from django.conf import settings
print(f"Loaded settings: {settings.SETTINGS_MODULE}")
print(f"DEBUG: {settings.DEBUG}")
print(f"CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}")
```

Expected output:
```
Loaded settings: promptcraft.settings.development
DEBUG: True
CORS_ALLOW_ALL_ORIGINS: True
```

**3. Clear Python cache:**

```bash
# Linux/Mac
find . -type d -name __pycache__ -exec rm -r {} +

# Windows - use GUI or:
Get-ChildItem -Path . -Filter __pycache__ -Recurse -Force | Remove-Item -Recurse -Force
```

**4. Restart server:**

Stop the server (Ctrl+C) and restart it WITH the environment variable:
```bash
export DJANGO_ENVIRONMENT=development
python manage.py runserver 0.0.0.0:8000
```

### Still Getting 401 Errors?

That's different from CORS - means authentication is working but token is missing:
- Check you're logged in
- Check token is in `localStorage.getItem('accessToken')`
- See [AUTHENTICATION_GUIDE.md](./AUTHENTICATION_GUIDE.md)

### Getting HTML Response Instead of JSON?

Check the Network tab response - if it starts with `<!DOCTYPE html>`, there's a 500 error on backend:
- Check backend terminal for error messages
- Look for stack traces
- Check database connection

## 📝 What Each Settings File Does

### `base.py` (Shared)
- INSTALLED_APPS configuration
- Middleware setup (CORS, Auth, etc.)
- CORS header configuration
- Database engine selection
- JWT configuration
- Email backend

### `development.py` (Inherits from base.py)
- DEBUG = True
- CORS_ALLOW_ALL_ORIGINS = True
- SQLite database (default)
- Email console output
- Email backend = console (logs to console)
- No rate limiting on API

### `production.py` (Inherits from base.py)
- DEBUG = False  
- CORS_ALLOW_ALL_ORIGINS = False (specific domains only)
- PostgreSQL database (required)
- Email via SMTP
- Sentry error tracking enabled
- Rate limiting enabled
- Security headers enforced

### `testing.py` (Inherits from base.py)
- DEBUG = True
- CORS_ALLOW_ALL_ORIGINS = True
- SQLite in-memory database
- Email disabled
- Minimal logging

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] Environment variable `DJANGO_ENVIRONMENT=production` will be set on server
- [ ] `.env` file configured with production database
- [ ] `DEBUG=False` in production settings
- [ ] CORS_ALLOWED_ORIGINS updated for production domain
- [ ] Static files collected: `python manage.py collectstatic`
- [ ] Database migrations applied: `python manage.py migrate`
- [ ] Gunicorn or Daphne installed for production WSGI/ASGI
- [ ] Tests passing: `python manage.py test`
- [ ] CORS verified with curl test before deployment

## 🎯 Common Commands (With Environment Variable)

```bash
# Run development server
export DJANGO_ENVIRONMENT=development
python manage.py runserver 0.0.0.0:8000

# Run tests
export DJANGO_ENVIRONMENT=testing
python manage.py test

# Create migrations
export DJANGO_ENVIRONMENT=development
python manage.py makemigrations

# Apply migrations
export DJANGO_ENVIRONMENT=development
python manage.py migrate

# Create superuser
export DJANGO_ENVIRONMENT=development
python manage.py createsuperuser

# Django shell
export DJANGO_ENVIRONMENT=development
python manage.py shell

# Verify API
export DJANGO_ENVIRONMENT=development
python manage.py verify_api --check-cors

# Collect static files (production)
export DJANGO_ENVIRONMENT=production
python manage.py collectstatic --noinput
```

## 📞 Still Having Issues?

1. **Read** [CORS_FIX_GUIDE.md](./CORS_FIX_GUIDE.md) - detailed explanation
2. **Debug with** [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md)
3. **Check** [README_INTEGRATION.md](./README_INTEGRATION.md) for overview
4. **Test** endpoints at `/api/schema/swagger-ui/` when server is running

---

**Status**: ✅ FIX APPLIED - Ready to test  
**Next Step**: Set `DJANGO_ENVIRONMENT=development` and restart server  
**Expected Result**: CORS headers returned, frontend-backend integration working

