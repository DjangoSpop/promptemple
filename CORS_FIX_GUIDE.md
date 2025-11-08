# CORS Configuration Fix - Critical Issue Resolution

## Problem Identified

**Status**: ❌ CORS headers NOT being returned despite configuration

**Root Cause**: Django settings conflict
- Two settings modules exist: `settings.py` (file) and `settings/` (package)
- Python was loading the old `settings.py` instead of the modular `settings/` package
- The old `settings.py` file doesn't have proper CORS middleware configuration
- This caused OPTIONS requests to NOT receive CORS headers

## The Fix

### 1. Updated `manage.py` (✅ Done)

Changed from:
```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings")
```

To:
```python
environment = os.environ.get("DJANGO_ENVIRONMENT", "development")
settings_module = f"promptcraft.settings.{environment}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
```

**Why**: This ensures Django loads the correct settings module from `promptcraft/settings/development.py`, `production.py`, or `testing.py` instead of the old `promptcraft/settings.py` file.

### 2. Update ASGI/WSGI Applications

Both `asgi.py` and `wsgi.py` need the same fix:

**File**: `promptcraft/asgi.py`
```python
# OLD
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings")

# NEW
environment = os.environ.get("DJANGO_ENVIRONMENT", "development")
settings_module = f"promptcraft.settings.{environment}"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
```

**File**: `promptcraft/wsgi.py`
```python
# Same change as above
```

### 3. Environment Variable Configuration

Set the environment variable when running the server:

```bash
# Development (default)
export DJANGO_ENVIRONMENT=development
python manage.py runserver 0.0.0.0:8000

# Or with Daphne (WebSocket support)
export DJANGO_ENVIRONMENT=development
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application

# Production
export DJANGO_ENVIRONMENT=production
gunicorn promptcraft.wsgi:application --bind 0.0.0.0:8000
```

**On Windows**:
```powershell
# PowerShell
$env:DJANGO_ENVIRONMENT="development"
python manage.py runserver 0.0.0.0:8000

# Or Command Prompt
set DJANGO_ENVIRONMENT=development
python manage.py runserver 0.0.0.0:8000
```

## Verification Steps

After applying the fix, verify CORS is working:

### 1. Restart Backend Server

```bash
# Make sure to set environment variable first!
export DJANGO_ENVIRONMENT=development  # Linux/Mac
# or: set DJANGO_ENVIRONMENT=development  # Windows

python manage.py runserver 0.0.0.0:8000
```

### 2. Test CORS Headers

