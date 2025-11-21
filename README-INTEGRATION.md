# PromptCraft Integration Documentation

This document describes the complete integration of the PromptCraft application with the backend API, WebSocket functionality, and enhanced chat interface.

## 🚀 Overview

The PromptCraft application now features a fully integrated chat interface that connects to the PromptCraft API with real-time WebSocket communication, prompt optimization, template recommendations, and analytics tracking.

## 📋 Features

### ✅ Implemented Features

1. **Real-time Chat Interface**
   - WebSocket-based communication
   - Real-time message delivery
   - Typing indicators
   - Message status tracking
   - Error handling and reconnection

2. **Prompt Optimization**
   - AI-powered prompt enhancement
   - Real-time optimization suggestions
   - Scoring and improvement recommendations
   - Intent detection and analysis

3. **Template Integration**
   - Template search and discovery
   - Real-time template recommendations
   - Variable extraction and rendering
   - Category-based filtering

4. **Analytics & Gamification**
   - User interaction tracking
   - Performance metrics
   - Achievement system
   - Progress monitoring

5. **System Monitoring**
   - Connection status monitoring
   - Performance metrics dashboard
   - Error tracking and reporting
   - Health checks

## 🏗️ Architecture

### Core Components

#### 1. WebSocket Chat Service (`src/lib/services/websocket-chat.ts`)
- Manages WebSocket connections
- Handles real-time communication
- Provides message queuing and retry logic
- Supports event-driven architecture

#### 2. PromptCraft Integration Service (`src/lib/services/promptcraft-integration.ts`)
- Centralizes API interactions
- Provides caching and request management
- Handles optimization and recommendations
- Manages analytics tracking

#### 3. Enhanced Chat Interface (`src/components/EnhancedChatInterface.tsx`)
- Modern chat UI with animations
- Real-time message display
- Optimization result visualization
- Template search and selection

#### 4. Integration Dashboard (`src/app/integration/page.tsx`)
- System status monitoring
- Configuration management
- Performance metrics
- Live chat testing

## 🛠️ API Integration

### Endpoints Used

The application integrates with the following PromptCraft API endpoints:

#### Authentication
- `POST /api/v2/auth/login/` - User authentication
- `POST /api/v2/auth/refresh/` - Token refresh
- `GET /api/v2/auth/profile/` - User profile

#### Templates
- `GET /api/v2/templates/` - List templates
- `GET /api/v2/templates/{id}/` - Get template details
- `POST /api/v2/templates/` - Create template
- `GET /api/v2/templates/featured/` - Featured templates
- `GET /api/v2/templates/trending/` - Trending templates

#### Orchestrator
- `POST /api/v2/orchestrator/assess/` - Prompt assessment
- `POST /api/v2/orchestrator/render/` - Template rendering
- `GET /api/v2/orchestrator/search/` - Template search

#### Analytics
- `POST /api/v2/analytics/track/` - Event tracking
- `GET /api/v2/analytics/dashboard/` - Dashboard data

#### Gamification
- `GET /api/v2/gamification/achievements/` - User achievements
- `GET /api/v2/gamification/user-level/` - User level info

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
NEXT_PUBLIC_ENABLE_OPTIMIZATION=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

### WebSocket Configuration

```typescript
const wsConfig = {
  apiUrl: process.env.NEXT_PUBLIC_WS_URL,
  enableOptimization: true,
  enableAnalytics: true,
  maxRetries: 3,
  retryDelay: 2000,
};
```

## 📱 Usage Examples

### Basic Chat Integration

```tsx
import { EnhancedChatInterface } from '@/components/EnhancedChatInterface';

function MyApp() {
  return (
    <EnhancedChatInterface
      enableOptimization={true}
      enableTemplateSearch={true}
      enableAnalytics={true}
      onPromptOptimized={(result) => {
        console.log('Optimization result:', result);
      }}
      onTemplateSelected={(templateId) => {
        console.log('Template selected:', templateId);
      }}
    />
  );
}
```

### Using the Integration Service

