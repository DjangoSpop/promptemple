# 🚀 GraphQL Quick Start Guide

## Setup (Local Development)

### 1. Activate Virtual Environment & Install

```powershell
# Run the complete setup script
.\setup_graphql_complete.ps1
```

This script will:
- ✅ Activate your virtual environment
- ✅ Install GraphQL dependencies (graphene-django, graphene)
- ✅ Create database migrations
- ✅ Apply migrations
- ✅ Create test data
- ✅ Verify installation

### 2. Start Development Server

```powershell
python manage.py runserver
```

### 3. Access GraphiQL Interface

Open your browser to: **http://localhost:8000/api/graphql/**

## Quick Test

### Get JWT Token

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/v2/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@promptcraft.com","password":"testpass123"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Test GraphQL Query (in GraphiQL)

Add token to HTTP Headers in GraphiQL:
```json
{
  "Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE"
}
```

Run this query:
```graphql
query {
  allPromptHistories(limit: 5) {
    id
    originalPrompt
    createdAt
    iterations {
      id
      iterationNumber
      promptText
    }
  }
}
```

## Deploy to Heroku

### Option 1: Automated Deployment

```powershell
.\deploy_graphql.ps1
```

### Option 2: Manual Deployment

```powershell
# 1. Activate venv
.\venv\Scripts\Activate.ps1

# 2. Commit changes
git add .
git commit -m "feat: Add GraphQL prompt iteration tracking"

# 3. Push to Heroku
git push heroku main

# 4. Run migrations on Heroku
heroku run python manage.py migrate prompt_history

# 5. Open app
heroku open
```

## Test on Heroku

```bash
# Get your Heroku app URL
heroku info

# Test GraphQL endpoint
curl -X POST https://your-app.herokuapp.com/api/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query":"{ __schema { types { name } } }"}'
```

## Common GraphQL Queries

### 1. Get All Iterations for a Prompt
```graphql
query {
  allIterationsForPrompt(parentPromptId: "UUID_HERE") {
    id
    iterationNumber
    promptText
    aiResponse
    tokensInput
    tokensOutput
    creditsSpent
    isActive
  }
}
```

### 2. Create New Iteration
```graphql
mutation {
  createPromptIteration(input: {
    parentPromptId: "UUID_HERE"
    promptText: "Your prompt here"
    aiResponse: "AI response here"
    interactionType: "manual"
    tokensInput: 10
    tokensOutput: 100
    creditsSpent: 2
  }) {
    success
    message
    iteration {
      id
      iterationNumber
    }
  }
}
```

### 3. Search Iterations
```graphql
query {
  searchIterations(query: "machine learning", limit: 10) {
    id
    promptText
    aiResponse
    tags
  }
}
```

### 4. Get Conversation Thread
```graphql
query {
  allConversationThreads(status: "active", limit: 10) {
    id
    title
    totalIterations
    totalTokens
    messages {
      messageOrder
      iteration {
        promptText
        aiResponse
      }
    }
  }
}
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'graphene_django'"

**Solution:**
```powershell
# Activate venv first!
.\venv\Scripts\Activate.ps1

# Then install
pip install graphene-django==3.2.0 graphene==3.3
```

### Issue: Migration errors

**Solution:**
```powershell
# Delete migration files (except __init__.py)
# Then recreate:
python manage.py makemigrations prompt_history
python manage.py migrate prompt_history
```

### Issue: "Authentication required" error

**Solution:**
Make sure you're sending the JWT token:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Issue: CSRF errors

**Solution:**
GraphQL endpoint is CSRF exempt by default. If you still see errors, check that you're using POST requests.

## Documentation

- **Full Documentation**: [GRAPHQL_PROMPT_HISTORY.md](./GRAPHQL_PROMPT_HISTORY.md)
- **Frontend Integration**: [graphql_frontend_integration.tsx](./graphql_frontend_integration.tsx)
- **Models**: `apps/prompt_history/models.py`
- **Schema**: `apps/prompt_history/schema.py`

## Features Implemented

✅ **Prompt Iteration Tracking**
- Version control for prompts
- Chain tracking with previous iterations
- Change summaries and diff sizes

✅ **Conversation Threading**
- Group related prompts into conversations
- Track aggregate metrics (tokens, credits)
- Multi-turn AI conversation support

✅ **Human-AI Interactions**
- Complete interaction history
- User ratings and feedback
- Bookmarking system

✅ **Performance Metrics**
- Token tracking (input/output)
- Response time monitoring
- Credit consumption tracking

✅ **Quality Management**
- 5-star rating system
- Detailed feedback notes
- Active/inactive version management

✅ **Flexible Metadata**
- JSON fields for custom data
- Tagging system
- Extensible parameters

## Production Checklist

Before deploying to production:

- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Migrations created and applied
- [ ] GraphQL endpoint tested locally
- [ ] JWT authentication working
- [ ] Environment variables set on Heroku
- [ ] Database backed up (if applicable)
- [ ] Heroku app scaling configured
- [ ] Monitoring/logging configured

## Support

For issues or questions:
1. Check [GRAPHQL_PROMPT_HISTORY.md](./GRAPHQL_PROMPT_HISTORY.md) for detailed documentation
2. Review model definitions in `apps/prompt_history/models.py`
3. Test queries in GraphiQL interface
4. Check Heroku logs: `heroku logs --tail`

---

**🎉 Happy Coding!**
