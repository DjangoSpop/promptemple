# 🏗️ Backend Architecture: SSE Chat Implementation

## 📋 Technical Overview

**Document**: Backend Architecture & Implementation Details  
**Author**: Backend Engineering Team  
**Date**: September 7, 2025  
**Version**: 1.0

This document provides comprehensive technical details for the SSE (Server-Sent Events) chat implementation, replacing WebSocket for real-time chat functionality.

---

## 🏛️ System Architecture

### **High-Level Architecture**
```
┌─────────────────┐    HTTP/SSE     ┌─────────────────┐    HTTP/JSON    ┌─────────────────┐
│   Frontend      │ ───────────────▶│   Django API    │ ───────────────▶│   Z.AI API      │
│   (React/Vue)   │                 │   (SSE Proxy)   │                 │   (GLM-4-32B)   │
│                 │ ◀─────────────── │                 │ ◀─────────────── │                 │
└─────────────────┘    SSE Stream   └─────────────────┘    Stream       └─────────────────┘
        │                                   │                                    │
        │                                   │                                    │
        ▼                                   ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐                ┌─────────────────┐
│   JWT Token     │                │   PostgreSQL    │                │   Rate Limiting │
│   Storage       │                │   Database      │                │   & Monitoring  │
└─────────────────┘                └─────────────────┘                └─────────────────┘
```

### **Request Flow**
1. **Frontend** → POST `/api/v2/chat/completions/` with JWT token
2. **Django Middleware** → Validates JWT token and rate limits
3. **ChatCompletionsProxyView** → Processes request and initiates stream
4. **Z.AI Client** → Streams response from external API
5. **SSE Response** → Real-time token streaming to frontend
6. **Database** → Logs conversation history and analytics

---

## 🔧 Implementation Details

### **Core Components**

#### **1. SSE Proxy View (`apps/chat/views.py`)**
```python
class ChatCompletionsProxyView(APIView):
    """
    Server-Sent Events proxy for chat completions.
    
    Features:
    - JWT authentication with user context
    - Rate limiting (5 requests/minute per user)
    - Real-time token streaming
    - Comprehensive error handling
    - Request/response logging
    """
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'chat_completions'
    
    def post(self, request, *args, **kwargs):
        # Implementation details...
```

#### **2. Authentication & Authorization**
```python
# JWT Token Validation
def get_user_from_token(request):
    """Extract and validate user from JWT token."""
    try:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            raise AuthenticationFailed('Invalid token format')
            
        token = auth_header.split(' ')[1]
        validated_token = UntypedToken(token)
        user_id = validated_token['user_id']
        return User.objects.get(id=user_id)
    except Exception as e:
        raise AuthenticationFailed(f'Token validation failed: {str(e)}')
```

#### **3. Rate Limiting Configuration**
```python
# settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'chat_completions': '5/min',  # 5 requests per minute per user
        'anon': '2/min',              # Anonymous users
        'burst': '60/hour',           # Burst protection
    }
}
```

#### **4. Z.AI Integration Layer**
```python
class ZAIStreamingClient:
    """
    Handles streaming communication with Z.AI API.
    
    Features:
    - Connection pooling and reuse
    - Automatic retry with exponential backoff
    - Timeout handling (30s connect, 120s read)
    - Request/response transformation
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=30.0, read=120.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5)
        )
    
    async def stream_completion(self, messages, model, **kwargs):
        """Stream chat completion from Z.AI API."""
        # Implementation with error handling and retries...
```

---

## 🗄️ Database Schema

### **Chat Sessions Table**
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_user(id),
    session_id VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_chat_sessions_user_id (user_id),
    INDEX idx_chat_sessions_session_id (session_id),
    INDEX idx_chat_sessions_created_at (created_at)
);
```

### **Chat Messages Table**
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    model VARCHAR(100),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_chat_messages_session_id (session_id),
    INDEX idx_chat_messages_created_at (created_at),
    INDEX idx_chat_messages_role (role)
);
```

