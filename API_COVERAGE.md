# API Coverage & Frontend Integration Guide

This file explains how the frontend should integrate with the backend (promptcraft). It collects the most-used endpoints, auth patterns, CORS requirements, WebSocket notes and example client code (axios / fetch / WebSocket) so frontend engineers can wire the app quickly and professionally.

---

## Quick summary
- Base (dev): http://127.0.0.1:8000
- Production base (example): https://api.prompt-temple.com
- Versioned API prefix in repo: `/api/v2/` (you'll see auth and core endpoints here).
- Auth: JWT-style tokens (Authorization: Bearer <token>) are used in logged requests.
- Health and app-config endpoints are fetched at app start: `/health/`, `/api/v2/core/config/` (frontend needs these early).
- WebSockets: ASGI channels + Daphne; channel routing includes health and other ws endpoints (e.g. `/ws/health/`).

---

## Base URLs / env
Set these in your frontend environment variables (or .env):
- REACT_APP_API_URL (or NEXT_PUBLIC_API_URL) — e.g. `http://127.0.0.1:8000` for local dev
- REACT_APP_WS_URL — e.g. `ws://127.0.0.1:8000` or `wss://api.prompt-temple.com`

Example values (dev):
- API_BASE = http://127.0.0.1:8000
- WS_BASE = ws://127.0.0.1:8000

---

## Important endpoints (observed in repo/logs)
These are the endpoints the frontend will call most often. Confirm the route & contract with the backend if you need extra fields.

- Health checks
  - GET `/health/` — simple health
  - GET `/api/v2/core/health/` or `/api/v1/core/health/` — more detailed system health

- App config (loaded at app start)
  - GET `/api/v2/core/config/` — returns app-level config (feature flags, settings used by the frontend). This is fetched automatically on app boot.

- Auth (users)
  - POST `/api/v2/auth/login/` — login with username/email + password. Returns token(s) (access/refresh) and user info
  - POST `/api/v2/auth/register/` — register a new user (fields depend on backend)
  - GET `/api/v2/auth/profile/` — get current user profile (requires Authorization header)
  - POST `/api/v2/auth/logout/` — logout (may invalidate tokens)
  - (Social) GET `/api/v2/auth/social/providers/` — list social auth providers
  - (Social initiate) GET `/api/v2/auth/social/google/initiate/`, `/api/v2/auth/social/github/initiate/` — start social login flows
  - (Social callback) `/api/v2/auth/social/callback/` — backend side callback (frontend may not call this directly)

- Analytics / dashboard (example)
  - GET `/api/v2/analytics/dashboard/`

- Chat/AI health endpoints (example)
  - GET `/api/v2/chat/health/`

Notes: logs show successful POST /api/v2/auth/login/ responses and many requests using the Authorization header `Bearer <token>`.

---

## Auth & token handling (recommended)
1. Prefer storing refresh tokens in an httpOnly secure cookie set by the server on login. If backend cannot set httpOnly cookie, store the refresh token securely (but know it's less safe).
2. Store the access token in memory (or secure storage) and add it to Authorization header: `Authorization: Bearer <access>` on each request.
3. Refresh flow: when the backend returns 401/403 for an expired access token, call the refresh endpoint (if present) to get a new access token. Typical endpoint name: `/api/v2/auth/token/refresh/` (confirm with backend). If refresh fails, redirect to login.
4. Logout should call `/api/v2/auth/logout/` and clear local tokens and cookies.

Example axios interceptor pattern (simplified):

```js
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
    'X-Client-Version': 'frontend@1.0.0' // add a client version header
  },
  withCredentials: true // if using cookies for refresh
});

// attach access token
api.interceptors.request.use(config => {
  const token = getAccessToken(); // implement retrieval
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// response interceptor to attempt refresh on 401
api.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config;
    if (err.response && err.response.status === 401 && !original._retry) {
      original._retry = true;
      try {
        // attempt refresh; endpoint may vary, confirm with backend
        const resp = await api.post('/api/v2/auth/token/refresh/', { refresh: getRefreshToken() });
        setAccessToken(resp.data.access);
        original.headers.Authorization = `Bearer ${resp.data.access}`;
        return api(original);
      } catch (refreshErr) {
        // fallback: sign out and redirect to login
        signOutFrontend();
        return Promise.reject(refreshErr);
      }
    }
    return Promise.reject(err);
  }
);

export default api;
```

Notes:
- `X-Client-Version` is used by the frontend in the logs; the backend must allow this header for preflight CORS.
- If you use fetch() instead of axios, set credentials and headers accordingly.

---

## Example fetch / login request

```js
await fetch(`${API_BASE}/api/v2/auth/login/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Client-Version': 'frontend@1.0.0'
  },
  body: JSON.stringify({ username: 'me', password: 'secret' }),
  credentials: 'include' // if backend sets cookies
});
```

Expected successful response (example):
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>",
  "user": { "id": 1, "email": "..." }
}
```
Confirm the exact response fields with the backend.

---

## WebSocket / Realtime integration
Backend runs via Daphne + Redis channel layer; the repo has ASGI WebSocket consumers and routing for patterns such as `/ws/health/`.

- Example simple connection pattern (plain WebSocket):

```js
const WS_BASE = process.env.REACT_APP_WS_URL || 'ws://127.0.0.1:8000';
const token = getAccessToken();
const ws = new WebSocket(`${WS_BASE}/ws/health/?token=${encodeURIComponent(token)}`);

ws.onopen = () => console.log('ws open');
ws.onmessage = (e) => console.log('msg', e.data);
ws.onclose = () => console.log('closed');
```

