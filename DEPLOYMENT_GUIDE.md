# PromptCraft WebSocket & AI Integration Deployment Guide

## 🚀 Overview

This guide covers the complete setup of PromptCraft with:
- **Sentry** for error monitoring and performance tracking
- **Django Channels** for WebSocket real-time communication
- **Daphne** ASGI server for production WebSocket handling
- **LangChain** integration for AI-powered search and optimization
- **Redis** backend for channel layers and caching

## 📋 Prerequisites

### System Requirements
- Python 3.8+ 
- Redis Server 6.0+
- 4GB+ RAM (8GB+ recommended for production)
- 2GB+ disk space

### Development Tools
- Git
- PowerShell (Windows) or Bash (Linux/macOS)
- VS Code (recommended)

## 🔧 Installation Steps

### 1. Install Dependencies

```powershell
# Install Python packages
pip install -r requirements.txt

# Install Redis (Windows - via Chocolatey)
choco install redis-64

# Install Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Install Redis (macOS)
brew install redis
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ENVIRONMENT=production

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Channels Configuration
CHANNEL_LAYER_SECRET=your-channel-layer-secret-key

# Sentry Error Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
APP_VERSION=1.0.0

# AI Service Configuration
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# Search Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.7
MAX_SEARCH_RESULTS=20
ENABLE_VECTOR_SEARCH=True

# Performance Settings
SEARCH_BATCH_SIZE=100
INDEX_UPDATE_FREQUENCY=3600

# SSL Configuration (Production)
SSL_CERT_PATH=/path/to/ssl/certificate.pem
SSL_KEY_PATH=/path/to/ssl/private.key
```

### 3. Database Setup

```powershell
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (if available)
python manage.py loaddata fixtures/*.json
```

### 4. Redis Setup

```powershell
# Start Redis server
redis-server

# Test Redis connection
redis-cli ping
# Should return: PONG
```

### 5. Test Installation

```powershell
# Run comprehensive system tests
python test_integration.py

# Test WebSocket connections specifically
python test_integration.py --websocket-only
```

## 🚀 Deployment Options

### Option 1: Development Server (Daphne)

```powershell
# Basic development setup
.\run_daphne.ps1

# With custom port
.\run_daphne.ps1 -Port 8080

# Production mode
.\run_daphne.ps1 -Environment production
```

### Option 2: Production with SSL

```powershell
# With SSL certificates
.\run_daphne.ps1 -Environment production -SSL_CERT cert.pem -SSL_KEY key.pem
```

### Option 3: Docker Deployment

```dockerfile
# Dockerfile is already configured
docker build -t promptcraft .
docker run -p 8000:8000 --env-file .env promptcraft
```

### Option 4: Make Commands (Linux/macOS)

```bash
# Install dependencies
make install-deps

# Setup logs directory
make setup-logs

# Start Redis
make redis-start

# Start full stack
make start-stack

# Run tests
make ws-test
```

## 🔍 Monitoring & Debugging

### Sentry Configuration

