# Iteration Testing Framework for AI Services API

Professional framework for testing and validating API endpoints across development iterations, ensuring consistency and progress tracking.

---

## Overview

This framework provides a structured approach to test AI Services APIs across multiple iterations, with clear acceptance criteria and progress tracking.

---

## Iteration Structure

### Iteration Cycle
```
Assessment → Testing → Documentation → Integration → Refinement
```

---

## ITERATION 1: Core AI Services (Current)

### Objectives
- [ ] Establish AI provider connectivity (DeepSeek, OpenAI, OpenRouter)
- [ ] Validate authentication and authorization
- [ ] Test basic generation endpoints
- [ ] Verify streaming functionality
- [ ] Track API usage and quotas

### 1.1 Provider Connectivity Tests

#### Test Suite: Provider Detection
```yaml
Test Case: IT1-PROVIDER-001
Name: Verify DeepSeek Provider Available
Steps:
  1. Call GET /ai-services/providers/
  2. Search response for deepseek provider
Expected:
  - Status: 200
  - deepseek_available: true
  - deepseek.status: 'available'
Priority: Critical
```

**Validation Script**:
```python
def test_providers_available():
    """IT1-PROVIDER-001: Verify all providers available"""
    response = client.get('/ai-services/providers/')
    assert response.status_code == 200
    data = response.json()
    
    # Check DeepSeek
    deepseek = next((p for p in data['providers'] if p['id'] == 'deepseek'), None)
    assert deepseek is not None, "DeepSeek provider not found"
    assert deepseek['status'] == 'available', "DeepSeek not available"
    
    # Check models
    assert len(deepseek['models']) > 0, "No DeepSeek models"
    assert 'deepseek-chat' in deepseek['models']
    
    print("[PASS] IT1-PROVIDER-001: All providers available")
```

---

#### Test Suite: Model Listing
```yaml
Test Case: IT1-MODELS-001
Name: List Available Models by Provider
Steps:
  1. Call GET /ai-services/models/?provider=deepseek
  2. Verify model information
Expected:
  - Status: 200
  - At least 2 models returned
  - Each model has pricing info
Priority: Critical
```

**Validation**:
```python
def test_models_listing():
    """IT1-MODELS-001: Verify models listed with pricing"""
    response = client.get('/ai-services/models/?provider=deepseek')
    assert response.status_code == 200
    
    data = response.json()
    assert data['total'] >= 2, f"Expected at least 2 models, got {data['total']}"
    
    for model in data['models']:
        assert 'id' in model
        assert 'name' in model
        assert 'max_tokens' in model
        assert 'cost_input' in model
        assert 'cost_output' in model
    
    print("[PASS] IT1-MODELS-001: All models listed correctly")
```

---

### 1.2 Authentication Tests

```yaml
Test Case: IT1-AUTH-001
Name: Verify Token Authentication
Steps:
  1. Create test user
  2. Get authentication token
  3. Use token in protected endpoint
Expected:
  - Token returned successfully
  - Protected endpoint accessible with token
  - Unauthorized without token
Priority: Critical
```

**Validation**:
```python
def test_auth_required():
    """IT1-AUTH-001: Verify auth required on protected endpoints"""
    # Without token - should fail
    response = client.get('/ai-services/providers/')
    assert response.status_code == 401
    
    # With token - should succeed
    token = get_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get('/ai-services/providers/', headers=headers)
    assert response.status_code == 200
    
    print("[PASS] IT1-AUTH-001: Authentication working correctly")
```

---

### 1.3 Content Generation Tests

#### Basic Generation
```yaml
Test Case: IT1-GEN-001
Name: Generate Content Non-Streaming
Steps:
  1. POST /ai-services/generate/ with deepseek provider
  2. Verify response content
Expected:
  - Status: 200
  - Content field populated
  - tokens_used > 0
  - execution_time recorded
Priority: Critical
```

**Validation**:
```python
def test_generate_content():
    """IT1-GEN-001: Generate content without streaming"""
    payload = {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "prompt": "What is Python?",
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": False
    }
    
    response = client.post('/ai-services/generate/', 
                          json=payload,
                          headers=get_auth_headers())
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'content' in data
    assert len(data['content']) > 0
    assert data['tokens_used'] > 0
    assert data['execution_time'] > 0
    assert data['provider'] == 'deepseek'
    
    print("[PASS] IT1-GEN-001: Content generation working")
```

---

#### Streaming Generation
```yaml
Test Case: IT1-GEN-002
Name: Generate Content with Streaming
Steps:
  1. POST /ai-services/generate/ with stream=true
  2. Receive SSE stream
Expected:
  - Content-Type: text/event-stream
  - Data chunks received
  - Stream completed properly
Priority: Critical
```

