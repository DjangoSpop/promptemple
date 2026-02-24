# PromptCraft Frontend Integration Guide

> Ground-truth map of every working endpoint, exact request/response shapes,
> auth requirements, streaming protocol, and known gotchas.
>
> **Transport:** HTTP + SSE only (Gunicorn/WSGI). WebSocket URLs return JSON with SSE alternatives.

---

## Table of Contents

1. [Base URL & Auth](#1-base-url--auth)
2. [Streaming Protocol — SSE](#2-streaming-protocol--sse)
3. [AI Providers & Models](#3-ai-providers--models)
4. [Content Generation](#4-content-generation)
5. [DeepSeek Endpoints](#5-deepseek-endpoints)
6. [Ask-Me Prompt Builder](#6-ask-me-prompt-builder)
7. [Prompt Optimization (RAG)](#7-prompt-optimization-rag)
8. [AI Assistant & Threads](#8-ai-assistant--threads)
9. [Orchestrator Utilities](#9-orchestrator-utilities)
10. [Usage & Quotas](#10-usage--quotas)
11. [WebSocket — What to Do](#11-websocket--what-to-do)
12. [Error Reference](#12-error-reference)
13. [Minimal TypeScript Client](#13-minimal-typescript-client)

---

## 1. Base URL & Auth

```
Production:  https://<heroku-app>.herokuapp.com/api/v2
Local:       http://localhost:8000/api/v2
```

All endpoints marked **Auth: JWT** require:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

Get tokens:
```
POST /api/v2/auth/token/          { "username": "...", "password": "..." }
POST /api/v2/auth/token/refresh/  { "refresh": "<refresh_token>" }
```

Endpoints marked **Auth: None** are open (Ask-Me is open during development — add auth before production).

---

## 2. Streaming Protocol — SSE

All streaming endpoints return `Content-Type: text/event-stream`.

Standard SSE format — each event:
```
event: <type>\n
data: <json_string>\n\n
```

### Event types used across all streaming endpoints

| Event | Meaning |
|-------|---------|
| `meta` | Connection open, includes `request_id` |
| `stream_start` | Upstream connected, includes `model` |
| `data` | Content chunk — parse the JSON payload |
| `progress` | Step description (optimization only) |
| `result` | Final output object (optimization only) |
| `[DONE]` | Upstream finished sending tokens |
| `stream_complete` | Processing time summary |
| `stream_end` | Final event, always emitted |
| `error` | Error occurred |

### Reading SSE from a POST endpoint (use `fetch`, NOT `EventSource`)

`EventSource` only supports GET. For POST streaming:

```typescript
async function* readSSE(
  url: string,
  body: object,
  token: string
): AsyncGenerator<any> {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buf = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split('\n');
    buf = lines.pop()!;
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const payload = line.slice(6).trim();
      if (payload === '[DONE]') return;
      try { yield JSON.parse(payload); } catch { /* skip non-JSON */ }
    }
  }
}
```

---

## 3. AI Providers & Models

### `GET /api/v2/ai/providers/` — Auth: JWT

```json
{
  "providers": [
    {
      "id": "deepseek",
      "name": "DeepSeek",
      "status": "available",
      "models": ["deepseek-chat", "deepseek-coder", "deepseek-math"],
      "features": ["chat", "code_generation", "optimization", "cost_effective"],
      "cost_per_1k_tokens": 0.0014,
      "max_tokens": 4000
    },
    {
      "id": "openrouter",
      "name": "OpenRouter",
      "status": "available",
      "models": ["nvidia/nemotron-3-nano-30b-a3b:free", "..."],
      "cost_per_1k_tokens": 0
    }
  ],
  "total_providers": 3,
  "deepseek_available": true,
  "openrouter_available": true
}
```

`status: "disabled"` = API key not configured on server — hide from users.

---

### `GET /api/v2/ai/models/` — Auth: JWT

```json
{
  "models": [
    {
      "id": "deepseek-chat",
      "name": "DeepSeek Chat",
      "provider": "deepseek",
      "cost_per_token": 0.0014,
      "max_tokens": 4000,
      "features": ["chat", "general_purpose"],
      "description": "General conversation and reasoning"
    }
  ],
  "total_models": 8,
  "deepseek_available": true,
  "openrouter_available": true
}
```

---

## 4. Content Generation

### `POST /api/v2/ai/generate/` — Auth: JWT

Non-streaming. Routes automatically based on model name.

**Request:**
```json
{
  "prompt": "Write a haiku about code",
  "model": "deepseek-chat",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Model routing:**
- `deepseek-*` → DeepSeek API
- `nvidia/`, `qwen/`, `ai/`, `deepseek/`, `nousresearch/` prefixes → OpenRouter
- Anything else → placeholder (no real AI call)

**Response:**
```json
{
  "result": "Fingers on the keys...",
  "model": "deepseek-chat",
  "tokens_used": 87,
  "processing_time_ms": 423,
  "cost_estimate": 0.000122,
  "provider": "deepseek",
  "success": true
}
```

---

## 5. DeepSeek Endpoints

### `GET /api/v2/ai/deepseek/test/` — Auth: JWT

Health-check. Call on startup to decide whether to show DeepSeek in the UI.

```json
{
  "status": "success",
  "available": true,
  "api_key_configured": true,
  "test_response": "Hello from DeepSeek!",
  "model": "deepseek-chat",
  "response_time_ms": 381
}
```

---

### `POST /api/v2/ai/deepseek/chat/` — Auth: JWT

Multi-turn non-streaming chat.

**Request:**
```json
{
  "messages": [
    { "role": "user", "content": "What is recursion?" }
  ],
  "model": "deepseek-chat",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "message": { "role": "assistant", "content": "Recursion is..." },
  "model": "deepseek-chat",
  "tokens_used": 143,
  "processing_time_ms": 612,
  "provider": "deepseek",
  "success": true
}
```

---

### `POST /api/v2/ai/deepseek/stream/` — Auth: JWT — **SSE**

Streaming chat. Use `fetch` + `ReadableStream`.

**Request:**
```json
{
  "messages": [{ "role": "user", "content": "Explain async/await" }],
  "model": "deepseek-chat",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

Or shorthand: `{ "prompt": "Explain async/await" }` (auto-wrapped as user message).

**SSE events in order:**
```
event: meta
data: {"request_id": "a1b2c3d4", "status": "connected"}

event: stream_start
data: {"trace_id": "xyz", "model": "deepseek-chat"}

data: {"choices":[{"delta":{"content":"Async"},"index":0}]}
data: {"choices":[{"delta":{"content":"/await"},"index":0}]}
...
data: [DONE]

event: stream_complete
data: {"processing_time_ms": 1240}

event: stream_end
data: {"request_id": "a1b2c3d4"}
```

**Extracting text:**
```typescript
for await (const chunk of readSSE('/api/v2/ai/deepseek/stream/', body, token)) {
  const delta = chunk?.choices?.[0]?.delta?.content;
  if (delta) output += delta;
}
```

---

## 6. Ask-Me Prompt Builder

> **Auth: None** — open endpoints (add `IsAuthenticated` before production).

### Flow

```
POST /askme/start/    → session_id + initial questions
POST /askme/answer/   → answer one question → next questions   (repeat)
POST /askme/finalize/ → final generated prompt
```

---

### `POST /api/v2/ai/askme/start/` — Auth: None

**Request:**
```json
{
  "intent": "Build a Python web scraper for e-commerce prices",
  "context": "Must run on a schedule"
}
```

`intent` or `goal` both accepted.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "questions": [
    {
      "qid": "q_target_site",
      "title": "Which website are you scraping?",
      "help_text": "The scraper will be tailored to this structure",
      "kind": "short_text",
      "options": [],
      "variable": "target_site",
      "required": true,
      "suggested": "amazon.com",
      "is_answered": false,
      "answer": null
    }
  ],
  "good_enough_to_run": false
}
```

**Question `kind` → UI control:**

| kind | Render as |
|------|-----------|
| `short_text` | `<input type="text">` |
| `long_text` | `<textarea>` |
| `choice` | `<select>` or radio using `options[]` |
| `boolean` | Toggle / yes-no buttons |
| `number` | `<input type="number">` |

---

### `POST /api/v2/ai/askme/answer/` — Auth: None

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "qid": "q_target_site",
  "value": "amazon.com"
}
```

Field aliases: `question_id` / `id` for `qid`; `answer` for `value`.

**Response:**
```json
{
  "session_id": "...",
  "questions": [ /* next unanswered questions */ ],
  "good_enough_to_run": false,
  "preview_prompt": null
}
```

- When `preview_prompt` is non-null → show as live preview (user is nearly done)
- When `good_enough_to_run: true` → enable the Finalize button

---

### `POST /api/v2/ai/askme/finalize/` — Auth: None

**Request:**
```json
{ "session_id": "550e8400-e29b-41d4-a716-446655440000" }
```

**Response:**
```json
{
  "prompt": "You are a Python web scraping expert...\n\nTask: Scrape amazon.com for product prices...",
  "metadata": {
    "spec": { "target_site": "amazon.com", "output_format": "CSV" },
    "variables_used": ["target_site", "output_format"],
    "completion_percentage": 0.85
  }
}
```

---

### `GET /api/v2/ai/askme/stream/?session_id=<uuid>` — Auth: None — **SSE**

Snapshot of current session state. Use `EventSource` (this is a GET endpoint).

```typescript
const es = new EventSource(`/api/v2/ai/askme/stream/?session_id=${sid}`);
es.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  if (msg.type === 'question')  renderQuestion(msg.data);
  if (msg.type === 'preview')   showPreview(msg.data);
  if (msg.type === 'ready')     enableFinalizeButton();
  if (msg.type === 'complete')  es.close();
};
```

Events: `question`, `preview`, `ready`, `complete`, `error`.

---

### Session Management (Auth: None)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v2/ai/askme/sessions/` | Last 50 sessions |
| GET | `/api/v2/ai/askme/sessions/<uuid>/` | Session detail |
| DELETE | `/api/v2/ai/askme/sessions/<uuid>/delete/` | Delete session |
| GET | `/api/v2/ai/askme/debug/` | Auth connectivity check |

---

## 7. Prompt Optimization (RAG)

### `POST /api/v2/ai/optimization/stream/` — Auth: JWT — **SSE**

**Request:**
```json
{
  "original": "Write code to read a file",
  "mode": "fast",
  "budget": { "tokens_in": 2000, "tokens_out": 800, "max_credits": 5 }
}
```

`mode`: `"fast"` (1 credit) or `"deep"` (3 credits). `original` or `prompt` both accepted.

**SSE events:**
```
event: meta
data: {"status": "connected"}

event: progress
data: {"step": "retrieve", "message": "Searching knowledge base..."}

event: progress
data: {"step": "optimize", "message": "Applying improvements..."}

event: result
data: {
  "optimized": "Write a Python function that reads a file line by line...",
  "citations": [{"id": "...", "title": "...", "score": 0.91}],
  "diff_summary": "Added specificity and output format",
  "usage": {"tokens_in": 1200, "tokens_out": 450, "credits": 1}
}

event: stream_complete
data: {"processing_time_ms": 2100}
```

---

### `POST /api/v2/ai/optimization/` — Auth: JWT

Non-streaming version. Same request. Returns the `result` payload directly:

```json
{
  "optimized": "...",
  "citations": [{ "id": "...", "title": "...", "score": 0.91 }],
  "diff_summary": "...",
  "usage": { "tokens_in": 1200, "tokens_out": 450, "credits": 1 },
  "run_id": "abc123",
  "processing_time_ms": 2100,
  "success": true
}
```

---

### `POST /api/v2/ai/agent/optimize/` — Auth: JWT

RAG optimization with idempotency + explicit credit control.

**Extra required fields:**
```json
{
  "session_id": "unique-string",
  "original": "...",
  "mode": "fast"
}
```

Returns `402` if credits insufficient. Returns cached result if same `session_id` + content repeats within 1 hour. Rate limit: 20 req/hr (returns `429`).

---

### `POST /api/v2/ai/rag/retrieve/` — Auth: JWT

Direct document retrieval (no AI generation).

```json
{ "query": "prompt engineering best practices", "top_k": 5 }
```

```json
{
  "results": [{ "id": "...", "title": "...", "source": "...", "snippet": "..." }],
  "count": 5
}
```

---

## 8. AI Assistant & Threads

### `GET /api/v2/ai/assistant/` — Auth: JWT

```json
{
  "assistants": [
    { "id": "deepseek_chat", "name": "DeepSeek Chat", "features": [] }
  ],
  "default_assistant": "deepseek_chat",
  "total": 1
}
```

---

### `POST /api/v2/ai/assistant/run/` — Auth: JWT

```json
{
  "message": "Help me improve this prompt",
  "assistant_id": "deepseek_chat",
  "thread_id": "optional-uuid"
}
```

Omit `thread_id` to start a new thread automatically.

---

### `GET /api/v2/ai/assistant/threads/` — Auth: JWT

List threads for the current user.

```json
{
  "threads": [{
    "id": "uuid", "assistant_id": "deepseek_chat",
    "title": "Session title", "last_interaction_at": "2026-02-24T19:00:00Z"
  }],
  "total": 1
}
```

---

### `GET /api/v2/ai/assistant/threads/<uuid>/` — Auth: JWT

Full thread with all messages. Returns `403` if thread belongs to another user.

```json
{
  "thread": { "id": "...", "assistant_id": "..." },
  "messages": [
    { "role": "user", "content": "...", "created_at": "..." },
    { "role": "assistant", "content": "...", "created_at": "..." }
  ]
}
```

---

## 9. Orchestrator Utilities

Base: `/api/v2/orchestrator/` — all Auth: JWT.

### `POST orchestrator/intent_detection/`

Classify what the user wants before routing to the right feature.

```json
{ "prompt": "I want to scrape Amazon for prices" }
```
```json
{
  "intent": "technical",
  "confidence": 0.87,
  "sub_intent": "web_scraping",
  "suggested_categories": ["coding", "automation"],
  "keywords": ["scrape", "amazon", "prices"]
}
```

---

### `POST orchestrator/prompt_assessment/`

Score a prompt. Use for live feedback as the user types.

```json
{ "original_prompt": "Write code" }
```
```json
{
  "score": 4.2,
  "clarity": 3.0,
  "specificity": 2.5,
  "effectiveness": 5.0,
  "suggestions": ["Add the programming language", "Specify output format"],
  "strengths": ["Clear intent"],
  "improved_prompt": "Write a Python function that..."
}
```

---

### `POST orchestrator/template_rendering/`

Fill template variables. Supports `{{var}}` and `{var}`.

```json
{
  "template_content": "Write a {{language}} function to {{task}}",
  "variables": { "language": "Python", "task": "sort a list" }
}
```
```json
{ "rendered": "Write a Python function to sort a list", "variables_applied": ["language", "task"] }
```

---

### `GET orchestrator/library_search/?q=<query>`

```
?q=email&category=business&limit=12
```
```json
{
  "templates": [{
    "id": "uuid", "title": "Email Writer",
    "category": "business", "usage_count": 342, "average_rating": 4.7
  }],
  "total": 1
}
```

---

### `GET orchestrator/template/<uuid>/`

Full template including `content` field.

---

## 10. Usage & Quotas

### `GET /api/v2/ai/usage/` — Auth: JWT

```json
{
  "usage": {
    "tokens_used_today": 12400,
    "tokens_remaining_today": 87600,
    "daily_limit": 100000,
    "monthly_limit": 1000000,
    "cost_today": 0.0174
  }
}
```

### `GET /api/v2/ai/quotas/` — Auth: JWT

```json
{
  "quotas": {
    "daily_limit": 100000,
    "used_today": 12400,
    "remaining_today": 87600,
    "can_use_ai": true,
    "reset_time": "2026-02-25T00:00:00Z"
  }
}
```

---

## 11. WebSocket — What to Do

The server runs **Gunicorn (WSGI)**. WebSocket upgrade requests return:

```json
{
  "error": "WebSocket endpoints are not available on this deployment",
  "message": "This server uses HTTP/SSE. Use the REST API instead.",
  "sse_endpoints": {
    "deepseek_stream": "/api/v2/ai/deepseek/stream/",
    "optimization_stream": "/api/v2/ai/optimization/stream/"
  }
}
```

**Migration guide for the frontend:**

| If you were using WS for... | Use instead |
|-----------------------------|-------------|
| DeepSeek streaming | `POST /api/v2/ai/deepseek/stream/` (SSE) |
| Prompt optimization streaming | `POST /api/v2/ai/optimization/stream/` (SSE) |
| Ask-Me session updates | `GET /api/v2/ai/askme/stream/` (SSE, GET) |
| General AI processing | `POST /api/v2/ai/generate/` (JSON) |

---

## 12. Error Reference

| Status | Meaning | Action |
|--------|---------|--------|
| `400` | Bad request / missing field | Show field error |
| `401` | Token expired or missing | Refresh token / redirect to login |
| `402` | Insufficient credits | Show upgrade prompt |
| `403` | Access denied | Show permission error |
| `404` | Not found | Show not-found message |
| `429` | Rate limit (20 req/hr on RAG) | Show retry-after |
| `500` | Internal error | Log and show generic error |
| `503` | AI provider not configured | Check `/ai/providers/` |

All error bodies:
```json
{ "error": "human readable message", "details": "optional extra context" }
```

---

## 13. Minimal TypeScript Client

```typescript
const BASE = process.env.REACT_APP_API_URL ?? 'http://localhost:8000/api/v2';

class PromptCraftAPI {
  private token = localStorage.getItem('access_token');

  private h(extra: Record<string, string> = {}) {
    return {
      'Content-Type': 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      ...extra,
    };
  }

  async get<T>(path: string): Promise<T> {
    const r = await fetch(`${BASE}${path}`, { headers: this.h() });
    if (!r.ok) throw await r.json();
    return r.json();
  }

  async post<T>(path: string, body: object): Promise<T> {
    const r = await fetch(`${BASE}${path}`, {
      method: 'POST', headers: this.h(), body: JSON.stringify(body),
    });
    if (!r.ok) throw await r.json();
    return r.json();
  }

  async *stream(path: string, body: object) {
    const r = await fetch(`${BASE}${path}`, {
      method: 'POST', headers: this.h(), body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const reader = r.body!.getReader();
    const dec = new TextDecoder();
    let buf = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop()!;
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const p = line.slice(6).trim();
        if (p === '[DONE]') return;
        try { yield JSON.parse(p); } catch { /* skip */ }
      }
    }
  }

  // --- AI ---
  providers       = () => this.get('/ai/providers/');
  models          = () => this.get('/ai/models/');
  generate        = (prompt: string, model = 'deepseek-chat') =>
                      this.post('/ai/generate/', { prompt, model });
  deepseekTest    = () => this.get('/ai/deepseek/test/');
  deepseekChat    = (messages: object[]) =>
                      this.post('/ai/deepseek/chat/', { messages });
  deepseekStream  = (messages: object[]) =>
                      this.stream('/ai/deepseek/stream/', { messages });

  // --- Ask-Me ---
  askmeStart    = (intent: string, context?: string) =>
                    this.post('/ai/askme/start/', { intent, context });
  askmeAnswer   = (session_id: string, qid: string, value: unknown) =>
                    this.post('/ai/askme/answer/', { session_id, qid, value });
  askmeFinalize = (session_id: string) =>
                    this.post('/ai/askme/finalize/', { session_id });
  // Ask-Me stream is GET → use EventSource directly
  askmeStream   = (session_id: string) =>
                    new EventSource(`${BASE}/ai/askme/stream/?session_id=${session_id}`);

  // --- Optimization ---
  optimize       = (original: string, mode = 'fast') =>
                     this.post('/ai/optimization/', { original, mode });
  optimizeStream = (original: string, mode = 'fast') =>
                     this.stream('/ai/optimization/stream/', { original, mode });

  // --- Orchestrator ---
  detectIntent   = (prompt: string) =>
                     this.post('/orchestrator/intent_detection/', { prompt });
  assessPrompt   = (original_prompt: string) =>
                     this.post('/orchestrator/prompt_assessment/', { original_prompt });
  searchLibrary  = (q: string) =>
                     this.get(`/orchestrator/library_search/?q=${encodeURIComponent(q)}`);
}

export const api = new PromptCraftAPI();
```

---

## Production Checklist

| # | Action |
|---|--------|
| 1 | Add `IsAuthenticated` to all `askme_*` endpoints |
| 2 | Filter `askme_sessions_list` by `user=request.user` |
| 3 | Add token refresh interceptor (401 → refresh → retry) |
| 4 | Remove `/api/v2/ai/askme/debug/` route |
| 5 | Confirm `DEEPSEEK_API_KEY` / `ZAI_API_TOKEN` env var is set on Heroku |
| 6 | Confirm `REDIS_URL` env var is set (used by django-redis cache) |
| 7 | Do not expose `/api/v2/ai/agent/stats/` in user-facing UI (staff-only) |
