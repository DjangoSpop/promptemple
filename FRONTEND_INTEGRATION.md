# 🚀 Frontend Integration Guide - Next.js + Django WebSocket

## 🎯 Overview
This guide shows how to connect your Next.js chat frontend with our Django WebSocket backend. Everything is ready - just follow these steps!

## ⚡ Quick Start

### 1. Start Django WebSocket Server
```powershell
# In your Django backend directory
cd "C:\Users\ahmed el bahi\MyPromptApp\my_prmpt_bakend"

# Activate environment and set API key
$env:DEEPSEEK_API_KEY="sk-e2b0d6d2de3a4850bfc21ebd4a671af8"

# Start with WebSocket support
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

### 2. Update Next.js Environment
In your Next.js project's `.env.local`:
```env
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 3. Test the Connection
```powershell
# Test WebSocket integration
python test_frontend_integration.py
```

## 🔌 WebSocket Protocol

### Connection URL
```
ws://localhost:8000/ws/chat/{session_id}/
```

### Message Types (Frontend → Backend)

#### 1. Chat Message
```javascript
{
  type: 'chat_message',
  message_id: 'uuid',
  content: 'Hello, can you help me?',
  timestamp: '2025-09-02T...'
}
```

#### 2. Prompt Optimization
```javascript
{
  type: 'optimize_prompt',
  prompt: 'Write something good',
  context: { category: 'marketing' },
  optimization_type: 'enhancement'
}
```

#### 3. Intent Analysis
```javascript
{
  type: 'intent_analysis',
  query: 'I need help with marketing content'
}
```

#### 4. Slash Commands
```javascript
{
  type: 'slash_command',
  command: 'summarize',  // 'intent', 'optimize', 'rewrite', 'code'
  content: 'Text to process...'
}
```

#### 5. Ping (for latency)
```javascript
{
  type: 'ping',
  timestamp: '2025-09-02T...'
}
```

### Message Types (Backend → Frontend)

#### 1. Connection Acknowledgment
```javascript
{
  type: 'connection_ack',
  session_id: 'uuid',
  timestamp: '2025-09-02T...',
  user_id: 'user_uuid',
  authenticated: true
}
```

#### 2. Message Response
```javascript
{
  type: 'message',
  message_id: 'uuid',
  content: 'AI response here...',
  role: 'assistant', // or 'user'
  timestamp: '2025-09-02T...',
  session_id: 'uuid',
  processing_time_ms: 250
}
```

#### 3. Typing Indicators
```javascript
// Start typing
{
  type: 'typing_start',
  timestamp: '2025-09-02T...'
}

// Stop typing
{
  type: 'typing_stop',
  timestamp: '2025-09-02T...'
}
```

#### 4. Optimization Result
```javascript
{
  type: 'optimization_result',
  message_id: 'uuid',
  original_prompt: 'Original text',
  optimized_prompt: 'Enhanced version',
  improvements: ['Added clarity', 'Better structure'],
  suggestions: ['Consider adding...'],
  confidence: 0.85,
  processing_time_ms: 350,
  timestamp: '2025-09-02T...'
}
```

#### 5. Intent Analysis Result
```javascript
{
  type: 'intent_result',
  query: 'Original query',
  category: 'content_creation',
  confidence: 0.9,
  keywords: ['marketing', 'content'],
  context: 'Marketing content creation intent',
  suggestions: ['Consider focusing on...'],
  processing_time_ms: 150
}
```

#### 6. Heartbeat
```javascript
{
  type: 'heartbeat',
  timestamp: '2025-09-02T...',
  session_id: 'uuid'
}
```

#### 7. Pong (latency response)
```javascript
{
  type: 'pong',
  timestamp: '2025-09-02T...',
  latency_ms: 25
}
```

#### 8. Error Messages
```javascript
{
  type: 'error',
  message: 'Error description',
  timestamp: '2025-09-02T...'
}
```

## 🔧 Frontend Integration Code

### WebSocket Hook Update
Update your `useWebSocket.ts` to match our protocol:

```typescript
// Add to your message type definitions
interface ChatMessage {
  type: 'chat_message';
  message_id: string;
  content: string;
  timestamp: string;
}

interface OptimizePrompt {
  type: 'optimize_prompt';
  prompt: string;
  context?: any;
  optimization_type?: string;
}

interface SlashCommand {
  type: 'slash_command';
  command: 'intent' | 'optimize' | 'rewrite' | 'summarize' | 'code';
  content: string;
}

// WebSocket connection with auth
const connectWebSocket = (sessionId: string, token?: string) => {
  const url = token 
    ? `${WS_URL}/ws/chat/${sessionId}/?token=${token}`
    : `${WS_URL}/ws/chat/${sessionId}/`;
  
  return new WebSocket(url);
};
```

