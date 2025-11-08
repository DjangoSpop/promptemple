# PromptCraft Backend API - Complete Integration & Deployment Guide

Welcome! This README provides everything you need to integrate the PromptCraft backend with frontend applications and deploy to production.

## 🚀 Quick Start

### For Developers (Local Setup - 5 minutes)

```bash
# 1. Clone and setup backend
git clone <backend-repo> my_prmpt_backend
cd my_prmpt_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and set DEBUG=True, DATABASE_URL, etc.

# 3. Run migrations
python manage.py migrate

# 4. Start backend
python manage.py runserver 0.0.0.0:8000

# 5. In another terminal, setup frontend
cd ../my_prmpt_frontend
npm install
npm start  # Runs on http://localhost:3001

# 6. Verify integration
# Open http://localhost:3001 in browser
# Check DevTools console for errors (should be none)
```

### For DevOps/Deployment (Railway, AWS, etc.)

```bash
# See ENVIRONMENT_SETUP_GUIDE.md → Production Deployment section
# Or RAILWAY_DEPLOYMENT.md for Railway-specific steps
```

---

## 📚 Documentation Files

### For Frontend Developers

| Document | Purpose | Read When |
|----------|---------|-----------|
| **[API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)** | Complete API reference and integration patterns | Starting frontend integration |
| **[FRONTEND_API_CLIENT.ts](./FRONTEND_API_CLIENT.ts)** | Production-ready TypeScript API client | Integrating API client into frontend |
| **[FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md)** | Step-by-step debugging guide | Fixing API/CORS issues |
| **[AUTHENTICATION_GUIDE.md](./AUTHENTICATION_GUIDE.md)** | JWT authentication flow | Implementing login/logout |

### For Backend Developers

| Document | Purpose | Read When |
|----------|---------|-----------|
| **[ENVIRONMENT_SETUP_GUIDE.md](./ENVIRONMENT_SETUP_GUIDE.md)** | Complete backend setup and deployment | Setting up development environment |
| **[API_COVERAGE.md](./API_COVERAGE.md)** | Endpoint coverage and status report | Reviewing API completeness |
| **[AI_TESTING_GUIDE.md](./AI_TESTING_GUIDE.md)** | AI services testing | Testing AI integration endpoints |

### For DevOps/Operations

| Document | Purpose | Read When |
|----------|---------|-----------|
| **[RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)** | Railway platform deployment | Deploying to Railway |
| **[ENVIRONMENT_SETUP_GUIDE.md](./ENVIRONMENT_SETUP_GUIDE.md)** | Production deployment steps | Deploying to production |
| **[INTEGRATION_DOCUMENTATION_SUMMARY.md](./INTEGRATION_DOCUMENTATION_SUMMARY.md)** | Complete summary of all tools | Getting project overview |

---

## ✅ Current Status

### Backend Configuration

- ✅ **CORS Configured**: Ready for frontend integration
- ✅ **JWT Authentication**: Enabled and tested
- ✅ **Database**: SQLite (dev) / PostgreSQL (prod)
- ✅ **API Documentation**: OpenAPI/Swagger available
- ✅ **Error Monitoring**: Sentry integration ready
- ✅ **WebSocket Support**: Channels/Daphne configured

### API Endpoints

**Production-Ready Endpoints:**
- 🟢 Authentication: `/api/v2/auth/*`
- 🟢 Templates: `/api/v2/templates/*`
- 🟢 Core Config: `/api/v2/core/*`
- 🟢 Analytics: `/api/v2/analytics/*`
- 🟢 AI Services: `/api/v2/ai/*`
- 🟢 Chat: `/api/v2/chat/*`
- 🟢 Billing: `/api/v2/billing/*`
- 🟢 Orchestrator: `/api/v2/orchestrator/*`
- 🟢 Gamification: `/api/v2/gamification/*`

**View Full Coverage:** See [API_COVERAGE.md](./API_COVERAGE.md)

---

## 🔧 Key Tools & Commands

### Verify API Endpoints

```bash
# Check if all endpoints are accessible and CORS is working
python manage.py verify_api

# Check with CORS headers verification
python manage.py verify_api --check-cors

# Verbose output
python manage.py verify_api --verbose --check-cors
```

### Test with cURL

