# 🔧 WebSocket Protocol Mismatch & DeepSeek Integration Fix

## 🚨 CRITICAL ISSUE IDENTIFIED

Your frontend is using **Socket.IO** but your Django backend uses **native WebSockets**. This is causing a protocol mismatch.

### Current Situation:
- **Frontend**: Connecting to `ws://localhost:8000/socket.io/` (Socket.IO protocol)
- **Backend**: Expects connections at `ws://localhost:8000/ws/chat/{session_id}/` (Native WebSocket)

## 🔧 Solution Options

### Option 1: Fix Frontend to Use Native WebSockets (RECOMMENDED)

Update your frontend WebSocket connection:

```typescript
// WRONG - Currently using Socket.IO:
const socket = io('ws://localhost:8000');

// CORRECT - Use native WebSocket:
const ws = new WebSocket(`ws://localhost:8000/ws/chat/${sessionId}/?token=${authToken}`);
```

### Option 2: Add Socket.IO Support to Backend (Alternative)

If you prefer Socket.IO, install django-socketio:
```bash
pip install python-socketio django-socketio
```

## 🎯 Frontend WebSocket Implementation Fix

### Step 1: Replace Socket.IO with Native WebSocket

```typescript
// Remove Socket.IO imports
// import { io } from 'socket.io-client';

// Use native WebSocket instead
export class ChatWebSocketManager {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private authToken: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(sessionId: string, authToken: string) {
    this.sessionId = sessionId;
    this.authToken = authToken;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // CORRECT WebSocket URL format for your Django backend
        const wsUrl = `ws://localhost:8000/ws/chat/${this.sessionId}/?token=${this.authToken}`;
        console.log('🔌 Connecting to:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
          console.log('✅ WebSocket connected successfully');
          this.reconnectAttempts = 0;
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Failed to parse message:', error);
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          reject(error);
        };
        
        this.ws.onclose = (event) => {
          console.log(`🔌 WebSocket closed (code: ${event.code})`);
          this.attemptReconnect();
        };
        
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'pong':
        // Heartbeat response - ignore
        console.debug('🏓 Heartbeat pong');
        break;
        
      case 'stream_token':
        // Handle streaming AI response
        this.onStreamToken?.(data);
        break;
        
      case 'stream_complete':
        // AI response finished
        this.onStreamComplete?.(data);
        break;
        
      case 'chat_message':
        // Complete message received
        this.onChatMessage?.(data);
        break;
        
      case 'error':
        // Handle errors
        this.onError?.(data);
        break;
        
      default:
        console.debug('📨 Unknown message type:', data.type);
    }
  }

  sendMessage(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
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

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = Math.pow(2, this.reconnectAttempts) * 1000;
      console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);
      
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, delay);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

### Step 2: Update Your Chat Component

```tsx
import React, { useState, useEffect, useCallback } from 'react';
import { ChatWebSocketManager } from './ChatWebSocketManager';

export const ChatInterface: React.FC = () => {
  const [wsManager, setWsManager] = useState<ChatWebSocketManager | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState<string>('');

  // Initialize WebSocket connection
  useEffect(() => {
    const sessionId = `session_user_${Date.now()}_${Math.random().toString(36)}`;
    const authToken = localStorage.getItem('auth_token') || '';
    
    const manager = new ChatWebSocketManager(sessionId, authToken);
    
    // Set up event handlers
    manager.onStreamToken = (data) => {
      console.log('📝 Streaming token:', data);
      setCurrentStreamingMessage(prev => prev + data.data.token);
    };
    
    manager.onStreamComplete = (data) => {
      console.log('✅ Stream complete:', data);
      setMessages(prev => [...prev, {
        id: data.data.message_id,
        role: 'assistant',
        content: currentStreamingMessage,
        timestamp: new Date()
      }]);
      setCurrentStreamingMessage('');
    };
    
    manager.onChatMessage = (data) => {
      console.log('💬 Chat message:', data);
      setMessages(prev => [...prev, {
        id: data.data.message_id || Date.now(),
        role: 'assistant',
        content: data.data.content,
        timestamp: new Date()
      }]);
    };
    
    manager.onError = (data) => {
      console.error('❌ Chat error:', data);
    };
    
    // Connect
    manager.connect()
      .then(() => {
        setIsConnected(true);
        console.log('🎉 Chat connection established');
      })
      .catch((error) => {
        console.error('Failed to connect:', error);
      });
    
    setWsManager(manager);
    
    // Cleanup
    return () => {
      manager.disconnect();
    };
  }, []);

  const sendMessage = useCallback((content: string) => {
    if (!wsManager || !isConnected) {
      console.warn('Cannot send message: not connected');
      return;
    }

    // Add user message to UI
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Send to backend
    wsManager.sendMessage({
      type: 'chat_message',
      data: {
        message: content,
        conversation_id: `conv_${Date.now()}`,
        // Add any additional data your backend expects
      }
    });
  }, [wsManager, isConnected]);

  return (
    <div className="chat-interface">
      <div className="connection-status">
        {isConnected ? '🟢 Connected to DeepSeek AI' : '🔴 Connecting...'}
      </div>
      
      <div className="messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="content">{message.content}</div>
            <div className="timestamp">{message.timestamp.toLocaleTimeString()}</div>
          </div>
        ))}
        
        {currentStreamingMessage && (
          <div className="message assistant streaming">
            <div className="content">{currentStreamingMessage}</div>
            <div className="typing-indicator">✍️ AI is typing...</div>
          </div>
        )}
      </div>
      
      <div className="chat-input">
        <input
          type="text"
          placeholder={isConnected ? "Type your message..." : "Connecting..."}
          disabled={!isConnected}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && e.currentTarget.value.trim()) {
              sendMessage(e.currentTarget.value.trim());
              e.currentTarget.value = '';
            }
          }}
        />
      </div>
    </div>
  );
};
```

