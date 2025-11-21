# RAG Agent for Prompt Optimization

## Overview

The RAG (Retrieval-Augmented Generation) Agent is an intelligent prompt optimization system that leverages internal knowledge to enhance user prompts. It integrates seamlessly with the existing PromptCraft infrastructure while adding powerful document retrieval and context-aware optimization capabilities.

## Architecture

### Components

1. **Document Indexer** - Loads and indexes content from:
   - Markdown documentation files
   - Template database (high-quality prompts)
   - Application documentation
   - Usage history and patterns

2. **RAG Retriever** - Uses FAISS vector search to find relevant context:
   - Semantic similarity search
   - Metadata filtering
   - Citation generation

3. **RAG Agent** - Orchestrates optimization process:
   - Budget-aware processing
   - Context compression
   - Prompt optimization with citations
   - Streaming response generation

4. **Credit Integration** - Enforces usage limits:
   - Trial user limitations (3 credits/day)
   - Subscription-based quotas
   - Token counting and billing

## API Endpoints

### POST /v1/ai-services/agent/optimize/

Optimizes a prompt using RAG with internal knowledge base.

**Request:**
```json
{
  "session_id": "string",
  "original": "string",
  "mode": "fast|deep",
  "context": {
    "intent": "code|summarize|rewrite|...",
    "domain": "docs|templates|history"
  },
  "budget": {
    "tokens_in": 2000,
    "tokens_out": 800,
    "max_credits": 5
  }
}
```

**Response:**
```json
{
  "optimized": "string",
  "citations": [
    {
      "id": "string",
      "title": "string",
      "source": "string",
      "score": 0.82
    }
  ],
  "diff_summary": "bullet list of improvements",
  "usage": {
    "tokens_in": 123,
    "tokens_out": 456,
    "credits": 2
  },
  "run_id": "uuid",
  "processing_time_ms": 250
}
```

### GET /v1/ai-services/agent/stats/

Get RAG agent statistics (staff only).

**Response:**
```json
{
  "index_status": {
    "available": true,
    "document_count": 150,
    "chunk_count": 1200,
    "last_build": "2025-01-01T12:00:00Z"
  },
  "user_usage": {
    "api_calls_today": 5,
    "api_limit": 50,
    "subscription_active": true
  },
  "system_metrics": {
    "optimizations_today": 1250,
    "avg_processing_time": 280,
    "success_rate": 0.95
  }
}
```

## WebSocket Protocol Extensions

The RAG agent adds new WebSocket events while maintaining compatibility with existing chat protocol.

### New Event Types

#### agent.start
```json
{
  "type": "agent.start",
  "run_id": "uuid",
  "session_id": "string",
  "mode": "fast|deep",
  "budget": { "tokens_in": 2000, "tokens_out": 800, "max_credits": 5 }
}
```

#### agent.step
```json
{
  "type": "agent.step",
  "run_id": "uuid",
  "tool": "retriever|optimizer|compressor",
  "note": "human-readable status"
}
```

#### agent.token
```json
{
  "type": "agent.token",
  "run_id": "uuid",
  "content": "streaming optimized content..."
}
```

#### agent.citations
```json
{
  "type": "agent.citations",
  "run_id": "uuid",
  "citations": [
    {
      "id": "doc_123",
      "title": "Email Writing Best Practices",
      "source": "templates",
      "score": 0.85,
      "snippet": "Professional emails should..."
    }
  ]
}
```

#### agent.done
```json
{
  "type": "agent.done",
  "run_id": "uuid",
  "optimized": "final optimized prompt",
  "diff_summary": "• Added specific context\n• Improved clarity\n• Enhanced structure",
  "usage": { "tokens_in": 145, "tokens_out": 89, "credits": 1 }
}
```

#### agent.error
```json
{
  "type": "agent.error",
  "run_id": "uuid",
  "code": "insufficient_credits|cancelled|optimization_failed",
  "message": "human-readable error message"
}
```

### Client Usage

```javascript
// Send optimization request
ws.send(JSON.stringify({
  type: 'agent_optimize',
  original: 'Write a professional email',
  mode: 'fast',
  context: { intent: 'business' },
  budget: { max_credits: 3 }
}));

// Handle streaming events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'agent.start':
      console.log('Optimization started:', data.run_id);
      break;
    case 'agent.step':
      console.log('Processing:', data.note);
      break;
    case 'agent.token':
      appendStreamingContent(data.content);
      break;
    case 'agent.citations':
      displayCitations(data.citations);
      break;
    case 'agent.done':
      showFinalResult(data.optimized, data.diff_summary);
      break;
    case 'agent.error':
      handleError(data.code, data.message);
      break;
  }
};
```

## Setup and Configuration

### 1. Environment Variables

Add to your `.env` file:
```env
# Vector store configuration
ENABLE_VECTOR_SEARCH=True
VECTOR_STORE_TYPE=faiss  # faiss|redis|pgvector

# Embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# RAG settings
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=150
RAG_TOP_K=6
RAG_SIMILARITY_THRESHOLD=0.7

# Budget limits
RAG_DEFAULT_TOKENS_IN=2000
RAG_DEFAULT_TOKENS_OUT=800
RAG_MAX_CREDITS_PER_REQUEST=10
RAG_TRIAL_DAILY_LIMIT=3
```

