# 🚀 Quick Start - DRF Spectacular API

## Start Server
```bash
.\deploy_production.ps1
```

## Test API
```bash
python test_api_schema.py
```

## Access Documentation
- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/

## Frontend Setup
```bash
# Generate types
npx openapi-typescript http://localhost:8000/api/schema/ -o src/types/api.ts
```

## Key Endpoints
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/health/` | GET | No | Health check |
| `/api/schema/` | GET | No | OpenAPI schema |
| `/api/v2/auth/login/` | POST | No | Login |
| `/api/v2/templates/` | GET | No* | Templates |
| `/api/v2/ai/agent/optimize/` | POST | Yes | AI optimization |

*Public read, authenticated write

## Quick Examples

### Login
```typescript
const response = await fetch('http://localhost:8000/api/v2/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', password: 'pass123' })
});
const { access, refresh } = await response.json();
```

### Fetch Templates
```typescript
const response = await fetch('http://localhost:8000/api/v2/templates/');
const { results } = await response.json();
```

### AI Optimization (with auth)
```typescript
const response = await fetch('http://localhost:8000/api/v2/ai/agent/optimize/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({ prompt: 'Write a blog post' })
});
```

## Files Created
- ✅ `DRF_SPECTACULAR_FIX.md` - Technical details
- ✅ `FRONTEND_INTEGRATION_COMPLETE.md` - Frontend guide
- ✅ `SPECTACULAR_INTEGRATION_COMPLETE.md` - Summary
- ✅ `test_api_schema.py` - Test script
- ✅ Fixed `deploy_production.ps1` - Deployment

## Status
✅ **COMPLETE & READY FOR FRONTEND**
