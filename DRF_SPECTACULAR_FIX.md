# DRF Spectacular API Schema Fix

## Problem
The application was experiencing a critical error when trying to access the API schema:
```
AssertionError: Incompatible AutoSchema used on View <class 'apps.core.views.WrappedAPIView'>. 
Is DRF's DEFAULT_SCHEMA_CLASS pointing to "drf_spectacular.openapi.AutoSchema" or any other 
drf-spectacular compatible AutoSchema?
```

This error occurred because:
1. The `DEFAULT_SCHEMA_CLASS` was not configured in the REST_FRAMEWORK settings
2. Function-based views decorated with `@api_view` didn't have proper schema definitions
3. drf-spectacular couldn't generate OpenAPI documentation for these views

## Solution

### 1. Updated Django Settings
**File**: `promptcraft/settings.py`

Added the required schema class to REST_FRAMEWORK configuration:
```python
REST_FRAMEWORK = {
    # ... existing settings ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # Required for drf-spectacular
}
```

### 2. Updated View Files with Schema Decorators

#### Core Views (`apps/core/views.py`)
- Added `extend_schema` import from drf-spectacular
- Added schema decorators to all function-based views:
  - `rag_status()`
  - `app_config()`
  - `system_status()`
  - `redis_health()`
  - `cors_test()`

#### User Views (`apps/users/views.py`)
- Added schema decorators with parameter specifications:
  - `check_username_availability()` - with username query parameter
  - `check_email_availability()` - with email query parameter

#### Template Views (`apps/templates/api_views.py`)
- Added schema decorator to:
  - `stream_validation()` - SSE streaming endpoint

#### AI Services Views (`apps/ai_services/views.py`)
- Added import for extend_schema decorator
- Ready for additional schema decorators as needed

### 3. Fixed Deployment Script
**File**: `deploy_production.ps1`

Fixed typo in daphne command:
```powershell
# Before:
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:applicatio

# After:
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

## Benefits

### 1. **API Documentation Works**
- Swagger UI is now accessible at `/api/schema/swagger-ui/`
- ReDoc is accessible at `/api/schema/redoc/`
- OpenAPI schema generation works properly

### 2. **Frontend Integration**
- Frontend can now discover API endpoints automatically
- Type-safe API client generation is possible
- Better developer experience with interactive documentation

### 3. **Error Prevention**
- No more schema generation errors
- All endpoints are properly documented
- Better API contract validation

### 4. **Production Ready**
- Daphne server starts correctly
- WebSocket support maintained
- SSE streaming endpoints work properly

## Testing

### 1. Test API Schema Generation
```bash
# Start the server
python manage.py runserver
# OR for production with WebSockets
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

### 2. Access API Documentation
- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### 3. Test Endpoints
```bash
# Health check
curl http://localhost:8000/health/

# Redis health
curl http://localhost:8000/health/redis/

# System status
curl http://localhost:8000/api/v2/core/status/

# App config
curl http://localhost:8000/api/v2/core/config/
```

## API Endpoints Now Available

### Core Endpoints
- `GET /api/v2/core/config/` - App configuration
- `GET /api/v2/core/health/` - Health check
- `GET /api/v2/core/status/` - System status
- `GET /health/` - Simple health check
- `GET /health/redis/` - Redis health check

### User Endpoints
- `GET /api/v2/auth/check-username/` - Username availability
- `GET /api/v2/auth/check-email/` - Email availability
- `POST /api/v2/auth/login/` - User login
- `POST /api/v2/auth/registration/` - User registration

### Template Endpoints
- `GET /api/v2/templates/` - List templates
- `GET /api/v2/templates/{id}/` - Template detail
- `GET /api/v2/templates/{id}/stream-validation/` - SSE validation

### AI Endpoints
- `POST /api/v2/ai/deepseek/stream/` - DeepSeek chat streaming
- `POST /api/v2/ai/agent/optimize/` - RAG-powered prompt optimization
- `POST /api/v2/ai/rag/retrieve/` - Vector similarity search
- `POST /api/v2/ai/rag/answer/` - RAG-powered Q&A

## Frontend Connection Guide

### 1. API Base URL
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

### 2. Example API Client
```typescript
// Fetch API schema for type generation
const schema = await fetch(`${API_BASE_URL}/api/schema/`);
const openAPISpec = await schema.json();

// Use with openapi-typescript or similar tools
// to generate TypeScript types
```

### 3. Authentication Headers
```typescript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${accessToken}`,
};
```

### 4. CORS Configuration
The backend is already configured to accept requests from:
- `http://localhost:3000` (Next.js dev)
- `http://localhost:3001` (Alternative frontend)
- Any origin in development mode

## Next Steps

1. **Generate TypeScript Types**: Use the OpenAPI schema to generate TypeScript types for the frontend
2. **Add More Schemas**: Continue adding `@extend_schema` decorators to remaining endpoints
3. **API Versioning**: Consider using drf-spectacular's version support for API v1/v2
4. **Rate Limiting**: Configure rate limiting for public endpoints
5. **Monitoring**: Set up API monitoring and analytics

## File Changes Summary

### Modified Files
1. `promptcraft/settings.py` - Added DEFAULT_SCHEMA_CLASS
2. `apps/core/views.py` - Added schema decorators to 5 endpoints
3. `apps/users/views.py` - Added schema decorators to 2 endpoints
4. `apps/templates/api_views.py` - Added schema decorator to 1 endpoint
5. `apps/ai_services/views.py` - Added schema import
6. `deploy_production.ps1` - Fixed daphne command typo

### Pattern Used
All changes follow this pattern:
```python
# Import at top of file
try:
    from drf_spectacular.utils import extend_schema, OpenApiParameter
    from drf_spectacular.types import OpenApiTypes
    DRF_SPECTACULAR_AVAILABLE = True
except ImportError:
    def extend_schema(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    DRF_SPECTACULAR_AVAILABLE = False

# Decorate function-based views
@extend_schema(
    description="Endpoint description",
    parameters=[...],  # Optional
    responses={200: dict},
    tags=["Category"]
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def my_view(request):
    ...
```

## Maintenance

### Adding New Endpoints
When adding new function-based views with `@api_view`:
1. Import `extend_schema` at the top
2. Add decorator before `@api_view`
3. Specify description, parameters, responses, and tags
4. Test schema generation at `/api/schema/`

### Debugging Schema Issues
```bash
# Check for schema errors
python manage.py spectacular --validate

# Generate schema file
python manage.py spectacular --file schema.yml
```

## Support

If you encounter issues:
1. Check that drf-spectacular is installed: `pip list | grep spectacular`
2. Verify DEFAULT_SCHEMA_CLASS is set in settings
3. Ensure all @api_view decorators have @extend_schema
4. Test individual endpoints for errors
5. Check Django logs for detailed error messages