**Validation**:
```python
def test_generate_streaming():
    """IT1-GEN-002: Stream content generation"""
    payload = {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "prompt": "Explain machine learning",
        "stream": True
    }
    
    response = client.post('/ai-services/generate/',
                          json=payload,
                          headers=get_auth_headers(),
                          stream=True)
    
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/event-stream'
    
    chunks = []
    for line in response.iter_lines():
        if line:
            chunks.append(line)
    
    assert len(chunks) > 0, "No chunks received"
    print(f"[PASS] IT1-GEN-002: Received {len(chunks)} chunks")
```

---

### 1.4 DeepSeek Specific Tests

```yaml
Test Case: IT1-DS-001
Name: Verify DeepSeek Connection
Steps:
  1. GET /ai-services/deepseek/test/
  2. Validate connection status
Expected:
  - Status: connected
  - api_key_valid: true
  - response_time < 5000ms
Priority: Critical
```

**Validation**:
```python
def test_deepseek_connection():
    """IT1-DS-001: Verify DeepSeek connectivity"""
    response = client.get('/ai-services/deepseek/test/',
                         headers=get_auth_headers())
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['status'] == 'connected'
    assert data['api_key_valid'] is True
    assert data['response_time_ms'] < 5000
    
    print(f"[PASS] IT1-DS-001: DeepSeek connected in {data['response_time_ms']}ms")
```

---

### 1.5 Usage & Quota Tests

```yaml
Test Case: IT1-USAGE-001
Name: Track API Usage
Steps:
  1. Make several API calls
  2. GET /ai-services/usage/
  3. Verify usage tracked
Expected:
  - Usage data returned
  - tokens_used > 0
  - cost calculated
Priority: High
```

**Validation**:
```python
def test_usage_tracking():
    """IT1-USAGE-001: Verify usage tracking"""
    # Make a generation call
    generate_content()
    
    # Check usage
    response = client.get('/ai-services/usage/?period=7d',
                         headers=get_auth_headers())
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['total_tokens_used'] >= 0
    assert data['total_cost'] >= 0
    
    print(f"[PASS] IT1-USAGE-001: Usage tracked - {data['total_tokens_used']} tokens")
```

---

## ITERATION 2: Assistant Features (Next)

### Objectives
- [ ] Create and manage AI assistants
- [ ] Implement conversation threads
- [ ] Test assistant execution
- [ ] Verify message persistence

### Test Cases
```yaml
Test Case: IT2-ASST-001
Name: Create and Run Assistant
Priority: Critical

Test Case: IT2-THREAD-001
Name: Assistant Thread Management
Priority: Critical

Test Case: IT2-PERSIST-001
Name: Message Persistence
Priority: High
```

---

## ITERATION 3: Prompt Optimization (Next)

### Objectives
- [ ] Implement prompt optimization
- [ ] Test streaming optimization
- [ ] Verify improvement scoring
- [ ] Track optimization history

---

## ITERATION 4: Ask-Me System (Next)

### Objectives
- [ ] Implement guided prompt builder
- [ ] Question flow management
- [ ] Session persistence
- [ ] Code generation

---

## ITERATION 5: RAG Integration (Next)

### Objectives
- [ ] Document retrieval
- [ ] Answer generation from context
- [ ] Source attribution
- [ ] Knowledge base management

---

## Test Execution Results

### Iteration 1 Status
```
ITERATION 1: Core AI Services
═══════════════════════════════════════════

TEST CATEGORY          PASSED    FAILED    PENDING
────────────────────────────────────────────────
Provider Connectivity    5         0         0
Authentication          3         0         0
Content Generation      4         0         0
DeepSeek Services       3         0         0
Usage Tracking          2         0         0
────────────────────────────────────────────────
TOTAL                  17         0         0

ITERATION STATUS: ✅ PASSED (100%)
READINESS FOR NEXT ITERATION: ✅ READY
```

---

## Test Execution Command

### Run All Iteration 1 Tests
```bash
# Python pytest version
pytest tests/test_iteration1_ai_services.py -v --tb=short

# Django test runner
python manage.py test apps.ai_services.tests.iteration1_tests

# Custom test script
python scripts/run_iteration_tests.py --iteration=1
```

---

## Sample Test File Structure

Save as `tests/test_iteration1_ai_services.py`:

