# Complete API Endpoints & AI Services Documentation

## Overview
Comprehensive documentation of all API endpoints for the PromptCraft backend, organized by service module with full request/response specifications.

**Base URL**: `http://localhost:8000/api/v2` (local development)

---

## 1. AI SERVICES ENDPOINTS

### 1.1 Provider Management

#### GET `/ai-services/providers/`
**Description**: List all available AI providers (OpenAI, Anthropic, DeepSeek, OpenRouter)

**Authentication**: Required (Token/Session)

**Request**:
```http
GET /api/v2/ai-services/providers/ HTTP/1.1
Authorization: Bearer YOUR_TOKEN
```

**Response** (200 OK):
```json
{
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "status": "available",
      "models": ["gpt-3.5-turbo", "gpt-4"],
      "features": ["chat", "completion", "embeddings"]
    },
    {
      "id": "deepseek",
      "name": "DeepSeek",
      "status": "available",
      "models": ["deepseek-chat", "deepseek-coder", "deepseek-math"],
      "features": ["chat", "code_generation", "optimization", "cost_effective"],
      "cost_per_1k_tokens": 0.0014,
      "max_tokens": 4000
    },
    {
      "id": "openrouter",
      "name": "OpenRouter",
      "status": "available",
      "models": ["qwen/qwen3-next-80b-a3b-instruct:free", "deepseek/deepseek-r1"],
      "features": ["chat", "free_tier", "multiple_models"],
      "cost_per_1k_tokens": 0
    }
  ],
  "total_providers": 3,
  "deepseek_available": true,
  "openrouter_available": true
}
```

**Error Responses**:
- `401`: Unauthorized - Missing or invalid token
- `403`: Forbidden - Insufficient permissions

---

#### GET `/ai-services/models/`
**Description**: List all available AI models across providers

**Request**:
```http
GET /api/v2/ai-services/models/ HTTP/1.1
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters**:
- `provider` (optional): Filter by provider ID (e.g., `deepseek`, `openai`)
- `feature` (optional): Filter by feature (e.g., `chat`, `code_generation`)

**Response** (200 OK):
```json
{
  "models": [
    {
      "id": "gpt-4",
      "provider": "openai",
      "name": "GPT-4",
      "max_tokens": 8192,
      "cost_input": 0.03,
      "cost_output": 0.06,
      "description": "Most capable model",
      "features": ["chat", "completion", "vision"]
    },
    {
      "id": "deepseek-chat",
      "provider": "deepseek",
      "name": "DeepSeek Chat",
      "max_tokens": 4000,
      "cost_input": 0.0014,
      "cost_output": 0.0028,
      "description": "Cost-effective chat model"
    }
  ],
  "total": 12
}
```

---

### 1.2 AI Generation

#### POST `/ai-services/generate/`
**Description**: Generate content using any AI provider

**Request**:
```json
{
  "provider": "deepseek",
  "model": "deepseek-chat",
  "prompt": "Write a Python function for binary search",
  "temperature": 0.7,
  "max_tokens": 500,
  "system_message": "You are a helpful programming assistant",
  "stream": false
}
```

**Response** (200 OK - Non-streaming):
```json
{
  "content": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
  "tokens_used": 145,
  "provider": "deepseek",
  "model": "deepseek-chat",
  "execution_time": 1.23
}
```

**Response** (200 OK - Streaming SSE):
When `stream: true`, response is Server-Sent Events (SSE):
```
data: "def binary_search"
data: "(arr, target):"
data: "\n    left"
...
```

---

### 1.3 DeepSeek Streaming

#### POST `/ai-services/deepseek/stream/`
**Description**: Real-time streaming proxy for DeepSeek API

**Request**:
```json
{
  "message": "Explain quantum computing",
  "max_tokens": 1500,
  "temperature": 0.7
}
```

**Response**: Server-Sent Events Stream
```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "start", "provider": "deepseek"}
data: {"type": "chunk", "content": "Quantum computing is"}
data: {"type": "chunk", "content": " a revolutionary"}
data: {"type": "done", "tokens": 89}
```

#### POST `/ai-services/deepseek/chat/`
**Description**: Standard DeepSeek chat endpoint (non-streaming)

**Request**:
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello, what can you do?"}
  ],
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response** (200 OK):
```json
{
  "response": "I can help you with...",
  "tokens_used": 87,
  "model": "deepseek-chat"
}
```

#### GET `/ai-services/deepseek/test/`
**Description**: Test DeepSeek connection and API key validity

**Response** (200 OK):
```json
{
  "status": "connected",
  "api_key_valid": true,
  "available_models": ["deepseek-chat", "deepseek-coder"],
  "last_tested": "2024-02-24T10:30:00Z",
  "response_time_ms": 234
}
```

---

### 1.4 AI Usage & Quotas

#### GET `/ai-services/usage/`
**Description**: Get current AI usage statistics for authenticated user

**Request**:
```http
GET /api/v2/ai-services/usage/?period=7d HTTP/1.1
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters**:
- `period`: `24h`, `7d`, `30d`, `all` (default: `30d`)

