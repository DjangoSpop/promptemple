# API Client Documentation

This document provides a comprehensive guide to the API client layer built for the PromptCraft application. The implementation provides type-safe, feature-rich HTTP client functionality with authentication, error handling, caching, and React integration.

## Architecture Overview

The API client is built with the following structure:

```
src/lib/
├── api/                    # API service modules
│   ├── base.ts            # Base API client with auth & interceptors
│   ├── auth.ts            # Authentication services
│   ├── templates.ts       # Template CRUD operations
│   ├── categories.ts      # Category management
│   ├── analytics.ts       # Analytics & tracking
│   ├── gamification.ts    # Gamification features
│   ├── ai.ts             # AI/ML services
│   ├── orchestrator.ts    # Advanced orchestration
│   ├── billing.ts        # Billing & subscriptions
│   ├── core.ts           # Core utilities (health, config)
│   └── index.ts          # Main exports
├── hooks/                 # React Query hooks
│   ├── useAuth.ts        # Authentication hooks
│   ├── useTemplates.ts   # Template management hooks
│   ├── useCategories.ts  # Category hooks
│   ├── useAnalytics.ts   # Analytics hooks
│   ├── useGamification.ts # Gamification hooks
│   ├── useAI.ts          # AI service hooks
│   ├── useOrchestrator.ts # Orchestrator hooks
│   ├── useBilling.ts     # Billing hooks
│   ├── useCore.ts        # Core service hooks
│   └── index.ts          # Main exports
├── components/            # Reusable components
│   ├── ErrorBoundary.tsx # Error boundary wrapper
│   ├── LoadingSpinner.tsx # Loading indicators
│   ├── ErrorDisplay.tsx  # Error display components
│   └── index.ts          # Main exports
├── utils/                # Utilities
│   ├── error-handling.ts # Error handling utilities
│   └── loading-states.ts # Loading state utilities
├── providers/            # React providers
│   └── QueryProvider.tsx # React Query setup
└── examples/             # Usage examples
    └── usage-examples.tsx # Complete examples
```

## Features

### ✅ Type Safety
- Full TypeScript support using generated OpenAPI types
- Type-safe request/response handling
- Runtime type validation for critical paths

### ✅ Authentication
- Automatic JWT token management
- Token refresh with request queuing
- Authentication state events
- Persistent token storage

### ✅ Error Handling
- Comprehensive error classification (network, auth, validation, server)
- Retry logic with exponential backoff
- User-friendly error messages
- Validation error extraction

### ✅ Caching & Performance
- React Query integration for intelligent caching
- Optimistic updates for mutations
- Background refetching
- Infinite queries for pagination

### ✅ Developer Experience
- React DevTools integration
- Comprehensive testing suite
- Usage examples and documentation
- Error boundaries and loading states

## Quick Start

### 1. Setup Provider

Wrap your app with the QueryProvider:

```tsx
import { QueryProvider } from '@/lib/providers/QueryProvider';
import { ErrorBoundary } from '@/lib/components';

function App() {
  return (
    <ErrorBoundary>
      <QueryProvider>
        <YourApp />
      </QueryProvider>
    </ErrorBoundary>
  );
}
```

### 2. Authentication

```tsx
import { useAuth } from '@/lib/hooks';

function LoginForm() {
  const { 
    login, 
    isLoggingIn, 
    loginError, 
    user, 
    isAuthenticated 
  } = useAuth();

  const handleLogin = (credentials) => {
    login(credentials);
  };

  if (isAuthenticated) {
    return <div>Welcome, {user.username}!</div>;
  }

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleLogin({ username: 'user', password: 'pass' });
    }}>
      <input name="username" type="text" />
      <input name="password" type="password" />
      <button disabled={isLoggingIn}>
        {isLoggingIn ? 'Logging in...' : 'Login'}
      </button>
      {loginError && <ErrorDisplay error={loginError} />}
    </form>
  );
}
```

### 3. Data Fetching

