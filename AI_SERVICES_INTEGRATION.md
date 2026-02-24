# AI Services Frontend Integration Guide

Complete guide for integrating AI Services API endpoints into frontend applications, covering React/TypeScript implementation with best practices.

---

## Overview

This guide covers integrating the PromptCraft AI Services API into your frontend after successful local testing and validation.

**Prerequisites**:
- ✅ All API endpoints tested and working locally
- ✅ Iteration 1 tests passing
- ✅ Token authentication working
- ✅ CORS configured properly

---

## Frontend Architecture Overview

```
Frontend Layer
├── API Client (HTTPClient)
├── Services Layer
│   ├── AIProviderService
│   ├── GenerationService
│   ├── AssistantService
│   ├── OptimizationService
│   ├── AskMeService
│   └── RAGService
├── State Management (Context/Redux)
└── UI Components
```

---

## API Client Setup

### 1. Create API Client Service

Save as `src/services/apiClient.ts`:

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
  timestamp: string;
}

export interface ApiError extends AxiosError {
  response?: {
    status: number;
    data: {
      error: string;
      detail: string;
      code: string;
    };
  };
}

class APIClient {
  private baseURL: string;
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v2';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Add request interceptor for token
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: ApiError) => {
        if (error.response?.status === 401) {
          // Token expired - trigger re-login
          this.handleUnauthorized();
        }
        return Promise.reject(error);
      }
    );

    // Load token from localStorage on init
    this.loadToken();
  }

  /**
   * Set authentication token
   */
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  /**
   * Load token from localStorage
   */
  private loadToken(): void {
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.token = token;
    }
  }

  /**
   * Clear token on logout
   */
  clearToken(): void {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  /**
   * Handle unauthorized requests
   */
  private handleUnauthorized(): void {
    this.clearToken();
    window.location.href = '/login';
  }

  /**
   * GET request
   */
  async get<T>(url: string, params?: Record<string, any>): Promise<T> {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  /**
   * POST request
   */
  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post(url, data);
    return response.data;
  }

  /**
   * PUT request
   */
  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put(url, data);
    return response.data;
  }

  /**
   * DELETE request
   */
  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete(url);
    return response.data;
  }

  /**
   * Streaming GET (SSE)
   */
  async *streamGet(url: string): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${this.baseURL}${url}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            yield line.slice(6);
          }
        }
      }

      if (buffer) {
        if (buffer.startsWith('data: ')) {
          yield buffer.slice(6);
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Streaming POST (SSE)
   */
  async *streamPost(url: string, data: any): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${this.baseURL}${url}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            yield line.slice(6);
          }
        }
      }

      if (buffer && buffer.startsWith('data: ')) {
        yield buffer.slice(6);
      }
    } finally {
      reader.releaseLock();
    }
  }
}

export const apiClient = new APIClient();
```

---

## Service Layer Implementation

### 2. AI Provider Service

Save as `src/services/aiProviderService.ts`:

```typescript
import { apiClient } from './apiClient';

export interface AIProvider {
  id: string;
  name: string;
  status: 'available' | 'disabled';
  models: string[];
  features: string[];
  cost_per_1k_tokens?: number;
  max_tokens?: number;
}

export interface AIModel {
  id: string;
  provider: string;
  name: string;
  max_tokens: number;
  cost_input: number;
  cost_output: number;
  description: string;
  features: string[];
}

export class AIProviderService {
  /**
   * Get list of available AI providers
   */
  static async getProviders(): Promise<AIProvider[]> {
    const response = await apiClient.get('/ai-services/providers/');
    return response.providers;
  }

  /**
   * Get available models with optional filtering
   */
  static async getModels(provider?: string, feature?: string): Promise<AIModel[]> {
    const params: Record<string, string> = {};
    if (provider) params.provider = provider;
    if (feature) params.feature = feature;

    const response = await apiClient.get('/ai-services/models/', params);
    return response.models;
  }

