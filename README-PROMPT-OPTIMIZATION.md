# Prompt Optimization Platform

A high-performance Next.js frontend with Django backend for real-time prompt optimization using WebSocket, LangChain, and vector search.

## 🚀 Features

- **Real-time Prompt Optimization** - WebSocket-based optimization with <50ms response times
- **Intelligent Search** - Vector similarity search with LangChain integration
- **Bulk Ingest** - Process 100,000+ prompts with batch optimization
- **Animated UI** - Smooth animations and real-time typing suggestions
- **Intent Analysis** - AI-powered user intent detection and categorization
- **Performance Analytics** - Real-time metrics and optimization insights

## 🏗️ Architecture

### Frontend (Next.js)
- **WebSocket Client** - Real-time communication with <50ms latency
- **Animated Components** - Framer Motion powered animations
- **Intelligent Caching** - Optimized search result caching
- **TypeScript** - Full type safety and developer experience

### Backend (Django + WebSocket)
- **Django REST API** - Robust HTTP API for data management
- **WebSocket Server** - Real-time prompt optimization
- **Vector Database** - ChromaDB for similarity search
- **LangChain Integration** - Advanced prompt engineering
- **Celery Workers** - Background task processing

## 🛠️ Setup Instructions

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL
- Redis
- OpenAI API Key (optional but recommended)

### Frontend Setup

1. **Install dependencies:**
```bash
npm install
```

2. **Environment configuration:**
Create `.env.local` and add:
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

3. **Start development server:**
```bash
npm run dev
```

### Backend Setup

1. **Run the Django setup script:**
```bash
python django_setup.py
```

2. **Create Django project (if not automated):**
```bash
# Create virtual environment
python -m venv django_backend
source django_backend/bin/activate  # On Windows: django_backend\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create Django project
django-admin startproject promptcraft_backend
cd promptcraft_backend

# Create apps
python manage.py startapp prompts
python manage.py startapp optimization
python manage.py startapp analytics
python manage.py startapp websocket_handler
```

3. **Database setup:**
```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

4. **Start services:**
```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: WebSocket server
python manage.py run_websocket_server

# Terminal 3: Celery worker
celery -A promptcraft_backend worker -l info

# Terminal 4: Celery beat (for scheduled tasks)
celery -A promptcraft_backend beat -l info
```

## 📊 Usage

### 1. Smart Search & Optimization

Access the optimization dashboard at: `http://localhost:3000/optimization`

- **Intent Analysis**: Type your prompt and get real-time intent detection
- **Optimized Suggestions**: Receive AI-optimized prompts with alternatives
- **Related Templates**: Find similar prompts from the database

### 2. Chat Interface

Use the chat interface for interactive prompt optimization:

- Real-time conversation with AI optimizer
- Live typing indicators
- Processing time metrics (<50ms target)
- Feedback system for continuous improvement

### 3. Bulk Ingest

Process large datasets:

- Upload 100,000+ prompts
- Batch processing with progress tracking
- Vector embedding generation
- Search index optimization

### 4. Analytics Dashboard

Monitor performance:

- Response time distribution
- Success rates and error tracking
- Intent category analysis
- User engagement metrics

## 🔧 Configuration

### WebSocket Configuration

The WebSocket service supports:

- **Auto-reconnection** with exponential backoff
- **Connection pooling** for multiple users
- **Message queuing** for reliability
- **Performance monitoring** with sub-50ms targeting

### Vector Search Configuration

ChromaDB configuration for optimal performance:

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Similarity Threshold**: 0.7 (configurable)
- **Batch Size**: 1000 prompts per batch
- **Index Optimization**: Automatic after bulk ingests

### Caching Strategy

Multi-layer caching:

- **Frontend**: React Query with 5-minute TTL
- **Backend**: Redis with 15-minute TTL
- **Vector Search**: In-memory caching for frequent queries
- **API Responses**: HTTP caching headers

## 🚀 Performance Optimizations

### Frontend
- **Code Splitting**: Dynamic imports for reduced bundle size
- **Image Optimization**: Next.js automatic optimization
- **Prefetching**: Smart prefetching of likely next pages
- **Memoization**: React.memo and useMemo for expensive operations

### Backend
- **Database Indexing**: Optimized indexes for frequent queries
- **Connection Pooling**: PostgreSQL connection pooling
- **Async Processing**: Celery for background tasks
- **Caching**: Redis for session and API response caching

### WebSocket
- **Binary Protocol**: Efficient message serialization
- **Connection Reuse**: Persistent connections
- **Batch Processing**: Group similar requests
- **Circuit Breaker**: Automatic fallback to HTTP API

## 📈 Monitoring & Analytics

### Key Metrics

- **Response Time**: Target <50ms for WebSocket operations
- **Throughput**: 1000+ concurrent connections supported
- **Success Rate**: >95% optimization success rate
- **Cache Hit Rate**: >80% for frequently accessed prompts

### Logging

Comprehensive logging system:

- **Application Logs**: Django + Winston for Node.js
- **Performance Logs**: Response times and error rates
- **User Analytics**: Intent patterns and usage statistics
- **System Metrics**: Resource utilization monitoring

## 🔐 Security

- **CORS Configuration**: Restricted to allowed origins
- **Rate Limiting**: API throttling (1000 req/hour per user)
- **Input Validation**: Comprehensive input sanitization
- **Authentication**: JWT-based authentication system

## 📦 Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# Scale WebSocket workers
docker-compose up -d --scale websocket=3
```

### Production Configuration

1. **Environment Variables**:
   - Set production API keys
   - Configure database URLs
   - Enable Redis clustering

2. **Performance Tuning**:
   - Enable HTTP/2
   - Configure CDN for static assets
   - Set up load balancing

3. **Monitoring**:
   - Set up application monitoring
   - Configure error tracking
   - Enable performance profiling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**:
   - Check if Redis is running
   - Verify WebSocket URL in environment
   - Ensure ports 8001 is available

2. **Slow Response Times**:
   - Check database connection pool
   - Verify Redis cache configuration
   - Monitor system resources

3. **Import Errors**:
   - Ensure all dependencies are installed
   - Check Python/Node.js versions
   - Verify virtual environment activation

### Performance Issues

1. **High Memory Usage**:
   - Tune vector database settings
   - Optimize embedding batch sizes
   - Enable memory monitoring

2. **Database Locks**:
   - Check concurrent connections
   - Optimize query performance
   - Review indexing strategy

For more help, check the documentation or open an issue on GitHub.