### **API Usage Tracking**
```sql
CREATE TABLE api_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_user(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    request_id VARCHAR(100) UNIQUE,
    status_code INTEGER,
    response_time_ms INTEGER,
    tokens_used INTEGER DEFAULT 0,
    model VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_api_usage_logs_user_id (user_id),
    INDEX idx_api_usage_logs_created_at (created_at),
    INDEX idx_api_usage_logs_endpoint (endpoint)
);
```

---

## 🔒 Security Implementation

### **JWT Token Security**
```python
# Token validation with comprehensive checks
class EnhancedJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None
            
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
            
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        
        # Additional security checks
        if not user.is_active:
            raise AuthenticationFailed('User account is disabled')
            
        # Check token expiration with grace period
        exp = validated_token.get('exp')
        if exp and exp < time.time() - 300:  # 5-minute grace period
            raise AuthenticationFailed('Token has expired')
            
        return (user, validated_token)
```

### **Rate Limiting & DDoS Protection**
```python
class ChatRateLimiter:
    """
    Advanced rate limiting for chat endpoints.
    
    Features:
    - Per-user rate limiting
    - IP-based rate limiting
    - Sliding window algorithm
    - Redis-backed counters
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )
    
    def is_allowed(self, user_id, ip_address):
        # Implementation with sliding window...
```

### **Input Validation & Sanitization**
```python
class ChatRequestValidator:
    """Comprehensive request validation for chat endpoints."""
    
    MAX_MESSAGE_LENGTH = 32000  # Characters
    MAX_MESSAGES_PER_REQUEST = 50
    ALLOWED_MODELS = ['glm-4-32b-0414-128k', 'glm-4-plus']
    
    def validate_request(self, data):
        """Validate chat completion request."""
        errors = []
        
        # Validate messages
        messages = data.get('messages', [])
        if not messages:
            errors.append('Messages array cannot be empty')
            
        if len(messages) > self.MAX_MESSAGES_PER_REQUEST:
            errors.append(f'Too many messages (max: {self.MAX_MESSAGES_PER_REQUEST})')
            
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                errors.append(f'Message {i} must be an object')
                continue
                
            role = message.get('role')
            if role not in ['user', 'assistant', 'system']:
                errors.append(f'Invalid role in message {i}: {role}')
                
            content = message.get('content', '')
            if len(content) > self.MAX_MESSAGE_LENGTH:
                errors.append(f'Message {i} too long (max: {self.MAX_MESSAGE_LENGTH})')
                
        # Validate model
        model = data.get('model', 'glm-4-32b-0414-128k')
        if model not in self.ALLOWED_MODELS:
            errors.append(f'Invalid model: {model}')
            
        return errors
```

---

## 📊 Monitoring & Observability

### **Metrics Collection**
```python
# Prometheus metrics for monitoring
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
chat_requests_total = Counter(
    'chat_requests_total',
    'Total chat completion requests',
    ['method', 'endpoint', 'status', 'user_id']
)

chat_request_duration = Histogram(
    'chat_request_duration_seconds',
    'Chat request duration',
    ['endpoint', 'model']
)

active_sse_connections = Gauge(
    'active_sse_connections',
    'Number of active SSE connections'
)

# Token metrics
tokens_processed_total = Counter(
    'tokens_processed_total',
    'Total tokens processed',
    ['model', 'user_id']
)

# Error metrics
chat_errors_total = Counter(
    'chat_errors_total',
    'Total chat errors',
    ['error_type', 'endpoint']
)
```

### **Structured Logging**
```python
import structlog

logger = structlog.get_logger(__name__)

class SSELoggingMiddleware:
    """Structured logging for SSE requests."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # Log request start
        logger.info(
            "sse_request_start",
            request_id=request_id,
            method=request.method,
            path=request.path,
            user_id=getattr(request.user, 'id', None),
            ip_address=self.get_client_ip(request)
        )
        
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        # Log request completion
        logger.info(
            "sse_request_complete",
            request_id=request_id,
            status_code=response.status_code,
            duration_ms=int(duration * 1000),
            response_size=len(response.content) if hasattr(response, 'content') else 0
        )
        
        return response
```

