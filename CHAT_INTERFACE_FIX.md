# 🔧 Chat Interface Integration Fix

## Critical Issues Identified

Based on your console logs, here are the issues preventing your chat interface from working properly:

### 1. ✅ FIXED - Missing AI Suggestions Endpoint
**Problem**: Frontend calling `/api/v2/ai/suggestions` but getting 404
**Solution**: Added the endpoint to `apps/ai_services/views.py` and `urls.py`

### 2. 🔧 WebSocket Message Handling Issues

**Problem**: Frontend receiving 'pong' messages but doesn't know how to handle them
```javascript
// Current error in page.tsx:229
Unknown message type: pong Object
```

**Solution**: Update your frontend WebSocket message handler to handle system messages:

```typescript
// In your WebSocket message handler (likely in page.tsx or useWebSocketConnection.ts)
const handleWebSocketMessage = (event: MessageEvent) => {
  try {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
      case 'chat_message':
        // Handle actual chat messages
        handleChatMessage(data);
        break;
        
      case 'stream_token':
        // Handle streaming tokens
        handleStreamToken(data);
        break;
        
      case 'stream_complete':
        // Handle stream completion
        handleStreamComplete(data);
        break;
        
      case 'pong':
        // Handle heartbeat pong - just log and ignore
        console.log('🏓 Received heartbeat pong');
        break;
        
      case 'error':
        // Handle errors
        handleError(data);
        break;
        
      default:
        // Don't log unknown types as errors, just debug info
        console.debug('📨 Received system message:', data.type, data);
    }
  } catch (error) {
    console.error('Failed to parse WebSocket message:', error);
  }
};
```

### 3. 🔧 SVG ViewBox Errors

**Problem**: SVG elements have invalid viewBox attributes
```
Error: <svg> attribute viewBox: Expected number, "0 0 100% 1"
```

**Solution**: Fix SVG viewBox values in your UI components:

```jsx
// Instead of:
<svg viewBox="0 0 100% 1">

// Use proper numeric values:
<svg viewBox="0 0 100 1">
// or
<svg viewBox="0 0 24 24"> // For icons
```

### 4. 🔧 AutoCorrection Cache Errors

**Problem**: React state management issues with undefined cache
```
TypeError: Cannot read properties of undefined (reading 'autoCorrectionCache')
```

**Solution**: Initialize state properly in your React components:

```typescript
// In your chat component state initialization
const [initializationProgress, setInitializationProgress] = useState({
  autoCorrectionCache: {},
  loadingStates: {},
  // ... other initial state
});

// Or use a reducer pattern for complex state
const initialState = {
  autoCorrectionCache: new Map(),
  messages: [],
  isConnected: false,
  // ... other state
};
```

## 🚀 Complete Frontend Integration Fix

### Step 1: Update WebSocket Connection Hook

Create or update `useWebSocketConnection.ts`:

```typescript
import { useCallback, useEffect, useRef, useState } from 'react';

export interface WebSocketMessage {
  type: 'chat_message' | 'stream_token' | 'stream_complete' | 'error' | 'pong' | 'status';
  data?: any;
  timestamp?: string;
}

export const useWebSocketConnection = (sessionId: string, token: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      const wsUrl = `ws://localhost:8000/ws/chat/${sessionId}/?token=${token}`;
      console.log('🔌 Attempting WebSocket connection to:', wsUrl);
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          // Handle different message types
          switch (message.type) {
            case 'pong':
              // Heartbeat response - just acknowledge
              console.debug('🏓 Heartbeat pong received');
              break;
              
            case 'chat_message':
            case 'stream_token':
            case 'stream_complete':
              // Forward to message handler
              onMessage?.(message);
              break;
              
            case 'error':
              console.error('❌ WebSocket error message:', message);
              setError(message.data?.message || 'Unknown error');
              break;
              
            default:
              console.debug('📨 System message:', message.type);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setError('Connection error');
      };
      
      wsRef.current.onclose = (event) => {
        console.log(`🔌 WebSocket disconnected (code: ${event.code}, reason: ${event.reason})`);
        setIsConnected(false);
        
        // Auto-reconnect logic
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.pow(2, reconnectAttempts.current) * 1000; // Exponential backoff
          console.log(`🔄 Scheduling reconnection attempt ${reconnectAttempts.current + 1} in ${delay}ms`);
          
          setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        } else {
          setError('Connection failed after multiple attempts');
        }
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setError('Failed to connect');
    }
  }, [sessionId, token]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }, [isConnected]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    error,
    connect,
    disconnect,
    sendMessage
  };
};
```

### Step 2: Fix Chat Component State Management

Update your main chat component:

```tsx
import React, { useState, useCallback, useEffect } from 'react';
import { useWebSocketConnection } from './hooks/useWebSocketConnection';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatState {
  messages: ChatMessage[];
  currentStreamingId: string | null;
  isTyping: boolean;
  autoCorrectionCache: Map<string, string>;
  initializationProgress: {
    websocket: boolean;
    auth: boolean;
    templates: boolean;
  };
}

