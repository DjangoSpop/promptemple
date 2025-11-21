# Railway ASGI Deployment Guide

## Overview
This guide explains how to deploy your Django application with Daphne (ASGI) on Railway for proper WebSocket and real-time communication support.

## Current Setup ✅
- ✅ Daphne installed (`daphne==4.1.2`)
- ✅ Channels configured (`channels==4.0.0`)
- ✅ ASGI application configured (`promptcraft.asgi:application`)
- ✅ WebSocket routing configured
- ✅ Railway configuration created (`railway.toml`)
- ✅ Dockerfile updated for Daphne

## Deployment Steps

### 1. Environment Variables
Set these environment variables in your Railway project:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DJANGO_SETTINGS_MODULE=promptcraft.settings.production

# Database (Railway provides DATABASE_URL automatically)
# DATABASE_URL will be set by Railway

# Redis (for Channels and caching)
REDIS_URL=redis://redis:6379/0

# AI Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
DEEPSEEK_API_KEY=your-deepseek-key

# CORS Settings
ALLOWED_HOSTS=your-railway-app-url.railway.app,localhost,127.0.0.1

# Security (optional but recommended)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 2. Deploy to Railway

```bash
# Login to Railway
railway login

# If you haven't initialized Railway in this project yet
railway init

# Deploy your application
railway up
```

### 3. Verify Deployment

After deployment, verify that:

1. **HTTP requests work**: Your API endpoints should respond normally
2. **WebSocket connections work**: Test your WebSocket endpoints
3. **Static files are served**: CSS, JS, and media files load correctly
4. **Database connections work**: Check your database operations

## Key Changes Made

### 1. Railway Configuration (`railway.toml`)
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
runtime = "V2"
numReplicas = 1
startCommand = "daphne promptcraft.asgi:application --bind 0.0.0.0 --port $PORT"
sleepApplication = false
useLegacyStacker = false
multiRegionConfig = {"europe-west4-drams3a":{"numReplicas":1}}
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### 2. Dockerfile Changes
**Before:**
```dockerfile
CMD ["gunicorn", "promptcraft.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**After:**
```dockerfile
CMD ["daphne", "promptcraft.asgi:application", "--bind", "0.0.0.0", "--port", "8000"]
```

## Why Daphne + ASGI?

1. **WebSocket Support**: Unlike Gunicorn (WSGI), Daphne supports WebSockets natively
2. **Real-time Communication**: Essential for your chat and AI streaming features
3. **Better Performance**: ASGI handles concurrent connections more efficiently
4. **Channels Integration**: Works seamlessly with Django Channels for WebSocket routing

## Troubleshooting

### Common Issues:

1. **Port Binding**: Railway uses `$PORT` environment variable
2. **Static Files**: WhiteNoise handles static files in production
3. **Database**: Ensure `DATABASE_URL` is properly set by Railway
4. **Redis**: Required for Channels layer and caching

### Health Checks:
```bash
# Test HTTP endpoint
curl https://your-app.railway.app/api/health/

# Test WebSocket connection (using a WebSocket client)
# Your WebSocket endpoints should be accessible
```

### Logs:
```bash
# View Railway logs
railway logs

# View specific service logs
railway logs --service your-service-name
```

## Performance Optimization

1. **Redis Configuration**: Ensure Redis is properly configured for Channels
2. **Database Connection Pooling**: Already configured in production settings
3. **Static File Caching**: WhiteNoise provides compression and caching
4. **Gzip Compression**: Daphne handles compression automatically

## Security Considerations

1. **HTTPS**: Railway provides SSL certificates automatically
2. **Environment Variables**: Never commit secrets to code
3. **CORS**: Properly configured for your frontend domains
4. **CSRF Protection**: Enabled for security

## Next Steps

1. **Test thoroughly** after deployment
2. **Monitor performance** using Railway's dashboard
3. **Set up monitoring** for errors and performance
4. **Configure backups** for your database
5. **Set up CI/CD** for automatic deployments

## Support

If you encounter issues:
1. Check Railway logs: `railway logs`
2. Verify environment variables are set correctly
3. Test locally with Daphne: `daphne promptcraft.asgi:application`
4. Ensure all dependencies are installed in requirements.txt

Your application is now configured for ASGI deployment with full WebSocket support! 🚀