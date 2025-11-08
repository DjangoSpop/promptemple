# PromptCraft Frontend-Backend Integration Setup Guide

## Overview

This guide provides step-by-step instructions for setting up and integrating the PromptCraft frontend and backend applications. It covers local development, staging, and production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Setup](#backend-setup)
3. [Frontend Setup](#frontend-setup)
4. [Development Environment](#development-environment)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)
7. [Verification Checklist](#verification-checklist)

---

## Prerequisites

### System Requirements

- **Backend**: Python 3.9+, Django 4.0+
- **Frontend**: Node.js 16+, npm or yarn
- **Database**: SQLite (development) or PostgreSQL (production)
- **Redis**: For caching and WebSocket support (optional but recommended)

### Required Software

```bash
# Python (for backend)
python --version  # Should be 3.9 or higher

# Node.js (for frontend)
node --version    # Should be 16 or higher
npm --version     # Or use yarn

# Git (for version control)
git --version
```

---

## Backend Setup

### 1. Clone Repository

```bash
cd /path/to/workspace
git clone <backend-repo> my_prmpt_bakend
cd my_prmpt_bakend
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# For development with additional tools
pip install -r requirements.dev.txt
```

### 4. Configure Django Settings

Create a `.env` file in the backend root directory:

```env
# Environment
DEBUG=True
ENVIRONMENT=development

# Secret Key (generate a new one for production)
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///db.sqlite3
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/promptcraft

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
CHANNEL_LAYER_SECRET=your-secret-key

# API Configuration
API_DOMAIN=http://127.0.0.1:8000
FRONTEND_DOMAIN=http://localhost:3001

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# Or for production:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password

# Sentry (optional - error monitoring)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# JWT Configuration
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256

# App Version
APP_VERSION=1.0.0
```

### 5. Run Database Migrations

```bash
# Apply migrations
python manage.py migrate

# Create superuser for admin
python manage.py createsuperuser
```

### 6. Create Initial Data (Optional)

```bash
# Load fixtures or create sample data
python manage.py loaddata fixtures/initial_data.json
# Or create data via Django shell
python manage.py shell
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Test Backend Server

```bash
# Start development server
python manage.py runserver 0.0.0.0:8000

# Or for ASGI (WebSocket support)
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

Verify by visiting: `http://127.0.0.1:8000/health/`

---

## Frontend Setup

### 1. Clone Repository

```bash
cd /path/to/workspace
git clone <frontend-repo> my_prmpt_frontend
cd my_prmpt_frontend
```

### 2. Install Dependencies

```bash
# Using npm
npm install

# Or using yarn
yarn install
```

### 3. Configure Environment Variables

Create a `.env.local` file in the frontend root directory:

```env
# API Configuration
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_API_VERSION=v2

# App Configuration
REACT_APP_APP_NAME=PromptCraft
REACT_APP_VERSION=1.0.0

# Debug Mode
REACT_APP_DEBUG=true

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_CHAT=true
REACT_APP_ENABLE_BILLING=true
REACT_APP_ENABLE_RESEARCH=true

# Analytics (optional)
REACT_APP_GOOGLE_ANALYTICS_ID=UA-XXXXXXXXX-X

# Email
REACT_APP_SUPPORT_EMAIL=support@prompt-temple.com
```

### 4. Start Development Server

```bash
# Using npm
npm start

# Or using yarn
yarn start

# Server will start on http://localhost:3001
```

---

## Development Environment

### 1. Verify Backend CORS Configuration

Check that the backend has proper CORS settings in `promptcraft/settings.py`:

```python
# Development CORS settings (should be present)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_ALL_ORIGINS = True  # In development only

CORS_ALLOW_CREDENTIALS = True

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
```

### 2. Test CORS Configuration

```bash
# Test preflight request
curl -X OPTIONS http://127.0.0.1:8000/api/v2/templates/ \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization" \
  -v

# Should see:
# < Access-Control-Allow-Origin: http://localhost:3001
# < Access-Control-Allow-Methods: GET, POST, ...
# < Access-Control-Allow-Headers: ...
```

### 3. Test API Endpoints

```bash
# Health check
curl http://127.0.0.1:8000/health/

# Get config
curl http://127.0.0.1:8000/api/v2/core/config/

# Get templates
curl http://127.0.0.1:8000/api/v2/templates/
```

### 4. Enable Debug Tools

**Django Debug Toolbar** (Backend):
```python
# Already configured in settings.py if DEBUG=True
# Access at: http://127.0.0.1:8000/__debug__/
```

**React Developer Tools** (Frontend):
- Install browser extension
- Inspect React component hierarchy
- View props and state

**Network Tab**:
- Monitor API requests
- Check CORS headers
- View request/response bodies
- Check for failed requests

### 5. Using the Verify API Command

```bash
# Check if all endpoints are accessible
python manage.py verify_api

# Check CORS headers specifically
python manage.py verify_api --check-cors

# Verbose output
python manage.py verify_api --verbose --check-cors
```

---

## Production Deployment

### 1. Backend Deployment (Railway/Heroku)

```bash
# Update requirements.txt
pip freeze > requirements.txt

# Configure production environment
export DEBUG=False
export SECRET_KEY=<generate-secure-key>
export ALLOWED_HOSTS=www.prompt-temple.com,prompt-temple.com
export DATABASE_URL=<production-db-url>

# Update CORS settings for production
# In settings.py:
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "https://www.prompt-temple.com",
        "https://prompt-temple.com",
    ]
    CORS_ALLOW_ALL_ORIGINS = False
```

### 2. Frontend Deployment (Vercel/Netlify)

```bash
# Build optimized frontend
npm run build

# Preview build locally
npm run serve

# Environment variables for production
# In Vercel/Netlify dashboard:
REACT_APP_API_URL=https://api.prompt-temple.com
REACT_APP_API_VERSION=v2
```

### 3. Domain Configuration

**Option A: Separate Domains with CORS**
- Frontend: `https://www.prompt-temple.com`
- Backend: `https://api.prompt-temple.com`
- Configure CORS to allow frontend domain

**Option B: Same Domain with Reverse Proxy (Recommended)**
```nginx
# Nginx configuration
server {
    listen 443 ssl;
    server_name www.prompt-temple.com;

    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. SSL/TLS Configuration

```bash
# Using Let's Encrypt with Certbot
certbot certonly --standalone -d www.prompt-temple.com -d prompt-temple.com

# Update Nginx/Apache with certificate paths
```

---

## Troubleshooting

### CORS Errors

**Problem**: `No 'Access-Control-Allow-Origin' header is present on the requested resource`

**Solutions**:
1. Check backend CORS settings in `settings.py`
2. Verify `corsheaders` middleware is installed: `pip install django-cors-headers`
3. Check middleware order (CorsMiddleware must be first)
4. Verify frontend origin is in `CORS_ALLOWED_ORIGINS`
5. In development, check `CORS_ALLOW_ALL_ORIGINS = True`

```bash
# Check if corsheaders is installed
pip list | grep django-cors-headers

# Verify middleware setup
python manage.py shell
from django.conf import settings
print(settings.MIDDLEWARE)
```

### 401 Unauthorized Errors

**Problem**: `401 Unauthorized` on API requests

**Solutions**:
1. Check if token is being sent in Authorization header
2. Verify token hasn't expired
3. Try refreshing token
4. Check JWT configuration in `settings.py`

```bash
# Test with token
curl -H "Authorization: Bearer <your-token>" \
     http://127.0.0.1:8000/api/v2/templates/
```

### 404 Not Found Errors

**Problem**: `404 Not Found` on endpoints

**Solutions**:
1. Verify endpoint URL is correct
2. Check if using correct API version (v1 vs v2)
3. Verify resource exists
4. Check URL routing in `urls.py`

```bash
# List all available URLs
python manage.py show_urls
```

### Network Timeouts

**Problem**: `Error: timeout of 30000ms exceeded`

**Solutions**:
1. Increase timeout in API client (default: 30s)
2. Check backend performance
3. Check network connectivity
4. Verify Redis/database are running

```typescript
// Update timeout in api-client.ts
const apiClient = axios.create({
  timeout: 60000, // 60 seconds
});
```

### Database Connection Issues

**Problem**: `Cannot connect to database`

**Solutions**:
1. Verify database is running
2. Check `DATABASE_URL` environment variable
3. Run migrations: `python manage.py migrate`
4. Check database credentials

```bash
# Test database connection
python manage.py dbshell

# Run migrations
python manage.py migrate --run-syncdb
```

### Static Files Not Loading

**Problem**: CSS/JS not loading in frontend

**Solutions**:
1. Run `python manage.py collectstatic`
2. Check `STATIC_URL` and `STATIC_ROOT` in settings
3. In production, use CDN or S3 for static files

```bash
# Collect static files
python manage.py collectstatic --noinput --clear

# Check static files
ls -la staticfiles/
```

---

## Verification Checklist

Use this checklist to verify your setup is correct:

### Backend

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file created with correct settings
- [ ] Database migrations run: `python manage.py migrate`
- [ ] Django superuser created: `python manage.py createsuperuser`
- [ ] Static files collected: `python manage.py collectstatic`
- [ ] Backend running: `python manage.py runserver`
- [ ] Health check working: `curl http://127.0.0.1:8000/health/`
- [ ] CORS configured correctly
- [ ] All endpoints returning 200 status (except auth)

### Frontend

- [ ] Node.js 16+ installed
- [ ] Dependencies installed: `npm install`
- [ ] `.env.local` file created
- [ ] Frontend running: `npm start`
- [ ] App loading on `http://localhost:3001`
- [ ] No CORS errors in browser console
- [ ] No 401 unauthorized errors
- [ ] API requests succeeding
- [ ] Data displaying correctly

### Integration

- [ ] Frontend can reach backend API
- [ ] CORS headers present in responses
- [ ] Authentication working (login/logout)
- [ ] API calls succeeding from frontend
- [ ] WebSocket connection working (if using)
- [ ] Error handling working correctly
- [ ] Retry logic functioning
- [ ] No console errors

### Production (if applicable)

- [ ] Backend deployed and running
- [ ] Frontend deployed and running
- [ ] SSL/TLS certificates installed
- [ ] Domain DNS configured
- [ ] CORS updated for production domains
- [ ] Database backed up
- [ ] Error monitoring configured (Sentry)
- [ ] CDN configured for static files (if using)

---

## Additional Resources

- [API Integration Guide](./API_INTEGRATION_GUIDE.md)
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [Axios Documentation](https://axios-http.com/)
- [CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [JWT Authentication](https://jwt.io/)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review error messages in console/logs
3. Run the verification checklist
4. Contact the development team

---

**Last Updated**: January 2024
**Version**: 1.0.0
