# 🚀 PromptCraft Frontend Integration Guide
## DeepSeek AI + Template System Integration

> **Status: ✅ LIVE WITH DEEPSEEK CREDITS**  
> Your system is now fully operational with AI-powered prompt optimization!

---

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [WebSocket Integration](#websocket-integration)
- [Message Protocol](#message-protocol)
- [Template Management](#template-management)
- [User Flow Examples](#user-flow-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## 🚀 Quick Start

### 1. Connect to Enhanced Chat WebSocket
```typescript
const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
const sessionId = generateSessionId(); // Your session ID logic
const socket = new WebSocket(`${wsUrl}/ws/chat/${sessionId}/`);
```

### 2. Authentication (Optional but Recommended)
```typescript
// Include JWT token in connection
const wsUrl = `${baseUrl}/ws/chat/${sessionId}/?token=${jwtToken}`;
// OR send in first message
socket.send(JSON.stringify({
  type: 'authenticate',
  token: jwtToken
}));
```

---

## 🔌 WebSocket Integration

### Connection Setup
```typescript
interface WebSocketManager {
  socket: WebSocket | null;
  sessionId: string;
  isConnected: boolean;
  messageQueue: any[];
}

const connectToChat = (sessionId: string, token?: string) => {
  const wsUrl = token 
    ? `ws://localhost:8000/ws/chat/${sessionId}/?token=${token}`
    : `ws://localhost:8000/ws/chat/${sessionId}/`;
    
  const socket = new WebSocket(wsUrl);
  
  socket.onopen = (event) => {
    console.log('🔌 Connected to PromptCraft Chat');
    setConnectionStatus('connected');
  };
  
  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleIncomingMessage(message);
  };
  
  socket.onclose = (event) => {
    console.log('🔌 Disconnected from chat:', event.code);
    handleReconnection();
  };
  
  return socket;
};
```

---

## 📨 Message Protocol

### Outbound Messages (Frontend → Backend)

#### 1. Chat Message
```typescript
interface ChatMessage {
  type: 'chat_message';
  content: string;
  message_id?: string;
  context?: Record<string, any>;
}

// Example
socket.send(JSON.stringify({
  type: 'chat_message',
  content: 'Help me write a professional email to my team about project updates',
  message_id: crypto.randomUUID(),
  context: {
    user_intent: 'business_communication',
    previous_templates: []
  }
}));
```

#### 2. Prompt Optimization Request
```typescript
interface OptimizePrompt {
  type: 'optimize_prompt';
  prompt: string;
  context?: Record<string, any>;
  optimization_type?: 'enhancement' | 'clarity' | 'specificity' | 'structure';
}

// Example
socket.send(JSON.stringify({
  type: 'optimize_prompt',
  prompt: 'Write marketing copy',
  context: {
    target_audience: 'B2B SaaS',
    tone: 'professional',
    length: 'medium'
  },
  optimization_type: 'specificity'
}));
```

#### 3. Save Conversation as Template
```typescript
interface SaveAsTemplate {
  type: 'save_conversation_as_template';
  title: string;
  category: string;
  include_ai_responses?: boolean;
  description?: string;
}

// Example
socket.send(JSON.stringify({
  type: 'save_conversation_as_template',
  title: 'Professional Email Template',
  category: 'Business',
  include_ai_responses: true,
  description: 'Template for team communication and project updates'
}));
```

#### 4. Create Template Directly
```typescript
interface CreateTemplate {
  type: 'create_template';
  template_data: {
    title: string;
    description: string;
    content: string;
    category: string;
    fields?: TemplateField[];
  };
}

// Example
socket.send(JSON.stringify({
  type: 'create_template',
  template_data: {
    title: 'Meeting Notes Template',
    description: 'Structured template for recording meeting outcomes',
    content: '# Meeting Notes\n\n**Date:** {{date}}\n**Attendees:** {{attendees}}\n\n## Agenda Items\n{{agenda}}\n\n## Action Items\n{{actions}}',
    category: 'Business',
    fields: [
      {
        name: 'date',
        label: 'Meeting Date',
        type: 'date',
        required: true
      },
      {
        name: 'attendees',
        label: 'Attendees',
        type: 'textarea',
        placeholder: 'List meeting attendees...',
        required: true
      }
    ]
  }
}));
```

#### 5. Get Template Suggestions
```typescript
socket.send(JSON.stringify({
  type: 'get_template_suggestions',
  context: {
    current_conversation_length: conversationHistory.length,
    user_preferences: userPreferences,
    recent_categories: ['Business', 'Writing']
  }
}));
```

---

### Inbound Messages (Backend → Frontend)

#### 1. Connection Acknowledgment
```typescript
interface ConnectionAck {
  type: 'connection_ack';
  session_id: string;
  timestamp: string;
  user_id?: string;
  authenticated: boolean;
  features: {
    template_creation: boolean;
    ai_optimization: boolean;
    langchain_fallback: boolean;
  };
}
```

#### 2. AI Chat Response
```typescript
interface ChatResponse {
  type: 'message';
  message_id: string;
  content: string;
  role: 'assistant';
  timestamp: string;
  session_id: string;
  processing_time_ms: number;
  template_suggestions?: TemplateSuggestion[];
}
```

#### 3. Template Opportunity Detected
```typescript
interface TemplateOpportunity {
  type: 'template_opportunity';
  suggestion: {
    title: string;
    description: string;
    category: string;
    confidence: number; // 0-1
    reasoning: string;
  };
  timestamp: string;
}

// Handle template opportunities
const handleTemplateOpportunity = (message: TemplateOpportunity) => {
  showTemplateCreationModal({
    suggestedTitle: message.suggestion.title,
    suggestedCategory: message.suggestion.category,
    confidence: message.suggestion.confidence,
    reasoning: message.suggestion.reasoning
  });
};
```

#### 4. Template Created Successfully
```typescript
interface TemplateCreated {
  type: 'template_created' | 'conversation_template_created';
  template: {
    id: string;
    title: string;
    description: string;
    category: string;
    fields_count?: number;
    source?: 'conversation' | 'manual_creation';
    message_count?: number;
  };
  message: string;
  timestamp: string;
}

// Handle successful template creation
const handleTemplateCreated = (message: TemplateCreated) => {
  // Add to user's template library
  addToUserLibrary(message.template);
  
  // Show success notification
  showNotification({
    type: 'success',
    title: 'Template Created!',
    message: `"${message.template.title}" has been added to your library`,
    action: {
      label: 'View Template',
      onClick: () => navigateToTemplate(message.template.id)
    }
  });
  
  // Update UI state
  setTemplateCount(prev => prev + 1);
  refreshTemplateLibrary();
};
```

#### 5. Optimization Result
```typescript
interface OptimizationResult {
  type: 'optimization_result';
  message_id: string;
  original_prompt: string;
  optimized_prompt: string;
  improvements: string[];
  suggestions: string[];
  confidence: number;
  processing_time_ms: number;
  timestamp: string;
  session_id: string;
}

// Display optimization results
const handleOptimizationResult = (message: OptimizationResult) => {
  setOptimizationResults({
    original: message.original_prompt,
    optimized: message.optimized_prompt,
    improvements: message.improvements,
    confidence: message.confidence,
    suggestions: message.suggestions
  });
  
  // Show side-by-side comparison
  showOptimizationModal(message);
};
```

#### 6. Typing Indicators
```typescript
interface TypingIndicator {
  type: 'typing_start' | 'typing_stop';
  timestamp: string;
}

// Handle typing indicators
const handleTypingIndicator = (message: TypingIndicator) => {
  if (message.type === 'typing_start') {
    setIsAITyping(true);
    showTypingAnimation();
  } else {
    setIsAITyping(false);
    hideTypingAnimation();
  }
};
```

---

## 📚 Template Management

### Template Library Integration
```typescript
interface TemplateLibrary {
  templates: Template[];
  categories: string[];
  totalCount: number;
  userTemplates: Template[];
  publicTemplates: Template[];
}

const useTemplateLibrary = () => {
  const [library, setLibrary] = useState<TemplateLibrary | null>(null);
  
  const addTemplateFromChat = (template: Template) => {
    setLibrary(prev => ({
      ...prev,
      templates: [...prev.templates, template],
      userTemplates: [...prev.userTemplates, template],
      totalCount: prev.totalCount + 1
    }));
    
    // Sync with backend
    syncTemplateLibrary();
  };
  
  const categorizeTemplate = (template: Template) => {
    // Auto-categorization based on AI analysis
    return template.category || 'General';
  };
  
  return {
    library,
    addTemplateFromChat,
    categorizeTemplate,
    searchTemplates,
    filterByCategory
  };
};
```

### Archive System
```typescript
interface ArchiveManager {
  archiveTemplate: (templateId: string, reason?: string) => Promise<void>;
  getArchivedTemplates: () => Promise<Template[]>;
  restoreTemplate: (templateId: string) => Promise<void>;
}

const useArchiveSystem = () => {
  const archiveSuccessfulPrompt = async (
    conversationId: string, 
    promptData: {
      userPrompt: string;
      aiResponse: string;
      optimization: OptimizationResult;
      userRating?: number;
    }
  ) => {
    try {
      // Archive the successful interaction
      await fetch('/api/v2/archive/prompt/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          prompt_data: promptData,
          success_metrics: {
            user_satisfaction: promptData.userRating || 0,
            optimization_confidence: promptData.optimization.confidence,
            response_quality: calculateResponseQuality(promptData.aiResponse)
          }
        })
      });
      
      console.log('✅ Prompt archived successfully');
    } catch (error) {
      console.error('❌ Failed to archive prompt:', error);
    }
  };
  
  return { archiveSuccessfulPrompt };
};
```

---

## 👤 User Flow Examples

### 1. Complete Chat-to-Template Flow
```typescript
const ChatToTemplateFlow = () => {
  const [conversation, setConversation] = useState<Message[]>([]);
  const [templateOpportunity, setTemplateOpportunity] = useState<TemplateOpportunity | null>(null);
  
  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'message':
        // Add AI response to conversation
        setConversation(prev => [...prev, {
          id: message.message_id,
          content: message.content,
          role: 'assistant',
          timestamp: message.timestamp,
          templateSuggestions: message.template_suggestions
        }]);
        
        // Check for template suggestions in the response
        if (message.template_suggestions?.length > 0) {
          showTemplateSuggestionBadge(message.template_suggestions);
        }
        break;
        
      case 'template_opportunity':
        // Show template creation opportunity
        setTemplateOpportunity(message);
        showTemplateOpportunityModal(message.suggestion);
        break;
        
      case 'template_created':
        // Handle successful template creation
        addToUserLibrary(message.template);
        showSuccessMessage(`Template "${message.template.title}" created!`);
        setTemplateOpportunity(null);
        break;
    }
  };
  
  const acceptTemplateOpportunity = () => {
    if (templateOpportunity) {
      socket.send(JSON.stringify({
        type: 'save_conversation_as_template',
        title: templateOpportunity.suggestion.title,
        category: templateOpportunity.suggestion.category,
        include_ai_responses: true
      }));
    }
  };
  
  return (
    <ChatInterface 
      conversation={conversation}
      onMessage={handleMessage}
      templateOpportunity={templateOpportunity}
      onAcceptTemplate={acceptTemplateOpportunity}
    />
  );
};
```

### 2. Real-time Prompt Optimization
```typescript
const PromptOptimizer = () => {
  const [originalPrompt, setOriginalPrompt] = useState('');
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  
  const optimizePrompt = (prompt: string, context?: any) => {
    setIsOptimizing(true);
    
    socket.send(JSON.stringify({
      type: 'optimize_prompt',
      prompt: prompt,
      context: context,
      optimization_type: 'enhancement'
    }));
  };
  
  const handleOptimizationResult = (result: OptimizationResult) => {
    setOptimizationResult(result);
    setIsOptimizing(false);
    
    // Show confidence indicator
    showConfidenceIndicator(result.confidence);
    
    // If high confidence, suggest saving as template
    if (result.confidence > 0.8) {
      suggestTemplateSave(result.optimized_prompt);
    }
  };
  
  return (
    <OptimizationInterface
      originalPrompt={originalPrompt}
      optimizationResult={optimizationResult}
      isOptimizing={isOptimizing}
      onOptimize={optimizePrompt}
    />
  );
};
```

---

## ⚠️ Error Handling

### Connection Management
```typescript
const useWebSocketWithRetry = (url: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const retryTimeoutRef = useRef<NodeJS.Timeout>();
  const retryCount = useRef(0);
  
  const connect = useCallback(() => {
    if (socket?.readyState === WebSocket.OPEN) return;
    
    setConnectionState('connecting');
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setConnectionState('connected');
      retryCount.current = 0;
      setSocket(ws);
    };
    
    ws.onclose = (event) => {
      setConnectionState('disconnected');
      
      // Auto-retry with exponential backoff
      if (retryCount.current < 5) {
        const delay = Math.pow(2, retryCount.current) * 1000;
        retryTimeoutRef.current = setTimeout(() => {
          retryCount.current++;
          connect();
        }, delay);
      } else {
        setConnectionState('error');
      }
    };
    
    ws.onerror = () => {
      setConnectionState('error');
    };
  }, [url]);
  
  return { socket, connectionState, connect };
};
```

### Error Message Handling
```typescript
const handleError = (error: any) => {
  switch (error.type) {
    case 'authentication_error':
      redirectToLogin();
      break;
      
    case 'rate_limit_exceeded':
      showRateLimitMessage(error.retry_after);
      break;
      
    case 'insufficient_credits':
      showCreditsModal();
      break;
      
    case 'template_creation_failed':
      showErrorNotification('Failed to create template. Please try again.');
      break;
      
    default:
      showGenericErrorMessage(error.message);
  }
};
```

---

## 🎯 Best Practices

### 1. Performance Optimization
```typescript
// Debounce typing for real-time optimization
const debouncedOptimize = useMemo(
  () => debounce((prompt: string) => {
    if (prompt.length > 10) {
      optimizePrompt(prompt);
    }
  }, 500),
  []
);