```bash
# Health check (no auth required)
curl http://127.0.0.1:8000/health/

# Get configuration
curl http://127.0.0.1:8000/api/v2/core/config/

# Test CORS preflight
curl -X OPTIONS http://127.0.0.1:8000/api/v2/templates/ \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.templates

# With coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

---

## 🌐 API Endpoint Reference

### Authentication (No Auth Required)

```
POST   /api/v2/auth/login/           Register or login user
POST   /api/v2/auth/register/        Create new account
POST   /api/v2/auth/refresh/         Refresh access token
POST   /api/v2/auth/logout/          Logout user
```

### Health & Config (No Auth Required)

```
GET    /health/                      Health check
GET    /api/v2/core/config/         Application configuration
GET    /api/v2/core/health/         Detailed health check
```

### Templates (Auth Required)

```
GET    /api/v2/templates/            List all templates
GET    /api/v2/templates/featured/   Get featured templates
GET    /api/v2/templates/trending/   Get trending templates
GET    /api/v2/template-categories/  Get categories
```

### AI Services (Auth Required)

```
GET    /api/v2/ai/assistant/         List assistants
POST   /api/v2/ai/assistant/         Create assistant
GET    /api/v2/ai/assistant/threads/ List threads
POST   /api/v2/ai/assistant/threads/ Create thread
```

### Analytics (Auth Required)

```
GET    /api/v2/analytics/dashboard/      Get dashboard data
POST   /api/v2/analytics/track/          Track event
GET    /api/v2/analytics/user-insights/  Get user insights
GET    /api/v2/analytics/template-analytics/ Template analytics
```

### Orchestrator (Auth Required)

```
POST   /api/v2/orchestrator/intent/   Detect intent
POST   /api/v2/orchestrator/render/   Render template
POST   /api/v2/orchestrator/assess/   Assess prompt
GET    /api/v2/orchestrator/search/   Search templates
```

**Full API Documentation:** Visit `/api/schema/swagger-ui/` when backend is running

---

## 🏗️ Project Structure

```
my_prmpt_backend/
├── promptcraft/           # Django settings and configuration
│   ├── settings.py       # CORS, middleware, apps configuration
│   ├── urls.py           # URL routing
│   ├── wsgi.py           # WSGI application
│   └── asgi.py           # ASGI application (WebSocket)
│
├── apps/                  # Django applications
│   ├── core/             # Core app (health, config)
│   ├── templates/        # Template management
│   ├── users/            # User management and auth
│   ├── ai_services/      # AI integration
│   ├── analytics/        # Analytics and tracking
│   ├── chat/             # Chat functionality
│   ├── billing/          # Billing and subscriptions
│   ├── orchestrator/     # AI orchestration
│   ├── gamification/     # Gamification features
│   └── research_agent/   # Research agent
│
├── Documentation/        # (This is you are reading)
│   ├── README.md                           # This file
│   ├── API_INTEGRATION_GUIDE.md             # Frontend integration guide
│   ├── ENVIRONMENT_SETUP_GUIDE.md           # Setup and deployment
│   ├── FRONTEND_API_CLIENT.ts               # TypeScript API client
│   ├── FRONTEND_DEBUGGING_GUIDE.md          # Debugging guide
│   ├── AUTHENTICATION_GUIDE.md              # Auth details
│   ├── API_COVERAGE.md                      # Endpoint coverage
│   ├── AI_TESTING_GUIDE.md                  # AI testing
│   ├── RAILWAY_DEPLOYMENT.md                # Railway deployment
│   └── INTEGRATION_DOCUMENTATION_SUMMARY.md # Summary
│
├── manage.py             # Django management utility
├── requirements.txt      # Python dependencies
├── db.sqlite3           # SQLite database (dev only)
└── .env.example         # Environment variables template
```

---

## 🔐 Environment Configuration

### Development (.env)

```env
DEBUG=True
SECRET_KEY=your-development-secret-key
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0

# CORS - automatic in dev when DEBUG=True
CORS_ALLOWED_ORIGINS=http://localhost:3001,http://127.0.0.1:3001

# API URLs
API_DOMAIN=http://127.0.0.1:8000
FRONTEND_DOMAIN=http://localhost:3001

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production (.env)

```env
DEBUG=False
SECRET_KEY=your-production-secret-key-very-secure
DATABASE_URL=postgresql://user:password@db.example.com/promptcraft
REDIS_URL=redis://redis.example.com:6379/0

# CORS - must be specific in production
CORS_ALLOWED_ORIGINS=https://www.prompt-temple.com,https://prompt-temple.com

# API URLs
API_DOMAIN=https://api.prompt-temple.com
FRONTEND_DOMAIN=https://www.prompt-temple.com

# Email (Gmail example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@prompt-temple.com
EMAIL_HOST_PASSWORD=your-app-password

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

---

## 🚦 CORS Configuration

### ✅ What's Already Configured

The backend is **pre-configured** for CORS and ready to work with any frontend:

**Development (DEBUG=True):**
- All origins allowed automatically
- Credentials supported
- All HTTP methods allowed

**Production (DEBUG=False):**
- Only specific domains allowed
- Currently configured for: `prompt-temple.com` and `www.prompt-temple.com`
- Update in `settings.py` for other domains

### Verify CORS is Working

```bash
# Run this command
python manage.py verify_api --check-cors

