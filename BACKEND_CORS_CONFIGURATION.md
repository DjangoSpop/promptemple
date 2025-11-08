# Backend CORS Configuration Guide

## ✅ Production-Ready CORS Settings for PromptTemple

This document provides the **complete, production-ready CORS configuration** for the Django backend to work seamlessly with the Next.js frontend.

**Status**: ✅ **FULLY CONFIGURED AND PRODUCTION-READY**

---

## 🎯 Configuration Overview

**CORS is now fully configured** with:
- ✅ All custom headers supported (`x-request-id`, `x-client-version`, `x-operation-id`, `x-timestamp`, `x-correlation-id`)
- ✅ Proper origin whitelisting for development and production
- ✅ Credentials enabled for authentication
- ✅ Response headers exposed to frontend
- ✅ 24-hour preflight caching for performance
- ✅ Environment-based settings (development.py vs production.py)

---

## 📋 Current Configuration (Development)

**Location**: `promptcraft/settings/development.py`

```python
# ============================================================================
# CORS SETTINGS - Development Configuration
# ============================================================================

# Development Origins - Allow localhost and Android AVD
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",  # Alternative frontend port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://10.0.2.2:8000",   # Android AVD accessing Django
    "http://10.0.2.2:3000",   # Android AVD accessing frontend
    "http://0.0.0.0",
]

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# Allow all origins in development for easier testing
CORS_ALLOW_ALL_ORIGINS = True  # DEVELOPMENT ONLY!

# Custom headers that the frontend sends
CORS_ALLOWED_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
    # Custom Frontend Headers
    'x-client-version', 'x-request-id', 'x-operation-id',
    'x-timestamp', 'x-correlation-id', 'cache-control', 'pragma',
]

# Expose headers to the frontend
CORS_EXPOSE_HEADERS = [
    'x-request-id', 'x-correlation-id', 'x-client-version',
    'x-ratelimit-limit', 'x-ratelimit-remaining', 'x-ratelimit-reset',
    'content-type', 'content-length',
]

# Allowed HTTP methods
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']

# Preflight cache duration - 24 hours
CORS_PREFLIGHT_MAX_AGE = 86400
```

---

## 🚀 Production Configuration

**Location**: `promptcraft/settings/production.py`

```python
# ============================================================================
# CORS SETTINGS - Production Configuration
# ============================================================================

# Production Origins - HTTPS only for security
CORS_ALLOWED_ORIGINS = [
    "https://prompt-temple.com",
    "https://www.prompt-temple.com",
    "https://api.prompt-temple.com",
]

# DO NOT use CORS_ALLOW_ALL_ORIGINS in production
CORS_ALLOW_ALL_ORIGINS = False  # NEVER set to True in production!

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# Custom headers (same as development)
CORS_ALLOWED_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
    'x-client-version', 'x-request-id', 'x-operation-id',
    'x-timestamp', 'x-correlation-id', 'cache-control', 'pragma',
]

# Expose headers to frontend
CORS_EXPOSE_HEADERS = [
    'x-request-id', 'x-correlation-id', 'x-client-version',
    'x-ratelimit-limit', 'x-ratelimit-remaining', 'x-ratelimit-reset',
    'content-type', 'content-length',
]

# Allowed HTTP methods
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']

# Preflight cache duration - 24 hours
CORS_PREFLIGHT_MAX_AGE = 86400
```

---

## 🔧 How to Use

### Development Mode

**Set environment variable before starting server**:

```powershell
# Windows PowerShell
$env:DJANGO_ENVIRONMENT="development"
daphne --bind 0.0.0.0 --port 8000 promptcraft.asgi:application

# OR use manage.py
$env:DJANGO_ENVIRONMENT="development"
python manage.py runserver 0.0.0.0:8000
```

**Linux/macOS**:
```bash
export DJANGO_ENVIRONMENT=development
daphne --bind 0.0.0.0 --port 8000 promptcraft.asgi:application
```

### Production Mode

```powershell
# Windows PowerShell
$env:DJANGO_ENVIRONMENT="production"
daphne --bind 0.0.0.0 --port 8000 promptcraft.asgi:application
```

---

## ✅ Middleware Configuration

**Location**: `promptcraft/settings/base.py`

CORS middleware is automatically added if `django-cors-headers` is installed:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # ← Must be BEFORE CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # ... rest of middleware
]
```

**✅ Verified**: CorsMiddleware is positioned correctly (before CommonMiddleware)



---

## 🔍 Header Purposes

| Header | Purpose | Example | Required |
|--------|---------|---------|----------|
| `x-request-id` | Unique request identifier for logging/debugging | `a3f5d8c2-9e4b-4d3c-a1b2-c3d4e5f6a7b8` | ✅ Yes |
| `x-client-version` | Frontend version for compatibility checks | `1.0.0` | ✅ Yes |
| `x-operation-id` | Groups related requests into operations | `user-login-flow-123` | Optional |
| `x-timestamp` | Request timestamp for latency tracking | `1699000000000` | Optional |
| `x-correlation-id` | Distributed tracing across microservices | `trace-abc123` | Optional |
| `authorization` | JWT token for authenticated requests | `Bearer eyJ0eXAiOiJKV1QiLCJhbGc...` | For auth |

---

## 🛠️ Testing & Verification

### 1. Verify CORS Configuration

```bash
# Windows PowerShell
$env:DJANGO_ENVIRONMENT="development"
python manage.py verify_api --check-cors --verbose
```

**Expected Output**:
```
✓ Health check: HTTP 200 ✓ CORS enabled
✓ API root: HTTP 200 ✓ CORS enabled
✓ Core config: HTTP 200 ✓ CORS enabled
...
All endpoints should show ✓ CORS enabled
```

### 2. Test CORS Headers with curl

```bash
curl -X OPTIONS http://127.0.0.1:8000/api/v2/templates/ \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-request-id,x-client-version" \
  -v