- Notes about auth for WebSockets:
  - The backend accepts Authorization bearer tokens on HTTP requests; for WebSockets, many projects accept the token as a query parameter `?token=...` or use the `Sec-WebSocket-Protocol` subprotocol to send a token. Check the backend consumer implementation to know which is supported. The repo contains routing at `apps/core/routing.py` with `path('ws/health/', consumers.HealthCheckConsumer.as_asgi())` — check the corresponding consumer to confirm the accepted auth mechanism.
  - If you send tokens via query param, be aware that those tokens may be logged; prefer other secure patterns if possible.

- Reconnect strategy: implement a reconnect backoff or use a small wrapper library (e.g., ReconnectingWebSocket).

---

## CORS and preflight
You will likely see CORS-related errors during frontend development (the logs you provided show blocked requests and headers issues). To avoid problems, the backend must be configured to allow frontend origins and headers used by the client.

Frontend requirements to communicate correctly:
1. The backend must include your frontend origin in allowed origins (e.g., `http://localhost:3000`).
2. The backend must allow the custom headers you send. From logs we saw `x-client-version` being used; ensure backend `CORS_ALLOW_HEADERS` includes `x-client-version`.
3. If the frontend sends cookies for refresh or session, ensure `Access-Control-Allow-Credentials` is `true`, and set `withCredentials: true` in axios or `credentials: 'include'` in fetch.
4. Preflight (OPTIONS) must return allowed headers and methods for endpoints that accept custom headers or methods.

Example server-side (Django + django-cors-headers) settings the backend team should ensure:
```py
CORS_ALLOWED_ORIGINS = [
  'http://localhost:3000',
  'https://your-production-domain.com',
]
CORS_ALLOW_HEADERS = list(default_headers) + [
  'x-client-version',
]
CORS_ALLOW_CREDENTIALS = True
```

If CORS is misconfigured you will see browser errors like "No 'Access-Control-Allow-Origin' header is present" or "Request header field x-client-version is not allowed by Access-Control-Allow-Headers" (these were present in the logs). Ask backend to add the header to allowed headers and origins.

---

## Social auth (flow)
- Frontend calls GET `/api/v2/auth/social/providers/` to discover available providers.
- For each provider, the frontend should redirect the user to the provider's `initiate` URL (e.g., `/api/v2/auth/social/google/initiate/`) or open popup depending on implementation.
- The provider will redirect back to the server callback `/api/v2/auth/social/callback/` which finalizes authentication and issues tokens/cookies. Confirm whether the backend then redirects to a frontend route with tokens or sets httpOnly cookies.

Troubleshooting: logs show `Internal Server Error` on `/api/v2/auth/social/providers/` in some cases — coordinate with backend to stabilize provider list endpoint.

---

## Health checks & app startup
- The frontend loads `/api/v2/core/config/` early — if this fails, the app will retry and may show degraded UI.
- For local debugging, hitting `/health/` verifies the server is responsive.
- Dockerfile and deployment configs target `/api/v1/core/health/` or `/api/v2/core/health/` in different places — confirm which one your environment uses.

---

## Error handling & UX guidance
- Show a friendly UI for network errors and CORS failures (detect `TypeError: Failed to fetch` or HTTP 0/NETWORK errors and show a troubleshooting page).
- On 401: attempt token refresh; if refresh fails, force logout and redirect to login.
- Distinguish between permanently unavailable (500) and transient problems (502/503) — allow retry with backoff on transient errors.

---

## Troubleshooting quick checklist (frontend dev)
If requests fail locally:
1. Confirm backend is running at API_BASE and accessible in the browser (open `http://127.0.0.1:8000/health/`).
2. Open browser console, check CORS errors: ask backend to add missing headers/origin.
3. Confirm tokens are present and `Authorization` header set.
4. If social endpoints return 404/500, coordinate with backend logs; these endpoints are in `apps/social_auth/views.py`.
5. For WebSocket failures, confirm WS_BASE and path (`/ws/...`) and token transport (query param vs subprotocol).

---

## Next steps & notes for backend team (so frontend works smoothly)
- Add `http://localhost:3000` and any other dev origin to CORS_ALLOWED_ORIGINS.
- Add `x-client-version` to allowed CORS headers.
- Consider setting refresh tokens via secure httpOnly cookie to make refresh flows easier and safer for SPA.
- Confirm refresh endpoint path and contract, and share it with frontend.
- Document WebSocket token acceptance (query param name or subprotocol) in the backend docs or code.

---

## Contact / where to look in the repo
- Backend URL routing: `promptcraft/urls.py` — maps `/api/v2/auth/`, `/api/v2/core/config/`, `/health/` etc.
- Social auth logic: `apps/social_auth/views.py` (initiate & callback URLs)
- WebSocket routing: `apps/core/routing.py` (e.g. `path('ws/health/', ...)`)
- Logs show request patterns in `logs/wsgi.log` and `logs/django_error.log` — useful for debugging CORS/auth errors.

---

If you want, I can:
- Add a minimal frontend example repo/snippet that exercises login, config fetch and WebSocket, or
- Open a small PR that adds a concrete axios starter file in the frontend (e.g., `src/lib/api.ts`) with the pattern above.

If you want that next step, tell me which frontend framework you're using (React, Next.js, Vue, etc.) and whether refresh tokens are available as an endpoint or via cookie. 

-- End of API_COVERAGE.md