## 🤖 DeepSeek AI Integration Verification

### Step 1: Check DeepSeek Configuration

Let's verify your DeepSeek setup in the backend:

```python
# Check if DEEPSEEK_API_KEY is set
import os
print("DeepSeek API Key:", "✅ Set" if os.getenv('DEEPSEEK_API_KEY') else "❌ Missing")
```

### Step 2: Test DeepSeek API Connection

```python
# In your Django shell or a test script
from apps.templates.langchain_services import langchain_service

# Test DeepSeek connection
try:
    response = langchain_service.generate_response("Hello, test message")
    print("✅ DeepSeek API working:", response[:100])
except Exception as e:
    print("❌ DeepSeek API error:", str(e))
```

### Step 3: Configure Environment Variables

Make sure you have these in your `.env` file:

```env
# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# LangChain Configuration  
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key_here
```

## 🧪 Testing the Complete Flow

### 1. Backend Test
```bash
# In your Django terminal, test the WebSocket consumer
python manage.py shell
```

```python
# Test the chat consumer
from apps.templates.consumers import EnhancedChatConsumer
print("✅ Chat consumer loaded successfully")

# Test LangChain service
from apps.templates.langchain_services import langchain_service
print("✅ LangChain service loaded:", langchain_service.is_available())
```

### 2. Frontend Test
```javascript
// In browser console, test the connection
const ws = new WebSocket('ws://localhost:8000/ws/chat/test_session/?token=your_token');
ws.onopen = () => console.log('✅ Connected');
ws.onmessage = (e) => console.log('📨 Message:', JSON.parse(e.data));
```

## 🎯 Expected Results

After implementing these fixes, you should see:

1. **✅ Proper WebSocket Connection**
   ```
   🔌 Connecting to: ws://localhost:8000/ws/chat/session_123/?token=...
   ✅ WebSocket connected successfully
   🎉 Chat connection established
   ```

2. **✅ DeepSeek AI Responses**
   ```
   📝 Streaming token: {"type": "stream_token", "data": {"token": "Hello"}}
   📝 Streaming token: {"type": "stream_token", "data": {"token": " there"}}
   ✅ Stream complete: {"type": "stream_complete", "data": {...}}
   ```

3. **✅ Real-time Chat Flow**
   - User types message → Sent via WebSocket
   - Backend processes with DeepSeek AI
   - Response streams back token by token
   - UI updates in real-time

## 🚀 Production Checklist

- [ ] Replace Socket.IO with native WebSocket
- [ ] Set DEEPSEEK_API_KEY environment variable
- [ ] Test WebSocket connection to correct endpoint
- [ ] Verify streaming responses work
- [ ] Test error handling and reconnection
- [ ] Confirm DeepSeek AI integration works

Your chat interface will be fully functional once you switch from Socket.IO to native WebSockets and ensure DeepSeek API key is configured!