```

**Expected Response Headers**:
```
Access-Control-Allow-Origin: http://localhost:3001
Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: x-request-id, x-client-version, authorization, ...
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 86400
```

### 3. Test with Frontend

```javascript
// Browser Console Test
fetch('http://127.0.0.1:8000/api/v2/templates/', {
  method: 'GET',
  headers: {
    'x-request-id': crypto.randomUUID(),
    'x-client-version': '1.0.0',
  },
  credentials: 'include',
})
.then(res => {
  console.log('✅ CORS working!');
  console.log('Response headers:', [...res.headers.entries()]);
  return res.json();
})
.then(data => console.log('Data:', data))
.catch(err => console.error('❌ Error:', err));
```

---

## 🔒 Security Best Practices

### Development
- ✅ `CORS_ALLOW_ALL_ORIGINS = True` - Acceptable for development
- ✅ Specific origins listed in `CORS_ALLOWED_ORIGINS`
- ✅ Enable credentials for authentication testing
- ⚠️ HTTP allowed (localhost/127.0.0.1)

### Production
- ✅ **NEVER** use `CORS_ALLOW_ALL_ORIGINS = True`
- ✅ Specify exact production domains (HTTPS only)
- ✅ Use environment variables for origins
- ✅ Implement rate limiting
- ✅ Log all CORS violations
- ✅ Monitor for unusual patterns
- ✅ Enable Sentry for error tracking

---

## � Environment Variable Configuration

**Recommended approach** using `.env` file:

```bash
# .env.development
DJANGO_ENVIRONMENT=development
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000
CORS_ALLOW_ALL_ORIGINS=True  # Development only!

# .env.production
DJANGO_ENVIRONMENT=production
CORS_ALLOWED_ORIGINS=https://prompt-temple.com,https://www.prompt-temple.com
CORS_ALLOW_ALL_ORIGINS=False  # NEVER True in production!
```

**Load in settings** (already configured):
```python
from decouple import config

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', 
    default='http://localhost:3000').split(',')

CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', 
    default=False, cast=bool)
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "Preflight response not successful"

**Solution**: Ensure `corsheaders.middleware.CorsMiddleware` is **first** in MIDDLEWARE.

### Issue 2: "Authorization header not allowed"

**Solution**: Add `'authorization'` to `CORS_ALLOWED_HEADERS`.

### Issue 3: "Credentials not included"

**Solution**: Set `CORS_ALLOW_CREDENTIALS = True` and frontend must use `credentials: 'include'`.

### Issue 4: "Wildcard origin with credentials"

**Solution**: Cannot use `*` with credentials. Specify exact origins.

---

## 📝 Environment Variables

Use environment variables for flexibility:

```python
# settings.py
import os

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 
    'http://localhost:3000,http://127.0.0.1:3000').split(',')

CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'False').lower() == 'true'
```

`.env` file:
```bash
# Development
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_ALL_ORIGINS=False

# Production
CORS_ALLOWED_ORIGINS=https://prompttemple.io,https://app.prompttemple.io
CORS_ALLOW_ALL_ORIGINS=False
```

---

## ✅ Verification Checklist

- [ ] `django-cors-headers` installed
- [ ] `corsheaders` in `INSTALLED_APPS`
- [ ] `CorsMiddleware` at top of `MIDDLEWARE`
- [ ] `CORS_ALLOWED_ORIGINS` configured
- [ ] All custom headers in `CORS_ALLOWED_HEADERS`
- [ ] `CORS_ALLOW_CREDENTIALS = True`
- [ ] `CORS_ALLOW_ALL_ORIGINS = False` in production
- [ ] Tested with curl
- [ ] Tested with frontend
- [ ] No CORS errors in browser console

---

## 🔗 Additional Resources

- [django-cors-headers Documentation](https://github.com/adamchainz/django-cors-headers)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Django Security Settings](https://docs.djangoproject.com/en/stable/ref/settings/#secure-cross-origin-opener-policy)

---

## 📞 Support

If you encounter issues with this configuration:

1. Check Django logs for CORS-related errors
2. Verify middleware order
3. Test with curl first
4. Check browser Network tab for preflight requests
5. Ensure frontend is sending headers correctly

---

**Last Updated**: November 2, 2025  
**Version**: 1.0.0  
**Maintained by**: PromptTemple DevOps Team
