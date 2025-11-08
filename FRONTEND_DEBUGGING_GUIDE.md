# PromptCraft Frontend Debugging Guide

## Overview

This guide helps frontend developers diagnose and resolve issues when integrating with the PromptCraft API backend.

## Quick Diagnostics

### 1. Check If Backend is Running

```bash
# In browser console or terminal
curl http://127.0.0.1:8000/health/

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Check CORS Configuration

Open browser console (F12) and look for errors like:
```
Access to XMLHttpRequest at 'http://127.0.0.1:8000/api/v2/templates/' 
from origin 'http://localhost:3001' has been blocked by CORS policy
```

**If you see this error:**
- Backend CORS is not configured
- Run: `python manage.py verify_api --check-cors` on backend
- Update `settings.py` CORS settings

### 3. Check Network Requests

1. Open DevTools → Network tab
2. Make an API call in your app
3. Look for the request in the Network tab
4. Click on it to see details:
   - **Headers tab**: Check request headers and response headers
   - **Response tab**: Check response body
   - **Status**: Should be 2xx for success, 4xx for client error, 5xx for server error

### 4. Check Console for Errors

Open DevTools → Console tab and look for:
- Red error messages
- Warning messages
- Failed requests
- Stack traces

## Common Issues and Solutions

### Issue 1: CORS Policy Blocking Requests

**Error Message:**
```
Access to XMLHttpRequest at 'http://127.0.0.1:8000/api/v2/...' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header
```

**Root Cause**: Backend not configured for CORS

**Solutions**:

1. **Check backend CORS configuration:**
   ```bash
   # SSH into backend or local terminal
   python manage.py shell
   from django.conf import settings
   
   # Check if corsheaders is installed
   print('corsheaders' in settings.INSTALLED_APPS)
   
   # Check CORS settings
   print(settings.CORS_ALLOW_ALL_ORIGINS)
   print(settings.CORS_ALLOWED_ORIGINS)
   ```

2. **Verify middleware order:**
   ```python
   # In settings.py, CORS middleware must be FIRST
   MIDDLEWARE = [
       "django.middleware.security.SecurityMiddleware",
       "corsheaders.middleware.CorsMiddleware",  # ← MUST BE HERE
       "django.contrib.sessions.middleware.SessionMiddleware",
       # ... other middleware
   ]
   ```

3. **Check if DEBUG=True in development:**
   ```bash
   # Backend settings should have:
   DEBUG=True  # Development only!
   CORS_ALLOW_ALL_ORIGINS = True  # Only in development
   ```

4. **Test with curl:**
   ```bash
   # Test preflight request
   curl -X OPTIONS http://127.0.0.1:8000/api/v2/templates/ \
     -H "Origin: http://localhost:3001" \
     -H "Access-Control-Request-Method: GET" \
     -v
   
   # Look for these headers in response:
   # Access-Control-Allow-Origin: http://localhost:3001
   # Access-Control-Allow-Methods: GET, POST, OPTIONS, ...
   ```

### Issue 2: 401 Unauthorized Errors

**Error Message:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Root Cause**: Missing or invalid authentication token

**Debugging Steps**:

1. **Check if logged in:**
   ```javascript
   // In browser console
   localStorage.getItem('accessToken')  // Should return token
   ```

2. **Check Authorization header:**
   ```javascript
   // In Network tab, click on API request
   // Headers section should show:
   // Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
   ```

3. **Check token expiration:**
   ```javascript
   // Decode JWT token (https://jwt.io/)
   const token = localStorage.getItem('accessToken');
   const parts = token.split('.');
   const payload = JSON.parse(atob(parts[1]));
   console.log('Token expires at:', new Date(payload.exp * 1000));
   console.log('Token is valid:', payload.exp * 1000 > Date.now());
   ```

4. **Login and refresh token:**
   ```bash
   # Clear stored token
   localStorage.clear()
   
   # Login again
   # This should fetch new token from backend
   ```

**Solutions**:

1. **Ensure token is sent in requests:**
   ```typescript
   // In api-client.ts or wherever you make requests
   headers: {
     'Authorization': `Bearer ${accessToken}`
   }
   ```

2. **Implement token refresh logic:**
   ```typescript
   // When 401 is received, refresh token
   if (error.response.status === 401) {
     const newToken = await refreshAccessToken();
     localStorage.setItem('accessToken', newToken);
     // Retry original request
   }
   ```

3. **Check endpoint doesn't require auth:**
   ```bash
   # These endpoints don't need authentication
   GET /health/
   POST /api/v2/auth/login/
   POST /api/v2/auth/register/
   ```

### Issue 3: 404 Not Found Errors

**Error Message:**
```json
{
  "detail": "Not found."
}
```

**Debugging Steps**:

1. **Verify endpoint URL:**
   ```javascript
   // In browser console
   const url = '/api/v2/templates/';
   console.log('Full URL:', `http://127.0.0.1:8000${url}`);
   
   // Try in new tab or with curl
   ```

2. **Check API version:**
   - API v2: `/api/v2/*`
   - API v1: `/api/v1/*` (legacy)
   - Choose correct version

3. **List all available endpoints:**
   ```bash
   # Backend terminal
   python manage.py show_urls
   
   # Or visit API root
   curl http://127.0.0.1:8000/api/
   ```

4. **Check URL parameters:**
   ```javascript
   // Wrong
   '/api/v2/templates/featured'  // Missing trailing slash
   
   // Correct
   '/api/v2/templates/featured/'
   ```

**Solutions**:

1. **Verify endpoint exists:**
   ```bash
   # List endpoints
   curl http://127.0.0.1:8000/api/
   ```

2. **Check URL format:**
   ```typescript
   // Make sure endpoint has trailing slash
   const endpoint = '/api/v2/templates/';  // ✓ Correct
   // not: '/api/v2/templates'              // ✗ Wrong
   ```

3. **Check API version:**
   ```typescript
   const apiVersion = process.env.REACT_APP_API_VERSION || 'v2';
   const endpoint = `/api/${apiVersion}/templates/`;
   ```

### Issue 4: Network Timeouts

**Error Message:**
```
Error: timeout of 30000ms exceeded
```

**Debugging Steps**:

1. **Check backend is running:**
   ```bash
   # Try to reach backend
   curl http://127.0.0.1:8000/health/
   ```

2. **Check network latency:**
   ```javascript
   // In Network tab
   // Check Time column - should be < 5s for most requests
   ```

3. **Check if database is slow:**
   ```bash
   # Backend logs might show slow queries
   # Check database connection
   python manage.py dbshell
   ```

**Solutions**:

1. **Increase timeout:**
   ```typescript
   // In api-client.ts
   const apiClient = axios.create({
     timeout: 60000  // Increase from 30s to 60s
   });
   ```

2. **Implement retry logic:**
   ```typescript
   // Retry on timeout
   async function retryRequest(fn, maxRetries = 3) {
     for (let i = 0; i < maxRetries; i++) {
       try {
         return await fn();
       } catch (error) {
         if (i === maxRetries - 1) throw error;
         await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
       }
     }
   }
   ```

3. **Use pagination for large data:**
   ```typescript
   // Load data in chunks
   const templates = await apiClient.get('/api/v2/templates/', {
     params: { page: 1, limit: 20 }
   });
   ```

### Issue 5: JSON Parsing Errors

**Error Message:**
```
Unexpected token < in JSON at position 0
```

**Root Cause**: Response is HTML instead of JSON (often an error page)

**Debugging Steps**:

1. **Check response in Network tab:**
   - Click on request
   - Go to Response tab
   - If it starts with `<!DOCTYPE html>`, it's HTML not JSON
   - This usually means a 500 error or 404

2. **Check response status code:**
   - 5xx means server error
   - 4xx means client error
   - Check Status column in Network tab

3. **Check backend logs:**
   ```bash
   # Backend terminal should show error messages
   # Look for stack trace or error details
   ```

**Solutions**:

1. **Handle different response types:**
   ```typescript
   try {
     const response = await apiClient.get(url);
     // Process JSON response
   } catch (error) {
     if (error.response?.headers['content-type']?.includes('text/html')) {
       console.error('Got HTML response, likely an error page');
       console.error('Check backend logs');
     }
   }
   ```

2. **Check backend logs for errors:**
   ```bash
   # Backend terminal will show detailed errors
   # Look for exception tracebacks
   ```

3. **Verify endpoint returns JSON:**
   ```bash
   curl -H "Accept: application/json" http://127.0.0.1:8000/api/v2/templates/
   ```

### Issue 6: Mixed Content Warnings

**Error Message:**
```
Mixed Content: The page at 'https://...' was loaded over HTTPS, 
but requested an insecure resource 'http://...'
```

**Root Cause**: Frontend is HTTPS but backend is HTTP

**Solutions**:

1. **Use same protocol:**
   ```typescript
   // In production, use HTTPS for both
   const baseURL = process.env.REACT_APP_API_URL;
   // Should be 'https://api.example.com'
   ```

2. **In development, use HTTP for both:**
   ```typescript
   // Local: http://localhost:3001 → http://127.0.0.1:8000
   const baseURL = 'http://127.0.0.1:8000';
   ```

## Browser DevTools Tips

### 1. Network Tab

```
1. Open DevTools (F12)
2. Go to Network tab
3. Reload page (Ctrl+R or Cmd+R)
4. Click on API request
5. View tabs:
   - Headers: Request and response headers
   - Preview: Formatted response
   - Response: Raw response text
   - Timing: Request timing breakdown
```

### 2. Console Tab

```
1. Open DevTools (F12)
2. Go to Console tab
3. Check for errors (red text)
4. Check for warnings (yellow text)
5. Type JavaScript commands to test:
   - localStorage.getItem('accessToken')
   - fetch('/api/v2/templates/')
   - console.log('debugging')
```

### 3. Application Tab

```
1. Open DevTools (F12)
2. Go to Application tab
3. Check:
   - Local Storage: Stored tokens, config
   - Cookies: Session cookies
   - Session Storage: Temporary data
   - Indexed DB: Offline data
```

### 4. Network Throttling

```
1. Open Network tab
2. Click dropdown (usually says "No throttling")
3. Select "Slow 3G" or "Fast 3G"
4. This simulates slow networks
5. Good for testing timeout/retry logic
```

## API Testing Tools

### Using cURL

```bash
# GET request
curl http://127.0.0.1:8000/api/v2/templates/

# POST request
curl -X POST http://127.0.0.1:8000/api/v2/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# With Authorization header
curl http://127.0.0.1:8000/api/v2/templates/ \
  -H "Authorization: Bearer <your-token>"

# Print request and response headers
curl -v http://127.0.0.1:8000/api/v2/templates/

# Follow redirects
curl -L http://127.0.0.1:8000/api/v2/templates/
```

### Using Postman

1. Download Postman: https://www.postman.com/downloads/
2. Create new request
3. Enter URL: `http://127.0.0.1:8000/api/v2/templates/`
4. Go to Headers tab
5. Add: `Authorization: Bearer <your-token>`
6. Click Send
7. View response in Response tab

### Using REST Client Extension (VS Code)

Create file `test.http`:
```http
GET http://127.0.0.1:8000/api/v2/templates/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

###

POST http://127.0.0.1:8000/api/v2/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

Then click "Send Request" above each request.

## Logging and Debugging Code

### Add Console Logging

```typescript
// In api-client.ts
client.interceptors.request.use(
  (config) => {
    console.log('[API] Request:', config.method?.toUpperCase(), config.url, config);
    return config;
  }
);

client.interceptors.response.use(
  (response) => {
    console.log('[API] Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('[API] Error:', error.response?.status, error.response?.data);
    throw error;
  }
);
```

### Add Breakpoints

1. Open DevTools
2. Go to Sources tab
3. Click line number to set breakpoint
4. Trigger action in app
5. Debugger pauses at breakpoint
6. Use Step Over/Into to debug

### React DevTools

1. Install React DevTools extension
2. Go to Components tab in DevTools
3. Click on component to inspect
4. View props and state
5. Edit props to test

## Performance Issues

### Check Load Time

```javascript
// In console
performance.getEntriesByType('navigation')[0];

// Check Network tab for slow requests
// Requests taking >5s should be optimized
```

### Identify Bottlenecks

```javascript
// Time API request
console.time('templates');
const data = await fetch('/api/v2/templates/');
console.timeEnd('templates');
```

### Use Pagination

```typescript
// Instead of loading all data at once
const page1 = await apiClient.get('/api/v2/templates/', {
  params: { page: 1, limit: 20 }
});

// Load more on demand
const page2 = await apiClient.get('/api/v2/templates/', {
  params: { page: 2, limit: 20 }
});
```

## Useful Resources

- [MDN Web Docs](https://developer.mozilla.org/)
- [Chrome DevTools Guide](https://developer.chrome.com/docs/devtools/)
- [Axios Documentation](https://axios-http.com/)
- [REST API Best Practices](https://restfulapi.net/)
- [JWT.io](https://jwt.io/) - JWT token decoder
- [Postman Learning Center](https://learning.postman.com/)

## Getting Help

1. **Check console errors** - Most issues shown in red
2. **Check Network tab** - See request/response details
3. **Test with curl** - Verify backend is working
4. **Check logs** - Backend logs show detailed errors
5. **Ask for help** - Include:
   - Error message (from console)
   - Network tab screenshot
   - Steps to reproduce
   - Browser/OS info

---

**Last Updated**: January 2024
