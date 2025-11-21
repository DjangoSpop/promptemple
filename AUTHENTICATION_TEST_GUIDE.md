# Authentication Test Guide

## Current Status ✅

The Django endpoint `/api/v2/chat/completions/` exists and is properly configured. The frontend is successfully connecting to Django directly (no more proxy errors).

## Test Authentication

### 1. Check if User is Logged In
Open browser console and run:
```javascript
// Check current token status
console.log('Access Token:', localStorage.getItem('access_token'));
console.log('Refresh Token:', localStorage.getItem('refresh_token'));

// Check auth status
window.debugAuth?.();
```

### 2. If No Token, Login First
Navigate to `/auth/login` and login with valid credentials.

### 3. Test Chat After Login
After successful login, try the chat function again. The enhanced error handling will now show:
- Token validation details
- Specific error messages for 401/406
- Clearer debugging information

## Expected Behavior

**Before Login:**
- ❌ "No authentication token available" error
- ❌ 401 Unauthorized from Django

**After Login:**
- ✅ Token present in localStorage
- ✅ Detailed token information in console
- ✅ Successful chat requests to Django

## Error Codes Explained

- **401 Unauthorized**: Token missing/invalid → Login required
- **406 Not Acceptable**: Request format issue → Check headers
- **403 Forbidden**: Valid token but insufficient permissions
- **200 Success**: Chat working correctly

## Debugging Commands

```javascript
// Check authentication
localStorage.getItem('access_token') ? 'Logged in' : 'Not logged in'

// Manual token test
fetch('http://127.0.0.1:8000/api/v2/chat/health/', {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
}).then(r => console.log('Health check:', r.status))
```
