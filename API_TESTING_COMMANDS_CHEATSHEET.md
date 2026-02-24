# API Testing Quick Reference & Commands Cheat Sheet

Fast reference guide for testing all AI Services endpoints locally.

---

## Environment Setup

```bash
# Set base URL
export BASE_URL="http://localhost:8000/api/v2"

# Create test user
python create_test_users.py

# Get token (save this!)
export TOKEN=$(curl -s -X POST $BASE_URL/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}' \
  | jq -r '.token')

echo "Token: $TOKEN"

# Verify token
curl -H "Authorization: Bearer $TOKEN" $BASE_URL/ai-services/providers/ | jq .
```

---

## AI PROVIDERS SECTION

### Get All Providers
```bash
curl -X GET $BASE_URL/ai-services/providers/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

**Expected**: 
```json
{
  "providers": [{
    "id": "deepseek",
    "status": "available",
    "cost_per_1k_tokens": 0.0014
  }],
  "deepseek_available": true
}
```

---

### Get Models by Provider
```bash
# All models
curl -X GET $BASE_URL/ai-services/models/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Filter by provider
curl -X GET "$BASE_URL/ai-services/models/?provider=deepseek" \
  -H "Authorization: Bearer $TOKEN" | jq '.models[0]'
```

---

## DEEPSEEK SPECIFIC TESTS

### Test DeepSeek Connection
```bash
curl -X GET $BASE_URL/ai-services/deepseek/test/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

**Expected**: Status "connected", api_key_valid: true

---

## CONTENT GENERATION SECTION

### Generate Content (Non-Streaming)
```bash
curl -X POST $BASE_URL/ai-services/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "prompt": "Write a Python function for factorial",
    "temperature": 0.7,
    "max_tokens": 300,
    "stream": false
  }' | jq '.content'
```

---

### Generate Content (Streaming)
```bash
curl -X POST $BASE_URL/ai-services/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "prompt": "Explain machine learning",
    "stream": true
  }' --no-buffer
```

**Note**: Use `--no-buffer` to see real-time chunks

---

### DeepSeek Chat Endpoint
```bash
curl -X POST $BASE_URL/ai-services/deepseek/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are helpful"},
      {"role": "user", "content": "What is Python?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }' | jq '.response'
```

---

### DeepSeek Streaming Endpoint
```bash
curl -X POST $BASE_URL/ai-services/deepseek/stream/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing",
    "max_tokens": 500,
    "temperature": 0.7
  }' --no-buffer
```

---

## AI ASSISTANTS SECTION

### Get Available Assistants
```bash
curl -X GET $BASE_URL/ai-services/assistant/ \
  -H "Authorization: Bearer $TOKEN" | jq '.assistants'
```

---

### Run an Assistant
```bash
# First, save an assistant ID from the list above as $ASSISTANT_ID

curl -X POST $BASE_URL/ai-services/assistant/run/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "'$ASSISTANT_ID'",
    "message": "Help me debug this Python code",
    "stream": false
  }' | jq '.response'
```

---

### List Conversation Threads
```bash
curl -X GET $BASE_URL/ai-services/assistant/threads/ \
  -H "Authorization: Bearer $TOKEN" | jq '.threads'
```

---

### Get Thread Details
```bash
# Save a thread_id from the list above as $THREAD_ID

curl -X GET $BASE_URL/ai-services/assistant/threads/$THREAD_ID/ \
  -H "Authorization: Bearer $TOKEN" | jq '.thread.messages'
```

---

## PROMPT OPTIMIZATION SECTION

### Optimize Prompt
```bash
curl -X POST $BASE_URL/ai-services/optimization/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "write code to sort",
    "context": "Python",
    "optimization_type": "clarity",
    "stream": false
  }' | jq '{optimized: .optimized_prompt, score: .optimization_score}'
```

---

### Stream Optimization
```bash
curl -X POST $BASE_URL/ai-services/optimization/stream/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "make a web app",
    "context": "React"
  }' --no-buffer
```

---

## RAG ENDPOINTS SECTION

### Retrieve Documents from Knowledge Base
```bash
curl -X POST $BASE_URL/ai-services/rag/retrieve/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to authenticate in Django REST Framework?",
    "top_k": 5,
    "similarity_threshold": 0.7
  }' | jq '.results'
```

---