```bash
# Test preflight request
curl -X OPTIONS http://127.0.0.1:8000/api/v2/templates/ \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**Expected output** (should show these headers):
```
< HTTP/1.1 200 OK
< Access-Control-Allow-Origin: http://localhost:3001
< Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD
< Access-Control-Allow-Headers: accept, accept-encoding, accept-language, authorization, cache-control, content-type, dnt, origin, pragma, user-agent, x-csrftoken, x-requested-with, x-client-version, x-client-name
< Access-Control-Max-Age: 86400
```

### 3. Run Verification Command

```bash
python manage.py verify_api --check-cors --verbose
```

**Expected output** (should show ✓ CORS enabled):
```
✓ Health check: HTTP 200 (CORS: http://localhost:3001)
✓ Core config: HTTP 200 (CORS: http://localhost:3001)
✓ Templates list: HTTP 200 (CORS: http://localhost:3001)
... etc
```

### 4. Test in Browser

1. Open `http://localhost:3001` in browser
2. Open DevTools (F12)
3. Go to Console tab
4. You should see NO CORS errors
5. Make API call and check it succeeds

## Settings Module Structure

```
promptcraft/
├── settings.py                 ← OLD FILE (should be deprecated)
├── settings/
│   ├── __init__.py            ← Chooses which settings to load
│   ├── base.py                ← Shared settings
│   ├── development.py         ← Development-specific (DEBUG=True, CORS=True)
│   ├── production.py          ← Production-specific (DEBUG=False)
│   └── testing.py             ← Testing-specific
├── asgi.py                    ← WebSocket application (needs fix)
├── wsgi.py                    ← WSGI application (needs fix)
└── urls.py                    ← URL routing
```

### Settings Resolution Priority

1. **Check `DJANGO_ENVIRONMENT` env variable**
   - If set to "production" → uses `promptcraft/settings/production.py`
   - If set to "testing" → uses `promptcraft/settings/testing.py`
   - Otherwise → uses `promptcraft/settings/development.py` (default)

2. **Load base settings from `base.py`**
   - Contains CORS configuration
   - Contains middleware setup
   - Contains INSTALLED_APPS

3. **Override with environment-specific settings**
   - Development: DEBUG=True, CORS_ALLOW_ALL_ORIGINS=True
   - Production: DEBUG=False, specific CORS domains
   - Testing: Minimal configuration

## Development Settings (Working Correctly)

File: `promptcraft/settings/development.py`

```python
DEBUG = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  # Allow all origins in development

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'accept-language',
    'authorization',
    'cache-control',
    'content-type',
    'dnt',
    'origin',
    'pragma',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-client-version',
    'x-client-name',
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
    'HEAD',
]
```

## Base Settings (CORS Middleware)

File: `promptcraft/settings/base.py`

```python
# Conditionally add corsheaders if installed
try:
    import corsheaders
    THIRD_PARTY_APPS.append('corsheaders')
except ImportError:
    pass

# Add CORS middleware FIRST, before all other middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
]

if 'corsheaders' in THIRD_PARTY_APPS:
    MIDDLEWARE.append("corsheaders.middleware.CorsMiddleware")

MIDDLEWARE.extend([
    "django.contrib.sessions.middleware.SessionMiddleware",
    # ... other middleware
])
```

## Testing the Fix

### Quick Test Script

Create `test_cors.py`:
```python
#!/usr/bin/env python
import os
import django

# Set environment before Django setup
os.environ.setdefault("DJANGO_ENVIRONMENT", "development")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings.development")

django.setup()

from django.conf import settings

print("=" * 60)
print("DJANGO SETTINGS VERIFICATION")
print("=" * 60)

print(f"\n✓ DEBUG: {settings.DEBUG}")
print(f"✓ CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}")
print(f"✓ CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}")
print(f"✓ corsheaders in INSTALLED_APPS: {'corsheaders' in settings.INSTALLED_APPS}")

middleware_list = settings.MIDDLEWARE
cors_index = -1
session_index = -1

for i, middleware in enumerate(middleware_list):
    if 'CorsMiddleware' in middleware:
        cors_index = i
    if 'SessionMiddleware' in middleware:
        session_index = i

print(f"\n✓ CorsMiddleware position: {cors_index}")
print(f"✓ SessionMiddleware position: {session_index}")

if cors_index >= 0 and session_index >= 0:
    if cors_index < session_index:
        print("✅ CORS middleware is BEFORE SessionMiddleware (CORRECT)")
    else:
        print("❌ CORS middleware is AFTER SessionMiddleware (WRONG)")
else:
    print("❌ Middleware not found")

print("\n✓ MIDDLEWARE ORDER:")
for i, middleware in enumerate(middleware_list):
    marker = "→ CORS" if 'CorsMiddleware' in middleware else "→ SESSION" if 'SessionMiddleware' in middleware else ""
    print(f"  {i}: {middleware} {marker}")

print("\n" + "=" * 60)
```

Run it:
```bash
export DJANGO_ENVIRONMENT=development
python test_cors.py
```

Expected output:
```
============================================================
DJANGO SETTINGS VERIFICATION
============================================================

✓ DEBUG: True
✓ CORS_ALLOW_ALL_ORIGINS: True
✓ CORS_ALLOWED_ORIGINS: ['http://localhost:3000', ...]
✓ corsheaders in INSTALLED_APPS: True

✓ CorsMiddleware position: 1
✓ SessionMiddleware position: 2
✅ CORS middleware is BEFORE SessionMiddleware (CORRECT)

✓ MIDDLEWARE ORDER:
  0: django.middleware.security.SecurityMiddleware
  1: corsheaders.middleware.CorsMiddleware → CORS
  2: django.contrib.sessions.middleware.SessionMiddleware → SESSION
  ...
```

## Troubleshooting

### Still Not Working?

1. **Verify environment variable is set:**
   ```bash
   # Linux/Mac
   echo $DJANGO_ENVIRONMENT
   
   # Windows PowerShell
   echo $env:DJANGO_ENVIRONMENT
   
   # Windows CMD
   echo %DJANGO_ENVIRONMENT%
   ```

2. **Check which settings is loaded:**
   ```bash
   python manage.py shell
   from django.conf import settings
   print(settings.SETTINGS_MODULE)
   ```

3. **Clear Python cache:**
   ```bash
   find . -type d -name __pycache__ -exec rm -r {} +  # Linux/Mac
   # Or manually delete all __pycache__ folders
   ```

4. **Restart server:**
   Make sure to set the environment variable BEFORE starting the server:
   ```bash
   export DJANGO_ENVIRONMENT=development
   python manage.py runserver 0.0.0.0:8000
   ```

### Old settings.py File

The old `promptcraft/settings.py` file can now be safely ignored or removed. All actual settings are in `promptcraft/settings/` directory.

If you want to clean up (optional):
```bash
# Rename old settings file (backup)
mv promptcraft/settings.py promptcraft/settings.py.bak

# Or delete if you're sure it's not needed
rm promptcraft/settings.py
```

## Summary of Changes

| File | Change | Purpose |
|------|--------|---------|
| `manage.py` | ✅ Updated | Use environment-based settings module |
| `asgi.py` | ⏳ Needs update | Same fix as manage.py |
| `wsgi.py` | ⏳ Needs update | Same fix as manage.py |
| `promptcraft/settings.py` | ℹ️ Old file | No longer needed, kept for compatibility |
| `promptcraft/settings/` | ✅ Working | Correct modular settings structure |

## Next Steps

1. **Apply this fix** to `asgi.py` and `wsgi.py`
2. **Set environment variable** when running server
3. **Restart backend** server
4. **Test CORS** with curl or browser
5. **Run verification** command
6. **Test frontend** - should see no CORS errors

---

**Status**: Ready to implement ✅
**Priority**: Critical - Blocks all frontend-backend communication
**Time to fix**: 5 minutes

Questions? Check [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md) or [README_INTEGRATION.md](./README_INTEGRATION.md)
