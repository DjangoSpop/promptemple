# 🏛️ PromptTemple Frontend Setup Guide

This is the Next.js frontend for PromptTemple, a professional AI prompt management platform.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Running Django backend (see backend setup)

### 1. Clone and Install

```bash
git clone <your-repo>
cd promptcord
npm install
```

### 2. Environment Setup

Copy the environment template:
```bash
cp .env.example .env.local
```

Update `.env.local` with your configuration:
```env
# Point to your Django backend
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1

# For production
# NEXT_PUBLIC_API_BASE_URL=https://your-domain.com/api/v1
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## 🏗️ Architecture Overview

This frontend is built with:

- **Next.js 15** (App Router)
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **shadcn/ui** for components
- **Framer Motion** for animations
- **React Query** for data fetching
- **Zod** for schema validation

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (app)/             # Authenticated app layouts
│   │   ├── dashboard/     # Main dashboard
│   │   └── library/       # Template library
│   ├── (shell)/           # Shell layout (library, optimizer)
│   │   ├── library/       # Public template library
│   │   ├── optimizer/     # Prompt optimizer
│   │   └── analytics/     # Analytics dashboard
│   ├── auth/              # Authentication pages
│   │   ├── login/         # Login page
│   │   └── register/      # Registration page
│   └── api/               # API routes (NextAuth, webhooks)
├── components/            # Reusable UI components
│   ├── ui/               # shadcn/ui components
│   ├── SearchBar.tsx     # Search functionality
│   ├── TemplateCard.tsx  # Template display
│   └── ...
├── lib/                  # Utilities and configurations
│   ├── api/             # API client and types
│   ├── providers/       # React context providers
│   ├── hooks/           # Custom React hooks
│   └── utils/           # Utility functions
├── providers/           # Application providers
│   ├── AuthProvider.tsx # Authentication context
│   ├── ConfigProvider.tsx # App configuration
│   └── AnalyticsProvider.tsx # Analytics tracking
└── types/              # TypeScript type definitions
```

## 🔌 Backend Integration

### API Client Architecture

The frontend uses a professional API client (`@/lib/api/client-v2.ts`) that:

- **Authentication**: JWT token management with automatic refresh
- **Error Handling**: Comprehensive error types and retry logic
- **Type Safety**: Full TypeScript integration with Zod schemas
- **Interceptors**: Request/response transformation and logging

### Key API Endpoints

```typescript
// Authentication
POST /auth/login/          # User login
POST /auth/register/       # User registration
POST /auth/logout/         # User logout
GET  /auth/profile/        # Get user profile

// Templates
GET  /templates/           # List templates (with filters)
GET  /templates/{id}/      # Get template details
POST /templates/           # Create template
GET  /templates/featured/  # Featured templates
GET  /templates/trending/  # Trending templates

// Categories
GET  /template-categories/ # List categories

// AI Integration
POST /templates/{id}/analyze_with_ai/  # AI analysis
```

## 🎨 Component Architecture

### Template Cards

```typescript
<EnhancedTemplateCard
  template={template}
  variant="grid" // or "list"
  showAuthor={true}
  showStats={true}
  onTemplateAction={(action, id) => {
    // Handle: use, edit, delete, share, etc.
  }}
/>
```

### Search & Filtering

```typescript
<SearchBar
  onSearch={(query) => handleSearch(query)}
  placeholder="Search templates..."
/>

<CategoryChips
  categories={categories}
  selectedCategory={selectedId}
  onCategorySelect={handleFilter}
/>
```

### Authentication Flow

```typescript
const { user, login, logout, isAuthenticated } = useAuth();

// Login
await login(username, password);

// Registration
await register({
  username,
  email,
  password,
  password_confirm,
  first_name,
  last_name
});
```

## 🚢 Deployment

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm start
```

### Environment Variables

For production, set these environment variables:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com/api/v1
NEXT_PUBLIC_APP_URL=https://your-app-domain.com
NEXTAUTH_SECRET=your-production-secret
NEXTAUTH_URL=https://your-app-domain.com
```

### Vercel Deployment

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🔧 Development Workflow

### Code Quality
```bash
npm run lint        # ESLint
npm run type-check  # TypeScript
npm run format      # Prettier
npm run test        # Vitest
```

### Pre-commit Checks
```bash
npm run ci          # Full CI pipeline
```

## 🎯 Features Implemented

### ✅ Authentication System
- JWT-based authentication with Django backend
- Login/Register forms with validation
- Automatic token refresh
- Session management

### ✅ Template Management
- Browse template library with filters
- Template cards with rich metadata
- Search functionality
- Category-based filtering
- Pagination support

### ✅ Dashboard
- User statistics and gamification
- Recent activity
- Quick actions
- Template recommendations

### ✅ Prompt Optimizer
- AI-powered prompt improvement
- Multiple model support
- Before/after comparison
- Improvement suggestions
- Save optimized prompts as templates

### 🔄 In Development
- Analytics dashboard
- Template creation/editing
- Collaboration features
- Advanced AI integrations

## 🔍 Troubleshooting

### Common Issues

**1. API Connection Errors**
```bash
# Check if Django backend is running
curl http://127.0.0.1:8000/api/v1/core/health/

# Verify environment variables
echo $NEXT_PUBLIC_API_BASE_URL
```

**2. Authentication Issues**
```bash
# Clear browser localStorage
localStorage.clear()

# Check JWT tokens in Network tab
# Verify Django CORS settings
```

**3. Build Errors**
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

### Debug Mode

Enable debug logging:
```env
NEXT_PUBLIC_DEBUG=true
```

## 📞 Support

For setup assistance or bug reports:

1. Check the [backend integration guide](../my_prmpt_bakend/BACKEND_API_INTEGRATION_GUIDE.md)
2. Review API documentation in `PromptCraft API (8).yaml`
3. Check browser console for client-side errors
4. Verify Django backend logs for API errors

## 🎯 Next Steps

1. **Start Django Backend**: Follow backend setup guide
2. **Test Authentication**: Register/login flow
3. **Verify API Integration**: Check network requests
4. **Customize Branding**: Update colors, fonts, logo
5. **Deploy to Production**: Set up CI/CD pipeline

---

*Built with ❤️ for the PromptTemple ecosystem*