1. Create account at [sentry.io](https://sentry.io)
2. Create new Django project
3. Copy DSN to `.env` file
4. Monitor errors at sentry.io dashboard

### Log Files

```
logs/
├── django.log          # Django application logs
├── django_error.log    # Django error logs
├── daphne.log         # Daphne server logs
├── daphne_access.log  # HTTP/WebSocket access logs
└── wsgi.log           # WSGI server logs
```

### Health Checks

```powershell
# Check application health
curl http://localhost:8000/health/

# Test WebSocket connection
python -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://localhost:8000/ws/chat/test/') as ws:
        await ws.send(json.dumps({'type': 'ping'}))
        response = await ws.recv()
        print(f'WebSocket OK: {response}')
asyncio.run(test())
"
```

## 🔧 Configuration Details

### WebSocket Endpoints

- **Chat/Optimization**: `ws://domain/ws/chat/{session_id}/`
- **AI Processing**: `ws://domain/ws/ai/process/{session_id}/`
- **Real-time Search**: `ws://domain/ws/search/{session_id}/`
- **Analytics**: `ws://domain/ws/analytics/{session_id}/`

### WebSocket Message Types

#### Prompt Chat Consumer
```json
// User intent processing
{
    "type": "user_intent",
    "query": "Write a professional email"
}

// Search request
{
    "type": "search_request", 
    "query": "marketing copy",
    "category": "business",
    "max_results": 10
}

// Prompt optimization
{
    "type": "optimize_prompt",
    "prompt_id": "prompt-uuid",
    "optimization_type": "enhancement"
}
```

#### AI Processing Consumer
```json
// Content generation
{
    "type": "generate_content",
    "prompt": "Write a blog post about AI",
    "content_type": "marketing",
    "max_length": 500
}

// Sentiment analysis
{
    "type": "analyze_sentiment",
    "text": "This product is amazing!"
}
```

### Performance Optimization

#### Redis Configuration
```redis
# redis.conf optimizations
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### Daphne Optimization
```bash
# Production Daphne command
daphne \
    --bind 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --application-close-timeout 30 \
    --websocket-timeout 86400 \
    --websocket-connect-timeout 10 \
    --access-log logs/access.log \
    promptcraft.asgi:application
```

## 🔐 Security Considerations

### WebSocket Security
- All WebSocket connections require authentication
- CORS properly configured for allowed origins
- Rate limiting implemented for message processing
- Input validation on all WebSocket messages

### Environment Variables
```env
# Security settings
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# SSL/HTTPS
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
```

## 🚨 Troubleshooting

### Common Issues

#### 1. WebSocket Connection Fails
```bash
# Check if Daphne is running
netstat -an | findstr :8000

# Check Django Channels configuration
python manage.py shell -c "
from django.conf import settings
print('ASGI_APPLICATION:', getattr(settings, 'ASGI_APPLICATION', 'Not set'))
print('CHANNEL_LAYERS:', getattr(settings, 'CHANNEL_LAYERS', 'Not set'))
"
```

#### 2. Redis Connection Error
```bash
# Test Redis connection
redis-cli ping

# Check Redis configuration
redis-cli config get "*"
```

#### 3. Sentry Not Working
```python
# Test Sentry configuration
python manage.py shell -c "
import sentry_sdk
sentry_sdk.capture_message('Test message from Django')
print('Sentry test message sent')
"
```

#### 4. LangChain API Errors
```bash
# Check API keys
python -c "
import os
print('OpenAI API Key:', 'Set' if os.getenv('OPENAI_API_KEY') else 'Not set')
print('Anthropic API Key:', 'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set')
"
```

### Performance Debugging

#### Check WebSocket Performance
```python
# Monitor WebSocket message processing times
# Check logs/django.log for performance metrics
tail -f logs/django.log | grep "websocket"
```

#### Monitor Memory Usage
```bash
# Check Redis memory usage
redis-cli info memory

# Check Python process memory
ps aux | grep python
```

## 📊 Monitoring Dashboard

### Key Metrics to Monitor

1. **WebSocket Connections**: Active connections count
2. **Message Processing Time**: Average response time
3. **Search Performance**: Query execution time
4. **AI Service Latency**: LangChain processing time
5. **Error Rate**: Sentry error tracking
6. **Redis Performance**: Memory usage and hit rates

### Alerting Setup

Configure Sentry alerts for:
- WebSocket connection failures
- Search service timeouts
- AI service API errors
- High memory usage
- Database connection issues

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Redis server optimized
- [ ] Sentry monitoring active
- [ ] Log rotation configured
- [ ] Backup strategy implemented
- [ ] Load balancer configured (if needed)
- [ ] CDN setup for static files
- [ ] Database optimized
- [ ] Security headers configured

## 📞 Support

For issues and questions:
1. Check logs in `logs/` directory
2. Run `python test_integration.py` for diagnostics
3. Review Sentry dashboard for errors
4. Check Redis and database connectivity

---

## 🔗 Quick Commands Reference

```powershell
# Start development server
.\run_daphne.ps1

# Run tests
python test_integration.py

# Check logs
Get-Content logs\django.log -Tail 50

# Monitor WebSocket connections
netstat -an | findstr :8000

# Redis CLI
redis-cli monitor

# Django shell
python manage.py shell
```