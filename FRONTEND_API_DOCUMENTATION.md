# PromptCraft Backend API Documentation for Frontend Developers

**API Version**: 2.0.0
**Base URL**: `http://localhost:8000` (Development) / `https://your-domain.com` (Production)
**Last Updated**: January 2026

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [API Endpoints](#api-endpoints)
   - [Authentication & User Management](#authentication--user-management)
   - [Chat & AI Services](#chat--ai-services)
   - [Template Management](#template-management)
   - [Gamification](#gamification)
   - [Analytics](#analytics)
   - [Billing](#billing)
   - [Health & Monitoring](#health--monitoring)
5. [Data Models & TypeScript Types](#data-models--typescript-types)
6. [SSE Streaming Guide](#sse-streaming-guide)
7. [WebSocket Guide](#websocket-guide)
8. [Error Handling](#error-handling)
9. [Common Workflows](#common-workflows)
10. [Rate Limiting & Pagination](#rate-limiting--pagination)

---

## Quick Start

### Base URL
```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### Authentication Flow
```typescript
// 1. Register
const registerResponse = await fetch(`${API_BASE_URL}/api/v2/auth/register/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'johndoe',
    email: 'john@example.com',
    password: 'SecurePass123!',
    password_confirm: 'SecurePass123!'
  })
});

// 2. Login
const loginResponse = await fetch(`${API_BASE_URL}/api/v2/auth/login/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'johndoe',
    password: 'SecurePass123!'
  })
});

const { access, refresh, user } = await loginResponse.json();

// 3. Store tokens
localStorage.setItem('access_token', access);
localStorage.setItem('refresh_token', refresh);
localStorage.setItem('user', JSON.stringify(user));

// 4. Use in subsequent requests
const profileResponse = await fetch(`${API_BASE_URL}/api/v2/auth/profile/`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
  }
});
```

---

## Authentication

### Overview
PromptCraft uses **JWT (JSON Web Token)** authentication with access and refresh tokens.

### Token Lifecycle
- **Access Token**: Short-lived (15 minutes), used for API requests
- **Refresh Token**: Long-lived (7 days), used to obtain new access tokens

### Authentication Header
All protected endpoints require:
```http
Authorization: Bearer {access_token}
```

### Token Refresh
When access token expires (401 error with code `token_not_valid`):
```typescript
const refreshToken = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v2/auth/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      refresh: localStorage.getItem('refresh_token')
    })
  });

  const { access } = await response.json();
  localStorage.setItem('access_token', access);
  return access;
};
```

---

## Core Concepts

### UUID Format
All IDs use UUID v4 format:
```typescript
type UUID = string; // e.g., "550e8400-e29b-41d4-a716-446655440000"
```

### Timestamps
All timestamps are in ISO 8601 format (UTC):
```typescript
type Timestamp = string; // e.g., "2026-01-20T14:30:00.000Z"
```

### Pagination
List endpoints use cursor-based pagination:
```typescript
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

---

## API Endpoints

### Authentication & User Management

#### POST `/api/v2/auth/register/`
**Register a new user**

**Authentication**: None (public)

**Request Body**:
```typescript
interface RegisterRequest {
  username: string;           // 3-50 chars, alphanumeric + _ -
  email: string;              // Valid email format
  password: string;           // Min 8 chars
  password_confirm: string;   // Must match password
  first_name?: string;        // Optional
  last_name?: string;         // Optional
  bio?: string;              // Optional, max 500 chars
  theme_preference?: 'light' | 'dark' | 'system'; // Optional
  language_preference?: string; // Optional, default 'en'
}
```

**Response** (201 Created):
```typescript
interface RegisterResponse {
  user: {
    id: UUID;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    bio: string;
    avatar_url: string | null;
    theme_preference: 'light' | 'dark' | 'system';
    language_preference: string;
    created_at: Timestamp;
  };
  tokens: {
    access: string;  // JWT access token
    refresh: string; // JWT refresh token
  };
}
```

**Error Responses**:
- `400 Bad Request`: Validation errors
  ```typescript
  {
    "username": ["Username already exists"],
    "email": ["A user with this email already exists"],
    "password": ["Password must contain at least one uppercase letter"]
  }
  ```

**Example**:
```typescript
const response = await fetch('/api/v2/auth/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'johndoe',
    email: 'john@example.com',
    password: 'SecurePass123!',
    password_confirm: 'SecurePass123!',
    first_name: 'John',
    last_name: 'Doe'
  })
});

if (response.ok) {
  const data = await response.json();
  localStorage.setItem('access_token', data.tokens.access);
  localStorage.setItem('refresh_token', data.tokens.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));
}
```

---

#### POST `/api/v2/auth/login/`
**Login with username/email and password**

**Authentication**: None (public)

**Request Body**:
```typescript
interface LoginRequest {
  username: string;  // Username OR email address
  password: string;
}
```

**Response** (200 OK):
```typescript
interface LoginResponse {
  access: string;   // JWT access token
  refresh: string;  // JWT refresh token
  user: {
    id: UUID;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    avatar_url: string | null;
    level: number;
    experience_points: number;
    credits: number;
    user_rank: string;
    is_premium: boolean;
    premium_expires_at: Timestamp | null;
    theme_preference: 'light' | 'dark' | 'system';
    daily_streak: number;
    templates_created: number;
    templates_completed: number;
    total_prompts_generated: number;
  };
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials
  ```typescript
  {
    "detail": "Invalid credentials. Please check your username/email and password."
  }
  ```
- `400 Bad Request`: Missing fields

**Example**:
```typescript
const response = await fetch('/api/v2/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'johndoe',  // or 'john@example.com'
    password: 'SecurePass123!'
  })
});

const data = await response.json();
```

---

#### POST `/api/v2/auth/refresh/`
**Refresh access token**

**Authentication**: None (requires refresh token)

**Request Body**:
```typescript
interface RefreshRequest {
  refresh: string;  // JWT refresh token
}
```

**Response** (200 OK):
```typescript
interface RefreshResponse {
  access: string;  // New JWT access token
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired refresh token
  ```typescript
  {
    "detail": "Token is invalid or expired",
    "code": "token_not_valid"
  }
  ```

---

#### GET `/api/v2/auth/profile/`
**Get current user profile**

**Authentication**: Required (JWT)

**Headers**:
```http
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```typescript
interface UserProfile {
  id: UUID;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  bio: string;
  avatar_url: string | null;
  social_avatar_url: string | null;

  // Gamification
  credits: number;
  level: number;
  experience_points: number;
  next_level_xp: number;
  daily_streak: number;
  user_rank: string;
  rank_info: {
    name: string;
    min_level: number;
    max_level: number;
    benefits: string[];
  };

  // Premium
  is_premium: boolean;
  premium_expires_at: Timestamp | null;

  // Preferences
  theme_preference: 'light' | 'dark' | 'system';
  language_preference: string;
  ai_assistance_enabled: boolean;
  analytics_enabled: boolean;

  // Statistics
  templates_created: number;
  templates_completed: number;
  total_prompts_generated: number;
  completion_rate: number;  // Percentage (0-100)

  // Dates
  last_login_date: string;  // YYYY-MM-DD
  date_joined: Timestamp;
  last_login: Timestamp;
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid token

**Example**:
```typescript
const getProfile = async () => {
  const response = await fetch('/api/v2/auth/profile/', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });

  if (response.ok) {
    const profile = await response.json();
    return profile;
  }
};
```

---

#### PUT/PATCH `/api/v2/auth/profile/update/`
**Update user profile**

**Authentication**: Required (JWT)

**Request Body** (all fields optional):
```typescript
interface ProfileUpdateRequest {
  first_name?: string;
  last_name?: string;
  bio?: string;
  avatar?: File;  // Use FormData for file upload
  theme_preference?: 'light' | 'dark' | 'system';
  language_preference?: string;
  ai_assistance_enabled?: boolean;
  analytics_enabled?: boolean;
}
```

**Response** (200 OK): Same as GET `/api/v2/auth/profile/`

**Example with FormData**:
```typescript
const updateProfile = async (updates: ProfileUpdateRequest) => {
  const formData = new FormData();

  Object.keys(updates).forEach(key => {
    if (updates[key] !== undefined) {
      formData.append(key, updates[key]);
    }
  });

  const response = await fetch('/api/v2/auth/profile/update/', {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      // Don't set Content-Type for FormData
    },
    body: formData
  });

  return await response.json();
};
```

---

#### POST `/api/v2/auth/change-password/`
**Change user password**

**Authentication**: Required (JWT)

**Request Body**:
```typescript
interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}
```

**Response** (200 OK):
```typescript
{
  "detail": "Password updated successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Validation errors
  ```typescript
  {
    "old_password": ["Incorrect password"],
    "new_password": ["Password must be at least 8 characters"]
  }
  ```

---

#### POST `/api/v2/auth/logout/`
**Logout (optional - mainly clears server-side session)**

**Authentication**: Required (JWT)

**Request Body**:
```typescript
interface LogoutRequest {
  refresh?: string;  // Optional: refresh token to blacklist
}
```

**Response** (200 OK):
```typescript
{
  "detail": "Successfully logged out"
}
```

**Note**: For JWT, logout is mainly client-side (clear tokens from localStorage)

---

#### GET `/api/v2/auth/check-username/?username={username}`
**Check if username is available**

**Authentication**: None (public)

**Query Parameters**:
- `username`: Username to check

**Response** (200 OK):
```typescript
{
  "available": boolean,
  "username": string
}
```

---

#### GET `/api/v2/auth/check-email/?email={email}`
**Check if email is available**

**Authentication**: None (public)

**Query Parameters**:
- `email`: Email to check

**Response** (200 OK):
```typescript
{
  "available": boolean,
  "email": string
}
```

---

#### GET `/api/v2/auth/stats/`
**Get user statistics**

**Authentication**: Required (JWT)

**Response** (200 OK):
```typescript
interface UserStats {
  templates_created: number;
  templates_completed: number;
  total_prompts_generated: number;
  daily_streak: number;
  credits: number;
  level: number;
  experience_points: number;
  completion_rate: number;
  favorite_categories: Array<{
    category: string;
    count: number;
  }>;
  recent_activity: Array<{
    action: string;
    timestamp: Timestamp;
    details: object;
  }>;
}
```

---

### Chat & AI Services

#### POST `/api/v2/chat/completions/`
**SSE Streaming Chat Completions (RECOMMENDED)**

**Authentication**: Required (JWT)

**Headers**:
```http
Authorization: Bearer {access_token}
Content-Type: application/json
Accept: text/event-stream
```

**Request Body**:
```typescript
interface ChatCompletionRequest {
  messages: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
  model?: string;           // Default: 'deepseek-chat'
  stream?: boolean;         // Default: true
  temperature?: number;     // 0.0-1.0, default: 0.7
  max_tokens?: number;      // Default: 2048
  top_p?: number;          // 0.0-1.0, default: 1.0
  frequency_penalty?: number; // -2.0-2.0, default: 0.0
  presence_penalty?: number;  // -2.0-2.0, default: 0.0
}
```

**Response** (SSE Stream):
The response is a stream of Server-Sent Events:

```
data: {"type":"stream_start","message_id":"550e8400-e29b-41d4-a716-446655440000","timestamp":"2026-01-20T14:30:00.000Z"}

data: {"type":"stream_token","message_id":"550e8400-e29b-41d4-a716-446655440000","token":"Hello"}

data: {"type":"stream_token","message_id":"550e8400-e29b-41d4-a716-446655440000","token":" world"}

data: {"type":"stream_complete","message_id":"550e8400-e29b-41d4-a716-446655440000","final_content":"Hello world!","tokens_used":5}

data: [DONE]
```

**Event Types**:
```typescript
type StreamEvent =
  | { type: 'stream_start'; message_id: UUID; timestamp: Timestamp }
  | { type: 'stream_token'; message_id: UUID; token: string }
  | { type: 'stream_complete'; message_id: UUID; final_content: string; tokens_used: number }
  | { type: 'error'; error: string; code?: string };
```

**Example (EventSource)**:
```typescript
const streamChat = async (messages: Message[]) => {
  const token = localStorage.getItem('access_token');

  const response = await fetch('/api/v2/chat/completions/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream'
    },
    body: JSON.stringify({
      messages,
      model: 'deepseek-chat',
      stream: true,
      temperature: 0.7,
      max_tokens: 2048
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);

        if (data === '[DONE]') {
          return;
        }

        try {
          const event = JSON.parse(data);

          if (event.type === 'stream_token') {
            // Append token to UI
            appendToken(event.token);
          } else if (event.type === 'stream_complete') {
            // Finalize message
            console.log('Tokens used:', event.tokens_used);
          } else if (event.type === 'error') {
            console.error('Stream error:', event.error);
          }
        } catch (e) {
          console.error('Parse error:', e);
        }
      }
    }
  }
};
```

**Error Responses**:
- `401 Unauthorized`: Invalid token
- `400 Bad Request`: Invalid request format
- `429 Too Many Requests`: Rate limit exceeded
  ```typescript
  {
    "error": "Rate limit exceeded",
    "retry_after": 60  // seconds
  }
  ```

---

#### GET `/api/v2/chat/health/`
**Check chat service health**

**Authentication**: Optional (better with JWT for full details)

**Response** (200 OK):
```typescript
interface ChatHealthResponse {
  status: 'healthy' | 'degraded' | 'error';
  message: string;
  config: {
    provider: 'deepseek';
    model: string;
    max_tokens: number;
    temperature: number;
    base_url: string;
    sse_available: boolean;
  };
}
```

---

#### GET `/api/v2/chat/auth-test/`
**Test authentication (debugging endpoint)**

**Authentication**: Required (JWT)

**Response** (200 OK):
```typescript
{
  "authenticated": true,
  "user": {
    "id": UUID,
    "username": string
  },
  "token_info": {
    "exp": number,  // Expiration timestamp
    "iat": number   // Issued at timestamp
  }
}
```

---

### Template Management

#### GET `/api/v2/templates/`
**List all templates**

**Authentication**: Required (JWT)

**Query Parameters**:
```typescript
interface TemplateListParams {
  page?: number;              // Page number (default: 1)
  page_size?: number;         // Results per page (default: 20, max: 100)
  category?: string;          // Filter by category slug
  search?: string;            // Search in title/description
  ordering?: string;          // Sort field: created_at, -created_at, usage_count, -usage_count
  is_featured?: boolean;      // Filter featured templates
  is_public?: boolean;        // Filter public templates
  created_by?: 'me' | UUID;   // Filter by creator
}
```

**Response** (200 OK):
```typescript
interface TemplateListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Array<{
    id: UUID;
    title: string;
    description: string;
    category: {
      id: number;
      name: string;
      slug: string;
      icon: string;
      color: string;
    };
    created_by: {
      id: UUID;
      username: string;
      avatar_url: string | null;
    };
    is_featured: boolean;
    is_public: boolean;
    usage_count: number;
    average_rating: number;  // 0.0-5.0
    tags: string[];
    created_at: Timestamp;
    updated_at: Timestamp;
  }>;
}
```

**Example**:
```typescript
const getTemplates = async (params: TemplateListParams = {}) => {
  const queryString = new URLSearchParams(params).toString();

  const response = await fetch(`/api/v2/templates/?${queryString}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });

  return await response.json();
};

// Usage
const templates = await getTemplates({
  category: 'business',
  ordering: '-usage_count',
  page_size: 10
});
```

---

#### GET `/api/v2/templates/{id}/`
**Get template details**

**Authentication**: Required (JWT)

**Response** (200 OK):
```typescript
interface TemplateDetail {
  id: UUID;
  title: string;
  description: string;
  category: {
    id: number;
    name: string;
    slug: string;
    icon: string;
    color: string;
    description: string;
  };
  template_content: string;  // Template with {{placeholders}}
  fields: Array<{
    id: UUID;
    label: string;
    placeholder: string;
    field_type: 'text' | 'textarea' | 'dropdown' | 'checkbox' | 'radio' | 'number';
    is_required: boolean;
    default_value: string;
    help_text: string;
    options: string[];  // For dropdown/radio/checkbox
    order: number;
  }>;
  created_by: {
    id: UUID;
    username: string;
    avatar_url: string | null;
    user_rank: string;
  };
  is_featured: boolean;
  is_public: boolean;
  tags: string[];
  usage_count: number;
  average_rating: number;
  your_rating: number | null;
  created_at: Timestamp;
  updated_at: Timestamp;

  // Analytics
  analytics: {
    total_uses: number;
    unique_users: number;
    success_rate: number;  // Percentage
    avg_completion_time: number;  // Seconds
  };
}
```

**Error Responses**:
- `404 Not Found`: Template doesn't exist

---

#### POST `/api/v2/templates/`
**Create new template**

**Authentication**: Required (JWT)

**Request Body**:
```typescript
interface CreateTemplateRequest {
  title: string;  // Max 200 chars
  description: string;
  category: number;  // Category ID
  template_content: string;  // Template with {{placeholders}}
  fields: Array<{
    label: string;
    placeholder?: string;
    field_type: 'text' | 'textarea' | 'dropdown' | 'checkbox' | 'radio' | 'number';
    is_required?: boolean;
    default_value?: string;
    help_text?: string;
    options?: string[];  // Required for dropdown/radio/checkbox
    order?: number;
  }>;
  tags?: string[];
  is_public?: boolean;  // Default: false
}
```

**Response** (201 Created): Same as GET `/api/v2/templates/{id}/`

**Error Responses**:
- `400 Bad Request`: Validation errors

---

#### PUT/PATCH `/api/v2/templates/{id}/`
**Update template**

**Authentication**: Required (JWT, must be creator or admin)

**Request Body**: Same as POST (all fields optional for PATCH)

**Response** (200 OK): Same as GET `/api/v2/templates/{id}/`

**Error Responses**:
- `403 Forbidden`: Not the owner
- `404 Not Found`: Template doesn't exist

---

#### DELETE `/api/v2/templates/{id}/`
**Delete template**

**Authentication**: Required (JWT, must be creator or admin)

**Response** (204 No Content): Empty response

**Error Responses**:
- `403 Forbidden`: Not the owner
- `404 Not Found`: Template doesn't exist

---

#### GET `/api/v2/template-categories/`
**List template categories**

**Authentication**: None (public)

**Response** (200 OK):
```typescript
Array<{
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  color: string;  // Hex color
  is_active: boolean;
  order: number;
  template_count: number;  // Number of templates in category
}>
```

---

#### GET `/api/v2/search/prompts/`
**High-performance template search**

**Authentication**: Required (JWT)

**Query Parameters**:
```typescript
interface SearchPromptsParams {
  q: string;              // Search query (required)
  category?: string;      // Category slug
  max_results?: number;   // Max results (default: 20, max: 50)
  min_rating?: number;    // Minimum average rating (0-5)
}
```

**Response** (200 OK):
```typescript
interface SearchResult {
  results: Array<{
    id: UUID;
    title: string;
    description: string;
    category: string;
    tags: string[];
    score: number;  // Relevance score (0-1)
    relevance_reason: string;  // Why this matched
    usage_count: number;
    average_rating: number;
    preview: string;  // First 200 chars of content
  }>;
  total_results: number;
  search_time_ms: number;
  from_cache: boolean;
}
```

---

### Gamification

#### GET `/api/v2/gamification/achievements/`
**Get user achievements**

**Authentication**: Required (JWT)

**Response** (200 OK):
```typescript
interface AchievementsResponse {
  unlocked: Array<{
    id: UUID;
    name: string;
    description: string;
    icon: string;
    points: number;
    category: string;
    unlocked_at: Timestamp;
    rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  }>;
  locked: Array<{
    id: UUID;
    name: string;
    description: string;
    icon: string;
    points: number;
    category: string;
    progress: number;  // 0-100 percentage
    requirement: string;
  }>;
  progress: {
    total_xp: number;
    current_level: number;
    next_level_xp: number;
    level_progress: number;  // 0-100 percentage
    total_achievements: number;
    unlocked_achievements: number;
  };
}
```

---

#### GET `/api/v2/gamification/leaderboard/`
**Get leaderboard rankings**

**Authentication**: Required (JWT)

**Query Parameters**:
```typescript
interface LeaderboardParams {
  timeframe?: 'weekly' | 'monthly' | 'all_time';  // Default: 'all_time'
  category?: 'xp' | 'templates' | 'prompts' | 'streak';  // Default: 'xp'
  limit?: number;  // Default: 100
}
```

**Response** (200 OK):
```typescript
interface LeaderboardResponse {
  rankings: Array<{
    rank: number;
    user: {
      id: UUID;
      username: string;
      avatar_url: string | null;
      user_rank: string;
    };
    score: number;
    level: number;
    badge: string | null;
  }>;
  your_rank: {
    rank: number;
    score: number;
    percentile: number;  // 0-100
  };
}
```

---

### Analytics

#### GET `/api/v2/analytics/dashboard/`
**Get analytics dashboard data**

**Authentication**: Required (JWT)

**Query Parameters**:
```typescript
interface AnalyticsDashboardParams {
  timeframe?: 'day' | 'week' | 'month' | 'year';  // Default: 'week'
}
```

**Response** (200 OK):
```typescript
interface AnalyticsDashboard {
  overview: {
    total_prompts: number;
    total_templates: number;
    total_credits_used: number;
    avg_completion_time: number;  // Seconds
  };
  trends: Array<{
    date: string;  // YYYY-MM-DD
    prompts_generated: number;
    templates_created: number;
    credits_used: number;
  }>;
  top_categories: Array<{
    category: string;
    count: number;
    percentage: number;
  }>;
  recent_activity: Array<{
    id: UUID;
    action: string;
    timestamp: Timestamp;
    details: object;
  }>;
}
```

---

#### POST `/api/v2/analytics/track/`
**Track user event**

**Authentication**: Required (JWT)

**Request Body**:
```typescript
interface TrackEventRequest {
  event_type: string;  // e.g., 'template_used', 'prompt_generated'
  event_data: object;  // Event-specific data
  timestamp?: Timestamp;  // Optional, defaults to now
}
```

**Response** (201 Created):
```typescript
{
  "id": UUID,
  "event_type": string,
  "tracked_at": Timestamp
}
```

---

### Billing

#### GET `/api/v2/billing/plans/`
**Get available subscription plans**

**Authentication**: None (public)

**Response** (200 OK):
```typescript
Array<{
  id: string;
  name: string;
  description: string;
  price: number;  // In cents
  currency: string;  // e.g., 'usd'
  interval: 'month' | 'year';
  features: string[];
  credits_per_month: number;
  is_popular: boolean;
  stripe_price_id: string;
}>
```

---

#### GET `/api/v2/billing/me/entitlements/`
**Get current user's subscription entitlements**

**Authentication**: Required (JWT)

**Response** (200 OK):
```typescript
{
  plan: {
    name: string;
    is_premium: boolean;
    expires_at: Timestamp | null;
  };
  credits: {
    available: number;
    used_this_month: number;
    total_allocated: number;
  };
  features: string[];
  limits: {
    templates_per_month: number;
    prompts_per_day: number;
    api_calls_per_minute: number;
  };
}
```

---

#### POST `/api/v2/billing/checkout/`
**Create checkout session**

**Authentication**: Required (JWT)

**Request Body**:
```typescript
{
  price_id: string;  // Stripe price ID
  success_url?: string;  // Redirect after success
  cancel_url?: string;   // Redirect on cancel
}
```

**Response** (200 OK):
```typescript
{
  checkout_url: string;  // Redirect user here
  session_id: string;
}
```

---

### Health & Monitoring

#### GET `/api/health/`
**System health check (public)**

**Authentication**: None (public)

**Response** (200 OK or 503 Service Unavailable):
```typescript
{
  status: 'healthy' | 'degraded' | 'error';
  timestamp: Timestamp;
  app: 'PromptCraft';
  version: string;
  response_time_ms: number;
  services: {
    database: {
      status: 'healthy' | 'error';
      type?: string;
    };
    cache: {
      status: 'healthy' | 'degraded' | 'error';
      backend?: string;
    };
    celery?: {
      status: 'healthy' | 'warning' | 'error';
      workers?: number;
    };
    deepseek: {
      status: 'configured' | 'not_configured';
      model?: string;
    };
    channels?: {
      status: 'configured' | 'not_configured';
      backend?: string;
    };
  };
}
```

---

## Data Models & TypeScript Types

### Complete Type Definitions

```typescript
// ============= Core Types =============

type UUID = string;
type Timestamp = string;  // ISO 8601

// ============= User Types =============

interface User {
  id: UUID;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  bio: string;
  avatar_url: string | null;
  social_avatar_url: string | null;

  // Gamification
  credits: number;
  level: number;
  experience_points: number;
  next_level_xp: number;
  daily_streak: number;
  user_rank: string;

  // Premium
  is_premium: boolean;
  premium_expires_at: Timestamp | null;

  // Preferences
  theme_preference: 'light' | 'dark' | 'system';
  language_preference: string;
  ai_assistance_enabled: boolean;
  analytics_enabled: boolean;

  // Stats
  templates_created: number;
  templates_completed: number;
  total_prompts_generated: number;
  completion_rate: number;

  // Dates
  last_login_date: string;
  date_joined: Timestamp;
  last_login: Timestamp;
}

// ============= Template Types =============

type FieldType = 'text' | 'textarea' | 'dropdown' | 'checkbox' | 'radio' | 'number';

interface TemplateCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  color: string;
  is_active: boolean;
  order: number;
  template_count?: number;
}

interface TemplateField {
  id: UUID;
  label: string;
  placeholder: string;
  field_type: FieldType;
  is_required: boolean;
  default_value: string;
  validation_pattern?: string;
  help_text: string;
  options: string[];
  order: number;
}

interface Template {
  id: UUID;
  title: string;
  description: string;
  category: TemplateCategory;
  template_content: string;
  fields: TemplateField[];
  created_by: {
    id: UUID;
    username: string;
    avatar_url: string | null;
    user_rank: string;
  };
  is_featured: boolean;
  is_public: boolean;
  tags: string[];
  usage_count: number;
  average_rating: number;
  your_rating: number | null;
  created_at: Timestamp;
  updated_at: Timestamp;
  analytics?: {
    total_uses: number;
    unique_users: number;
    success_rate: number;
    avg_completion_time: number;
  };
}

// ============= Chat Types =============

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatCompletionRequest {
  messages: ChatMessage[];
  model?: string;
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
}

type StreamEvent =
  | { type: 'stream_start'; message_id: UUID; timestamp: Timestamp }
  | { type: 'stream_token'; message_id: UUID; token: string }
  | { type: 'stream_complete'; message_id: UUID; final_content: string; tokens_used: number }
  | { type: 'error'; error: string; code?: string };

// ============= Pagination Types =============

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ============= Error Types =============

interface APIError {
  detail?: string;
  errors?: Record<string, string[]>;
  code?: string;
}
```

---

## SSE Streaming Guide

### What is SSE?
Server-Sent Events (SSE) is a technology for streaming data from server to client over HTTP. It's simpler than WebSocket and perfect for one-way real-time data.

### Why Use SSE for Chat?
- ✅ Simpler than WebSocket
- ✅ Works over HTTP/HTTPS (no special protocol)
- ✅ Auto-reconnects on disconnect
- ✅ Built-in event ID tracking
- ✅ Works through corporate firewalls

### Complete SSE Implementation

```typescript
class ChatService {
  private baseUrl: string;
  private getToken: () => string | null;

  constructor(baseUrl: string, getToken: () => string | null) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
  }

  async streamCompletion(
    messages: ChatMessage[],
    onToken: (token: string) => void,
    onComplete: (fullContent: string, tokensUsed: number) => void,
    onError: (error: string) => void
  ): Promise<void> {
    const token = this.getToken();
    if (!token) {
      onError('Not authenticated');
      return;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v2/chat/completions/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({
          messages,
          model: 'deepseek-chat',
          stream: true,
          temperature: 0.7,
          max_tokens: 2048
        })
      });

      if (!response.ok) {
        const error = await response.json();
        onError(error.detail || 'Request failed');
        return;
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last incomplete line in buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();

            if (data === '[DONE]') {
              return;
            }

            try {
              const event: StreamEvent = JSON.parse(data);

              switch (event.type) {
                case 'stream_start':
                  // Stream started
                  break;

                case 'stream_token':
                  onToken(event.token);
                  break;

                case 'stream_complete':
                  onComplete(event.final_content, event.tokens_used);
                  break;

                case 'error':
                  onError(event.error);
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE event:', e);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unknown error');
    }
  }
}

// Usage in React component
const ChatComponent = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const chatService = new ChatService(
    process.env.REACT_APP_API_URL!,
    () => localStorage.getItem('access_token')
  );

  const sendMessage = async (content: string) => {
    const newMessages = [...messages, { role: 'user' as const, content }];
    setMessages(newMessages);
    setCurrentResponse('');
    setIsStreaming(true);

    await chatService.streamCompletion(
      newMessages,
      // On token
      (token) => {
        setCurrentResponse(prev => prev + token);
      },
      // On complete
      (fullContent, tokensUsed) => {
        setMessages(prev => [...prev, { role: 'assistant', content: fullContent }]);
        setCurrentResponse('');
        setIsStreaming(false);
        console.log(`Used ${tokensUsed} tokens`);
      },
      // On error
      (error) => {
        console.error('Stream error:', error);
        setIsStreaming(false);
      }
    );
  };

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i} className={msg.role}>
          {msg.content}
        </div>
      ))}
      {isStreaming && currentResponse && (
        <div className="assistant streaming">
          {currentResponse}
          <span className="cursor">▊</span>
        </div>
      )}
    </div>
  );
};
```

---

## WebSocket Guide

### WebSocket Connection (Alternative to SSE)

**WebSocket URL**: `ws://localhost:8000/ws/chat/{session_id}/?token={jwt_token}`

### Connection with Authentication

```typescript
class WebSocketChatService {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private token: string;

  constructor(sessionId: string, token: string) {
    this.sessionId = sessionId;
    this.token = token;
  }

  connect(
    onMessage: (event: any) => void,
    onError: (error: Event) => void,
    onClose: () => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `ws://localhost:8000/ws/chat/${this.sessionId}/?token=${this.token}`;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        resolve();
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError(error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        onClose();
      };
    });
  }

  sendMessage(content: string, options = {}) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify({
      type: 'send_message',
      content,
      sessionId: this.sessionId,
      messageId: crypto.randomUUID(),
      options: {
        model: 'deepseek-chat',
        temperature: 0.7,
        maxTokens: 2000,
        ...options
      }
    }));
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage
const ws = new WebSocketChatService(
  'session-123',
  localStorage.getItem('access_token')!
);

