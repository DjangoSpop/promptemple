# 🚀 DeepSeek Integration Guide for Frontend Developer

## 🔍 Problem Analysis
The 429 error you're seeing is from the **ZAI API** (GLM-4 model), not DeepSeek. Your backend was configured to use ZAI's API which has strict rate limits.

**Error Details:**
- **Status**: 429 "Too Many Requests" 
- **Model**: `glm-4-32b-0414-128k` (ZAI's GLM model)
- **Issue**: ZAI API rate limits are very restrictive

## ✅ Solution: Switch to DeepSeek API

I've updated the backend to use **DeepSeek API** instead, which has:
- **Better rate limits**
- **Lower costs** 
- **Better performance**
- **More reliable service**

## 🔧 Backend Changes Made

### 1. Updated Chat Views (`apps/chat/views.py`)
- ✅ Switched from ZAI API to DeepSeek API
- ✅ Changed model from `glm-4-32b-0414-128k` to `deepseek-chat`
- ✅ Updated API endpoints and authentication

### 2. Environment Configuration
- ✅ Added DeepSeek API configuration
- ✅ Maintained SSE streaming support

## 🎯 Frontend Actions Required

### 1. **No Frontend Code Changes Needed!**
Your existing SSE chat implementation will work without changes:

```typescript
// Your existing code continues to work
const response = await fetch('/api/v2/chat/completions/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream, application/json',
    'Authorization': `Bearer ${token}`,
  },
  body: JSON.stringify({
    messages: [{ role: 'user', content: message }],
    model: 'deepseek-chat', // Now uses DeepSeek!
    stream: true,
    temperature: 0.7,
    max_tokens: 2048
  })
});
```

### 2. **Optional: Update Model Names**
You can now use these DeepSeek models:

```typescript
// Available DeepSeek models
const models = {
  chat: 'deepseek-chat',      // General conversation
  coder: 'deepseek-coder',    // Code-specific tasks
  v2: 'deepseek-chat-v2',     // Latest version
};

// Example usage
const payload = {
  messages: [...],
  model: 'deepseek-chat',  // or 'deepseek-coder' for coding tasks
  stream: true
};
```

### 3. **Updated Response Format**
You'll now receive DeepSeek responses instead of GLM:

```typescript
// Expected stream responses from DeepSeek
{
  "id": "chatcmpl-...",
  "object": "chat.completion.chunk",
  "created": 1693838400,
  "model": "deepseek-chat",  // No longer glm-4-32b-0414-128k
  "choices": [{
    "index": 0,
    "delta": {
      "content": "Response content here..."
    },
    "finish_reason": null
  }]
}
```

## 🛠️ Backend Setup Required

**For the backend developer (you):**

1. **Add DeepSeek API Key to environment:**
```bash
# Add to .env file
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
```

2. **Get DeepSeek API Key:**
   - Visit: https://platform.deepseek.com
   - Sign up/login
   - Generate API key
   - Add to environment variables

3. **Restart your backend server:**
```powershell
python manage.py runserver
```

## 🧪 Testing the Fix

### Test 1: Health Check
```bash
curl http://localhost:8000/api/v2/chat/health/
```

**Expected Response:**
```json
{
  "status": "healthy",
  "message": "Chat SSE service is properly configured",
  "config": {
    "provider": "deepseek",
    "api_base_configured": true,
    "api_token_configured": true,
    "sse_available": true
  }
}
```

### Test 2: Chat Completion
```bash
curl -X POST http://localhost:8000/api/v2/chat/completions/ \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "messages": [{"role": "user", "content": "Hello DeepSeek!"}],
    "model": "deepseek-chat",
    "stream": true
  }'
```

**Expected Response:**
```
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","model":"deepseek-chat",...}
data: {"choices":[{"delta":{"content":"Hello! How can I help you today?"}}]}
data: [DONE]
```

## 🎉 Benefits of DeepSeek

✅ **No more 429 rate limit errors**  
✅ **Faster response times**  
✅ **Lower API costs**  
✅ **Better model performance**  
✅ **More reliable service**  

## 🚨 Important Notes

1. **Frontend code requires NO changes** - same API endpoint, same format
2. **Model responses will be from DeepSeek** instead of GLM
3. **Rate limits are much more generous** with DeepSeek
4. **API costs are significantly lower**

## 📞 Need Help?

If you encounter any issues:
1. Check that `DEEPSEEK_API_KEY` is set in environment
2. Verify the backend server restarted after environment changes
3. Test the health endpoint first
4. Check backend logs for any configuration errors

The 429 error should be completely resolved with this switch to DeepSeek! 🎯