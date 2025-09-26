# 🚨 WebSocket Authentication Fix
## Frontend Connection Error Resolution

**Error:** `WebSocket connection failed: WebSocket is closed before the connection is established`

**Cause:** JWT token in WebSocket URL not supported by backend routing

---

## 🔧 **Quick Fix - Remove Token from URL**

### Frontend Update (page.tsx)
```typescript
// ❌ CURRENT (BROKEN):
const wsUrl = `ws://localhost:8000/ws/chat/${sessionId}/?token=${jwtToken}`;

// ✅ FIXED VERSION:
const wsUrl = `ws://localhost:8000/ws/chat/${sessionId}/`;
```

### Complete Fixed Component
```tsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { toast } from 'react-hot-toast';

const PromptCraftChatInline = ({ userId, onTemplateCreated }) => {
  const [socket, setSocket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isAITyping, setIsAITyping] = useState(false);
  const [templateOpportunity, setTemplateOpportunity] = useState(null);
  
  // Generate session ID
  const sessionId = useMemo(() => 
    `session_user_${userId}_${Date.now()}`, [userId]
  );

  // WebSocket connection - FIXED VERSION
  useEffect(() => {
    // ✅ REMOVE TOKEN FROM URL
    const wsUrl = `ws://localhost:8000/ws/chat/${sessionId}/`;
    console.log('🔌 Connecting to:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setIsConnected(true);
      toast.success('🚀 Connected to PromptCraft AI');
      console.log('✅ WebSocket connected to PromptCraft');
      
      // ✅ SEND TOKEN AFTER CONNECTION (if needed)
      // Uncomment if you need authentication
      /*
      const token = localStorage.getItem('authToken');
      if (token) {
        ws.send(JSON.stringify({
          type: 'authenticate',
          token: token
        }));
      }
      */
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleIncomingMessage(message);
    };
    
    ws.onclose = (event) => {
      setIsConnected(false);
      console.log('🔌 WebSocket closed:', event.code, event.reason);
      
      // Don't show error for normal closure
      if (event.code !== 1000) {
        toast.error('❌ Disconnected from PromptCraft');
      }
    };
    
    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      toast.error('Connection error. Please refresh.');
    };
    
    setSocket(ws);
    
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Component unmounted');
      }
    };
  }, [sessionId]);

  // Handle incoming messages
  const handleIncomingMessage = useCallback((message) => {
    console.log('📨 Received message:', message.type);
    
    switch (message.type) {
      case 'connection_ack':
        console.log('🔌 Connection acknowledged:', message);
        break;
        
      case 'message':
        // AI response received
        setMessages(prev => [...prev, {
          id: message.message_id,
          content: message.content,
          role: 'assistant',
          timestamp: new Date(message.timestamp),
          processingTime: message.processing_time_ms,
          templateSuggestions: message.template_suggestions || []
        }]);
        setIsAITyping(false);
        
        // Show template suggestions if available
        if (message.template_suggestions?.length > 0) {
          toast.success(
            `💡 ${message.template_suggestions.length} template suggestions available!`
          );
        }
        break;
        
      case 'template_opportunity':
        // Template creation opportunity detected
        setTemplateOpportunity(message.suggestion);
        toast((t) => (
          <div className="template-opportunity-toast">
            <div>
              <strong>💡 Template Opportunity!</strong>
              <p>{message.suggestion.title}</p>
              <p>Confidence: {Math.round(message.suggestion.confidence * 100)}%</p>
            </div>
            <div>
              <button 
                onClick={() => {
                  acceptTemplateOpportunity();
                  toast.dismiss(t.id);
                }}
                className="btn-primary"
              >
                Create Template
              </button>
              <button 
                onClick={() => toast.dismiss(t.id)}
                className="btn-secondary"
              >
                Dismiss
              </button>
            </div>
          </div>
        ), {
          duration: 10000,
          position: 'top-right'
        });
        break;
        
      case 'template_created':
        // Template successfully created
        toast.success(`✅ Template "${message.template.title}" created!`);
        onTemplateCreated?.(message.template);
        setTemplateOpportunity(null);
        break;
        
      case 'optimization_result':
        // Prompt optimization completed
        setMessages(prev => prev.map(msg => 
          msg.id === message.message_id 
            ? { ...msg, optimization: message }
            : msg
        ));
        toast.success(`⚡ Prompt optimized! Confidence: ${Math.round(message.confidence * 100)}%`);
        break;
        
      case 'typing_start':
        setIsAITyping(true);
        break;
        
      case 'typing_stop':
        setIsAITyping(false);
        break;
        
      case 'error':
        toast.error(`❌ Error: ${message.message || message.error}`);
        break;
        
      default:
        console.log('🔍 Unhandled message type:', message.type);
    }
  }, [onTemplateCreated]);

  // Send message
  const sendMessage = useCallback((content, type = 'chat_message') => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      toast.error('❌ Not connected. Please refresh.');
      return;
    }
    
    const messageId = crypto.randomUUID();
    const message = {
      type,
      content,
      message_id: messageId,
      timestamp: new Date().toISOString(),
      user_id: userId // Include user ID in message
    };
    
    socket.send(JSON.stringify(message));
    
    // Add user message to UI
    if (type === 'chat_message') {
      setMessages(prev => [...prev, {
        id: messageId,
        content,
        role: 'user',
        timestamp: new Date()
      }]);
      setIsAITyping(true);
    }
    
    return messageId;
  }, [socket, userId]);

  // Accept template opportunity
  const acceptTemplateOpportunity = useCallback(() => {
    if (templateOpportunity && socket) {
      socket.send(JSON.stringify({
        type: 'save_conversation_as_template',
        title: templateOpportunity.title,
        category: templateOpportunity.category,
        include_ai_responses: true,
        description: templateOpportunity.description,
        user_id: userId
      }));
      toast.loading('🔄 Creating template...');
    }
  }, [templateOpportunity, socket, userId]);

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputMessage.trim() && isConnected) {
      sendMessage(inputMessage.trim());
      setInputMessage('');
    }
  };

  return (
    <div className="promptcraft-chat">
      {/* Connection Status */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? '🟢 Connected to PromptCraft AI' : '🔴 Connecting...'}
      </div>
      
      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>👋 Welcome to PromptCraft AI!</p>
            <p>Ask me to help you create and optimize prompts. I'll suggest templates for reusable conversations!</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-content">{message.content}</div>
            <div className="message-meta">
              {message.timestamp.toLocaleTimeString()}
              {message.processingTime && (
                <span className="processing-time">
                  ⚡ {message.processingTime}ms
                </span>
              )}
              {message.templateSuggestions?.length > 0 && (
                <span className="template-suggestions">
                  💡 {message.templateSuggestions.length} suggestions
                </span>
              )}
            </div>
          </div>
        ))}
        
        {/* AI Typing Indicator */}
        {isAITyping && (
          <div className="message assistant typing">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
            <div className="typing-text">AI is thinking...</div>
          </div>
        )}
      </div>
      
      {/* Input Form */}
      <form onSubmit={handleSubmit} className="message-input-form">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder={isConnected ? "Ask me to help optimize your prompts..." : "Connecting..."}
          disabled={!isConnected}
          className="message-input"
        />
        <button 
          type="submit" 
          disabled={!isConnected || !inputMessage.trim()}
          className="send-button"
        >
          {isConnected ? 'Send 🚀' : '⏳'}
        </button>
      </form>
      
      {/* Template Opportunity Modal */}
      {templateOpportunity && (
        <div className="template-opportunity-modal">
          <div className="modal-content">
            <h3>💡 Create Template?</h3>
            <p><strong>Title:</strong> {templateOpportunity.title}</p>
            <p><strong>Category:</strong> {templateOpportunity.category}</p>
            <p><strong>Confidence:</strong> {Math.round(templateOpportunity.confidence * 100)}%</p>
            <p><strong>Reasoning:</strong> {templateOpportunity.reasoning}</p>
            
            <div className="modal-actions">
              <button onClick={acceptTemplateOpportunity} className="btn-primary">
                ✅ Create Template
              </button>
              <button 
                onClick={() => setTemplateOpportunity(null)} 
                className="btn-secondary"
              >
                ❌ Not Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PromptCraftChatInline;
```

---

## 🧪 **Test the Fix**

### 1. Browser Console Test
```javascript
// Test without token
const testSocket = new WebSocket('ws://localhost:8000/ws/chat/test-session/');

testSocket.onopen = () => {
  console.log('✅ Connected successfully!');
  
  // Test message
  testSocket.send(JSON.stringify({
    type: 'chat_message',
    content: 'Hello PromptCraft!',
    message_id: crypto.randomUUID()
  }));
};

testSocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('📨 Received:', data);
};

testSocket.onerror = (error) => {
  console.error('❌ Error:', error);
};
```

### 2. Check Server Logs
Make sure your Daphne server is running:
```bash
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

---

## 📋 **Debugging Checklist**

- [ ] ✅ Remove `/?token=...` from WebSocket URL
- [ ] ✅ Ensure Daphne server is running on port 8000
- [ ] ✅ Check browser console for WebSocket connection status
- [ ] ✅ Verify sessionId format matches expected pattern
- [ ] ✅ Test with simple message after connection

---

## 🎯 **Why This Fixes the Issue**

1. **URL Format**: Our backend expects `ws://localhost:8000/ws/chat/{sessionId}/` **without** query parameters
2. **Token Handling**: If authentication is needed, send token **after** connection in a message
3. **Routing**: The Django Channels routing doesn't handle JWT tokens in URLs by default

After applying this fix, your WebSocket connection should work perfectly! 🚀