### Generate Answer from Retrieved Documents
```bash
curl -X POST $BASE_URL/ai-services/rag/answer/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How to set up JWT authentication?",
    "documents": [],
    "model": "deepseek-chat",
    "include_sources": true
  }' | jq '.answer'
```

---

## ASK-ME GUIDED BUILDER SECTION

### Start Ask-Me Session
```bash
# Save the session_id from response
curl -X POST $BASE_URL/ai-services/askme/start/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Create a Python web scraper for e-commerce",
    "context": "Python, beginner to intermediate"
  }' | jq '{session_id: .session_id, questions: .questions}'

# Save session_id
export SESSION_ID="copied-from-response"
```

---

### Answer First Question
```bash
# Get the first question's qid from the previous response
curl -X POST $BASE_URL/ai-services/askme/answer/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "qid": "q1",
    "value": "amazon.com"
  }' | jq '{completion: .completion_percentage, good_enough: .good_enough_to_run}'
```

---

### Answer Second Question (Multiple Choice)
```bash
curl -X POST $BASE_URL/ai-services/askme/answer/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "qid": "q2",
    "value": ["Product Name", "Price", "Description"]
  }' | jq '.completion_percentage'
```

---

### Finalize Session & Generate Code
```bash
curl -X POST $BASE_URL/ai-services/askme/finalize/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "generate_code": true,
    "code_language": "python"
  }' | jq '{is_complete: .is_complete, final_prompt: .final_prompt}'
```

---

### View Generated Code
```bash
curl -X POST $BASE_URL/ai-services/askme/finalize/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "generate_code": true,
    "code_language": "python"
  }' | jq '.generated_code'
```

---

### Get All Ask-Me Sessions
```bash
curl -X GET $BASE_URL/ai-services/askme/sessions/ \
  -H "Authorization: Bearer $TOKEN" | jq '.sessions'
```

---

### Get Specific Session
```bash
curl -X GET $BASE_URL/ai-services/askme/sessions/$SESSION_ID/ \
  -H "Authorization: Bearer $TOKEN" | jq '.session'
```

---

### Delete Session
```bash
curl -X DELETE $BASE_URL/ai-services/askme/sessions/$SESSION_ID/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## USAGE & QUOTAS SECTION

### Check Your Usage (Last 7 Days)
```bash
curl -X GET "$BASE_URL/ai-services/usage/?period=7d" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

**Shows**: tokens_used, cost, by_provider breakdown

---

### Check Usage (Custom Period)
```bash
# Options: 24h, 7d, 30d, all
curl -X GET "$BASE_URL/ai-services/usage/?period=30d" \
  -H "Authorization: Bearer $TOKEN" | jq '.by_provider'
```

---

### Check Quotas & Remaining Budget
```bash
curl -X GET $BASE_URL/ai-services/quotas/ \
  -H "Authorization: Bearer $TOKEN" | jq '{
    monthly_quota: .monthly_quota,
    remaining: .remaining,
    usage_percentage: .usage_percentage
  }'
```

---

## ERROR TESTING SECTION

### Test Missing Token (Should fail)
```bash
curl -X GET $BASE_URL/ai-services/providers/
# Expected: 401 Unauthorized
```

---

### Test Invalid Provider
```bash
curl -X POST $BASE_URL/ai-services/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "invalid_provider",
    "prompt": "test"
  }' | jq '.error'
# Expected: "Invalid provider"
```

---

### Test Rate Limiting (Make many requests)
```bash
for i in {1..101}; do
  curl -X GET $BASE_URL/ai-services/providers/ \
    -H "Authorization: Bearer $TOKEN"
done
# Expected: 429 Too Many Requests after limit
```

---

## BATCH TESTING SCRIPT

Save as `test_batch.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api/v2"
TOKEN=$1

if [ -z "$TOKEN" ]; then
  echo "Usage: ./test_batch.sh TOKEN"
  exit 1
fi

echo "=== Testing Providers ==="
curl -s $BASE_URL/ai-services/providers/ \
  -H "Authorization: Bearer $TOKEN" | jq '.total_providers'

echo "=== Testing DeepSeek Connection ==="
curl -s $BASE_URL/ai-services/deepseek/test/ \
  -H "Authorization: Bearer $TOKEN" | jq '.status'

echo "=== Testing Generation ==="
curl -s -X POST $BASE_URL/ai-services/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "prompt": "Hello",
    "stream": false
  }' | jq '.tokens_used'

echo "=== Testing Usage ==="
curl -s $BASE_URL/ai-services/usage/ \
  -H "Authorization: Bearer $TOKEN" | jq '.total_tokens_used'

echo "=== Tests Complete ==="
```