```tsx
import { useTemplates, useTemplate } from '@/lib/hooks';
import { LoadingSpinner, ErrorDisplay } from '@/lib/components';

function TemplateList() {
  const {
    templates,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
  } = useTemplates({ 
    search: 'react', 
    category: 1 
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay error={error} />;

  return (
    <div>
      {templates.map(template => (
        <div key={template.id}>
          <h3>{template.title}</h3>
          <p>{template.description}</p>
        </div>
      ))}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()}>
          Load More
        </button>
      )}
    </div>
  );
}
```

### 4. Mutations

```tsx
import { useTemplateActions } from '@/lib/hooks';

function TemplateEditor({ templateId }) {
  const {
    updateTemplate,
    deleteTemplate,
    isUpdating,
    isDeleting,
    updateError,
  } = useTemplateActions();

  const handleUpdate = (data) => {
    updateTemplate({ id: templateId, data });
  };

  const handleDelete = () => {
    if (confirm('Delete template?')) {
      deleteTemplate(templateId);
    }
  };

  return (
    <div>
      <button 
        onClick={() => handleUpdate({ title: 'New Title' })}
        disabled={isUpdating}
      >
        {isUpdating ? 'Updating...' : 'Update'}
      </button>
      
      <button 
        onClick={handleDelete}
        disabled={isDeleting}
      >
        {isDeleting ? 'Deleting...' : 'Delete'}
      </button>
      
      <ErrorDisplay error={updateError} />
    </div>
  );
}
```

## API Services

### Authentication Service
```typescript
import { authService } from '@/lib/api';

// Login
const response = await authService.login({
  username: 'user',
  password: 'password'
});

// Register
const user = await authService.register({
  username: 'newuser',
  email: 'user@example.com',
  password: 'password',
  password_confirm: 'password'
});

// Get profile
const profile = await authService.getProfile();

// Update profile
await authService.updateProfile({
  first_name: 'John',
  bio: 'Updated bio'
});
```

### Template Service
```typescript
import { templatesService } from '@/lib/api';

// Get templates with filters
const templates = await templatesService.getTemplates({
  search: 'react',
  category: 1,
  is_featured: true
});

// Create template
const newTemplate = await templatesService.createTemplate({
  title: 'My Template',
  description: 'Template description',
  category: 1,
  template_content: 'Hello {{name}}!',
  fields_data: [
    {
      label: 'Name',
      field_type: 'text',
      is_required: true
    }
  ]
});

// Update template
await templatesService.updateTemplate(templateId, {
  title: 'Updated Title'
});
```

### AI Service
```typescript
import { aiService } from '@/lib/api';

// Generate content
const result = await aiService.generate({
  model: 'gpt-3.5-turbo',
  prompt: 'Write a haiku about coding',
  max_tokens: 100,
  temperature: 0.7
});

// Get usage statistics
const usage = await aiService.getUsage();

// Check quotas
const quotas = await aiService.getQuotas();
```

## Error Handling

### Error Types
The system recognizes and handles different error types:

- **Network Errors**: Connection issues, timeouts
- **Authentication Errors**: 401/403 status codes
- **Validation Errors**: 400/422 with field-specific errors
- **Server Errors**: 500+ status codes

### Error Components
```tsx
import { ErrorDisplay, InlineError } from '@/lib/components';

// Full error display with retry button
<ErrorDisplay 
  error={error} 
  onRetry={() => refetch()} 
  showDetails={true} 
/>

// Inline error message
<InlineError error={fieldError} />

// Error boundary for crash protection
<ErrorBoundary fallback={<CustomErrorFallback />}>
  <YourComponent />
</ErrorBoundary>
```

### Manual Error Handling
```typescript
import { 
  formatApiError, 
  isAuthError, 
  isValidationError,
  getValidationErrors 
} from '@/lib/utils/error-handling';

try {
  await apiCall();
} catch (error) {
  if (isAuthError(error)) {
    // Handle authentication error
    redirectToLogin();
  } else if (isValidationError(error)) {
    // Handle validation errors
    const fieldErrors = getValidationErrors(error);
    setFormErrors(fieldErrors);
  } else {
    // Handle other errors
    showNotification(formatApiError(error));
  }
}
```

## Advanced Usage

### Custom Hooks
Create your own hooks for specific use cases:

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { templatesService } from '@/lib/api';