### **Health Check Implementation**
```python
class ChatHealthView(APIView):
    """
    Comprehensive health check for chat system.
    
    Checks:
    - Database connectivity
    - Z.AI API availability
    - Redis cache connectivity
    - Rate limiter functionality
    """
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {}
        }
        
        # Database check
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_data['checks']['database'] = {'status': 'healthy'}
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health_data['status'] = 'degraded'
        
        # Z.AI API check
        try:
            # Quick health check to Z.AI API
            response = requests.get(
                f"{settings.ZAI_API_BASE}/health",
                timeout=5,
                headers={'Authorization': f'Bearer {settings.ZAI_API_TOKEN}'}
            )
            health_data['checks']['zai_api'] = {
                'status': 'healthy' if response.status_code == 200 else 'degraded',
                'response_time_ms': int(response.elapsed.total_seconds() * 1000)
            }
        except Exception as e:
            health_data['checks']['zai_api'] = {
                'status': 'error',
                'error': str(e)
            }
            health_data['status'] = 'degraded'
        
        # Configuration check
        health_data['checks']['configuration'] = {
            'status': 'healthy',
            'chat_transport': settings.CHAT_TRANSPORT,
            'model': settings.ZAI_DEFAULT_MODEL,
            'rate_limit': '5/min'
        }
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return Response(health_data, status=status_code)
```

---

## 🚀 Performance Optimization

### **Connection Pooling**
```python
# HTTP client optimization
class OptimizedHTTPClient:
    """Optimized HTTP client for Z.AI API communication."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            # Connection pooling
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=20,
                keepalive_expiry=30
            ),
            # Timeout configuration
            timeout=httpx.Timeout(
                connect=10.0,
                read=120.0,
                write=30.0,
                pool=5.0
            ),
            # HTTP/2 support
            http2=True,
            # Compression
            headers={'Accept-Encoding': 'gzip, deflate'}
        )
```

### **Caching Strategy**
```python
from django.core.cache import cache

class ChatCacheManager:
    """Intelligent caching for chat responses."""
    
    CACHE_TTL = {
        'user_context': 3600,      # 1 hour
        'model_config': 86400,     # 24 hours
        'rate_limit': 300,         # 5 minutes
    }
    
    def get_user_context(self, user_id):
        """Get cached user context for personalization."""
        cache_key = f"user_context:{user_id}"
        return cache.get(cache_key)
    
    def set_user_context(self, user_id, context):
        """Cache user context."""
        cache_key = f"user_context:{user_id}"
        cache.set(cache_key, context, self.CACHE_TTL['user_context'])
```

### **Async Processing**
```python
import asyncio
from asgiref.sync import sync_to_async

class AsyncChatProcessor:
    """Asynchronous chat processing for better performance."""
    
    async def process_chat_request(self, request_data, user):
        """Process chat request asynchronously."""
        
        # Parallel execution of independent tasks
        tasks = [
            self.validate_request_async(request_data),
            self.get_user_context_async(user.id),
            self.check_rate_limit_async(user.id)
        ]
        
        validation_result, user_context, rate_limit_ok = await asyncio.gather(*tasks)
        
        if not validation_result.is_valid:
            raise ValidationError(validation_result.errors)
            
        if not rate_limit_ok:
            raise RateLimitExceeded()
        
        # Stream response
        async for token in self.stream_from_zai_async(request_data):
            yield token
```

---

## 🔄 Deployment Configuration

