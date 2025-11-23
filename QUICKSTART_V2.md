# Quick Start: Prompt History API v2

## 🚀 Immediate Actions

### 1. Verify Installation
```bash
cd "c:\Users\ahmed el bahi\MyPromptApp\my_prmpt_bakend"
.\venv\Scripts\Activate.ps1
python manage.py showmigrations prompt_history
```

### 2. Run Server
```bash
python manage.py runserver
```

### 3. Test Endpoints

#### Get JWT Token
```bash
curl -X POST http://localhost:8000/api/v2/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

#### Create History Entry
```bash
curl -X POST http://localhost:8000/api/v2/history/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "original_prompt": "Write a blog post about AI",
    "source": "raw",
    "intent_category": "content_creation",
    "tags": ["blog", "ai"]
  }'
```

#### List History
```bash
curl -X GET "http://localhost:8000/api/v2/history/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Enhance Prompt
```bash
curl -X POST "http://localhost:8000/api/v2/history/{id}/enhance/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","style":"concise"}'
```

---

## 📂 Key Files

- **Model**: `apps/prompt_history/models.py`
- **Views**: `apps/prompt_history/views.py`
- **Serializers**: `apps/prompt_history/serializers.py`
- **Optimization**: `apps/prompt_history/services/optimization.py`
- **URLs**: `promptcraft/urls.py` (line with `/api/v2/history/`)
- **API Docs**: `docs/API_HISTORY_V2.md`
- **Deploy Guide**: `docs/DEPLOY_HEROKU.md`

---

## 🔧 Commands

```bash
# Migrations
python manage.py makemigrations prompt_history
python manage.py migrate

# Seed data
python manage.py seed_prompts_small

# Create user
python manage.py createsuperuser

# Run tests
pytest apps/prompt_history/tests.py -v

# Start server
python manage.py runserver

# Shell
python manage.py shell
```

---

## 🌐 Endpoints

### History CRUD
```
POST   /api/v2/history/                # Create
GET    /api/v2/history/                # List (paginated)
GET    /api/v2/history/{id}/           # Retrieve
PATCH  /api/v2/history/{id}/           # Update
DELETE /api/v2/history/{id}/           # Soft delete
POST   /api/v2/history/{id}/enhance/   # AI optimize
```

### Health
```
GET    /health/                        # Basic
GET    /health/redis/                  # Redis check
```

---

## 🚢 Deploy to Heroku

```bash
# Login & create app
heroku login
heroku create prompt-temple-backend

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Set env vars
heroku config:set DJANGO_SETTINGS_MODULE=promptcraft.settings.production
heroku config:set SECRET_KEY="GENERATE_RANDOM_KEY"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="prompt-temple-backend.herokuapp.com,www.prompt-temple.com"
heroku config:set CORS_ALLOWED_ORIGINS="https://www.prompt-temple.com"

# Deploy
git add .
git commit -m "Add prompt history API v2"
git push heroku main

# Migrate & seed
heroku run python manage.py migrate
heroku run python manage.py seed_prompts_small

# Check health
curl https://prompt-temple-backend.herokuapp.com/health/
curl https://prompt-temple-backend.herokuapp.com/health/redis/
```

---

## 📊 Features Implemented

✅ JWT-authenticated CRUD endpoints  
✅ Soft delete (audit trail preserved)  
✅ Filtering by intent_category, source  
✅ Search in original_prompt  
✅ Pagination (20 items/page)  
✅ AI enhancement with LangChain  
✅ LangSmith tracing (optional)  
✅ Redis health check  
✅ Owner-only permissions  
✅ Credits debit on enhance  
✅ Token/latency tracking  
✅ CORS for production  
✅ Heroku-ready (500MB limit)  

---

## 🔐 Auth Flow

```
1. POST /api/v2/auth/login/ → Get JWT token
2. Include in header: Authorization: Bearer <token>
3. Access /api/v2/history/* endpoints
```

---

## 🎯 Response Format

```json
{
  "id": "uuid",
  "user": 1,
  "source": "library",
  "original_prompt": "...",
  "optimized_prompt": "...",
  "model_used": "gpt-4o-mini",
  "tokens_input": 512,
  "tokens_output": 246,
  "credits_spent": 3,
  "intent_category": "email",
  "tags": ["sales", "outreach"],
  "meta": {"session_id": "abc123", "latency_ms": 820},
  "is_deleted": false,
  "created_at": "2025-11-23T10:30:00Z",
  "updated_at": "2025-11-23T10:30:00Z"
}
```

---

## 📖 Full Documentation

- **API Spec**: `docs/API_HISTORY_V2.md`
- **Deployment**: `docs/DEPLOY_HEROKU.md`
- **Implementation**: `IMPLEMENTATION_COMPLETE_V2.md`

---

**Status**: ✅ Ready for testing & deployment