**Response** (200 OK):
```json
{
  "user_id": "uuid",
  "period": "7d",
  "total_tokens_used": 15234,
  "total_cost": 0.45,
  "by_provider": {
    "deepseek": {
      "tokens_used": 10000,
      "cost": 0.15,
      "requests": 25
    },
    "openai": {
      "tokens_used": 5234,
      "cost": 0.30,
      "requests": 8
    }
  },
  "daily_breakdown": [
    {"date": "2024-02-18", "tokens": 2000, "cost": 0.06},
    {"date": "2024-02-19", "tokens": 2100, "cost": 0.07}
  ]
}
```

---

#### GET `/ai-services/quotas/`
**Description**: Get current quota limits and usage

**Response** (200 OK):
```json
{
  "monthly_quota": {
    "tokens": 1000000,
    "cost_limit": 50.0,
    "requests_limit": 1000
  },
  "current_usage": {
    "tokens_used": 145234,
    "cost_used": 8.34,
    "requests_used": 234
  },
  "remaining": {
    "tokens": 854766,
    "cost_budget": 41.66,
    "requests": 766
  },
  "reset_date": "2024-03-01",
  "usage_percentage": 14.5
}
```

---

## 2. AI ASSISTANT ENDPOINTS

### 2.1 Assistant Management

#### GET `/ai-services/assistant/`
**Description**: List all AI assistants available to user

**Response** (200 OK):
```json
{
  "assistants": [
    {
      "id": "uuid",
      "name": "Code Wizard",
      "description": "Expert programming assistant",
      "provider": "deepseek",
      "model": "deepseek-coder",
      "system_prompt": "You are an expert programmer...",
      "created_at": "2024-01-15T10:30:00Z",
      "last_used": "2024-02-24T09:15:00Z"
    },
    {
      "id": "uuid",
      "name": "Content Creator",
      "description": "Writing and content generation",
      "provider": "openai",
      "model": "gpt-4",
      "system_prompt": "You are a creative writer...",
      "created_at": "2024-01-10T08:00:00Z",
      "last_used": "2024-02-22T14:45:00Z"
    }
  ],
  "total": 2
}
```

---

#### POST `/ai-services/assistant/run/`
**Description**: Execute an AI assistant with a message

**Request**:
```json
{
  "assistant_id": "uuid-of-assistant",
  "message": "Help me debug this code",
  "thread_id": "uuid-optional-thread",
  "stream": false
}
```

**Response** (200 OK):
```json
{
  "response": "I'd be happy to help debug your code...",
  "thread_id": "uuid-thread",
  "assistant_id": "uuid-assistant",
  "tokens_used": 234,
  "execution_time": 2.1,
  "citations": []
}
```

---

### 2.2 Assistant Threads

#### GET `/ai-services/assistant/threads/`
**Description**: List conversation threads for authenticated user

**Response** (200 OK):
```json
{
  "threads": [
    {
      "id": "uuid",
      "assistant_id": "uuid",
      "title": "Code Review Discussion",
      "message_count": 5,
      "created_at": "2024-02-20T10:30:00Z",
      "last_message_at": "2024-02-24T09:15:00Z",
      "preview": "Help me debug this code..."
    }
  ],
  "total": 1
}
```

