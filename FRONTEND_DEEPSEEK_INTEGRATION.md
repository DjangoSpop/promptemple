# 🎯 Complete Frontend Integration & DeepSeek AI Setup

## Current Issues & Solutions

### Issue 1: WebSocket Protocol Mismatch
**Problem**: Frontend using Socket.IO (`/socket.io/`) but backend expects native WebSocket (`/ws/chat/`)

### Issue 2: DeepSeek API Configuration  
**Problem**: DeepSeek service needs API key configuration

## 🔧 IMMEDIATE FIXES NEEDED

### 1. Frontend WebSocket Connection Fix

Your frontend is currently doing this (WRONG):
```javascript
// Socket.IO connection (incorrect)
ws://localhost:8000/socket.io/?EIO=4&transport=websocket&sid=session_e64525b4
```

It should be doing this (CORRECT):
```javascript
// Native WebSocket connection (correct)
ws://localhost:8000/ws/chat/session_user_123/?token=your_jwt_token
```

### Frontend Code Fix:

```typescript
// File: lib/websocket/ChatWebSocket.ts
export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private authToken: string;
  
  constructor(sessionId: string, authToken: string) {
    this.sessionId = sessionId;
    this.authToken = authToken;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      // CORRECT URL format for your Django backend
      const wsUrl = `ws://localhost:8000/ws/chat/${this.sessionId}/?token=${this.authToken}`;
      console.log('🔌 Connecting to WebSocket:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        resolve();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        reject(error);
      };
      
      this.ws.onclose = (event) => {
        console.log(`🔌 WebSocket closed (code: ${event.code}, reason: ${event.reason})`);
        this.reconnect();
      };
    });
  }

  private handleMessage(data: any) {
    console.log('📨 Received message:', data);
    
    switch (data.type) {
      case 'pong':
        // Heartbeat - just acknowledge
        console.debug('🏓 Heartbeat pong');
        break;
        
      case 'stream_token':
        // DeepSeek AI streaming response
        this.onStreamToken?.(data.data);
        break;
        
      case 'stream_complete':
        // Stream finished
        this.onStreamComplete?.(data.data);
        break;
        
      case 'chat_message':
        // Complete message
        this.onChatMessage?.(data.data);
        break;
        
      case 'error':
        console.error('❌ Chat error:', data);
        this.onError?.(data.data);
        break;
        
      default:
        console.debug('Unknown message type:', data.type);
    }
  }

  sendMessage(content: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'chat_message',
        data: {
          message: content,
          conversation_id: this.sessionId,
          timestamp: new Date().toISOString()
        }
      };
      
      console.log('📤 Sending message:', message);
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }

  // Event handlers (set these from your components)
  onStreamToken?: (data: any) => void;
  onStreamComplete?: (data: any) => void;
  onChatMessage?: (data: any) => void;
  onError?: (data: any) => void;

  private reconnect() {
    setTimeout(() => {
      console.log('🔄 Attempting to reconnect...');
      this.connect().catch(console.error);
    }, 2000);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

### 2. Chat Component Implementation

```tsx
// File: components/chat/ChatInterface.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { ChatWebSocket } from '../../lib/websocket/ChatWebSocket';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export const ChatInterface: React.FC = () => {
  const [wsClient, setWsClient] = useState<ChatWebSocket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Initialize WebSocket connection
    const sessionId = `session_user_${Date.now()}_${Math.random().toString(36)}`;
    const authToken = localStorage.getItem('auth_token') || '';
    
    if (!authToken) {
      console.error('No auth token found');
      return;
    }

    const client = new ChatWebSocket(sessionId, authToken);
    
    // Set up event handlers
    client.onStreamToken = (data) => {
      console.log('📝 Streaming token:', data.token);
      setStreamingContent(prev => prev + data.token);
      setIsLoading(true);
    };
    
    client.onStreamComplete = (data) => {
      console.log('✅ Stream complete:', data);
      
      // Add the complete streamed message
      setMessages(prev => [...prev, {
        id: data.message_id || `assistant_${Date.now()}`,
        role: 'assistant',
        content: streamingContent,
        timestamp: new Date(),
        isStreaming: false
      }]);
      
      setStreamingContent('');
      setIsLoading(false);
    };
    
    client.onChatMessage = (data) => {
      console.log('💬 Complete message:', data);
      
      setMessages(prev => [...prev, {
        id: data.message_id || `assistant_${Date.now()}`,
        role: 'assistant',
        content: data.content,
        timestamp: new Date()
      }]);
      
      setIsLoading(false);
    };
    
    client.onError = (data) => {
      console.error('❌ Chat error:', data);
      setIsLoading(false);
    };

    // Connect
    client.connect()
      .then(() => {
        console.log('🎉 Connected to DeepSeek AI via WebSocket');
        setIsConnected(true);
      })
      .catch((error) => {
        console.error('Failed to connect:', error);
        setIsConnected(false);
      });

    setWsClient(client);

    // Cleanup
    return () => {
      client.disconnect();
    };
  }, []);

  const sendMessage = useCallback((content: string) => {
    if (!wsClient || !isConnected) {
      console.warn('Cannot send message: not connected');
      return;
    }

    // Add user message to UI immediately
    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setStreamingContent('');

    // Send to backend
    wsClient.sendMessage(content);
  }, [wsClient, isConnected]);

  return (
    <div className="chat-interface h-full flex flex-col">
      {/* Connection Status */}
      <div className="connection-status p-2 bg-gray-100 text-center">
        {isConnected ? (
          <span className="text-green-600">🟢 Connected to DeepSeek AI</span>
        ) : (
          <span className="text-red-600">🔴 Connecting to DeepSeek AI...</span>
        )}
      </div>

      {/* Messages Area */}
      <div className="messages flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              <div className="content whitespace-pre-wrap">{message.content}</div>
              <div className="timestamp text-xs opacity-70 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {/* Streaming Message */}
        {streamingContent && (
          <div className="message flex justify-start">
            <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-gray-200 text-gray-800">
              <div className="content whitespace-pre-wrap">{streamingContent}</div>
              <div className="typing-indicator text-xs text-blue-500 mt-1">
                ✍️ DeepSeek AI is typing...
              </div>
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && !streamingContent && (
          <div className="message flex justify-start">
            <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-gray-200 text-gray-800">
              <div className="loading-dots">💭 Thinking...</div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="chat-input p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={
              isConnected 
                ? "Ask DeepSeek AI anything..." 
                : "Connecting to DeepSeek AI..."
            }
            disabled={!isConnected || isLoading}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const input = e.currentTarget;
                if (input.value.trim()) {
                  sendMessage(input.value.trim());
                  input.value = '';
                }
              }
            }}
          />
          <button
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!isConnected || isLoading}
            onClick={() => {
              const input = document.querySelector('input') as HTMLInputElement;
              if (input && input.value.trim()) {
                sendMessage(input.value.trim());
                input.value = '';
              }
            }}
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
      </div>
    </div>
  );
};
```

## 🔑 DeepSeek API Key Setup

### 1. Set Environment Variable

Add to your `.env` file or set in your environment:

```env
# DeepSeek AI Configuration
DEEPSEEK_API_KEY=your_actual_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

### 2. Test DeepSeek Connection

Run this in your Django shell to test:

```python
python manage.py shell
```

```python
# Test DeepSeek service
import os
print("DeepSeek API Key set:", "✅ Yes" if os.getenv('DEEPSEEK_API_KEY') else "❌ No")

from apps.templates.deepseek_service import get_deepseek_service
service = get_deepseek_service()
if service:
    print("✅ DeepSeek service initialized")
    # Test a simple request
    response = service.generate("Hello, can you help me?")
    print("✅ DeepSeek response:", response[:100])
else:
    print("❌ DeepSeek service not available")
```

## 🧪 Testing the Complete Flow

### 1. Expected WebSocket Logs

When working correctly, you should see:

**Backend (Django) logs:**
```
INFO: WebSocket connection from ['127.0.0.1', 12345]
INFO: Enhanced Chat WebSocket connected: session=session_user_123, user=User123
INFO: DeepSeek service initialized successfully
INFO: Using real LangChain service
```

**Frontend (Browser) logs:**
```
🔌 Connecting to WebSocket: ws://localhost:8000/ws/chat/session_user_123/?token=...
✅ WebSocket connected successfully
🎉 Connected to DeepSeek AI via WebSocket
📤 Sending message: {"type": "chat_message", "data": {...}}
📝 Streaming token: {"token": "Hello"}
📝 Streaming token: {"token": " there!"}
✅ Stream complete
```

### 2. End-to-End Test

1. **Start Daphne**: `daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application`
2. **Open frontend**: Should see "🟢 Connected to DeepSeek AI" 
3. **Send message**: Type "Hello" and press Enter
4. **Verify response**: Should see streaming response from DeepSeek AI

## 🚀 Production Ready Checklist

- [ ] Replace Socket.IO with native WebSocket connection
- [ ] Set DEEPSEEK_API_KEY environment variable  
- [ ] Update frontend to use correct WebSocket URL format
- [ ] Implement proper message handling for streaming responses
- [ ] Test end-to-end chat flow with DeepSeek AI
- [ ] Add error handling and reconnection logic
- [ ] Verify token-by-token streaming works properly

Once you implement these changes, your chat interface will work seamlessly with DeepSeek AI through your Django backend!