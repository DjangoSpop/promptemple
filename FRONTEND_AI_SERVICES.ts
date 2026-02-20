/**
 * PromptCraft – AI Services Frontend Integration
 * ================================================
 *
 * Drop-in module for any React / Next.js / vanilla-TS frontend.
 *
 * KEY CHANGE: The old `/ws/optimization/` WebSocket endpoint is GONE.
 * Heroku runs Gunicorn (WSGI) — WebSockets are not supported.
 * All real-time streaming now uses **SSE (Server-Sent Events)** over
 * regular HTTP, which works everywhere (Heroku, Vercel, Cloudflare, …).
 *
 * Base path for all AI endpoints:
 *   PRODUCTION  → https://api.prompt-temple.com/api/v2/ai/
 *   DEV         → http://127.0.0.1:8000/api/v2/ai/
 *
 * Requires a valid JWT access token (Bearer).
 *
 * Usage example (React):
 * ```tsx
 * import { aiService } from './FRONTEND_AI_SERVICES';
 *
 * // set token once after login
 * aiService.setToken(accessToken);
 *
 * // non-streaming optimization
 * const result = await aiService.optimizePrompt({ original: 'Write me a poem' });
 *
 * // SSE streaming optimization
 * aiService.optimizePromptStream(
 *   { original: 'Write me a poem about AI' },
 *   {
 *     onProgress: (step, message) => console.log(step, message),
 *     onResult:   (data)          => console.log('optimized:', data.optimized),
 *     onError:    (err)           => console.error(err),
 *     onComplete: ()              => console.log('done'),
 *   }
 * );
 * ```
 */

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const API_BASE =
  process.env.REACT_APP_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === 'production'
    ? 'https://api.prompt-temple.com'
    : 'http://127.0.0.1:8000');

const AI_PREFIX = '/api/v2/ai';

// ---------------------------------------------------------------------------
// Types  – mirror the backend response shapes exactly
// ---------------------------------------------------------------------------

/** POST /api/v2/ai/providers/ */
export interface AIProvider {
  id: string;
  name: string;
  status: 'available' | 'disabled';
  models: string[];
  features: string[];
  cost_per_1k_tokens?: number;
  max_tokens?: number;
  description?: string;
}

export interface AIProvidersResponse {
  providers: AIProvider[];
  total_providers: number;
  deepseek_available: boolean;
  openrouter_available: boolean;
}

/** POST /api/v2/ai/models/ */
export interface AIModel {
  id: string;
  name: string;
  provider: string;
  cost_per_token: number;
  max_tokens: number;
  features: string[];
  description?: string;
}

export interface AIModelsResponse {
  models: AIModel[];
  total_models: number;
  deepseek_available: boolean;
  openrouter_available: boolean;
}

/** POST /api/v2/ai/generate/ */
export interface GenerateRequest {
  prompt: string;
  model?: string;           // default 'deepseek-chat'
  temperature?: number;     // default 0.7
  max_tokens?: number;      // default 1000
}

export interface GenerateResponse {
  result: string;
  model: string;
  tokens_used: number;
  processing_time_ms: number;
  cost_estimate: number;
  provider: string;
  success: boolean;
  error?: string;
}

