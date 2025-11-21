# 🚀 Chat Migration Guide: WebSocket → HTTP SSE Streaming

## 📋 Overview

**From Backend Engineering Team to Frontend Team**

We've successfully implemented **HTTP Server-Sent Events (SSE)** streaming for our chat functionality to replace WebSocket connections. This migration provides better reliability, simpler error handling, and improved scalability for our MVP.

### 🎯 Migration Benefits
- **Simpler Implementation**: Standard HTTP requests vs complex WebSocket management
- **Better Error Handling**: HTTP status codes and standard retry mechanisms
- **Improved Reliability**: Auto-reconnection and standard browser caching
- **Production Ready**: Works seamlessly with load balancers and CDNs
- **Cost Effective**: Integrated with Z.AI's high-performance models

---

## 🔧 Backend Implementation Status

### ✅ Completed
- **SSE Streaming Endpoint**: `/api/v2/chat/completions/`
- **Z.AI Integration**: High-performance GLM-4-32B model
- **JWT Authentication**: Secure user verification
- **Rate Limiting**: 5 requests/minute per user
- **Error Handling**: Comprehensive error responses
- **Health Check**: `/api/v2/chat/health/`

### 🎛️ Configuration
```env
# Current Backend Configuration
CHAT_TRANSPORT=sse
ZAI_API_BASE=https://api.z.ai/api/paas/v4
ZAI_DEFAULT_MODEL=glm-4-32b-0414-128k
```

---

## 📡 API Protocol Documentation

### **New SSE Endpoint**
```
POST /api/v2/chat/completions/
Content-Type: application/json
Accept: text/event-stream
Authorization: Bearer <JWT_TOKEN>
```

### **Request Format**
```typescript
interface ChatCompletionRequest {
  messages: Array<{
    role: 'user' | 'assistant' | 'system';
    content: string;
  }>;
  model?: string;           // Default: 'glm-4-32b-0414-128k'
  stream?: boolean;         // Always true for SSE
  temperature?: number;     // Default: 0.7
  max_tokens?: number;      // Default: 4096
}
```

### **Response Format (SSE Stream)**
```typescript
// Connection Start
event: stream_start
data: {"trace_id":"abc123","model":"glm-4-32b-0414-128k","stream_start":true}

// Streaming Tokens (OpenAI-compatible format)
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"glm-4-32b-0414-128k","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"glm-4-32b-0414-128k","choices":[{"index":0,"delta":{"content":" there!"},"finish_reason":null}]}

// Stream Complete
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"glm-4-32b-0414-128k","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]

// Completion Event
event: stream_complete
data: {"stream_complete":true,"processing_time_ms":1500,"request_id":"req123"}
```

### **Error Handling**
```typescript
// Error Response
event: error
data: {"error":"Rate limit exceeded","code":"rate_limit_error","status":429}

// Connection Error
event: error
data: {"error":"Cannot connect to vendor API","code":"connection_error"}

// Timeout Error
event: error
data: {"error":"Request timeout","code":"timeout_error"}
```

---

## 🔄 Frontend Migration Guide

### **Phase 1: Create SSE Client Class**

```typescript
// utils/sseClient.ts
export class ChatSSEClient {
  private eventSource: EventSource | null = null;
  private abortController: AbortController | null = null;
  
  // Event handlers
  onStreamStart?: (data: any) => void;
  onStreamToken?: (data: any) => void;
  onStreamComplete?: (data: any) => void;
  onError?: (error: any) => void;
  onConnectionEnd?: () => void;

  async sendMessage(
    messages: Array<{role: string; content: string}>,
    options: {
      model?: string;
      temperature?: number;
      max_tokens?: number;
    } = {}
  ): Promise<void> {
    try {
      // Clean up previous connection
      this.disconnect();
      
      // Create new abort controller for this request
      this.abortController = new AbortController();
      
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('No authentication token');
      }

      const payload = {
        messages,
        model: options.model || 'glm-4-32b-0414-128k',
        stream: true,
        temperature: options.temperature || 0.7,
        max_tokens: options.max_tokens || 4096
      };

      // Make HTTP request to SSE endpoint
      const response = await fetch('/api/v2/chat/completions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify(payload),
        signal: this.abortController.signal
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      // Create EventSource from response
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          this.handleSSELine(line);
        }
      }

      this.onConnectionEnd?.();

    } catch (error) {
      if (error.name !== 'AbortError') {
        this.onError?.(error);
      }
    }
  }

  private handleSSELine(line: string) {
    const trimmed = line.trim();
    if (!trimmed) return;

    if (trimmed.startsWith('event: ')) {
      // Handle event type (stream_start, stream_complete, error)
      return;
    }

    if (trimmed.startsWith('data: ')) {
      const data = trimmed.slice(6);
      
      if (data === '[DONE]') {
        return; // Stream finished
      }

      try {
        const parsed = JSON.parse(data);
        
        // Handle different event types
        if (parsed.stream_start) {
          this.onStreamStart?.(parsed);
        } else if (parsed.stream_complete) {
          this.onStreamComplete?.(parsed);
        } else if (parsed.error) {
          this.onError?.(parsed);
        } else if (parsed.choices && parsed.choices[0]?.delta?.content) {
          // OpenAI-compatible token streaming
          this.onStreamToken?.(parsed.choices[0].delta);
        }
      } catch (e) {
        console.warn('Failed to parse SSE data:', data);
      }
    }
  }

  disconnect() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
```

### **Phase 2: Update Chat Component**