  /**
   * Test DeepSeek connection
   */
  static async testDeepSeek() {
    return apiClient.get('/ai-services/deepseek/test/');
  }

  /**
   * Get provider by ID
   */
  static async getProviderById(providerId: string): Promise<AIProvider | null> {
    const providers = await this.getProviders();
    return providers.find(p => p.id === providerId) || null;
  }
}
```

---

### 3. Content Generation Service

Save as `src/services/generationService.ts`:

```typescript
import { apiClient } from './apiClient';

export interface GenerateRequest {
  provider: string;
  model: string;
  prompt: string;
  system_message?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface GenerateResponse {
  content: string;
  tokens_used: number;
  provider: string;
  model: string;
  execution_time: number;
  finish_reason: string;
}

export class GenerationService {
  /**
   * Generate content (non-streaming)
   */
  static async generate(request: GenerateRequest): Promise<GenerateResponse> {
    return apiClient.post('/ai-services/generate/', {
      ...request,
      stream: false,
    });
  }

  /**
   * Generate content with streaming
   */
  static async *generateStream(request: GenerateRequest): AsyncGenerator<string> {
    const stream = apiClient.streamPost('/ai-services/generate/', {
      ...request,
      stream: true,
    });

    for await (const chunk of stream) {
      yield chunk;
    }
  }

  /**
   * Chat with DeepSeek
   */
  static async deepseekChat(messages: any[], temperature = 0.7, maxTokens = 500) {
    return apiClient.post('/ai-services/deepseek/chat/', {
      messages,
      temperature,
      max_tokens: maxTokens,
    });
  }

  /**
   * Stream from DeepSeek
   */
  static async *deepseekStream(
    message: string,
    maxTokens = 500,
    temperature = 0.7
  ): AsyncGenerator<string> {
    const stream = apiClient.streamPost('/ai-services/deepseek/stream/', {
      message,
      max_tokens: maxTokens,
      temperature,
    });

    for await (const chunk of stream) {
      yield chunk;
    }
  }
}
```

---

### 4. Ask-Me Service

Save as `src/services/askmeService.ts`:

```typescript
import { apiClient } from './apiClient';

export interface AskMeQuestion {
  qid: string;
  title: string;
  kind: 'text' | 'checkbox' | 'radio' | 'textarea';
  help_text: string;
  options?: string[];
  is_required: boolean;
  suggested_answer?: string;
  answer?: string;
  is_answered: boolean;
  order: number;
}

export interface AskMeSession {
  id: string;
  intent: string;
  questions: AskMeQuestion[];
  answered_vars: Record<string, any>;
  preview_prompt: string;
  final_prompt: string;
  is_complete: boolean;
  good_enough_to_run: boolean;
  completion_percentage: number;
  created_at: string;
  updated_at: string;
}

export class AskMeService {
  /**
   * Start new Ask-Me session
   */
  static async startSession(intent: string, context?: string): Promise<AskMeSession> {
    return apiClient.post('/ai-services/askme/start/', {
      intent,
      context,
    });
  }

  /**
   * Answer a question in session
   */
  static async answerQuestion(
    sessionId: string,
    qid: string,
    value: string | string[]
  ): Promise<AskMeSession> {
    return apiClient.post('/ai-services/askme/answer/', {
      session_id: sessionId,
      qid,
      value,
    });
  }

  /**
   * Finalize session and generate final prompt/code
   */
  static async finalizeSession(
    sessionId: string,
    generateCode = true,
    codeLanguage = 'python'
  ): Promise<AskMeSession & { generated_code?: string }> {
    return apiClient.post('/ai-services/askme/finalize/', {
      session_id: sessionId,
      generate_code: generateCode,
      code_language: codeLanguage,
    });
  }

  /**
   * Get all sessions for user
   */
  static async getSessions(limit = 10, offset = 0) {
    return apiClient.get('/ai-services/askme/sessions/', {
      limit,
      offset,
    });
  }