# You should see:
# ✓ Core config: HTTP 200 (CORS enabled)
# ✓ Templates list: HTTP 200 (CORS enabled)
# ✓ Health check: HTTP 200 (CORS enabled)
# ... etc
```

### Troubleshoot CORS Issues

If you see errors like: `No 'Access-Control-Allow-Origin' header`

1. **Check backend is running:** `curl http://127.0.0.1:8000/health/`
2. **Check CORS middleware:** Verify in `settings.py` that `corsheaders.middleware.CorsMiddleware` is first
3. **Check DEBUG setting:** Should be `True` in development
4. **Restart backend:** Stop and start the server
5. **Clear frontend cache:** Ctrl+Shift+R in browser

See [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md) for detailed troubleshooting.

---

## 🔐 Authentication

All API endpoints (except those listed below) require JWT authentication.

### No Authentication Required

```
GET  /health/
POST /api/v2/auth/login/
POST /api/v2/auth/register/
POST /api/v2/auth/refresh/
```

### With Authentication

```
Authorization: Bearer <access_token>
```

### Authentication Flow

1. **Register/Login** → Get access and refresh tokens
2. **Store Tokens** → Save access token in localStorage, refresh token in httpOnly cookie
3. **Send Requests** → Include `Authorization: Bearer <token>` header
4. **Token Expires** → Use refresh token to get new access token
5. **Refresh Fails** → Redirect to login

See [AUTHENTICATION_GUIDE.md](./AUTHENTICATION_GUIDE.md) for detailed flow.

---

## 📊 Common Issues & Solutions

### CORS Errors

**Problem:** `No 'Access-Control-Allow-Origin' header`