### Chat Store Updates
Your existing Zustand store should work perfectly! Just ensure these message handlers:

```typescript
// In your chat store
const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'connection_ack':
      setConnectionStatus('connected');
      break;
      
    case 'message':
      addMessage({
        id: data.message_id,
        content: data.content,
        role: data.role,
        timestamp: data.timestamp,
        sessionId: data.session_id
      });
      break;
      
    case 'typing_start':
      setTypingIndicator(true);
      break;
      
    case 'typing_stop':
      setTypingIndicator(false);
      break;
      
    case 'optimization_result':
      addOptimizationResult(data);
      break;
      
    case 'intent_result':
      addIntentResult(data);
      break;
      
    case 'heartbeat':
      updateLastHeartbeat();
      break;
      
    case 'pong':
      updateLatency(data.latency_ms);
      break;
      
    case 'error':
      showError(data.message);
      break;
  }
};
```

## 🧪 Testing Your Integration

### 1. Backend Test
```powershell
# Test the WebSocket server
python test_frontend_integration.py
```

Expected output:
- ✅ WebSocket connected successfully
- ✅ Connection acknowledged
- ✅ Ping/Pong successful
- ✅ Chat message processed
- ✅ AI response received

### 2. Frontend Test
```javascript
// Test connection in browser console
const ws = new WebSocket('ws://localhost:8000/ws/chat/test-session/');

ws.onopen = () => console.log('Connected!');
ws.onmessage = (e) => console.log('Received:', JSON.parse(e.data));

// Send test message
ws.send(JSON.stringify({
  type: 'chat_message',
  message_id: crypto.randomUUID(),
  content: 'Hello from frontend!',
  timestamp: new Date().toISOString()
}));
```

## 🎯 Slash Commands Integration

Your existing slash commands will work perfectly:

```typescript
const handleSlashCommand = (command: string, content: string) => {
  websocket.send(JSON.stringify({
    type: 'slash_command',
    command: command, // 'intent', 'optimize', 'rewrite', 'summarize', 'code'
    content: content,
    timestamp: new Date().toISOString()
  }));
};

// Usage examples:
// /intent What should I write about?
// /optimize Write something good
// /rewrite This text needs improvement
// /summarize Long article content here...
// /code Help me with React hooks
```

## 🚀 Production Deployment

### Backend (Django)
```powershell
# Production server with WebSocket
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application

# Or with process management
gunicorn promptcraft.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Frontend (Next.js)
```env
# Production environment
NEXT_PUBLIC_WS_URL=wss://yourdomain.com
```

## 🔒 Authentication

The WebSocket supports JWT authentication:

### Query Parameter Method
```
ws://localhost:8000/ws/chat/session-id/?token=your-jwt-token
```

### Header Method (if your WebSocket client supports it)
```javascript
const headers = {
  'Authorization': 'Bearer your-jwt-token'
};
```

## 📊 Performance Metrics

Expected performance:
- **Connection Time**: <100ms
- **Message Round Trip**: <50ms
- **AI Response**: 200-800ms (depending on DeepSeek API)
- **Optimization**: 300-1000ms
- **Intent Analysis**: 100-300ms

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   Solution: Ensure Django is running with Daphne
   Command: daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
   ```

2. **CORS Issues**
   ```
   Add to Django settings:
   CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
   ```

3. **WebSocket Close Immediately**
   ```
   Check: Authentication and session_id format
   Valid session_id: alphanumeric, hyphens, underscores
   ```

4. **Slow AI Responses**
   ```
   Check: DeepSeek account balance
   Fallback: System uses mock responses if API unavailable
   ```

## 🎉 Success Checklist

- [ ] Django WebSocket server running
- [ ] Frontend connects successfully
- [ ] Messages send/receive properly
- [ ] AI responses working
- [ ] Slash commands functional
- [ ] Typing indicators showing
- [ ] Latency measurement working
- [ ] Error handling graceful
- [ ] Authentication working (if enabled)

## 🚀 You're Ready!

Your chat integration is now complete! The backend supports:
- ✅ Real-time chat with AI
- ✅ Prompt optimization
- ✅ Intent analysis
- ✅ Slash commands
- ✅ Typing indicators
- ✅ Latency measurement
- ✅ Error handling
- ✅ Authentication
- ✅ Heartbeat/reconnection

**Start chatting with your AI assistant! 🎯**