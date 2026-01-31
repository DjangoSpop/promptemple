# Frontend Integration Guide - Enhanced API with DRF Spectacular

## Overview
After fixing the DRF Spectacular schema issues, the backend now provides full OpenAPI documentation and type-safe API integration for the frontend.

## Quick Start

### 1. Backend Setup
```bash
# Start the production server with WebSocket support
cd my_prmpt_bakend
.\deploy_production.ps1

# Or manually:
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

### 2. Verify API Documentation
Open your browser and visit:
- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema JSON**: http://localhost:8000/api/schema/

### 3. Test API Endpoints
```bash
# Run the test script
python test_api_schema.py
```

## Frontend Integration

### Step 1: Generate TypeScript Types (Recommended)

#### Using openapi-typescript
```bash
# Install openapi-typescript
npm install -D openapi-typescript

# Generate types
npx openapi-typescript http://localhost:8000/api/schema/ -o src/types/api.ts
```

#### Using openapi-generator
```bash
# Install globally
npm install -g @openapitools/openapi-generator-cli

# Generate TypeScript client
openapi-generator-cli generate \
  -i http://localhost:8000/api/schema/ \
  -g typescript-axios \
  -o src/api-client
```

### Step 2: Create API Client

#### Basic Fetch Client
```typescript
// src/lib/api-client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RequestConfig {
  method?: string;
  headers?: Record<string, string>;
  body?: any;
}