### 2. Build the RAG Index

```bash
# Build the vector index
python manage.py build_rag_index

# Force rebuild
python manage.py build_rag_index --force

# Verbose output
python manage.py build_rag_index --verbose --force
```

### 3. Background Index Updates

If Celery is configured, the index can be rebuilt automatically:

```python
# In your Celery beat schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'rebuild-rag-index': {
        'task': 'apps.ai_services.rag_service.rebuild_rag_index',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

## Credit System Integration

### Trial Users
- 3 optimizations per day
- Fast mode only
- Basic citations

### Basic Subscribers
- 20 optimizations per day
- Fast and deep modes
- Full citations with snippets

### Premium Subscribers
- 100 optimizations per day
- All features
- Priority processing

### Credit Costs
- **Fast mode**: 1 credit
- **Deep mode**: 3 credits
- **Failed requests**: No charge

## Performance Optimization

### Caching Strategy
- **Document cache**: 1 hour TTL
- **Retrieval cache**: 15 minutes TTL
- **Idempotency cache**: 1 hour TTL

### Index Management
- **Incremental updates**: Check file modification times
- **Batch processing**: 100 documents per batch
- **Memory optimization**: Stream large files

### Response Times
- **Target first token**: < 300ms
- **P95 processing time**: < 700ms
- **Index loading**: < 2 seconds (cold start)

## Monitoring and Analytics

### Metrics Tracked
- Optimization success rate
- Average processing time
- Credit consumption patterns
- Popular optimization types
- Citation relevance scores

### Logging
```python
# RAG-specific logs
logger.info(f"RAG optimization: user={user_id}, mode={mode}, tokens={tokens}")
logger.warning(f"RAG retrieval failed: {error}")
logger.error(f"Index building failed: {error}")
```

### Health Checks
```bash
# Check RAG system health
curl http://localhost:8000/v1/ai-services/agent/stats/

# Check index status
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/v1/ai-services/agent/stats/
```

## Security Considerations

### Input Sanitization
- Strip dangerous directives
- Limit prompt length (10,000 chars)
- Validate session IDs

### Content Filtering
- Exclude PII from indexing
- Filter sensitive internal docs
- Sanitize HTML in responses

### Rate Limiting
- 20 requests per hour per user
- Exponential backoff for failures
- IP-based rate limiting for anonymous users

## Troubleshooting

### Common Issues

#### "No documents found for indexing"
```bash
# Check if markdown files exist
ls *.md

# Check template database
python manage.py shell -c "from apps.templates.models import PromptLibrary; print(PromptLibrary.objects.count())"
```

#### "Embeddings not available"
```bash
# Install required packages
pip install sentence-transformers transformers torch

# Check model download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

#### "FAISS index corrupted"
```bash
# Rebuild index
python manage.py build_rag_index --force

# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

### Debug Mode
```python
# Enable verbose logging
import logging
logging.getLogger('apps.ai_services.rag_service').setLevel(logging.DEBUG)
```

## Development

### Adding New Document Sources
```python
# In DocumentIndexer._load_custom_source()
def _load_custom_source(self) -> List[RAGDocument]:
    documents = []
    # Load from your custom source
    # Return RAGDocument instances
    return documents
```

### Custom Retrieval Logic
```python
# Extend RAGRetriever
class CustomRetriever(RAGRetriever):
    def retrieve_documents(self, query: str, filters: Dict = None):
        # Custom retrieval logic
        pass
```

### Frontend Integration Helpers

#### React Hook Example
```typescript
// useRAGAgent.ts
export const useRAGAgent = (websocket: WebSocket) => {
  const [optimizing, setOptimizing] = useState(false);
  const [result, setResult] = useState(null);
  const [citations, setCitations] = useState([]);

  const optimizePrompt = (prompt: string, mode: 'fast' | 'deep' = 'fast') => {
    setOptimizing(true);
    websocket.send(JSON.stringify({
      type: 'agent_optimize',
      original: prompt,
      mode,
      context: { intent: 'general' }
    }));
  };

  useEffect(() => {
    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'agent.citations') {
        setCitations(data.citations);
      } else if (data.type === 'agent.done') {
        setResult(data.optimized);
        setOptimizing(false);
      }
    };

    websocket.addEventListener('message', handleMessage);
    return () => websocket.removeEventListener('message', handleMessage);
  }, [websocket]);

  return { optimizing, result, citations, optimizePrompt };
};
```

## Migration Guide

### From Existing Optimization
1. RAG agent works alongside existing optimization
2. New WebSocket events are additive
3. REST endpoint is separate (`/agent/optimize/` vs `/optimize/`)
4. Credit system integrates with existing billing

### Frontend Updates
1. Add RAG mode selector
2. Display citations in UI
3. Handle streaming optimization
4. Show budget/credit status

### Backend Updates
1. Run `build_rag_index` command
2. Update WebSocket routing if needed
3. Configure environment variables
4. Test credit integration

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: 2025-01-04  
**Compatibility**: Django 4.2+, LangChain 0.1+, FAISS 1.7+