// Lazy load template library
const LazyTemplateLibrary = lazy(() => import('./TemplateLibrary'));

// Virtualize large template lists
const VirtualizedTemplateList = ({ templates }: { templates: Template[] }) => {
  return (
    <FixedSizeList
      height={600}
      itemCount={templates.length}
      itemSize={120}
      itemData={templates}
    >
      {TemplateItem}
    </FixedSizeList>
  );
};
```

### 2. User Experience
```typescript
// Progressive enhancement
const ChatInterface = () => {
  const [features, setFeatures] = useState({
    aiOptimization: false,
    templateCreation: false,
    realTimeAnalysis: false
  });
  
  useEffect(() => {
    // Enable features based on connection capabilities
    socket.addEventListener('message', (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'connection_ack') {
        setFeatures(message.features);
      }
    });
  }, []);
  
  return (
    <div>
      <ChatMessages />
      {features.templateCreation && <TemplateCreationTools />}
      {features.aiOptimization && <OptimizationPanel />}
    </div>
  );
};
```

### 3. Analytics & Monitoring
```typescript
// Track template creation success
const trackTemplateCreation = (template: Template, source: string) => {
  analytics.track('template_created', {
    template_id: template.id,
    title: template.title,
    category: template.category,
    source: source, // 'conversation' | 'manual'
    user_id: currentUser.id,
    session_id: sessionId
  });
};