### **Docker Configuration**
```dockerfile
# Dockerfile.chat-service
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment variables
ENV DJANGO_SETTINGS_MODULE=promptcraft.settings.production
ENV CHAT_TRANSPORT=sse
ENV WORKERS=4

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/api/v2/chat/health/ || exit 1

# Run with Gunicorn + Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "promptcraft.asgi:application"]
```

### **Load Balancer Configuration (Nginx)**
```nginx
# nginx.conf for SSE support
upstream chat_backend {
    server chat-service-1:8000;
    server chat-service-2:8000;
    server chat-service-3:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # SSE-specific configuration
    location /api/v2/chat/completions/ {
        proxy_pass http://chat_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection '';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE specific settings
        proxy_cache off;
        proxy_buffering off;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        
        # CORS for SSE
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept";
    }
}
```

### **Production Environment Variables**
```bash
# .env.production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:pass@db:5432/promptcraft

# Redis
REDIS_URL=redis://redis:6379/0

# Z.AI Configuration
ZAI_API_TOKEN=your-zai-token-here
ZAI_API_BASE=https://api.z.ai/api/paas/v4
ZAI_DEFAULT_MODEL=glm-4-32b-0414-128k

# Chat Configuration
CHAT_TRANSPORT=sse
CHAT_MAX_TOKENS=4096
CHAT_TEMPERATURE=0.7

# Security
ALLOWED_HOSTS=api.yourdomain.com,localhost
CORS_ALLOWED_ORIGINS=https://yourdomain.com,http://localhost:3000

# Monitoring
SENTRY_DSN=your-sentry-dsn-here
PROMETHEUS_ENABLED=True
```

---

## 🧪 Testing Strategy

### **Unit Tests**
```python
# tests/test_chat_views.py
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch, AsyncMock

class ChatCompletionsProxyViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('apps.chat.views.ZAIStreamingClient')
    async def test_successful_sse_stream(self, mock_zai_client):
        """Test successful SSE streaming response."""
        mock_zai_client.return_value.stream_completion = AsyncMock(
            return_value=self.mock_stream_response()
        )
        
        response = self.client.post('/api/v2/chat/completions/', {
            'messages': [{'role': 'user', 'content': 'Hello'}],
            'model': 'glm-4-32b-0414-128k',
            'stream': True
        }, HTTP_ACCEPT='text/event-stream')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Make 6 requests (limit is 5/min)
        for i in range(6):
            response = self.client.post('/api/v2/chat/completions/', {
                'messages': [{'role': 'user', 'content': f'Message {i}'}]
            })
            
            if i < 5:
                self.assertNotEqual(response.status_code, 429)
            else:
                self.assertEqual(response.status_code, 429)
```

### **Integration Tests**
```python
# tests/test_integration.py
import asyncio
import pytest
from django.test import TransactionTestCase

class SSEIntegrationTests(TransactionTestCase):
    """Integration tests for SSE chat functionality."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_chat_flow(self):
        """Test complete chat flow from request to response."""
        
        # Simulate frontend SSE connection
        client = AsyncHTTPClient()
        
        response = await client.post(
            'http://localhost:8000/api/v2/chat/completions/',
            headers={
                'Authorization': f'Bearer {self.get_jwt_token()}',
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            json={
                'messages': [{'role': 'user', 'content': 'Hello, how are you?'}],
                'model': 'glm-4-32b-0414-128k',
                'stream': True
            }
        )
        
        # Verify SSE stream
        events = []
        async for line in response.iter_lines():
            if line.startswith('data: '):
                events.append(json.loads(line[6:]))
        
        # Verify response structure
        self.assertTrue(any(event.get('stream_start') for event in events))
        self.assertTrue(any(event.get('choices') for event in events))
        self.assertTrue(any(event.get('stream_complete') for event in events))
```