await ws.connect(
  // On message
  (data) => {
    if (data.type === 'stream_token') {
      appendToken(data.token);
    } else if (data.type === 'stream_complete') {
      console.log('Complete:', data.final_content);
    }
  },
  // On error
  (error) => console.error(error),
  // On close
  () => console.log('Connection closed')
);

ws.sendMessage('Hello AI!');
```

**Note**: SSE is recommended over WebSocket for this use case as it's simpler and more reliable.

---

## Error Handling

### Standard Error Response Format

```typescript
interface ErrorResponse {
  detail?: string;              // Human-readable error message
  errors?: Record<string, string[]>;  // Field-specific validation errors
  code?: string;                // Error code for programmatic handling
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET/PUT/PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation errors, malformed request |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

### Error Handling Best Practices

```typescript
class APIClient {
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = localStorage.getItem('access_token');

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      }
    });

    // Handle 401 - Try to refresh token
    if (response.status === 401) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        // Retry request with new token
        return this.request(endpoint, options);
      } else {
        // Redirect to login
        window.location.href = '/login';
        throw new Error('Authentication failed');
      }
    }

    // Handle other errors
    if (!response.ok) {
      const error: ErrorResponse = await response.json();

      if (error.errors) {
        // Validation errors
        throw new ValidationError(error.errors);
      } else if (error.detail) {
        // Generic error
        throw new APIError(error.detail, response.status);
      } else {
        throw new APIError(`HTTP ${response.status}`, response.status);
      }
    }

    return await response.json();
  }

  private async refreshToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/api/v2/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken })
      });

      if (response.ok) {
        const { access } = await response.json();
        localStorage.setItem('access_token', access);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    return false;
  }
}

class APIError extends Error {
  constructor(public message: string, public statusCode: number) {
    super(message);
    this.name = 'APIError';
  }
}

class ValidationError extends Error {
  constructor(public errors: Record<string, string[]>) {
    super('Validation failed');
    this.name = 'ValidationError';
  }
}
```

---

## Common Workflows

### Complete User Registration & Login Flow

```typescript
// 1. Register
const register = async (userData: RegisterRequest) => {
  const response = await fetch('/api/v2/auth/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  });

  if (response.ok) {
    const data = await response.json();
    // Store tokens
    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data.user;
  } else {
    const errors = await response.json();
    throw new ValidationError(errors);
  }
};

// 2. Login
const login = async (username: string, password: string) => {
  const response = await fetch('/api/v2/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();

  if (response.ok) {
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data.user;
  } else {
    throw new Error(data.detail);
  }
};

// 3. Logout
const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
};

// 4. Check if authenticated
const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('access_token');
};

// 5. Get current user
const getCurrentUser = (): User | null => {
  const userJson = localStorage.getItem('user');
  return userJson ? JSON.parse(userJson) : null;
};
```

### Template Creation Flow

```typescript
const createTemplate = async (template: CreateTemplateRequest) => {
  // 1. Validate required fields
  if (!template.title || !template.template_content || !template.category) {
    throw new Error('Missing required fields');
  }

  // 2. Create template
  const response = await fetch('/api/v2/templates/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(template)
  });

  if (response.ok) {
    const createdTemplate = await response.json();

    // 3. Track event
    await fetch('/api/v2/analytics/track/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        event_type: 'template_created',
        event_data: {
          template_id: createdTemplate.id,
          category: template.category
        }
      })
    });

    return createdTemplate;
  } else {
    const errors = await response.json();
    throw new ValidationError(errors);
  }
};
```

### Chat Conversation Flow

```typescript
const chatConversation = async () => {
  const messages: ChatMessage[] = [];

  // 1. Add user message
  const userMessage = 'Hello! Can you help me write a blog post?';
  messages.push({ role: 'user', content: userMessage });

  // 2. Stream AI response
  let aiResponse = '';

  await streamChat(messages, {
    onToken: (token) => {
      aiResponse += token;
      updateUI(aiResponse);  // Update UI in real-time
    },
    onComplete: (fullContent, tokens) => {
      messages.push({ role: 'assistant', content: fullContent });
      console.log(`Used ${tokens} tokens`);
    },
    onError: (error) => {
      console.error('Chat error:', error);
      showError(error);
    }
  });

  // 3. Continue conversation
  messages.push({ role: 'user', content: 'Make it about AI' });
  // Repeat step 2 with updated messages array
};
```

---

## Rate Limiting & Pagination

### Rate Limits

Different endpoints have different rate limits based on user tier:

| Endpoint | Free Tier | Premium Tier |
|----------|-----------|--------------|
| `/api/v2/chat/completions/` | 10/hour | 100/hour |
| `/api/v2/templates/` (list) | 100/hour | Unlimited |
| `/api/v2/auth/*` | 20/hour | 50/hour |

### Rate Limit Headers

When rate limited, you'll receive:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642680000
```

### Handling Rate Limits

```typescript
const handleRateLimit = async (response: Response) => {
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    const seconds = parseInt(retryAfter || '60');

    throw new RateLimitError(`Rate limit exceeded. Retry after ${seconds} seconds`, seconds);
  }
};