  /**
   * Get specific session details
   */
  static async getSession(sessionId: string): Promise<AskMeSession> {
    return apiClient.get(`/ai-services/askme/sessions/${sessionId}/`);
  }

  /**
   * Delete session
   */
  static async deleteSession(sessionId: string) {
    return apiClient.delete(`/ai-services/askme/sessions/${sessionId}/`);
  }

  /**
   * Stream finalization process
   */
  static async *streamFinalization(sessionId: string): AsyncGenerator<string> {
    const stream = apiClient.streamPost('/ai-services/askme/stream/', {
      session_id: sessionId,
    });

    for await (const chunk of stream) {
      yield chunk;
    }
  }
}
```

---

## React Hooks for Services

### 5. useAIProvider Hook

Save as `src/hooks/useAIProvider.ts`:

```typescript
import { useState, useEffect } from 'react';
import { AIProviderService, AIProvider, AIModel } from '../services/aiProviderService';

interface UseAIProviderReturn {
  providers: AIProvider[];
  models: AIModel[];
  loading: boolean;
  error: string | null;
  selectProvider: (providerId: string) => void;
  selectedProvider: AIProvider | null;
}

export function useAIProvider(): UseAIProviderReturn {
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [models, setModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<AIProvider | null>(null);

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        setLoading(true);
        const providers = await AIProviderService.getProviders();
        setProviders(providers);
      } catch (err: any) {
        setError(err.message || 'Failed to load providers');
      } finally {
        setLoading(false);
      }
    };

