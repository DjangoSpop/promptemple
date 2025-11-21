# 🚀 PromptCraft Enhanced WebSocket Chat Integration

## Overview

This enhanced chat system integrates real-time WebSocket communication with billing management and automatic template creation. The system provides a seamless user experience with credit tracking, AI-powered conversations, and intelligent template suggestions.

## ✨ Features

### 🔄 Real-time WebSocket Chat
- **Live Connection**: WebSocket-powered real-time communication with Django backend
- **Auto-reconnection**: Intelligent reconnection with exponential backoff
- **Connection Status**: Real-time connection monitoring with visual indicators
- **Message Queuing**: Messages queued during disconnections and sent when reconnected

### 💳 Integrated Billing System
- **Credit Tracking**: Real-time credit consumption and balance updates
- **Plan Management**: Support for multiple subscription tiers
- **Usage Limits**: Enforce chat limits, template creation limits, and feature access
- **Billing Portal**: Direct integration with Stripe customer portal

### 🤖 AI-Powered Features
- **Template Detection**: Automatic detection of template opportunities during conversations
- **DeepSeek Integration**: Advanced AI model integration with proper credit attribution
- **Smart Suggestions**: Context-aware template suggestions and improvements
- **Conversation Analysis**: Real-time analysis for template creation potential

### 📝 Template Management
- **Auto-Template Creation**: Convert conversations to reusable templates
- **Template Opportunities**: AI-powered detection of templateable conversations
- **Variable Extraction**: Automatic identification of template variables
- **Template Library**: Integration with existing template management system

## 🏗️ Architecture

### Frontend Components

```
src/
├── components/
│   ├── EnhancedWebSocketChat.tsx       # Main chat interface
│   ├── IntegratedChatDashboard.tsx     # Complete dashboard with billing
│   └── CreditsWidget.tsx               # Enhanced credits display
├── lib/
│   └── services/
│       ├── billing.ts                  # Billing service integration
│       └── websocket-chat.ts           # Enhanced WebSocket service
└── app/
    ├── chat/
    │   ├── live/page.tsx               # Live chat interface
    │   └── test/page.tsx               # Chat testing page
    ├── status/page.tsx                 # System status dashboard
    └── api/
        └── test/route.ts               # Backend integration testing
```

### Backend Integration

The system integrates with Django backend endpoints:

#### WebSocket Endpoints
- `ws://localhost:8000/ws/chat/{session_id}/` - Real-time chat communication
- **Message Types**:
  - `chat_message` - Send/receive chat messages
  - `template_opportunity` - Template creation suggestions
  - `credit_update` - Real-time credit balance updates
  - `save_conversation_as_template` - Convert chat to template

#### Billing API Endpoints
- `/api/v2/billing/plans/` - Available subscription plans
- `/api/v2/billing/me/subscription/` - User's current subscription
- `/api/v2/billing/me/entitlements/` - User's plan entitlements
- `/api/v2/billing/me/usage/` - Current usage statistics
- `/api/v2/billing/checkout/` - Create Stripe checkout session
- `/api/v2/billing/portal/` - Access billing portal

## 🚀 Getting Started

### 1. Environment Setup

Create `.env.local` with the following variables:

```bash
# Backend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Authentication
NEXT_PUBLIC_JWT_SECRET=your-jwt-secret

# Billing (if using Stripe)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

### 2. Install Dependencies

```bash
npm install
# or
yarn install
```

### 3. Start Development Server

```bash
npm run dev
# or
yarn dev
```

### 4. Access the Enhanced Chat

- **Live Chat Dashboard**: http://localhost:3001/chat/live
- **System Status**: http://localhost:3001/status
- **Simple Chat Test**: http://localhost:3001/chat/test

## 🎯 Usage Guide

### Starting a Chat Session

1. **Authentication**: User must be logged in to access chat features
2. **Credit Check**: System verifies sufficient credits before allowing chat
3. **WebSocket Connection**: Automatic connection to real-time chat service
4. **Message Exchange**: Real-time message exchange with AI assistant

### Credit Management

```typescript
// Check if user can perform action
const canChat = await billingService.canPerformAction('chat_message', 1);

// Consume credits for action
await billingService.consumeCredits('chat_message', 1);

// Get current entitlements
const entitlements = await billingService.getEntitlements();
```

### WebSocket Integration

```typescript
// Initialize WebSocket service
const { service, isConnected, error } = useWebSocketChat();

// Send message with billing check
await service.sendMessage("Hello AI assistant!");