---

#### GET `/ai-services/assistant/threads/{thread_id}/`
**Description**: Get specific thread with full conversation history

**Response** (200 OK):
```json
{
  "thread": {
    "id": "uuid",
    "assistant_id": "uuid",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "Help me debug this code",
        "created_at": "2024-02-20T10:30:00Z"
      },
      {
        "id": "msg-2",
        "role": "assistant",
        "content": "I'd be happy to help...",
        "created_at": "2024-02-20T10:31:00Z"
      }
    ],
    "created_at": "2024-02-20T10:30:00Z"
  }
}
```

---

## 3. PROMPT OPTIMIZATION ENDPOINTS

### 3.1 Optimization

#### POST `/ai-services/optimization/`
**Description**: Optimize user prompt using AI

**Request**:
```json
{
  "prompt": "write code to sort array",
  "context": "Python, beginner-friendly",
  "optimization_type": "clarity",
  "stream": false
}
```

**Response** (200 OK):
```json
{
  "original_prompt": "write code to sort array",
  "optimized_prompt": "Create a Python function that sorts an array of integers in ascending order using the most efficient built-in method. Include comments explaining the approach and provide an example usage.",
  "improvements": [
    "Added specific language (Python)",
    "Clarified the data type",
    "Specified sort order",
    "Added documentation requirement"
  ],
  "optimization_score": 8.5,
  "execution_time": 1.23
}
```

#### POST `/ai-services/optimization/stream/`
**Description**: Streaming optimization endpoint

**Response**: Server-Sent Events
```
data: {"type": "start"}
data: {"type": "chunk", "content": "Create a Python"}
data: {"type": "improvements", "list": [...]}
data: {"type": "complete", "score": 8.5}
```

---

## 4. RAG (RETRIEVAL-AUGMENTED GENERATION) ENDPOINTS

### 4.1 RAG Agent Operations

#### POST `/ai-services/agent/optimize/`
**Description**: Optimize prompt using RAG agent

**Request**:
```json
{
  "prompt": "How do I deploy a Django app?",
  "knowledge_base": "django-docs",
  "max_sources": 5
}
```

**Response** (200 OK):
```json
{
  "optimized_prompt": "...",
  "sources": [
    {
      "title": "Django Deployment Guide",
      "url": "...",
      "relevance": 0.95
    }
  ],
  "execution_time": 2.34
}
```

---

#### POST `/ai-services/rag/retrieve/`
**Description**: Retrieve relevant documents from knowledge base

**Request**:
```json
{
  "query": "How to handle authentication in Django REST Framework?",
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "id": "doc-1",
      "title": "DRF Authentication",
      "content": "...",
      "similarity_score": 0.92,
      "source": "documentation"
    }
  ],
  "total_found": 5,
  "execution_time": 0.85
}
```

---

#### POST `/ai-services/rag/answer/`
**Description**: Generate answer based on retrieved documents

**Request**:
```json
{
  "question": "How to set up JWT authentication?",
  "documents": ["doc-1", "doc-2"],
  "model": "deepseek-chat",
  "include_sources": true
}
```

**Response** (200 OK):
```json
{
  "answer": "To set up JWT authentication in Django REST Framework...",
  "sources": [
    {"title": "...", "url": "..."}
  ],
  "confidence": 0.89,
  "execution_time": 1.56
}
```

---

## 5. ASK-ME (GUIDED PROMPT BUILDER) ENDPOINTS

### 5.1 Session Management

#### POST `/ai-services/askme/start/`
**Description**: Start a new Ask-Me guided session

**Request**:
```json
{
  "intent": "Create a Python web scraper for e-commerce",
  "context": "Python, experienced programming"
}
```

**Response** (200 OK):
```json
{
  "session_id": "uuid-session",
  "intent": "Create a Python web scraper for e-commerce",
  "questions": [
    {
      "qid": "q1",
      "title": "Target Website",
      "kind": "text",
      "help_text": "Which website do you want to scrape?",
      "is_required": true,
      "suggested_answer": "example.com"
    },
    {
      "qid": "q2",
      "title": "Data to Extract",
      "kind": "checkbox",
      "options": ["Product Name", "Price", "Description", "Images"],
      "is_required": true
    }
  ],
  "good_enough_to_run": false,
  "completion_percentage": 0
}
```

