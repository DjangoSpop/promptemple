# Django ASGI Production Deployment Guide

## 🚀 Deployment Status: READY

Your Django backend is now configured for production deployment with Daphne ASGI server, WebSockets, SSE, and Celery support.

## ✅ What's Been Fixed

### 1. Requirements & Dependencies
- ✅ Cleaned up `requirements.txt` with production-ready packages
- ✅ Added missing `djangorestframework-simplejwt` for authentication
- ✅ Added `django-redis` for caching and sessions
- ✅ Added `sentry-sdk` for error monitoring
- ✅ Added `gunicorn` as backup WSGI server

### 2. ASGI Configuration
- ✅ Fixed `promptcraft.asgi:application` to use production settings
- ✅ Configured WebSocket routing with proper error handling
- ✅ Set up Channels with Redis backend (fallback to in-memory)

### 3. Production Settings
- ✅ Created robust production settings in `promptcraft/settings/production.py`
- ✅ Database: Auto-detects Railway DATABASE_URL, falls back to SQLite
- ✅ Cache: Redis-first with graceful fallback to in-memory
- ✅ Security headers and HTTPS configuration
- ✅ Static files with WhiteNoise compression

### 4. Docker & Railway Config
- ✅ Updated Dockerfile to use dynamic `$PORT` variable
- ✅ Fixed health check endpoint to use dynamic port
- ✅ Updated `railway.toml` with proper deployment commands
- ✅ Added automatic migrations and static file collection

### 5. WebSocket & SSE Support
- ✅ Configured Channels for real-time communication
- ✅ WebSocket consumers for AI processing and chat
- ✅ SSE endpoints in AI services for streaming responses

### 6. Celery Background Tasks
- ✅ Production-ready Celery configuration
- ✅ Task routing and retry policies
- ✅ Redis broker with fallback support

## 🚀 Railway Deployment Instructions

### Step 1: Environment Variables
Set these in your Railway project dashboard:

```bash
# Core Django
DEBUG=False
SECRET_KEY=your-super-secret-production-key
DJANGO_SETTINGS_MODULE=promptcraft.settings.production

# Security
ALLOWED_HOSTS=*.railway.app,yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# AI Services
DEEPSEEK_API_KEY=your-deepseek-api-key
OPENAI_API_KEY=your-openai-api-key-optional
ANTHROPIC_API_KEY=your-anthropic-api-key-optional
TAVILY_API_KEY=your-tavily-api-key-optional

# Channels Security
CHANNEL_LAYER_SECRET=your-random-32-char-secret

# Features
FEATURE_RAG=True
CHAT_TRANSPORT=sse
```

### Step 2: Add Railway Services
1. **PostgreSQL**: Add PostgreSQL addon (sets DATABASE_URL automatically)
2. **Redis**: Add Redis addon (sets REDIS_URL automatically)

### Step 3: Deploy
```bash
# Login to Railway
railway login

# Deploy your application
railway up
```

## 📊 Architecture Overview

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Frontend      │────│   Railway    │────│  Database   │
│   (React/Next)  │    │   (Daphne)   │    │ (PostgreSQL)│
└─────────────────┘    └──────────────┘    └─────────────┘
                              │
                       ┌──────────────┐
                       │    Redis     │
                       │ (Cache+WS)   │
                       └──────────────┘
```

## 🔧 Key Components

### ASGI Server (Daphne)
- **Port**: Dynamic `$PORT` from Railway
- **WebSockets**: Enabled for real-time features
- **HTTP/2**: Supported for better performance

### Database
- **Primary**: PostgreSQL (Railway addon)
- **Fallback**: SQLite3 for development
- **Migrations**: Auto-run on deployment

### Caching & Sessions
- **Primary**: Redis (Railway addon)
- **Fallback**: In-memory for local development
- **Sessions**: Redis-backed with cookie fallback

### Real-time Features
- **WebSockets**: AI processing, chat, analytics
- **SSE**: Streaming AI responses
- **Channels**: Redis-backed message passing

## 🔍 Health Checks

### Basic Health Check
```bash
curl https://your-app.railway.app/health/
```

### WebSocket Test
```bash
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" \
  https://your-app.railway.app/ws/health/
```

## 🛠 Troubleshooting

### Common Issues

1. **Port Binding Error**
   - Railway automatically sets `$PORT` environment variable
   - Our Dockerfile uses `${PORT:-8000}` for fallback

2. **Database Connection**
   - Railway PostgreSQL sets `DATABASE_URL` automatically
   - Falls back to SQLite if no PostgreSQL addon

3. **Redis Connection**
   - Railway Redis sets `REDIS_URL` automatically
   - Falls back to in-memory cache if no Redis addon

4. **Static Files**
   - WhiteNoise serves static files automatically
   - `collectstatic` runs during deployment

### Debug Commands
```bash
# Check Django settings
python manage.py check --settings=promptcraft.settings.production

# Test database connection
python manage.py dbshell --settings=promptcraft.settings.production

# Collect static files
python manage.py collectstatic --noinput --settings=promptcraft.settings.production
```

## 📈 Performance Features

### Optimizations Enabled
- ✅ Static file compression (WhiteNoise)
- ✅ Database connection pooling
- ✅ Redis caching for sessions and data
- ✅ ASGI for concurrent connections
- ✅ Gzip compression
- ✅ Browser caching headers

### Monitoring
- ✅ Health check endpoints
- ✅ Error logging to files
- ✅ Sentry integration (optional)
- ✅ Performance metrics

## 🔐 Security Features

### Production Security
- ✅ HTTPS redirect in production
- ✅ Secure cookie settings
- ✅ CSRF protection
- ✅ XSS protection headers
- ✅ Content type sniffing protection
- ✅ CORS properly configured

## 🎯 Next Steps

1. **Deploy to Railway**: Run `railway up`
2. **Set Environment Variables**: Configure in Railway dashboard
3. **Add Database & Redis**: Install PostgreSQL and Redis addons
4. **Test Endpoints**: Verify health checks and API functionality
5. **Configure Domain**: Set up custom domain in Railway
6. **Monitor**: Set up Sentry for error tracking

## 📞 Support

If you encounter issues:
1. Check Railway logs: `railway logs`
2. Verify environment variables in Railway dashboard
3. Test locally with production settings first
4. Check health endpoint: `/health/`

Your Django backend is now production-ready for Railway deployment! 🚀