# Research Agent - Enhanced Django App

The Research Agent is a sophisticated Django application that provides intelligent research capabilities with real-time streaming, evidence-bounded card synthesis, and quality guards.

## Features

### 🔍 **Intelligent Research Pipeline**
- **Web Search**: Integrates with Tavily API for comprehensive web search
- **Content Fetching**: Asynchronous URL fetching with rate limiting
- **Content Processing**: HTML cleaning, text extraction, and chunking
- **Embedding Generation**: Vector embeddings for semantic search
- **Evidence-Based Synthesis**: AI-powered content synthesis with citations

### 📊 **Card-Based Synthesis**
- **Domain Clustering**: Groups content by source domain
- **InsightCard Generation**: Creates structured insight cards with evidence
- **Quality Guards**: Multiple validation layers for content quality
- **Citation Tracking**: Comprehensive source attribution

### 🔄 **Real-Time Streaming**
- **Server-Sent Events (SSE)**: Real-time progress updates
- **Card Streaming**: Live delivery of insight cards as they're generated
- **Progress Tracking**: Detailed stage-by-stage progress reporting
- **Error Handling**: Graceful error reporting through streams

### ⚡ **Two-Lane Execution**
- **Fast Path** (`/intent_fast`): Immediate response with warm cards + background processing
- **Standard Path** (`/intent`): Full processing pipeline
- **Celery Integration**: Background task processing with priority queues

## API Endpoints

### Core Endpoints

#### POST `/api/v2/research/intent_fast/`
Fast-path endpoint that returns immediately with optional warm card.

```json
{
  "query": "What is quantum computing?",
  "top_k": 6
}
```

Response:
```json
{
  "intent_id": "uuid",
  "query": "What is quantum computing?",
  "status": "queued",
  "stream_url": "/api/v2/research/jobs/{id}/stream/",
  "cards_stream_url": "/api/v2/research/jobs/{id}/cards/stream/",
  "warm_card": {
    "id": "warm_uuid",
    "title": "Initial insights for: What is quantum computing?",
    "content": "## Researching: What is quantum computing?\n\n...",
    "type": "warm",
    "confidence": 1.0,
    "authority": 0.5
  }
}
```

#### POST `/api/v2/research/quick/`
Standard research endpoint for background processing.

#### GET `/api/v2/research/jobs/{job_id}/stream/`
Server-Sent Events stream for complete job progress.

#### GET `/api/v2/research/jobs/{job_id}/cards/stream/`
Dedicated SSE stream for card events only.

### Management Endpoints

#### GET `/api/v2/research/health/`
System health check.

#### GET `/api/v2/research/stats/`
System statistics and metrics.

## Models

### ResearchJob
Primary research task entity.

```python
class ResearchJob(models.Model):
    id = models.UUIDField(primary_key=True)
    query = models.TextField()
    top_k = models.IntegerField(default=6)
    status = models.CharField(choices=STATUS)
    created_by = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
```

### InsightCard (Pydantic Contract)
Structured insight with evidence bounds.

```python
class InsightCard(BaseModel):
    id: str
    title: str
    content: str  # Markdown content
    citations: List[CitationModel]
    confidence: float  # 0.0-1.0
    authority: float   # 0.0-1.0
    domain_cluster: Optional[str]
    tags: List[str]
```

## Quality Guards

The system implements multiple quality validation layers:

### 1. Citation Guard
Ensures cards have minimum citations.

### 2. Authority Guard  
Validates source authority scores meet thresholds.

### 3. Confidence Guard
Checks AI confidence in synthesis quality.

### 4. Content Length Guard
Ensures appropriate content length (50-2000 chars).

### 5. Duplicate Guard
Prevents similar/duplicate cards.

### 6. Relevance Guard
Validates relevance to original query.

## Configuration

Add to `settings.py`:

```python
# Research Agent Configuration
RESEARCH = {
    'SEARCH_PROVIDER': 'tavily',
    'SEARCH_TOP_K': 8,
    'MAX_PAGES': 12,
    'FETCH_TIMEOUT_S': 15,
    'MAX_TOKENS_PER_CHUNK': 800,
    'CHUNK_OVERLAP_TOKENS': 120,
    'MIN_AUTHORITY_SCORE': 0.6,
    'MIN_CONFIDENCE_SCORE': 0.5,
    'MAX_CARDS_PER_DOMAIN': 2,
    'ENABLE_QUALITY_GUARDS': True,
    'ENABLE_DOMAIN_CLUSTERING': True,
}

# Tavily API Key
TAVILY_API_KEY = 'your_tavily_api_key'

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'research_agent',
]
```

## Installation

1. **Install Dependencies**:
```bash
pip install tavily-python httpx bleach pydantic orjson sentence-transformers
```

2. **Run Migrations**:
```bash
python manage.py makemigrations research_agent
python manage.py migrate
```

3. **Configure API Keys**:
Set `TAVILY_API_KEY` in your environment or settings.