**Run**:
```bash
chmod +x test_batch.sh
./test_batch.sh $TOKEN
```

---

## PYTHON TESTING

### Simple Test Script

Save as `test_api_simple.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v2"
TOKEN = input("Enter token: ")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Test 1: Providers
print("1. Testing Providers...")
resp = requests.get(f"{BASE_URL}/ai-services/providers/", headers=HEADERS)
print(f"   Status: {resp.status_code}")
data = resp.json()
print(f"   Providers: {len(data['providers'])}")

# Test 2: DeepSeek Test
print("\n2. Testing DeepSeek Connection...")
resp = requests.get(f"{BASE_URL}/ai-services/deepseek/test/", headers=HEADERS)
print(f"   Status: {resp.status_code}")
data = resp.json()
print(f"   Connection: {data['status']}")
print(f"   API Key Valid: {data['api_key_valid']}")

# Test 3: Generate Content
print("\n3. Testing Content Generation...")
payload = {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "prompt": "What is Python?",
    "stream": False
}
resp = requests.post(f"{BASE_URL}/ai-services/generate/", 
                     json=payload, headers=HEADERS)
print(f"   Status: {resp.status_code}")
data = resp.json()
print(f"   Content Length: {len(data['content'])}")
print(f"   Tokens: {data['tokens_used']}")

# Test 4: Usage
print("\n4. Testing Usage Tracking...")
resp = requests.get(f"{BASE_URL}/ai-services/usage/", headers=HEADERS)
print(f"   Status: {resp.status_code}")
data = resp.json()
print(f"   Total Tokens: {data['total_tokens_used']}")
print(f"   Total Cost: ${data['total_cost']:.2f}")

print("\n✅ All basic tests passed!")
```

**Run**:
```bash
python test_api_simple.py
```

---

## PERFORMANCE TESTING

### Measure Response Time
```bash
time curl -s -X GET $BASE_URL/ai-services/providers/ \
  -H "Authorization: Bearer $TOKEN" > /dev/null

# Should be < 500ms
```

---

### Stream Performance
```bash
time curl -s -X POST $BASE_URL/ai-services/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "prompt": "Explain how AI works",
    "stream": true
  }' > /dev/null

# Should be < 5s for 500+ tokens
```

---

## Quick Diagnostics

### Check Server Health
```bash
curl http://localhost:8000/health/ | jq '.'
```

---

### Check Django Status
```bash
python manage.py check
```

---

### Check Database
```bash
python manage.py dbshell
# SELECT COUNT(*) FROM ai_services_aiinteraction;
```

---

### Check Logs
```bash
tail -f logs/django.log
# or
python manage.py runserver --verbosity 3
```

---

## Save Results to File

```bash
# Save all providers
curl -s $BASE_URL/ai-services/providers/ \
  -H "Authorization: Bearer $TOKEN" | jq . > providers.json

# Save generation output
curl -s -X POST $BASE_URL/ai-services/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}' | jq '.content' > generated.txt

# Save streaming output
curl -s -X POST $BASE_URL/ai-services/deepseek/stream/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}' > stream_output.txt
```

---

## Common Patterns

### Full Ask-Me Session Flow
```bash
# 1. Start
RESULT=$(curl -s -X POST $BASE_URL/ai-services/askme/start/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"intent": "Build a web app"}')
SESSION_ID=$(echo $RESULT | jq -r '.session_id')

# 2. Answer Q1
curl -s -X POST $BASE_URL/ai-services/askme/answer/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "'$SESSION_ID'", "qid": "q1", "value": "React"}'

# 3. Answer Q2
curl -s -X POST $BASE_URL/ai-services/askme/answer/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "'$SESSION_ID'", "qid": "q2", "value": ["Auth", "API"]}'

# 4. Finalize
curl -s -X POST $BASE_URL/ai-services/askme/finalize/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "'$SESSION_ID'", "generate_code": true, "code_language": "javascript"}' \
  | jq '.generated_code'
```

---

**Last Updated**: February 24, 2026
**For Full Details**: See [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)