// Monitor optimization quality
const trackOptimizationQuality = (result: OptimizationResult, userFeedback: number) => {
  analytics.track('optimization_completed', {
    confidence: result.confidence,
    user_rating: userFeedback,
    improvements_count: result.improvements.length,
    processing_time: result.processing_time_ms
  });
};
```

---

## 🚀 Getting Started Checklist

- [ ] **Set up WebSocket connection** to `ws://localhost:8000/ws/chat/{sessionId}/`
- [ ] **Implement message handlers** for all inbound message types
- [ ] **Add template creation UI** with modal/drawer for opportunities
- [ ] **Create template library view** with search and categorization
- [ ] **Implement optimization interface** with side-by-side comparison
- [ ] **Add error handling** with retry logic and user feedback
- [ ] **Set up analytics tracking** for template and optimization events
- [ ] **Test with real DeepSeek responses** to validate AI integration
- [ ] **Implement archive system** for successful prompts
- [ ] **Add user preference management** for template suggestions

---

## 🎉 System Status: READY FOR PRODUCTION

✅ **DeepSeek API**: Active with credits  
✅ **WebSocket Server**: Running on port 8000  
✅ **Template System**: Fully integrated  
✅ **Archive System**: Ready for prompt storage  
✅ **AI Optimization**: Real-time prompt enhancement  
✅ **User Library**: Personal template management  

Your PromptCraft system is now **fully operational** with intelligent AI-powered prompt optimization and automatic template creation! 🚀