/** POST /api/v2/ai/deepseek/chat/ */
export interface DeepSeekChatRequest {
  messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface DeepSeekChatResponse {
  message: { role: 'assistant'; content: string };
  model: string;
  tokens_used: number;
  processing_time_ms: number;
  cost_estimate: number;
  provider: 'deepseek';
  success: boolean;
  error?: string;
}

/** POST /api/v2/ai/optimization/ (JSON) & /optimization/stream/ (SSE) */
export interface OptimizationRequest {
  original: string;            // alias: prompt
  mode?: 'fast' | 'deep';     // default 'fast'
  session_id?: string;         // auto-generated if omitted
  context?: Record<string, any>;
  budget?: {
    tokens_in?: number;        // default 2000, max 5000
    tokens_out?: number;       // default 800,  max 2000
    max_credits?: number;      // default 5,    max 10
  };
}

export interface Citation {
  id: string;
  title: string;
  source: string;
  score: number;
}

export interface OptimizationResult {
  optimized: string;
  citations: Citation[];
  diff_summary: string;
  usage: Record<string, any>;
  run_id: string;
  processing_time_ms: number;
  success: boolean;
}

/** POST /api/v2/ai/agent/optimize/ (RAG agent) */
export interface AgentOptimizeRequest {
  session_id: string;
  original: string;
  mode?: 'fast' | 'deep';
  context?: { intent?: string; domain?: string };
  budget?: { tokens_in?: number; tokens_out?: number; max_credits?: number };
}

export interface AgentOptimizeResponse extends OptimizationResult {
  run_id: string;
}

/** POST /api/v2/ai/deepseek/stream/  (SSE) */
export interface DeepSeekStreamRequest {
  messages: Array<{ role: string; content: string }> | string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

/** GET /api/v2/ai/assistant/ */
export interface AssistantDescription {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
}

export interface AssistantListResponse {
  assistants: AssistantDescription[];
  default_assistant: string;
  total: number;
}

/** POST /api/v2/ai/assistant/run/ */
export interface AssistantRunRequest {
  assistant_id?: string;
  message: string;
  thread_id?: string;
  metadata?: Record<string, any>;
}

/** GET /api/v2/ai/assistant/threads/ */
export interface AssistantThread {
  id: string;
  assistant_id: string;
  title: string;
  metadata: Record<string, any>;
  last_interaction_at: string;
  created_at: string;
}

export interface AssistantThreadMessage {
  id: string;
  role: string;
  content: string;
  created_at: string;
  tool_name?: string;
  tool_result?: string;
}

/** SSE event handlers for streaming endpoints */
export interface SSEHandlers {
  onMeta?: (data: { request_id: string; status: string }) => void;
  onProgress?: (step: string, message: string) => void;
  onResult?: (data: any) => void;
  onStreamStart?: (data: any) => void;
  onStreamComplete?: (data: { request_id: string; processing_time_ms: number }) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
  /** Receives every raw data line (useful for token-by-token DeepSeek streaming) */
  onData?: (rawLine: string) => void;
}

// ---------------------------------------------------------------------------
// Helper: authenticated fetch
// ---------------------------------------------------------------------------

let _token: string | null = null;

function getToken(): string {
  if (_token) return _token;
  if (typeof window !== 'undefined') {
    return localStorage.getItem('accessToken') ?? '';
  }
  return '';
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${AI_PREFIX}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${getToken()}`,
    ...(options.headers as Record<string, string> ?? {}),
  };

  const res = await fetch(url, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body?.detail ?? body?.error ?? `HTTP ${res.status}`;
    throw new AIServiceError(res.status, msg, body);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Helper: SSE reader using native fetch + ReadableStream
// ---------------------------------------------------------------------------

function connectSSE(
  path: string,
  body: any,
  handlers: SSEHandlers,
): AbortController {
  const controller = new AbortController();

  const url = `${API_BASE}${AI_PREFIX}${path}`;

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        handlers.onError?.(errBody?.error ?? errBody?.detail ?? `HTTP ${res.status}`);
        handlers.onComplete?.();
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        handlers.onError?.('Response body is not readable');
        handlers.onComplete?.();
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = 'message'; // default SSE event type

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n');
        buffer = parts.pop() ?? '';

        for (const line of parts) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
            continue;
          }

          if (line.startsWith('data: ')) {
            const raw = line.slice(6).trim();

            // Forward raw data for token-by-token use
            handlers.onData?.(raw);

            // Try to parse JSON
            let data: any;
            try {
              data = JSON.parse(raw);
            } catch {
              // raw might be "[DONE]" or a non-JSON data: line
              if (raw === '[DONE]') {
                handlers.onComplete?.();
                return;
              }
              // For DeepSeek stream, raw may be a "data: {...}" prefixed chunk
              if (raw.startsWith('data: ')) {
                try { data = JSON.parse(raw.slice(6)); } catch { /* skip */ }
              }
              if (!data) continue;
            }

            switch (currentEvent) {
              case 'meta':
                handlers.onMeta?.(data);
                break;
              case 'progress':
                handlers.onProgress?.(data.step, data.message);
                break;
              case 'result':
                handlers.onResult?.(data);
                break;
              case 'stream_start':
                handlers.onStreamStart?.(data);
                break;
              case 'stream_complete':
                handlers.onStreamComplete?.(data);
                break;
              case 'error':
                handlers.onError?.(data.error ?? JSON.stringify(data));
                break;
              case 'stream_end':
                handlers.onComplete?.();
                break;
              default:
                // generic message or unknown event — treat as data
                handlers.onData?.(raw);
                break;
            }

            // Reset event type after processing
            currentEvent = 'message';
          }
        }
      }

      handlers.onComplete?.();
    })
    .catch((err) => {
      if (err.name === 'AbortError') return;
      handlers.onError?.(err.message ?? String(err));
      handlers.onComplete?.();
    });

  return controller;
}

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class AIServiceError extends Error {
  constructor(
    public status: number,
    message: string,
    public body?: any,
  ) {
    super(message);
    this.name = 'AIServiceError';
  }
}

// ---------------------------------------------------------------------------
// AI Service class  –  the single import the frontend needs
// ---------------------------------------------------------------------------

export class AIService {
  /** Call once after login to set the JWT */
  setToken(token: string) {
    _token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('accessToken', token);
    }
  }

  clearToken() {
    _token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('accessToken');
    }
  }

  // -------- providers & models --------

  /** GET /api/v2/ai/providers/ */
  getProviders(): Promise<AIProvidersResponse> {
    return apiFetch('/providers/');
  }

  /** GET /api/v2/ai/models/ */
  getModels(): Promise<AIModelsResponse> {
    return apiFetch('/models/');
  }

  // -------- generation --------

  /** POST /api/v2/ai/generate/ */
  generate(req: GenerateRequest): Promise<GenerateResponse> {
    return apiFetch('/generate/', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  // -------- DeepSeek chat --------

  /** POST /api/v2/ai/deepseek/chat/ */
  deepseekChat(req: DeepSeekChatRequest): Promise<DeepSeekChatResponse> {
    return apiFetch('/deepseek/chat/', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  /** GET /api/v2/ai/deepseek/test/ */
  deepseekTest(): Promise<any> {
    return apiFetch('/deepseek/test/');
  }

  /**
   * POST /api/v2/ai/deepseek/stream/  (SSE)
   *
   * Streams token-by-token DeepSeek completions.
   * Returns an AbortController — call `.abort()` to cancel.
   *
   * ```ts
   * const ctrl = aiService.deepseekStream(
   *   { messages: [{ role: 'user', content: 'Hello' }] },
   *   {
   *     onData: (raw) => appendToken(raw),
   *     onError: (e) => showToast(e),
   *     onComplete: () => setLoading(false),
   *   },
   * );
   * // later: ctrl.abort();
   * ```
   */
  deepseekStream(req: DeepSeekStreamRequest, handlers: SSEHandlers): AbortController {
    return connectSSE('/deepseek/stream/', req, handlers);
  }

  // -------- prompt optimization (replaces /ws/optimization/) --------

  /**
   * POST /api/v2/ai/optimization/   (JSON – one-shot)
   *
   * Simple request/response optimisation. Use when you don't need
   * progress events.
   */
  optimizePrompt(req: OptimizationRequest): Promise<OptimizationResult> {
    return apiFetch('/optimization/', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  /**
   * POST /api/v2/ai/optimization/stream/   (SSE)
   *
   * Real-time streaming optimisation with progress steps.
   * Returns an AbortController — call `.abort()` to cancel.
   *
   * Events emitted:
   *   meta           → { request_id, status: "connected" }
   *   progress       → { step: "init"|"retrieval"|"optimizing", message }
   *   result         → OptimizationResult
   *   stream_complete→ { request_id, processing_time_ms }
   *   error          → { error: string }
   *   stream_end     → { request_id }
   *
   * Example:
   * ```ts
   * const ctrl = aiService.optimizePromptStream(
   *   { original: 'Write a poem about the sea', mode: 'deep' },
   *   {
   *     onProgress: (step, msg) => setStatus(msg),
   *     onResult:   (r) => setOptimized(r.optimized),
   *     onError:    (e) => toast.error(e),
   *     onComplete: () => setLoading(false),
   *   },
   * );
   * ```
   */
  optimizePromptStream(req: OptimizationRequest, handlers: SSEHandlers): AbortController {
    return connectSSE('/optimization/stream/', req, handlers);
  }

  // -------- RAG agent --------

  /** POST /api/v2/ai/agent/optimize/ */
  agentOptimize(req: AgentOptimizeRequest): Promise<AgentOptimizeResponse> {
    return apiFetch('/agent/optimize/', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  /** GET /api/v2/ai/agent/stats/  (staff only) */
  agentStats(): Promise<any> {
    return apiFetch('/agent/stats/');
  }

  /** POST /api/v2/ai/rag/retrieve/ */
  ragRetrieve(query: string, topK = 5): Promise<any> {
    return apiFetch('/rag/retrieve/', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    });
  }

  /** POST /api/v2/ai/rag/answer/ */
  ragAnswer(query: string): Promise<any> {
    return apiFetch('/rag/answer/', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  // -------- assistants --------

  /** GET /api/v2/ai/assistant/ */
  getAssistants(): Promise<AssistantListResponse> {
    return apiFetch('/assistant/');
  }

  /** POST /api/v2/ai/assistant/run/ */
  runAssistant(req: AssistantRunRequest): Promise<any> {
    return apiFetch('/assistant/run/', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  /** GET /api/v2/ai/assistant/threads/ */
  getThreads(): Promise<{ threads: AssistantThread[]; total: number }> {
    return apiFetch('/assistant/threads/');
  }

  /** GET /api/v2/ai/assistant/threads/:threadId/ */
  getThread(threadId: string): Promise<{
    thread: AssistantThread;
    messages: AssistantThreadMessage[];
  }> {
    return apiFetch(`/assistant/threads/${threadId}/`);
  }

  // -------- suggestions --------

  /** GET /api/v2/ai/suggestions/?partial=...&limit=... */
  getSuggestions(partial: string, limit = 10): Promise<{
    suggestions: Array<{
      id: string;
      text: string;
      description: string;
      category: string;
      type: string;
    }>;
    total: number;
  }> {
    const params = new URLSearchParams({ partial, limit: String(limit) });
    return apiFetch(`/suggestions/?${params}`);
  }

  // -------- usage & quotas --------

  /** GET /api/v2/ai/usage/ */
  getUsage(): Promise<any> {
    return apiFetch('/usage/');
  }

  /** GET /api/v2/ai/quotas/ */
  getQuotas(): Promise<any> {
    return apiFetch('/quotas/');
  }

  // -------- Ask-Me prompt builder --------

  /** POST /api/v2/ai/askme/start/ */
  askmeStart(data: { goal: string; domain?: string; complexity?: string }): Promise<any> {
    return apiFetch('/askme/start/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /** POST /api/v2/ai/askme/answer/ */
  askmeAnswer(data: {
    session_id: string;
    question_id: string;
    answer: string;
  }): Promise<any> {
    return apiFetch('/askme/answer/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /** POST /api/v2/ai/askme/finalize/ */
  askmeFinalize(data: { session_id: string }): Promise<any> {
    return apiFetch('/askme/finalize/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /** GET /api/v2/ai/askme/sessions/ */
  askmeSessions(): Promise<any> {
    return apiFetch('/askme/sessions/');
  }

  /** GET /api/v2/ai/askme/sessions/:id/ */
  askmeSession(sessionId: string): Promise<any> {
    return apiFetch(`/askme/sessions/${sessionId}/`);
  }

  /** DELETE /api/v2/ai/askme/sessions/:id/delete/ */
  askmeDeleteSession(sessionId: string): Promise<any> {
    return apiFetch(`/askme/sessions/${sessionId}/delete/`, { method: 'DELETE' });
  }
}

// ---------------------------------------------------------------------------
// Singleton instance – import { aiService } from './FRONTEND_AI_SERVICES';
// ---------------------------------------------------------------------------

export const aiService = new AIService();

// ---------------------------------------------------------------------------
// React hooks (optional – only if React is available)
// ---------------------------------------------------------------------------

/**
 * React hook for SSE-based prompt optimization.
 *
 * ```tsx
 * function OptimizePage() {
 *   const { optimize, result, progress, loading, error } = usePromptOptimization();
 *
 *   return (
 *     <>
 *       <button onClick={() => optimize({ original: prompt })} disabled={loading}>
 *         Optimize
 *       </button>
 *       {progress && <p>{progress}</p>}
 *       {result && <pre>{result.optimized}</pre>}
 *       {error && <p className="error">{error}</p>}
 *     </>
 *   );
 * }
 * ```
 */
export function usePromptOptimization() {
  // Lazy-require React so this file works in non-React envs too
  const React = require('react');

  const [loading, setLoading] = React.useState(false);
  const [progress, setProgress] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<OptimizationResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const ctrlRef = React.useRef<AbortController | null>(null);

  const optimize = React.useCallback((req: OptimizationRequest) => {
    // Cancel any in-flight stream
    ctrlRef.current?.abort();

    setLoading(true);
    setProgress(null);
    setResult(null);
    setError(null);

    ctrlRef.current = aiService.optimizePromptStream(req, {
      onProgress: (_step: string, message: string) => setProgress(message),
      onResult: (data: OptimizationResult) => setResult(data),
      onError: (err: string) => setError(err),
      onComplete: () => setLoading(false),
    });
  }, []);

  const cancel = React.useCallback(() => {
    ctrlRef.current?.abort();
    setLoading(false);
  }, []);

  // Cleanup on unmount
  React.useEffect(() => () => ctrlRef.current?.abort(), []);

  return { optimize, cancel, result, progress, loading, error };
}

/**
 * React hook for SSE-based DeepSeek streaming chat.
 *
 * ```tsx
 * function ChatPage() {
 *   const { send, tokens, loading, error } = useDeepSeekStream();
 *
 *   return (
 *     <>
 *       <button onClick={() => send([{ role: 'user', content: input }])}>
 *         Send
 *       </button>
 *       <pre>{tokens}</pre>
 *     </>
 *   );
 * }
 * ```
 */
export function useDeepSeekStream() {
  const React = require('react');

  const [loading, setLoading] = React.useState(false);
  const [tokens, setTokens] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);
  const ctrlRef = React.useRef<AbortController | null>(null);

  const send = React.useCallback(
    (messages: Array<{ role: string; content: string }>, model?: string) => {
      ctrlRef.current?.abort();

      setLoading(true);
      setTokens('');
      setError(null);

      ctrlRef.current = aiService.deepseekStream(
        { messages, model },
        {
          onData: (raw: string) => {
            // Try to extract content delta from OpenAI-style chunk
            try {
              const obj = JSON.parse(raw.startsWith('data: ') ? raw.slice(6) : raw);
              const delta = obj?.choices?.[0]?.delta?.content;
              if (delta) setTokens((prev: string) => prev + delta);
            } catch {
              // non-JSON line — skip
            }
          },
          onError: (e: string) => setError(e),
          onComplete: () => setLoading(false),
        },
      );
    },
    [],
  );

  const cancel = React.useCallback(() => {
    ctrlRef.current?.abort();
    setLoading(false);
  }, []);

  React.useEffect(() => () => ctrlRef.current?.abort(), []);

  return { send, cancel, tokens, loading, error };
}

// ---------------------------------------------------------------------------
// Endpoint map  –  quick reference for developers
// ---------------------------------------------------------------------------

/**
 * ## Endpoint Map
 *
 * | Method | Path                                | Type | Description                      |
 * |--------|-------------------------------------|------|----------------------------------|
 * | GET    | /api/v2/ai/providers/               | JSON | List AI providers                |
 * | GET    | /api/v2/ai/models/                  | JSON | List AI models                   |
 * | POST   | /api/v2/ai/generate/                | JSON | One-shot generation              |
 * | POST   | /api/v2/ai/deepseek/chat/           | JSON | DeepSeek chat                    |
 * | GET    | /api/v2/ai/deepseek/test/           | JSON | Test DeepSeek connectivity       |
 * | POST   | /api/v2/ai/deepseek/stream/         | SSE  | DeepSeek streaming chat          |
 * | POST   | /api/v2/ai/optimization/            | JSON | Prompt optimization (one-shot)   |
 * | POST   | /api/v2/ai/optimization/stream/     | SSE  | Prompt optimization (streaming)  |
 * | POST   | /api/v2/ai/agent/optimize/          | JSON | RAG agent optimization           |
 * | GET    | /api/v2/ai/agent/stats/             | JSON | RAG agent stats (staff)          |
 * | POST   | /api/v2/ai/rag/retrieve/            | JSON | RAG document retrieval           |
 * | POST   | /api/v2/ai/rag/answer/              | JSON | RAG answer                       |
 * | GET    | /api/v2/ai/assistant/               | JSON | List assistants                  |
 * | POST   | /api/v2/ai/assistant/run/           | JSON | Run assistant                    |
 * | GET    | /api/v2/ai/assistant/threads/       | JSON | List threads                     |
 * | GET    | /api/v2/ai/assistant/threads/:id/   | JSON | Thread detail + messages         |
 * | GET    | /api/v2/ai/suggestions/             | JSON | Autocomplete suggestions         |
 * | GET    | /api/v2/ai/usage/                   | JSON | Usage stats                      |
 * | GET    | /api/v2/ai/quotas/                  | JSON | Quota info                       |
 * | POST   | /api/v2/ai/askme/start/             | JSON | Start Ask-Me session             |
 * | POST   | /api/v2/ai/askme/answer/            | JSON | Answer Ask-Me question           |
 * | POST   | /api/v2/ai/askme/finalize/          | JSON | Finalize Ask-Me prompt           |
 * | GET    | /api/v2/ai/askme/sessions/          | JSON | List Ask-Me sessions             |
 * | GET    | /api/v2/ai/askme/sessions/:id/      | JSON | Get Ask-Me session detail        |
 * | DELETE | /api/v2/ai/askme/sessions/:id/delete/| JSON | Delete Ask-Me session           |
 *
 * ### DEPRECATED (returns 426)
 * | ANY    | /ws/*                               |  –   | WebSocket routes (not supported) |
 *
 * The `/ws/` catch-all now returns HTTP 426 with a JSON body pointing
 * callers to the correct SSE / REST endpoints listed above.
 */