    fetchProviders();
  }, []);

  const selectProvider = async (providerId: string) => {
    const provider = providers.find(p => p.id === providerId);
    if (!provider) return;

    setSelectedProvider(provider);

    try {
      const models = await AIProviderService.getModels(providerId);
      setModels(models);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return {
    providers,
    models,
    loading,
    error,
    selectProvider,
    selectedProvider,
  };
}
```

---

### 6. useGeneration Hook

Save as `src/hooks/useGeneration.ts`:

```typescript
import { useState, useCallback } from 'react';
import { GenerationService, GenerateRequest } from '../services/generationService';

interface UseGenerationReturn {
  content: string;
  loading: boolean;
  error: string | null;
  tokens: number;
  generate: (params: GenerateRequest) => Promise<void>;
  stream: (params: GenerateRequest) => AsyncGenerator<string>;
  clear: () => void;
}

export function useGeneration(): UseGenerationReturn {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tokens, setTokens] = useState(0);

  const generate = useCallback(async (params: GenerateRequest) => {
    try {
      setLoading(true);
      setError(null);
      setContent('');

      const response = await GenerationService.generate(params);
      setContent(response.content);
      setTokens(response.tokens_used);
    } catch (err: any) {
      setError(err.message || 'Generation failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const stream = async function* (params: GenerateRequest) {
    try {
      setLoading(true);
      setError(null);
      setContent('');

      let fullContent = '';
      for await (const chunk of GenerationService.generateStream(params)) {
        fullContent += chunk;
        setContent(fullContent);
        yield chunk;
      }
    } catch (err: any) {
      setError(err.message || 'Streaming failed');
    } finally {
      setLoading(false);
    }
  };

  const clear = useCallback(() => {
    setContent('');
    setTokens(0);
    setError(null);
  }, []);

  return {
    content,
    loading,
    error,
    tokens,
    generate,
    stream,
    clear,
  };
}
```

---

### 7. useAskMe Hook

Save as `src/hooks/useAskMe.ts`:

```typescript
import { useState, useCallback } from 'react';
import { AskMeService, AskMeSession } from '../services/askmeService';

interface UseAskMeReturn {
  session: AskMeSession | null;
  loading: boolean;
  error: string | null;
  currentQuestion: any;
  completionPercentage: number;
  canComplete: boolean;
  startSession: (intent: string, context?: string) => Promise<void>;
  answerQuestion: (qid: string, value: any) => Promise<void>;
  finalize: (generateCode?: boolean, language?: string) => Promise<any>;
  reset: () => void;
}

export function useAskMe(): UseAskMeReturn {
  const [session, setSession] = useState<AskMeSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startSession = useCallback(async (intent: string, context?: string) => {
    try {
      setLoading(true);
      setError(null);
      const newSession = await AskMeService.startSession(intent, context);
      setSession(newSession);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const answerQuestion = useCallback(async (qid: string, value: any) => {
    if (!session) return;

    try {
      setLoading(true);
      const updated = await AskMeService.answerQuestion(session.id, qid, value);
      setSession(updated);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [session]);

  const finalize = useCallback(async (generateCode = true, language = 'python') => {
    if (!session) return;

    try {
      setLoading(true);
      const result = await AskMeService.finalizeSession(session.id, generateCode, language);
      setSession({ ...session, is_complete: true });
      return result;
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [session]);

  const reset = useCallback(() => {
    setSession(null);
    setError(null);
  }, []);

  const currentQuestion = session?.questions.find(q => !q.is_answered);
  const completionPercentage = session?.completion_percentage || 0;
  const canComplete = session?.good_enough_to_run || false;

  return {
    session,
    loading,
    error,
    currentQuestion,
    completionPercentage,
    canComplete,
    startSession,
    answerQuestion,
    finalize,
    reset,
  };
}
```

---

## React Components

### 8. Content Generator Component

Save as `src/components/ContentGenerator.tsx`:

```typescript
import React, { useState } from 'react';
import { useAIProvider } from '../hooks/useAIProvider';
import { useGeneration } from '../hooks/useGeneration';

export const ContentGenerator: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const { providers, models, selectProvider, selectedProvider } = useAIProvider();
  const { content, loading, error, stream } = useGeneration();
  const [isStreaming, setIsStreaming] = useState(false);

  const handleGenerate = async (useStream = false) => {
    if (!selectedProvider || !prompt) return;

    const model = models[0]?.id || selectedProvider.models[0];

    if (useStream) {
      setIsStreaming(true);
      await stream({
        provider: selectedProvider.id,
        model,
        prompt,
        stream: true,
      });
      setIsStreaming(false);
    } else {
      // Non-streaming
      await stream({
        provider: selectedProvider.id,
        model,
        prompt,
        stream: false,
      });
    }
  };

  return (
    <div className="content-generator">
      <div className="generator-section">
        <h2>Content Generator</h2>

        {/* Provider Selection */}
        <div className="provider-selector">
          <label>AI Provider:</label>
          <select onChange={(e) => selectProvider(e.target.value)}>
            <option value="">Select provider</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.status})
              </option>
            ))}
          </select>
        </div>

        {/* Model Display */}
        {selectedProvider && (
          <div className="model-info">
            <p>Provider: {selectedProvider.name}</p>
            <p>Models: {selectedProvider.models.join(', ')}</p>
            <p>Cost: ${selectedProvider.cost_per_1k_tokens}/1K tokens</p>
          </div>
        )}

        {/* Prompt Input */}
        <div className="input-section">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt..."
            rows={5}
          />
        </div>

        {/* Generate Buttons */}
        <div className="button-group">
          <button
            onClick={() => handleGenerate(false)}
            disabled={loading || !selectedProvider || !prompt}
          >
            {loading ? 'Generating...' : 'Generate'}
          </button>
          <button
            onClick={() => handleGenerate(true)}
            disabled={loading || !selectedProvider || !prompt}
          >
            {isStreaming ? 'Streaming...' : 'Stream'}
          </button>
        </div>

        {/* Error Display */}
        {error && <div className="error">{error}</div>}

        {/* Output Display */}
        {content && (
          <div className="output-section">
            <h3>Generated Content:</h3>
            <pre>{content}</pre>
          </div>
        )}
      </div>
    </div>
  );
};
```

---

### 9. Ask-Me Component

Save as `src/components/AskMeBuilder.tsx`:

```typescript
import React, { useState } from 'react';
import { useAskMe } from '../hooks/useAskMe';

export const AskMeBuilder: React.FC = () => {
  const [intent, setIntent] = useState('');
  const {
    session,
    loading,
    error,
    currentQuestion,
    completionPercentage,
    canComplete,
    startSession,
    answerQuestion,
    finalize,
    reset,
  } = useAskMe();

  if (!session) {
    return (
      <div className="askme-start">
        <h2>Ask-Me Prompt Builder</h2>
        <textarea
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          placeholder="What do you want to create?"
          rows={3}
        />
        <button
          onClick={() => startSession(intent)}
          disabled={loading || !intent}
        >
          Start Builder
        </button>
        {error && <div className="error">{error}</div>}
      </div>
    );
  }

  return (
    <div className="askme-builder">
      <h2>{session.intent}</h2>

      {/* Progress Bar */}
      <div className="progress">
        <div 
          className="progress-bar"
          style={{ width: `${completionPercentage}%`}}
        />
        <span>{completionPercentage}% Complete</span>
      </div>

      {/* Current Question */}
      {currentQuestion ? (
        <div className="question-form">
          <h3>{currentQuestion.title}</h3>
          <p>{currentQuestion.help_text}</p>

          {/* Text Input */}
          {currentQuestion.kind === 'text' && (
            <input
              type="text"
              defaultValue={currentQuestion.suggested_answer}
              onBlur={(e) =>
                answerQuestion(currentQuestion.qid, e.target.value)
              }
            />
          )}

          {/* Checkbox */}
          {currentQuestion.kind === 'checkbox' && (
            <div className="checkbox-group">
              {currentQuestion.options?.map((opt) => (
                <label key={opt}>
                  <input type="checkbox" value={opt} />
                  {opt}
                </label>
              ))}
            </div>
          )}

          {/* Textarea */}
          {currentQuestion.kind === 'textarea' && (
            <textarea
              rows={5}
              onBlur={(e) =>
                answerQuestion(currentQuestion.qid, e.target.value)
              }
            />
          )}
        </div>
      ) : (
        <div className="complete-ready">
          <h3>Ready to Generate!</h3>
          {canComplete && (
            <button
              onClick={() => finalize(true, 'python')}
              disabled={loading}
            >
              {loading ? 'Finalizing...' : 'Generate Prompt & Code'}
            </button>
          )}
        </div>
      )}

      {session.preview_prompt && (
        <div className="preview">
          <h4>Preview:</h4>
          <pre>{session.preview_prompt}</pre>
        </div>
      )}

      <button onClick={reset} className="reset-btn">
        Reset
      </button>
      {error && <div className="error">{error}</div>}
    </div>
  );
};
```

---

## Environment Configuration

### 10. Environment Setup

Create `.env.local`:

```bash
REACT_APP_API_BASE_URL=http://localhost:8000/api/v2
REACT_APP_AUTH_TOKEN_KEY=auth_token
REACT_APP_API_TIMEOUT=30000
REACT_APP_STREAMING_CHUNK_SIZE=1024
```

For production (`.env.production`):

```bash
REACT_APP_API_BASE_URL=https://api.promptcraft.app/api/v2
REACT_APP_AUTH_TOKEN_KEY=auth_token
REACT_APP_API_TIMEOUT=60000
```

---

## Error Handling & Validation

### 11. Error Handler Utility

Save as `src/utils/errorHandler.ts`:

```typescript
export class APIError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export function handleAPIError(error: any): APIError {
  if (error.response) {
    const { status, data } = error.response;
    return new APIError(
      status,
      data.code || 'UNKNOWN_ERROR',
      data.error || data.detail || 'An error occurred',
      data
    );
  }

  if (error.message) {
    return new APIError(0, 'NETWORK_ERROR', error.message);
  }

  return new APIError(0, 'UNKNOWN_ERROR', 'Unknown error occurred');
}

export function getErrorMessage(error: APIError): string {
  switch (error.code) {
    case 'INVALID_PROVIDER':
      return 'The selected AI provider is not available.';
    case 'MISSING_FIELD':
      return `Required field missing: ${error.details?.field}`;
    case 'RATE_LIMITED':
      return 'Too many requests. Please wait before trying again.';
    case 'TIMEOUT':
      return 'Request timed out. Please try again.';
    default:
      return error.message;
  }
}
```

---

## Testing Integration

### 12. API Integration Tests

Save as `src/__tests__/api.integration.test.ts`:

```typescript
import { APIClient } from '../services/apiClient';
import { AIProviderService } from '../services/aiProviderService';
import { GenerationService } from '../services/generationService';
import { AskMeService } from '../services/askmeService';

describe('API Integration Tests', () => {
  beforeAll(() => {
    // Set test token
    const apiClient = new APIClient();
    apiClient.setToken('test_token_here');
  });

  describe('Providers', () => {
    it('should fetch providers', async () => {
      const providers = await AIProviderService.getProviders();
      expect(Array.isArray(providers)).toBe(true);
      expect(providers.length).toBeGreaterThan(0);
    });

    it('should find DeepSeek provider', async () => {
      const providers = await AIProviderService.getProviders();
      const deepseek = providers.find(p => p.id === 'deepseek');
      expect(deepseek).toBeDefined();
    });
  });

  describe('Generation', () => {
    it('should generate content', async () => {
      const response = await GenerationService.generate({
        provider: 'deepseek',
        model: 'deepseek-chat',
        prompt: 'Hello',
        stream: false,
      });

      expect(response.content).toBeTruthy();
      expect(response.tokens_used).toBeGreaterThan(0);
    });
  });

  describe('Ask-Me', () => {
    it('should start session', async () => {
      const session = await AskMeService.startSession(
        'Create a Python script'
      );

      expect(session.id).toBeTruthy();
      expect(Array.isArray(session.questions)).toBe(true);
    });
  });
});
```

---

## Checklist Before Frontend Integration

- [ ] All API endpoints tested locally and working
- [ ] Authentication token system implemented
- [ ] API Client created with interceptors
- [ ] All service classes implemented
- [ ] React hooks created and tested
- [ ] Components using hooks
- [ ] Error handling implemented
- [ ] Environment variables configured
- [ ] Integration tests passing
- [ ] CORS issues resolved
- [ ] Rate limiting understood
- [ ] Streaming endpoints working
- [ ] Token refresh working
- [ ] Error messages helpful

---

## Deployment Integration

### Production Checklist
- [ ] Update API_BASE_URL to production endpoint
- [ ] Enable HTTPS for API calls
- [ ] Configure CORS for production domain
- [ ] Set rate limits appropriately
- [ ] Monitor API usage
- [ ] Setup error tracking (Sentry, etc.)
- [ ] Performance monitoring enabled

---

## Common Issues & Solutions

### Issue: CORS Errors
**Solution**: Ensure CORS headers in backend:
```python
# In Django settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://yourdomain.com"
]
```

### Issue: Token Expires
**Solution**: Implement token refresh:
```typescript
// In apiClient.ts interceptor
if (error.response?.status === 401) {
  // Try refresh token
  // If fails, redirect to login
}
```

### Issue: Streaming Not Working
**Solution**: Check SSE headers in Django response:
```python
response = StreamingHttpResponse(...)
response['Content-Type'] = 'text/event-stream'
```

---

## Next Steps

1. ✅ Set up API client
2. ✅ Implement services
3. ✅ Create hooks
4. ✅ Build components
5. ✅ Test integration
6. ✅ Deploy to production

See [API_ENDPOINTS_COMPLETE.md](API_ENDPOINTS_COMPLETE.md) for endpoint reference.