### **Load Testing**
```python
# tests/load_test.py
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class LoadTester:
    """Load testing for SSE chat endpoints."""
    
    async def simulate_user_session(self, session_id):
        """Simulate a single user chat session."""
        async with aiohttp.ClientSession() as session:
            for i in range(10):  # 10 messages per user
                await self.send_chat_message(
                    session, 
                    f"User {session_id} message {i}"
                )
                await asyncio.sleep(1)  # 1 second between messages
    
    async def run_load_test(self, concurrent_users=100):
        """Run load test with multiple concurrent users."""
        tasks = [
            self.simulate_user_session(user_id) 
            for user_id in range(concurrent_users)
        ]
        
        await asyncio.gather(*tasks)
```

---

## 🔧 Troubleshooting Guide

### **Common Issues & Solutions**

#### **1. SSE Connection Drops**
```python
# Issue: Connections dropping unexpectedly
# Solution: Implement heartbeat mechanism

class SSEHeartbeat:
    async def send_heartbeat(self, response):
        """Send periodic heartbeat to keep connection alive."""
        while not response.closed:
            await response.write(b"event: heartbeat\ndata: {}\n\n")
            await asyncio.sleep(30)  # Every 30 seconds
```

#### **2. Rate Limiting Issues**
```python
# Issue: Legitimate users hitting rate limits
# Solution: Implement intelligent rate limiting

class SmartRateLimiter:
    def get_rate_limit(self, user):
        """Dynamic rate limiting based on user tier."""
        if user.is_premium:
            return '20/min'
        elif user.is_verified:
            return '10/min'
        else:
            return '5/min'
```

#### **3. Memory Leaks in Streaming**
```python
# Issue: Memory usage growing with long sessions
# Solution: Implement proper cleanup

class StreamingMemoryManager:
    def __init__(self):
        self.active_streams = {}
        self.cleanup_interval = 300  # 5 minutes
    
    async def cleanup_stale_streams(self):
        """Clean up stale streaming connections."""
        current_time = time.time()
        for stream_id, stream_data in list(self.active_streams.items()):
            if current_time - stream_data['last_activity'] > self.cleanup_interval:
                await self.close_stream(stream_id)
                del self.active_streams[stream_id]
```

---

## 📈 Performance Metrics

### **Target Performance Metrics**
- **Connection Establishment**: < 500ms
- **First Token Time**: < 2 seconds
- **Token Streaming Rate**: > 50 tokens/second
- **Concurrent Connections**: 1000+ users
- **Error Rate**: < 0.1%
- **99th Percentile Response Time**: < 5 seconds

### **Monitoring Dashboards**
```yaml
# Grafana dashboard configuration
dashboard:
  title: "Chat SSE Performance"
  panels:
    - title: "Request Rate"
      type: "graph"
      targets:
        - expr: "rate(chat_requests_total[5m])"
    
    - title: "Response Time"
      type: "graph"
      targets:
        - expr: "histogram_quantile(0.95, chat_request_duration_seconds_bucket)"
    
    - title: "Active Connections"
      type: "singlestat"
      targets:
        - expr: "active_sse_connections"
    
    - title: "Error Rate"
      type: "graph"
      targets:
        - expr: "rate(chat_errors_total[5m])"
```

---

## 🎯 Next Steps & Roadmap

### **Immediate (This Sprint)**
- [ ] **Production deployment** with blue-green strategy
- [ ] **Monitoring setup** with Prometheus + Grafana
- [ ] **Load testing** with 1000+ concurrent users
- [ ] **Documentation finalization**

### **Short Term (Next Sprint)**
- [ ] **WebSocket deprecation** and cleanup
- [ ] **Performance optimization** based on production metrics
- [ ] **Advanced rate limiting** with user tiers
- [ ] **Caching implementation** for frequently accessed data

### **Medium Term (Next Quarter)**
- [ ] **Multi-model support** (GPT-4, Claude, etc.)
- [ ] **Conversation persistence** and retrieval
- [ ] **Advanced analytics** and user insights
- [ ] **Auto-scaling** based on demand

---

**📞 Contact**: For technical questions or architecture discussions, reach out to the backend team leads or create an issue in the project repository.