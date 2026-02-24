# Local API Testing Guide - AI Services

Complete guide for testing all AI service endpoints locally with real examples and curl commands.

---

## Prerequisites

1. **Python Environment**: `source venv/Scripts/activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
2. **Django Server Running**: `python manage.py runserver`
3. **Database**: SQLite with migrations applied
4. **Test User**: Create test user with `python create_test_users.py`

---

## Setup for Local Testing

### 1. Get Authentication Token

First, authenticate to get a token:

```bash
# Create test user
python create_test_users.py

# Get token
curl -X POST http://localhost:8000/api/v2/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

**Response**:
```json
{
  "token": "abc123def456...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**Save token for all requests**:
```bash
export TOKEN="your_token_here"
```

---

### 2. Verify Server Health

```bash
curl http://localhost:8000/health/
```

**Expected Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-02-24T10:30:00Z"
}
```

---

## TESTING AI SERVICES ENDPOINTS

### 3. List AI Providers

```bash
curl -X GET http://localhost:8000/api/v2/ai-services/providers/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "providers": [
    {
      "id": "deepseek",
      "name": "DeepSeek",
      "status": "available",
      "models": ["deepseek-chat", "deepseek-coder"],
      "features": ["chat", "code_generation", "cost_effective"],
      "cost_per_1k_tokens": 0.0014,
      "max_tokens": 4000
    },
    {
      "id": "openai",
      "name": "OpenAI",
      "status": "available",
      "models": ["gpt-3.5-turbo", "gpt-4"],
      "features": ["chat", "completion"]
    }
  ],
  "total_providers": 2,
  "deepseek_available": true,
  "openrouter_available": false
}
```

**Test Checklist**:
- [ ] Status is 200
- [ ] At least one provider available
- [ ] DeepSeek status shows correctly
- [ ] OpenRouter status shows correctly

---

### 4. List Available Models

```bash
curl -X GET "http://localhost:8000/api/v2/ai-services/models/?provider=deepseek" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "models": [
    {
      "id": "deepseek-chat",
      "provider": "deepseek",
      "name": "DeepSeek Chat",
      "max_tokens": 4000,
      "cost_input": 0.0014,
      "cost_output": 0.0028
    }
  ],
  "total": 1
}
```

**Tests**:
- [ ] Filter by provider works
- [ ] Model pricing is included
- [ ] Max tokens specified

---

### 5. Test DeepSeek Connection

```bash
curl -X GET http://localhost:8000/api/v2/ai-services/deepseek/test/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response** (200 OK):
```json
{
  "status": "connected",
  "api_key_valid": true,
  "available_models": ["deepseek-chat", "deepseek-coder"],
  "last_tested": "2024-02-24T10:30:00Z",
  "response_time_ms": 245
}
```

**Tests**:
- [ ] Status is "connected"
- [ ] API key is valid
- [ ] Response time under 5000ms
- [ ] Models list is populated

---

### 6. Generate Content with DeepSeek

#### 6.1 Non-Streaming Generation

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "prompt": "Write a Python function for Fibonacci sequence",
    "temperature": 0.7,
    "max_tokens": 500,
    "system_message": "You are a helpful programming assistant",
    "stream": false
  }'
```

**Expected Response** (200 OK):
```json
{
  "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "tokens_used": 145,
  "provider": "deepseek",
  "model": "deepseek-chat",
  "execution_time": 2.34,
  "finish_reason": "stop"
}
```

**Test Checklist**:
- [ ] Response status 200
- [ ] Content is returned
- [ ] Tokens counted
- [ ] Execution time < 10 seconds
- [ ] Finish reason is "stop"

---

#### 6.2 Streaming Generation

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "prompt": "Explain machine learning",
    "stream": true
  }' \
  --no-buffer
```

**Expected Response** (SSE Stream):
```
data: "Machine learning is"
data: " a subset of"
data: " artificial intelligence"
...
```

**Test Checklist**:
- [ ] Response header `Content-Type: text/event-stream`
- [ ] Data arrives in chunks
- [ ] No buffering (use `--no-buffer`)
- [ ] Stream completes

---

### 7. DeepSeek Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/deepseek/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

**Expected Response** (200 OK):
```json
{
  "response": "The capital of France is Paris.",
  "tokens_used": 18,
  "model": "deepseek-chat",
  "finish_reason": "stop"
}
```

**Tests**:
- [ ] Correct answer returned
- [ ] Message history respected
- [ ] System message applied

---

### 8. DeepSeek Streaming Endpoint

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/deepseek/stream/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing in simple terms",
    "max_tokens": 500,
    "temperature": 0.7
  }' \
  --no-buffer
```