```typescript
import { promptCraftIntegration } from '@/lib/services/promptcraft-integration';

// Optimize a prompt
const result = await promptCraftIntegration.optimizePrompt({
  prompt: "Write a blog post about AI",
  intent: "content_creation",
  targetAudience: "tech_professionals",
  desiredTone: "professional",
});

// Get template recommendations
const recommendations = await promptCraftIntegration.getTemplateRecommendations(
  "Write a marketing email",
  "marketing"
);

// Track user interaction
await promptCraftIntegration.trackInteraction('prompt_optimized', {
  promptLength: prompt.length,
  optimizationScore: result.score,
});
```

### WebSocket Usage

```typescript
import { useWebSocketChat } from '@/lib/services/websocket-chat';

function ChatComponent() {
  const { service, isConnected, error } = useWebSocketChat();

  useEffect(() => {
    service.on('messageResponse', (data) => {
      console.log('New message:', data);
    });

    service.on('optimizationResult', (data) => {
      console.log('Optimization complete:', data);
    });
  }, [service]);

  const sendMessage = async () => {
    await service.sendMessage('Hello, world!', {
      optimize: true,
    });
  };

  return (
    <div>
      <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
      <button onClick={sendMessage}>Send Message</button>
    </div>
  );
}
```

## 🧪 Testing

### Integration Dashboard

Visit `/integration` to access the comprehensive integration dashboard:

1. **System Status** - Monitor API, WebSocket, and service health
2. **Configuration** - Enable/disable features and adjust settings
3. **Performance Metrics** - View real-time performance data
4. **Live Chat** - Test the chat interface with all features

### Connection Testing

```bash
# Test API connectivity
npm run test:api

# Test WebSocket connection
npm run test:websocket

# Run integration tests
npm run test:integration
```

## 🔍 Monitoring & Debugging

### Health Checks

The application includes comprehensive health monitoring:

- API connectivity status
- WebSocket connection state
- Database health
- AI service availability
- Performance metrics

### Error Handling

- Automatic reconnection for WebSocket failures
- Request retry logic with exponential backoff
- Graceful degradation when services are unavailable
- Comprehensive error logging and reporting

### Performance Monitoring

- Response time tracking
- Throughput measurement
- Error rate monitoring
- User activity metrics

## 🚨 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check NEXT_PUBLIC_WS_URL configuration
   - Verify backend WebSocket server is running
   - Check firewall and proxy settings

2. **API Authentication Errors**
   - Ensure valid access tokens
   - Check token expiration and refresh logic
   - Verify API endpoint URLs

3. **Performance Issues**
   - Monitor network latency
   - Check backend service health
   - Review caching configuration

### Debug Mode

Enable debug logging:

```typescript
localStorage.setItem('promptcraft_debug', 'true');
```

## 🔐 Security Considerations

- JWT token management with automatic refresh
- Secure WebSocket connections (WSS in production)
- Input validation and sanitization
- Rate limiting and request throttling
- CORS configuration for API access

## 🚀 Deployment

### Production Configuration

```bash
# Production environment variables
NEXT_PUBLIC_API_BASE_URL=https://api.promptcraft.com
NEXT_PUBLIC_WS_URL=wss://ws.promptcraft.com
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

### Build and Deploy

```bash
# Install dependencies
npm install

# Build the application
npm run build

# Start production server
npm start
```

## 📈 Performance Optimization

- WebSocket connection pooling
- Request caching and deduplication
- Lazy loading of components
- Efficient state management
- Image and asset optimization

## 🔄 Future Enhancements

1. **Advanced AI Features**
   - Multi-model support
   - Custom model fine-tuning
   - Advanced prompt engineering

2. **Enhanced Analytics**
   - A/B testing framework
   - Conversion tracking
   - User behavior analysis

3. **Collaboration Features**
   - Real-time collaborative editing
   - Template sharing
   - Team workspaces

4. **Mobile Optimization**
   - Progressive Web App (PWA)
   - Mobile-specific UI
   - Offline functionality

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request
5. Follow code review process

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

For more information, visit the [PromptCraft Documentation](https://docs.promptcraft.com) or contact the development team.