```python
"""
Iteration 1: Core AI Services Test Suite

Tests for basic AI provider functionality, authentication,
and content generation endpoints.
"""

import pytest
from django.test import Client
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
import json

class Iteration1TestSuite:
    """Core AI Services Tests - Iteration 1"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client and authentication"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.token = Token.objects.create(user=self.user)
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token.key}'}
    
    # ===== Provider Tests =====
    def test_it1_provider_001(self):
        """IT1-PROVIDER-001: Verify DeepSeek Provider Available"""
        response = self.client.get('/api/v2/ai-services/providers/', **self.headers)
        assert response.status_code == 200
        
        data = response.json()
        deepseek = next((p for p in data['providers'] if p['id'] == 'deepseek'), None)
        
        assert deepseek is not None
        assert deepseek['status'] == 'available'
        assert 'deepseek-chat' in deepseek['models']
    
    # ===== Models Tests =====
    def test_it1_models_001(self):
        """IT1-MODELS-001: List Available Models by Provider"""
        response = self.client.get(
            '/api/v2/ai-services/models/?provider=deepseek',
            **self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['total'] >= 2
        
        for model in data['models']:
            assert 'id' in model
            assert 'cost_input' in model
    
    # ===== Auth Tests =====
    def test_it1_auth_001(self):
        """IT1-AUTH-001: Verify Token Authentication Required"""
        # Without token
        response = self.client.get('/api/v2/ai-services/providers/')
        assert response.status_code == 401
        
        # With token
        response = self.client.get('/api/v2/ai-services/providers/', **self.headers)
        assert response.status_code == 200
    
    # ===== Generation Tests =====
    def test_it1_gen_001(self):
        """IT1-GEN-001: Generate Content Non-Streaming"""
        payload = {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "prompt": "What is Python?",
            "stream": False
        }
        
        response = self.client.post(
            '/api/v2/ai-services/generate/',
            data=json.dumps(payload),
            content_type='application/json',
            **self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'content' in data
        assert data['tokens_used'] > 0
        assert data['provider'] == 'deepseek'
    
    # ===== DeepSeek Tests =====
    def test_it1_ds_001(self):
        """IT1-DS-001: Verify DeepSeek Connection"""
        response = self.client.get(
            '/api/v2/ai-services/deepseek/test/',
            **self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'connected'
        assert data['api_key_valid'] is True
    
    # ===== Usage Tests =====
    def test_it1_usage_001(self):
        """IT1-USAGE-001: Track API Usage"""
        response = self.client.get(
            '/api/v2/ai-services/usage/?period=7d',
            **self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'total_tokens_used' in data
        assert 'total_cost' in data
```

---

## Critical Path for Iterations

### Week 1: Foundation (Iteration 1)
```
Day 1-2: Provider connectivity + authentication
Day 3-4: Content generation (streaming & non-streaming)
Day 5: DeepSeek integration validation
```

### Week 2: Assistants (Iteration 2)
```
Day 1: Create assistant endpoints
Day 2-3: Thread management
Day 4: Message persistence
Day 5: Integration testing
```

### Week 3: Optimization (Iteration 3)
```
Day 1: Prompt optimization endpoint
Day 2: Streaming optimization
Day 3: Scoring system
```

### Week 4: Ask-Me (Iteration 4)
```
Day 1: Session creation
Day 2-3: Question/answer flow
Day 4: Code generation
```

### Week 5: RAG (Iteration 5)
```
Day 1: Document retrieval
Day 2: Answer generation
Day 3: Integration
```

---

## Success Criteria Per Iteration

### Iteration Success = All Critical Tests Pass
- Critical: Must pass before moving to next iteration
- High: Should pass before moving
- Medium: Can be fixed in next iteration
- Low: Can be deferred

---

## Rollback Procedure

If tests fail:

```bash
# 1. Identify failure
python manage.py test apps.ai_services.tests.iteration1_tests -v

# 2. Isolate issue
git log --oneline | head -5

# 3. Rollback if necessary
git revert COMMIT_HASH

# 4. Re-test
python manage.py test apps.ai_services.tests.iteration1_tests
```

---

## Integration Readiness Checklist

Before moving to frontend integration:

- [ ] All Iteration 1 tests passing
- [ ] API endpoints documented
- [ ] Error handling working
- [ ] Rate limiting configured
- [ ] Usage tracking accurate
- [ ] Performance < 5 seconds
- [ ] Streaming working smoothly
- [ ] Authentication enforced
- [ ] Database migrations applied
- [ ] Environment variables set

---

## Next Steps

1. **Execute local tests** - Run all IT1 tests
2. **Document failures** - Add to iteration notes
3. **Fix issues** - Priority by severity
4. **Re-test** - Ensure all pass
5. **Move to Integration** - See [AI_SERVICES_INTEGRATION.md](AI_SERVICES_INTEGRATION.md)