class RateLimitError extends Error {
  constructor(message: string, public retryAfter: number) {
    super(message);
    this.name = 'RateLimitError';
  }
}
```

### Pagination

List endpoints support two pagination styles:

#### 1. Offset Pagination (Default)
```typescript
const getTemplates = async (page = 1, pageSize = 20) => {
  const response = await fetch(
    `/api/v2/templates/?page=${page}&page_size=${pageSize}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );

  const data: PaginatedResponse<Template> = await response.json();

  return {
    templates: data.results,
    hasNext: !!data.next,
    hasPrevious: !!data.previous,
    total: data.count
  };
};
```

#### 2. Cursor Pagination (For large datasets)
```typescript
const getTemplatesCursor = async (cursor?: string) => {
  const url = cursor || '/api/v2/templates/';

  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const data: PaginatedResponse<Template> = await response.json();

  return {
    templates: data.results,
    nextCursor: data.next,
    previousCursor: data.previous
  };
};
```

---

## Environment Configuration

### Environment Variables

Create a `.env` file in your frontend project:

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_BILLING=true

# External Services
REACT_APP_STRIPE_PUBLIC_KEY=pk_test_...
```

### TypeScript Configuration

```typescript
// src/config/api.ts
export const API_CONFIG = {
  baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  wsUrl: process.env.REACT_APP_WS_URL || 'ws://localhost:8000',
  timeout: 30000,
  retries: 3
};

export const ENDPOINTS = {
  auth: {
    register: '/api/v2/auth/register/',
    login: '/api/v2/auth/login/',
    refresh: '/api/v2/auth/refresh/',
    profile: '/api/v2/auth/profile/',
    logout: '/api/v2/auth/logout/'
  },
  chat: {
    completions: '/api/v2/chat/completions/',
    health: '/api/v2/chat/health/'
  },
  templates: {
    list: '/api/v2/templates/',
    detail: (id: string) => `/api/v2/templates/${id}/`,
    categories: '/api/v2/template-categories/'
  }
};
```

---

## Testing & Debugging

### Test Authentication
```bash
# Test registration
curl -X POST http://localhost:8000/api/v2/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'

# Test login
curl -X POST http://localhost:8000/api/v2/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'

# Test protected endpoint
curl -X GET http://localhost:8000/api/v2/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Debug Headers

Include these headers for debugging:
```http
X-Request-ID: unique-request-id  # Track specific requests
X-Debug: true                     # Enable debug mode (dev only)
```

Response will include:
```http
X-Request-ID: unique-request-id
X-Response-Time: 245ms
X-Server-Version: 2.0.0
```

---

## Quick Reference

### Authentication Headers
```typescript
{
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

### SSE Headers
```typescript
{
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json',
  'Accept': 'text/event-stream'
}
```

### WebSocket URL
```
ws://localhost:8000/ws/chat/{sessionId}/?token={jwtToken}
```

### Common Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (check request body)
- `401` - Unauthorized (check token)
- `403` - Forbidden (check permissions)
- `404` - Not Found
- `429` - Rate Limited (wait and retry)

---

## Support & Contact

**Backend Developer**: Available for questions during development
**API Documentation**: This file
**API Explorer**: http://localhost:8000/api/schema/swagger-ui/ (when server running)
**Health Check**: http://localhost:8000/api/health/

---

**Document Version**: 1.0.0
**Last Updated**: January 31, 2026
**Maintained By**: Backend Team

---

## Changelog

### v2.0.0 (2026-01-31)
- Initial comprehensive API documentation
- Added TypeScript type definitions
- Added SSE streaming guide
- Added WebSocket guide
- Added complete workflow examples
- Added error handling guide