4. **Start Celery Workers**:
```bash
# High priority queue for intent processing
celery -A your_project worker -Q high --concurrency=4

# Default queue for synthesis
celery -A your_project worker -Q default --concurrency=2

# Low priority queue for background tasks
celery -A your_project worker -Q low --concurrency=1
```

## Usage Examples

### JavaScript Client

```javascript
// Start research
const response = await fetch('/api/v2/research/intent_fast/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        query: 'What are the latest developments in AI?',
        top_k: 8
    })
});

const { intent_id, warm_card, cards_stream_url } = await response.json();

// Display warm card immediately
if (warm_card) {
    displayCard(warm_card);
}

// Listen for real-time cards
const eventSource = new EventSource(cards_stream_url);

eventSource.addEventListener('card', (event) => {
    const card = JSON.parse(event.data);
    displayCard(card);
});

eventSource.addEventListener('synthesis', (event) => {
    const progress = JSON.parse(event.data);
    updateProgress(progress);
});

eventSource.addEventListener('end', (event) => {
    console.log('Research completed');
    eventSource.close();
});
```

### Python Client

```python
import requests
import json

# Start research
response = requests.post('http://localhost:8000/api/v2/research/intent_fast/', json={
    'query': 'Explain machine learning fundamentals',
    'top_k': 6
})

data = response.json()
intent_id = data['intent_id']

# Monitor progress
import sseclient

messages = sseclient.SSEClient(data['stream_url'])
for msg in messages:
    if msg.event == 'card':
        card = json.loads(msg.data)
        print(f"New card: {card['title']}")
    elif msg.event == 'end':
        break
```

## SSE Event Types

| Event | Description | Data |
|-------|-------------|------|
| `planning` | Research planning phase | `{query, search_terms, stage}` |
| `searching` | Web search in progress | `{searches_completed, urls_found}` |
| `clustering` | Domain clustering | `{clusters_created, domains}` |
| `fetching` | Content fetching | `{urls_processed, total_urls, progress_percent}` |
| `synthesis` | Card synthesis | `{cards_generated, cards_rejected}` |
| `card` | New insight card | `{InsightCard object}` |
| `update` | General progress | `{stage, message, timestamp}` |
| `end` | Research completed | `{total_cards, processing_time_ms}` |
| `error` | Error occurred | `{error, stage, timestamp}` |

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django Views   │    │   Celery Tasks  │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Intent Fast │─┼────┤ │ intent_fast  │ │    │ │ High Queue  │ │
│ │   Request   │ │    │ │   Endpoint   │ │────┤ │   Planning  │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │   Search    │ │
│                 │    │                  │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ SSE Stream  │◄┼────┤ │ Stream Cards │ │    │ │Default Queue│ │
│ │  Listener   │ │    │ │   Endpoint   │ │    │ │ Synthesis   │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │ Processing  │ │
└─────────────────┘    └──────────────────┘    │ └─────────────┘ │
                                               │ ┌─────────────┐ │
┌─────────────────┐    ┌──────────────────┐    │ │ Low Queue   │ │
│   Redis Cache   │    │  Research Agent  │    │ │ Cleanup     │ │
│                 │    │                  │    │ │ Maintenance │ │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ └─────────────┘ │
│ │ SSE Events  │ │◄───┤ │    Agent     │ │    └─────────────────┘
│ │   Buffer    │ │    │ │ Orchestrator │ │
│ └─────────────┘ │    │ └──────────────┘ │
│                 │    │ ┌──────────────┐ │    ┌─────────────────┐
│ ┌─────────────┐ │    │ │Quality Guards│ │    │   External APIs │
│ │ Job State   │ │    │ │   Synthesis  │ │    │                 │
│ │   Cache     │ │    │ │   Streaming  │ │────┤ │ Tavily Search │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │ DeepSeek AI   │ │
└─────────────────┘    └──────────────────┘    │ │ Content URLs  │ │
                                               └─────────────────┘
```

## Testing

Run tests with:

```bash
python manage.py test research_agent
```

Test coverage includes:
- Model creation and validation
- API endpoint functionality
- Quality guard validation
- SSE streaming endpoints
- Utility functions
- InsightCard contracts

## Performance Considerations

- **Async Processing**: All I/O operations are asynchronous
- **Rate Limiting**: Built-in throttling for API endpoints
- **Caching**: Redis caching for SSE events and job state
- **Quality Guards**: Efficient validation with early exit
- **Database Optimization**: Optimized queries with select_related/prefetch_related
- **Memory Management**: Chunked processing and cleanup tasks

## Monitoring and Maintenance

### Health Check
GET `/api/v2/research/health/` provides system health status.

### Statistics
GET `/api/v2/research/stats/` provides usage statistics.

### Cleanup Tasks
Automated cleanup of old jobs and associated data.

### Logging
Comprehensive logging with configurable levels:
- Research pipeline progress
- Quality guard results
- SSE streaming events
- Error conditions

## Contributing

1. Follow Django best practices
2. Add tests for new functionality
3. Update documentation
4. Follow semantic versioning
5. Use type hints consistently

## License

This research agent is part of the PromptCraft application.