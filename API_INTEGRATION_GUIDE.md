# PromptCraft API Integration Guide

## Overview

This guide provides comprehensive instructions for integrating the PromptCraft API with frontend applications. The API is built with Django REST Framework and supports both development and production environments.

## Table of Contents

1. [Base Configuration](#base-configuration)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [CORS Configuration](#cors-configuration)
5. [API Endpoints](#api-endpoints)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Base Configuration

### Development Environment

**Backend URL:** `http://127.0.0.1:8000`
**Frontend URL:** `http://localhost:3001`

### Production Environment

**Backend URL:** `https://api.prompt-temple.com` (or your production domain)
**Frontend URL:** `https://www.prompt-temple.com`

### API Versions

The API supports two versions:
- **v1** (Legacy): `/api/v1/*` - Maintained for backward compatibility
- **v2** (Current): `/api/v2/*` - Recommended for all new development

### Base URL Configuration

Configure your API client with the appropriate base URL:

```typescript
// Development
const BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

// Production
const BASE_URL = process.env.REACT_APP_API_URL || 'https://www.prompt-temple.com';
```

**Environment Variables (.env):**
```env
# Development
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_API_VERSION=v2

# Production
REACT_APP_API_URL=https://api.prompt-temple.com
REACT_APP_API_VERSION=v2
```

---

## Authentication

### JWT Authentication

All API endpoints require JWT (JSON Web Token) authentication, except for:
- `GET /health/` - Health check
- `POST /api/v2/auth/register/` - User registration
- `POST /api/v2/auth/login/` - User login
- `POST /api/v2/auth/refresh/` - Token refresh

### Token Flow

1. **Login**: POST `/api/v2/auth/login/`
   ```json
   {
     "email": "user@example.com",
     "password": "password123"
   }
   ```
   Response:
   ```json
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
   }
   ```

2. **Store Tokens**: Save access token in memory/state and refresh token in httpOnly cookie

3. **Send Requests**: Include access token in Authorization header:
   ```
   Authorization: Bearer <access_token>
   ```

4. **Token Refresh**: When access token expires:
   ```json
   POST /api/v2/auth/refresh/
   {
     "refresh": "<refresh_token>"
   }
   ```

### TypeScript API Client Example

```typescript
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

export class APIClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to attach token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      }
    );

    // Add response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const response = await this.refreshAccessToken();
            this.accessToken = response.data.access;
            
            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${this.accessToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, redirect to login
            this.logout();
            throw refreshError;
          }
        }

        throw error;
      }
    );
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/api/v2/auth/login/', {
      email,
      password,
    });

    this.accessToken = response.data.access;
    this.refreshToken = response.data.refresh;

    // Save refresh token in httpOnly cookie (server-side)
    return response.data;
  }

  private async refreshAccessToken() {
    return this.client.post('/api/v2/auth/refresh/', {
      refresh: this.refreshToken,
    });
  }

  async logout() {
    this.accessToken = null;
    this.refreshToken = null;
    // Redirect to login page
  }

  async get(path: string, config = {}) {
    return this.client.get(path, config);
  }

  async post(path: string, data: any, config = {}) {
    return this.client.post(path, data, config);
  }

  async put(path: string, data: any, config = {}) {
    return this.client.put(path, data, config);
  }

  async patch(path: string, data: any, config = {}) {
    return this.client.patch(path, data, config);
  }

  async delete(path: string, config = {}) {
    return this.client.delete(path, config);
  }
}

// Initialize globally
export const apiClient = new APIClient(
  process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000'
);
```

---

## Error Handling

### HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful request with no content |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Invalid/missing authentication |
| 403 | Forbidden | Valid auth but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Backend error |

### Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "code": "ERROR_CODE"
}
```

### Retry Strategy

Implement exponential backoff for transient errors:

```typescript
async function retryRequest(
  fn: () => Promise<any>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<any> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      // Don't retry client errors (4xx) except 429
      if (error.response?.status >= 400 && error.response?.status < 500) {
        if (error.response?.status !== 429) {
          throw error;
        }
      }

      // On last attempt, throw error
      if (attempt === maxRetries - 1) {
        throw error;
      }

      // Exponential backoff: 1s, 2s, 4s
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

// Usage
try {
  const data = await retryRequest(() => 
    apiClient.get('/api/v2/templates/')
  );
} catch (error) {
  console.error('Failed after retries:', error);
}
```

---

## CORS Configuration

### Development

In development mode, the backend allows:
- **All Origins** when `DEBUG=True`
- **Specific Origins**: 
  - `http://localhost:3000`
  - `http://localhost:3001`
  - `http://127.0.0.1:3000`
  - `http://127.0.0.1:3001`

### Production

When `DEBUG=False`, only specific domains are allowed:
- `https://www.prompt-temple.com`
- `https://prompt-temple.com`

### Frontend Configuration

Ensure your API client uses consistent URLs:

```typescript
// ✓ CORRECT - Consistent use of hostname
const apiUrl = 'http://127.0.0.1:8000'; // Use IP
// OR
const apiUrl = 'http://localhost:8000';  // Use hostname

// ✗ INCORRECT - Mixed usage
const apiUrl1 = 'http://localhost:8000';
const apiUrl2 = 'http://127.0.0.1:8000'; // Creates CORS issues
```

---

## API Endpoints

### Core Endpoints

#### Health Check
```http
GET /health/
```
**No authentication required**

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "2.0.0"
}
```

#### Configuration
```http
GET /api/v2/core/config/
Authorization: Bearer <token>
```

Response:
```json
{
  "app_name": "PromptCraft",
  "version": "2.0.0",
  "features": {
    "templates": true,
    "ai_services": true,
    "chat": true,
    "analytics": true,
    "billing": true,
    "research": true
  }
}
```

### Templates

#### List Templates
```http
GET /api/v2/templates/?page=1&limit=20
Authorization: Bearer <token>
```

#### Featured Templates
```http
GET /api/v2/templates/featured/
Authorization: Bearer <token>
```

#### Trending Templates
```http
GET /api/v2/templates/trending/
Authorization: Bearer <token>
```

#### Template Categories
```http
GET /api/v2/template-categories/
Authorization: Bearer <token>
```

### AI Services

#### Assistant Endpoint
```http
GET /api/v2/ai/assistant/
POST /api/v2/ai/assistant/

Authorization: Bearer <token>
```

#### Threads
```http
GET /api/v2/ai/assistant/threads/
POST /api/v2/ai/assistant/threads/

Authorization: Bearer <token>
```

### Analytics

#### Dashboard
```http
GET /api/v2/analytics/dashboard/
Authorization: Bearer <token>
```

Response:
```json
{
  "user_metrics": {
    "total_users": 150,
    "active_today": 45,
    "new_today": 12
  },
  "template_metrics": {
    "total_templates": 245,
    "used_today": 89,
    "trending": [...]
  }
}
```

#### Track Event
```http
POST /api/v2/analytics/track/
Authorization: Bearer <token>

{
  "event_name": "template_used",
  "template_id": 123,
  "metadata": {
    "duration_ms": 5000
  }
}
```

### Orchestrator

#### Intent Detection
```http
POST /api/v2/orchestrator/intent/
Authorization: Bearer <token>

{
  "prompt": "Create a blog post about AI"
}
```

#### Template Rendering
```http
POST /api/v2/orchestrator/render/
Authorization: Bearer <token>

{
  "template_id": 123,
  "variables": {
    "topic": "Machine Learning",
    "length": "long"
  }
}
```

#### Library Search
```http
GET /api/v2/orchestrator/search/?q=blog&category=writing
Authorization: Bearer <token>
```

---

## Best Practices

### 1. API Client Setup

Create a single, centralized API client instance:

```typescript
// api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add interceptors for authentication, error handling, etc.
apiClient.interceptors.request.use(/* ... */);
apiClient.interceptors.response.use(/* ... */);
```

### 2. Environment-Specific Configuration

```typescript
// config/api.ts
export const API_CONFIG = {
  development: {
    baseURL: 'http://127.0.0.1:8000',
    timeout: 30000,
    retryAttempts: 3,
  },
  production: {
    baseURL: 'https://api.prompt-temple.com',
    timeout: 30000,
    retryAttempts: 2,
  },
};

export const getAPIConfig = () => {
  return API_CONFIG[process.env.NODE_ENV as keyof typeof API_CONFIG];
};
```

### 3. Error Boundaries

Wrap components that make API calls in error boundaries:

```typescript
import { ErrorBoundary } from 'react-error-boundary';

export function TemplatesPage() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <TemplatesList />
    </ErrorBoundary>
  );
}
```

### 4. Loading States

Always show loading indicators during API calls:

```typescript
export function useTemplates() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    apiClient.get('/api/v2/templates/')
      .then(res => setTemplates(res.data))
      .catch(err => setError(err))
      .finally(() => setLoading(false));
  }, []);

  return { templates, loading, error };
}
```

### 5. Rate Limiting

Implement rate limiting on the frontend:

```typescript
import { throttle } from 'lodash-es';