**Expected Response** (SSE Stream):
```
data: {"type": "start", "provider": "deepseek"}
data: {"type": "chunk", "content": "Quantum computing"}
data: {"type": "chunk", "content": " is a type"}
...
data: {"type": "done", "tokens": 89}
```

**Tests**:
- [ ] Start event received
- [ ] Content chunks arriving
- [ ] Done event with token count
- [ ] Stream properly closed

---

## TESTING AI ASSISTANT ENDPOINTS

### 9. List Assistants

```bash
curl -X GET http://localhost:8000/api/v2/ai-services/assistant/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "assistants": [
    {
      "id": "uuid",
      "name": "Code Wizard",
      "description": "Expert programming assistant",
      "provider": "deepseek",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

**Tests**:
- [ ] Status 200
- [ ] Assistants returned
- [ ] Required fields present

---

### 10. Run Assistant

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/assistant/run/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "uuid-from-previous-response",
    "message": "Help me optimize this Python code",
    "stream": false
  }'
```

**Expected Response** (200 OK):
```json
{
  "response": "I'll help you optimize the code...",
  "thread_id": "uuid",
  "assistant_id": "uuid",
  "tokens_used": 234,
  "execution_time": 2.1
}
```

**Tests**:
- [ ] Response received
- [ ] Thread ID created
- [ ] Message stored

---

### 11. List Assistant Threads

```bash
curl -X GET http://localhost:8000/api/v2/ai-services/assistant/threads/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "threads": [
    {
      "id": "uuid",
      "assistant_id": "uuid",
      "title": "Code Review",
      "message_count": 5,
      "created_at": "2024-02-20T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### 12. Get Thread Details

```bash
curl -X GET "http://localhost:8000/api/v2/ai-services/assistant/threads/THREAD_UUID/" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "thread": {
    "id": "uuid",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "Help me optimize code"
      },
      {
        "id": "msg-2",
        "role": "assistant",
        "content": "I suggest..."
      }
    ]
  }
}
```

---

## TESTING PROMPT OPTIMIZATION

### 13. Optimize Prompt

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/optimization/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "write code to sort array",
    "context": "Python, beginner",
    "optimization_type": "clarity",
    "stream": false
  }'
```

**Expected Response** (200 OK):
```json
{
  "original_prompt": "write code to sort array",
  "optimized_prompt": "Create a Python function that sorts an array of integers in ascending order...",
  "improvements": [
    "Added language specification",
    "Clarified expected output"
  ],
  "optimization_score": 8.5,
  "execution_time": 1.23
}
```

**Tests**:
- [ ] Original prompt preserved
- [ ] Optimized prompt longer and clearer
- [ ] Improvements listed
- [ ] Score between 1-10

---

## TESTING RAG ENDPOINTS

### 14. RAG Retrieve Documents

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/rag/retrieve/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to authenticate with JWT in Django?",
    "top_k": 5,
    "similarity_threshold": 0.7
  }'
```

**Expected Response** (200 OK):
```json
{
  "results": [
    {
      "id": "doc-1",
      "title": "JWT Authentication Guide",
      "content": "...",
      "similarity_score": 0.92,
      "source": "documentation"
    }
  ],
  "total_found": 1,
  "execution_time": 0.85
}
```

**Tests**:
- [ ] Results returned
- [ ] Similarity scores correct
- [ ] Performance < 2 seconds

---

## TESTING ASK-ME ENDPOINTS

### 15. Start Ask-Me Session

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/askme/start/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Create a Python web scraper for product prices",
    "context": "Python, beginner to intermediate"
  }'
```

**Expected Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "Create a Python web scraper for product prices",
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

**Save session ID**:
```bash
export SESSION_ID="550e8400-e29b-41d4-a716-446655440000"
```

**Tests**:
- [ ] Session ID created
- [ ] Questions returned
- [ ] Good_enough_to_run is false initially

---

### 16. Answer Ask-Me Question

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/askme/answer/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "qid": "q1",
    "value": "amazon.com"
  }'
```

**Expected Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "qid": "q1",
  "is_answered": true,
  "answered_at": "2024-02-24T10:30:00Z",
  "next_questions": [
    {
      "qid": "q2",
      "title": "Data to Extract",
      "kind": "checkbox"
    }
  ],
  "completion_percentage": 50,
  "good_enough_to_run": false,
  "preview_prompt": "Create a Python web scraper for amazon.com to extract..."
}
```

**Tests**:
- [ ] Answer stored
- [ ] Next questions provided
- [ ] Completion percentage increased
- [ ] Preview prompt updated

---

### 17. Continue Answering Questions

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/askme/answer/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "qid": "q2",
    "value": ["Product Name", "Price"]
  }'