---

#### POST `/ai-services/askme/answer/`
**Description**: Submit answer to an Ask-Me question

**Request**:
```json
{
  "session_id": "uuid-session",
  "qid": "q1",
  "value": "amazon.com"
}
```

**Response** (200 OK):
```json
{
  "session_id": "uuid-session",
  "qid": "q1",
  "is_answered": true,
  "answered_at": "2024-02-24T10:30:00Z",
  "next_questions": [
    {
      "qid": "q2",
      "title": "Data to Extract",
      "kind": "checkbox",
      "options": ["Product Name", "Price", "Description", "Images"]
    }
  ],
  "completion_percentage": 33,
  "good_enough_to_run": false,
  "preview_prompt": "Create a Python web scraper for amazon.com to extract..."
}
```

---

#### POST `/ai-services/askme/finalize/`
**Description**: Complete Ask-Me session and generate final prompt

**Request**:
```json
{
  "session_id": "uuid-session",
  "generate_code": true,
  "code_language": "python"
}
```

**Response** (200 OK):
```json
{
  "session_id": "uuid-session",
  "is_complete": true,
  "final_prompt": "Create a Python web scraper for amazon.com...",
  "generated_code": "import requests\nfrom bs4 import BeautifulSoup\n...",
  "answered_vars": {
    "target": "amazon.com",
    "fields": ["Product Name", "Price"]
  },
  "completion_percentage": 100
}
```

---

#### GET `/ai-services/askme/sessions/`
**Description**: List all Ask-Me sessions for user

**Response** (200 OK):
```json
{
  "sessions": [
    {
      "id": "uuid",
      "intent": "Create a Python web scraper",
      "completion_percentage": 100,
      "is_complete": true,
      "created_at": "2024-02-20T10:30:00Z",
      "updated_at": "2024-02-20T11:45:00Z"
    }
  ],
  "total": 1,
  "completed": 1,
  "in_progress": 0
}
```

---

#### GET `/ai-services/askme/sessions/{session_id}/`
**Description**: Get specific Ask-Me session details

**Response** (200 OK):
```json
{
  "session": {
    "id": "uuid",
    "intent": "Create a Python web scraper",
    "questions": [
      {
        "qid": "q1",
        "title": "Target Website",
        "kind": "text",
        "answer": "amazon.com",
        "is_answered": true
      }
    ],
    "is_complete": true,
    "final_prompt": "...",
    "completion_percentage": 100
  }
}
```

---

#### POST `/ai-services/askme/stream/`
**Description**: Stream generation of optimizations or code during Ask-Me

**Request**:
```json
{
  "session_id": "uuid-session"
}
```

**Response**: Server-Sent Events
```
data: {"type": "optimizing"}
data: {"type": "prompt_chunk", "content": "Create a"}
data: {"type": "complete"}
```

---

## Authentication

All endpoints (except `/health/`) require authentication. Supported methods:

### Token Authentication
```http
Authorization: Bearer YOUR_TOKEN
```

### Session Authentication
```http
Cookie: sessionid=YOUR_SESSION_ID
```

---

## Error Handling

### Standard Error Response
```json
{
  "error": "Invalid request",
  "detail": "Required field 'prompt' missing",
  "code": "MISSING_FIELD",
  "timestamp": "2024-02-24T10:30:00Z"
}
```

### Common Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Rate Limited
- `500`: Server Error

---

## Rate Limiting

- **Authenticated Users**: 1000 requests/hour
- **Streaming Requests**: No limit (counted separately)
- **AI Generation**: 100 requests/hour per provider

---

## Next Steps

1. **Local Testing**: See [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)
2. **Integration**: See [AI_SERVICES_INTEGRATION.md](AI_SERVICES_INTEGRATION.md)
3. **Iteration Framework**: See [ITERATION_TESTING_FRAMEWORK.md](ITERATION_TESTING_FRAMEWORK.md)