const throttledSearch = throttle(async (query: string) => {
  return apiClient.get('/api/v2/orchestrator/search/', {
    params: { q: query }
  });
}, 500);
```

### 6. Token Management

Store tokens securely:

```typescript
// localStorage - for access token (short-lived)
localStorage.setItem('accessToken', token);

// httpOnly cookie - for refresh token (long-lived)
// Set by backend on login response
// Automatically sent with requests

// Clear on logout
localStorage.removeItem('accessToken');
// Cookie cleared by backend
```

### 7. Request/Response Logging

Log requests and responses in development:

```typescript
if (process.env.NODE_ENV === 'development') {
  apiClient.interceptors.request.use(config => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config);
    return config;
  });

  apiClient.interceptors.response.use(
    response => {
      console.log(`[API] Response ${response.status}`, response.data);
      return response;
    },
    error => {
      console.error(`[API] Error ${error.response?.status}`, error);
      throw error;
    }
  );
}
```

### 8. Pagination

Implement proper pagination handling:

```typescript
export async function fetchPaginatedTemplates(page: number = 1, limit: number = 20) {
  return apiClient.get('/api/v2/templates/', {
    params: { page, limit }
  });
}
```

---

## Troubleshooting

### CORS Errors

**Error**: `No 'Access-Control-Allow-Origin' header is present on the requested resource`

**Solutions**:
1. Verify backend CORS configuration in `settings.py`
2. Ensure `corsheaders` middleware is installed and configured
3. Check that your frontend origin is in `CORS_ALLOWED_ORIGINS`
4. Verify middleware order (CORS middleware must come before other middleware)
5. In development, check that `DEBUG=True` and `CORS_ALLOW_ALL_ORIGINS=True`

**Check CORS Headers**:
```bash
# Make a preflight request
curl -X OPTIONS http://127.0.0.1:8000/api/v2/templates/ \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Look for in response:
# Access-Control-Allow-Origin: http://localhost:3001
# Access-Control-Allow-Methods: GET, POST, ...
# Access-Control-Allow-Headers: ...
```

### 401 Unauthorized Errors

**Error**: `401 Unauthorized`

**Solutions**:
1. Check that token is included in Authorization header
2. Verify token hasn't expired
3. Try refreshing token
4. Clear tokens and re-login
5. Check token format: `Authorization: Bearer <token>`

### 404 Not Found Errors

**Error**: `404 Not Found`

**Solutions**:
1. Verify endpoint URL is correct
2. Check API version (v1 vs v2)
3. Verify resource exists
4. Check URL parameters and query strings

### Network Timeouts

**Error**: `Error: timeout of 30000ms exceeded`

**Solutions**:
1. Increase timeout in API client configuration
2. Check backend performance and load
3. Check network connectivity
4. Implement request cancellation for long operations
5. Use WebSocket instead of long polling for real-time data

### Rate Limiting

**Error**: `429 Too Many Requests`

**Solutions**:
1. Implement exponential backoff retry logic
2. Throttle requests on frontend
3. Cache responses when possible
4. Contact support to increase rate limits if needed

---

## Additional Resources

- [OpenAPI Documentation](/api/schema/swagger-ui/)
- [Authentication Guide](./AUTHENTICATION_GUIDE.md)
- [Deployment Guide](./RAILWAY_DEPLOYMENT.md)
- [API Coverage Report](./API_COVERAGE.md)

---

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review the [OpenAPI documentation](/api/schema/swagger-ui/)
- Contact the development team