**Solution:** 
- Check backend is running: `curl http://127.0.0.1:8000/health/`
- Verify CORS settings: `python manage.py shell` then `from django.conf import settings; print(settings.CORS_ALLOW_ALL_ORIGINS)`
- See [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md#issue-1-cors-policy-blocking-requests)

### 401 Unauthorized

**Problem:** `Authentication credentials were not provided`

**Solution:**
- Check token is in localStorage: `localStorage.getItem('accessToken')`
- Check Authorization header is set: Look in Network tab
- Try login again to get new token
- See [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md#issue-2-401-unauthorized-errors)

### 404 Not Found

**Problem:** `Not found`

**Solution:**
- Verify endpoint URL: Check [API Endpoint Reference](#-api-endpoint-reference) above
- Check API version: Use `/api/v2/` not `/api/v1/`
- List all endpoints: `python manage.py show_urls`
- See [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md#issue-3-404-not-found-errors)

### Network Timeouts

**Problem:** `Error: timeout of 30000ms exceeded`

**Solution:**
- Check backend performance: `python manage.py runserver` should show requests
- Increase timeout in frontend API client
- Check database: `python manage.py dbshell`
- See [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md#issue-4-network-timeouts)

---

## 🚀 Deployment

### Quick Deploy to Railway

```bash
# 1. Push to GitHub
git push origin main

# 2. Connect Railway to repo
# See RAILWAY_DEPLOYMENT.md

# 3. Set environment variables in Railway dashboard
DEBUG=False
SECRET_KEY=<secure-key>
DATABASE_URL=<railway-postgres-url>
REDIS_URL=<railway-redis-url>

# 4. Deploy
# Railway auto-deploys on push
```

### Deploy to Other Platforms

See [ENVIRONMENT_SETUP_GUIDE.md](./ENVIRONMENT_SETUP_GUIDE.md#production-deployment) for:
- AWS EC2 / ECS
- Google Cloud
- Azure
- DigitalOcean
- Heroku
- Any custom server

---

## 📈 Monitoring & Debugging

### View Logs

```bash
# Real-time logs
python manage.py runserver

# Production logs
tail -f /var/log/promptcraft/error.log
tail -f /var/log/promptcraft/access.log
```

### Monitor API Performance

```bash
# Use Django Debug Toolbar (development only)
# Already configured if DEBUG=True
# Access: http://127.0.0.1:8000/__debug__/

# Use Sentry (production)
# Configure SENTRY_DSN in .env
# Visit https://sentry.io to view errors
```

### Database Queries

```bash
# View slow queries
python manage.py shell
from django.db import connection
from django.test.utils import CaptureQueriesContext
with CaptureQueriesContext(connection) as context:
    # Run your code here
    pass
for query in context:
    print(query)
```

---

## 🧪 Testing

### Run All Tests

```bash
python manage.py test
```

### Run Specific Tests

```bash
# Test specific app
python manage.py test apps.templates

# Test specific module
python manage.py test apps.templates.tests

# Test specific test case
python manage.py test apps.templates.tests.TemplateTests

# Test specific test method
python manage.py test apps.templates.tests.TemplateTests.test_create_template
```

### Test Coverage

```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report in htmlcov/index.html
```

### API Testing

```bash
# Using cURL
curl http://127.0.0.1:8000/api/v2/templates/

# Using Postman
# Import: https://www.postman.com/import
# Set collection variable: {{base_url}} = http://127.0.0.1:8000

# Using REST Client (VS Code)
# Create test.http file
# See FRONTEND_DEBUGGING_GUIDE.md for examples
```

---

## 📝 Logging

### Enable Debug Logging

```python
# In settings.py, add:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Log API Requests

```python
# In your view or middleware
import logging
logger = logging.getLogger(__name__)

logger.debug(f'Request: {request.method} {request.path}')
logger.info(f'User: {request.user}')
logger.warning(f'Cache miss: {cache_key}')
logger.error(f'Error: {str(error)}')
```

---

## 🔄 Git Workflow

### Clone Repository

```bash
git clone <repo-url> my_prmpt_backend
cd my_prmpt_backend
```

### Create Feature Branch

```bash
git checkout -b feature/my-feature
# Make changes
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

### Merge to Main

```bash
# Create pull request on GitHub
# After review and approval
git checkout main
git pull origin main
git merge feature/my-feature
git push origin main
```

---

## 📚 Learning Resources

### Django & DRF
- [Django Official Docs](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Real Python Django Tutorials](https://realpython.com/tutorials/django/)

### Frontend Integration
- [Axios Documentation](https://axios-http.com/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

### API Design
- [REST API Best Practices](https://restfulapi.net/)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)
- [OpenAPI Specification](https://www.openapis.org/)

### Deployment
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Railway Documentation](https://docs.railway.app/)

---

## 🆘 Getting Help

### Check These First

1. **Run verification:** `python manage.py verify_api --check-cors --verbose`
2. **Check browser console:** F12 → Console tab for errors
3. **Check Network tab:** F12 → Network tab to see requests
4. **Read error message:** Full error text usually tells you what's wrong
5. **Search documentation:** Use Ctrl+F to find your issue

### Ask for Help

Provide:
- ✅ Error message (full text from console or logs)
- ✅ What you were trying to do (step-by-step)
- ✅ Environment info (OS, Python version, Node version)
- ✅ What you've already tried
- ✅ Screenshot of Network tab or console

### Useful Debugging Commands

```bash
# Check if backend is running
curl http://127.0.0.1:8000/health/

# Check CORS configuration
python manage.py verify_api --check-cors

# Check database connection
python manage.py dbshell

# Check installed packages
pip list | grep django

# Check Python version
python --version

# Check Node version (for frontend)
node --version
```

---

## 📋 Deployment Checklist

Before deploying to production:

### Backend
- [ ] Set `DEBUG=False`
- [ ] Configure strong `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` to production domains
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for caching
- [ ] Configure Sentry for error monitoring
- [ ] Update `CORS_ALLOWED_ORIGINS` for frontend domain
- [ ] Run `python manage.py collectstatic`
- [ ] Set up SSL/TLS certificates
- [ ] Configure email backend
- [ ] Run database migrations
- [ ] Test all endpoints with production URL

### Frontend
- [ ] Set `REACT_APP_API_URL` to production backend URL
- [ ] Build optimized bundle: `npm run build`
- [ ] Test against production backend
- [ ] Set up CDN for static assets
- [ ] Configure HTTP caching headers
- [ ] Enable GZIP compression
- [ ] Set up monitoring/analytics
- [ ] Test on mobile devices
- [ ] Verify SSL/TLS is working

### DevOps
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Configure backups for database
- [ ] Set up health checks
- [ ] Configure auto-scaling (if needed)
- [ ] Set up CI/CD pipeline
- [ ] Test disaster recovery
- [ ] Document runbooks
- [ ] Set up alerting

---

## 📞 Support & Contact

- **Documentation:** See files listed in [📚 Documentation Files](#-documentation-files) above
- **Issues:** Check [📊 Common Issues & Solutions](#-common-issues--solutions)
- **Debugging:** See [FRONTEND_DEBUGGING_GUIDE.md](./FRONTEND_DEBUGGING_GUIDE.md)
- **API Reference:** Visit `/api/schema/swagger-ui/` when backend is running

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

- Built with [Django](https://www.djangoproject.com/) & [Django REST Framework](https://www.django-rest-framework.org/)
- API documentation powered by [drf-spectacular](https://drf-spectacular.readthedocs.io/)
- Deployment tools: [Railway](https://railway.app/), [Docker](https://www.docker.com/)

---

**Last Updated:** October 28, 2025  
**Version:** 1.0.0  
**Status:** ✅ Production Ready

**Questions?** Start with the [Quick Start](#-quick-start) section above or read the relevant documentation file for your role.