```typescript
// components/Chat.tsx
import { useState, useRef, useEffect } from 'react';
import { ChatSSEClient } from '../utils/sseClient';

export function ChatComponent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const sseClient = useRef<ChatSSEClient | null>(null);
  const currentMessageId = useRef<string | null>(null);

  useEffect(() => {
    // Initialize SSE client
    sseClient.current = new ChatSSEClient();
    
    sseClient.current.onStreamStart = (data) => {
      console.log('🚀 Stream started:', data);
      setIsStreaming(true);
      setError(null);
      currentMessageId.current = `msg_${Date.now()}`;
    };

    sseClient.current.onStreamToken = (delta) => {
      if (delta.content) {
        setStreamingContent(prev => prev + delta.content);
      }
    };

    sseClient.current.onStreamComplete = (data) => {
      console.log('✅ Stream completed:', data);
      
      // Add the complete message
      if (currentMessageId.current && streamingContent) {
        setMessages(prev => [...prev, {
          id: currentMessageId.current!,
          role: 'assistant',
          content: streamingContent,
          timestamp: new Date()
        }]);
      }
      
      // Reset streaming state
      setStreamingContent('');
      setIsStreaming(false);
      currentMessageId.current = null;
    };

    sseClient.current.onError = (error) => {
      console.error('❌ Chat error:', error);
      setError(error.error || error.message || 'Unknown error');
      setIsStreaming(false);
      setStreamingContent('');
    };

    sseClient.current.onConnectionEnd = () => {
      console.log('🔌 Connection ended');
      setIsStreaming(false);
    };

    return () => {
      sseClient.current?.disconnect();
    };
  }, []);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isStreaming) return;

    // Add user message
    const userMessage = {
      id: `user_${Date.now()}`,
      role: 'user' as const,
      content: content.trim(),
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setError(null);

    // Build conversation history
    const conversationHistory = [...messages, userMessage].map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    // Send via SSE
    await sseClient.current?.sendMessage(conversationHistory, {
      model: 'glm-4-32b-0414-128k',
      temperature: 0.7,
      max_tokens: 4096
    });
  };

  return (
    <div className="chat-container">
      {/* Messages Display */}
      <div className="messages">
        {messages.map(message => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="content">{message.content}</div>
            <div className="timestamp">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        
        {/* Streaming Message */}
        {isStreaming && streamingContent && (
          <div className="message assistant streaming">
            <div className="content">
              {streamingContent}
              <span className="cursor">▋</span>
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          ❌ {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Input */}
      <ChatInput 
        onSend={sendMessage} 
        disabled={isStreaming}
        placeholder={isStreaming ? "AI is typing..." : "Type your message..."}
      />
    </div>
  );
}
```

### **Phase 3: Health Check Integration**

```typescript
// utils/healthCheck.ts
export async function checkChatHealth(): Promise<{
  status: 'healthy' | 'degraded' | 'error';
  message: string;
  config?: any;
}> {
  try {
    const token = localStorage.getItem('auth_token');
    const response = await fetch('/api/v2/chat/health/', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return await response.json();
  } catch (error) {
    return {
      status: 'error',
      message: 'Cannot connect to chat service'
    };
  }
}

// Use in your app initialization
export function useChatHealth() {
  const [health, setHealth] = useState<any>(null);
  
  useEffect(() => {
    checkChatHealth().then(setHealth);
    const interval = setInterval(() => {
      checkChatHealth().then(setHealth);
    }, 30000); // Check every 30 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  return health;
}
```

---

## 🔄 Migration Checklist

### **Before Migration**
- [ ] **Test SSE endpoint** with curl or Postman
- [ ] **Verify JWT token** is correctly passed
- [ ] **Test error scenarios** (invalid token, rate limits)
- [ ] **Implement health checks** in your app

### **During Migration**
- [ ] **Feature flag** the new implementation
- [ ] **A/B test** with small user group
- [ ] **Monitor performance** and error rates
- [ ] **Fallback plan** to WebSocket if needed

### **After Migration**
- [ ] **Remove WebSocket dependencies** 
- [ ] **Update error handling** for HTTP-specific errors
- [ ] **Optimize reconnection logic**
- [ ] **Update monitoring dashboards**

---

## 🧪 Testing Guide

### **Manual Testing**
```bash
# Test SSE endpoint directly
curl -X POST "http://localhost:8000/api/v2/chat/completions/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "model": "glm-4-32b-0414-128k",
    "stream": true
  }'
```

### **Health Check**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/api/v2/chat/health/"
```

---

## 🚨 Migration Timeline

### **Phase 1 (This Week)**
- Implement SSE client class
- Update one chat component
- Test with development environment

### **Phase 2 (Next Week)**
- Deploy to staging
- Performance testing
- Error handling refinement

### **Phase 3 (Following Week)**
- Production deployment
- Monitor and optimize
- Remove WebSocket code

---

## 🔍 Debugging & Monitoring

### **Browser DevTools**
- **Network Tab**: Monitor SSE requests and responses
- **Console**: Check for JavaScript errors
- **Application Tab**: Verify JWT token storage

### **Server Logs**
- **SSE Connections**: `SSE Proxy: Starting stream for request {id}`
- **Token Streaming**: `Connected to vendor API - Request: {id}`
- **Errors**: `SSE Proxy: {error_type} - Request: {id}`

### **Key Metrics to Monitor**
- **Connection Success Rate**: >99%
- **Average Response Time**: <2 seconds
- **Token Streaming Rate**: >50 tokens/second
- **Error Rate**: <1%

---

## 💬 Support & Questions

**Backend Team Contact**: 
- Implementation questions: GitHub issues
- Urgent problems: Slack #backend-support
- Architecture discussions: Weekly tech sync

**Documentation**: 
- API Reference: `/api/schema/swagger-ui/`
- Health Status: `/api/v2/chat/health/`
- System Status: `/health/`

---

**🎯 Next Steps**: Implement the SSE client class and test with a single chat component. The backend is ready and tested - you're good to start the frontend migration!