export class APIClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  setToken(token: string) {
    this.token = token;
  }

  private getHeaders(customHeaders?: Record<string, string>): HeadersInit {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...customHeaders,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  async request<T>(endpoint: string, config?: RequestConfig): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      method: config?.method || 'GET',
      headers: this.getHeaders(config?.headers),
      body: config?.body ? JSON.stringify(config.body) : undefined,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Convenience methods
  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  post<T>(endpoint: string, body: any): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body });
  }

  put<T>(endpoint: string, body: any): Promise<T> {
    return this.request<T>(endpoint, { method: 'PUT', body });
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new APIClient();
```

#### Axios Client (Alternative)
```typescript
// src/lib/axios-client.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for JWT token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle token refresh
          await this.refreshToken();
          return this.client(error.config);
        }
        return Promise.reject(error);
      }
    );
  }

  private async refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    if (refreshToken) {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/v2/auth/token/refresh/`, {
          refresh: refreshToken,
        });
        localStorage.setItem('accessToken', response.data.access);
      } catch (error) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    }
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}

export const apiClient = new APIClient();
```

### Step 3: Create Service Modules

#### Authentication Service
```typescript
// src/services/auth.service.ts
import { apiClient } from '@/lib/api-client';

interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    email: string;
    username: string;
  };
}

interface RegisterRequest {
  email: string;
  username: string;
  password1: string;
  password2: string;
}

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    return apiClient.post('/api/v2/auth/login/', credentials);
  },

  async register(data: RegisterRequest) {
    return apiClient.post('/api/v2/auth/registration/', data);
  },

  async logout() {
    return apiClient.post('/api/v2/auth/logout/', {});
  },

  async checkUsername(username: string) {
    return apiClient.get(`/api/v2/auth/check-username/?username=${username}`);
  },

  async checkEmail(email: string) {
    return apiClient.get(`/api/v2/auth/check-email/?email=${email}`);
  },

  async refreshToken(refreshToken: string) {
    return apiClient.post('/api/v2/auth/token/refresh/', { refresh: refreshToken });
  },
};
```

#### Template Service
```typescript
// src/services/template.service.ts
import { apiClient } from '@/lib/api-client';

export interface Template {
  id: number;
  title: string;
  description: string;
  content: string;
  category: string;
  is_premium: boolean;
  author: {
    id: number;
    username: string;
  };
  created_at: string;
  updated_at: string;
}

export const templateService = {
  async getTemplates(params?: { page?: number; search?: string; category?: string }) {
    const queryString = new URLSearchParams(params as any).toString();
    return apiClient.get<{ results: Template[]; count: number }>(`/api/v2/templates/?${queryString}`);
  },

  async getTemplate(id: number): Promise<Template> {
    return apiClient.get(`/api/v2/templates/${id}/`);
  },

  async createTemplate(data: Partial<Template>) {
    return apiClient.post('/api/v2/templates/', data);
  },

  async updateTemplate(id: number, data: Partial<Template>) {
    return apiClient.put(`/api/v2/templates/${id}/`, data);
  },

  async deleteTemplate(id: number) {
    return apiClient.delete(`/api/v2/templates/${id}/`);
  },

  async getFeatured() {
    return apiClient.get<Template[]>('/api/v2/templates/featured/');
  },

  async getTrending() {
    return apiClient.get<Template[]>('/api/v2/templates/trending/');
  },
};
```

#### AI Service
```typescript
// src/services/ai.service.ts
import { apiClient } from '@/lib/api-client';

interface OptimizeRequest {
  prompt: string;
  context?: string;
}

interface OptimizeResponse {
  optimized_prompt: string;
  suggestions: string[];
  confidence_score: number;
}

export const aiService = {
  async optimizePrompt(data: OptimizeRequest): Promise<OptimizeResponse> {
    return apiClient.post('/api/v2/ai/agent/optimize/', data);
  },

  async ragRetrieve(query: string) {
    return apiClient.post('/api/v2/ai/rag/retrieve/', { query });
  },

  async ragAnswer(question: string) {
    return apiClient.post('/api/v2/ai/rag/answer/', { question });
  },

  // SSE Streaming
  streamDeepSeek(message: string, onMessage: (data: any) => void, onError?: (error: Error) => void) {
    const token = localStorage.getItem('accessToken');
    const eventSource = new EventSource(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v2/ai/deepseek/stream/?message=${encodeURIComponent(message)}&token=${token}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse SSE data:', error);
      }
    };

    eventSource.onerror = (error) => {
      eventSource.close();
      if (onError) {
        onError(new Error('SSE connection error'));
      }
    };

    return () => eventSource.close();
  },
};
```

### Step 4: React Hooks

#### useAuth Hook
```typescript
// src/hooks/useAuth.ts
import { useState, useEffect } from 'react';
import { authService } from '@/services/auth.service';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      // Validate token and fetch user
      setLoading(false);
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authService.login({ email, password });
    localStorage.setItem('accessToken', response.access);
    localStorage.setItem('refreshToken', response.refresh);
    setUser(response.user);
    return response;
  };

  const logout = async () => {
    await authService.logout();
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setUser(null);
  };

  return { user, loading, login, logout };
}
```

#### useTemplates Hook
```typescript
// src/hooks/useTemplates.ts
import { useState, useEffect } from 'react';
import { templateService, Template } from '@/services/template.service';

export function useTemplates(initialParams?: { page?: number; search?: string }) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    async function fetchTemplates() {
      try {
        setLoading(true);
        const response = await templateService.getTemplates(initialParams);
        setTemplates(response.results);
        setTotalCount(response.count);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    }

    fetchTemplates();
  }, [initialParams?.page, initialParams?.search]);

  return { templates, loading, error, totalCount };
}
```

## Testing the Integration

### 1. Test Health Endpoints
```typescript
// Test basic connectivity
async function testConnection() {
  try {
    const health = await apiClient.get('/health/');
    console.log('✅ Server is healthy:', health);

    const config = await apiClient.get('/api/v2/core/config/');
    console.log('✅ Config loaded:', config);

    return true;
  } catch (error) {
    console.error('❌ Connection failed:', error);
    return false;
  }
}
```

### 2. Test Authentication
```typescript
async function testAuth() {
  try {
    // Check username availability
    const usernameCheck = await authService.checkUsername('testuser');
    console.log('Username check:', usernameCheck);

    // Register new user
    const user = await authService.register({
      email: 'test@example.com',
      username: 'testuser',
      password1: 'SecurePass123!',
      password2: 'SecurePass123!',
    });
    console.log('✅ User registered:', user);

    // Login
    const loginResponse = await authService.login({
      email: 'test@example.com',
      password: 'SecurePass123!',
    });
    console.log('✅ Login successful:', loginResponse);
  } catch (error) {
    console.error('❌ Auth test failed:', error);
  }
}
```

### 3. Test Templates
```typescript
async function testTemplates() {
  try {
    const templates = await templateService.getTemplates({ page: 1 });
    console.log('✅ Templates loaded:', templates);

    const featured = await templateService.getFeatured();
    console.log('✅ Featured templates:', featured);
  } catch (error) {
    console.error('❌ Template test failed:', error);
  }
}
```

## Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=PromptCraft
```

### Backend (.env)
```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOW_ALL_ORIGINS=True
DEEPSEEK_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379/0
```

## Troubleshooting

### CORS Issues
If you encounter CORS errors:
1. Verify `CORS_ALLOW_ALL_ORIGINS=True` in development
2. Check that the request origin is in `CORS_ALLOWED_ORIGINS`
3. Ensure credentials are included: `credentials: 'include'`

### Authentication Issues
1. Check token expiry
2. Verify token format: `Bearer <token>`
3. Implement token refresh logic
4. Clear localStorage on logout

### Schema Not Loading
1. Verify server is running
2. Check `/api/schema/` endpoint directly
3. Review Django logs for errors
4. Ensure drf-spectacular is installed

## Next Steps
1. Implement real-time features with WebSockets
2. Add SSE streaming for AI responses
3. Set up error tracking (Sentry)
4. Implement analytics
5. Add end-to-end tests

## Resources
- [Swagger UI](http://localhost:8000/api/schema/swagger-ui/)
- [ReDoc](http://localhost:8000/api/schema/redoc/)
- [OpenAPI Schema](http://localhost:8000/api/schema/)
- [DRF Spectacular Docs](https://drf-spectacular.readthedocs.io/)