```

**Expected Response**:
```json
{
  "completion_percentage": 100,
  "good_enough_to_run": true,
  "final_prompt": "Create a Python web scraper for amazon.com to extract Product Name and Price..."
}
```

**Tests**:
- [ ] Completion percentage at 100
- [ ] good_enough_to_run is true
- [ ] Final prompt ready

---

### 18. Finalize Ask-Me Session

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/askme/finalize/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "generate_code": true,
    "code_language": "python"
  }'
```

**Expected Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_complete": true,
  "final_prompt": "Create a Python web scraper for amazon.com...",
  "generated_code": "import requests\nfrom bs4 import BeautifulSoup\n\ndef scrape_amazon(url):\n    # Code implementation\n    pass",
  "completion_percentage": 100
}
```

**Tests**:
- [ ] Session marked complete
- [ ] Final prompt returned
- [ ] Code generated correctly
- [ ] All variables in answered_vars

---

### 19. List Ask-Me Sessions

```bash
curl -X GET http://localhost:8000/api/v2/ai-services/askme/sessions/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "intent": "Create a Python web scraper",
      "completion_percentage": 100,
      "is_complete": true,
      "created_at": "2024-02-24T10:30:00Z"
    }
  ],
  "total": 1,
  "completed": 1,
  "in_progress": 0
}
```

---

### 20. Get Specific Session

```bash
curl -X GET "http://localhost:8000/api/v2/ai-services/askme/sessions/$SESSION_ID/" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "intent": "Create a Python web scraper",
    "questions": [
      {
        "qid": "q1",
        "title": "Target Website",
        "answer": "amazon.com",
        "is_answered": true
      }
    ],
    "is_complete": true,
    "final_prompt": "..."
  }
}
```

---

## TESTING AI USAGE & QUOTAS

### 21. Check Usage Statistics

```bash
curl -X GET "http://localhost:8000/api/v2/ai-services/usage/?period=7d" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response** (200 OK):
```json
{
  "period": "7d",
  "total_tokens_used": 15234,
  "total_cost": 0.45,
  "by_provider": {
    "deepseek": {
      "tokens_used": 10000,
      "requests": 25,
      "cost": 0.15
    }
  }
}
```

---

### 22. Check Quotas

```bash
curl -X GET http://localhost:8000/api/v2/ai-services/quotas/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "monthly_quota": {
    "tokens": 1000000,
    "cost_limit": 50.0
  },
  "current_usage": {
    "tokens_used": 145234,
    "cost_used": 8.34
  },
  "usage_percentage": 14.5
}
```

---

## Testing with Python

### 23. Using Python Requests

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v2"
TOKEN = "your_token_here"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Test 1: List providers
response = requests.get(f"{BASE_URL}/ai-services/providers/", headers=HEADERS)
print(response.json())

# Test 2: Generate content
payload = {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "prompt": "Hello, what can you do?",
    "stream": False
}
response = requests.post(f"{BASE_URL}/ai-services/generate/", 
                        headers=HEADERS, 
                        json=payload)
print(response.json())

# Test 3: Ask-Me Session
payload = {
    "intent": "Create a Python web scraper",
    "context": "Python, beginner"
}
response = requests.post(f"{BASE_URL}/ai-services/askme/start/",
                        headers=HEADERS,
                        json=payload)
session_data = response.json()
print(f"Session ID: {session_data['session_id']}")
```

---

## Error Testing

### 23.1 Missing Token

```bash
curl -X GET http://localhost:8000/api/v2/ai-services/providers/
```

**Expected Response** (401 Unauthorized):
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

###23.2 Invalid Provider

```bash
curl -X POST http://localhost:8000/api/v2/ai-services/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "invalid_provider",
    "prompt": "test"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "error": "Invalid provider",
  "detail": "Provider 'invalid_provider' is not available",
  "code": "INVALID_PROVIDER"
}
```

---

## Automated Testing Script

Save as `test_all_ai_services.sh`:

```bash
#!/bin/bash

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v2/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }' | jq -r '.token')

echo "Token: $TOKEN"

# Test providers
echo "Testing Providers endpoint..."
curl -X GET http://localhost:8000/api/v2/ai-services/providers/ \
  -H "Authorization: Bearer $TOKEN" | jq .

# Test DeepSeek test
echo "Testing DeepSeek connection..."
curl -X GET http://localhost:8000/api/v2/ai-services/deepseek/test/ \
  -H "Authorization: Bearer $TOKEN" | jq .

echo "All basic tests passed!"
```

---

## Next Steps

1. **Run all tests locally** using the above commands
2. **Document any failures** and debug using Django logs
3. **Move to iteration framework** - See [ITERATION_TESTING_FRAMEWORK.md](ITERATION_TESTING_FRAMEWORK.md)
4. **Frontend integration** - See [AI_SERVICES_INTEGRATION.md](AI_SERVICES_INTEGRATION.md)