// Listen for template opportunities
service.on('templateOpportunity', (opportunity) => {
  // Show template creation UI
});

// Handle credit updates
service.on('creditUpdate', (data) => {
  // Update credit display
});
```

### Template Creation

```typescript
// Save conversation as template
await service.saveConversationAsTemplate(
  "Meeting Notes Template",
  "Generate structured meeting notes",
  messages
);

// Analyze conversation for template potential
await service.analyzeForTemplate(messages);
```

## 🔧 Configuration

### WebSocket Service Configuration

```typescript
const service = new WebSocketChatService({
  apiUrl: 'http://localhost:8000',
  enableOptimization: true,
  enableAnalytics: true,
  maxRetries: 5,
  retryDelay: 3000
});
```

### Billing Service Configuration

The billing service automatically handles:
- Credit tracking and consumption
- Plan limitation enforcement
- Subscription status monitoring
- Usage analytics

## 🔍 Testing & Monitoring

### System Status Dashboard

Access the comprehensive status dashboard at `/status` to monitor:
- Backend API connectivity
- WebSocket connection status
- Billing system integration
- Real-time system health

### Testing Endpoints

```bash
# Test system health
GET /api/test

# Test billing integration
POST /api/test
Body: { "action": "test_billing" }

# Test WebSocket connectivity
POST /api/test
Body: { "action": "test_websocket" }
```

### Health Checks

The system provides multiple health check endpoints:
- Frontend: Real-time connection status in UI
- Backend: `/health/` endpoint for Django backend
- WebSocket: Connection status monitoring with auto-reconnection

## 🎨 UI Components

### Enhanced Chat Interface Features

- **Real-time Status Indicators**: Connection, credit balance, typing indicators
- **Smart Notifications**: Template opportunities, credit warnings, billing alerts
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode Support**: Automatic theme detection and switching
- **Accessibility**: Full keyboard navigation and screen reader support

### Credit Widget Features

- **Real-time Updates**: Live credit balance and usage tracking
- **Usage Visualization**: Progress bars and usage statistics
- **Quick Actions**: Upgrade buttons and billing portal access
- **Plan Information**: Current subscription details and limits

## 🔒 Security Features

### Authentication & Authorization
- JWT token-based authentication
- Automatic token refresh
- Secure WebSocket connections with auth headers
- Plan-based feature access control

### Billing Security
- Secure credit consumption tracking
- Plan limitation enforcement
- Stripe integration for payment processing
- Subscription status validation

## 🚀 Production Deployment

### Environment Variables for Production

```bash
# Production Backend
NEXT_PUBLIC_API_URL=https://api.promptcraft.com
NEXT_PUBLIC_WS_URL=wss://api.promptcraft.com

# Production Authentication
NEXT_PUBLIC_JWT_SECRET=your-production-jwt-secret

# Production Billing
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
```

### Performance Optimizations

- **Connection Pooling**: Efficient WebSocket connection management
- **Message Queuing**: Optimal message delivery during network issues
- **Credit Caching**: Local credit tracking with server synchronization
- **Component Lazy Loading**: Optimized bundle sizes

## 📊 Analytics & Monitoring

### Built-in Analytics
- Chat message frequency and patterns
- Template creation success rates
- Credit consumption analytics
- User engagement metrics

### Error Monitoring
- WebSocket connection errors
- Billing integration failures
- Template creation errors
- Performance bottlenecks

## 🛠️ Development Guide

### Adding New Features

1. **Billing Integration**: Extend `billingService` with new API endpoints
2. **WebSocket Events**: Add new message types to WebSocket service
3. **UI Components**: Create reusable components following existing patterns
4. **Testing**: Add tests to `/api/test` route for new integrations

### Best Practices

- Always check billing permissions before actions
- Handle WebSocket disconnections gracefully
- Provide clear user feedback for all states
- Implement proper error boundaries
- Use TypeScript for type safety

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/enhanced-chat`
3. Make your changes and test thoroughly
4. Submit a pull request with detailed description

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🎉 Success! Your Enhanced Chat System is Live!

The PromptCraft Enhanced WebSocket Chat system is now fully operational with:

✅ **Real-time WebSocket Communication**  
✅ **Integrated Billing & Credit Management**  
✅ **AI-Powered Template Detection**  
✅ **DeepSeek Integration with Proper Attribution**  
✅ **Comprehensive Status Monitoring**  
✅ **Production-Ready Architecture**

Visit http://localhost:3001/chat/live to experience the enhanced chat system in action!