export const ChatInterface: React.FC = () => {
  // Initialize state properly to prevent undefined errors
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    currentStreamingId: null,
    isTyping: false,
    autoCorrectionCache: new Map(),
    initializationProgress: {
      websocket: false,
      auth: false,
      templates: false
    }
  });

  const [sessionId] = useState(() => `session_user_${Math.random().toString(36)}_${Date.now()}`);
  const [authToken] = useState(() => localStorage.getItem('auth_token') || '');

  const { isConnected, error, sendMessage } = useWebSocketConnection(
    sessionId, 
    authToken
  );

  // Update initialization progress
  useEffect(() => {
    setChatState(prev => ({
      ...prev,
      initializationProgress: {
        ...prev.initializationProgress,
        websocket: isConnected
      }
    }));
  }, [isConnected]);

  const handleSendMessage = useCallback((content: string) => {
    const message: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date()
    };

    // Add user message to state
    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, message],
      isTyping: true
    }));

    // Send via WebSocket
    sendMessage({
      type: 'chat_message',
      data: {
        conversation_id: sessionId,
        message: content,
        user_id: 'current_user' // Replace with actual user ID
      }
    });
  }, [sessionId, sendMessage]);

  const handleWebSocketMessage = useCallback((wsMessage: any) => {
    switch (wsMessage.type) {
      case 'stream_token':
        // Handle streaming response
        const { token, message_id } = wsMessage.data;
        
        setChatState(prev => {
          const messages = [...prev.messages];
          let assistantMessage = messages.find(m => m.id === message_id);
          
          if (!assistantMessage) {
            // Create new assistant message
            assistantMessage = {
              id: message_id,
              role: 'assistant',
              content: token,
              timestamp: new Date(),
              isStreaming: true
            };
            messages.push(assistantMessage);
          } else {
            // Append token to existing message
            assistantMessage.content += token;
          }
          
          return {
            ...prev,
            messages,
            currentStreamingId: message_id,
            isTyping: true
          };
        });
        break;

      case 'stream_complete':
        // Stream finished
        setChatState(prev => ({
          ...prev,
          currentStreamingId: null,
          isTyping: false,
          messages: prev.messages.map(m => 
            m.id === wsMessage.data.message_id 
              ? { ...m, isStreaming: false }
              : m
          )
        }));
        break;

      case 'chat_message':
        // Complete message received
        const assistantMessage: ChatMessage = {
          id: wsMessage.data.message_id || `assistant_${Date.now()}`,
          role: 'assistant',
          content: wsMessage.data.content,
          timestamp: new Date()
        };

        setChatState(prev => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
          isTyping: false
        }));
        break;
    }
  }, []);

  // Rest of your component logic...
  
  return (
    <div className="chat-interface">
      {/* Your chat UI components */}
      <div className="connection-status">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        {error && <span className="error">Error: {error}</span>}
      </div>
      
      {/* Messages display */}
      <div className="messages">
        {chatState.messages.map(message => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="content">{message.content}</div>
            {message.isStreaming && <div className="streaming-indicator">✍️</div>}
          </div>
        ))}
      </div>
      
      {/* Chat input */}
      <div className="chat-input">
        <input 
          type="text" 
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleSendMessage(e.currentTarget.value);
              e.currentTarget.value = '';
            }
          }}
          disabled={!isConnected}
          placeholder={isConnected ? "Type your message..." : "Connecting..."}
        />
      </div>
    </div>
  );
};
```

### Step 3: Fix SVG Components

Search for and fix any SVG elements in your components:

```bash
# Search for problematic SVG viewBox attributes
grep -r "viewBox.*%" src/
```

Replace any percentage-based viewBox values with proper numeric values:

```jsx
// Bad:
<svg viewBox="0 0 100% 1">

// Good:
<svg viewBox="0 0 100 1">
```

## 🧪 Testing the Fix

1. **Restart your Django server** to pick up the new suggestions endpoint
2. **Reload your frontend** to get the updated WebSocket handling
3. **Test the flow**:
   - Open browser console
   - Try typing in the chat input
   - Check if suggestions appear (should no longer get 404)
   - Send a test message
   - Verify WebSocket connection stays stable

## 🔍 Debugging Tips

Add these debug statements to monitor the flow:

```typescript
// In your main chat component
useEffect(() => {
  console.log('🔍 Chat State:', {
    messagesCount: chatState.messages.length,
    isTyping: chatState.isTyping,
    connected: isConnected,
    streamingId: chatState.currentStreamingId
  });
}, [chatState, isConnected]);
```

## 📈 Expected Results

After implementing these fixes:

✅ No more 404 errors for `/api/v2/ai/suggestions`  
✅ No more "Unknown message type: pong" errors  
✅ No more SVG viewBox errors  
✅ No more autoCorrectionCache undefined errors  
✅ Stable WebSocket connection with auto-reconnect  
✅ Proper message streaming and display  

Your chat interface should now work smoothly with your LangChain backend!