export const useTemplatesByCategory = (categoryId: number) => {
  return useQuery({
    queryKey: ['templates', 'by-category', categoryId],
    queryFn: () => templatesService.getTemplates({ category: categoryId }),
    enabled: !!categoryId,
  });
};

export const useTemplateClone = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ templateId, modifications }) => {
      const original = await templatesService.getTemplate(templateId);
      return templatesService.createTemplate({
        ...original,
        ...modifications,
        title: `${original.title} (Copy)`
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
};
```

### Analytics Integration
```typescript
import { useTrackEvent } from '@/lib/hooks';

function TemplateCard({ template }) {
  const { trackEvent } = useTrackEvent();

  const handleClick = () => {
    trackEvent({
      event_type: 'template_clicked',
      data: {
        template_id: template.id,
        template_category: template.category.name,
        source: 'template_grid'
      }
    });
  };

  return <div onClick={handleClick}>{/* ... */}</div>;
}
```

### Optimistic Updates
```typescript
const updateTemplateMutation = useMutation({
  mutationFn: ({ id, data }) => templatesService.updateTemplate(id, data),
  onMutate: async ({ id, data }) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['templates', 'detail', id] });
    
    // Snapshot previous value
    const previousTemplate = queryClient.getQueryData(['templates', 'detail', id]);
    
    // Optimistically update
    queryClient.setQueryData(['templates', 'detail', id], old => ({
      ...old,
      ...data
    }));
    
    return { previousTemplate };
  },
  onError: (err, { id }, context) => {
    // Rollback on error
    queryClient.setQueryData(
      ['templates', 'detail', id], 
      context.previousTemplate
    );
  },
});
```

## Testing

The API client includes comprehensive tests:

```bash
# Run all tests
npm test

# Run specific test suites
npm test -- --grep "BaseApiClient"
npm test -- --grep "useAuth"
npm test -- --grep "ErrorHandler"

# Run with coverage
npm run test:coverage
```

### Example Test
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useAuth } from '@/lib/hooks';

test('should handle login successfully', async () => {
  const { result } = renderHook(() => useAuth(), {
    wrapper: QueryWrapper,
  });

  result.current.login({ username: 'test', password: 'pass' });

  await waitFor(() => {
    expect(result.current.isAuthenticated).toBe(true);
  });
});
```

## Configuration

### Environment Variables
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### Query Client Configuration
Customize the React Query configuration:

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000,   // 10 minutes
      retry: (failureCount, error) => {
        if (error?.status >= 400 && error?.status < 500) {
          return false; // Don't retry client errors
        }
        return failureCount < 3;
      },
    },
  },
});
```

## Best Practices

1. **Use TypeScript**: Always use the generated types for request/response data
2. **Handle Loading States**: Show loading indicators for better UX
3. **Handle Errors Gracefully**: Use ErrorDisplay components and retry mechanisms
4. **Cache Strategically**: Set appropriate staleTime and gcTime values
5. **Track User Actions**: Use analytics hooks to understand user behavior
6. **Test Your Components**: Write tests for hooks and error scenarios
7. **Optimize Updates**: Use optimistic updates for better perceived performance

## Migration Guide

If you're migrating from the old API client:

1. Replace direct API calls with hooks:
   ```tsx
   // Old
   const [data, setData] = useState(null);
   useEffect(() => {
     apiClient.getTemplates().then(setData);
   }, []);

   // New
   const { templates, isLoading, error } = useTemplates();
   ```

2. Update error handling:
   ```tsx
   // Old
   try {
     await apiCall();
   } catch (error) {
     alert(error.message);
   }

   // New
   <ErrorDisplay error={error} onRetry={() => refetch()} />
   ```

3. Use the new service modules:
   ```tsx
   // Old
   import { apiClient } from '@/lib/api-client';

   // New
   import { templatesService } from '@/lib/api';
   ```

## Contributing

When adding new API endpoints:

1. Add types to the generated API types (or update OpenAPI schema)
2. Create/update the appropriate service module
3. Create React hooks if needed
4. Add tests for the new functionality
5. Update this documentation

For questions or issues, please refer to the GitHub issues or contact the development team.